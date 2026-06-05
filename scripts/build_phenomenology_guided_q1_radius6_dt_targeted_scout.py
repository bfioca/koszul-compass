#!/usr/bin/env python3
"""Target radius-6 moves from proton-safe doublet-triplet-obstructed q=1 seeds."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_h2_frontier_search import (  # noqa: E402
    apply_moves,
    matrix_key,
    max_abs_charge,
    rectangle_primitives,
    row_transfer_primitives,
    single_column_dipole_primitives,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
)
from build_phenomenology_guided_q1_search import raw_q1_signature  # noqa: E402
from build_vectorlike_obstruction_report import certify_5259_matrix, gate  # noqa: E402
from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_seed_records(
    profile: dict[str, Any], *, source_limit: int, profile_bucket: str
) -> list[dict[str, Any]]:
    seeds = profile["nearest_miss_samples"][profile_bucket]
    seeds = sorted(seeds, key=lambda item: (-item["weight"], item["label"]))
    selected = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for seed in seeds:
        key = matrix_key(seed["matrix"])
        if key in seen:
            continue
        seen.add(key)
        selected.append(seed)
        if len(selected) >= source_limit:
            break
    return selected


def priority_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        max_abs_charge(item["matrix"]),
        item["source_label"],
        item["move"]["family"],
        json.dumps(item["move"], sort_keys=True),
    )


def build_frontier(
    seeds: list[dict[str, Any]],
    primitives: list[dict[str, Any]],
    *,
    max_abs_charge_bound: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    counters = {
        "seed_records": len(seeds),
        "primitive_count": len(primitives),
        "raw_edges": 0,
        "unique_candidates": 0,
        "duplicate_up_to_summand_permutation": 0,
        "within_charge_bound": 0,
        "rejected_charge_bound": 0,
    }
    frontier = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for seed in seeds:
        for primitive in primitives:
            counters["raw_edges"] += 1
            matrix = apply_moves(seed["matrix"], [primitive])
            key = matrix_key(matrix)
            if key in seen:
                counters["duplicate_up_to_summand_permutation"] += 1
                continue
            seen.add(key)
            counters["unique_candidates"] += 1
            if max_abs_charge(matrix) > max_abs_charge_bound:
                counters["rejected_charge_bound"] += 1
                continue
            counters["within_charge_bound"] += 1
            frontier.append(
                {
                    "source_label": seed["label"],
                    "source_file": seed["source_file"],
                    "source_weight": seed["weight"],
                    "source_profile_bucket": seed["profile_bucket"],
                    "source_classification": seed["classification"],
                    "move": primitive,
                    "matrix": matrix,
                }
            )
    frontier.sort(key=priority_key)
    return frontier, counters


def build_report(
    *,
    source_limit: int,
    profile_bucket: str,
    max_abs_charge_bound: int,
    frontier_start: int,
    max_frontier_to_screen: int,
    max_raw_q1_to_certify: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
    progress_every: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    profile = load_json(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.json")
    profile_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile_verification.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    primitives = [
        *single_column_dipole_primitives(),
        *row_transfer_primitives(),
        *rectangle_primitives(),
    ]
    seeds = load_seed_records(
        profile, source_limit=source_limit, profile_bucket=profile_bucket
    )
    frontier, frontier_counters = build_frontier(
        seeds, primitives, max_abs_charge_bound=max_abs_charge_bound
    )
    screened = frontier[frontier_start : frontier_start + max_frontier_to_screen]
    counters = {
        "frontier_start": frontier_start,
        "frontier_records_screened": len(screened),
        "frontier_records_after_window": max(
            0, len(frontier) - frontier_start - len(screened)
        ),
        "c1_survivors": 0,
        "index_survivors": 0,
        "anomaly_survivors": 0,
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "raw_q1_spectrum_survivors": 0,
        "raw_q1_certification_attempts": 0,
        "character_certified_q1_survivors": 0,
        "topology_exceptions": 0,
        "cohomology_exceptions": 0,
    }
    rejections: Counter[str] = Counter()
    raw_q1_records = []
    exception_samples = []

    for index, item in enumerate(screened):
        try:
            if bundle_c1(item["matrix"]) != [0] * 7:
                rejections["c1"] += 1
                continue
            counters["c1_survivors"] += 1
            index_v = bundle_index(item["matrix"], intersections, c2_tx)
            index_wedge = wedge2_index(item["matrix"], intersections, c2_tx)
            if index_v != -6 or index_wedge != -6:
                rejections["index"] += 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(item["matrix"], intersections)
        except Exception as error:
            counters["topology_exceptions"] += 1
            if len(exception_samples) < 8:
                exception_samples.append(
                    {"stage": "topology", "type": type(error).__name__, "message": str(error)}
                )
            continue
        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            rejections["anomaly"] += 1
            continue
        counters["anomaly_survivors"] += 1
        slope = find_slope_zero(
            item["matrix"],
            tensor,
            tolerance=1e-7,
            restarts=slope_restarts,
            max_iterations=slope_max_iterations,
            seed=seed + index,
        )
        if not slope.feasible:
            rejections["slope"] += 1
            continue
        counters["slope_survivors"] += 1
        try:
            cohomology = cohomology_and_spectrum(
                {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2_tx},
                2,
                item["matrix"],
            )
        except Exception as error:
            counters["cohomology_exceptions"] += 1
            if len(exception_samples) < 8:
                exception_samples.append(
                    {"stage": "cohomology", "type": type(error).__name__, "message": str(error)}
                )
            continue
        spectrum = cohomology["su5_upstairs_spectrum"]
        quality = cohomology["line_bundle_sum_quality"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not quality["regular_nontrivial_summand_scan_style"]
        ):
            rejections["spectrum_or_quality"] += 1
            continue
        counters["spectrum_survivors"] += 1
        if not raw_q1_signature(cohomology):
            rejections["not_raw_q1"] += 1
            continue
        counters["raw_q1_spectrum_survivors"] += 1
        raw_q1_records.append(
            {
                **item,
                "anomaly": anomaly,
                "slope_search": slope.as_dict(),
                "cohomology": {
                    "V": cohomology["V_cohomology"],
                    "V_dual": cohomology["V_dual_cohomology"],
                    "wedge2_V": cohomology["wedge2_V_cohomology"],
                    "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
                },
            }
        )
        if progress_every and (index + 1) % progress_every == 0:
            print(
                "progress "
                f"screened={index + 1} "
                f"slope_survivors={counters['slope_survivors']} "
                f"raw_q1={counters['raw_q1_spectrum_survivors']}",
                flush=True,
            )

    certified_records = []
    filtered_records = []
    for index, raw in enumerate(raw_q1_records[:max_raw_q1_to_certify]):
        counters["raw_q1_certification_attempts"] += 1
        certified = certify_5259_matrix(
            label=f"radius6_dt_targeted_certified_{index}",
            matrix=raw["matrix"],
            move=[raw["move"]],
            slope_restarts=certification_restarts,
            slope_seed=seed + 700000 + index,
        )
        for key in [
            "source_label",
            "source_file",
            "source_weight",
            "source_profile_bucket",
            "source_classification",
            "move",
        ]:
            certified[f"radius6_{key}"] = raw[key]
        if certified["character_certified"]:
            counters["character_certified_q1_survivors"] += 1
        certified_records.append(certified)
        filtered = candidate_certificate_from_5259_record(
            label=f"radius6_dt_targeted_filtered_{index}",
            record=certified,
            conf=conf,
        )
        apply_monoid_obstruction_override(filtered)
        if not certified["character_certified"]:
            filtered["spectrum_certificate"]["desired_q1_three_family_signature"] = True
            filtered["classification"] = {
                "category": "unresolved",
                "status": "missing_character_or_charge_level_data",
                "reason": "candidate has the raw q=1 signature but lacks a complete character certificate",
            }
        for key in [
            "source_label",
            "source_file",
            "source_weight",
            "source_profile_bucket",
            "source_classification",
            "move",
        ]:
            filtered[f"radius6_{key}"] = raw[key]
        filtered_records.append(filtered)

    categories = Counter(record["classification"]["category"] for record in filtered_records)
    statuses = Counter(record["classification"]["status"] for record in filtered_records)
    viable = [
        record for record in filtered_records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "imports_charge_profile": gate(
            profile_verification["all_gates_pass"]
            and profile["summary"]["weighted_profile_buckets"][profile_bucket] > 0,
            str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile_verification.json"),
            f"radius6 scout starts from verified `{profile_bucket}` profiles",
        ),
        "seed_records_loaded": gate(
            len(seeds) > 0
            and all(
                seed["profile_bucket"] == profile_bucket
                for seed in seeds
            ),
            str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.json"),
            f"selected seeds come from the `{profile_bucket}` filter bucket",
        ),
        "frontier_nonempty": gate(
            len(screened) > 0,
            "radius6 targeted frontier",
            "bounded radius6 frontier window is nonempty",
        ),
        "certification_budget_respected": gate(
            counters["raw_q1_certification_attempts"]
            == min(counters["raw_q1_spectrum_survivors"], max_raw_q1_to_certify),
            "radius6 q1 certification budget",
            "certification pass attempted the configured number of raw q1 survivors",
        ),
        "candidate_tables_emitted": gate(
            all(
                record["spectrum_certificate"] is not None
                and record["character_certificate"] is not None
                and (
                    record["classification"]["category"] == "unresolved"
                    or (
                        record["mass_operator_table"] is not None
                        and record["proton_decay_operator_table"] is not None
                    )
                )
                for record in filtered_records
            ),
            "radius6 filtered candidate records",
            "every emitted candidate has spectrum/character evidence and charge tables when character-certified",
        ),
    }
    return {
        "scope": f"bounded radius6 targeted scout from `{profile_bucket}` q1 seeds",
        "status": (
            "viable_candidate_found_in_radius6_dt_targeted_scout"
            if viable
            else "no_viable_candidate_found_in_radius6_dt_targeted_scout_window"
        ),
        "parameters": {
            "source_limit": source_limit,
            "profile_bucket": profile_bucket,
            "max_abs_charge_bound": max_abs_charge_bound,
            "frontier_start": frontier_start,
            "max_frontier_to_screen": max_frontier_to_screen,
            "max_raw_q1_to_certify": max_raw_q1_to_certify,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
        },
        "source_summary": {
            "selected_seed_records": len(seeds),
            "selected_seed_labels": [seed["label"] for seed in seeds],
            "selected_seed_weight": sum(seed["weight"] for seed in seeds),
        },
        "frontier_counters": frontier_counters,
        "screening_counters": counters,
        "rejection_counters": dict(sorted(rejections.items())),
        "summary": {
            "raw_q1_spectrum_survivors": counters["raw_q1_spectrum_survivors"],
            "certified_q1_records": len(filtered_records),
            "character_certified_q1_survivors": counters[
                "character_certified_q1_survivors"
            ],
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "viable_count": len(viable),
        },
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_candidate_records": filtered_records,
        "exception_samples": exception_samples,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-6 DT-Targeted Scout",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Seeds", ""])
    for label in report["source_summary"]["selected_seed_labels"]:
        lines.append(f"- `{label}`")
    lines.extend(["", "## Candidate Classifications", ""])
    for record in report["filtered_candidate_records"]:
        lines.append(
            f"- `{record['label']}` from `{record['radius6_source_label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-limit", type=int, default=8)
    parser.add_argument(
        "--profile-bucket",
        default="proton_safe_but_doublet_triplet_not_selective",
        choices=[
            "proton_safe_but_doublet_triplet_not_selective",
            "proton_safe_but_no_triplet_mass",
            "triplet_mass_but_dangerous_operator_allowed",
            "no_triplet_mass_and_dangerous_operator_allowed",
        ],
    )
    parser.add_argument("--max-abs-charge-bound", type=int, default=5)
    parser.add_argument("--frontier-start", type=int, default=0)
    parser.add_argument("--max-frontier-to-screen", type=int, default=2400)
    parser.add_argument("--max-raw-q1-to-certify", type=int, default=40)
    parser.add_argument("--slope-restarts", type=int, default=8)
    parser.add_argument("--slope-max-iterations", type=int, default=1500)
    parser.add_argument("--certification-restarts", type=int, default=32)
    parser.add_argument("--seed", type=int, default=526000)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.md"),
    )
    args = parser.parse_args()
    report = build_report(
        source_limit=args.source_limit,
        profile_bucket=args.profile_bucket,
        max_abs_charge_bound=args.max_abs_charge_bound,
        frontier_start=args.frontier_start,
        max_frontier_to_screen=args.max_frontier_to_screen,
        max_raw_q1_to_certify=args.max_raw_q1_to_certify,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
        progress_every=args.progress_every,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
