"""
RAG Validator - Ensures evidence-based responses for substantive claims

Validates that substantive scientific responses use RAG evidence.
Implements hybrid strategy: strong prompts + post-response validation.
"""

import re
from typing import Tuple, Optional, List, Dict, Any
from tools.rag_tool import run_rag_query


class ResponseClassifier:
    """
    Classifies agent responses as simple or substantive.

    Simple responses (skip validation):
    - Acknowledgments, greetings, brief clarifications
    - < 50 words
    - No numerical claims or mechanisms

    Substantive responses (require RAG):
    - Scientific claims with numerical values
    - Mechanistic explanations
    - References to literature or studies
    - > 100 words with technical content
    """

    # Patterns indicating simple responses
    SIMPLE_PATTERNS = [
        r"^I agree",
        r"^Thank you",
        r"^Yes,? that",
        r"^Good point",
        r"^Interesting",
        r"^Let me clarify",
        r"^To answer briefly",
        r"^Could you",
        r"^What do you mean",
        r"^I see",
    ]

    # Indicators of substantive claims
    NUMERICAL_PATTERN = r'\d+\.?\d*\s*[a-zA-Z/°µ]+'  # Numbers with units: "280 F/g", "1.5 nm"
    CITATION_PATTERNS = [r'et al\.?', r'\(\d{4}\)', r'according to']
    MECHANISM_KEYWORDS = [
        'mechanism', 'because', 'due to', 'caused by',
        'resulting from', 'leads to', 'controls', 'influences'
    ]

    def is_simple(self, response: str) -> bool:
        """
        Determine if response is simple (doesn't need RAG validation).

        Args:
            response: Agent response text

        Returns:
            True if simple response, False if substantive
        """
        # Strip whitespace
        response = response.strip()

        # Very short responses are likely simple
        if len(response) < 50:
            return True

        # Check for simple response patterns
        response_lower = response.lower()
        for pattern in self.SIMPLE_PATTERNS:
            if re.match(pattern, response, re.IGNORECASE):
                return True

        # If contains substantive indicators, not simple
        if self.is_substantive(response):
            return False

        # Default: if under 100 words and no substantive indicators, consider simple
        word_count = len(response.split())
        return word_count < 100

    def is_substantive(self, response: str) -> bool:
        """
        Determine if response contains substantive scientific claims.

        Args:
            response: Agent response text

        Returns:
            True if substantive, False otherwise
        """
        # Check for numbers with units
        if re.search(self.NUMERICAL_PATTERN, response):
            return True

        # Check for citation attempts
        for pattern in self.CITATION_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                return True

        # Check for mechanism keywords
        response_lower = response.lower()
        if any(keyword in response_lower for keyword in self.MECHANISM_KEYWORDS):
            # Only substantive if also reasonably long (avoids false positives)
            if len(response.split()) > 50:
                return True

        # Long technical responses are likely substantive
        if len(response.split()) > 150:
            return True

        return False


