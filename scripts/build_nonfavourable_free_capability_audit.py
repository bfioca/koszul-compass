#!/usr/bin/env python3
"""Audit non-favourable h11>=7 CICYs with recorded free symmetries."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import ambient_dimensions, triple_intersections  # noqa: E402
from string_theory.cicy_symmetry import infer_ambient_row_permutation  # noqa: E402
from string_theory.cicylist import (  # noqa: E402
    extract_rule_value_text,
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
    split_top_level_list_items,
)


def free_symmetry_options(entry: str, block_sizes: list[int]) -> list[dict[str, Any]]:
    """Summarize raw free symmetry options using only lightweight parsing."""

    summaries: list[dict[str, Any]] = []
    symmetries = extract_rule_value_text(entry, "Symmetries")
    for option_index, option_text in enumerate(split_top_level_list_items(symmetries)):
        items = split_top_level_list_items(option_text)
        if not items or items[0].strip() != "True":
            continue
        coordinate_data = split_top_level_list_items(items[1])
        generator_matrices = split_top_level_list_items(coordinate_data[0])
        descriptor = [int(value) for value in re.findall(r"-?\d+", coordinate_data[1])]
        group_structure = [int(value) for value in re.findall(r"-?\d+", items[2])]

        row_permutations = []
        inference_failures = []
        for generator_index, matrix_text in enumerate(generator_matrices):
            try:
                row_permutations.append(
                    list(infer_ambient_row_permutation(matrix_text, block_sizes))
                )
            except Exception as exc:  # pragma: no cover - recorded in report
                inference_failures.append(
                    {
                        "generator_index": generator_index,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:240],
                    }
                )
        summaries.append(
            {
                "option_index": option_index,
                "quotient_order": descriptor[0] if descriptor else None,
                "generator_count_declared": descriptor[1] if len(descriptor) > 1 else None,
                "quotient_group_structure": group_structure,
                "coordinate_generator_count": len(generator_matrices),
                "ambient_row_permutations_inferred": not inference_failures,
                "generator_ambient_row_permutations": row_permutations,
                "ambient_row_permutation_inference_failures": inference_failures,
                "all_generators_ambient_row_trivial": bool(row_permutations)
                and all(
                    perm == list(range(len(block_sizes))) for perm in row_permutations
                ),
            }
        )
    return summaries


def zero_bundle_cohomology_probe(conf: list[list[int]]) -> dict[str, Any]:
    try:
        from string_theory.cohomology import line_cohomology

        cohomology = line_cohomology(conf, [0] * len(conf))
        return {
            "available": True,
            "scope": "ambient-restricted pyCICY line-bundle cohomology",
            "zero_bundle_cohomology": cohomology,
            "zero_bundle_matches_calabi_yau_expectation": cohomology == [1, 0, 0, 1],
        }
    except Exception as exc:  # pragma: no cover - environment-dependent diagnostic
        return {
            "available": False,
            "scope": "ambient-restricted pyCICY line-bundle cohomology",
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
        }


def target_record(
    meta: dict[str, Any], entry: str, *, probe_cohomology: bool
) -> dict[str, Any]:
    conf = parse_integer_list_rule(entry, "Conf")
    c2 = parse_integer_list_rule(entry, "C2")
    ambient_rank = meta["NumPs"]
    h11 = meta["H11"]
    rank_defect = h11 - ambient_rank
    dimensions = list(ambient_dimensions(conf))
    block_sizes = [dim + 1 for dim in dimensions]
    free_options = free_symmetry_options(entry, block_sizes)
    min_order = min(
        option["quotient_order"]
        for option in free_options
        if option["quotient_order"] is not None
    )

    intersections_available = False
    intersection_error = None
    try:
        intersections = triple_intersections(conf)
        intersections_available = bool(intersections)
    except Exception as exc:  # pragma: no cover - diagnostic only
        intersection_error = {"error_type": type(exc).__name__, "error": str(exc)[:240]}

    cohomology_probe = (
        zero_bundle_cohomology_probe(conf)
        if probe_cohomology
        else {
            "available": None,
            "scope": "ambient-restricted pyCICY line-bundle cohomology",
            "skipped": True,
        }
    )
    row_perm_inference_ok = any(
        option["ambient_row_permutations_inferred"] for option in free_options
    )

    certifiable_now = (
        rank_defect == 0
        and intersections_available
        and len(c2) == h11
        and cohomology_probe.get("available") is True
        and row_perm_inference_ok
    )
    return {
        "num": meta["Num"],
        "h11": h11,
        "h21": meta["H21"],
        "num_projective_factors": ambient_rank,
        "rank_defect_h11_minus_num_projective_factors": rank_defect,
        "ambient_dimensions": dimensions,
        "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
        "symmetry_option_count": meta["SymmetryOptionCount"],
        "min_recorded_free_quotient_order": min_order,
        "sample_free_quotient_group_structures": [
            option["quotient_group_structure"] for option in free_options[:8]
        ],
        "divisor_basis": {
            "ambient_restricted_basis_available": True,
            "ambient_restricted_basis_rank": ambient_rank,
            "full_picard_rank": h11,
            "full_h11_divisor_basis_imported": rank_defect == 0,
            "missing_full_divisor_basis_rank": rank_defect,
        },
        "intersection_form": {
            "ambient_restricted_intersection_form_computable": intersections_available,
            "ambient_restricted_tensor_rank": ambient_rank,
            "full_h11_intersection_form_available": rank_defect == 0,
            "intersection_error": intersection_error,
        },
        "c2_tx": {
            "ambient_c2_available": len(c2) == ambient_rank,
            "ambient_c2_length": len(c2),
            "full_h11_c2_available": len(c2) == h11,
        },
        "kahler_mori_cone": {
            "ambient_positive_orthant_approximation_available": True,
            "full_kahler_or_mori_cone_imported": rank_defect == 0,
            "ambient_approximation_is_full_cone_certificate": rank_defect == 0,
        },
        "symmetry_action": {
            "raw_free_coordinate_action_available": bool(free_options),
            "free_options_with_ambient_row_permutation_inference": sum(
                1
                for option in free_options
                if option["ambient_row_permutations_inferred"]
            ),
            "free_options": free_options[:12],
        },
        "line_bundle_cohomology_interface": cohomology_probe,
        "current_full_nonfavourable_certificate_status": (
            "certifiable_with_current_favourable_style_pipeline"
            if certifiable_now
            else "blocked_missing_full_nonfavourable_picard_intersection_c2_cone_data"
        ),
        "ambient_restricted_scout_allowed": (
            intersections_available
            and len(c2) == ambient_rank
            and cohomology_probe.get("available") is True
            and row_perm_inference_ok
        ),
        "tractability_key": [
            rank_defect,
            ambient_rank,
            min_order,
            -meta["FreeSymmetryOptionCount"],
            meta["Num"],
        ],
    }


def build_report(*, probe_cohomology: bool) -> dict[str, Any]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    targets = [
        target_record(meta, entry, probe_cohomology=probe_cohomology)
        for meta, entry in zip(metadata, entries)
        if meta["Num"] <= 7890
        and meta["H11"] >= 7
        and meta["FreeSymmetryOptionCount"] > 0
        and meta["H11"] != meta["NumPs"]
    ]
    targets.sort(key=lambda item: item["tractability_key"])
    rank_defects = Counter(
        item["rank_defect_h11_minus_num_projective_factors"] for item in targets
    )
    min_orders = Counter(item["min_recorded_free_quotient_order"] for item in targets)
    scoutable = [item for item in targets if item["ambient_restricted_scout_allowed"]]
    certifiable = [
        item
        for item in targets
        if item["current_full_nonfavourable_certificate_status"]
        == "certifiable_with_current_favourable_style_pipeline"
    ]
    return {
        "scope": "capability audit for non-favourable canonical h11>=7 CICYs with recorded free symmetries",
        "conclusion": {
            "status": (
                "full_nonfavourable_extension_blocked_by_missing_full_geometry_data"
                if not certifiable
                else "some_targets_certifiable_with_current_pipeline"
            ),
            "target_count": len(targets),
            "ambient_restricted_scoutable_target_count": len(scoutable),
            "full_nonfavourable_certifiable_target_count": len(certifiable),
            "primary_blocker": (
                "raw cicylist.m provides ambient configuration/C2/symmetry data, "
                "but not the full h11 divisor basis, full intersection form, full "
                "c2(TX), or full Kahler/Mori cone needed for non-favourable "
                "line-bundle certificates"
            ),
        },
        "summary": {
            "rank_defect_counts": dict(sorted(rank_defects.items())),
            "min_recorded_free_quotient_order_counts": dict(sorted(min_orders.items())),
            "top_tractable_target_nums": [item["num"] for item in scoutable[:10]],
        },
        "selected_ambient_restricted_scout_targets": [
            {
                "num": item["num"],
                "h11": item["h11"],
                "num_projective_factors": item["num_projective_factors"],
                "rank_defect": item[
                    "rank_defect_h11_minus_num_projective_factors"
                ],
                "min_recorded_free_quotient_order": item[
                    "min_recorded_free_quotient_order"
                ],
                "free_symmetry_option_count": item["free_symmetry_option_count"],
            }
            for item in scoutable[:10]
        ],
        "targets": targets,
        "interpretation": {
            "ambient_restricted_scouts_are_not_full_certificates": True,
            "why": "On non-favourable CICYs, ambient divisor charges span only a sublattice of Pic(X), so ambient index/anomaly/slope/cohomology checks do not certify arbitrary line bundles in the full h11 basis.",
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Non-Favourable Free-Symmetry Capability Audit",
        "",
        f"Status: `{report['conclusion']['status']}`",
        "",
        report["conclusion"]["primary_blocker"],
        "",
        "## Counts",
        "",
        f"- targets: {report['conclusion']['target_count']}",
        f"- ambient-restricted scoutable targets: {report['conclusion']['ambient_restricted_scoutable_target_count']}",
        f"- full non-favourable certifiable targets now: {report['conclusion']['full_nonfavourable_certifiable_target_count']}",
        f"- rank-defect counts: {report['summary']['rank_defect_counts']}",
        "",
        "## Top Ambient-Restricted Scout Targets",
        "",
        "| CICY | h11 | NumPs | defect | min |Gamma| | free opts |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["selected_ambient_restricted_scout_targets"]:
        lines.append(
            "| {num} | {h11} | {num_ps} | {defect} | {order} | {free} |".format(
                num=item["num"],
                h11=item["h11"],
                num_ps=item["num_projective_factors"],
                defect=item["rank_defect"],
                order=item["min_recorded_free_quotient_order"],
                free=item["free_symmetry_option_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            report["interpretation"]["why"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-cohomology-probe", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "nonfavourable_free_capability_audit.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "nonfavourable_free_capability_audit.md"),
    )
    args = parser.parse_args()

    report = build_report(probe_cohomology=not args.skip_cohomology_probe)
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(f"target_count={report['conclusion']['target_count']}")
    print(
        "ambient_restricted_scoutable_target_count="
        f"{report['conclusion']['ambient_restricted_scoutable_target_count']}"
    )
    print(
        "full_nonfavourable_certifiable_target_count="
        f"{report['conclusion']['full_nonfavourable_certifiable_target_count']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
