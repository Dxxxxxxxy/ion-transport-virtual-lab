"""
Agent System for Ion Transport Symposium

This module provides:
- Base Agent class and constants
- Expert agent definitions (4 domain experts + PI + critic)
- Discussion prompts for symposium rounds
- Enhanced agent capabilities (via enhancements submodule)
"""

# Core agent infrastructure
from agents.base_agent import Agent
from agents.constants import DEFAULT_MODEL

# Agent definitions
from agents.agent_definitions import (
    SYMPOSIUM_PI,
    ELECTROCHEMISTRY_EXPERT,
    MEMBRANE_SCIENCE_EXPERT,
    BIOLOGY_EXPERT,
    NANOFLUIDICS_EXPERT,
    CUSTOM_SCIENTIFIC_CRITIC,
)

# Discussion prompts
from agents.prompts import (
    ROUND_1_DETAILED_AGENDA,
    ROUND_2_DETAILED_AGENDA,
    ROUND_3_DETAILED_AGENDA,
    ROUND_4_DETAILED_AGENDA,
    ROUND_1_QUESTIONS,
    ROUND_2_QUESTIONS,
    ROUND_3_QUESTIONS,
    ROUND_4_QUESTIONS,
    RIGOROUS_DISCUSSION_RULES,
)

# Enhanced capabilities (imports from enhancements submodule)
from agents.enhancements import (
    UnifiedAgent,
    ReActAgent,
    AgentMemory,
    AgentPlanner,
    ToolManager,
    RAGValidator,
)

__all__ = [
    # Core
    "Agent",
    "DEFAULT_MODEL",
    # Agents
    "SYMPOSIUM_PI",
    "ELECTROCHEMISTRY_EXPERT",
    "MEMBRANE_SCIENCE_EXPERT",
    "BIOLOGY_EXPERT",
    "NANOFLUIDICS_EXPERT",
    "CUSTOM_SCIENTIFIC_CRITIC",
    # Prompts
    "ROUND_1_DETAILED_AGENDA",
    "ROUND_2_DETAILED_AGENDA",
    "ROUND_3_DETAILED_AGENDA",
    "ROUND_4_DETAILED_AGENDA",
    "ROUND_1_QUESTIONS",
    "ROUND_2_QUESTIONS",
    "ROUND_3_QUESTIONS",
    "ROUND_4_QUESTIONS",
    "RIGOROUS_DISCUSSION_RULES",
    # Enhancements
    "UnifiedAgent",
    "ReActAgent",
    "AgentMemory",
    "AgentPlanner",
    "ToolManager",
    "RAGValidator",
]
