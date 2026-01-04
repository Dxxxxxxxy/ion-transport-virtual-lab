"""
Ion Transport Knowledge Base Module

This module provides RAG (Retrieval-Augmented Generation) capabilities for the
ion transport symposium by maintaining a vector database of domain-specific papers.

Main Components:
- ingest_papers.py: Ingests PDFs and creates vector database
- query_rag.py: Queries the knowledge base and retrieves relevant information

Usage:
    # Ingest papers (run once after adding new PDFs)
    python -m ion_transport.knowledge_base.ingest_papers

    # Query the knowledge base
    from ion_transport.knowledge_base.query_rag import query_papers, get_context_for_agent

    results = query_papers("How does EDL overlap affect selectivity?", domain="nanofluidics")
    context = get_context_for_agent("pore size effects", domain="nanofluidics", top_k=5)
"""

from .query_rag import query_papers, get_context_for_agent, RAGQueryEngine

__all__ = ['query_papers', 'get_context_for_agent', 'RAGQueryEngine']
