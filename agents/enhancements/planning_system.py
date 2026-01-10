"""
Strategic Planning System for AI Agents

Implements pre-round and in-turn planning to help agents strategically
prepare their contributions before speaking.

Author: Ion Transport Virtual Lab
"""

import json
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pathlib import Path

from agents.enhancements.plan_templates import (
    ContributionPlan,
    get_planning_prompt,
    format_plan_for_display,
    PLANNING_COST_ESTIMATES,
)


class AgentPlanner:
    """
    Strategic planner for AI agents.

    Helps agents create structured plans before contributing to discussions,
    improving focus, coherence, and evidence gathering.
    """

    def __init__(
        self,
        agent_title: str,
        agent_domain: str,
        planning_model: str = "gpt-4o-mini",  # Use cheaper model for planning
        use_simple_prompts: bool = False
    ):
        """
        Initialize agent planner.

        Args:
            agent_title: Title of the agent (e.g., "Electrochemistry Scientist")
            agent_domain: Domain of the agent (for context)
            planning_model: LLM model to use for planning (default: gpt-4o-mini for cost)
            use_simple_prompts: Use simpler prompts for cost savings
        """
        self.agent_title = agent_title
        self.agent_domain = agent_domain
        self.planning_model = planning_model
        self.use_simple_prompts = use_simple_prompts

        # Initialize OpenAI client
        self.client = OpenAI()

        # Track generated plans
        self.plans: Dict[int, ContributionPlan] = {}  # round_number -> plan
        self.planning_costs: List[float] = []

    def plan_round_contribution(
        self,
        round_number: int,
        agenda: str,
        questions: List[str],
        previous_summary: Optional[str] = None,
        memory_context: Optional[str] = None,
        save_plan: bool = True
    ) -> ContributionPlan:
        """
        Create a strategic plan for a round contribution.

        Args:
            round_number: Which round (1-4)
            agenda: Round agenda text
            questions: List of questions to address
            previous_summary: Summary from previous rounds
            memory_context: Relevant memories to build on
            save_plan: Whether to save plan in self.plans

        Returns:
            ContributionPlan object
        """
        print(f"  📋 Planning contribution for {self.agent_title}...")

        # Generate planning prompt
        planning_prompt = get_planning_prompt(
            round_number=round_number,
            agenda=agenda,
            questions=questions,
            previous_summary=previous_summary,
            memory_context=memory_context,
            use_simple=self.use_simple_prompts
        )

        try:
            # Call LLM to generate plan
            response = self.client.chat.completions.create(
                model=self.planning_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a strategic planner for a {self.agent_domain} expert in a scientific symposium."
                    },
                    {
                        "role": "user",
                        "content": planning_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for focused planning
                max_tokens=800,
            )

            response_text = response.choices[0].message.content

            # Parse the plan
            plan = self._parse_plan_response(response_text)

            # Save plan
            if save_plan:
                self.plans[round_number] = plan

            # Track cost (approximate)
            estimated_cost = PLANNING_COST_ESTIMATES["per_plan_generation"]
            self.planning_costs.append(estimated_cost)

            print(f"    ✓ Plan created: {len(plan.main_points)} points, {len(plan.evidence_needed)} queries")

            return plan

        except Exception as e:
            print(f"    ⚠ Planning failed: {e}")
            # Return default plan
            return self._create_default_plan(questions)

    def _parse_plan_response(self, response_text: str) -> ContributionPlan:
        """
        Parse LLM response into ContributionPlan.

        Args:
            response_text: LLM response text

        Returns:
            ContributionPlan object
        """
        try:
            # Try to extract JSON from response
            if "```json" in response_text:
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            elif "```" in response_text:
                json_match = re.search(r'```\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            # Parse JSON
            plan_dict = json.loads(response_text)

            # Create ContributionPlan
            return ContributionPlan(
                main_points=plan_dict.get("main_points", []),
                evidence_needed=plan_dict.get("evidence_needed", []),
                analogies_to_test=plan_dict.get("analogies_to_test", []),
                questions_for_others=plan_dict.get("questions_for_others", []),
                key_concepts=plan_dict.get("key_concepts", []),
                estimated_tool_calls=plan_dict.get("estimated_tool_calls", 0),
                priority=plan_dict.get("priority", "Medium")
            )

        except Exception as e:
            print(f"    ⚠ Could not parse plan JSON: {e}")
            # Try to extract lists from text
            return self._extract_plan_from_text(response_text)

    def _extract_plan_from_text(self, text: str) -> ContributionPlan:
        """
        Extract plan from unstructured text (fallback).

        Args:
            text: Response text

        Returns:
            ContributionPlan with extracted items
        """
        # Simple extraction: look for numbered lists or bullet points
        lines = text.split('\n')

        main_points = []
        evidence_needed = []
        questions = []

        current_section = None
        for line in lines:
            line = line.strip()

            # Detect sections
            if 'main point' in line.lower():
                current_section = 'points'
            elif 'evidence' in line.lower() or 'quer' in line.lower():
                current_section = 'evidence'
            elif 'question' in line.lower():
                current_section = 'questions'

            # Extract items (numbered or bulleted)
            if re.match(r'^[\d\-\*•]', line):
                item = re.sub(r'^[\d\-\*•\.\)]+\s*', '', line)
                if item:
                    if current_section == 'points':
                        main_points.append(item)
                    elif current_section == 'evidence':
                        evidence_needed.append(item)
                    elif current_section == 'questions':
                        questions.append(item)

        return ContributionPlan(
            main_points=main_points[:4],  # Limit to 4
            evidence_needed=evidence_needed[:5],  # Limit to 5
            analogies_to_test=[],
            questions_for_others=questions[:3],  # Limit to 3
            key_concepts=[],
            estimated_tool_calls=len(evidence_needed),
            priority="Medium"
        )

    def _create_default_plan(self, questions: List[str]) -> ContributionPlan:
        """
        Create a minimal default plan if planning fails.

        Args:
            questions: Questions to address

        Returns:
            Basic ContributionPlan
        """
        return ContributionPlan(
            main_points=[f"Address: {q}" for q in questions[:2]],
            evidence_needed=["relevant findings in my field"],
            analogies_to_test=[],
            questions_for_others=[],
            key_concepts=[],
            estimated_tool_calls=1,
            priority="Medium"
        )

    def get_plan_for_round(self, round_number: int) -> Optional[ContributionPlan]:
        """
        Retrieve saved plan for a round.

        Args:
            round_number: Round number

        Returns:
            ContributionPlan if exists, None otherwise
        """
        return self.plans.get(round_number)

    def format_plan_for_agent(self, round_number: int) -> str:
        """
        Format saved plan for display to agent.

        Args:
            round_number: Round number

        Returns:
            Formatted plan string (empty if no plan)
        """
        plan = self.get_plan_for_round(round_number)
        if plan:
            return format_plan_for_display(plan)
        return ""

    def get_total_planning_cost(self) -> float:
        """
        Get total estimated cost of planning.

        Returns:
            Total cost in dollars
        """
        return sum(self.planning_costs)

    def export_plans(self, output_path: Path):
        """
        Export all plans to JSON file.

        Args:
            output_path: Path to save JSON file
        """
        plans_dict = {
            round_num: plan.to_dict()
            for round_num, plan in self.plans.items()
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                "agent": self.agent_title,
                "domain": self.agent_domain,
                "plans": plans_dict,
                "total_cost": self.get_total_planning_cost()
            }, f, indent=2)

        print(f"  ✓ Plans exported to {output_path}")


