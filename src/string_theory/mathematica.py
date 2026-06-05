"""Small Mathematica subset parser for the Oxford line-bundle data files."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


Token = tuple[str, str]


TOKEN_RE = re.compile(
    r"""
    (?P<SPACE>\s+)
  | (?P<ARROW>->)
  | (?P<LBRACE>\{)
  | (?P<RBRACE>\})
  | (?P<COMMA>,)
  | (?P<NUMBER>-?\d+)
  | (?P<SYMBOL>[A-Za-z$][A-Za-z0-9$]*)
  | (?P<OTHER>.)
    """,
    re.VERBOSE,
)


def strip_comments(text: str) -> str:
    return re.sub(r"\(\*.*?\*\)", "", text, flags=re.DOTALL)


def extract_assignment(text: str, name: str) -> str:
    marker = re.search(rf"\b{re.escape(name)}\s*=", text)
    if not marker:
        raise ValueError(f"assignment {name!r} not found")
    start = marker.end()
    while start < len(text) and text[start].isspace():
        start += 1
    depth = 0
    seen_open = False
    for i in range(start, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
            seen_open = True
        elif char == "}":
            depth -= 1
            if seen_open and depth == 0:
                end = i + 1
                while end < len(text) and text[end].isspace():
                    end += 1
                if end < len(text) and text[end] == ";":
                    return text[start:end]
                return text[start:end]
    raise ValueError(f"could not find complete assignment for {name!r}")


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    for match in TOKEN_RE.finditer(text):
        kind = match.lastgroup
        value = match.group()
        if kind == "SPACE":
            continue
        if kind == "OTHER":
            raise ValueError(f"unexpected Mathematica token {value!r}")
        tokens.append((kind or "", value))
    return tokens


@dataclass
class Parser:
    tokens: list[Token]
    pos: int = 0

    def peek(self) -> Token | None:
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def pop(self, expected: str | None = None) -> Token:
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of input")
        if expected is not None and token[0] != expected:
            raise ValueError(f"expected {expected}, got {token}")
        self.pos += 1
        return token

    def parse(self) -> Any:
        value = self.parse_expr()
        if self.peek() is not None:
            raise ValueError(f"trailing tokens start at {self.peek()}")
        return value

    def parse_expr(self) -> Any:
        left = self.parse_atom()
        if self.peek() and self.peek()[0] == "ARROW":
            self.pop("ARROW")
            right = self.parse_expr()
            return ("Rule", left, right)
        return left

    def parse_atom(self) -> Any:
        token = self.peek()
        if token is None:
            raise ValueError("unexpected end of input")
        kind, value = token
        if kind == "NUMBER":
            self.pop()
            return int(value)
        if kind == "SYMBOL":
            self.pop()
            if value == "True":
                return True
            if value == "False":
                return False
            return value
        if kind == "LBRACE":
            return self.parse_list()
        raise ValueError(f"unexpected token {token}")

    def parse_list(self) -> list[Any]:
        items: list[Any] = []
        self.pop("LBRACE")
        if self.peek() and self.peek()[0] == "RBRACE":
            self.pop("RBRACE")
            return items
        while True:
            items.append(self.parse_expr())
            token = self.peek()
            if token is None:
                raise ValueError("unterminated list")
            if token[0] == "COMMA":
                self.pop("COMMA")
                continue
            if token[0] == "RBRACE":
                self.pop("RBRACE")
                return items
            raise ValueError(f"expected comma or closing brace, got {token}")


def parse_mathematica_expr(text: str) -> Any:
    return Parser(tokenize(text)).parse()


def rules_to_dict(rules: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in rules:
        if not (isinstance(item, tuple) and len(item) == 3 and item[0] == "Rule"):
            raise ValueError(f"expected rule item, got {item!r}")
        key = item[1]
        if not isinstance(key, str):
            raise ValueError(f"expected symbolic rule key, got {key!r}")
        out[key] = item[2]
    return out


def load_assignment(path: str, name: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        text = strip_comments(handle.read())
    return parse_mathematica_expr(extract_assignment(text, name))
