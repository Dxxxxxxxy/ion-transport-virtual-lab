"""
ReAct Enhancement Layer for AI Agents

This module implements the ReAct (Reasoning + Acting) pattern for agents,
making their thought process explicit and interpretable.

ReAct Pattern:
    Thought: [Agent explains reasoning]
    Action: [Agent uses tool, e.g., query_knowledge_base("query")]
    Observation: [Tool result appears here]
    ... (repeat as needed)
    Thought: [Final synthesis reasoning]
    Answer: [Final contribution]

Benefits:
- Transparent reasoning process
- Better debugging and interpretation
- Improved scientific rigor
- Clear logical flow in discussions

Author: Ion Transport Virtual Lab
"""

from typing import Optional, List, Dict, Any
from agents.base_agent import Agent


REACT_INSTRUCTION_TEMPLATE = """
IMPORTANT - REASONING FORMAT:

When responding to questions or contributing to discussions, structure your response using the ReAct (Reasoning + Acting) pattern:

**Thought**: Explain your reasoning about what information you need, what argument you plan to make, or how you'll approach the question.

**Action**: If you need information, specify the tool to use:
  - query_knowledge_base("specific query about your domain")
  - Example: query_knowledge_base("EDL capacitance in sub-nanometer pores")

**Observation**: [The tool result will appear here - you'll see the retrieved information]

... (you can repeat Thought → Action → Observation multiple times as needed)

**Thought**: Explain your final reasoning about how you're synthesizing the information and forming your argument.

**Answer**: Provide your actual contribution to the discussion, integrating the evidence you gathered.

EXAMPLE:
```
Thought: I need to find specific data on ion selectivity mechanisms in nanopores to support my argument about size-based exclusion.

Action: query_knowledge_base("ion selectivity mechanisms nanopore size exclusion")

Observation: [Retrieved: "Studies show that sub-5nm nanopores exhibit strong size-based selectivity, with K+ permeation 10x higher than Na+ due to hydrated ion size differences..."]

Thought: This evidence supports my claim. Now I should also check if there's information about charge-based selectivity to compare mechanisms.

Action: query_knowledge_base("charge-based selectivity surface charge nanopores")

Observation: [Retrieved: "Surface charge density controls ion selectivity through electrostatic interactions, with selectivity ratios reaching 100:1 for monovalent/divalent ions..."]

Thought: Perfect. I now have evidence for both size-based and charge-based selectivity. I can synthesize these to explain the complementary mechanisms.

Answer: Ion selectivity in nanopores operates through two complementary mechanisms. First, size-based exclusion: sub-5nm pores can achieve K+/Na+ selectivity of 10:1 due to differences in hydrated ion radii (Smith et al., Nano Lett. 2023). Second, charge-based selectivity: surface charge creates electrostatic barriers, enabling monovalent/divalent selectivity up to 100:1 (Zhang et al., Nature 2024). In my field, we combine both mechanisms by engineering pore geometry AND surface chemistry...
```

This format makes your thinking transparent and helps other experts follow your logic.
"""


