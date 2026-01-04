"""Full Ion Transport Symposium with 4 Experts and Scientific Critic.

This runs a comprehensive multi-round symposium with:
- 4 Domain Experts (Electrochemistry, Membrane Science, Biology, Nanofluidics)
- 1 Symposium Chair (PI)
- 1 Scientific Critic providing feedback
- 4 Rounds of discussion with increasing depth
"""

from pathlib import Path
from virtual_lab.run_meeting import run_meeting
from ion_transport.agents.detailed_agents import (
    SYMPOSIUM_PI,
    ELECTROCHEMISTRY_EXPERT,
    MEMBRANE_SCIENCE_EXPERT,
    BIOLOGY_EXPERT,
    NANOFLUIDICS_EXPERT,
    CUSTOM_SCIENTIFIC_CRITIC,
)
from ion_transport.prompts.detailed_prompts import (
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


def main():
    """Run the full 4-round symposium with all experts."""

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
    print("   • Electrochemistry Scientist")
    print("   • Membrane Science Expert")
    print("   • Biological Ion Transport Scientist")
    print("   • Nanofluidics Scientist")
    print("   • Scientific Critic - Providing rigorous feedback")
    print("\n🔍 KNOWLEDGE BASE:")
    print("   • Each expert has access to their curated paper collection via RAG")
    print("   • Citations automatically extracted and formatted")
    print("\n💰 ESTIMATED COST: $2.50-4.00 total")
    print("⏱️  ESTIMATED TIME: 15-25 minutes total")
    print("="*80 + "\n")

    # Get user confirmation
    response = input("Proceed with full symposium? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\nSymposium cancelled.")
        return

    # Define team
    team_lead = SYMPOSIUM_PI

    # Team members with critic providing feedback after each expert
    team_members = (
        ELECTROCHEMISTRY_EXPERT,
        MEMBRANE_SCIENCE_EXPERT,
        BIOLOGY_EXPERT,
        NANOFLUIDICS_EXPERT,
        CUSTOM_SCIENTIFIC_CRITIC,  # Critic summarizes all expert contributions
    )

    # Map agents to their knowledge base domains (for RAG tool)
    agent_to_domain = {
        ELECTROCHEMISTRY_EXPERT: "electrochemistry",
        MEMBRANE_SCIENCE_EXPERT: "membrane_science",
        BIOLOGY_EXPERT: "biology",
        NANOFLUIDICS_EXPERT: "nanofluidics",
        # PI and Critic don't have domain-specific knowledge bases
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

    round1_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_1_DETAILED_AGENDA,
        agenda_questions=ROUND_1_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_1_landscape",
        save_name="round1_discussion",
        team_lead=team_lead,
        team_members=team_members,
        num_rounds=2,  # 2 rounds of back-and-forth
        use_rag=True,  # Enable RAG knowledge base queries
        agent_to_domain=agent_to_domain,  # Map agents to their domains
        return_summary=True,
    )

    print("\n✅ Round 1 complete. Summary saved.\n")

    # ========================================================================
    # ROUND 2: Identify Unifying Principles
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 2: IDENTIFYING UNIFYING PRINCIPLES")
    print("="*80)
    print("Testing analogies and finding common mathematical frameworks.")
    print("Building on Round 1 insights.\n")

    round2_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_2_DETAILED_AGENDA,
        agenda_questions=ROUND_2_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_2_principles",
        save_name="round2_discussion",
        team_lead=team_lead,
        team_members=team_members,
        summaries=(round1_summary,),  # Include Round 1 as context
        num_rounds=3,  # More rounds for deeper discussion
        use_rag=True,  # Enable RAG knowledge base queries
        agent_to_domain=agent_to_domain,  # Map agents to their domains
        return_summary=True,
    )

    print("\n✅ Round 2 complete. Common principles identified.\n")

    # ========================================================================
    # ROUND 3: Build Unified Framework
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 3: BUILDING THE UNIFIED FRAMEWORK")
    print("="*80)
    print("Synthesizing insights into a coherent theoretical framework.")
    print("Defining common core + field-specific extensions.\n")

    round3_summary = run_meeting(
        meeting_type="team",
        agenda=ROUND_3_DETAILED_AGENDA,
        agenda_questions=ROUND_3_QUESTIONS,
        agenda_rules=RIGOROUS_DISCUSSION_RULES,
        save_dir=results_dir / "round_3_framework",
        save_name="round3_discussion",
        team_lead=team_lead,
        team_members=team_members,
        summaries=(round1_summary, round2_summary),  # Build on previous rounds
        num_rounds=4,  # Most important round - needs thorough discussion
        use_rag=True,  # Enable RAG knowledge base queries
        agent_to_domain=agent_to_domain,  # Map agents to their domains
        return_summary=True,
    )

    print("\n✅ Round 3 complete. Unified framework developed.\n")

    # ========================================================================
    # ROUND 4: Applications and Future Directions
    # ========================================================================
    print("\n" + "="*80)
    print("ROUND 4: APPLICATIONS AND FUTURE DIRECTIONS")
    print("="*80)
    print("Cross-field applications, borrowing techniques, future technologies.\n")

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
        use_rag=True,  # Enable RAG knowledge base queries
        agent_to_domain=agent_to_domain,  # Map agents to their domains
        return_summary=True,
    )

    print("\n✅ Round 4 complete. Applications identified.\n")

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
    main()
