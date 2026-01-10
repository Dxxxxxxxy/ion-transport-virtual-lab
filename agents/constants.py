"""
Constants for Ion Transport Virtual Lab

This module defines global constants used throughout the virtual lab,
including default model configurations and standard prompts.
"""

# Default OpenAI model for all agents
# Using gpt-4o as the most capable general-purpose model
DEFAULT_MODEL = "gpt-4o"

# Alternative models (commented out but available)
# DEFAULT_MODEL = "gpt-4o-mini"  # Faster, cheaper variant
# DEFAULT_MODEL = "o1-preview"   # Advanced reasoning model (more expensive)
# DEFAULT_MODEL = "gpt-4-turbo"  # GPT-4 Turbo

# Scientific Critic template (for reference)
# Note: The project uses CUSTOM_SCIENTIFIC_CRITIC defined in agents/detailed_agents.py
SCIENTIFIC_CRITIC = """You are a rigorous scientific critic. Your role is to:

1. Evaluate the quality and validity of scientific arguments
2. Identify unsupported claims or logical fallacies
3. Assess whether evidence properly supports conclusions
4. Check for overgeneralizations or missing caveats
5. Ensure scientific rigor and precision in language

Provide constructive feedback that improves the quality of scientific discussion."""
