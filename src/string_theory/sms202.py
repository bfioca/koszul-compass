"""Structured ingestion and golden-benchmark checks for the SMS202 corpus.

The Oxford ``sms202.m`` file contains Mathematica expressions that are richer
than the small arithmetic subset parsed by :mod:`string_theory.mathematica`.
This module therefore separates the problem into two layers:

* a delimiter-aware reader identifies top-level groups, records, and rules
  without interpreting symbolic operator expressions;
* the existing Mathematica subset parser decodes fields made only from lists,
  integers, booleans, symbols, and rules.

Unsupported expressions remain immutable source text and are compared by
SHA-256 in golden benchmarks.  That lets the benchmark fail closed instead of
silently dropping the phenomenology fields it cannot yet interpret.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .mathematica import (
    extract_assignment,
    parse_mathematica_expr,
    strip_comments,
)


class SMS202ParseError(ValueError):
    """Raised when an SMS202 source expression is structurally malformed."""


@dataclass(frozen=True)
class SMS202Record:
    """One record from the ``linemodels`` assignment."""

    source_key: tuple[int, ...]
    record_index: int
    fields: Mapping[str, str]
    source_text: str


@dataclass(frozen=True)
class BenchmarkResult:
    """Machine-readable result of one immutable golden benchmark."""

    benchmark_id: str
    passed: bool
    checks: Mapping[str, bool]
    observed: Mapping[str, Any]
    discrepancies: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "passed": self.passed,
            "checks": dict(self.checks),
            "observed": dict(self.observed),
            "discrepancies": list(self.discrepancies),
        }

    def summary_dict(self) -> dict[str, Any]:
        failed_checks = sorted(name for name, passed in self.checks.items() if not passed)
        summary: dict[str, Any] = {
            "benchmark_id": self.benchmark_id,
            "passed": self.passed,
            "check_count": len(self.checks),
            "failed_checks": failed_checks,
            "discrepancies": list(self.discrepancies),
        }
        for name in ("source_key", "field_count", "derived", "corpus"):
            if name in self.observed:
                summary[name] = self.observed[name]
        return summary


_OPEN_TO_CLOSE = {"{": "}", "[": "]", "(": ")"}
_CLOSE_TO_OPEN = {value: key for key, value in _OPEN_TO_CLOSE.items()}


def _scan_top_level(text: str, separator: str) -> Iterable[tuple[int, int]]:
    """Yield slices separated by ``separator`` outside all delimiters/strings."""

    stack: list[str] = []
    in_string = False
    escaped = False
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue
        if char in _OPEN_TO_CLOSE:
            stack.append(char)
            index += 1
            continue
        if char in _CLOSE_TO_OPEN:
            if not stack or stack[-1] != _CLOSE_TO_OPEN[char]:
                raise SMS202ParseError(f"unmatched closing delimiter {char!r}")
            stack.pop()
            index += 1
            continue
        if not stack and text.startswith(separator, index):
            yield start, index
            index += len(separator)
            start = index
            continue
        index += 1

    if in_string:
        raise SMS202ParseError("unterminated Mathematica string")
    if stack:
        raise SMS202ParseError(f"unterminated delimiter {stack[-1]!r}")
    yield start, len(text)


def split_top_level(text: str, separator: str = ",") -> list[str]:
    """Split a Mathematica expression without crossing nested expressions."""

    return [
        text[start:end].strip()
        for start, end in _scan_top_level(text, separator)
        if text[start:end].strip()
    ]


def split_rule(text: str) -> tuple[str, str]:
    """Split one top-level Mathematica rule into its left and right sides."""

    pieces = split_top_level(text, "->")
    if len(pieces) != 2:
        raise SMS202ParseError(
            f"expected one top-level rule arrow, found {len(pieces) - 1}: {text[:80]!r}"
        )
    return pieces[0], pieces[1]


def _strip_list(text: str) -> str:
    value = text.strip()
    if len(value) < 2 or value[0] != "{" or value[-1] != "}":
        raise SMS202ParseError(f"expected Mathematica list, got {value[:80]!r}")
    return value[1:-1]


def parse_record(text: str, *, source_key: tuple[int, ...], index: int) -> SMS202Record:
    """Parse the top-level fields of a single SMS202 model record."""

    fields: dict[str, str] = {}
    for raw_rule in split_top_level(_strip_list(text)):
        raw_name, raw_value = split_rule(raw_rule)
        name = raw_name.strip()
        if not name or not name.replace("$", "").isalnum():
            raise SMS202ParseError(f"invalid record field name {name!r}")
        if name in fields:
            raise SMS202ParseError(f"duplicate record field {name!r}")
        fields[name] = raw_value.strip()
    return SMS202Record(
        source_key=source_key,
        record_index=index,
        fields=fields,
        source_text=text.strip(),
    )


def parse_linemodels(text: str) -> list[SMS202Record]:
    """Parse every record in an SMS202 ``linemodels`` assignment."""

    try:
        assignment = extract_assignment(strip_comments(text), "linemodels")
    except ValueError as exc:
        raise SMS202ParseError("could not extract a complete linemodels assignment") from exc
    records: list[SMS202Record] = []
    for raw_group in split_top_level(_strip_list(assignment)):
        raw_key, raw_models = split_rule(raw_group)
        parsed_key = parse_mathematica_expr(raw_key)
        if not isinstance(parsed_key, list) or not all(
            isinstance(value, int) for value in parsed_key
        ):
            raise SMS202ParseError(f"invalid linemodels key {parsed_key!r}")
        source_key = tuple(parsed_key)
        for raw_record in split_top_level(_strip_list(raw_models)):
            records.append(
                parse_record(raw_record, source_key=source_key, index=len(records))
            )
    return records


def parse_simple_fields(
    record: SMS202Record,
    names: Iterable[str],
) -> dict[str, Any]:
    """Decode selected fields with the strict Mathematica subset parser."""

    parsed: dict[str, Any] = {}
    for name in names:
        if name not in record.fields:
            raise SMS202ParseError(f"record is missing required field {name!r}")
        try:
            parsed[name] = parse_mathematica_expr(record.fields[name])
        except ValueError as exc:
            raise SMS202ParseError(f"field {name!r} is not a simple expression") from exc
    return parsed


def digest_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def digest_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def digest_record_fields(record: SMS202Record) -> str:
    """Hash all named field bodies while ignoring irrelevant wrapper spacing."""

    payload = json.dumps(
        dict(record.fields),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return digest_text(payload)


def _sum_h1(table: list[list[int]]) -> int:
    if not all(len(row) == 4 and all(isinstance(value, int) for value in row) for row in table):
        raise SMS202ParseError("expected a table of [h0, h1, h2, h3] rows")
    return sum(row[1] for row in table)


_Z2X2_BITS = ((0, 0), (1, 0), (0, 1), (1, 1))
_Z2X2_NAMES = ("1", "a", "b", "ab")


def _z2x2_twist(multiplicities: list[int], twist: tuple[int, int]) -> list[int]:
    if len(multiplicities) != 4:
        raise SMS202ParseError("Z2 x Z2 multiplicities must have four entries")
    result = [0, 0, 0, 0]
    for source_index, value in enumerate(multiplicities):
        source = _Z2X2_BITS[source_index]
        target = (source[0] ^ twist[0], source[1] ^ twist[1])
        result[_Z2X2_BITS.index(target)] += value
    return result


def _sum_representations(representations: Iterable[list[int]]) -> list[int]:
    result = [0, 0, 0, 0]
    for representation in representations:
        if len(representation) != 4:
            raise SMS202ParseError("Z2 x Z2 representation must have four entries")
        result = [left + right for left, right in zip(result, representation)]
    return result


def _character_tables_match(cohomology: Any, characters: Any) -> bool:
    if not isinstance(cohomology, list) or not isinstance(characters, list):
        return False
    if len(cohomology) != len(characters):
        return False
    return all(
        isinstance(cohomology_row, list)
        and len(cohomology_row) == 4
        and isinstance(character_row, list)
        and len(character_row) == 4
        and all(
            isinstance(multiplicities, list)
            and len(multiplicities) == 4
            and sum(multiplicities) == dimension
            for dimension, multiplicities in zip(cohomology_row, character_row)
        )
        for cohomology_row, character_row in zip(cohomology, characters)
    )


def derive_z2x2_downstairs_spectrum(simple: Mapping[str, Any]) -> dict[str, Any]:
    """Project published source characters through the recorded Z2 x Z2 Wilson line.

    This independently checks the character/Wilson arithmetic. It intentionally
    does not claim to reconstruct the character tables from CICY geometry.
    """

    equivariant = [tuple(bits) for bits in simple["EquivStr"]]
    if len(equivariant) != 5 or any(bits not in _Z2X2_BITS for bits in equivariant):
        raise SMS202ParseError("expected five Z2 x Z2 summand linearisations")

    direct_characters = simple["GCoh"]
    wedge_characters = simple["GCoh2"]
    summand_pairs = list(combinations(range(5), 2))
    if len(direct_characters) != 5 or len(wedge_characters) != len(summand_pairs):
        raise SMS202ParseError("character tables do not match SU(5) line-sum sectors")

    h1_v = _sum_representations(
        _z2x2_twist(row[1], equivariant[index])
        for index, row in enumerate(direct_characters)
    )
    h1_v_dual = _sum_representations(
        _z2x2_twist(row[2], equivariant[index])
        for index, row in enumerate(direct_characters)
    )

    def wedge_representation(degree: int) -> list[int]:
        representations = []
        for row, (left, right) in zip(wedge_characters, summand_pairs):
            twist = (
                equivariant[left][0] ^ equivariant[right][0],
                equivariant[left][1] ^ equivariant[right][1],
            )
            representations.append(_z2x2_twist(row[degree], twist))
        return _sum_representations(representations)

    h1_wedge2 = wedge_representation(1)
    h2_wedge2 = wedge_representation(2)
    triplet_bits, weak_bits = (tuple(bits) for bits in simple["WLine"])
    if triplet_bits not in _Z2X2_BITS or weak_bits not in _Z2X2_BITS:
        raise SMS202ParseError("Wilson-line characters are not Z2 x Z2 characters")
    triplet_index = _Z2X2_BITS.index(triplet_bits)
    weak_index = _Z2X2_BITS.index(weak_bits)

    # For order-two characters, the 10-sector ubar/e characters are trivial
    # while Q carries the product of triplet and weak fundamental characters.
    q_bits = (
        triplet_bits[0] ^ weak_bits[0],
        triplet_bits[1] ^ weak_bits[1],
    )
    q_index = _Z2X2_BITS.index(q_bits)
    trivial_index = _Z2X2_BITS.index((0, 0))
    result = {
        "character_order": list(_Z2X2_NAMES),
        "H1_V": h1_v,
        "H1_V_dual": h1_v_dual,
        "H1_wedge2_V": h1_wedge2,
        "H2_wedge2_V": h2_wedge2,
        "wilson_triplet_character": _Z2X2_NAMES[triplet_index],
        "wilson_weak_character": _Z2X2_NAMES[weak_index],
        "Q": h1_v[q_index],
        "ubar": h1_v[trivial_index],
        "ebar": h1_v[trivial_index],
        "dbar": h1_wedge2[triplet_index],
        "lepton_doublets": h1_wedge2[weak_index],
        "colored_triplets": h2_wedge2[triplet_index],
        "higgs_up_doublets": h2_wedge2[weak_index],
        "net_dbar_families": h1_wedge2[triplet_index] - h2_wedge2[triplet_index],
        "net_lepton_families": h1_wedge2[weak_index] - h2_wedge2[weak_index],
        "colored_triplet_vectorlike_pairs": h2_wedge2[triplet_index],
        "electroweak_doublet_vectorlike_pairs": h2_wedge2[weak_index],
    }
    result["three_family_chiral_sm_matter"] = (
        result["Q"] == result["ubar"] == result["ebar"] == 3
        and result["net_dbar_families"] == 3
        and result["net_lepton_families"] == 3
        and h1_v_dual == [0, 0, 0, 0]
    )
    result["one_higgs_pair_triplet_free"] = (
        result["three_family_chiral_sm_matter"]
        and result["colored_triplet_vectorlike_pairs"] == 0
        and result["electroweak_doublet_vectorlike_pairs"] == 1
    )
    return result


def derive_invariants(simple: Mapping[str, Any], group_order: int) -> dict[str, Any]:
    """Derive low-level checks without trusting published summary labels."""

    line_sum = simple["LineSum"]
    if not line_sum or not all(isinstance(row, list) for row in line_sum):
        raise SMS202ParseError("LineSum must be a non-empty matrix")
    column_count = len(line_sum[0])
    if any(len(row) != column_count for row in line_sum):
        raise SMS202ParseError("LineSum rows have inconsistent lengths")

    c1_rows = [sum(row) for row in line_sum]
    upstairs_h1 = {
        "V": _sum_h1(simple["Coh"]),
        "wedge2_V": _sum_h1(simple["Coh2"]),
        "singlets": _sum_h1(simple["CohSing"]),
    }
    result = {
        "c1_row_sums": c1_rows,
        "determinant_trivial": all(value == 0 for value in c1_rows),
        "ambient_rank": len(line_sum),
        "summand_count": column_count,
        "group_order": group_order,
        "upstairs_h1": upstairs_h1,
        "upstairs_family_quotient": upstairs_h1["V"] // group_order,
        "upstairs_family_divisible_by_group": upstairs_h1["V"] % group_order == 0,
    }
    character_fields = {"GCoh", "GCoh2", "GCohSing", "EquivStr", "WLine"}
    if character_fields.issubset(simple):
        result["character_tables_match_cohomology"] = {
            "V": _character_tables_match(simple["Coh"], simple["GCoh"]),
            "wedge2_V": _character_tables_match(simple["Coh2"], simple["GCoh2"]),
            "singlets": _character_tables_match(simple["CohSing"], simple["GCohSing"]),
        }
        result["downstairs_spectrum"] = derive_z2x2_downstairs_spectrum(simple)
    return result


def _compare(
    path: str,
    expected: Any,
    observed: Any,
    checks: dict[str, bool],
    discrepancies: list[str],
) -> None:
    passed = observed == expected
    checks[path] = passed
    if not passed:
        discrepancies.append(f"{path}: expected {expected!r}, observed {observed!r}")


def verify_golden_benchmark(
    source_path: Path,
    expectation_path: Path,
    *,
    corpus_path: Path | None = None,
) -> BenchmarkResult:
    """Reconstruct and compare one source-backed SMS202 golden benchmark."""

    expectation = json.loads(expectation_path.read_text(encoding="utf-8"))
    records = parse_linemodels(source_path.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}
    discrepancies: list[str] = []

    _compare(
        "source_sha256",
        expectation["source_sha256"],
        digest_file(source_path),
        checks,
        discrepancies,
    )
    _compare("record_count", 1, len(records), checks, discrepancies)
    if len(records) != 1:
        return BenchmarkResult(
            benchmark_id=expectation["benchmark_id"],
            passed=False,
            checks=checks,
            observed={"record_count": len(records)},
            discrepancies=tuple(discrepancies),
        )

    record = records[0]
    simple_names = tuple(expectation["simple_fields"])
    simple = parse_simple_fields(record, simple_names)
    derived = derive_invariants(simple, group_order=record.source_key[1])

    _compare(
        "record_fields_sha256",
        expectation["record_fields_sha256"],
        digest_record_fields(record),
        checks,
        discrepancies,
    )

    _compare(
        "source_key",
        expectation["source_key"],
        list(record.source_key),
        checks,
        discrepancies,
    )
    _compare(
        "field_names",
        expectation["field_names"],
        sorted(record.fields),
        checks,
        discrepancies,
    )
    for name, expected in expectation["simple_fields"].items():
        _compare(f"simple_fields.{name}", expected, simple[name], checks, discrepancies)
    for name, expected_digest in expectation["opaque_field_sha256"].items():
        observed_digest = digest_text(record.fields[name]) if name in record.fields else None
        _compare(
            f"opaque_field_sha256.{name}",
            expected_digest,
            observed_digest,
            checks,
            discrepancies,
        )
    for name, expected in expectation["derived"].items():
        _compare(f"derived.{name}", expected, derived[name], checks, discrepancies)

    corpus_observed: dict[str, Any] | None = None
    if corpus_path is not None:
        provenance = expectation["provenance"]
        corpus_records = parse_linemodels(corpus_path.read_text(encoding="utf-8"))
        structured_index = provenance["structured_record_index"]
        corpus_record = (
            corpus_records[structured_index]
            if 0 <= structured_index < len(corpus_records)
            else None
        )
        _compare(
            "corpus.source_sha256",
            provenance["original_corpus_sha256"],
            digest_file(corpus_path),
            checks,
            discrepancies,
        )
        _compare(
            "corpus.record_count",
            provenance["structured_record_count"],
            len(corpus_records),
            checks,
            discrepancies,
        )
        _compare(
            "corpus.record_fields_sha256",
            expectation["record_fields_sha256"],
            digest_record_fields(corpus_record) if corpus_record else None,
            checks,
            discrepancies,
        )
        corpus_observed = {
            "record_count": len(corpus_records),
            "structured_record_index": structured_index,
            "source_key": list(corpus_record.source_key) if corpus_record else None,
        }

    observed = {
        "source_key": list(record.source_key),
        "field_count": len(record.fields),
        "simple_fields": simple,
        "derived": derived,
        "opaque_field_sha256": {
            name: digest_text(record.fields[name])
            for name in expectation["opaque_field_sha256"]
            if name in record.fields
        },
    }
    if corpus_observed is not None:
        observed["corpus"] = corpus_observed
    return BenchmarkResult(
        benchmark_id=expectation["benchmark_id"],
        passed=all(checks.values()),
        checks=checks,
        observed=observed,
        discrepancies=tuple(discrepancies),
    )
