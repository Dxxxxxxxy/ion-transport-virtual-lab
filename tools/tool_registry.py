"""
Tool Registry - Central Management for Agent Tools

Provides unified interface for registering and accessing all agent tools.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    description: str
    category: str  # "knowledge", "computation", "visualization", "search"
    cost_estimate: float  # Estimated cost per call in dollars
    requires_api: bool  # Whether tool requires external API


class Tool(ABC):
    """Base class for all agent tools."""

    def __init__(self, name: str, description: str, category: str,
                 cost_estimate: float = 0.0, requires_api: bool = False):
        self.metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            cost_estimate=cost_estimate,
            requires_api=requires_api
        )

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    def to_openai_schema(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function calling schema.

        Must be implemented by each tool to define:
        - function.name
        - function.description
        - function.parameters (JSON Schema)

        Returns:
            OpenAI tool definition dict in format:
            {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "...",
                    "parameters": {...}
                }
            }
        """
        pass

    def get_description_for_prompt(self) -> str:
        """Get tool description formatted for agent prompts."""
        return f"""
{self.metadata.name}: {self.metadata.description}
Category: {self.metadata.category}
Cost: ~${self.metadata.cost_estimate:.3f} per call
"""


class ToolRegistry:
    """
    Central registry for all agent tools.

    Manages tool registration, discovery, and access control.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._domain_tools: Dict[str, List[str]] = {
            "electrochemistry": [],
            "membrane_science": [],
            "biology": [],
            "nanofluidics": [],
            "all": []  # Tools available to all agents
        }

    def register_tool(self, tool: Tool, domains: Optional[List[str]] = None):
        """
        Register a tool for use by agents.

        Args:
            tool: Tool instance to register
            domains: List of domains that can use this tool (None = all domains)
        """
        self._tools[tool.metadata.name] = tool

        if domains is None:
            # Available to all domains
            self._domain_tools["all"].append(tool.metadata.name)
        else:
            # Available to specific domains
            for domain in domains:
                if domain in self._domain_tools:
                    self._domain_tools[domain].append(tool.metadata.name)

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_tools_for_domain(self, domain: str) -> List[Tool]:
        """
        Get all tools available for a domain.

        Args:
            domain: Domain name (e.g., "electrochemistry")

        Returns:
            List of Tool instances available for this domain
        """
        tool_names = set(self._domain_tools.get(domain, []) + self._domain_tools["all"])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_tool_descriptions_for_domain(self, domain: str) -> str:
        """
        Get formatted tool descriptions for agent prompts.

        Args:
            domain: Domain name

        Returns:
            Formatted string describing all available tools
        """
        tools = self.get_tools_for_domain(domain)

        if not tools:
            return "No additional tools available beyond RAG knowledge base."

        descriptions = ["AVAILABLE TOOLS:", "="*80]

        for tool in tools:
            descriptions.append(tool.get_description_for_prompt())
            descriptions.append("-" * 80)

        return "\n".join(descriptions)

    def get_openai_schemas(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get OpenAI function calling schemas for all tools in a domain.

        Args:
            domain: Domain name

        Returns:
            List of OpenAI function schema dicts
        """
        tools = self.get_tools_for_domain(domain)
        return [tool.to_openai_schema() for tool in tools]

    def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found in registry")

        return tool.execute(**kwargs)

    def list_all_tools(self) -> Dict[str, ToolMetadata]:
        """Get metadata for all registered tools."""
        return {name: tool.metadata for name, tool in self._tools.items()}

    def get_total_cost_estimate(self, tool_calls: Dict[str, int]) -> float:
        """
        Estimate total cost for a set of tool calls.

        Args:
            tool_calls: Dict mapping tool names to call counts

        Returns:
            Estimated total cost in dollars
        """
        total = 0.0
        for tool_name, count in tool_calls.items():
            tool = self.get_tool(tool_name)
            if tool:
                total += tool.metadata.cost_estimate * count
        return total


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_default_tools():
    """
    Register all default tools in the global registry.

    This should be called during initialization to set up
    the standard tool ecosystem.
    """
    from tools.web_search_tool import WebSearchTool
    from tools.equation_solver_tool import EquationSolverTool
    from tools.plotting_tool import PlottingTool
    from tools.concept_mapper_tool import ConceptMapperTool

    registry = get_global_registry()

    # Web search - available to all domains
    registry.register_tool(WebSearchTool(), domains=None)

    # Equation solver - available to all domains
    registry.register_tool(EquationSolverTool(), domains=None)

    # Plotting - available to all domains
    registry.register_tool(PlottingTool(), domains=None)

    # Concept mapper - available to all domains
    registry.register_tool(ConceptMapperTool(), domains=None)

    return registry
