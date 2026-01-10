"""
Enhanced Agent Capabilities for Ion Transport Symposium

This module provides advanced agent features built as enhancement layers
on top of the base virtual_lab Agent class:

- ReAct Layer: Explicit reasoning traces (Thought/Action/Observation) ✅ Phase 1
- Memory System: Persistent learning across symposium rounds ✅ Phase 2
- Planning System: Strategic contribution planning ✅ Phase 3
- Phase 4 Tools: Advanced tools (equations, plotting, concepts, web search) ✅ Phase 4
- UnifiedAgent: All-in-one agent wrapper with all enhancements ✅ Phase 4

All enhancements are backward-compatible and can be toggled on/off.
For new projects, use UnifiedAgent (integrates all phases by default).
"""

from agents.enhancements.react_layer import ReActAgent, enable_react_for_agents
from agents.enhancements.react_parser import (
    ReActParser,
    extract_reasoning_traces,
    format_discussion_with_traces,
    analyze_discussion_quality,
)
from agents.enhancements.memory_system import AgentMemory, create_memory_for_all_domains
from agents.enhancements.memory_config import (
    MemoryConfig,
    DEFAULT_MEMORY_CONFIG,
    COST_OPTIMIZED_CONFIG,
    QUALITY_OPTIMIZED_CONFIG,
    MemoryType,
    MemoryImportance,
)
from agents.enhancements.planning_system import (
    AgentPlanner,
    create_planners_for_agents,
    plan_round_for_all_agents,
)
from agents.enhancements.plan_templates import (
    ContributionPlan,
    get_planning_prompt,
    format_plan_for_display,
    PLANNING_COST_ESTIMATES,
)
from agents.enhancements.tool_manager import ToolManager
from agents.enhancements.rag_validator import RAGValidator, ResponseClassifier
from agents.enhancements.unified_agent import UnifiedAgent

__all__ = [
    # ReAct (Phase 1)
    "ReActAgent",
    "enable_react_for_agents",
    "ReActParser",
    "extract_reasoning_traces",
    "format_discussion_with_traces",
    "analyze_discussion_quality",
    # Memory (Phase 2)
    "AgentMemory",
    "create_memory_for_all_domains",
    "MemoryConfig",
    "DEFAULT_MEMORY_CONFIG",
    "COST_OPTIMIZED_CONFIG",
    "QUALITY_OPTIMIZED_CONFIG",
    "MemoryType",
    "MemoryImportance",
    # Planning (Phase 3)
    "AgentPlanner",
    "create_planners_for_agents",
    "plan_round_for_all_agents",
    "ContributionPlan",
    "get_planning_prompt",
    "format_plan_for_display",
    "PLANNING_COST_ESTIMATES",
    # Phase 4: Tools & Validation
    "ToolManager",
    "RAGValidator",
    "ResponseClassifier",
    # Unified Agent (All Phases)
    "UnifiedAgent",
]

__version__ = "0.4.0"  # Phase 4 complete - UnifiedAgent ready
