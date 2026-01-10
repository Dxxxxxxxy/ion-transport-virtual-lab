"""
Tool Manager - Orchestrates all agent tools with OpenAI function calling

Manages both RAG and Phase 4 tools, providing unified interface for
tool execution and result formatting.
"""

import json
from typing import List, Dict, Any, Tuple, Optional
from tools import get_global_registry, register_default_tools
from tools.rag_tool import get_rag_integration, RAG_TOOL_NAME, run_rag_query


class ToolManager:
    """
    Manages all agent tools with OpenAI function calling integration.

    Responsibilities:
    - Export tools as OpenAI function schemas
    - Execute tool calls from OpenAI responses
    - Format results for agent consumption
    - Track usage and costs
    """

    def __init__(self, domain: str):
        """
        Initialize ToolManager for a specific domain.

        Args:
            domain: Agent's domain (electrochemistry, membrane_science, biology, nanofluidics)
        """
        self.domain = domain

        # Initialize tool registry
        self.tool_registry = get_global_registry()

        # Register default tools if not already registered
        if not self.tool_registry.list_all_tools():
            register_default_tools()

        # Initialize RAG integration
        self.rag_integration = get_rag_integration(use_rag=True)

        # Track tool usage for analytics
        self.tool_usage = []  # List of {tool_name, timestamp, success}

    def get_all_openai_tools(self) -> List[Dict]:
        """
        Get all available tools as OpenAI function schemas.

        Returns:
            List of OpenAI function schema dicts for both RAG and Phase 4 tools
        """
        tools = []

        # Add RAG tool (domain-specific)
        rag_tools = self.rag_integration.get_tools_for_agent(self.domain)
        tools.extend(rag_tools)

        # Add Phase 4 tools from registry (all available to all domains)
        phase4_schemas = self.tool_registry.get_openai_schemas(self.domain)
        tools.extend(phase4_schemas)

        return tools

    def execute_tool_calls(
        self,
        tool_calls: List,
        conversation_context: Optional[List[Dict]] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Execute tool calls from OpenAI response.

        Args:
            tool_calls: Tool calls from OpenAI API response
            conversation_context: Current conversation for context (optional)

        Returns:
            Tuple of (tool_outputs, tool_messages)
            - tool_outputs: List of formatted result strings
            - tool_messages: List of OpenAI tool message dicts
        """
        tool_outputs = []
        tool_messages = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args_dict = json.loads(tool_call.function.arguments)

            try:
                # Route to appropriate handler
                if function_name == RAG_TOOL_NAME:
                    # RAG tool (existing implementation)
                    output = self._execute_rag_tool(args_dict)
                else:
                    # Phase 4 tools (via registry)
                    output = self._execute_phase4_tool(function_name, args_dict)

                # Record successful execution
                self._record_tool_usage(function_name, success=True)

            except Exception as e:
                # Handle errors gracefully
                output = f"Error executing {function_name}: {str(e)}"
                self._record_tool_usage(function_name, success=False)

            tool_outputs.append(output)

            # Create OpenAI tool message format
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": output
            })

        return tool_outputs, tool_messages

    def _execute_rag_tool(self, args: Dict[str, Any]) -> str:
        """Execute RAG knowledge base query."""
        query = args.get("query", "")
        top_k = args.get("top_k", 5)

        # Cap top_k at 10
        top_k = min(top_k, 10)

        # Run RAG query
        output = run_rag_query(query, self.domain, top_k)
        return output

    def _execute_phase4_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute Phase 4 tool from registry."""
        tool = self.tool_registry.get_tool(tool_name)

        if tool is None:
            return f"Error: Tool '{tool_name}' not found in registry"

        # Execute tool
        result = tool.execute(**args)

        # Format result for agent
        formatted_output = tool.format_results_for_agent(result)

        return formatted_output

    def _record_tool_usage(self, tool_name: str, success: bool):
        """Record tool usage for analytics."""
        import datetime
        self.tool_usage.append({
            "tool_name": tool_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "success": success
        })

    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get tool usage stats and cost estimates.

        Returns:
            Dictionary with usage statistics:
            {
                "total_calls": int,
                "successful_calls": int,
                "failed_calls": int,
                "tool_breakdown": {tool_name: count, ...},
                "estimated_cost": float
            }
        """
        total_calls = len(self.tool_usage)
        successful_calls = sum(1 for u in self.tool_usage if u["success"])
        failed_calls = total_calls - successful_calls

        # Count calls per tool
        tool_breakdown = {}
        for usage in self.tool_usage:
            tool_name = usage["tool_name"]
            tool_breakdown[tool_name] = tool_breakdown.get(tool_name, 0) + 1

        # Estimate cost (only Phase 4 tools that require APIs)
        estimated_cost = self.tool_registry.get_total_cost_estimate(tool_breakdown)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "tool_breakdown": tool_breakdown,
            "estimated_cost": estimated_cost
        }

    def reset_usage_stats(self):
        """Clear usage statistics."""
        self.tool_usage = []

    def get_available_tools_description(self) -> str:
        """
        Get human-readable description of available tools.

        Returns:
            Formatted string describing all tools
        """
        descriptions = [
            f"TOOLS AVAILABLE FOR {self.domain.upper()} DOMAIN:",
            "=" * 80,
            "",
            "1. RAG Tool:",
            f"   - query_knowledge_base: Query domain-specific knowledge base of {self.domain} papers",
            "",
            "2. Phase 4 Tools (all domains):"
        ]

        tools = self.tool_registry.get_tools_for_domain(self.domain)
        for i, tool in enumerate(tools, 3):
            descriptions.append(f"   {i}. {tool.metadata.name}: {tool.metadata.description}")

        descriptions.append("")
        descriptions.append("=" * 80)

        return "\n".join(descriptions)
