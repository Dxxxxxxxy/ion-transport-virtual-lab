"""
Advanced Tool Ecosystem for AI Agents

This module provides an expanded toolkit including RAG and Phase 4 tools:
- RAG integration for domain-specific knowledge retrieval
- Web search for recent papers
- Equation solving with SymPy
- Data visualization with Matplotlib
- Concept mapping with NetworkX

All tools are managed through a central ToolRegistry.
"""

from tools.tool_registry import (
    ToolRegistry,
    Tool,
    get_global_registry,
    register_default_tools
)
from tools.rag_tool import (
    RAGIntegration,
    get_rag_integration,
    run_rag_query,
    RAG_TOOL_NAME,
)
from tools.web_search_tool import WebSearchTool
from tools.equation_solver_tool import EquationSolverTool
from tools.plotting_tool import PlottingTool
from tools.concept_mapper_tool import ConceptMapperTool

__all__ = [
    "ToolRegistry",
    "Tool",
    "get_global_registry",
    "register_default_tools",
    "RAGIntegration",
    "get_rag_integration",
    "run_rag_query",
    "RAG_TOOL_NAME",
    "WebSearchTool",
    "EquationSolverTool",
    "PlottingTool",
    "ConceptMapperTool",
]

__version__ = "0.4.0"  # Phase 4
