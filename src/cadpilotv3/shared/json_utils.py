from __future__ import annotations

import ast
import json
import operator
import re
from typing import Any


class JSONExtractionError(ValueError):
    """Raised when valid JSON cannot be extracted from model output."""


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def extract_json_block(text: str) -> str:
    cleaned = strip_code_fences(text)

    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
    if not match:
        raise JSONExtractionError("No JSON object or array found in model output.")
    return match.group(1).strip()


def parse_json(text: str) -> Any:
    json_block = extract_json_block(text)
    try:
        return json.loads(json_block)
    except json.JSONDecodeError as exc:
        repaired_json_block = _repair_unquoted_numeric_expressions(json_block)
        if repaired_json_block != json_block:
            try:
                return json.loads(repaired_json_block)
            except json.JSONDecodeError:
                pass

        context = _format_json_error_context(json_block, exc.pos)
        raise JSONExtractionError(f"Failed to parse JSON: {exc}\n{context}") from exc


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _repair_unquoted_numeric_expressions(json_text: str) -> str:
    pattern = re.compile(
        r"(?P<prefix>:\s*)(?P<expr>[-+*/().0-9eE\s]+)(?=\s*[,}\]])",
    )

    def replace(match: re.Match[str]) -> str:
        expression = match.group("expr").strip()
        if not expression:
            return match.group(0)

        try:
            value = _evaluate_numeric_expression(expression)
        except ValueError:
            return match.group(0)

        return f"{match.group('prefix')}{_format_number(value)}"

    return pattern.sub(replace, json_text)


def _evaluate_numeric_expression(expression: str) -> float | int:
    if not re.fullmatch(r"[-+*/().0-9eE\s]+", expression):
        raise ValueError("expression contains unsupported characters")

    try:
        node = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("expression is not parseable") from exc

    value = _evaluate_numeric_ast(node.body)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _evaluate_numeric_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_numeric_ast(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_numeric_ast(node.left)
        right = _evaluate_numeric_ast(node.right)
        return _BINARY_OPERATORS[type(node.op)](left, right)

    raise ValueError("expression contains unsupported syntax")


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    return f"{value:.12g}"


def _format_json_error_context(json_text: str, position: int) -> str:
    start = max(0, position - 160)
    end = min(len(json_text), position + 160)
    excerpt = json_text[start:end].replace("\r", "")
    pointer = " " * (position - start) + "^"
    return f"Near JSON parse error:\n{excerpt}\n{pointer}"