class RAGValidator:
    """
    Validates that substantive claims are backed by RAG evidence.

    Strategy:
    1. Classify response (simple vs substantive)
    2. If substantive: check if RAG was used
    3. If not: force retrieval and suggest retry
    4. Cost optimization: skip validation for simple responses
    """

    def __init__(self, domain: str):
        """
        Initialize RAG validator for a domain.

        Args:
            domain: Agent's domain for RAG queries
        """
        self.domain = domain
        self.classifier = ResponseClassifier()
        self.validation_count = 0
        self.forced_retrievals = 0

    def validate_response(
        self,
        response: str,
        tool_calls_made: List[str],
        conversation_context: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate response against RAG-first policy.

        Args:
            response: Agent's response text
            tool_calls_made: List of tool names called in this response
            conversation_context: Current conversation (optional, for context)

        Returns:
            Tuple of (is_valid, retry_guidance)
            - is_valid: True if response is valid, False if needs retry
            - retry_guidance: None if valid, else guidance for retry
        """
        self.validation_count += 1

        # Step 1: Classify response
        if self.classifier.is_simple(response):
            # Simple response - no validation needed
            return (True, None)

        # Step 2: Check if substantive response used RAG
        used_rag = self._check_rag_usage(tool_calls_made)

        if used_rag:
            # Substantive response with RAG evidence - valid
            return (True, None)

        # Step 3: Substantive response without RAG - invalid
        self.forced_retrievals += 1

        # Generate retry guidance
        retry_guidance = self._generate_retry_guidance(response)

        return (False, retry_guidance)

    def _check_rag_usage(self, tool_calls_made: List[str]) -> bool:
        """Check if RAG tool was called."""
        return "query_knowledge_base" in tool_calls_made

    def _generate_retry_guidance(self, response: str) -> str:
        """
        Generate guidance for retrying with RAG evidence.

        Extracts key claims from response that need supporting evidence.

        Args:
            response: Agent's response text

        Returns:
            Retry guidance string
        """
        # Extract potential claims needing evidence
        claims = self._extract_claims(response)

        guidance = """Your response contains substantive scientific claims but lacks supporting evidence from your knowledge base.

REQUIRED ACTION:
Please query your knowledge base to support your claims. Use the query_knowledge_base tool before making substantive scientific statements.

"""

        if claims:
            guidance += "Suggested queries to support your response:\n"
            for i, claim in enumerate(claims[:3], 1):  # Limit to top 3
                guidance += f"{i}. query_knowledge_base(\"{claim}\")\n"
            guidance += "\n"

        guidance += "After retrieving evidence, reformulate your response with proper citations."

        return guidance

    def _extract_claims(self, response: str) -> List[str]:
        """
        Extract key claims from response that need evidence.

        Uses heuristics to identify scientific claims:
        - Sentences with numbers
        - Sentences with mechanism keywords
        - Long technical sentences

        Args:
            response: Agent's response text

        Returns:
            List of claim strings suitable for RAG queries
        """
        claims = []

        # Split into sentences
        sentences = re.split(r'[.!?]+', response)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Skip very short sentences
            if len(sentence.split()) < 5:
                continue

            # Check if sentence contains substantive content
            has_numbers = bool(re.search(self.classifier.NUMERICAL_PATTERN, sentence))
            has_mechanism = any(
                keyword in sentence.lower()
                for keyword in self.classifier.MECHANISM_KEYWORDS
            )

            if has_numbers or has_mechanism:
                # Convert sentence to a query
                query = self._sentence_to_query(sentence)
                claims.append(query)

        return claims[:5]  # Limit to 5 claims

    def _sentence_to_query(self, sentence: str) -> str:
        """
        Convert a claim sentence to a knowledge base query.

        Extracts key technical terms and concepts.

        Args:
            sentence: Sentence containing a claim

        Returns:
            Query string for knowledge base
        """
        # Remove common articles and conjunctions
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}

        # Tokenize and filter
        words = sentence.split()
        keywords = [
            word for word in words
            if len(word) > 3 and word.lower() not in stop_words
        ]

        # Limit query length
        query = ' '.join(keywords[:10])

        # Clean up
        query = re.sub(r'[^\w\s-]', '', query)  # Remove punctuation except hyphens
        query = query.strip()

        return query if query else sentence[:100]

    def force_rag_retrieval(
        self,
        response: str,
        agenda: Optional[str] = None
    ) -> str:
        """
        Force RAG retrieval for claims in response.

        Executes RAG queries for identified claims and returns context.

        Args:
            response: Agent's response needing evidence
            agenda: Current discussion agenda (optional)

        Returns:
            Retrieved context from knowledge base
        """
        # Extract claims
        claims = self._extract_claims(response)

        if not claims:
            # Fall back to agenda or generic query
            query = agenda if agenda else "ion transport selectivity mechanisms"
            return run_rag_query(query, self.domain, top_k=3)

        # Query for first claim (most relevant)
        primary_query = claims[0]
        context = run_rag_query(primary_query, self.domain, top_k=5)

        return context

    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Dictionary with validation metrics
        """
        return {
            "total_validations": self.validation_count,
            "forced_retrievals": self.forced_retrievals,
            "forced_retrieval_rate": (
                self.forced_retrievals / self.validation_count
                if self.validation_count > 0 else 0.0
            )
        }

    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_count = 0
        self.forced_retrievals = 0
