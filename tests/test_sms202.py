from __future__ import annotations

from pathlib import Path

import pytest

from string_theory.sms202 import (
    SMS202ParseError,
    derive_invariants,
    parse_linemodels,
    parse_simple_fields,
    split_top_level,
    verify_golden_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks" / "sms202" / "model_1710_source.m"
EXPECTED = ROOT / "benchmarks" / "sms202" / "model_1710_expected.json"


def test_top_level_split_preserves_nested_rules_and_strings() -> None:
    expression = 'A -> {1, Subscript["x,y", 2]}, B -> {False, True}'

    assert split_top_level(expression) == [
        'A -> {1, Subscript["x,y", 2]}',
        "B -> {False, True}",
    ]


def test_model_1710_source_structure_and_invariants() -> None:
    records = parse_linemodels(SOURCE.read_text(encoding="utf-8"))

    assert len(records) == 1
    record = records[0]
    assert record.source_key == (7487, 4, 3)
    assert len(record.fields) == 38

    simple = parse_simple_fields(
        record,
        (
            "LineSum",
            "Coh",
            "Coh2",
            "CohSing",
            "GCoh",
            "GCoh2",
            "GCohSing",
            "EquivStr",
            "WLine",
            "HPairs",
            "IsSM",
            "Num5",
            "YuRank",
            "YdRank",
            "Dim4ProtonQ",
            "Dim5ProtonQ",
        ),
    )
    derived = derive_invariants(simple, group_order=record.source_key[1])

    assert derived["determinant_trivial"] is True
    assert derived["upstairs_h1"]["V"] == 12
    assert derived["upstairs_family_quotient"] == 3
    assert all(derived["character_tables_match_cohomology"].values())
    assert derived["downstairs_spectrum"]["three_family_chiral_sm_matter"] is True
    assert derived["downstairs_spectrum"]["one_higgs_pair_triplet_free"] is True
    assert derived["downstairs_spectrum"]["colored_triplet_vectorlike_pairs"] == 0
    assert derived["downstairs_spectrum"]["electroweak_doublet_vectorlike_pairs"] == 1
    assert simple["HPairs"] == simple["Num5"] == 1
    assert simple["YuRank"] == [2, 2]
    assert simple["YdRank"] == [1, 1]
    assert simple["Dim4ProtonQ"] == simple["Dim5ProtonQ"] == [False, False]


def test_model_1710_golden_benchmark_passes() -> None:
    result = verify_golden_benchmark(SOURCE, EXPECTED)

    assert result.passed, result.discrepancies
    assert result.discrepancies == ()
    assert result.observed["derived"]["upstairs_family_quotient"] == 3


def test_golden_benchmark_fails_closed_on_semantic_mutation(tmp_path: Path) -> None:
    mutated = SOURCE.read_text(encoding="utf-8").replace(
        "HPairs -> 1",
        "HPairs -> 2",
        1,
    )
    source = tmp_path / "mutated.m"
    source.write_text(mutated, encoding="utf-8")

    result = verify_golden_benchmark(source, EXPECTED)

    assert result.passed is False
    assert result.checks["source_sha256"] is False
    assert result.checks["simple_fields.HPairs"] is False


def test_golden_benchmark_fails_closed_on_wilson_mutation(tmp_path: Path) -> None:
    mutated = SOURCE.read_text(encoding="utf-8").replace(
        "WLine -> {{0, 0}, {0, 1}}",
        "WLine -> {{0, 0}, {1, 0}}",
        1,
    )
    source = tmp_path / "mutated-wilson.m"
    source.write_text(mutated, encoding="utf-8")

    result = verify_golden_benchmark(source, EXPECTED)

    assert result.passed is False
    assert result.checks["simple_fields.WLine"] is False
    assert result.checks["derived.downstairs_spectrum"] is False


def test_parser_rejects_unbalanced_source() -> None:
    with pytest.raises(SMS202ParseError, match="complete linemodels"):
        parse_linemodels("linemodels={{{7487,4,3} -> {{{Num -> {7487,4,3}}};")
