"""
Multimodal Content Extractor for Scientific Papers

This module extracts and processes figures, plots, and images from PDF papers:
1. Extract images using PyMuPDF
2. Generate descriptions using GPT-4 Vision
3. Extract numerical data from plots
4. Generate multimodal embeddings using CLIP
5. Segment multi-panel figures into individual panels
6. Extract equations with LaTeX conversion

Author: Ion Transport Virtual Lab
"""

import base64
import io
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from openai import OpenAI
import re

# Import new modules for panel segmentation and equation extraction
try:
    from ion_transport.knowledge_base.panel_segmentation import PanelSegmenter
    from ion_transport.knowledge_base.equation_extractor import EquationExtractor
    PANEL_SEGMENTATION_AVAILABLE = True
except ImportError:
    PANEL_SEGMENTATION_AVAILABLE = False


class MultimodalExtractor:
    """Extracts and processes multimodal content from scientific PDFs."""

    def __init__(self, image_output_dir: Path, enable_panel_segmentation: bool = True):
        """
        Initialize multimodal extractor.

        Args:
            image_output_dir: Directory to save extracted images
            enable_panel_segmentation: Enable multi-panel figure segmentation
        """
        self.image_output_dir = image_output_dir
        self.image_output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize OpenAI client for GPT-4V
        self.client = OpenAI()

        # Vision model for figure analysis
        self.vision_model = "gpt-4o"  # GPT-4V with vision capabilities

        # Initialize panel segmentation and equation extraction
        self.enable_panel_segmentation = enable_panel_segmentation and PANEL_SEGMENTATION_AVAILABLE
        if self.enable_panel_segmentation:
            self.panel_segmenter = PanelSegmenter()
            self.equation_extractor = EquationExtractor()
            print("    ✓ Panel segmentation and equation extraction enabled")
        else:
            self.panel_segmenter = None
            self.equation_extractor = None

    def should_extract_image(
        self,
        width: int,
        height: int,
        size_bytes: int,
        ext: str
    ) -> tuple[bool, str]:
        """
        Intelligent multi-criteria filtering for scientific figures.

        Uses multiple signals to distinguish meaningful figures from
        decorative elements, icons, and noise.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            size_bytes: File size in bytes
            ext: Image extension/format

        Returns:
            Tuple of (should_extract: bool, reason: str)
        """
        # Calculate metrics
        area = width * height
        aspect_ratio = max(width, height) / min(width, height) if min(width, height) > 0 else 999
        min_dimension = min(width, height)
        max_dimension = max(width, height)

        # Filter 1: Exclude tiny images (icons, bullets, decorative elements)
        if max_dimension < 50:
            return False, f"too small (max dimension {max_dimension} < 50)"

        # Filter 2: Exclude extreme aspect ratios (decorative lines, borders)
        if aspect_ratio > 20:
            return False, f"extreme aspect ratio ({aspect_ratio:.1f} > 20)"

        # Filter 3: Require minimum area for meaningful content
        MIN_AREA = 5000  # e.g., 70x70 or 100x50
        if area < MIN_AREA:
            return False, f"insufficient area ({area} < {MIN_AREA})"

        # Filter 4: For medium-sized images, check aspect ratio more strictly
        if area < 10000:  # Between 5k-10k pixels
            if aspect_ratio > 5:
                return False, f"medium image with high aspect ratio ({aspect_ratio:.1f} > 5)"

        # Filter 5: File size check (very small files are likely decorative)
        if size_bytes < 500:  # Less than 500 bytes
            return False, f"file too small ({size_bytes} bytes < 500)"

        # Filter 6: Extremely large aspect ratios even for large images
        if aspect_ratio > 10 and area < 50000:
            return False, f"elongated image ({aspect_ratio:.1f} > 10)"

        # Passed all filters
        return True, f"valid figure ({width}x{height}, area={area}, aspect={aspect_ratio:.1f})"

    def extract_images_from_pdf(
        self,
        pdf_path: Path,
        min_width: int = 100,
        min_height: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Extract all images from a PDF with metadata.

        Args:
            pdf_path: Path to PDF file
            min_width: Minimum image width in pixels (legacy, now uses intelligent filtering)
            min_height: Minimum image height in pixels (legacy, now uses intelligent filtering)

        Returns:
            List of image dictionaries with metadata
        """
        doc = fitz.open(pdf_path)
        extracted_images = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Get images on this page
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                try:
                    # Extract image
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)

                    if base_image is None:
                        continue

                    # Get image data
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    size_bytes = len(image_bytes)

                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    # Intelligent filtering
                    should_extract, reason = self.should_extract_image(
                        pil_image.width,
                        pil_image.height,
                        size_bytes,
                        image_ext
                    )

                    if not should_extract:
                        # Uncomment for debugging:
                        # print(f"    ⊗ Skipped page {page_num+1} img {img_index}: {reason}")
                        continue

                    # Generate unique filename
                    pdf_name = pdf_path.stem
                    img_filename = f"{pdf_name}_page{page_num+1}_img{img_index}.{image_ext}"
                    img_path = self.image_output_dir / img_filename

                    # Save image
                    pil_image.save(img_path)

                    # Store metadata
                    extracted_images.append({
                        "filename": img_filename,
                        "path": str(img_path),
                        "page_number": page_num + 1,
                        "image_index": img_index,
                        "width": pil_image.width,
                        "height": pil_image.height,
                        "format": image_ext,
                        "pdf_source": pdf_path.name,
                    })

                except Exception as e:
                    print(f"    ⚠ Could not extract image {img_index} from page {page_num+1}: {e}")
                    continue

        doc.close()
        return extracted_images

    def extract_figure_captions(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extract figure captions from PDF text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary mapping page numbers to captions
        """
        doc = fitz.open(pdf_path)
        captions = {}

        # Pattern to match figure captions
        caption_pattern = re.compile(
            r'(Fig(?:ure)?\.?\s+\d+[a-z]?:?\s*[^\n]+(?:\n(?!Fig)[^\n]+)*)',
            re.IGNORECASE
        )

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            # Find all captions on this page
            matches = caption_pattern.findall(text)
            if matches:
                captions[page_num + 1] = matches

        doc.close()
        return captions

    def analyze_image_with_vision(
        self,
        image_path: Path,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze image using GPT-4 Vision to extract insights.

        Args:
            image_path: Path to image file
            caption: Optional figure caption

        Returns:
            Dictionary with analysis results
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Construct prompt
            prompt = """You are a scientific figure analyzer. Analyze this figure from a research paper and provide:

1. **Figure Type**: (e.g., XY plot, bar chart, schematic diagram, microscopy image, heatmap, etc.)

2. **Detailed Description**: Describe what the figure shows in 2-3 sentences.

3. **Key Insights**: List 2-4 quantitative or qualitative insights from the figure.

4. **Approximate Values**: If this is a plot, extract approximate key values (e.g., "Peak at x=0.7nm, y=200 F/g")

5. **Variables**: List the measured/plotted variables (e.g., x-axis: pore size (nm), y-axis: capacitance (F/g))

6. **Data Extractable**: Can numerical data be extracted from this figure? (yes/no)

Format your response as JSON with keys: figure_type, description, key_insights, approximate_values, variables, data_extractable"""

            if caption:
                prompt += f"\n\nFigure caption: {caption}"

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
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.2,
            )

            # Parse response
            response_text = response.choices[0].message.content

            # Try to parse as JSON
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)

                analysis = json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, return as plain text
                analysis = {
                    "figure_type": "Unknown",
                    "description": response_text,
                    "key_insights": [],
                    "approximate_values": "",
                    "variables": {},
                    "data_extractable": False
                }

            return analysis

        except Exception as e:
            print(f"    ✗ Error analyzing image with GPT-4V: {e}")
            return {
                "figure_type": "Unknown",
                "description": f"Analysis failed: {str(e)}",
                "key_insights": [],
                "approximate_values": "",
                "variables": {},
                "data_extractable": False,
                "error": str(e)
            }

    def extract_plot_data(
        self,
        image_path: Path,
        figure_analysis: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract numerical data from plot images.

        Args:
            image_path: Path to image file
            figure_analysis: Analysis from GPT-4V

        Returns:
            Dictionary with extracted data or None
        """
        # Check if data extraction is recommended
        if not figure_analysis.get("data_extractable", False):
            return None

        figure_type = figure_analysis.get("figure_type", "").lower()

        # Only attempt for XY plots, line graphs, scatter plots
        if not any(plot_type in figure_type for plot_type in [
            "xy", "line", "scatter", "plot", "graph", "curve"
        ]):
            return None

        try:
            # Use GPT-4V for approximate data extraction
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = """Extract numerical data from this plot. Provide:

1. **Axis Information**:
   - x_axis: {label, unit, range}
   - y_axis: {label, unit, range}

2. **Data Points**: List of approximate (x, y) coordinates for key points on the main curve(s).
   Extract at least 10-20 points if possible, focusing on:
   - Peaks and valleys
   - Inflection points
   - Start and end points
   - Representative points along the curve

3. **Trends**: Describe the overall trend (increasing, decreasing, peak at, etc.)

Format as JSON with keys: axis_info, data_points, trends"""

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
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1,  # Lower temperature for numerical extraction
            )

            response_text = response.choices[0].message.content

            # Try to parse as JSON
            try:
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)

                plot_data = json.loads(response_text)
                return plot_data
            except json.JSONDecodeError:
                return {
                    "extraction_method": "vision_llm",
                    "raw_response": response_text,
                    "note": "Could not parse as structured JSON"
                }

        except Exception as e:
            print(f"    ⚠ Could not extract plot data: {e}")
            return None

    def process_pdf_multimodal(
        self,
        pdf_path: Path,
        domain: str
    ) -> List[Dict[str, Any]]:
        """
        Complete multimodal processing of a PDF.

        Args:
            pdf_path: Path to PDF file
            domain: Domain category

        Returns:
            List of processed figure data
        """
        print(f"  🖼️  Extracting multimodal content from: {pdf_path.name}")

        # Create domain-specific image directory
        domain_image_dir = self.image_output_dir / domain
        domain_image_dir.mkdir(parents=True, exist_ok=True)
        self.image_output_dir = domain_image_dir

        # Step 1: Extract images
        images = self.extract_images_from_pdf(pdf_path)
        print(f"    ✓ Extracted {len(images)} images")

        if not images:
            return []

        # Step 2: Extract captions
        captions_by_page = self.extract_figure_captions(pdf_path)

        # Step 3: Process each image
        processed_figures = []

        for img_data in images:
            img_path = Path(img_data["path"])
            page_num = img_data["page_number"]

            # Get caption for this page
            caption = None
            if page_num in captions_by_page and captions_by_page[page_num]:
                # Use first caption on the page (could be improved with better matching)
                caption = captions_by_page[page_num][0]

            print(f"    🔍 Analyzing {img_data['filename']} with GPT-4V...")

            # Check for multi-panel figures if enabled
            panel_data = None
            panels_to_process = [(img_path, caption, None)]  # Default: process as single image

            if self.enable_panel_segmentation and self.panel_segmenter:
                # Detect and extract panels
                panel_result = self.panel_segmenter.process_figure_with_panels(
                    img_path, caption, domain_image_dir / "panels"
                )

                if panel_result.get("is_multi_panel"):
                    # Multi-panel figure detected, process each panel separately
                    panels_to_process = []
                    for panel_info in panel_result.get("panels", []):
                        panel_path = Path(panel_info["path"])
                        panel_caption = panel_info.get("sub_caption") or caption
                        panels_to_process.append((panel_path, panel_caption, panel_info))

                    panel_data = panel_result

            # Process each panel (or the single image if not multi-panel)
            for panel_path, panel_caption, panel_info in panels_to_process:
                # Analyze with Vision LLM
                analysis = self.analyze_image_with_vision(panel_path, panel_caption)

                # Extract plot data if applicable
                plot_data = None
                if analysis.get("data_extractable", False):
                    print(f"    📊 Extracting plot data...")
                    plot_data = self.extract_plot_data(panel_path, analysis)

                # Combine all information
                figure_content = {
                    "image_metadata": img_data,
                    "caption": caption,
                    "panel_info": panel_info,  # None for single-panel figures
                    "panel_data": panel_data,  # Overall multi-panel info
                    "vision_analysis": analysis,
                    "plot_data": plot_data,
                    "domain": domain,
                    "pdf_source": pdf_path.name,
                    "is_panel": panel_info is not None,
                    "panel_label": panel_info.get("label") if panel_info else None,
                }

                processed_figures.append(figure_content)

        print(f"    ✅ Processed {len(processed_figures)} figures with multimodal analysis")

        return processed_figures

    def process_pdf_equations(
        self,
        pdf_path: Path,
        domain: str
    ) -> List[Dict[str, Any]]:
        """
        Extract equations from a PDF.

        Args:
            pdf_path: Path to PDF file
            domain: Domain category

        Returns:
            List of extracted equations
        """
        if not self.enable_panel_segmentation or not self.equation_extractor:
            return []

        print(f"  📐 Extracting equations from: {pdf_path.name}")

        # Create domain-specific equation directory
        domain_equation_dir = self.image_output_dir / domain / "equations"
        domain_equation_dir.mkdir(parents=True, exist_ok=True)

        # Extract equations
        equations = self.equation_extractor.process_pdf_equations(
            pdf_path,
            domain_equation_dir
        )

        return equations
