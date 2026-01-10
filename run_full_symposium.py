"""Full Ion Transport Symposium with Unified Enhanced Agents.

This runs a comprehensive multi-round symposium with:
- 4 Domain Experts (Electrochemistry, Membrane Science, Biology, Nanofluidics)
- 1 Symposium Chair (PI)
- 1 Scientific Critic providing feedback
- 4 Rounds of discussion with increasing depth

ALL ENHANCEMENTS ENABLED BY DEFAULT:
✅ ReAct reasoning (explicit thought process)
✅ Persistent memory across rounds
✅ Strategic planning before each round
✅ RAG-first validation (evidence-based responses)
✅ Phase 4 tools (equations, plotting, concept mapping, web search)
✅ Domain-isolated knowledge bases

Legacy version (with optional flags) saved as run_full_symposium_legacy.py
"""

import argparse
import datetime
from pathlib import Path
from typing import Dict
from orchestrator import run_meeting

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

# Unified Agent (all enhancements integrated)
from agents.enhancements import UnifiedAgent


def create_unified_agents(symposium_id: str = None) -> Dict[str, UnifiedAgent]:
    """
    Create all domain experts as UnifiedAgents.

    Each agent has ALL enhancements enabled:
    - ReAct reasoning
    - Persistent memory
    - Strategic planning
    - RAG-first validation
    - Phase 4 tools

    Args:
        symposium_id: ID for this symposium (auto-generated if None)

    Returns:
        Dictionary mapping domain names to UnifiedAgent instances
    """
    if symposium_id is None:
        symposium_id = f"symposium_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"\n🔧 Initializing Unified Agents (Symposium ID: {symposium_id})")
    print("="*80)

    agents = {
        "electrochemistry": UnifiedAgent(
            base_agent=ELECTROCHEMISTRY_EXPERT,
            domain="electrochemistry",
            symposium_id=symposium_id
        ),
        "membrane_science": UnifiedAgent(
            base_agent=MEMBRANE_SCIENCE_EXPERT,
            domain="membrane_science",
            symposium_id=symposium_id
        ),
        "biology": UnifiedAgent(
            base_agent=BIOLOGY_EXPERT,
            domain="biology",
            symposium_id=symposium_id
        ),
        "nanofluidics": UnifiedAgent(
            base_agent=NANOFLUIDICS_EXPERT,
            domain="nanofluidics",
            symposium_id=symposium_id
        ),
    }

    print("\n✅ UNIFIED AGENTS INITIALIZED WITH ALL ENHANCEMENTS:")
    print("   ✓ ReAct reasoning (Thought/Action/Observation)")
    print("   ✓ Persistent memory across rounds")
    print("   ✓ Strategic planning before each round")
    print("   ✓ RAG-first validation (evidence-based responses)")
    print("   ✓ Phase 4 tools:")
    print("     - query_knowledge_base (RAG)")
    print("     - solve_equation (SymPy)")
    print("     - create_plot (Matplotlib)")
    print("     - create_concept_map (NetworkX)")
    print("     - search_recent_papers (Semantic Scholar)")
    print("   ✓ Domain-isolated knowledge bases")
    print("="*80 + "\n")

    return agents


