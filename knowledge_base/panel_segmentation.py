"""
Multi-Panel Figure Segmentation Module

This module detects and extracts individual panels from multi-panel scientific figures
using GPT-4 Vision to identify panel layouts and bounding boxes.

Features:
- Automatic panel detection (a, b, c, d, etc.)
- Bounding box extraction using GPT-4V
- Individual panel cropping
- Sub-caption matching

Author: Ion Transport Virtual Lab
"""

import base64
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io
from openai import OpenAI


class PanelSegmenter:
    """Detects and segments multi-panel figures into individual panels."""

    def __init__(self):
        """Initialize panel segmenter."""
        self.client = OpenAI()
        self.vision_model = "gpt-4o"

    def detect_panels(
        self,
        image_path: Path,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect if image contains multiple panels and identify their locations.

        Args:
            image_path: Path to the figure image
            caption: Optional figure caption for context

        Returns:
            Dictionary with panel detection results
        """
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Get image dimensions
            img = Image.open(image_path)
            width, height = img.size

            # Construct prompt for panel detection
            prompt = f"""Analyze this scientific figure and determine if it contains multiple panels.

Image dimensions: {width}x{height} pixels

Please provide:

1. **is_multi_panel**: (true/false) Does this figure contain multiple distinct panels/subfigures?

2. **num_panels**: Number of panels if multi-panel (e.g., 2, 3, 4)

3. **layout**: Description of layout (e.g., "2x2 grid", "horizontal row", "vertical column", "irregular")

4. **panel_labels**: List of panel labels if visible (e.g., ["a", "b", "c", "d"] or ["A", "B", "C"])

5. **panels**: Array of panel information, where each panel has:
   - label: Panel identifier (e.g., "a", "b", "1", "2")
   - bbox: Bounding box as [x_min, y_min, x_max, y_max] in pixels
   - description: Brief description of what this panel shows (1 sentence)
   - type: Type of content (e.g., "plot", "microscopy", "schematic", "bar chart")

IMPORTANT for bounding boxes:
- Use pixel coordinates with origin (0,0) at top-left
- x increases to the right, y increases downward
- Ensure bbox coordinates are within image bounds: x_max ≤ {width}, y_max ≤ {height}
- Include a small margin around panels if possible

If caption is provided, use it to help identify panels.

Format response as JSON with keys: is_multi_panel, num_panels, layout, panel_labels, panels
"""

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
                max_tokens=1500,
                temperature=0.1,  # Low temperature for precise detection
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            try:
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)

                detection_result = json.loads(response_text)

                # Validate bounding boxes
                if detection_result.get("is_multi_panel") and "panels" in detection_result:
                    for panel in detection_result["panels"]:
                        if "bbox" in panel:
                            bbox = panel["bbox"]
                            # Ensure bbox is within bounds
                            bbox[0] = max(0, min(bbox[0], width))
                            bbox[1] = max(0, min(bbox[1], height))
                            bbox[2] = max(0, min(bbox[2], width))
                            bbox[3] = max(0, min(bbox[3], height))

                return detection_result

            except json.JSONDecodeError:
                return {
                    "is_multi_panel": False,
                    "num_panels": 1,
                    "error": "Could not parse panel detection response",
                    "raw_response": response_text
                }

        except Exception as e:
            print(f"    ✗ Error detecting panels: {e}")
            return {
                "is_multi_panel": False,
                "num_panels": 1,
                "error": str(e)
            }

    def extract_panels(
        self,
        image_path: Path,
        detection_result: Dict[str, Any],
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Extract individual panels from a multi-panel figure.

        Args:
            image_path: Path to original figure
            detection_result: Panel detection result from detect_panels()
            output_dir: Directory to save extracted panels

        Returns:
            List of extracted panel information
        """
        if not detection_result.get("is_multi_panel"):
            # Not a multi-panel figure, return original
            return [{
                "label": "full",
                "path": str(image_path),
                "is_panel": False,
                "bbox": None
            }]

        try:
            # Load original image
            img = Image.open(image_path)
            width, height = img.size

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            extracted_panels = []
            base_filename = image_path.stem

            # Extract each panel
            for panel_info in detection_result.get("panels", []):
                label = panel_info.get("label", "unknown")
                bbox = panel_info.get("bbox")

                if bbox is None or len(bbox) != 4:
                    continue

                x_min, y_min, x_max, y_max = bbox

                # Validate bbox
                if x_max <= x_min or y_max <= y_min:
                    print(f"    ⚠ Invalid bbox for panel {label}: {bbox}")
                    continue

                if x_max > width or y_max > height:
                    print(f"    ⚠ Bbox out of bounds for panel {label}: {bbox}")
                    continue

                # Crop panel
                try:
                    panel_img = img.crop((x_min, y_min, x_max, y_max))

                    # Save panel
                    panel_filename = f"{base_filename}_panel_{label}.png"
                    panel_path = output_dir / panel_filename

                    panel_img.save(panel_path)

                    # Store panel info
                    extracted_panels.append({
                        "label": label,
                        "path": str(panel_path),
                        "is_panel": True,
                        "bbox": bbox,
                        "description": panel_info.get("description", ""),
                        "type": panel_info.get("type", "unknown"),
                        "original_image": str(image_path)
                    })

                    print(f"      ✓ Extracted panel '{label}': {panel_filename}")

                except Exception as e:
                    print(f"    ✗ Error cropping panel {label}: {e}")
                    continue

            return extracted_panels

        except Exception as e:
            print(f"    ✗ Error extracting panels: {e}")
            return [{
                "label": "full",
                "path": str(image_path),
                "is_panel": False,
                "error": str(e)
            }]

    def match_panel_captions(
        self,
        caption: str,
        panel_labels: List[str]
    ) -> Dict[str, str]:
        """
        Match sub-captions to panel labels.

        Args:
            caption: Full figure caption
            panel_labels: List of detected panel labels (e.g., ["a", "b", "c"])

        Returns:
            Dictionary mapping panel labels to their captions
        """
        if not caption or not panel_labels:
            return {}

        matched_captions = {}

        # Common patterns for panel references in captions
        # e.g., "(a) SEM image...", "a. TEM image...", "Panel a: ..."
        for label in panel_labels:
            # Try multiple patterns
            patterns = [
                rf'\({label}\)\s*([^(]+?)(?=\([a-z]\)|$)',  # (a) caption text
                rf'{label}\.\s*([^.]+?)(?=[a-z]\.|$)',      # a. caption text
                rf'{label}:\s*([^:]+?)(?=[a-z]:|$)',        # a: caption text
                rf'Panel\s+{label}[:\s]+([^.]+)',           # Panel a: caption text
                rf'\b{label}\b[:\s]+([^.]+)',               # a caption text
            ]

            for pattern in patterns:
                match = re.search(pattern, caption, re.IGNORECASE)
                if match:
                    matched_captions[label] = match.group(1).strip()
                    break

        return matched_captions

    def process_figure_with_panels(
        self,
        image_path: Path,
        caption: Optional[str],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Complete pipeline: detect panels, extract them, and match captions.

        Args:
            image_path: Path to figure image
            caption: Optional figure caption
            output_dir: Directory for extracted panels

        Returns:
            Dictionary with all panel information
        """
        print(f"    🔍 Detecting panels in: {image_path.name}")

        # Step 1: Detect panels
        detection_result = self.detect_panels(image_path, caption)

        is_multi_panel = detection_result.get("is_multi_panel", False)
        num_panels = detection_result.get("num_panels", 1)

        if is_multi_panel:
            print(f"      ✓ Multi-panel figure detected: {num_panels} panels")
            print(f"        Layout: {detection_result.get('layout', 'unknown')}")
        else:
            print(f"      ℹ Single-panel figure")

        # Step 2: Extract panels
        extracted_panels = self.extract_panels(image_path, detection_result, output_dir)

        # Step 3: Match captions
        panel_captions = {}
        if is_multi_panel and caption:
            panel_labels = detection_result.get("panel_labels", [])
            panel_captions = self.match_panel_captions(caption, panel_labels)

        # Combine all information
        result = {
            "original_image": str(image_path),
            "is_multi_panel": is_multi_panel,
            "num_panels": num_panels,
            "layout": detection_result.get("layout", "single"),
            "panels": []
        }

        for panel_info in extracted_panels:
            label = panel_info.get("label")
            result["panels"].append({
                **panel_info,
                "sub_caption": panel_captions.get(label, "")
            })

        return result
