"""
Equation Solver Tool

Symbolic mathematics using SymPy for equation solving, differentiation,
integration, and algebraic manipulation.
"""

from typing import Dict, Any, List, Optional
from tools.tool_registry import Tool

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


class EquationSolverTool(Tool):
    """
    Tool for symbolic mathematics using SymPy.

    Supports:
    - Solving equations
    - Symbolic differentiation
    - Symbolic integration
    - Expression simplification
    - Equation manipulation
    """

    def __init__(self):
        super().__init__(
            name="solve_equation",
            description="Solve equations, differentiate/integrate expressions, simplify formulas using symbolic math",
            category="computation",
            cost_estimate=0.0,  # Free, local computation
            requires_api=False
        )

        if not SYMPY_AVAILABLE:
            print("Warning: SymPy not installed. Equation solver will not work.")
            print("Install with: pip install sympy")

    def execute(self, operation: str, expression: str, variable: Optional[str] = None,
                **kwargs) -> Dict[str, Any]:
        """
        Execute symbolic math operation.

        Args:
            operation: One of "solve", "differentiate", "integrate", "simplify", "expand", "factor"
            expression: Mathematical expression as string (e.g., "x**2 + 2*x + 1")
            variable: Variable to solve for / differentiate with respect to (e.g., "x")
            **kwargs: Additional operation-specific parameters

        Returns:
            Dictionary with result:
            {
                "operation": str,
                "input": str,
                "output": str,
                "latex": str (LaTeX formatted result),
                "success": bool,
                "error": str (if failed)
            }
        """
        if not SYMPY_AVAILABLE:
            return {
                "operation": operation,
                "input": expression,
                "output": None,
                "success": False,
                "error": "SymPy not installed. Run: pip install sympy"
            }

        try:
            # Parse transformations for better expression parsing
            transformations = standard_transformations + (implicit_multiplication_application,)

            # Parse the expression
            expr = parse_expr(expression, transformations=transformations)

            # Get variable symbol if provided
            var_sym = sp.Symbol(variable) if variable else None

            # Execute requested operation
            if operation == "solve":
                if not variable:
                    return {
                        "operation": operation,
                        "input": expression,
                        "output": None,
                        "success": False,
                        "error": "Variable required for solve operation"
                    }
                result = sp.solve(expr, var_sym)

            elif operation == "differentiate":
                if not variable:
                    return {
                        "operation": operation,
                        "input": expression,
                        "output": None,
                        "success": False,
                        "error": "Variable required for differentiation"
                    }
                result = sp.diff(expr, var_sym)

            elif operation == "integrate":
                if not variable:
                    return {
                        "operation": operation,
                        "input": expression,
                        "output": None,
                        "success": False,
                        "error": "Variable required for integration"
                    }
                result = sp.integrate(expr, var_sym)

            elif operation == "simplify":
                result = sp.simplify(expr)

            elif operation == "expand":
                result = sp.expand(expr)

            elif operation == "factor":
                result = sp.factor(expr)

            else:
                return {
                    "operation": operation,
                    "input": expression,
                    "output": None,
                    "success": False,
                    "error": f"Unknown operation: {operation}. Use: solve, differentiate, integrate, simplify, expand, factor"
                }

            # Format output
            output_str = str(result)
            latex_str = sp.latex(result)

            return {
                "operation": operation,
                "input": expression,
                "variable": variable,
                "output": output_str,
                "latex": latex_str,
                "success": True
            }

        except Exception as e:
            return {
                "operation": operation,
                "input": expression,
                "output": None,
                "success": False,
                "error": f"Error: {str(e)}"
            }

    def get_description_for_prompt(self) -> str:
        """Get tool description formatted for agent prompts."""
        return """
solve_equation(operation, expression, variable=None)
    Perform symbolic mathematics using SymPy.

    Parameters:
        - operation (str): Operation type
            - "solve": Solve equation for variable (e.g., "x**2 - 4 = 0" → x = ±2)
            - "differentiate": Compute derivative d/dx
            - "integrate": Compute integral ∫ dx
            - "simplify": Algebraically simplify expression
            - "expand": Expand algebraic expression
            - "factor": Factor expression
        - expression (str): Math expression (use * for multiplication, ** for power)
        - variable (str): Variable name (required for solve/differentiate/integrate)

    Returns: Dictionary with result (string and LaTeX format)

    Use this when:
        - Need to solve equations analytically
        - Derive relationships between variables
        - Simplify complex mathematical expressions
        - Compute derivatives or integrals

    Examples:
        - solve_equation("solve", "x**2 - 4", variable="x")
        - solve_equation("differentiate", "x**2 + 2*x", variable="x")
        - solve_equation("integrate", "2*x", variable="x")
        - solve_equation("simplify", "(x+1)**2 - (x-1)**2")
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
                        "operation": {
                            "type": "string",
                            "enum": ["solve", "differentiate", "integrate", "simplify", "expand", "factor"],
                            "description": "Mathematical operation to perform"
                        },
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression as string (e.g., 'x**2 + 2*x + 1', 'E*exp(-z*F*V/(R*T))'). Use * for multiplication, ** for exponentiation"
                        },
                        "variable": {
                            "type": "string",
                            "description": "Variable to solve for, differentiate, or integrate with respect to (e.g., 'x', 'V', 't'). Required for solve, differentiate, and integrate operations"
                        }
                    },
                    "required": ["operation", "expression"]
                }
            }
        }

    def format_results_for_agent(self, results: Dict[str, Any]) -> str:
        """
        Format solver results for agent consumption.

        Args:
            results: Output from execute()

        Returns:
            Formatted string with results
        """
        if not results["success"]:
            return f"Equation solver error: {results['error']}"

        output = [
            f"Operation: {results['operation']}",
            f"Input: {results['input']}"
        ]

        if results.get('variable'):
            output.append(f"Variable: {results['variable']}")

        output.append(f"Result: {results['output']}")

        if results.get('latex'):
            output.append(f"LaTeX: {results['latex']}")

        return "\n".join(output)
