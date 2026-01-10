"""
Memory System Configuration

Configuration settings for the agent memory system including
memory types, storage parameters, and retrieval settings.

Author: Ion Transport Virtual Lab
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class MemoryConfig:
    """Configuration for agent memory system."""

    # Memory storage settings
    memory_db_path: Optional[Path] = None  # If None, uses default location
    embedding_model: str = "text-embedding-3-small"  # Same as RAG for consistency

    # Memory types and retention
    enable_short_term: bool = True   # Current round conversation buffer
    enable_working: bool = True      # Key insights from current symposium
    enable_long_term: bool = True    # Persistent across all symposia

    # Retrieval settings
    max_memories_per_recall: int = 3  # Top-K memories to retrieve
    relevance_threshold: float = 0.6  # Minimum similarity score (0-1)

    # Consolidation settings
    consolidate_after_round: bool = True  # Extract insights after each round
    min_insight_length: int = 50  # Minimum chars for insight to be stored

    # Memory importance scoring
    use_importance_scoring: bool = True
    importance_decay_rate: float = 0.95  # Decay per symposium (0-1)

    # Performance settings
    batch_size: int = 10  # Batch embeddings for efficiency
    cache_embeddings: bool = True  # Cache to avoid recomputation

    def __post_init__(self):
        """Set default memory DB path if not provided."""
        if self.memory_db_path is None:
            # Use same location as RAG database
            from pathlib import Path
            self.memory_db_path = Path(__file__).parent.parent / "data" / "memory_db"


# Default configuration
DEFAULT_MEMORY_CONFIG = MemoryConfig()


# Cost-optimized configuration (minimal memory usage)
COST_OPTIMIZED_CONFIG = MemoryConfig(
    enable_long_term=False,  # Skip persistent storage
    max_memories_per_recall=2,  # Fewer retrievals
    consolidate_after_round=False,  # Manual consolidation only
    use_importance_scoring=False,  # Skip importance calculation
)


# Quality-optimized configuration (maximum memory capabilities)
QUALITY_OPTIMIZED_CONFIG = MemoryConfig(
    enable_short_term=True,
    enable_working=True,
    enable_long_term=True,
    max_memories_per_recall=5,  # More context
    relevance_threshold=0.5,  # Lower threshold = more memories
    consolidate_after_round=True,
    use_importance_scoring=True,
)


# Domain-specific collection names
MEMORY_COLLECTION_NAMES = {
    "electrochemistry": "electrochemistry_agent_memory",
    "membrane_science": "membrane_science_agent_memory",
    "biology": "biology_agent_memory",
    "nanofluidics": "nanofluidics_agent_memory",
}


def get_memory_collection_name(domain: str) -> str:
    """
    Get the memory collection name for a domain.

    Args:
        domain: Domain name (electrochemistry, membrane_science, biology, nanofluidics)

    Returns:
        Collection name string

    Raises:
        ValueError: If domain is invalid
    """
    if domain not in MEMORY_COLLECTION_NAMES:
        raise ValueError(
            f"Invalid domain '{domain}'. "
            f"Choose from: {list(MEMORY_COLLECTION_NAMES.keys())}"
        )
    return MEMORY_COLLECTION_NAMES[domain]


# Memory importance categories
class MemoryImportance:
    """Constants for memory importance levels."""
    CRITICAL = 1.0      # Must remember (key insights, breakthroughs)
    HIGH = 0.8          # Very important (major findings)
    MEDIUM = 0.6        # Important (supporting evidence)
    LOW = 0.4           # Nice to have (minor details)
    MINIMAL = 0.2       # Barely relevant (background info)


# Memory type definitions
class MemoryType:
    """Constants for different memory types."""
    SHORT_TERM = "short_term"      # Current round only
    WORKING = "working"            # Current symposium (4 rounds)
    LONG_TERM = "long_term"        # Persistent across symposia

    @staticmethod
    def all_types():
        """Get all memory type values."""
        return [MemoryType.SHORT_TERM, MemoryType.WORKING, MemoryType.LONG_TERM]


# Insight extraction prompts
INSIGHT_EXTRACTION_PROMPT = """You are analyzing a scientific discussion round to extract key insights.

From the following discussion, identify 3-5 key insights that should be remembered for future rounds:

{discussion_text}

For each insight, provide:
1. The insight itself (1-2 sentences)
2. Why it's important (1 sentence)
3. Which expert(s) contributed to it

Format as:
**Insight 1**: [Brief insight]
**Importance**: [Why it matters]
**Contributors**: [Agent names]

Focus on:
- Novel findings or arguments
- Key analogies or connections between fields
- Quantitative results or specific examples
- Consensus points or disagreements
- Open questions identified
"""


# Memory consolidation settings
CONSOLIDATION_CONFIG = {
    "min_insights": 2,  # Minimum insights to extract per round
    "max_insights": 5,  # Maximum insights to extract per round
    "use_llm_extraction": True,  # Use LLM to extract insights (vs simple parsing)
    "extraction_model": "gpt-4o-mini",  # Cheaper model for extraction
}
