"""
Equation Extraction Module

This module extracts mathematical equations from scientific PDFs using:
1. PDF text parsing for embedded LaTeX
2. GPT-4 Vision for equation region detection
3. GPT-4V-based LaTeX OCR for equation images

Features:
- Extract equations from PDF text
- Detect equation regions using GPT-4V
- Convert equation images to LaTeX
- Inline and display equation support
- Equation numbering preservation

Author: Ion Transport Virtual Lab
"""

import base64
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io
from openai import OpenAI


class EquationExtractor:
    """Extracts mathematical equations from scientific PDFs."""

    def __init__(self):
        """Initialize equation extractor."""
        self.client = OpenAI()
        self.vision_model = "gpt-4o"

    def extract_equations_from_text(
        self,
        pdf_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Extract equations from PDF text (for PDFs with embedded LaTeX).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of equations found in text
        """
        doc = fitz.open(pdf_path)
        equations = []

        # Common LaTeX equation delimiters
        equation_patterns = [
            (r'\$\$(.*?)\$\$', 'display'),           # $$...$$
            (r'\\\[(.*?)\\\]', 'display'),           # \[...\]
            (r'\\begin\{equation\}(.*?)\\end\{equation\}', 'display'),  # \begin{equation}
            (r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}', 'display'),  # \begin{align}
            (r'\$(.*?)\$', 'inline'),                # $...$
            (r'\\\((.*?)\\\)', 'inline'),            # \(...\)
        ]

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Try each pattern
            for pattern, eq_type in equation_patterns:
                matches = re.finditer(pattern, text, re.DOTALL)
                for match in matches:
                    latex = match.group(1).strip()

                    # Skip very short matches (likely false positives)
                    if len(latex) < 3:
                        continue

                    equations.append({
                        "page": page_num + 1,
                        "type": eq_type,
                        "latex": latex,
                        "source": "text_extraction",
                        "raw_match": match.group(0)
                    })

        doc.close()

        # Deduplicate
        unique_equations = []
        seen = set()
        for eq in equations:
            key = (eq["page"], eq["latex"])
            if key not in seen:
                seen.add(key)
                unique_equations.append(eq)

        return unique_equations

    def detect_equation_regions(
        self,
        pdf_path: Path,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """
        Detect equation regions in a PDF page using GPT-4V.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)

        Returns:
            List of detected equation regions with bounding boxes
        """
        try:
            # Render page to image
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # Render at higher resolution for better text recognition
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            width, height = img.size

            # Encode image
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

            doc.close()

            # Construct prompt
            prompt = f"""Analyze this page from a scientific paper and identify all mathematical equations.

Page dimensions: {width}x{height} pixels

Please identify:
1. All mathematical equations (both inline and display equations)
2. Their approximate locations as bounding boxes [x_min, y_min, x_max, y_max]
3. The LaTeX representation of each equation
4. Whether it's an inline or display equation
5. Any equation numbers (e.g., (1), (2.3), etc.)

IMPORTANT:
- Use pixel coordinates with origin (0,0) at top-left
- Include both simple equations (e.g., E = mc²) and complex ones
- For inline equations, estimate the bounding box around just the equation
- For display equations, include the entire equation block
- If an equation is numbered, note the number

Format response as JSON with key "equations", which is an array where each equation has:
- bbox: [x_min, y_min, x_max, y_max]
- latex: The equation in LaTeX format
- type: "inline" or "display"
- number: Equation number if present (e.g., "1", "2.3") or null
- confidence: Your confidence (0-1) that this is an equation
"""

            # Call GPT-4V
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1,
            )

            response_text = response.choices[0].message.content

            # Parse JSON
            try:
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)

                result = json.loads(response_text)
                equations = result.get("equations", [])

                # Scale bounding boxes back to original resolution (we used 2x zoom)
                for eq in equations:
                    if "bbox" in eq:
                        eq["bbox"] = [coord / 2.0 for coord in eq["bbox"]]

                return equations

            except json.JSONDecodeError:
                print(f"    ⚠ Could not parse equation detection response")
                return []

        except Exception as e:
            print(f"    ✗ Error detecting equations on page {page_num + 1}: {e}")
            return []

    def extract_equation_image(
        self,
        pdf_path: Path,
        page_num: int,
        bbox: List[float],
        output_dir: Path,
        equation_id: str
    ) -> Optional[Path]:
        """
        Extract equation region as image.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            bbox: Bounding box [x_min, y_min, x_max, y_max]
            output_dir: Output directory
            equation_id: Unique ID for equation

        Returns:
            Path to saved equation image or None
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # Create rectangle from bbox
            rect = fitz.Rect(bbox)

            # Render equation region at high resolution
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom for clarity
            pix = page.get_pixmap(matrix=mat, clip=rect)

            # Save image
            output_dir.mkdir(parents=True, exist_ok=True)
            img_filename = f"equation_{equation_id}.png"
            img_path = output_dir / img_filename

            pix.save(str(img_path))

            doc.close()
            return img_path

        except Exception as e:
            print(f"    ✗ Error extracting equation image: {e}")
            return None

    def ocr_equation_to_latex(
        self,
        image_path: Path
    ) -> Optional[str]:
        """
        Convert equation image to LaTeX using GPT-4V.

        Args:
            image_path: Path to equation image

        Returns:
            LaTeX representation or None
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prompt for LaTeX conversion
            prompt = """Convert this mathematical equation image to LaTeX format.

