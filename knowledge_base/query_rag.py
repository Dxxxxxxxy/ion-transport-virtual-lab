"""
RAG Query Functions for Ion Transport Knowledge Base

This module provides functions to query the ChromaDB knowledge base and retrieve
relevant information from domain-specific paper collections.

Usage:
    from ion_transport.knowledge_base.query_rag import query_papers

    results = query_papers(
        query="How does pore size affect ion selectivity in nanopores?",
        domain="nanofluidics",
        top_k=5
    )
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings


# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"

# Domain mapping
DOMAINS = {
    "electrochemistry": "electrochemistry_papers",
    "membrane_science": "membrane_science_papers",
    "biology": "biology_papers",
    "nanofluidics": "nanofluidics_papers",
    "all": None,  # Query across all domains
}


class RAGQueryEngine:
    """Query engine for retrieving information from ChromaDB knowledge base."""

    def __init__(self, vector_db_dir: Optional[Path] = None):
        """
        Initialize RAG query engine.

        Args:
            vector_db_dir: Path to vector database. If None, uses default location.
        """
        if vector_db_dir is None:
            # Default location: ion_transport/data/vector_db/
            current_dir = Path(__file__).parent
            vector_db_dir = current_dir.parent / "data" / "vector_db"

        self.vector_db_dir = vector_db_dir

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(vector_db_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    def query_collection(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a specific ChromaDB collection.

        Args:
            query: Query string
            collection_name: Name of collection to query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of results with text, metadata, and distance
        """
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            print(f"Error: Collection '{collection_name}' not found: {e}")
            return []

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )

        # Format results
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'id': results['ids'][0][i],
                })

        return formatted_results

    def query_domain(
        self,
        query: str,
        domain: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query papers from a specific domain.

        Args:
            query: Query string
            domain: Domain name (electrochemistry, membrane_science, biology, nanofluidics)
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of results with text, metadata, and distance
        """
        if domain not in DOMAINS:
            raise ValueError(f"Invalid domain. Choose from: {list(DOMAINS.keys())}")

        collection_name = DOMAINS[domain]
        return self.query_collection(query, collection_name, top_k, filter_metadata)

    def query_all_domains(
        self,
        query: str,
        top_k_per_domain: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query across all domains and return results grouped by domain.

        Args:
            query: Query string
            top_k_per_domain: Number of results per domain

        Returns:
            Dictionary mapping domain names to results
        """
        all_results = {}

        for domain, collection_name in DOMAINS.items():
            if domain == "all":
                continue

            results = self.query_collection(query, collection_name, top_k_per_domain)
            all_results[domain] = results

        return all_results

    def format_results_for_llm(
        self,
        results: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """
        Format query results for LLM consumption.

        Args:
            results: List of query results
            include_metadata: Whether to include metadata in output

        Returns:
            Formatted string for LLM context
        """
        if not results:
            return "No relevant information found in the knowledge base."

        formatted = []
        for i, result in enumerate(results, 1):
            text = result['text']
            metadata = result['metadata']

            if include_metadata:
                # Extract citation metadata
                citation = metadata.get('citation', 'Citation unavailable')
                title = metadata.get('title', 'Unknown Title')
                authors = metadata.get('authors', 'Unknown')
                year = metadata.get('year', 'n.d.')

                # Format: [Source 1] Authors (Year) - Title
                #         Citation: Journal (Year), Volume, Pages
                #         <content>
                formatted.append(
                    f"[Source {i}] {authors} ({year}) - {title}\n"
                    f"Citation: {citation}\n\n{text}\n"
                )
            else:
                formatted.append(f"[{i}] {text}\n")

        return "\n---\n".join(formatted)


# Convenience functions for direct use
def query_papers(
    query: str,
    domain: str = "all",
    top_k: int = 5,
    format_for_llm: bool = False
) -> Any:
    """
    Convenient function to query papers.

    Args:
        query: Query string
        domain: Domain to search (or 'all' for all domains)
        top_k: Number of results
        format_for_llm: Whether to format results for LLM

    Returns:
        Query results (formatted string if format_for_llm=True, else list/dict)
    """
    engine = RAGQueryEngine()

    if domain == "all":
        results = engine.query_all_domains(query, top_k_per_domain=top_k)
        if format_for_llm:
            # Flatten and format all results
            all_results_flat = []
            for domain_name, domain_results in results.items():
                all_results_flat.extend(domain_results)
            return engine.format_results_for_llm(all_results_flat)
        return results
    else:
        results = engine.query_domain(query, domain, top_k)
        if format_for_llm:
            return engine.format_results_for_llm(results)
        return results


def get_context_for_agent(query: str, domain: str, top_k: int = 5) -> str:
    """
    Get formatted context for an AI agent from the knowledge base.

    This is the primary function that will be used by AI agents during symposium.

    Args:
        query: What the agent wants to know
        domain: Agent's domain (electrochemistry, membrane_science, biology, nanofluidics)
        top_k: Number of relevant chunks to retrieve

    Returns:
        Formatted context string with citations
    """
    engine = RAGQueryEngine()
    results = engine.query_domain(query, domain, top_k)

    if not results:
        return f"No relevant information found in {domain} knowledge base for: {query}"

    # Format with citations
    context_parts = []
    for i, result in enumerate(results, 1):
        text = result['text']
        metadata = result['metadata']

        # Extract citation metadata
        citation = metadata.get('citation', 'Citation unavailable')
        title = metadata.get('title', 'Unknown Title')
        authors = metadata.get('authors', 'Unknown')
        year = metadata.get('year', 'n.d.')

        # Format with full citation info
        context_parts.append(
            f"[Source {i}] {authors} ({year}) - {title}\n"
            f"Citation: {citation}\n\n{text}"
        )

    return "\n\n---\n\n".join(context_parts)


# CLI interface for testing
def main():
    """CLI interface for testing queries."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python query_rag.py <query> [domain] [top_k]")
        print("\nDomains: electrochemistry, membrane_science, biology, nanofluidics, all")
        print("\nExample:")
        print("  python query_rag.py 'ion selectivity mechanisms' nanofluidics 5")
        sys.exit(1)

    query = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else "all"
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"Domain: {domain}")
    print(f"Top K: {top_k}")
    print(f"{'='*80}\n")

    results = query_papers(query, domain, top_k, format_for_llm=True)
    print(results)


if __name__ == "__main__":
    main()
