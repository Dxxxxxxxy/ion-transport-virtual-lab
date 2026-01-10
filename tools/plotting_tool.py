"""
Plotting Tool

Data visualization using Matplotlib for creating comparative plots,
trends, and relationships discussed in symposiums.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from tools.tool_registry import Tool

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PlottingTool(Tool):
    """
    Tool for creating data visualizations.

    Supports:
    - Line plots (trends)
    - Bar plots (comparisons)
    - Scatter plots (correlations)
    - Multiple datasets on same axes
    """

    def __init__(self):
        super().__init__(
            name="create_plot",
            description="Create data visualizations (line, bar, scatter plots) to compare values or show trends",
            category="visualization",
            cost_estimate=0.0,  # Free, local computation
            requires_api=False
        )

        if not MATPLOTLIB_AVAILABLE:
            print("Warning: Matplotlib not installed. Plotting will not work.")
            print("Install with: pip install matplotlib")

    def execute(self, plot_type: str, data: Dict[str, List[float]],
                title: str = "Comparison Plot",
                xlabel: str = "X", ylabel: str = "Y",
                save_path: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
        """
        Create a plot.

        Args:
            plot_type: One of "line", "bar", "scatter"
            data: Dictionary mapping series names to data lists
                  For line/scatter: {"x": [1,2,3], "y": [4,5,6], "label": "Series 1"}
                  For bar: {"labels": ["A", "B"], "values": [10, 20]}
                  For multiple series: {"Series 1": [1,2,3], "Series 2": [4,5,6]}
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            save_path: Path to save figure (optional, auto-generated if None)
            **kwargs: Additional matplotlib parameters

        Returns:
            Dictionary with result:
            {
                "plot_type": str,
                "title": str,
                "save_path": str,
                "success": bool,
                "error": str (if failed)
            }
        """
        if not MATPLOTLIB_AVAILABLE:
            return {
                "plot_type": plot_type,
                "title": title,
                "save_path": None,
                "success": False,
                "error": "Matplotlib not installed. Run: pip install matplotlib"
            }

        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))

            if plot_type == "line":
                # Line plot - handle multiple series
                if "x" in data and "y" in data:
                    # Single series with explicit x, y
                    ax.plot(data["x"], data["y"], marker='o',
                           label=data.get("label", "Data"), linewidth=2)
                else:
                    # Multiple series (assume x is index)
                    for series_name, values in data.items():
                        ax.plot(values, marker='o', label=series_name, linewidth=2)

                ax.legend()
                ax.grid(True, alpha=0.3)

            elif plot_type == "bar":
                # Bar plot - compare categories
                if "labels" in data and "values" in data:
                    # Single series
                    ax.bar(data["labels"], data["values"], alpha=0.8)
                else:
                    # Multiple series - grouped bars
                    import numpy as np
                    labels = list(data.keys())
                    values = list(data.values())
                    x = np.arange(len(labels))
                    width = 0.35

                    if isinstance(values[0], list):
                        # Multiple bars per category
                        for i, (label, vals) in enumerate(zip(labels, values)):
                            ax.bar(x + i*width, vals, width, label=label, alpha=0.8)
                    else:
                        # Single value per category
                        ax.bar(x, values, alpha=0.8)
                        ax.set_xticks(x)
                        ax.set_xticklabels(labels)

                ax.legend()

            elif plot_type == "scatter":
                # Scatter plot - correlations
                if "x" in data and "y" in data:
                    # Single series
                    ax.scatter(data["x"], data["y"], s=100, alpha=0.6,
                              label=data.get("label", "Data"))
                else:
                    # Multiple series
                    for series_name, values in data.items():
                        if len(values) >= 2:
                            x = list(range(len(values)))
                            ax.scatter(x, values, s=100, alpha=0.6, label=series_name)

                ax.legend()
                ax.grid(True, alpha=0.3)

            else:
                return {
                    "plot_type": plot_type,
                    "title": title,
                    "save_path": None,
                    "success": False,
                    "error": f"Unknown plot type: {plot_type}. Use: line, bar, scatter"
                }

            # Set labels and title
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')

            # Generate save path if not provided
            if save_path is None:
                save_dir = Path("ion_transport/results/plots")
                save_dir.mkdir(parents=True, exist_ok=True)
                # Create filename from title
                filename = title.lower().replace(" ", "_").replace("/", "_") + ".png"
                save_path = str(save_dir / filename)

            # Save figure
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close(fig)

            return {
                "plot_type": plot_type,
                "title": title,
                "save_path": save_path,
                "success": True
            }

        except Exception as e:
            return {
                "plot_type": plot_type,
                "title": title,
                "save_path": None,
                "success": False,
                "error": f"Plotting error: {str(e)}"
            }

    def get_description_for_prompt(self) -> str:
        """Get tool description formatted for agent prompts."""
        return """
create_plot(plot_type, data, title="", xlabel="", ylabel="", save_path=None)
    Create data visualizations using Matplotlib.

    Parameters:
        - plot_type (str): "line", "bar", or "scatter"
        - data (dict): Data to plot
            - For line/scatter: {"x": [1,2,3], "y": [4,5,6], "label": "Series"}
            - For bar: {"labels": ["A","B","C"], "values": [10,20,30]}
            - For multiple series: {"Series1": [1,2,3], "Series2": [4,5,6]}
        - title (str): Plot title
        - xlabel (str): X-axis label
        - ylabel (str): Y-axis label
        - save_path (str): Where to save (auto-generated if omitted)

    Returns: Dictionary with save path and success status

    Use this when:
        - Comparing values across fields (e.g., selectivity ratios)
        - Showing trends (e.g., capacitance vs pore size)
        - Visualizing correlations discussed in symposium
        - Creating figures for synthesis

    Examples:
        - create_plot("bar", {"Electrochemistry": [280], "Biology": [100]},
                     title="Capacitance Comparison", ylabel="F/g")
        - create_plot("line", {"x": [0.5,1.0,1.5], "y": [100,150,280]},
                     title="Capacitance vs Pore Size", xlabel="Pore Size (nm)",
                     ylabel="Capacitance (F/g)")
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
                        "plot_type": {
                            "type": "string",
                            "enum": ["line", "bar", "scatter"],
                            "description": "Type of plot to create"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data to plot. Format depends on plot_type: For line/scatter plots use {\"x\": [1,2,3], \"y\": [4,5,6], \"label\": \"Series Name\"}. For bar plots use {\"labels\": [\"A\",\"B\",\"C\"], \"values\": [10,20,30]}. For multiple series use {\"Series1\": [1,2,3], \"Series2\": [4,5,6]}"
                        },
                        "title": {
                            "type": "string",
                            "description": "Plot title",
                            "default": "Comparison Plot"
                        },
                        "xlabel": {
                            "type": "string",
                            "description": "X-axis label",
                            "default": "X"
                        },
                        "ylabel": {
                            "type": "string",
                            "description": "Y-axis label",
                            "default": "Y"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Optional path to save the figure (auto-generated if not provided)"
                        }
                    },
                    "required": ["plot_type", "data"]
                }
            }
        }

    def format_results_for_agent(self, results: Dict[str, Any]) -> str:
        """
        Format plotting results for agent consumption.

        Args:
            results: Output from execute()

        Returns:
            Formatted string with results
        """
        if not results["success"]:
            return f"Plotting error: {results['error']}"

        return f"""Plot created successfully!
Type: {results['plot_type']}
Title: {results['title']}
Saved to: {results['save_path']}
"""