class ReActAgent:
    """
    Wrapper that enhances any Agent with explicit ReAct reasoning capabilities.

    This class wraps a base Agent and enhances its role/prompt with ReAct
    instructions, making the agent's reasoning process explicit and transparent.

    The wrapper is designed to be a drop-in replacement for Agent, maintaining
    the same interface while adding ReAct capabilities.

    Attributes:
        base_agent: The original Agent being wrapped
        enable_react: Whether ReAct mode is active
        react_instruction: The ReAct formatting instruction
        reasoning_traces: Collected reasoning traces from agent responses
    """

    def __init__(
        self,
        base_agent: Agent,
        enable_react: bool = True,
        custom_react_instruction: Optional[str] = None
    ):
        """
        Initialize ReActAgent wrapper.

        Args:
            base_agent: The Agent to enhance with ReAct capabilities
            enable_react: Whether to enable ReAct mode (default: True)
            custom_react_instruction: Optional custom ReAct instruction
                                     (default: uses REACT_INSTRUCTION_TEMPLATE)
        """
        self.base_agent = base_agent
        self.enable_react = enable_react
        self.react_instruction = (
            custom_react_instruction
            if custom_react_instruction
            else REACT_INSTRUCTION_TEMPLATE
        )
        self.reasoning_traces: List[Dict[str, Any]] = []

    @property
    def title(self) -> str:
        """Agent title (delegates to base agent)."""
        return self.base_agent.title

    @property
    def expertise(self) -> str:
        """Agent expertise (delegates to base agent)."""
        return self.base_agent.expertise

    @property
    def goal(self) -> str:
        """Agent goal (delegates to base agent)."""
        return self.base_agent.goal

    @property
    def role(self) -> str:
        """
        Enhanced role with ReAct instructions.

        Returns the base agent's role enhanced with ReAct formatting
        instructions if ReAct is enabled, otherwise returns original role.
        """
        if self.enable_react:
            return f"{self.base_agent.role}\n\n{self.react_instruction}"
        return self.base_agent.role

    @property
    def model(self) -> str:
        """Agent model (delegates to base agent)."""
        return self.base_agent.model

    @property
    def prompt(self) -> str:
        """
        Complete agent prompt with ReAct enhancement.

        Combines title, expertise, goal, and enhanced role into a
        formatted prompt string.
        """
        return f"""Title: {self.title}

Expertise: {self.expertise}

Goal: {self.goal}

Role: {self.role}
"""

    @property
    def message(self) -> Dict[str, str]:
        """
        OpenAI-compatible system message with ReAct enhancement.

        Returns:
            Dictionary with role="system" and enhanced content
        """
        return {
            "role": "system",
            "content": self.prompt
        }

    def add_reasoning_trace(
        self,
        thought: str,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        answer: Optional[str] = None,
        round_number: Optional[int] = None
    ):
        """
        Record a reasoning trace from the agent's response.

        Args:
            thought: The agent's reasoning/thinking
            action: Tool call or action taken
            observation: Result of the action
            answer: Final answer/contribution
            round_number: Which discussion round this is from
        """
        trace = {
            "thought": thought,
            "action": action,
            "observation": observation,
            "answer": answer,
            "round": round_number,
            "agent": self.title
        }
        self.reasoning_traces.append(trace)

    def get_reasoning_traces(
        self,
        round_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve reasoning traces, optionally filtered by round.

        Args:
            round_number: If provided, only return traces from this round

        Returns:
            List of reasoning trace dictionaries
        """
        if round_number is None:
            return self.reasoning_traces
        return [t for t in self.reasoning_traces if t.get("round") == round_number]

    def clear_traces(self):
        """Clear all collected reasoning traces."""
        self.reasoning_traces = []

    def toggle_react(self, enabled: bool):
        """
        Enable or disable ReAct mode.

        Args:
            enabled: True to enable ReAct, False to disable
        """
        self.enable_react = enabled

    def __repr__(self) -> str:
        """String representation of ReActAgent."""
        mode = "enabled" if self.enable_react else "disabled"
        return f"ReActAgent({self.title}, ReAct {mode})"

    def __hash__(self) -> int:
        """Hash based on base agent's title."""
        return hash(self.title)

    def __eq__(self, other) -> bool:
        """
        Equality check.

        Two ReActAgents are equal if their base agents are equal
        and ReAct mode matches.
        """
        if not isinstance(other, ReActAgent):
            return False
        return (
            self.base_agent == other.base_agent
            and self.enable_react == other.enable_react
        )


def enable_react_for_agents(
    agents: List[Agent],
    enable_react: bool = True
) -> List[ReActAgent]:
    """
    Wrap a list of agents with ReAct capabilities.

    Convenience function to batch-wrap multiple agents.

    Args:
        agents: List of Agent objects to wrap
        enable_react: Whether to enable ReAct mode for all

    Returns:
        List of ReActAgent wrappers

    Example:
        >>> from ion_transport.agents.detailed_agents import (
        ...     ELECTROCHEMISTRY_EXPERT,
        ...     MEMBRANE_SCIENCE_EXPERT
        ... )
        >>> react_agents = enable_react_for_agents([
        ...     ELECTROCHEMISTRY_EXPERT,
        ...     MEMBRANE_SCIENCE_EXPERT
        ... ])
    """
    return [ReActAgent(agent, enable_react=enable_react) for agent in agents]


def create_react_agent(
    title: str,
    expertise: str,
    goal: str,
    role: str,
    model: str,
    enable_react: bool = True
) -> ReActAgent:
    """
    Create a new ReActAgent from scratch.

    Helper function to create an agent with ReAct capabilities without
    needing to first create a base Agent.

    Args:
        title: Agent title
        expertise: Domain expertise
        goal: Agent's goal
        role: Agent's role and behavior instructions
        model: LLM model to use
        enable_react: Whether to enable ReAct mode

    Returns:
        ReActAgent instance
    """
    base_agent = Agent(
        title=title,
        expertise=expertise,
        goal=goal,
        role=role,
        model=model
    )
    return ReActAgent(base_agent, enable_react=enable_react)
