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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_openai import OpenAIEmbeddings
import hashlib
from tqdm import tqdm
import fitz  # PyMuPDF
import requests
import re
import time


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

    def __init__(self, base_dir: Path, vector_db_dir: Path):
        """
        Initialize PDF ingester.

        Args:
            base_dir: Path to knowledge_base directory
            vector_db_dir: Path to vector database storage
        """
        self.base_dir = base_dir
        self.pdf_dir = base_dir / "pdfs"
        self.vector_db_dir = vector_db_dir

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
            # Use UnstructuredPDFLoader for comprehensive extraction
            # This extracts text, tables, images, and maintains structure
            loader = UnstructuredPDFLoader(
                str(pdf_path),
                mode="elements",  # Extract individual elements
                strategy="hi_res",  # High-resolution processing for tables/figures
            )

            # Load and parse PDF
            documents = loader.load()

            # Extract metadata
            base_metadata = self.extract_pdf_metadata(pdf_path)

            # Combine all text from elements
            full_text = "\n\n".join([doc.page_content for doc in documents])

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

            print(f"    ✓ Extracted {len(chunks)} chunks from {len(documents)} elements")
            return doc_chunks

        except Exception as e:
            print(f"    ✗ Error processing {pdf_path.name}: {str(e)}")
            return []

    def generate_doc_id(self, text: str, metadata: Dict) -> str:
        """Generate unique ID for document chunk."""
        unique_string = f"{metadata['filename']}_{metadata['chunk_id']}_{text[:100]}"
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
        pdf_files = list(domain_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"⚠ No PDF files found in {domain}/")
            return 0

        print(f"\n{'='*80}")
        print(f"📚 Processing {len(pdf_files)} PDFs from {domain}/")
        print(f"{'='*80}")

        # Get or create collection
        collection = self.get_or_create_collection(domain)

        total_chunks = 0

        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc=f"Ingesting {domain}"):
            doc_chunks = self.process_pdf(pdf_path, domain)

            if not doc_chunks:
                continue

            # Prepare data for ChromaDB
            texts = [chunk["text"] for chunk in doc_chunks]
            metadatas = [chunk["metadata"] for chunk in doc_chunks]
            ids = [self.generate_doc_id(chunk["text"], chunk["metadata"])
                   for chunk in doc_chunks]

            # Generate embeddings
            try:
                embeddings = self.embeddings.embed_documents(texts)

                # Add to collection
                collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                )

                total_chunks += len(doc_chunks)

            except Exception as e:
                print(f"    ✗ Error adding to database: {str(e)}")
                continue

        print(f"\n✓ Ingested {total_chunks} chunks from {len(pdf_files)} papers")
        return total_chunks

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
    # Get paths
    current_dir = Path(__file__).parent
    base_dir = current_dir  # knowledge_base/
    vector_db_dir = current_dir.parent / "vector_db"  # ion_transport/vector_db/

    # Create vector_db directory if it doesn't exist
    vector_db_dir.mkdir(parents=True, exist_ok=True)

    # Initialize ingester
    ingester = PDFIngester(base_dir, vector_db_dir)

    # Check if user wants to see stats or ingest
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        ingester.get_collection_stats()
    else:
        # Run ingestion
        ingester.ingest_all()

        # Show stats after ingestion
        ingester.get_collection_stats()


if __name__ == "__main__":
    main()
