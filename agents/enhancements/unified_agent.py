"""
Unified Agent - Fully-Enhanced Expert Agent

Integrates all enhancement layers into a single, cohesive agent wrapper:
- ReAct reasoning (Phase 1)
- Persistent memory (Phase 2)
- Strategic planning (Phase 3)
- Advanced tools (Phase 4) - RAG + equation solver + plotting + concept mapping + web search
- RAG-first validation (ensures evidence-based responses)

This is the recommended interface for creating expert agents.
"""

from typing import Optional, List, Dict, Any, Tuple
from agents.base_agent import Agent
from agents.enhancements.memory_system import AgentMemory
from agents.enhancements.memory_config import MemoryConfig, DEFAULT_MEMORY_CONFIG
from agents.enhancements.planning_system import AgentPlanner
from agents.enhancements.tool_manager import ToolManager
from agents.enhancements.rag_validator import RAGValidator
from agents.enhancements.react_layer import REACT_INSTRUCTION_TEMPLATE


class UnifiedAgent:
    """
    Fully-enhanced agent with all capabilities integrated.

    Combines:
    - Base Agent (from virtual_lab)
    - AgentMemory (persistent learning)
    - AgentPlanner (strategic planning)
    - ToolManager (RAG + Phase 4 tools)
    - RAGValidator (evidence-based responses)
    - ReAct reasoning (explicit thought process)

    Interface:
    - Drop-in replacement for Agent
    - All properties delegated to base_agent
    - Enhanced role with ReAct + tool instructions
    - Domain-isolated knowledge base
    """

    def __init__(
        self,
        base_agent: Agent,
        domain: str,
        memory_config: Optional[MemoryConfig] = None,
        symposium_id: Optional[str] = None,
        planning_model: str = "gpt-4o-mini"
    ):
        """
        Initialize UnifiedAgent with all enhancements.

        Args:
            base_agent: Base Agent from virtual_lab
            domain: Agent's domain (electrochemistry, membrane_science, biology, nanofluidics)
            memory_config: Memory configuration (default: DEFAULT_MEMORY_CONFIG)
            symposium_id: Symposium ID for memory persistence (auto-generated if None)
            planning_model: Model for planning (default: gpt-4o-mini for cost)
        """
        # Core components
        self.base_agent = base_agent
        self.domain = domain

        # Enhancement layers (always enabled)
        config = memory_config if memory_config is not None else DEFAULT_MEMORY_CONFIG
        self.memory = AgentMemory(domain, config, symposium_id)
        self.planner = AgentPlanner(base_agent.title, domain, planning_model)
        self.tool_manager = ToolManager(domain)
        self.rag_validator = RAGValidator(domain)

        # State tracking
        self.current_round = 0
        self.conversation_history = []

    # ========================================================================
    # Agent Interface Properties (delegated to base_agent)
    # ========================================================================

    @property
    def title(self) -> str:
        """Agent's title."""
        return self.base_agent.title

    @property
    def expertise(self) -> str:
        """Agent's expertise."""
        return self.base_agent.expertise

    @property
    def goal(self) -> str:
        """Agent's goal."""
        return self.base_agent.goal

    @property
    def model(self) -> str:
        """LLM model."""
        return self.base_agent.model

    @property
    def role(self) -> str:
        """Enhanced role with ReAct + RAG-first instructions."""
        return self.enhanced_role

    @property
    def prompt(self) -> str:
        """Full formatted prompt."""
        return self.base_agent.prompt

    @property
    def message(self) -> Dict[str, str]:
        """OpenAI-compatible system message."""
        return {
            "role": "system",
            "content": self.enhanced_role
        }

    @property
    def enhanced_role(self) -> str:
        """
        Combine base role with ReAct instructions and RAG-first guidance.

        Returns:
            Enhanced role string with:
            - Base agent role
            - ReAct formatting instructions
            - RAG-first mandate
            - Tool catalog
        """
        base_role = self.base_agent.role

        # RAG-first mandate
        rag_mandate = """

=================================================================================
⚠️  MANDATORY RAG-FIRST PROTOCOL ⚠️
=================================================================================

CRITICAL REQUIREMENT:
For ALL substantive scientific claims (especially those with numerical values,
mechanisms, or comparisons), you MUST query your knowledge base FIRST using
the query_knowledge_base tool before making the claim.

REQUIRED WORKFLOW:
1. Identify the substantive claim you want to make
2. Query knowledge base for supporting evidence
3. Formulate claim with proper citations

EXAMPLES OF SUBSTANTIVE CLAIMS REQUIRING RAG:
✓ "EDL capacitance can reach 280 F/g in sub-nm pores"
✓ "K+ channels achieve 1000:1 selectivity over Na+"
✓ "Selectivity mechanisms include dehydration and binding site chemistry"

EXAMPLES OF SIMPLE RESPONSES NOT REQUIRING RAG:
✓ "I agree with your point about selectivity"
✓ "That's an interesting analogy"
✓ "Could you clarify what you mean by..."

If you make substantive claims without RAG evidence, your response will be
rejected and you will be asked to retry with proper evidence retrieval.

=================================================================================
"""

        # ReAct instructions
        react_instructions = REACT_INSTRUCTION_TEMPLATE

        # Tool catalog
        tool_catalog = f"\n\n{self.tool_manager.get_available_tools_description()}\n"

        # Combine all elements
        enhanced = base_role + rag_mandate + react_instructions + tool_catalog

        return enhanced

    @property
    def openai_tools(self) -> List[Dict]:
        """
        Get all tools as OpenAI function schemas.

        Returns:
            List of OpenAI function schema dicts (RAG + Phase 4 tools)
        """
        return self.tool_manager.get_all_openai_tools()

    # ========================================================================
    # Core Methods
    # ========================================================================

    def prepare_for_round(
        self,
        round_number: int,
        agenda: str,
        questions: List[str],
        previous_summary: Optional[str] = None
    ) -> str:
        """
        Prepare for a symposium round: planning + memory retrieval.

        Args:
            round_number: Round number (1-4)
            agenda: Round agenda text
            questions: Discussion questions
            previous_summary: Summary from previous round (optional)

        Returns:
            Enhanced agenda with plan and memories injected
        """
        self.current_round = round_number

        # Step 1: Recall relevant memories from previous rounds
        memory_context = ""
        if round_number > 1:
            query = f"{agenda}\n{' '.join(questions)}"
            memories = self.memory.recall(query=query, top_k=3)

            if memories:
                memory_context = "\n\n" + "="*80 + "\n"
                memory_context += f"🧠 MEMORIES FROM PREVIOUS ROUNDS:\n"
                memory_context += "="*80 + "\n\n"
                for i, mem in enumerate(memories, 1):
                    memory_context += f"[Memory {i}] {mem['content']}\n\n"
                memory_context += "="*80 + "\n"

        # Step 2: Generate strategic plan
        plan = self.planner.plan_round_contribution(
            round_number=round_number,
            agenda=agenda,
            questions=questions,
            previous_summary=previous_summary,
            memory_context=memory_context if memory_context else None,
            save_plan=True
        )

        # Step 3: Format plan for display
        plan_context = "\n\n" + "="*80 + "\n"
        plan_context += f"📋 YOUR STRATEGIC PLAN FOR ROUND {round_number}:\n"
        plan_context += "="*80 + "\n\n"
        plan_context += self.planner.format_plan_for_agent(round_number)
        plan_context += "\n" + "="*80 + "\n"

        # Combine everything
        enhanced_agenda = agenda + memory_context + plan_context

        return enhanced_agenda

    def respond(
        self,
        messages: List[Dict],
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate response with tool support and RAG validation.

        Pipeline:
        1. Call OpenAI with all tools available
        2. Execute tool calls (if any)
        3. Get final response
        4. Validate RAG usage for substantive claims
        5. Retry if validation fails
        6. Return response + metadata

        Args:
            messages: OpenAI conversation messages
            **kwargs: Additional OpenAI API parameters

        Returns:
            Tuple of (response_text, metadata_dict)
            - response_text: Final validated response
            - metadata: {tool_calls, validation_passed, retry_count, etc.}
        """
        # This method would typically be called by the virtual_lab framework
        # For now, it serves as a placeholder showing the intended flow

        # NOTE: The actual OpenAI API calls are handled by virtual_lab.run_meeting()
        # This method defines the intended validation and retry logic

        metadata = {
            "tool_calls_made": [],
            "validation_passed": False,
            "retry_count": 0,
            "tools_available": len(self.openai_tools)
        }

        # Placeholder - actual implementation would integrate with run_meeting
        # The key is that RAGValidator will check responses and force retries if needed

        return ("", metadata)

    def consolidate_round(
        self,
        round_number: int,
        round_summary: str,
        discussion_messages: Optional[List[Dict]] = None
    ):
        """
        Post-round consolidation: extract and store memories.

        Args:
            round_number: Round that just completed
            round_summary: Summary of the round
            discussion_messages: Optional conversation messages
        """
        self.memory.consolidate_round(
            round_summary=round_summary,
            round_number=round_number,
            discussion_messages=discussion_messages,
            use_llm=True  # Use LLM for quality insight extraction
        )

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about agent's activity.

        Returns:
            Dictionary with tool usage, memory stats, validation stats
        """
        return {
            "domain": self.domain,
            "current_round": self.current_round,
            "tool_usage": self.tool_manager.get_usage_statistics(),
            "memory_stats": {
                "symposium_id": self.memory.symposium_id,
                "collection_name": self.memory.collection.name
            },
            "validation_stats": self.rag_validator.get_validation_stats(),
            "planning_cost": self.planner.get_total_planning_cost()
        }

    def export_agent_data(self, output_dir: str):
        """
        Export all agent data (plans, memories, stats).

        Args:
            output_dir: Directory to save exports
        """
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Export plans
        plan_file = output_path / f"{self.domain}_plans.json"
        self.planner.export_plans(plan_file)

        # Export statistics
        import json
        stats_file = output_path / f"{self.domain}_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.get_statistics(), f, indent=2)

        print(f"✓ Exported {self.domain} agent data to {output_dir}")

    def promote_to_long_term_memory(self):
        """Promote working memories to long-term storage."""
        self.memory.promote_to_long_term()

    def reset_for_new_symposium(self, new_symposium_id: Optional[str] = None):
        """
        Reset agent for a new symposium.

        Promotes current memories to long-term and starts fresh.

        Args:
            new_symposium_id: ID for new symposium (auto-generated if None)
        """
        # Promote current memories
        self.promote_to_long_term_memory()

        # Reset state
        self.current_round = 0
        self.conversation_history = []

        # Create new memory instance
        self.memory = AgentMemory(
            self.domain,
            self.memory.config,
            new_symposium_id
        )

        # Reset validators and managers
        self.rag_validator.reset_stats()
        self.tool_manager.reset_usage_stats()

        print(f"✓ {self.title} reset for new symposium: {self.memory.symposium_id}")

    # ========================================================================
    # Special Methods
    # ========================================================================

    def __repr__(self) -> str:
        return f"UnifiedAgent(title='{self.title}', domain='{self.domain}')"

    def __str__(self) -> str:
        return f"{self.title} [UnifiedAgent: {self.domain}]"

    def __hash__(self) -> int:
        # Hash based on base agent's hash
        return hash(self.base_agent)

    def __eq__(self, other) -> bool:
        if isinstance(other, UnifiedAgent):
            return self.base_agent == other.base_agent
        elif isinstance(other, Agent):
            return self.base_agent == other
        return False
