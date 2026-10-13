import ast
import math
import re
from typing import Union


Number = Union[int, float]


class CalculatorError(ValueError):
    pass


def _checked(value: Number) -> Number:
    if type(value) is int and value.bit_length() > 1024:
        raise CalculatorError("Hasil berada di luar rentang yang didukung.")
    if isinstance(value, float) and not math.isfinite(value):
        raise CalculatorError("Hasil berada di luar rentang yang didukung.")
    return value


def _normalize(expression: str) -> str:
    expression = expression.strip().lower().replace(",", ".")
    expression = re.sub(r"\bdari\b", "*", expression)
    expression = re.sub(r"(\d+(?:\.\d*)?|\.\d+)\s*%", r"(\1/100)", expression)
    expression = expression.replace("×", "*").replace("÷", "/")
    expression = re.sub(r"(?<=\d)\s*(?=\()", "*", expression)
    expression = re.sub(r"(?<=\))\s*(?=\d)", "*", expression)
    expression = re.sub(r"(?<=\))\s*(?=\()", "*", expression)
    return expression


def _evaluate(node: ast.AST) -> Number:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return _checked(node.value)
    if isinstance(node, ast.Num) and type(node.n) in (int, float):
        return _checked(node.n)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand)
        return _checked(value if isinstance(node.op, ast.UAdd) else -value)
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        try:
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise CalculatorError("Tidak dapat membagi dengan nol.")
                result = left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise CalculatorError("Tidak dapat membagi dengan nol.")
                result = left // right
            elif isinstance(node.op, ast.Mod):
                if right == 0:
                    raise CalculatorError("Tidak dapat membagi dengan nol.")
                result = left % right
            elif isinstance(node.op, ast.Pow):
                if abs(right) > 12:
                    raise CalculatorError("Pangkat maksimal yang didukung adalah 12.")
                result = left ** right
            else:
                raise CalculatorError("Operator tersebut tidak didukung.")
        except (OverflowError, ZeroDivisionError) as error:
            raise CalculatorError("Hasil berada di luar rentang yang didukung.") from error
        if isinstance(result, complex):
            raise CalculatorError("Hasil berada di luar rentang yang didukung.")
        return _checked(result)
    raise CalculatorError("Ekspresi mengandung operasi yang tidak didukung.")


def calculate(expression: str) -> Number:
    normalized = _normalize(expression)
    if not normalized:
        raise CalculatorError("Masukkan ekspresi terlebih dahulu.")
    if len(normalized) > 256:
        raise CalculatorError("Ekspresi terlalu panjang.")
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as error:
        raise CalculatorError("Ekspresi belum lengkap atau tidak valid.") from error
    return _evaluate(tree)


def format_result(value: Number) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return format(value, ".12g")
