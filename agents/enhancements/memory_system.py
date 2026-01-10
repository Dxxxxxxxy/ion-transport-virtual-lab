"""
Agent Memory System

Implements persistent memory for AI agents across symposium rounds.

Memory Architecture:
- Short-term: Current round conversation buffer
- Working: Key insights from current symposium (4 rounds)
- Long-term: Persistent knowledge from all symposia

Storage: ChromaDB (same infrastructure as RAG)
Retrieval: Semantic search using embeddings

Author: Ion Transport Virtual Lab
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from agents.enhancements.memory_config import (
    MemoryConfig,
    DEFAULT_MEMORY_CONFIG,
    MemoryType,
    MemoryImportance,
    INSIGHT_EXTRACTION_PROMPT,
    CONSOLIDATION_CONFIG,
    get_memory_collection_name,
)


class AgentMemory:
    """
    Persistent memory system for AI agents.

    Stores and retrieves insights across symposium rounds using
    semantic search over ChromaDB collections.
    """

    def __init__(
        self,
        agent_domain: str,
        config: Optional[MemoryConfig] = None,
        symposium_id: Optional[str] = None
    ):
        """
        Initialize agent memory.

        Args:
            agent_domain: Domain name (electrochemistry, membrane_science, etc.)
            config: Memory configuration (defaults to DEFAULT_MEMORY_CONFIG)
            symposium_id: Unique ID for current symposium (generated if None)
        """
        self.domain = agent_domain
        self.config = config or DEFAULT_MEMORY_CONFIG
        self.symposium_id = symposium_id or self._generate_symposium_id()

        # Initialize ChromaDB client
        self.config.memory_db_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.config.memory_db_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embeddings (same model as RAG)
        self.embeddings = OpenAIEmbeddings(model=self.config.embedding_model)

        # Get or create memory collection
        self.collection_name = get_memory_collection_name(agent_domain)
        self.collection = self._get_or_create_collection()

        # OpenAI client for insight extraction
        self.openai_client = OpenAI()

        # In-memory buffers
        self.short_term_buffer: List[Dict[str, Any]] = []
        self.working_memory_ids: List[str] = []  # IDs of memories from this symposium

        print(f"    ✓ Memory initialized for {agent_domain} (symposium: {self.symposium_id})")

    def _generate_symposium_id(self) -> str:
        """Generate unique symposium ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"symposium_{timestamp}"

    def _get_or_create_collection(self):
        """Get or create ChromaDB collection for agent memory."""
        try:
            collection = self.client.get_collection(name=self.collection_name)
            print(f"    ✓ Using existing memory collection: {self.collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"domain": self.domain, "type": "agent_memory"}
            )
            print(f"    ✓ Created new memory collection: {self.collection_name}")

        return collection

    def remember(
        self,
        insight: str,
        context: Optional[Dict[str, Any]] = None,
        importance: float = MemoryImportance.MEDIUM,
        memory_type: str = MemoryType.WORKING,
        round_number: Optional[int] = None
    ) -> str:
        """
        Store an insight in memory.

        Args:
            insight: The insight text to remember
            context: Additional context metadata
            importance: Importance score (0-1)
            memory_type: Type of memory (short_term, working, long_term)
            round_number: Which round this is from

        Returns:
            Memory ID (UUID)
        """
        if len(insight) < self.config.min_insight_length:
            return None  # Skip very short insights

        # Generate unique ID
        memory_id = str(uuid.uuid4())

        # Generate embedding
        embedding = self.embeddings.embed_query(insight)

        # Prepare metadata
        metadata = {
            "symposium_id": self.symposium_id,
            "domain": self.domain,
            "memory_type": memory_type,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "round_number": round_number if round_number is not None else -1,
        }

        # Add custom context
        if context:
            for key, value in context.items():
                # ChromaDB only supports str, int, float, bool
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value

        # Store in ChromaDB
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[insight],
            metadatas=[metadata]
        )

        # Track working memory IDs
        if memory_type == MemoryType.WORKING:
            self.working_memory_ids.append(memory_id)

        # Add to short-term buffer
        if memory_type == MemoryType.SHORT_TERM and self.config.enable_short_term:
            self.short_term_buffer.append({
                "id": memory_id,
                "insight": insight,
                "metadata": metadata
            })

        return memory_id

    def recall(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        min_importance: Optional[float] = None,
        round_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories.

        Args:
            query: Query string for semantic search
            memory_types: Filter by memory types (None = all types)
            top_k: Number of memories to return (None = use config default)
            min_importance: Minimum importance threshold
            round_number: Filter by specific round

        Returns:
            List of memory dictionaries with content and metadata
        """
        if top_k is None:
            top_k = self.config.max_memories_per_recall

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Build metadata filter
        where_filter = {"domain": self.domain}

        if memory_types:
            # ChromaDB doesn't support IN operator, so we need to query each type
            # For simplicity, we'll filter in post-processing
            pass

        if round_number is not None:
            where_filter["round_number"] = round_number

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # Get extra, filter later
            where=where_filter
        )

        # Format and filter results
        memories = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i]

                # Apply filters
                if memory_types and metadata.get('memory_type') not in memory_types:
                    continue

                if min_importance and metadata.get('importance', 0) < min_importance:
                    continue

                # Calculate similarity (ChromaDB returns distances, we want similarity)
                distance = results['distances'][0][i]
                similarity = 1 / (1 + distance)  # Convert distance to similarity

                if similarity < self.config.relevance_threshold:
                    continue

                memory = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'similarity': similarity,
                    'distance': distance,
                }
                memories.append(memory)

        # Sort by importance * similarity
        if self.config.use_importance_scoring:
            memories.sort(
                key=lambda m: m['metadata'].get('importance', 0.5) * m['similarity'],
                reverse=True
            )
        else:
            memories.sort(key=lambda m: m['similarity'], reverse=True)

        # Return top-k
        return memories[:top_k]

    def consolidate_round(
        self,
        round_summary: str,
        round_number: int,
        discussion_messages: Optional[List[Dict[str, str]]] = None,
        use_llm: bool = True
    ) -> List[str]:
        """
        Extract and store key insights from a discussion round.

        Args:
            round_summary: Summary text of the round
            round_number: Which round (1-4)
            discussion_messages: Optional full discussion for detailed extraction
            use_llm: Whether to use LLM for insight extraction (vs simple parsing)

        Returns:
            List of memory IDs created
        """
        if not self.config.consolidate_after_round:
            return []

        print(f"\n🧠 Consolidating Round {round_number} memories for {self.domain}...")

        insights = []

        if use_llm and CONSOLIDATION_CONFIG["use_llm_extraction"]:
            # Use LLM to extract structured insights
            insights = self._extract_insights_with_llm(round_summary, round_number)
        else:
            # Simple extraction: treat summary as single insight
            insights = [{
                "content": round_summary,
                "importance": MemoryImportance.MEDIUM,
                "context": {"source": "round_summary"}
            }]

        # Store insights
        memory_ids = []
        for insight_data in insights:
            memory_id = self.remember(
                insight=insight_data["content"],
                context=insight_data.get("context", {}),
                importance=insight_data.get("importance", MemoryImportance.MEDIUM),
                memory_type=MemoryType.WORKING,
                round_number=round_number
            )
            if memory_id:
                memory_ids.append(memory_id)

        print(f"    ✓ Stored {len(memory_ids)} insights from Round {round_number}")
        return memory_ids

    def _extract_insights_with_llm(
        self,
        discussion_text: str,
        round_number: int
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to extract structured insights from discussion.

        Args:
            discussion_text: Full discussion or summary text
            round_number: Round number

        Returns:
            List of insight dictionaries
        """
        # Prepare prompt
        prompt = INSIGHT_EXTRACTION_PROMPT.format(discussion_text=discussion_text)

        try:
            # Call LLM (use cheaper model)
            response = self.openai_client.chat.completions.create(
                model=CONSOLIDATION_CONFIG["extraction_model"],
                messages=[
                    {"role": "system", "content": "You are a scientific insight extractor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content

            # Parse insights (simple parsing - look for **Insight N**)
            insights = []
            import re
            insight_blocks = re.split(r'\*\*Insight \d+\*\*:', response_text)

            for block in insight_blocks[1:]:  # Skip first empty split
                # Extract content (text before **Importance**)
                content_match = re.search(r'^(.+?)\*\*Importance\*\*:', block, re.DOTALL)
                if content_match:
                    content = content_match.group(1).strip()

                    # Determine importance based on keywords
                    importance = MemoryImportance.MEDIUM
                    if "critical" in block.lower() or "breakthrough" in block.lower():
                        importance = MemoryImportance.CRITICAL
                    elif "major" in block.lower() or "significant" in block.lower():
                        importance = MemoryImportance.HIGH

                    insights.append({
                        "content": content,
                        "importance": importance,
                        "context": {"round": round_number, "extracted_by": "llm"}
                    })

            # Limit to max insights
            max_insights = CONSOLIDATION_CONFIG["max_insights"]
            return insights[:max_insights]

        except Exception as e:
            print(f"    ⚠ LLM extraction failed: {e}")
            # Fallback: simple extraction
            return [{
                "content": discussion_text[:500],  # First 500 chars
                "importance": MemoryImportance.MEDIUM,
                "context": {"round": round_number, "extracted_by": "fallback"}
            }]

    def get_context_for_round(
        self,
        agenda: str,
        questions: List[str],
        round_number: int
    ) -> str:
        """
        Generate memory context for an upcoming round.

        Args:
            agenda: Round agenda text
            questions: List of questions for the round
            round_number: Which round

        Returns:
            Formatted context string with relevant memories
        """
        # Combine agenda and questions for query
        query_parts = [agenda] + questions
        query = " ".join(query_parts)

        # Retrieve relevant memories
        memories = self.recall(
            query=query,
            memory_types=[MemoryType.WORKING, MemoryType.LONG_TERM],
            top_k=self.config.max_memories_per_recall
        )

        if not memories:
            return ""

        # Format memories
        context_parts = [f"\n{'='*60}"]
        context_parts.append(f"RELEVANT MEMORIES FROM YOUR PREVIOUS INSIGHTS:")
        context_parts.append(f"{'='*60}\n")

        for i, mem in enumerate(memories, 1):
            metadata = mem['metadata']
            round_num = metadata.get('round_number', '?')
            importance = metadata.get('importance', 0.5)

            context_parts.append(f"[Memory {i}] (Round {round_num}, Importance: {importance:.2f})")
            context_parts.append(mem['content'])
            context_parts.append("")

        context_parts.append(f"{'='*60}\n")
        context_parts.append("Use these memories to build on your previous contributions.\n")

        return "\n".join(context_parts)

    def clear_short_term(self):
        """Clear short-term memory buffer."""
        self.short_term_buffer = []

    def promote_to_long_term(self, memory_ids: Optional[List[str]] = None):
        """
        Promote working memories to long-term storage.

        Args:
            memory_ids: Specific IDs to promote (None = promote all working memory)
        """
        if not self.config.enable_long_term:
            return

        ids_to_promote = memory_ids or self.working_memory_ids

        for memory_id in ids_to_promote:
            # Get the memory
            result = self.collection.get(ids=[memory_id])

            if result['ids']:
                # Update metadata to long-term
                metadata = result['metadatas'][0]
                metadata['memory_type'] = MemoryType.LONG_TERM
                metadata['promoted_at'] = datetime.now().isoformat()

                # Update in collection
                self.collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )

        print(f"    ✓ Promoted {len(ids_to_promote)} memories to long-term storage")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory counts and metadata
        """
        all_memories = self.collection.get()

        total_count = len(all_memories['ids'])
        by_type = {}
        by_importance = {"high": 0, "medium": 0, "low": 0}

        for metadata in all_memories['metadatas']:
            # Count by type
            mem_type = metadata.get('memory_type', 'unknown')
            by_type[mem_type] = by_type.get(mem_type, 0) + 1

            # Count by importance
            importance = metadata.get('importance', 0.5)
            if importance >= 0.8:
                by_importance["high"] += 1
            elif importance >= 0.5:
                by_importance["medium"] += 1
            else:
                by_importance["low"] += 1

        return {
            "total_memories": total_count,
            "by_type": by_type,
            "by_importance": by_importance,
            "current_symposium_count": len(self.working_memory_ids),
            "short_term_buffer_size": len(self.short_term_buffer),
        }


def create_memory_for_all_domains(
    config: Optional[MemoryConfig] = None,
    symposium_id: Optional[str] = None
) -> Dict[str, AgentMemory]:
    """
    Create memory instances for all domains.

    Args:
        config: Memory configuration
        symposium_id: Shared symposium ID

    Returns:
        Dictionary mapping domain names to AgentMemory instances
    """
    from enhanced_agents.memory_config import MEMORY_COLLECTION_NAMES

    memories = {}
    shared_symposium_id = symposium_id or AgentMemory._generate_symposium_id(None)

    for domain in MEMORY_COLLECTION_NAMES.keys():
        memories[domain] = AgentMemory(
            agent_domain=domain,
            config=config,
            symposium_id=shared_symposium_id
        )

    return memories
