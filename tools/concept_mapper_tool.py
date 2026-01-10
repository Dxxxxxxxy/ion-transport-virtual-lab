"""
Concept Mapping Tool

Visualize relationships between concepts, theories, and domains
using NetworkX and Matplotlib.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from tools.tool_registry import Tool

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class ConceptMapperTool(Tool):
    """
    Tool for creating concept maps showing relationships between ideas.

    Supports:
    - Concept relationship graphs
    - Cross-domain connection visualization
    - Theory mapping
    """

    def __init__(self):
        super().__init__(
            name="create_concept_map",
            description="Create visual concept maps showing relationships between theories, concepts, and domains",
            category="visualization",
            cost_estimate=0.0,  # Free, local computation
            requires_api=False
        )

        if not NETWORKX_AVAILABLE:
            print("Warning: NetworkX/Matplotlib not installed. Concept mapping will not work.")
            print("Install with: pip install networkx matplotlib")

    def execute(self, concepts: List[str], relationships: List[Tuple[str, str, str]],
                title: str = "Concept Map",
                save_path: Optional[str] = None,
                layout: str = "spring",
                **kwargs) -> Dict[str, Any]:
        """
        Create a concept map.

        Args:
            concepts: List of concept names
            relationships: List of (source, target, label) tuples
                          e.g., [("EDL", "Selectivity", "controls"),
                                 ("Selectivity", "Ion channels", "similar to")]
            title: Map title
            save_path: Path to save figure (optional, auto-generated if None)
            layout: Graph layout algorithm: "spring", "circular", "hierarchical"
            **kwargs: Additional networkx/matplotlib parameters

        Returns:
            Dictionary with result:
            {
                "title": str,
                "num_concepts": int,
                "num_relationships": int,
                "save_path": str,
                "success": bool,
                "error": str (if failed)
            }
        """
        if not NETWORKX_AVAILABLE:
            return {
                "title": title,
                "num_concepts": 0,
                "num_relationships": 0,
                "save_path": None,
                "success": False,
                "error": "NetworkX/Matplotlib not installed. Run: pip install networkx matplotlib"
            }

        try:
            # Create directed graph
            G = nx.DiGraph()

            # Add nodes (concepts)
            G.add_nodes_from(concepts)

            # Add edges (relationships)
            for source, target, label in relationships:
                G.add_edge(source, target, label=label)

            # Create figure
            fig, ax = plt.subplots(figsize=(14, 10))

            # Choose layout
            if layout == "spring":
                pos = nx.spring_layout(G, k=2, iterations=50)
            elif layout == "circular":
                pos = nx.circular_layout(G)
            elif layout == "hierarchical":
                # Try hierarchical layout
                try:
                    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
                except:
                    # Fall back to spring if graphviz not available
                    pos = nx.spring_layout(G, k=2, iterations=50)
            else:
                pos = nx.spring_layout(G, k=2, iterations=50)

            # Draw nodes
            nx.draw_networkx_nodes(
                G, pos,
                node_color='lightblue',
                node_size=3000,
                alpha=0.9,
                ax=ax
            )

            # Draw edges
            nx.draw_networkx_edges(
                G, pos,
                edge_color='gray',
                arrows=True,
                arrowsize=20,
                arrowstyle='->',
                width=2,
                alpha=0.6,
                ax=ax
            )

            # Draw labels
            nx.draw_networkx_labels(
                G, pos,
                font_size=10,
                font_weight='bold',
                ax=ax
            )

            # Draw edge labels (relationships)
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels=edge_labels,
                font_size=8,
                font_color='red',
                ax=ax
            )

            # Set title and remove axes
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.axis('off')

            # Generate save path if not provided
            if save_path is None:
                save_dir = Path("ion_transport/results/concept_maps")
                save_dir.mkdir(parents=True, exist_ok=True)
                # Create filename from title
                filename = title.lower().replace(" ", "_").replace("/", "_") + ".png"
                save_path = str(save_dir / filename)

            # Save figure
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig)

            return {
                "title": title,
                "num_concepts": len(concepts),
                "num_relationships": len(relationships),
                "save_path": save_path,
                "success": True
            }

        except Exception as e:
            return {
                "title": title,
                "num_concepts": 0,
                "num_relationships": 0,
                "save_path": None,
                "success": False,
                "error": f"Concept mapping error: {str(e)}"
            }

    def get_description_for_prompt(self) -> str:
        """Get tool description formatted for agent prompts."""
        return """
create_concept_map(concepts, relationships, title="", save_path=None, layout="spring")
    Create visual maps of concept relationships using NetworkX.

    Parameters:
        - concepts (list): List of concept/theory names
            e.g., ["EDL", "Selectivity", "Ion Channels", "Dehydration"]
        - relationships (list): List of (source, target, label) tuples
            e.g., [("EDL", "Selectivity", "controls"),
                   ("Selectivity", "Ion Channels", "similar to"),
                   ("Dehydration", "Selectivity", "mechanism for")]
        - title (str): Map title
        - save_path (str): Where to save (auto-generated if omitted)
        - layout (str): "spring", "circular", or "hierarchical"

    Returns: Dictionary with save path and statistics

    Use this when:
        - Mapping cross-domain connections discovered in discussion
        - Visualizing unified framework structure
        - Showing how concepts from different fields relate
        - Creating synthesis diagrams

    Example:
        create_concept_map(
            concepts=["EDL Capacitance", "Ion Selectivity", "Biological Channels", "Dehydration"],
            relationships=[
                ("EDL Capacitance", "Ion Selectivity", "influences"),
                ("Dehydration", "Ion Selectivity", "mechanism"),
                ("Ion Selectivity", "Biological Channels", "analogous to")
            ],
            title="Ion Transport Unified Framework"
        )
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
                        "concepts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of concept or theory names to include in the map (e.g., [\"EDL\", \"Ion Selectivity\", \"Biological Channels\"])"
                        },
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 3
                            },
                            "description": "List of relationships as [source, target, label] arrays (e.g., [[\"EDL\", \"Selectivity\", \"controls\"], [\"Selectivity\", \"Ion Channels\", \"similar to\"]])"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title for the concept map",
                            "default": "Concept Map"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Optional path to save the figure (auto-generated if not provided)"
                        },
                        "layout": {
                            "type": "string",
                            "enum": ["spring", "circular", "hierarchical"],
                            "description": "Graph layout algorithm to use",
                            "default": "spring"
                        }
                    },
                    "required": ["concepts", "relationships"]
                }
            }
        }

    def format_results_for_agent(self, results: Dict[str, Any]) -> str:
        """
        Format concept map results for agent consumption.

        Args:
            results: Output from execute()

        Returns:
            Formatted string with results
        """
        if not results["success"]:
            return f"Concept mapping error: {results['error']}"

        return f"""Concept map created successfully!
Title: {results['title']}
Concepts: {results['num_concepts']}
Relationships: {results['num_relationships']}
Saved to: {results['save_path']}
"""
