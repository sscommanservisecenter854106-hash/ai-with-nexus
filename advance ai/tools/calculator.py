import ast
import math
import operator
from .base import BaseTool
from .registry import register_tool

# Safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe functions
SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
}

@register_tool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = (
        "Evaluates exact mathematical, trigonometric, and scientific calculations. "
        "Use this whenever precise numerical results are required."
    )
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical formula to evaluate (e.g., 'sqrt(144) + 2**8', '355 / 113', 'sin(pi/2)')."
            }
        },
        "required": ["expression"]
    }

    def _eval(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in SAFE_FUNCTIONS:
                    args = [self._eval(arg) for arg in node.args]
                    return SAFE_FUNCTIONS[func_name](*args)
            raise ValueError(f"Unsupported function call: {ast.dump(node)}")
        elif isinstance(node, ast.Name):
            if node.id in SAFE_FUNCTIONS:
                return SAFE_FUNCTIONS[node.id]
            raise ValueError(f"Undefined variable or constant: {node.id}")
        else:
            raise ValueError(f"Unsupported syntax expression: {ast.dump(node)}")

    async def run(self, expression: str = "", **kwargs) -> str:
        if not expression.strip():
            return "Error: Empty expression provided."
        try:
            expr_clean = expression.replace("^", "**")
            parsed = ast.parse(expr_clean, mode="eval")
            result = self._eval(parsed.body)
            return f"Result: {result}"
        except Exception as e:
            return f"Calculation error for '{expression}': {str(e)}"