def main(skip_confirmation=False):
    """Run the full 4-round symposium with all enhancements enabled.

    Args:
        skip_confirmation: If True, skip user confirmation prompt
    """

    print("\n" + "="*80)
    print("FULL ION TRANSPORT SYMPOSIUM")
    print("Developing a Unified Theoretical Framework for Ion Transport")
    print("="*80)
    print("\n📋 SYMPOSIUM STRUCTURE:")
    print("   Round 1: Map the Landscape - Understanding current paradigms")
    print("   Round 2: Identify Unifying Principles - Test analogies")
    print("   Round 3: Build Unified Framework - Define common core")
    print("   Round 4: Applications & Future Directions - Cross-pollination")
    print("\n👥 PARTICIPANTS:")
    print("   • Symposium Chair (PI) - Facilitator")
    print("   • Electrochemistry Scientist (UnifiedAgent)")
    print("   • Membrane Science Expert (UnifiedAgent)")
    print("   • Biological Ion Transport Scientist (UnifiedAgent)")
    print("   • Nanofluidics Scientist (UnifiedAgent)")
    print("   • Scientific Critic - Providing rigorous feedback")
    print("\n🔍 KNOWLEDGE BASE:")
    print("   • Each expert has domain-isolated RAG knowledge base")
    print("   • 200+ research papers across 4 domains")
    print("\n💰 ESTIMATED COST: $3.20-4.00 total")
    print("⏱️  ESTIMATED TIME: 15-25 minutes total")
    print("="*80 + "\n")

    # Get user confirmation unless skipped
    if not skip_confirmation:
        response = input("Proceed with full symposium? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\nSymposium cancelled.")
            return
    else:
        print("Auto-confirmed: Starting symposium...\n")

    # Initialize unified agents (all enhancements enabled)
    unified_agents = create_unified_agents()

    # Team composition
    team_lead = SYMPOSIUM_PI
    team_members = (
        unified_agents["electrochemistry"],
        unified_agents["membrane_science"],
        unified_agents["biology"],
        unified_agents["nanofluidics"],
        CUSTOM_SCIENTIFIC_CRITIC,
    )

    # Domain mapping (for backward compatibility with run_meeting)
    agent_to_domain = {
        unified_agents["electrochemistry"]: "electrochemistry",
        unified_agents["membrane_science"]: "membrane_science",
        unified_agents["biology"]: "biology",
        unified_agents["nanofluidics"]: "nanofluidics",
    }

    # Results directory
    results_dir = Path(__file__).parent / "results" / "full_symposium"
    results_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # ROUND 1: Map the Landscape
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 1: MAPPING THE LANDSCAPE OF ION TRANSPORT THEORY")
    print("="*80)
    print("Each expert presents their field's approach to ion transport.")
    print("Critic evaluates rigor and identifies patterns across fields.\n")

    # Agents auto-prepare (planning + memory retrieval)
    for domain, agent in unified_agents.items():
        enhanced_agenda = agent.prepare_for_round(
            round_number=1,
            agenda=ROUND_1_DETAILED_AGENDA,
            questions=list(ROUND_1_QUESTIONS),
            previous_summary=None
        )

    round1_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_1_DETAILED_AGENDA,
        agenda_questions=ROUND_1_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_1_landscape",
        save_name="round1_discussion",
        team_lead=team_lead,
        team_members=team_members,
        num_rounds=2,
        use_rag=True,
        agent_to_domain=agent_to_domain,
        return_summary=True,
    )

    print("\n✅ Round 1 complete. Summary saved.\n")

    # Agents auto-consolidate memories
    for domain, agent in unified_agents.items():
        agent.consolidate_round(1, round1_summary)

    # ========================================================================
    # ROUND 2: Identify Unifying Principles
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 2: IDENTIFYING UNIFYING PRINCIPLES")
    print("="*80)
    print("Testing analogies and finding common mathematical frameworks.")
    print("Building on Round 1 insights.\n")

    # Agents auto-prepare
    for domain, agent in unified_agents.items():
        enhanced_agenda = agent.prepare_for_round(
            round_number=2,
            agenda=ROUND_2_DETAILED_AGENDA,
            questions=list(ROUND_2_QUESTIONS),
            previous_summary=round1_summary
        )

    round2_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_2_DETAILED_AGENDA,
        agenda_questions=ROUND_2_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_2_principles",
        save_name="round2_discussion",
        team_lead=team_lead,
        team_members=team_members,
        summaries=(round1_summary,),
        num_rounds=3,
        use_rag=True,
        agent_to_domain=agent_to_domain,
        return_summary=True,
    )

    print("\n✅ Round 2 complete. Common principles identified.\n")

    # Agents auto-consolidate
    for domain, agent in unified_agents.items():
        agent.consolidate_round(2, round2_summary)

    # ========================================================================
    # ROUND 3: Build Unified Framework
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 3: BUILDING THE UNIFIED FRAMEWORK")
    print("="*80)
    print("Synthesizing insights into a coherent theoretical framework.")
    print("Defining common core + field-specific extensions.\n")

    # Agents auto-prepare
    for domain, agent in unified_agents.items():
        enhanced_agenda = agent.prepare_for_round(
            round_number=3,
            agenda=ROUND_3_DETAILED_AGENDA,
            questions=list(ROUND_3_QUESTIONS),
            previous_summary=round2_summary
        )

    round3_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_3_DETAILED_AGENDA,
        agenda_questions=ROUND_3_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_3_framework",
        save_name="round3_discussion",
        team_lead=team_lead,
        team_members=team_members,
        summaries=(round1_summary, round2_summary),
        num_rounds=4,
        use_rag=True,
        agent_to_domain=agent_to_domain,
        return_summary=True,
    )

    print("\n✅ Round 3 complete. Unified framework developed.\n")

    # Agents auto-consolidate
    for domain, agent in unified_agents.items():
        agent.consolidate_round(3, round3_summary)

    # ========================================================================
    # ROUND 4: Applications and Future Directions
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 4: APPLICATIONS AND FUTURE DIRECTIONS")
    print("="*80)
    print("Cross-field applications, borrowing techniques, future technologies.\n")

    # Agents auto-prepare
    for domain, agent in unified_agents.items():
        enhanced_agenda = agent.prepare_for_round(
            round_number=4,
            agenda=ROUND_4_DETAILED_AGENDA,
            questions=list(ROUND_4_QUESTIONS),
            previous_summary=round3_summary
        )

    round4_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_4_DETAILED_AGENDA,
        agenda_questions=ROUND_4_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_4_applications",
        save_name="round4_discussion",
        team_lead=team_lead,
        team_members=team_members,
        summaries=(round1_summary, round2_summary, round3_summary),
        num_rounds=3,
        use_rag=True,
        agent_to_domain=agent_to_domain,
        return_summary=True,
    )

    print("\n✅ Round 4 complete. Applications identified.\n")

    # Agents auto-consolidate
    for domain, agent in unified_agents.items():
        agent.consolidate_round(4, round4_summary)

    # ========================================================================
    # EXPORT DATA & PROMOTE MEMORIES
    # ========================================================================
    print("\n📊 Exporting agent data...")
    export_dir = results_dir / "agent_data"
    for domain, agent in unified_agents.items():
        agent.export_agent_data(str(export_dir))

    print("\n💾 Promoting memories to long-term storage...")
    for domain, agent in unified_agents.items():
        agent.promote_to_long_term_memory()
    print("✓ Memories saved for future symposiums\n")

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("🎉 FULL SYMPOSIUM COMPLETE!")
    print("="*80)
    print(f"\n📁 All results saved in: {results_dir}")
    print("\n📊 Discussion files created:")
    print("   • round_1_landscape/round1_discussion.md")
    print("   • round_2_principles/round2_discussion.md")
    print("   • round_3_framework/round3_discussion.md")
    print("   • round_4_applications/round4_discussion.md")
    print("\n📈 Agent data exported:")
    print(f"   • agent_data/ (plans, statistics for each domain)")
    print("\n🔬 FINAL SYNTHESIS:")
    print("-" * 80)
    print(round4_summary)
    print("-" * 80)
    print("\n✨ Next Steps:")
    print("   1. Review each round's discussion in the results folder")
    print("   2. Extract the unified framework from Round 3")
    print("   3. Identify high-impact applications from Round 4")
    print("   4. Use insights for your research/paper/grant proposal")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full Ion Transport Symposium")
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt and start immediately"
    )
    args = parser.parse_args()

    main(skip_confirmation=args.yes)
