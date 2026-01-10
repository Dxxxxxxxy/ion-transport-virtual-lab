"""
Planning Templates and Prompts

Templates for strategic contribution planning before each round.
Agents use these to plan their arguments, evidence gathering, and questions.

Author: Ion Transport Virtual Lab
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ContributionPlan:
    """
    A strategic plan for an agent's contribution to a discussion round.

    Attributes:
        main_points: Key arguments to make
        evidence_needed: RAG queries to run for supporting evidence
        analogies_to_test: Cross-domain comparisons to explore
        questions_for_others: Questions to pose to other experts
        key_concepts: Important concepts to introduce
        estimated_tool_calls: Expected number of tool calls
        priority: High/Medium/Low priority for this contribution
    """
    main_points: List[str]
    evidence_needed: List[str]
    analogies_to_test: List[str]
    questions_for_others: List[str]
    key_concepts: List[str]
    estimated_tool_calls: int
    priority: str = "Medium"

    def to_dict(self):
        """Convert to dictionary format."""
        return {
            "main_points": self.main_points,
            "evidence_needed": self.evidence_needed,
            "analogies_to_test": self.analogies_to_test,
            "questions_for_others": self.questions_for_others,
            "key_concepts": self.key_concepts,
            "estimated_tool_calls": self.estimated_tool_calls,
            "priority": self.priority,
        }


# Planning prompt template
PLANNING_PROMPT_TEMPLATE = """You are preparing to contribute to a scientific symposium. Before speaking, you need to strategically plan your contribution.

SYMPOSIUM CONTEXT:
Round: {round_number}
Agenda: {agenda}

Questions to Address:
{questions}

Previous Discussion Summary (if available):
{previous_summary}

YOUR TASK: Create a strategic plan for your contribution. Think carefully about:

1. MAIN POINTS (2-4 key arguments you want to make)
   - What are the most important insights from your field?
   - What unique perspective can you offer?
   - How does this address the agenda questions?

2. EVIDENCE NEEDED (specific queries for your knowledge base)
   - What specific data or examples do you need?
   - What quantitative evidence would strengthen your arguments?
   - Be specific in your queries (e.g., "EDL capacitance in sub-1nm pores" not just "capacitance")

3. ANALOGIES TO TEST (connections to other fields)
   - What analogies or comparisons might be productive?
   - How does your field's approach relate to others?
   - What cross-domain insights can you explore?

4. QUESTIONS FOR OTHERS (to deepen understanding)
   - What would you like to learn from other experts?
   - What clarifications would be helpful?
   - What challenges or counterpoints might arise?

5. KEY CONCEPTS (important terminology or frameworks to introduce)
   - What concepts from your field are essential?
   - What definitions or frameworks should be established?

Format your response as JSON:
{{
  "main_points": ["point 1", "point 2", ...],
  "evidence_needed": ["query 1", "query 2", ...],
  "analogies_to_test": ["analogy 1", "analogy 2", ...],
  "questions_for_others": ["question 1", "question 2", ...],
  "key_concepts": ["concept 1", "concept 2", ...],
  "estimated_tool_calls": N,
  "priority": "High/Medium/Low"
}}

Be strategic and focused. Quality over quantity.
"""


# Simpler planning prompt (for cost optimization)
SIMPLE_PLANNING_PROMPT = """Plan your contribution for this round.

Agenda: {agenda}
Questions: {questions}

List:
1. Main points to make (2-3)
2. Evidence queries needed (1-3)
3. Questions for others (1-2)

Keep it brief and focused.
"""


# Planning prompt for building on previous rounds
BUILDING_PLANNING_PROMPT = """You are planning your contribution for Round {round_number}.

PREVIOUS INSIGHTS (from your memory):
{memory_context}

CURRENT AGENDA:
{agenda}

QUESTIONS:
{questions}

YOUR TASK: Plan how to BUILD ON your previous insights while addressing the new agenda.

Focus on:
1. How your Round 1-{prev_round} insights connect to this round's focus
2. New evidence or examples that extend your previous arguments
3. Deeper connections or applications of earlier ideas
4. Questions that emerged from previous rounds

Format as JSON:
{{
  "main_points": ["Building on X from Round {prev_round}, I want to explore Y..."],
  "evidence_needed": ["specific query 1", "specific query 2"],
  "analogies_to_test": ["connection 1", "connection 2"],
  "questions_for_others": ["question 1", "question 2"],
  "key_concepts": ["new concept 1", "new concept 2"],
  "estimated_tool_calls": N,
  "priority": "High/Medium/Low"
}}
"""


# Round-specific planning guidance
ROUND_SPECIFIC_GUIDANCE = {
    1: """
