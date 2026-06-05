#!/usr/bin/env python3
"""Cheap executable prefilters for the No-Go Atlas v0.

These predicates intentionally operate on small normalized dictionaries, not on
full CICY/cohomology records.  The atlas builder records the evidence scope and
replay counts for each predicate.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def no_recorded_free_symmetry(record: dict[str, Any]) -> bool:
    """Reject Wilson-line goals when no recorded free action is available."""

    return bool(record.get("requires_wilson_line_descent", True)) and int(
        record.get("free_symmetry_option_count", 0)
    ) == 0


def vectorlike_excess(record: dict[str, Any]) -> bool:
    """Reject character-certified spectra with too many vectorlike 5/5bar pairs."""

    pair = (
        record.get("actual_per_character_pair")
        or record.get("best_actual_pair")
        or record.get("vectorlike_pair")
    )
    if not pair or len(pair) != 2:
        return False
    allowed_pairs = {
        tuple(item)
        for item in record.get("allowed_pairs", [[3, 0], [4, 1]])
    }
    return tuple(pair) not in allowed_pairs and int(pair[1]) > int(
        record.get("max_vectorlike_pairs", 1)
    )


def representative_character_mismatch(record: dict[str, Any]) -> bool:
    """Reject branch shadows whose requested character is not realized."""

    return (
        record.get("leg_type") == "physical_5bar_H1"
        and record.get("requested_multiplicities")
        != record.get("computed_multiplicities")
        and record.get("representative_status") == "representative_obstructed"
    )


def degree_zero_bilinear_not_top_cup(record: dict[str, Any]) -> bool:
    """Reject neutral degree-zero bilinears that miss H3(O_X)."""

    return (
        int(record.get("monomial_degree", -1)) == 0
        and int(record.get("direct_total_cohomological_degree", -1)) == 2
        and record.get("direct_target_group") == "H2(O_X)"
        and int(record.get("direct_target_dimension", -1)) == 0
        and int(record.get("required_singlet_degree_for_top_cubic", -1)) == 1
    )


def degree_one_doublet_triplet_inseparable(record: dict[str, Any]) -> bool:
    """Reject degree-one top-cup mass channels that also support doublets."""

    return (
        int(record.get("singlet_degree", 1)) == 1
        and int(record.get("triplet_pair_support", 0)) > 0
        and int(record.get("doublet_pair_support", 0)) > 0
    )


def higher_monoid_downstream_obstructed(record: dict[str, Any]) -> bool:
    """Reject higher-degree monoid operators that fail downstream safety gates."""

    return record.get("status") in {
        "higher_monoid_doublet_support_obstruction",
        "higher_monoid_triplet_only_but_proton_unprotected",
        "higher_monoid_triplet_only_proton_safe_but_cup_5_unrealizable",
        "higher_monoid_no_triplet_component_support",
        "no_invariant_monoid_le_bound",
    }


PREFILTERS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "no_recorded_free_symmetry": no_recorded_free_symmetry,
    "vectorlike_excess": vectorlike_excess,
    "representative_character_mismatch": representative_character_mismatch,
    "degree_zero_bilinear_not_top_cup": degree_zero_bilinear_not_top_cup,
    "degree_one_doublet_triplet_inseparable": degree_one_doublet_triplet_inseparable,
    "higher_monoid_downstream_obstructed": higher_monoid_downstream_obstructed,
}


def evaluate_prefilter(prefilter_id: str, record: dict[str, Any]) -> bool:
    return PREFILTERS[prefilter_id](record)


def describe_prefilters() -> dict[str, dict[str, Any]]:
    return {
        "no_recorded_free_symmetry": {
            "callable": "no_go_atlas_prefilters.no_recorded_free_symmetry",
            "inputs_required": [
                "requires_wilson_line_descent",
                "free_symmetry_option_count",
            ],
            "scope_note": "geometry-selection prefilter for Wilson-line descent goals",
        },
        "vectorlike_excess": {
            "callable": "no_go_atlas_prefilters.vectorlike_excess",
            "inputs_required": [
                "actual_per_character_pair or best_actual_pair",
                "allowed_pairs",
                "max_vectorlike_pairs",
            ],
            "scope_note": "spectrum/character prefilter after Wilson-line character decomposition",
        },
        "representative_character_mismatch": {
            "callable": "no_go_atlas_prefilters.representative_character_mismatch",
            "inputs_required": [
                "leg_type",
                "requested_multiplicities",
                "computed_multiplicities",
                "representative_status",
            ],
            "scope_note": "representative-realizability prefilter for branch-completed character shadows",
        },
        "degree_zero_bilinear_not_top_cup": {
            "callable": "no_go_atlas_prefilters.degree_zero_bilinear_not_top_cup",
            "inputs_required": [
                "monomial_degree",
                "direct_total_cohomological_degree",
                "direct_target_group",
                "direct_target_dimension",
                "required_singlet_degree_for_top_cubic",
            ],
            "scope_note": "CY3 top-degree prefilter before mass-rank claims",
        },
        "degree_one_doublet_triplet_inseparable": {
            "callable": "no_go_atlas_prefilters.degree_one_doublet_triplet_inseparable",
            "inputs_required": [
                "singlet_degree",
                "triplet_pair_support",
                "doublet_pair_support",
            ],
            "scope_note": "doublet-triplet selection prefilter for degree-one top-cup channels",
        },
        "higher_monoid_downstream_obstructed": {
            "callable": "no_go_atlas_prefilters.higher_monoid_downstream_obstructed",
            "inputs_required": ["status"],
            "scope_note": "higher-degree monoid status prefilter before candidate promotion",
        },
    }
