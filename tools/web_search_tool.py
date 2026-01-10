"""
Web Search Tool for Recent Papers

Searches academic databases for recent publications.
Uses Semantic Scholar API for paper search.
"""

import requests
from typing import List, Dict, Optional, Any
from tools.tool_registry import Tool


class WebSearchTool(Tool):
    """
    Tool for searching recent academic papers.

    Uses Semantic Scholar API to find relevant publications.
    """

    def __init__(self):
        super().__init__(
            name="search_recent_papers",
            description="Search for recent academic papers (2020-2025) on a topic. Returns titles, authors, abstracts, and DOIs.",
            category="search",
            cost_estimate=0.0,  # Free API
            requires_api=True
        )
        self.api_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def execute(self, query: str, year_range: str = "2020-", max_results: int = 5) -> Dict[str, Any]:
        """
        Search for recent papers.

        Args:
            query: Search query (e.g., "ion selectivity nanopores")
            year_range: Year range (e.g., "2020-" for 2020 onwards, "2023-2024" for specific range)
            max_results: Maximum number of results to return (default: 5)

        Returns:
            Dictionary with search results:
            {
                "query": str,
                "num_results": int,
                "papers": [
                    {
                        "title": str,
                        "authors": List[str],
                        "year": int,
                        "abstract": str,
                        "doi": str,
                        "url": str,
                        "citation_count": int
                    },
                    ...
                ]
            }
        """
        try:
            # Semantic Scholar API parameters
            params = {
                "query": query,
                "limit": min(max_results, 10),  # API limit
                "fields": "title,authors,year,abstract,externalIds,citationCount,url",
                "year": year_range,
            }

            # Make API request
            response = requests.get(
                self.api_url,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                return {
                    "query": query,
                    "num_results": 0,
                    "papers": [],
                    "error": f"API returned status {response.status_code}"
                }

            data = response.json()

            # Parse results
            papers = []
            for paper_data in data.get("data", []):
                paper = {
                    "title": paper_data.get("title", "Unknown"),
                    "authors": [
                        author.get("name", "Unknown")
                        for author in paper_data.get("authors", [])
                    ],
                    "year": paper_data.get("year"),
                    "abstract": paper_data.get("abstract", "No abstract available"),
                    "doi": paper_data.get("externalIds", {}).get("DOI"),
                    "url": paper_data.get("url", ""),
                    "citation_count": paper_data.get("citationCount", 0)
                }
                papers.append(paper)

            return {
                "query": query,
                "num_results": len(papers),
                "papers": papers
            }

        except requests.exceptions.Timeout:
            return {
                "query": query,
                "num_results": 0,
                "papers": [],
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            return {
                "query": query,
                "num_results": 0,
                "papers": [],
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "query": query,
                "num_results": 0,
                "papers": [],
                "error": f"Unexpected error: {str(e)}"
            }

    def get_description_for_prompt(self) -> str:
        """Get tool description formatted for agent prompts."""
        return """
search_recent_papers(query, year_range="2020-", max_results=5)
    Search for recent academic papers using Semantic Scholar.

    Parameters:
        - query (str): Search terms (e.g., "EDL capacitance nanopores")
        - year_range (str): Year filter (e.g., "2023-" for 2023 onwards, "2022-2024" for range)
        - max_results (int): Number of papers to return (default: 5, max: 10)

    Returns: Dictionary with paper titles, authors, abstracts, DOIs, and citation counts

    Use this when:
        - You need information beyond your knowledge base
        - Looking for very recent developments (2024-2025)
        - Checking latest research on a specific topic

    Example: search_recent_papers("ion transport 2D materials", year_range="2024-", max_results=3)
"""

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for academic papers (e.g., 'ion selectivity nanopores', 'EDL capacitance 2D materials')"
                        },
                        "year_range": {
                            "type": "string",
                            "description": "Year range filter (e.g., '2020-' for 2020 onwards, '2023-2024' for specific range). Default is '2020-'",
                            "default": "2020-"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of papers to return (1-10). Default is 5",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    def format_results_for_agent(self, results: Dict[str, Any]) -> str:
        """
        Format search results for agent consumption.

        Args:
            results: Output from execute()

        Returns:
            Formatted string with search results
        """
        if "error" in results:
            return f"Search failed: {results['error']}"

        if results["num_results"] == 0:
            return f"No papers found for query: '{results['query']}'"

        output = [f"Found {results['num_results']} recent papers:\n"]

        for i, paper in enumerate(results["papers"], 1):
            output.append(f"{i}. {paper['title']}")
            output.append(f"   Authors: {', '.join(paper['authors'][:3])}{' et al.' if len(paper['authors']) > 3 else ''}")
            output.append(f"   Year: {paper['year']}")
            if paper['doi']:
                output.append(f"   DOI: {paper['doi']}")
            output.append(f"   Citations: {paper['citation_count']}")

            # Show abstract snippet (first 200 chars)
            abstract = paper.get('abstract', 'No abstract')
            if abstract and len(abstract) > 200:
                abstract = abstract[:200] + "..."
            output.append(f"   Abstract: {abstract}")
            output.append("")

        return "\n".join(output)