def create_planners_for_agents(
    agents_info: Dict[str, str],
    planning_model: str = "gpt-4o-mini",
    use_simple: bool = False
) -> Dict[str, AgentPlanner]:
    """
    Create planners for multiple agents.

    Args:
        agents_info: Dict mapping agent titles to domains
        planning_model: Model to use for planning
        use_simple: Use simple prompts for cost savings

    Returns:
        Dict mapping agent titles to AgentPlanner instances

    Example:
        >>> planners = create_planners_for_agents({
        ...     "Electrochemistry Scientist": "electrochemistry",
        ...     "Nanofluidics Scientist": "nanofluidics"
        ... })
    """
    planners = {}

    for title, domain in agents_info.items():
        planners[title] = AgentPlanner(
            agent_title=title,
            agent_domain=domain,
            planning_model=planning_model,
            use_simple_prompts=use_simple
        )

    return planners


def plan_round_for_all_agents(
    planners: Dict[str, AgentPlanner],
    round_number: int,
    agenda: str,
    questions: List[str],
    previous_summary: Optional[str] = None,
    memory_contexts: Optional[Dict[str, str]] = None
) -> Dict[str, ContributionPlan]:
    """
    Generate plans for all agents for a round.

    Args:
        planners: Dict of AgentPlanner instances
        round_number: Which round
        agenda: Round agenda
        questions: Questions to address
        previous_summary: Summary from previous rounds
        memory_contexts: Dict mapping agent titles to memory context

    Returns:
        Dict mapping agent titles to ContributionPlan instances
    """
    print(f"\n📋 Planning Round {round_number} contributions for all agents...")

    plans = {}

    for title, planner in planners.items():
        memory_context = None
        if memory_contexts and title in memory_contexts:
            memory_context = memory_contexts[title]

        plan = planner.plan_round_contribution(
            round_number=round_number,
            agenda=agenda,
            questions=questions,
            previous_summary=previous_summary,
            memory_context=memory_context
        )

        plans[title] = plan

    total_cost = sum(p.get_total_planning_cost() for p in planners.values())
    print(f"  ✓ All plans created (est. cost: ${total_cost:.3f})")

    return plans
