"""Math tools: calculator, solve_linear_system, linprog.

AST-based safe calculator (no eval), numpy linalg solver, scipy LP solver.
"""
import ast
import operator as op

import numpy as np
from scipy.optimize import linprog as _scipy_linprog

_ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Non-numeric constant: {node.value!r}")
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Disallowed operator: {op_type.__name__}")
        return _ALLOWED_OPS[op_type](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPS:
            raise ValueError(f"Disallowed unary operator: {op_type.__name__}")
        return _ALLOWED_OPS[op_type](_eval(node.operand))
    raise ValueError(f"Disallowed AST node: {type(node).__name__}")


def calculator(expression: str) -> float:
    """Evaluate a simple arithmetic expression safely using AST."""
    tree = ast.parse(expression, mode="eval")
    return _eval(tree)


def solve_linear_system(A: list, b: list) -> list:
    """Solve linear system Ax = b. Returns list[float]."""
    try:
        x = np.linalg.solve(np.array(A, dtype=float), np.array(b, dtype=float))
        return [float(v) for v in x]
    except np.linalg.LinAlgError as e:
        raise ValueError(f"Singular matrix; no unique solution: {e}") from e


def linprog(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None, bounds=None) -> dict:
    """Minimize c·x subject to constraints. For maximization, negate c.

    bounds default: (0, None) per variable (non-negative).
    """
    if bounds is None:
        bounds = [(0, None)] * len(c)
    else:
        # convert [[lo, hi], ...] with None-friendly representation
        bounds = [tuple(pair) for pair in bounds]

    result = _scipy_linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )
    return {
        "x": [float(v) for v in result.x] if result.x is not None else [],
        "fun": float(result.fun) if result.fun is not None else None,
        "status": int(result.status),
        "success": bool(result.success),
        "message": result.message,
    }


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a simple arithmetic expression with +, -, *, /, **, %, and parentheses. Numbers only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression, e.g. '(3+4)*2'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solve_linear_system",
            "description": "Solve the linear system Ax = b where A is an n×n matrix and b is a length-n vector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "A": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "number"}},
                    },
                    "b": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["A", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "linprog",
            "description": (
                "Solve a linear program: minimize c·x subject to A_ub·x ≤ b_ub, "
                "A_eq·x = b_eq, bounds. For maximization, negate c."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "c": {"type": "array", "items": {"type": "number"}},
                    "A_ub": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "number"}},
                    },
                    "b_ub": {"type": "array", "items": {"type": "number"}},
                    "A_eq": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "number"}},
                    },
                    "b_eq": {"type": "array", "items": {"type": "number"}},
                    "bounds": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": ["number", "null"]},
                        },
                        "description": "List of [lower, upper] per variable. null means unbounded. Default [0, null] if omitted.",
                    },
                },
                "required": ["c"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "solve_linear_system": solve_linear_system,
    "linprog": linprog,
}
