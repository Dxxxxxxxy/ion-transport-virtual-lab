"""
Meeting Orchestrator for Multi-Agent Symposiums

This module provides the run_meeting() function that orchestrates multi-agent
discussions for the Ion Transport Virtual Lab. It manages agent turns, tool
execution, conversation flow, and result saving.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import openai

from agents.base_agent import Agent


def run_meeting(
    team_lead: Agent,
    team_members: Tuple[Agent, ...],
    agenda: str,
    meeting_type: str = "team",
    agenda_questions: Optional[List[str]] = None,
    agenda_rules: Optional[str] = None,
    summaries: Optional[Tuple[str, ...]] = None,
    num_rounds: int = 2,
    use_rag: bool = False,
    agent_to_domain: Optional[Dict[Agent, str]] = None,
    save_dir: Optional[Path] = None,
    save_name: str = "discussion",
    return_summary: bool = False,
    **kwargs
) -> Optional[str]:
    """
    Orchestrate a multi-agent scientific discussion.

    This function manages a structured discussion between multiple AI agents,
    where agents take turns contributing to the conversation based on the
    agenda. It handles tool calls (especially RAG queries), saves transcripts,
    and generates summaries.

    Args:
        team_lead: The facilitator agent (usually the PI/Chair)
        team_members: Tuple of participating expert agents
        agenda: Main discussion agenda/topic
        meeting_type: Type of meeting ("team" for symposiums)
        agenda_questions: Specific questions to address
        agenda_rules: Discussion rules and guidelines
        summaries: Previous round summaries for context
        num_rounds: Number of discussion rounds (each agent speaks once per round)
        use_rag: Whether to enable RAG tool calls
        agent_to_domain: Mapping of agents to their domains (for RAG queries)
        save_dir: Directory to save discussion transcript
        save_name: Filename for saved transcript
        return_summary: Whether to return a summary of the discussion
        **kwargs: Additional parameters (for compatibility)

    Returns:
        If return_summary=True: Summary string of the discussion
        Otherwise: None

    Example:
        >>> summary = run_meeting(
        ...     team_lead=symposium_pi,
        ...     team_members=(electrochem_expert, membrane_expert),
        ...     agenda="Discuss ion transport mechanisms",
        ...     num_rounds=2,
        ...     use_rag=True,
        ...     return_summary=True
        ... )
    """
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build initial context
    context_parts = [f"# Discussion Agenda\n\n{agenda}"]

    if agenda_questions:
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(agenda_questions)])
        context_parts.append(f"\n# Key Questions to Address\n\n{questions_text}")

    if agenda_rules:
        context_parts.append(f"\n# Discussion Rules\n\n{agenda_rules}")

    if summaries:
        for i, summary in enumerate(summaries, 1):
            context_parts.append(f"\n# Summary from Previous Round {i}\n\n{summary}")

    full_context = "\n".join(context_parts)

    # Initialize conversation
    all_agents = [team_lead] + list(team_members)
    conversation_transcript = []
    conversation_history = [
        {"role": "system", "content": full_context}
    ]

    # Add opening from team lead
    conversation_transcript.append(f"[{team_lead.title}] Opening the discussion\n")
    print(f"\n{'='*80}")
    print(f"[{team_lead.title}] Opening discussion...")
    print(f"{'='*80}\n")

    # Run discussion rounds
    for round_num in range(num_rounds):
        print(f"\n--- Round {round_num + 1}/{num_rounds} ---\n")

        for agent in team_members:
            # Get agent's tools if available (for UnifiedAgent)
            tools = None
            if hasattr(agent, 'openai_tools'):
                tools = agent.openai_tools

            # Build messages for this agent
            agent_messages = [agent.message] + conversation_history

            # Call OpenAI API
            try:
                if tools:
                    # Agent has tools available (UnifiedAgent)
                    response = client.chat.completions.create(
                        model=agent.model,
                        messages=agent_messages,
                        tools=tools,
                        temperature=0.7,
                        max_tokens=2000
                    )
                else:
                    # Standard agent without tools
                    response = client.chat.completions.create(
                        model=agent.model,
                        messages=agent_messages,
                        temperature=0.7,
                        max_tokens=2000
                    )

                message = response.choices[0].message
                content = message.content or ""

                # Handle tool calls if present
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Execute tools and get results
                    tool_outputs, tool_messages = agent.tool_manager.execute_tool_calls(
                        message.tool_calls,
                        conversation_context=full_context
                    )

                    # Add tool messages to conversation
                    conversation_history.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    conversation_history.extend(tool_messages)

                    # Get final response after tool execution
                    follow_up = client.chat.completions.create(
                        model=agent.model,
                        messages=[agent.message] + conversation_history,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    content = follow_up.choices[0].message.content or content

                # Add to conversation
                conversation_history.append({
                    "role": "assistant",
                    "content": content,
                    "name": agent.title.replace(" ", "_")
                })

                # Record in transcript
                transcript_entry = f"[{agent.title}]\n{content}\n"
                conversation_transcript.append(transcript_entry)

                # Print to console
                print(f"[{agent.title}]")
                print(f"{content[:500]}..." if len(content) > 500 else content)
                print()

            except Exception as e:
                error_msg = f"Error getting response from {agent.title}: {e}"
                print(f"⚠️  {error_msg}")
                conversation_transcript.append(f"[ERROR: {agent.title}] {error_msg}\n")

    # Save transcript if requested
    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save as markdown
        transcript_path = save_dir / f"{save_name}.md"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(f"# {agenda}\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Participants**: {', '.join([a.title for a in all_agents])}\n\n")
            f.write(f"**Rounds**: {num_rounds}\n\n")
            f.write("---\n\n")
            f.write("\n\n".join(conversation_transcript))

        print(f"\n✅ Transcript saved to: {transcript_path}")

        # Save as JSON for programmatic access
        json_path = save_dir / f"{save_name}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "agenda": agenda,
                "timestamp": datetime.now().isoformat(),
                "participants": [a.title for a in all_agents],
                "num_rounds": num_rounds,
                "conversation": conversation_history[1:]  # Exclude system message
            }, f, indent=2)

    # Generate summary if requested
    if return_summary:
        print("\n📝 Generating summary...")
        try:
            summary_prompt = f"""Based on the following discussion, provide a concise summary (200-300 words) of:
1. Main points and insights discussed
2. Areas of agreement
3. Key questions or challenges identified
4. Potential directions for further exploration

Discussion:
{' '.join([t for t in conversation_transcript])}
"""
            summary_response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheaper model for summarization
                messages=[
                    {"role": "system", "content": "You are a scientific summarizer. Create concise, accurate summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            summary = summary_response.choices[0].message.content

            # Save summary if save_dir provided
            if save_dir:
                summary_path = save_dir / f"{save_name}_summary.txt"
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"✅ Summary saved to: {summary_path}")

            return summary

        except Exception as e:
            print(f"⚠️  Error generating summary: {e}")
            return "Summary generation failed."

    return None
