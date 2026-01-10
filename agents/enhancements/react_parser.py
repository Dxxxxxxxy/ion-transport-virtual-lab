"""
ReAct Response Parser

Utilities for parsing and analyzing agent responses that use the ReAct format.

This module provides functions to:
- Extract Thought/Action/Observation/Answer blocks from responses
- Count reasoning steps
- Format discussions with highlighted reasoning traces
- Analyze discussion quality metrics

Author: Ion Transport Virtual Lab
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ReActTrace:
    """
    A single ReAct reasoning trace.

    Attributes:
        thoughts: List of thought/reasoning steps
        actions: List of actions/tool calls
        observations: List of observations/results
        answer: Final answer/contribution
        step_count: Number of reasoning steps
        agent_name: Name of the agent
    """
    thoughts: List[str]
    actions: List[str]
    observations: List[str]
    answer: str
    step_count: int
    agent_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary format."""
        return {
            "agent": self.agent_name,
            "thoughts": self.thoughts,
            "actions": self.actions,
            "observations": self.observations,
            "answer": self.answer,
            "step_count": self.step_count,
        }


class ReActParser:
    """
    Parser for extracting ReAct reasoning traces from agent responses.

    Handles various formatting patterns and edge cases in agent responses.
    """

    # Regex patterns for extracting ReAct components
    THOUGHT_PATTERN = re.compile(
        r'\*\*Thought\*\*:?\s*(.+?)(?=\*\*(?:Action|Answer|Thought)|$)',
        re.DOTALL | re.IGNORECASE
    )
    ACTION_PATTERN = re.compile(
        r'\*\*Action\*\*:?\s*(.+?)(?=\*\*(?:Observation|Thought|Answer)|$)',
        re.DOTALL | re.IGNORECASE
    )
    OBSERVATION_PATTERN = re.compile(
        r'\*\*Observation\*\*:?\s*(.+?)(?=\*\*(?:Thought|Action|Answer)|$)',
        re.DOTALL | re.IGNORECASE
    )
    ANSWER_PATTERN = re.compile(
        r'\*\*Answer\*\*:?\s*(.+?)$',
        re.DOTALL | re.IGNORECASE
    )

    @staticmethod
    def extract_trace(response: str, agent_name: Optional[str] = None) -> Optional[ReActTrace]:
        """
        Extract ReAct trace from an agent response.

        Args:
            response: The agent's response text
            agent_name: Optional name of the agent

        Returns:
            ReActTrace object if ReAct format detected, None otherwise
        """
        # Check if response contains ReAct markers
        has_react_markers = any([
            "**Thought**" in response or "**thought**" in response,
            "**Action**" in response or "**action**" in response,
            "**Answer**" in response or "**answer**" in response,
        ])

        if not has_react_markers:
            return None

        # Extract components
        thoughts = [
            m.group(1).strip()
            for m in ReActParser.THOUGHT_PATTERN.finditer(response)
        ]
        actions = [
            m.group(1).strip()
            for m in ReActParser.ACTION_PATTERN.finditer(response)
        ]
        observations = [
            m.group(1).strip()
            for m in ReActParser.OBSERVATION_PATTERN.finditer(response)
        ]
        answer_match = ReActParser.ANSWER_PATTERN.search(response)
        answer = answer_match.group(1).strip() if answer_match else ""

        # Calculate step count (each thought-action-observation cycle = 1 step)
        step_count = len(thoughts)

        return ReActTrace(
            thoughts=thoughts,
            actions=actions,
            observations=observations,
            answer=answer,
            step_count=step_count,
            agent_name=agent_name
        )

    @staticmethod
    def is_react_response(response: str) -> bool:
        """
        Check if a response uses ReAct format.

        Args:
            response: Agent response text

        Returns:
            True if ReAct markers detected, False otherwise
        """
        return ReActParser.extract_trace(response) is not None

    @staticmethod
    def count_reasoning_steps(response: str) -> int:
        """
        Count the number of reasoning steps in a response.

        Args:
            response: Agent response text

        Returns:
            Number of Thought blocks (reasoning steps)
        """
        trace = ReActParser.extract_trace(response)
        return trace.step_count if trace else 0

    @staticmethod
    def extract_tool_calls(response: str) -> List[str]:
        """
        Extract tool call commands from Action blocks.

        Args:
            response: Agent response text

        Returns:
            List of tool call strings (e.g., ["query_knowledge_base(...)"])
        """
        trace = ReActParser.extract_trace(response)
        if not trace:
            return []

        # Extract function calls from actions
        tool_calls = []
        for action in trace.actions:
            # Look for patterns like: query_knowledge_base("...")
            function_pattern = re.compile(r'(\w+)\s*\(["\'](.+?)["\']\)')
            matches = function_pattern.findall(action)
            for func_name, query in matches:
                tool_calls.append(f"{func_name}({query})")

        return tool_calls


