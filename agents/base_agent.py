"""
Base Agent Class for Ion Transport Virtual Lab

This module provides the core Agent class that represents an AI expert
in the multi-agent symposium. Each agent has a specific domain expertise,
goal, and role that guides their contributions to scientific discussions.

The Agent class is designed to work with OpenAI's Chat API and can be
enhanced with additional capabilities through wrapper classes.
"""

from typing import Dict, Any


class Agent:
    """
    Base AI agent for scientific discussions.

    An Agent represents a domain expert with specific knowledge, goals,
    and communication patterns. Agents are used in multi-agent symposiums
    to discuss and develop unified theoretical frameworks.

    Attributes:
        title: Agent's professional title (e.g., "Electrochemistry Scientist")
        expertise: Detailed description of agent's domain expertise
        goal: Agent's objectives in discussions
        role: Behavioral guidelines and communication instructions
        model: OpenAI model to use for this agent (e.g., "gpt-4o")

    Example:
        >>> agent = Agent(
        ...     title="Electrochemistry Scientist",
        ...     expertise="EDL capacitors, ion transport in aqueous electrolytes...",
        ...     goal="explain ion transport and EDL formation...",
        ...     role="You are an electrochemistry researcher...",
        ...     model="gpt-4o"
        ... )
        >>> print(agent.title)
        Electrochemistry Scientist
        >>> message = agent.message
        >>> # Use message in OpenAI API call
    """

    def __init__(
        self,
        title: str,
        expertise: str,
        goal: str,
        role: str,
        model: str = "gpt-4o"
    ):
        """
        Initialize an AI agent.

        Args:
            title: Agent's professional title
            expertise: Detailed expertise description
            goal: Agent's discussion goals
            role: Behavioral and communication guidelines
            model: OpenAI model identifier (default: "gpt-4o")
        """
        self.title = title
        self.expertise = expertise
        self.goal = goal
        self.role = role
        self.model = model

    @property
    def prompt(self) -> str:
        """
        Get the full formatted prompt combining expertise, goal, and role.

        Returns:
            Multi-line string with full agent context
        """
        return f"{self.expertise}\n\n{self.goal}\n\n{self.role}"

    @property
    def message(self) -> Dict[str, str]:
        """
        Get OpenAI-compatible system message.

        Returns:
            Dictionary with 'role' and 'content' keys for OpenAI API

        Example:
            >>> agent.message
            {'role': 'system', 'content': 'You are an electrochemistry researcher...'}
        """
        return {
            "role": "system",
            "content": self.role
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Agent(title='{self.title}', model='{self.model}')"

    def __hash__(self) -> int:
        """
        Make Agent hashable (for use in sets/dicts).

        Hash is based on title to ensure uniqueness.
        """
        return hash(self.title)

    def __eq__(self, other: Any) -> bool:
        """
        Check equality based on title.

        Two agents are equal if they have the same title.
        """
        if isinstance(other, Agent):
            return self.title == other.title
        return False
