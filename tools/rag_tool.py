"""
RAG Tool Integration for Ion Transport Symposium

This module provides RAG (Retrieval-Augmented Generation) tool functionality
for AI agents to query their domain-specific knowledge bases during discussions.

This replaces PubMed search with curated, domain-specific paper knowledge.
"""

import json
from typing import Optional
from pathlib import Path

# RAG tool constants
RAG_TOOL_NAME = "query_knowledge_base"

RAG_TOOL_DESCRIPTION = {
    "type": "function",
    "function": {
        "name": RAG_TOOL_NAME,
        "description": """Query your domain-specific knowledge base of curated papers on ion transport.
        This retrieves relevant content from high-quality papers you have access to, including full text,
        figures, tables, and equations. Use this to support your arguments with specific evidence from
        your field's literature.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific question or topic to search for in your knowledge base. Be specific about what you want to know (e.g., 'pore size effects on ion selectivity' or 'EDL capacitance in nanopores').",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of relevant paper sections to retrieve (default: 5, max: 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def run_rag_query(query: str, domain: str, top_k: int = 5) -> str:
    """
    Execute RAG query for an agent.

    Args:
        query: What the agent wants to know
        domain: Agent's domain (electrochemistry, membrane_science, biology, nanofluidics)
        top_k: Number of relevant chunks to retrieve

    Returns:
        Formatted string with retrieved context and citations
    """
    try:
        # Import here to avoid circular dependencies
        from knowledge_base import get_context_for_agent

        # Print query for transparency
        print(f'\n🔍 [{domain.upper()}] Querying knowledge base: "{query}"')

        # Query the knowledge base
        context = get_context_for_agent(query, domain, top_k)

        # Add usage instruction
        formatted_result = f"""Knowledge Base Results for: "{query}"

{context}

---
Instructions for citation:
When using information from above, cite as: Journal abbreviation (Year), Volume, Page numbers
Extract this from the paper metadata or content when available.
"""

        print(f'✓ Retrieved {top_k} relevant sections from {domain} papers\n')

        return formatted_result

    except Exception as e:
        error_msg = f"Error querying knowledge base: {str(e)}"
        print(f"✗ {error_msg}\n")
        return f"Unable to retrieve information from knowledge base. Error: {str(e)}\nPlease try rephrasing your query or proceed with your existing knowledge."


def handle_rag_tool_calls(tool_calls, agent_domain: str):
    """
    Handle RAG tool calls from an agent.

    Args:
        tool_calls: List of tool calls from OpenAI API
        agent_domain: The agent's domain for knowledge base queries

    Returns:
        Tuple of (tool_outputs, tool_messages) for API
    """
    tool_outputs = []
    tool_messages = []

    for tool_call in tool_calls:
        if tool_call.function.name == RAG_TOOL_NAME:
            # Extract arguments
            args_dict = json.loads(tool_call.function.arguments)
            query = args_dict.get("query", "")
            top_k = args_dict.get("top_k", 5)

            # Cap top_k at 10
            top_k = min(top_k, 10)

            # Run RAG query
            output = run_rag_query(query, agent_domain, top_k)
            tool_outputs.append(output)

            # Create tool response message for API
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output,
            })

    return tool_outputs, tool_messages


# Agent-specific RAG tool configurations
def get_rag_tool_for_agent(agent_domain: str) -> dict:
    """
    Get RAG tool configuration customized for a specific agent's domain.

    Args:
        agent_domain: Domain name (electrochemistry, membrane_science, biology, nanofluidics)

    Returns:
        Tool description dict
    """
    # Customize description based on domain
    domain_descriptions = {
        "electrochemistry": "supercapacitors, capacitive deionization, EDL capacitors, and porous electrodes",
        "membrane_science": "desalination, ion separation, element extraction, and membrane materials",
        "biology": "ion channels (K+, Na+, Ca2+), selectivity filters, and biological membranes",
        "nanofluidics": "synthetic nanopores, nanochannels, nanofluidic devices, and confined transport",
    }

    tool_desc = RAG_TOOL_DESCRIPTION.copy()
    domain_info = domain_descriptions.get(agent_domain, "ion transport")

    # Customize description
    tool_desc["function"]["description"] = f"""Query your specialized knowledge base of curated papers on {domain_info}.
    This retrieves relevant content from high-quality papers in your field, including full text,
    figures, tables, and equations. Use this to support your arguments with specific evidence."""

    return tool_desc


# Wrapper to integrate with virtual_lab framework
class RAGIntegration:
    """Integration layer for RAG with virtual_lab framework."""

    def __init__(self, use_rag: bool = True):
        """
        Initialize RAG integration.

        Args:
            use_rag: Whether to use RAG (True) or fall back to no tool (False)
        """
        self.use_rag = use_rag
        self._check_knowledge_base()

    def _check_knowledge_base(self):
        """Check if knowledge base exists and has been populated."""
        if not self.use_rag:
            return

        # Navigate from tools/ back to project root, then to data/vector_db
        vector_db_path = Path(__file__).parent.parent / "data" / "vector_db"

        if not vector_db_path.exists():
            print("⚠️  Warning: Vector database not found. RAG will not work.")
            print(f"   Expected location: {vector_db_path}")
            print("   Run: python knowledge_base/ingest_papers.py")
            self.use_rag = False

    def get_tools_for_agent(self, agent_domain: str) -> list:
        """
        Get list of tools available to an agent.

        Args:
            agent_domain: Agent's domain

        Returns:
            List of tool descriptions
        """
        if not self.use_rag:
            return []

        return [get_rag_tool_for_agent(agent_domain)]

    def process_tool_calls(self, tool_calls, agent_domain: str):
        """
        Process tool calls from an agent.

        Args:
            tool_calls: Tool calls from OpenAI
            agent_domain: Agent's domain

        Returns:
            Tuple of (tool_outputs, tool_messages)
        """
        if not self.use_rag:
            return [], []

        return handle_rag_tool_calls(tool_calls, agent_domain)


# Singleton instance
_rag_integration = None


def get_rag_integration(use_rag: bool = True) -> RAGIntegration:
    """Get or create RAG integration singleton."""
    global _rag_integration
    if _rag_integration is None:
        _rag_integration = RAGIntegration(use_rag=use_rag)
    return _rag_integration
