"""High-level CICY-list extraction without parsing symbolic symmetry payloads."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

from .mathematica import parse_mathematica_expr, strip_comments


FIELD_RE = re.compile(r"\b(Num|NumPs|NumPol|Eta|H11|H21)\s*->\s*(-?\d+)")


def split_top_level_entries(text: str) -> list[str]:
    """Split the outer Mathematica list into entry strings by brace depth."""

    clean = strip_comments(text)
    start = clean.find("{")
    if start < 0:
        raise ValueError("no outer list found")

    entries: list[str] = []
    entry_start: int | None = None
    depth = 0
    for pos in range(start, len(clean)):
        char = clean[pos]
        if char == "{":
            depth += 1
            if depth == 2 and entry_start is None:
                entry_start = pos
        elif char == "}":
            if depth == 2 and entry_start is not None:
                entries.append(clean[entry_start : pos + 1])
                entry_start = None
            depth -= 1
            if depth == 0:
                break
    return entries


def extract_rule_value_text(entry: str, key: str) -> str:
    """Extract the raw value text for a Mathematica rule in a CICY entry."""

    marker = re.search(rf"\b{re.escape(key)}\s*->", entry)
    if not marker:
        raise ValueError(f"rule {key!r} not found")
    pos = marker.end()
    while pos < len(entry) and entry[pos].isspace():
        pos += 1
    if pos >= len(entry):
        raise ValueError(f"rule {key!r} has no value")

    if entry[pos] == "{":
        depth = 0
        for end in range(pos, len(entry)):
            char = entry[end]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return entry[pos : end + 1]
        raise ValueError(f"unterminated list value for rule {key!r}")

    end = pos
    while end < len(entry) and entry[end] not in ",}":
        end += 1
    return entry[pos:end].strip()


def split_top_level_list_items(list_text: str) -> list[str]:
    """Split a raw Mathematica list value into top-level item strings."""

    text = strip_comments(list_text).strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError("expected Mathematica list text")

    items: list[str] = []
    item_start = 1
    depth = 0
    for pos, char in enumerate(text):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                item = text[item_start:pos].strip()
                if item:
                    items.append(item)
                break
        elif char == "," and depth == 1:
            item = text[item_start:pos].strip()
            if item:
                items.append(item)
            item_start = pos + 1
    return items


def parse_integer_list_rule(entry: str, key: str) -> list[Any]:
    """Parse a CICY rule whose value is a pure integer Mathematica list."""

    return parse_mathematica_expr(extract_rule_value_text(entry, key))


def symmetry_option_count(entry: str) -> int:
    if re.search(r'Symmetries\s*->\s*"unknown"', entry) or re.search(
        r"Symmetries\s*->\s*\{\}", entry
    ):
        return 0
    return len(split_top_level_list_items(extract_rule_value_text(entry, "Symmetries")))


def free_symmetry_option_count(entry: str) -> int:
    if re.search(r'Symmetries\s*->\s*"unknown"', entry) or re.search(
        r"Symmetries\s*->\s*\{\}", entry
    ):
        return 0
    return sum(
        1
        for item in split_top_level_list_items(extract_rule_value_text(entry, "Symmetries"))
        if item.lstrip().startswith("{True")
    )


def parse_cicy_metadata(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        entries = split_top_level_entries(handle.read())

    parsed: list[dict[str, Any]] = []
    for entry in entries:
        fields = {key: int(value) for key, value in FIELD_RE.findall(entry)}
        symm_unknown = bool(re.search(r'Symmetries\s*->\s*"unknown"', entry))
        symm_empty = bool(re.search(r"Symmetries\s*->\s*\{\}", entry))
        fields["SymmetryStatus"] = (
            "unknown" if symm_unknown else "empty" if symm_empty else "known_nonempty"
        )
        fields["HasKnownNonemptySymmetryData"] = fields["SymmetryStatus"] == "known_nonempty"
        fields["SymmetryOptionCount"] = symmetry_option_count(entry)
        fields["FreeSymmetryOptionCount"] = free_symmetry_option_count(entry)
        parsed.append(fields)
    return parsed


def summarize_cicy_metadata(entries: list[dict[str, Any]]) -> dict[str, Any]:
    h11_counts = Counter(entry["H11"] for entry in entries)
    h11_known_symmetry_counts = Counter(
        entry["H11"] for entry in entries if entry.get("HasKnownNonemptySymmetryData")
    )
    symmetry_status_counts = Counter(entry["SymmetryStatus"] for entry in entries)
    return {
        "entry_count": len(entries),
        "canonical_num_le_7890_count": sum(1 for entry in entries if entry["Num"] <= 7890),
        "appended_num_gt_7890_count": sum(1 for entry in entries if entry["Num"] > 7890),
        "symmetry_status_counts": dict(sorted(symmetry_status_counts.items())),
        "h11_counts": dict(sorted(h11_counts.items())),
        "h11_with_known_nonempty_symmetry_counts": dict(sorted(h11_known_symmetry_counts.items())),
        "candidate_h11_ge_7_with_known_symmetry": [
            entry["Num"]
            for entry in entries
            if entry.get("HasKnownNonemptySymmetryData") and entry["H11"] >= 7
        ],
        "appended_h11_ge_7_unknown_symmetry": [
            entry["Num"]
            for entry in entries
            if entry["Num"] > 7890 and entry["H11"] >= 7 and entry["SymmetryStatus"] == "unknown"
        ],
    }