def extract_reasoning_traces(
    discussion: List[Dict[str, str]],
    agent_names: Optional[List[str]] = None
) -> List[ReActTrace]:
    """
    Extract all ReAct traces from a discussion transcript.

    Args:
        discussion: List of message dictionaries with 'role' and 'content'
        agent_names: Optional list of agent names corresponding to messages

    Returns:
        List of ReActTrace objects

    Example:
        >>> discussion = [
        ...     {"role": "assistant", "content": "**Thought**: I need..."},
        ...     {"role": "assistant", "content": "Regular response"}
        ... ]
        >>> traces = extract_reasoning_traces(discussion)
    """
    traces = []
    parser = ReActParser()

    for i, message in enumerate(discussion):
        if message.get("role") != "assistant":
            continue

        content = message.get("content", "")
        agent_name = agent_names[i] if agent_names and i < len(agent_names) else None

        trace = parser.extract_trace(content, agent_name)
        if trace:
            traces.append(trace)

    return traces


def format_discussion_with_traces(
    discussion: List[Dict[str, str]],
    highlight_traces: bool = True
) -> str:
    """
    Format a discussion transcript with highlighted ReAct traces.

    Args:
        discussion: List of message dictionaries
        highlight_traces: Whether to visually highlight reasoning steps

    Returns:
        Formatted markdown string

    Example:
        >>> formatted = format_discussion_with_traces(discussion)
        >>> print(formatted)
    """
    parser = ReActParser()
    output_lines = []

    for message in discussion:
        role = message.get("role", "unknown")
        content = message.get("content", "")

        # Check if this is a ReAct response
        trace = parser.extract_trace(content)

        if trace and highlight_traces:
            # Format with highlighting
            output_lines.append(f"\n### {role.upper()} (ReAct Mode - {trace.step_count} steps)")
            output_lines.append("")

            # Show thoughts
            for i, thought in enumerate(trace.thoughts, 1):
                output_lines.append(f"**💭 Thought {i}**: {thought}")
                output_lines.append("")

                # Show corresponding action if exists
                if i <= len(trace.actions):
                    output_lines.append(f"**⚡ Action {i}**: {trace.actions[i-1]}")
                    output_lines.append("")

                # Show corresponding observation if exists
                if i <= len(trace.observations):
                    output_lines.append(f"**👁️ Observation {i}**: {trace.observations[i-1]}")
                    output_lines.append("")

            # Show final answer
            if trace.answer:
                output_lines.append(f"**✅ Answer**: {trace.answer}")
                output_lines.append("")

        else:
            # Regular formatting
            output_lines.append(f"\n### {role.upper()}")
            output_lines.append("")
            output_lines.append(content)
            output_lines.append("")

        output_lines.append("---")
        output_lines.append("")

    return "\n".join(output_lines)


def analyze_discussion_quality(
    discussion: List[Dict[str, str]],
    agent_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze quality metrics of a discussion based on ReAct usage.

    Args:
        discussion: List of message dictionaries
        agent_names: Optional list of agent names

    Returns:
        Dictionary with quality metrics

    Metrics:
        - total_messages: Total number of messages
        - react_messages: Number of messages using ReAct
        - react_percentage: Percentage of messages using ReAct
        - avg_steps_per_react: Average reasoning steps per ReAct message
        - total_tool_calls: Total number of tool calls
        - agents_using_react: List of agents that used ReAct

    Example:
        >>> metrics = analyze_discussion_quality(discussion, agent_names)
        >>> print(f"ReAct usage: {metrics['react_percentage']:.1f}%")
    """
    parser = ReActParser()
    traces = extract_reasoning_traces(discussion, agent_names)

    total_messages = sum(1 for m in discussion if m.get("role") == "assistant")
    react_messages = len(traces)
    react_percentage = (react_messages / total_messages * 100) if total_messages > 0 else 0

    total_steps = sum(t.step_count for t in traces)
    avg_steps = total_steps / react_messages if react_messages > 0 else 0

    # Count tool calls
    total_tool_calls = 0
    for message in discussion:
        if message.get("role") == "assistant":
            tool_calls = parser.extract_tool_calls(message.get("content", ""))
            total_tool_calls += len(tool_calls)

    # Identify agents using ReAct
    agents_using_react = list(set(t.agent_name for t in traces if t.agent_name))

    return {
        "total_messages": total_messages,
        "react_messages": react_messages,
        "react_percentage": react_percentage,
        "avg_steps_per_react": avg_steps,
        "total_steps": total_steps,
        "total_tool_calls": total_tool_calls,
        "agents_using_react": agents_using_react,
        "traces": [t.to_dict() for t in traces],
    }


def export_traces_to_json(
    discussion: List[Dict[str, str]],
    output_path: str,
    agent_names: Optional[List[str]] = None
):
    """
    Export reasoning traces to JSON file.

    Args:
        discussion: List of message dictionaries
        output_path: Path to save JSON file
        agent_names: Optional list of agent names
    """
    import json
    from pathlib import Path

    traces = extract_reasoning_traces(discussion, agent_names)
    quality_metrics = analyze_discussion_quality(discussion, agent_names)

    output_data = {
        "quality_metrics": quality_metrics,
        "traces": [t.to_dict() for t in traces],
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported {len(traces)} traces to {output_path}")