Instructions:
1. Provide ONLY the LaTeX code for the equation
2. Do NOT include delimiters like $, $$, \[, \], \begin{equation}, etc.
3. Just the raw LaTeX expression
4. Use standard LaTeX math commands
5. Preserve all subscripts, superscripts, fractions, integrals, etc.
6. If you see multiple equations, provide them all separated by newlines

Example:
If image shows: E = mc²
Return: E = mc^2

If image shows: ∂ρ/∂t + ∇·(ρv) = 0
Return: \\frac{\\partial \\rho}{\\partial t} + \\nabla \\cdot (\\rho v) = 0
"""

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.0,  # Zero temperature for deterministic output
            )

            latex = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if "```" in latex:
                latex = re.sub(r'```(?:latex)?\n?(.*?)\n?```', r'\1', latex, flags=re.DOTALL)

            return latex.strip()

        except Exception as e:
            print(f"    ✗ Error converting equation to LaTeX: {e}")
            return None

    def process_pdf_equations(
        self,
        pdf_path: Path,
        output_dir: Path,
        page_range: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Complete pipeline: extract all equations from PDF.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for equation images
            page_range: Optional (start_page, end_page) tuple (0-indexed)

        Returns:
            List of all extracted equations
        """
        print(f"  📐 Extracting equations from: {pdf_path.name}")

        all_equations = []

        # Step 1: Try text extraction first (fast)
        text_equations = self.extract_equations_from_text(pdf_path)
        if text_equations:
            print(f"    ✓ Found {len(text_equations)} equations in PDF text")
            all_equations.extend(text_equations)

        # Step 2: Visual detection using GPT-4V
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()

        # Determine page range
        if page_range:
            start_page, end_page = page_range
            start_page = max(0, start_page)
            end_page = min(num_pages, end_page)
        else:
            # For efficiency, only process first 10 pages by default
            # (Can be changed to process all pages if needed)
            start_page = 0
            end_page = min(10, num_pages)

        print(f"    🔍 Scanning pages {start_page + 1}-{end_page} for equation regions...")

        equation_counter = 0

        for page_num in range(start_page, end_page):
            detected_equations = self.detect_equation_regions(pdf_path, page_num)

            if detected_equations:
                print(f"      Page {page_num + 1}: Found {len(detected_equations)} equation(s)")

            for eq_data in detected_equations:
                equation_counter += 1
                eq_id = f"{pdf_path.stem}_p{page_num + 1}_eq{equation_counter}"

                # Extract equation image
                bbox = eq_data.get("bbox")
                if bbox:
                    img_path = self.extract_equation_image(
                        pdf_path, page_num, bbox, output_dir, eq_id
                    )

                    # If GPT-4V didn't provide LaTeX, try OCR
                    latex = eq_data.get("latex")
                    if not latex and img_path:
                        latex = self.ocr_equation_to_latex(img_path)

                    all_equations.append({
                        "page": page_num + 1,
                        "type": eq_data.get("type", "unknown"),
                        "latex": latex or "",
                        "number": eq_data.get("number"),
                        "bbox": bbox,
                        "image_path": str(img_path) if img_path else None,
                        "source": "vision_detection",
                        "confidence": eq_data.get("confidence", 0.0)
                    })

        print(f"    ✅ Extracted {len(all_equations)} equations total")

        return all_equations
