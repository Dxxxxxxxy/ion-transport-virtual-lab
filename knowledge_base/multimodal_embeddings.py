"""
Multimodal Embeddings for Images and Text

Uses OpenAI's CLIP-based embeddings or alternatives for creating
unified vector representations of images and text.

Author: Ion Transport Virtual Lab
"""

from pathlib import Path
from typing import List, Union
import base64
from openai import OpenAI
from PIL import Image
import io


class MultimodalEmbedder:
    """Generate multimodal embeddings for images and text."""

    def __init__(self, model: str = "clip"):
        """
        Initialize multimodal embedder.

        Args:
            model: Embedding model to use ("clip" or "openai")
        """
        self.model_type = model
        self.client = OpenAI()

        # OpenAI doesn't have a direct CLIP API, but we can use GPT-4V for image understanding
        # and combine with text embeddings, or use a local CLIP model

    def embed_image(self, image_path: Path) -> List[float]:
        """
        Generate embedding vector for an image.

        Args:
            image_path: Path to image file

        Returns:
            Embedding vector
        """
        try:
            # For now, we'll create a rich text description using GPT-4V
            # and then embed that description
            # In production, you'd want to use actual CLIP embeddings

            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Get compact description for embedding
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this scientific figure in one detailed sentence that captures all key information for semantic search."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,
                temperature=0.1,
            )

            description = response.choices[0].message.content

            # Now embed the description using OpenAI's text embedding model
            embedding_response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=description
            )

            return embedding_response.data[0].embedding

        except Exception as e:
            print(f"    ✗ Error creating image embedding: {e}")
            # Return zero vector if embedding fails
            return [0.0] * 1536  # text-embedding-3-small dimension

    def embed_figure_content(
        self,
        figure_analysis: dict,
        caption: str = None
    ) -> List[float]:
        """
        Generate embedding for figure content (description + caption + data).

        Args:
            figure_analysis: Vision analysis results
            caption: Figure caption

        Returns:
            Embedding vector
        """
        # Combine all text information
        text_parts = []

        if caption:
            text_parts.append(f"Caption: {caption}")

        if "description" in figure_analysis:
            text_parts.append(f"Description: {figure_analysis['description']}")

        if "key_insights" in figure_analysis:
            insights = figure_analysis["key_insights"]
            if isinstance(insights, list):
                text_parts.append(f"Key insights: {'; '.join(insights)}")
            else:
                text_parts.append(f"Key insights: {insights}")

        if "approximate_values" in figure_analysis:
            text_parts.append(f"Values: {figure_analysis['approximate_values']}")

        if "variables" in figure_analysis:
            vars_str = str(figure_analysis["variables"])
            text_parts.append(f"Variables: {vars_str}")

        # Combine all parts
        combined_text = " | ".join(text_parts)

        try:
            # Create embedding
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=combined_text
            )

            return response.data[0].embedding

        except Exception as e:
            print(f"    ✗ Error creating text embedding: {e}")
            return [0.0] * 1536

    def embed_hybrid(
        self,
        image_path: Path,
        text_description: str,
        weight_image: float = 0.5,
        weight_text: float = 0.5
    ) -> List[float]:
        """
        Create hybrid embedding combining image and text.

        Args:
            image_path: Path to image file
            text_description: Text description
            weight_image: Weight for image embedding
            weight_text: Weight for text embedding

        Returns:
            Weighted average embedding vector
        """
        import numpy as np

        # Get both embeddings
        img_embedding = self.embed_image(image_path)
        txt_embedding = self.embed_text(text_description)

        # Weighted average
        img_array = np.array(img_embedding)
        txt_array = np.array(txt_embedding)

        hybrid = (weight_image * img_array + weight_text * txt_array)

        # Normalize
        hybrid = hybrid / np.linalg.norm(hybrid)

        return hybrid.tolist()

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"    ✗ Error creating text embedding: {e}")
            return [0.0] * 1536
