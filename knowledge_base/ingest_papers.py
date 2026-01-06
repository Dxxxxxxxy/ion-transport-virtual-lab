"""
PDF Ingestion Script for Ion Transport Knowledge Base

This script processes PDF papers from domain-specific folders, extracts comprehensive
content (text, figures, tables, equations), chunks them, generates embeddings, and
stores them in ChromaDB for RAG-based retrieval.

Usage:
    python -m ion_transport.knowledge_base.ingest_papers

Features:
- Extracts full PDF content including figures, captions, tables, and equations
- Chunks content intelligently (configurable size)
- Generates OpenAI embeddings
- Stores in domain-specific ChromaDB collections
- Preserves metadata (title, authors, year, domain, page numbers)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import hashlib
from tqdm import tqdm
import fitz  # PyMuPDF
import requests
import re
import time
import json

# Import multimodal modules
try:
    from ion_transport.knowledge_base.multimodal_extractor import MultimodalExtractor
    from ion_transport.knowledge_base.multimodal_embeddings import MultimodalEmbedder
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False
    print("⚠️  Multimodal modules not found. Running in text-only mode.")


# Configuration
CHUNK_SIZE = 1000  # tokens per chunk (adjustable)
CHUNK_OVERLAP = 200  # overlap between chunks
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model

# Domain folders
DOMAINS = {
    "electrochemistry": "Electrochemistry (Supercapacitors, CDI, EDL)",
    "membrane_science": "Membrane Science (Desalination, Ion Separation)",
    "biology": "Biology (Ion Channels: K+, Na+, Ca2+)",
    "nanofluidics": "Nanofluidics (Synthetic Nanopores, Nanochannels)",
}


class CitationExtractor:
    """Extracts citation metadata from PDF files."""

    def __init__(self):
        """Initialize citation extractor."""
        self.crossref_base_url = "https://api.crossref.org/works"

    def extract_doi_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """
        Extract DOI from PDF metadata or content.

        Args:
            pdf_path: Path to PDF file

        Returns:
            DOI string or None
        """
        try:
            # Open PDF
            doc = fitz.open(pdf_path)

            # Try to get DOI from metadata
            metadata = doc.metadata
            if metadata:
                # Check various metadata fields
                for key in ['subject', 'keywords', 'doi']:
                    if key in metadata and metadata[key]:
                        doi_match = re.search(r'10\.\d{4,}/[^\s]+', metadata[key])
                        if doi_match:
                            doc.close()
                            return doi_match.group(0)

            # Search first 3 pages for DOI
            doi_pattern = r'10\.\d{4,}/[^\s\]\)>"]+'
            for page_num in range(min(3, len(doc))):
                page = doc[page_num]
                text = page.get_text()

                # Look for DOI
                doi_match = re.search(doi_pattern, text, re.IGNORECASE)
                if doi_match:
                    doi = doi_match.group(0)
                    # Clean up common endings
                    doi = doi.rstrip('.,;:')
                    doc.close()
                    return doi

            doc.close()
            return None

        except Exception as e:
            print(f"      Warning: Could not extract DOI: {e}")
            return None

    def query_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Query CrossRef API for citation information.

        Args:
            doi: DOI string

        Returns:
            Dictionary with citation info or None
        """
        try:
            url = f"{self.crossref_base_url}/{doi}"
            headers = {'User-Agent': 'Ion-Transport-RAG/1.0 (mailto:researcher@example.com)'}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('message', {})
            else:
                return None

        except Exception as e:
            print(f"      Warning: CrossRef query failed: {e}")
            return None

    def extract_from_pdf_text(self, pdf_path: Path) -> Dict[str, str]:
        """
        Extract title and authors from PDF first page.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with 'title' and 'authors'
        """
        try:
            doc = fitz.open(pdf_path)

            if len(doc) == 0:
                doc.close()
                return {}

            # Get first page text
            first_page = doc[0].get_text()
            lines = [line.strip() for line in first_page.split('\n') if line.strip()]

            # Title is usually in first few lines and is longer
            title = None
            for i, line in enumerate(lines[:10]):
                if len(line) > 20 and not line.lower().startswith(('doi:', 'http', 'www')):
                    title = line
                    break

            doc.close()

            return {'title': title or 'Unknown'}

        except Exception as e:
            print(f"      Warning: Could not extract text metadata: {e}")
            return {'title': 'Unknown'}

    def format_citation(self, citation_data: Dict[str, Any]) -> str:
        """
        Format citation as: Journal abbreviation (Year), Volume, Pages

        Args:
            citation_data: Citation data from CrossRef

        Returns:
            Formatted citation string
        """
        try:
            # Extract components
            journal = citation_data.get('short-container-title', [])
            if journal:
                journal_abbr = journal[0]
            else:
                # Fall back to full title
                journal_full = citation_data.get('container-title', ['Unknown Journal'])
                journal_abbr = journal_full[0]

            # Year
            published = citation_data.get('published-print') or citation_data.get('published-online')
            if published and 'date-parts' in published:
                year = published['date-parts'][0][0]
            else:
                year = 'n.d.'

            # Volume
            volume = citation_data.get('volume', '')

            # Pages
            page = citation_data.get('page', '')

            # Format
            if volume and page:
                citation = f"{journal_abbr} ({year}), {volume}, {page}"
            elif volume:
                citation = f"{journal_abbr} ({year}), {volume}"
            else:
                citation = f"{journal_abbr} ({year})"

            return citation

        except Exception as e:
            print(f"      Warning: Could not format citation: {e}")
            return "Citation unavailable"

    def extract_citation_metadata(self, pdf_path: Path) -> Dict[str, str]:
        """
        Extract comprehensive citation metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with citation metadata
        """
        metadata = {
            'title': 'Unknown',
            'authors': 'Unknown',
            'year': 'Unknown',
            'journal': 'Unknown',
            'citation': 'Unknown',
            'doi': None,
        }

        # Try to extract DOI
        doi = self.extract_doi_from_pdf(pdf_path)

        if doi:
            metadata['doi'] = doi
            print(f"      ✓ Found DOI: {doi}")

            # Query CrossRef
            crossref_data = self.query_crossref(doi)

            if crossref_data:
                # Extract title
                title = crossref_data.get('title', [])
                if title:
                    metadata['title'] = title[0]

                # Extract authors
                authors_list = crossref_data.get('author', [])
                if authors_list:
                    first_author = authors_list[0]
                    family = first_author.get('family', '')
                    if len(authors_list) > 1:
                        metadata['authors'] = f"{family} et al."
                    else:
                        metadata['authors'] = family

                # Extract year
                published = crossref_data.get('published-print') or crossref_data.get('published-online')
                if published and 'date-parts' in published:
                    metadata['year'] = str(published['date-parts'][0][0])

                # Extract journal
                journal = crossref_data.get('short-container-title', [])
                if journal:
                    metadata['journal'] = journal[0]
                else:
                    container = crossref_data.get('container-title', [])
                    if container:
                        metadata['journal'] = container[0]

                # Format citation
                metadata['citation'] = self.format_citation(crossref_data)
                print(f"      ✓ Citation: {metadata['citation']}")

                # Rate limiting
                time.sleep(0.5)

        else:
            # Fall back to extracting from PDF text
            print(f"      ⚠ No DOI found, extracting from PDF text")
            text_metadata = self.extract_from_pdf_text(pdf_path)
            metadata.update(text_metadata)

        return metadata