ROUND 1 PLANNING GUIDANCE:
This is the landscape mapping round. Focus on:
- Establishing your field's fundamental approach
- Providing ONE concrete, quantitative example
- Clearly stating assumptions in your models
- Identifying what's universal vs. field-specific in your approach
    """,

    2: """
ROUND 2 PLANNING GUIDANCE:
This round tests analogies and finds common principles. Focus on:
- Testing proposed analogies between your field and others
- Providing quantitative comparisons when possible
- Clarifying where analogies hold and where they break
- Proposing unifying equations or principles
    """,

    3: """
ROUND 3 PLANNING GUIDANCE:
This round builds the unified framework. Focus on:
- Validating or challenging the proposed framework
- Defining your field's unique "boundary conditions"
- Creating terminology mappings to common framework
- Identifying knowledge gaps and cross-field opportunities
    """,

    4: """
ROUND 4 PLANNING GUIDANCE:
This round explores applications. Focus on:
- Proposing specific cross-field applications
- Identifying measurements or techniques to borrow
- Suggesting challenge problems for the unified framework
- Envisioning future technologies
    """,
}


def get_planning_prompt(
    round_number: int,
    agenda: str,
    questions: List[str],
    previous_summary: Optional[str] = None,
    memory_context: Optional[str] = None,
    use_simple: bool = False
) -> str:
    """
    Generate a planning prompt for an agent.

    Args:
        round_number: Which round (1-4)
        agenda: Round agenda text
        questions: List of questions to address
        previous_summary: Summary from previous rounds
        memory_context: Relevant memories to build on
        use_simple: Use simpler prompt for cost savings

    Returns:
        Formatted planning prompt string
    """
    # Format questions
    questions_text = "\n".join(f"- {q}" for q in questions)

    if use_simple:
        return SIMPLE_PLANNING_PROMPT.format(
            agenda=agenda,
            questions=questions_text
        )

    # Add round-specific guidance
    round_guidance = ROUND_SPECIFIC_GUIDANCE.get(round_number, "")
    enhanced_agenda = agenda + "\n\n" + round_guidance

    # If memory context available, use building prompt
    if memory_context and round_number > 1:
        return BUILDING_PLANNING_PROMPT.format(
            round_number=round_number,
            prev_round=round_number - 1,
            memory_context=memory_context,
            agenda=enhanced_agenda,
            questions=questions_text
        )

    # Standard planning prompt
    return PLANNING_PROMPT_TEMPLATE.format(
        round_number=round_number,
        agenda=enhanced_agenda,
        questions=questions_text,
        previous_summary=previous_summary if previous_summary else "N/A - This is Round 1"
    )


# Plan execution template (shown to agent during discussion)
PLAN_EXECUTION_TEMPLATE = """
================================================================================
YOUR CONTRIBUTION PLAN FOR THIS ROUND:
================================================================================

Main Points to Make:
{main_points}

Evidence to Gather:
{evidence_needed}

Analogies to Explore:
{analogies_to_test}

Questions for Others:
{questions_for_others}

Key Concepts to Introduce:
{key_concepts}

================================================================================
Execute this plan by using your query_knowledge_base tool to gather evidence,
then presenting your arguments clearly and concisely.
================================================================================
"""


def format_plan_for_display(plan: ContributionPlan) -> str:
    """
    Format a plan for display to the agent.

    Args:
        plan: ContributionPlan instance

    Returns:
        Formatted string
    """
    main_points = "\n".join(f"  • {p}" for p in plan.main_points)
    evidence = "\n".join(f"  • {e}" for e in plan.evidence_needed)
    analogies = "\n".join(f"  • {a}" for a in plan.analogies_to_test)
    questions = "\n".join(f"  • {q}" for q in plan.questions_for_others)
    concepts = "\n".join(f"  • {c}" for c in plan.key_concepts)

    return PLAN_EXECUTION_TEMPLATE.format(
        main_points=main_points,
        evidence=evidence,
        analogies=analogies,
        questions=questions,
        key_concepts=concepts
    )


# Cost estimates for planning
PLANNING_COST_ESTIMATES = {
    "per_plan_generation": 0.01,  # ~$0.01 per plan (gpt-4o-mini)
    "per_round_all_agents": 0.04,  # ~$0.04 for 4 agents
    "full_symposium": 0.16,  # ~$0.16 for 4 rounds
}