class PDFIngester:
    """Handles PDF ingestion, processing, and storage in ChromaDB."""

    def __init__(self, base_dir: Path, vector_db_dir: Path, enable_multimodal: bool = True):
        """
        Initialize PDF ingester.

        Args:
            base_dir: Path to knowledge_base directory
            vector_db_dir: Path to vector database storage
            enable_multimodal: Whether to enable multimodal figure extraction
        """
        self.base_dir = base_dir
        self.pdf_dir = base_dir.parent / "data" / "pdfs"
        self.vector_db_dir = vector_db_dir
        self.enable_multimodal = enable_multimodal and MULTIMODAL_AVAILABLE

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(vector_db_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Initialize citation extractor
        self.citation_extractor = CitationExtractor()

        # Initialize multimodal components
        if self.enable_multimodal:
            image_output_dir = base_dir.parent / "data" / "extracted_figures"
            self.multimodal_extractor = MultimodalExtractor(image_output_dir)
            self.multimodal_embedder = MultimodalEmbedder()
            print("✓ Multimodal RAG enabled: Figures will be extracted and analyzed")
        else:
            self.multimodal_extractor = None
            self.multimodal_embedder = None
            if MULTIMODAL_AVAILABLE:
                print("ℹ️  Multimodal RAG disabled: Text-only mode")

    def get_or_create_collection(self, domain: str):
        """Get or create ChromaDB collection for a domain."""
        collection_name = f"{domain}_papers"
        try:
            collection = self.client.get_collection(name=collection_name)
            print(f"✓ Using existing collection: {collection_name}")
        except Exception as e:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"domain": domain, "description": DOMAINS.get(domain, "")}
            )
            print(f"✓ Created new collection: {collection_name}")
        return collection

    def get_already_processed_pdfs(self, collection) -> set:
        """
        Get set of filenames that have already been processed in this collection.

        Args:
            collection: ChromaDB collection

        Returns:
            Set of filenames (e.g., {'paper1.pdf', 'paper2.pdf'})
        """
        try:
            # Get all documents in the collection
            count = collection.count()

            if count == 0:
                return set()

            # Retrieve all metadata (in batches if necessary)
            result = collection.get(limit=count, include=['metadatas'])

            # Extract unique filenames from metadata
            filenames = set()
            if result and 'metadatas' in result:
                for metadata in result['metadatas']:
                    if metadata and 'filename' in metadata:
                        filenames.add(metadata['filename'])

            return filenames

        except Exception as e:
            print(f"    ⚠ Warning: Could not check existing PDFs: {e}")
            return set()

    def extract_pdf_metadata(self, pdf_path: Path) -> Dict[str, str]:
        """
        Extract comprehensive metadata from PDF including citation information.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with citation metadata
        """
        domain = pdf_path.parent.name

        # Basic metadata
        metadata = {
            "filename": pdf_path.name,
            "domain": domain,
            "file_path": str(pdf_path),
        }

        # Extract citation metadata using CitationExtractor
        citation_metadata = self.citation_extractor.extract_citation_metadata(pdf_path)

        # Merge citation metadata
        metadata.update(citation_metadata)

        return metadata

    def process_pdf(self, pdf_path: Path, domain: str) -> List[Dict[str, Any]]:
        """
        Process a single PDF file and extract all content.

        Args:
            pdf_path: Path to PDF file
            domain: Domain category

        Returns:
            List of document chunks with metadata
        """
        print(f"  Processing: {pdf_path.name}")

        try:
            # Use PyMuPDF (fitz) for text extraction
            doc = fitz.open(pdf_path)

            # Extract text from all pages
            full_text = ""
            num_pages = len(doc)
            for page_num in range(num_pages):
                page = doc[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n\n"

            doc.close()

            # Extract metadata
            base_metadata = self.extract_pdf_metadata(pdf_path)

            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)

            # Create document chunks with metadata
            doc_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = base_metadata.copy()
                chunk_metadata.update({
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                    "char_count": len(chunk),
                })

                doc_chunks.append({
                    "text": chunk,
                    "metadata": chunk_metadata,
                })

            print(f"    ✓ Extracted {len(chunks)} chunks from {num_pages} pages")
            return doc_chunks

        except Exception as e:
            print(f"    ✗ Error processing {pdf_path.name}: {str(e)}")
            return []

    def process_pdf_figures(self, pdf_path: Path, domain: str, base_metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Process figures from a PDF using multimodal analysis.

        Args:
            pdf_path: Path to PDF file
            domain: Domain category
            base_metadata: Base metadata from PDF

        Returns:
            List of figure chunks with embeddings
        """
        if not self.enable_multimodal or not self.multimodal_extractor:
            return []

        try:
            # Extract and analyze all figures
            figures = self.multimodal_extractor.process_pdf_multimodal(pdf_path, domain)

            if not figures:
                return []

            # Process each figure into a searchable chunk
            figure_chunks = []

            for fig_idx, figure_data in enumerate(figures):
                # Create rich text representation of the figure
                text_parts = []

                # Add caption
                if figure_data.get("caption"):
                    text_parts.append(f"Figure Caption: {figure_data['caption']}")

                # Add vision analysis
                if "vision_analysis" in figure_data:
                    analysis = figure_data["vision_analysis"]

                    if "figure_type" in analysis:
                        text_parts.append(f"Figure Type: {analysis['figure_type']}")

                    if "description" in analysis:
                        text_parts.append(f"Description: {analysis['description']}")

                    if "key_insights" in analysis:
                        insights = analysis["key_insights"]
                        if isinstance(insights, list):
                            text_parts.append(f"Key Insights: {'; '.join(insights)}")

                    if "approximate_values" in analysis:
                        text_parts.append(f"Approximate Values: {analysis['approximate_values']}")

                    if "variables" in analysis:
                        text_parts.append(f"Variables: {json.dumps(analysis['variables'])}")

                # Add plot data if available
                if figure_data.get("plot_data"):
                    plot_data = figure_data["plot_data"]
                    text_parts.append(f"Plot Data: {json.dumps(plot_data)}")

                # Combine all text
                figure_text = "\n".join(text_parts)

                # Create metadata
                figure_metadata = base_metadata.copy()
                figure_metadata.update({
                    "content_type": "figure",
                    "figure_index": fig_idx,
                    "page_number": figure_data["image_metadata"]["page_number"],
                    "image_filename": figure_data["image_metadata"]["filename"],
                    "image_path": figure_data["image_metadata"]["path"],
                    "figure_type": figure_data.get("vision_analysis", {}).get("figure_type", "Unknown"),
                    "has_plot_data": figure_data.get("plot_data") is not None,
                })

                # Generate embedding using multimodal embedder
                embedding = self.multimodal_embedder.embed_figure_content(
                    figure_data.get("vision_analysis", {}),
                    figure_data.get("caption")
                )

                figure_chunks.append({
                    "text": figure_text,
                    "metadata": figure_metadata,
                    "embedding": embedding,
                    "figure_data": figure_data,  # Store full figure data for reference
                })

            print(f"    ✓ Created {len(figure_chunks)} searchable figure chunks")
            return figure_chunks

        except Exception as e:
            print(f"    ✗ Error processing figures: {str(e)}")
            return []

    def process_pdf_equations(
        self,
        pdf_path: Path,
        domain: str,
        base_metadata: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Process equations from a PDF.

        Args:
            pdf_path: Path to PDF file
            domain: Domain category
            base_metadata: Base metadata from PDF

        Returns:
            List of equation chunks with embeddings
        """
        if not self.enable_multimodal or not self.multimodal_extractor:
            return []

        try:
            # Extract equations using multimodal extractor
            equations = self.multimodal_extractor.process_pdf_equations(pdf_path, domain)

            if not equations:
                return []

            # Process each equation into a searchable chunk
            equation_chunks = []

            for eq_idx, equation_data in enumerate(equations):
                # Create text representation of equation
                text_parts = []

                # Add LaTeX equation
                latex = equation_data.get("latex", "")
                if latex:
                    text_parts.append(f"Equation (LaTeX): {latex}")

                # Add equation type
                eq_type = equation_data.get("type", "unknown")
                text_parts.append(f"Type: {eq_type} equation")

                # Add equation number if present
                eq_number = equation_data.get("number")
                if eq_number:
                    text_parts.append(f"Equation number: {eq_number}")

                # Add page number
                page = equation_data.get("page", 0)
                text_parts.append(f"Page: {page}")

                # Combine all text
                equation_text = "\n".join(text_parts)

                # Create metadata
                equation_metadata = base_metadata.copy()
                equation_metadata.update({
                    "content_type": "equation",
                    "equation_index": eq_idx,
                    "page_number": page,
                    "equation_type": eq_type,
                    "equation_number": eq_number,
                    "latex": latex,
                    "has_image": equation_data.get("image_path") is not None,
                    "image_path": equation_data.get("image_path", ""),
                    "source": equation_data.get("source", "unknown"),
                })

                # Generate embedding for equation text
                embedding = self.embeddings.embed_query(equation_text)

                equation_chunks.append({
                    "text": equation_text,
                    "metadata": equation_metadata,
                    "embedding": embedding,
                    "equation_data": equation_data,
                })

            print(f"    ✓ Created {len(equation_chunks)} searchable equation chunks")
            return equation_chunks

        except Exception as e:
            print(f"    ✗ Error processing equations: {str(e)}")
            return []

    def generate_doc_id(self, text: str, metadata: Dict) -> str:
        """Generate unique ID for document chunk."""
        content_type = metadata.get('content_type', 'text')

        if content_type == 'figure':
            unique_string = f"{metadata['filename']}_figure_{metadata['figure_index']}_{text[:50]}"
        elif content_type == 'equation':
            unique_string = f"{metadata['filename']}_equation_{metadata['equation_index']}_{text[:50]}"
        else:
            chunk_id = metadata.get('chunk_id', 0)
            unique_string = f"{metadata['filename']}_{chunk_id}_{text[:100]}"

        return hashlib.md5(unique_string.encode()).hexdigest()

    def ingest_domain(self, domain: str) -> int:
        """
        Ingest all PDFs from a domain folder.

        Args:
            domain: Domain name (electrochemistry, membrane_science, etc.)

        Returns:
            Number of documents ingested
        """
        domain_dir = self.pdf_dir / domain

        if not domain_dir.exists():
            print(f"✗ Domain directory not found: {domain_dir}")
            return 0

        # Get all PDF files
        all_pdf_files = list(domain_dir.glob("*.pdf"))

        if not all_pdf_files:
            print(f"⚠ No PDF files found in {domain}/")
            return 0

        # Get or create collection
        collection = self.get_or_create_collection(domain)

        # Get already-processed PDFs
        already_processed = self.get_already_processed_pdfs(collection)

        # Filter to only new PDFs
        pdf_files = [pdf for pdf in all_pdf_files if pdf.name not in already_processed]

        print(f"\n{'='*80}")
        print(f"📚 Domain: {domain}/")
        print(f"   Total PDFs in folder: {len(all_pdf_files)}")
        print(f"   Already processed: {len(already_processed)}")
        print(f"   New PDFs to ingest: {len(pdf_files)}")
        print(f"{'='*80}")

        if not pdf_files:
            print(f"✓ No new PDFs to process in {domain}/")
            return 0

        total_chunks = 0
        total_figures = 0
        total_equations = 0

        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc=f"Ingesting {domain}"):
            # Process text chunks
            doc_chunks = self.process_pdf(pdf_path, domain)

            if not doc_chunks:
                continue

            # Get base metadata for figures
            base_metadata = self.extract_pdf_metadata(pdf_path) if doc_chunks else {}

            # Process figures if multimodal is enabled
            figure_chunks = []
            if self.enable_multimodal:
                figure_chunks = self.process_pdf_figures(pdf_path, domain, base_metadata)

            # Process equations if multimodal is enabled
            equation_chunks = []
            if self.enable_multimodal:
                equation_chunks = self.process_pdf_equations(pdf_path, domain, base_metadata)

            # Combine text, figure, and equation chunks
            all_chunks = doc_chunks + figure_chunks + equation_chunks

            if not all_chunks:
                continue

            # Prepare data for ChromaDB (text chunks)
            if doc_chunks:
                texts = [chunk["text"] for chunk in doc_chunks]
                metadatas = [chunk["metadata"] for chunk in doc_chunks]
                ids = [self.generate_doc_id(chunk["text"], chunk["metadata"])
                       for chunk in doc_chunks]

                # Generate embeddings for text
                try:
                    embeddings = self.embeddings.embed_documents(texts)

                    # Add text chunks to collection
                    collection.add(
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids,
                    )

                    total_chunks += len(doc_chunks)

                except Exception as e:
                    print(f"    ✗ Error adding text to database: {str(e)}")

            # Add figure chunks to collection (they already have embeddings)
            if figure_chunks:
                fig_texts = [chunk["text"] for chunk in figure_chunks]
                fig_metadatas = [chunk["metadata"] for chunk in figure_chunks]
                fig_embeddings = [chunk["embedding"] for chunk in figure_chunks]
                fig_ids = [self.generate_doc_id(chunk["text"], chunk["metadata"])
                           for chunk in figure_chunks]

                try:
                    # Add figure chunks to collection
                    collection.add(
                        embeddings=fig_embeddings,
                        documents=fig_texts,
                        metadatas=fig_metadatas,
                        ids=fig_ids,
                    )

                    total_figures += len(figure_chunks)

                except Exception as e:
                    print(f"    ✗ Error adding figures to database: {str(e)}")

            # Add equation chunks to collection (they already have embeddings)
            if equation_chunks:
                eq_texts = [chunk["text"] for chunk in equation_chunks]
                eq_metadatas = [chunk["metadata"] for chunk in equation_chunks]
                eq_embeddings = [chunk["embedding"] for chunk in equation_chunks]
                eq_ids = [self.generate_doc_id(chunk["text"], chunk["metadata"])
                          for chunk in equation_chunks]

                try:
                    # Add equation chunks to collection
                    collection.add(
                        embeddings=eq_embeddings,
                        documents=eq_texts,
                        metadatas=eq_metadatas,
                        ids=eq_ids,
                    )

                    total_equations += len(equation_chunks)

                except Exception as e:
                    print(f"    ✗ Error adding equations to database: {str(e)}")

        summary = f"\n✓ Ingested {total_chunks} text chunks from {len(pdf_files)} new papers"
        if total_figures > 0:
            summary += f"\n✓ Ingested {total_figures} figure chunks with multimodal analysis"
        if total_equations > 0:
            summary += f"\n✓ Ingested {total_equations} equation chunks with LaTeX conversion"
        print(summary)

        return total_chunks + total_figures + total_equations

    def ingest_all(self):
        """Ingest PDFs from all domain folders."""
        print("\n" + "="*80)
        print("🚀 ION TRANSPORT KNOWLEDGE BASE INGESTION")
        print("="*80)
        print(f"\nPDF Directory: {self.pdf_dir}")
        print(f"Vector DB: {self.vector_db_dir}")
        print(f"Chunk Size: {CHUNK_SIZE} tokens")
        print(f"Chunk Overlap: {CHUNK_OVERLAP} tokens")
        print(f"Embedding Model: {EMBEDDING_MODEL}")
        print(f"Multimodal RAG: {'✓ ENABLED (figures will be extracted & analyzed)' if self.enable_multimodal else '✗ Disabled (text-only mode)'}")

        total_chunks_all = 0

        for domain in DOMAINS.keys():
            chunks = self.ingest_domain(domain)
            total_chunks_all += chunks

        print("\n" + "="*80)
        print(f"✅ INGESTION COMPLETE")
        print("="*80)
        print(f"Total chunks across all domains: {total_chunks_all}")
        print(f"\nYou can now query the knowledge base using query_rag.py")

    def get_collection_stats(self):
        """Print statistics about all collections."""
        print("\n" + "="*80)
        print("📊 KNOWLEDGE BASE STATISTICS")
        print("="*80)

        for domain in DOMAINS.keys():
            collection_name = f"{domain}_papers"
            try:
                collection = self.client.get_collection(name=collection_name)
                count = collection.count()
                print(f"\n{domain.upper()}:")
                print(f"  Collection: {collection_name}")
                print(f"  Documents: {count}")
            except Exception as e:
                print(f"\n{domain.upper()}:")
                print(f"  Collection: Not created yet")


def main():
    """Main entry point."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Ingest PDF papers into knowledge base with optional multimodal processing"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics only (no ingestion)"
    )
    parser.add_argument(
        "--multimodal",
        action="store_true",
        default=True,
        help="Enable multimodal RAG (extract and analyze figures) - DEFAULT"
    )
    parser.add_argument(
        "--no-multimodal",
        dest="multimodal",
        action="store_false",
        help="Disable multimodal RAG (text-only mode)"
    )

    args = parser.parse_args()

    # Get paths
    current_dir = Path(__file__).parent
    base_dir = current_dir  # knowledge_base/
    vector_db_dir = current_dir.parent / "data" / "vector_db"  # ion_transport/data/vector_db/

    # Create vector_db directory if it doesn't exist
    vector_db_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ingester with multimodal option
    ingester = PDFIngester(base_dir, vector_db_dir, enable_multimodal=args.multimodal)

    # Check if user wants to see stats or ingest
    if args.stats:
        ingester.get_collection_stats()
    else:
        # Run ingestion
        ingester.ingest_all()

        # Show stats after ingestion
        ingester.get_collection_stats()


if __name__ == "__main__":
    main()
