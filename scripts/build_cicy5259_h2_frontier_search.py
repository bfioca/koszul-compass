#!/usr/bin/env python3
"""Search the local 5259/7914 deformation frontier for lower H2(wedge2 V)."""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations, combinations_with_replacement
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

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


Matrix = list[list[int]]
Move = dict[str, Any]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def matrix_key(matrix: Matrix) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(column) for column in zip(*matrix)))


def max_abs_charge(matrix: Matrix) -> int:
    return max(abs(value) for row in matrix for value in row)


def row_transfer_primitives(rows: int = 7, cols: int = 5) -> list[Move]:
    out: list[Move] = []
    for row in range(rows):
        for a, b in combinations(range(cols), 2):
            for delta in (-1, 1):
                out.append(
                    {
                        "family": "two_column_row_transfer",
                        "row": row,
                        "columns": [a, b],
                        "delta": delta,
                    }
                )
    return out


def rectangle_primitives(rows: int = 7, cols: int = 5) -> list[Move]:
    out: list[Move] = []
    for r, s in combinations(range(rows), 2):
        for a, b in combinations(range(cols), 2):
            for delta in (-1, 1):
                out.append(
                    {
                        "family": "paired_row_column_rectangle",
                        "rows": [r, s],
                        "columns": [a, b],
                        "delta": delta,
                    }
                )
    return out


def single_column_dipole_primitives(rows: int = 7, cols: int = 5) -> list[Move]:
    out: list[Move] = []
    for column in range(cols):
        for r, s in combinations(range(rows), 2):
            for delta in (-1, 1):
                out.append(
                    {
                        "family": "single_column_row_dipole",
                        "column": column,
                        "rows": [r, s],
                        "delta": delta,
                    }
                )
    return out


def apply_move(matrix: Matrix, move: Move) -> None:
    family = move["family"]
    delta = move["delta"]
    if family == "two_column_row_transfer":
        row = move["row"]
        a, b = move["columns"]
        matrix[row][a] += delta
        matrix[row][b] -= delta
    elif family == "paired_row_column_rectangle":
        r, s = move["rows"]
        a, b = move["columns"]
        matrix[r][a] += delta
        matrix[s][a] -= delta
        matrix[r][b] -= delta
        matrix[s][b] += delta
    elif family == "single_column_row_dipole":
        r, s = move["rows"]
        column = move["column"]
        matrix[r][column] += delta
        matrix[s][column] -= delta
    else:
        raise ValueError(f"unknown move family {family}")


def apply_moves(base: Matrix, moves: Iterable[Move]) -> Matrix:
    matrix = [row[:] for row in base]
    for move in moves:
        apply_move(matrix, move)
    return matrix


def move_sequences(primitives: list[Move], max_radius: int) -> Iterable[tuple[int, tuple[int, ...]]]:
    yield 0, ()
    if max_radius >= 1:
        for index in range(len(primitives)):
            yield 1, (index,)
    for radius in range(2, max_radius + 1):
        for indices in combinations_with_replacement(range(len(primitives)), radius):
            yield radius, indices


def move_family_summary(moves: list[Move]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for move in moves:
        counts[move["family"]] += 1
    return dict(sorted(counts.items()))


def compact_record(
    *,
    label: str,
    radius: int,
    moves: list[Move],
    matrix: Matrix,
    anomaly: list[int],
    slope: dict[str, Any],
    cohomology: dict[str, Any],
) -> dict[str, Any]:
    spectrum = cohomology["su5_upstairs_spectrum"]
    return {
        "label": label,
        "radius": radius,
        "move_families": move_family_summary(moves),
        "moves": moves,
        "matrix": matrix,
        "max_abs_charge": max_abs_charge(matrix),
        "anomaly": anomaly,
        "slope_search": slope,
        "cohomology": {
            "V": cohomology["V_cohomology"],
            "V_dual": cohomology["V_dual_cohomology"],
            "wedge2_V": cohomology["wedge2_V_cohomology"],
            "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
        },
        "raw_h2_wedge2_v": cohomology["wedge2_V_cohomology"][2],
        "raw_h1_wedge2_v": cohomology["wedge2_V_cohomology"][1],
        "line_bundle_sum_quality": cohomology["line_bundle_sum_quality"],
        "su5_upstairs_spectrum": spectrum,
    }


def sort_compact_records(records: list[dict[str, Any]]) -> None:
    records.sort(
        key=lambda item: (
            item["raw_h2_wedge2_v"],
            item["raw_h1_wedge2_v"],
            item["radius"],
            item["max_abs_charge"],
            json.dumps(item["moves"], sort_keys=True),
        )
    )


def min_or_none(values: list[int]) -> int | None:
    return min(values) if values else None


def build_report(
    *,
    max_radius: int,
    max_abs_charge_bound: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    certification_limit: int,
    seed: int,
    progress_every: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    vectorlike = load_json(REPORTS / "vectorlike_obstruction_report.json")
    quotient = load_json(REPORTS / "cicy5259_quotient_wilson_line_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    start = vectorlike["new_5259_7914_candidate"]
    start_matrix = start["matrix"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)

    single_column = single_column_dipole_primitives()
    row_transfer = row_transfer_primitives()
    rectangles = rectangle_primitives()
    primitives = [*row_transfer, *rectangles]

    single_column_c1_preserving = sum(
        1
        for move in single_column
        if bundle_c1(apply_moves(start_matrix, [move])) == [0] * 7
    )

    counters_by_radius: dict[int, dict[str, int]] = {
        radius: {
            "unique_candidates": 0,
            "within_charge_bound": 0,
            "c1_survivors": 0,
            "index_survivors": 0,
            "anomaly_survivors": 0,
            "slope_survivors": 0,
            "spectrum_survivors": 0,
            "character_certified_survivors": 0,
        }
        for radius in range(max_radius + 1)
    }
    rejection_counters: dict[str, int] = defaultdict(int)
    minima: dict[str, list[int]] = defaultdict(list)
    seen: set[tuple[tuple[int, ...], ...]] = set()
    spectrum_records: list[dict[str, Any]] = []

    for sequence_index, (radius, primitive_indices) in enumerate(
        move_sequences(primitives, max_radius), start=1
    ):
        moves = [primitives[index] for index in primitive_indices]
        matrix = apply_moves(start_matrix, moves)
        key = matrix_key(matrix)
        if key in seen:
            rejection_counters["duplicate_up_to_summand_permutation"] += 1
            continue
        seen.add(key)
        counters = counters_by_radius[radius]
        counters["unique_candidates"] += 1

        if max_abs_charge(matrix) > max_abs_charge_bound:
            rejection_counters["charge_bound"] += 1
            continue
        counters["within_charge_bound"] += 1

        try:
            if bundle_c1(matrix) != [0] * 7:
                rejection_counters["c1"] += 1
                continue
            counters["c1_survivors"] += 1
            index_v = bundle_index(matrix, intersections, c2_tx)
            index_wedge = wedge2_index(matrix, intersections, c2_tx)
            if index_v != -6 or index_wedge != -6:
                rejection_counters["index"] += 1
                continue
            counters["index_survivors"] += 1
            c2_v = bundle_c2(matrix, intersections)
        except Exception:
            rejection_counters["topology_exception"] += 1
            continue

        anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
        if not all(value >= 0 for value in anomaly):
            rejection_counters["anomaly"] += 1
            continue
        counters["anomaly_survivors"] += 1

        slope = find_slope_zero(
            matrix,
            tensor,
            tolerance=1e-7,
            restarts=slope_restarts,
            max_iterations=slope_max_iterations,
            seed=seed + sequence_index,
        )
        if not slope.feasible:
            rejection_counters["slope"] += 1
            continue
        counters["slope_survivors"] += 1

        cohomology = cohomology_and_spectrum(
            {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2_tx},
            2,
            matrix,
        )
        raw_h2 = cohomology["wedge2_V_cohomology"][2]
        minima["after_slope_raw_h2_wedge2_v"].append(raw_h2)
        spectrum = cohomology["su5_upstairs_spectrum"]
        quality = cohomology["line_bundle_sum_quality"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not quality["regular_nontrivial_summand_scan_style"]
        ):
            rejection_counters["spectrum_or_quality"] += 1
            continue
        counters["spectrum_survivors"] += 1
        minima["after_spectrum_raw_h2_wedge2_v"].append(raw_h2)
        spectrum_records.append(
            compact_record(
                label=f"radius_{radius}_spectrum_candidate",
                radius=radius,
                moves=moves,
                matrix=matrix,
                anomaly=anomaly,
                slope=slope.as_dict(),
                cohomology=cohomology,
            )
        )
        if progress_every and sequence_index % progress_every == 0:
            print(
                "progress "
                f"sequence_index={sequence_index} "
                f"seen={len(seen)} "
                f"spectrum_survivors={len(spectrum_records)}",
                flush=True,
            )

    sort_compact_records(spectrum_records)
    if spectrum_records:
        min_raw_h2 = spectrum_records[0]["raw_h2_wedge2_v"]
    else:
        min_raw_h2 = None

    certification_queue: list[dict[str, Any]] = []
    seen_cert_keys: set[tuple[tuple[int, ...], ...]] = set()
    for record in spectrum_records:
        always_certify = record["raw_h2_wedge2_v"] <= 2
        minimum_frontier = min_raw_h2 is not None and record["raw_h2_wedge2_v"] == min_raw_h2
        under_current = record["raw_h2_wedge2_v"] <= 6
        if (
            always_certify
            or minimum_frontier
            or (under_current and len(certification_queue) < certification_limit)
        ):
            key = matrix_key(record["matrix"])
            if key not in seen_cert_keys:
                certification_queue.append(record)
                seen_cert_keys.add(key)

    certified_records: list[dict[str, Any]] = []
    for index, record in enumerate(certification_queue[: max(certification_limit, len([
        item for item in certification_queue if item["raw_h2_wedge2_v"] <= 2
    ]))]):
        certified = certify_5259_matrix(
            label=f"h2_frontier_radius_{record['radius']}_candidate_{index}",
            matrix=record["matrix"],
            move=record["moves"],
            slope_restarts=certification_restarts,
            slope_seed=seed + 900000 + index,
        )
        certified["frontier_radius"] = record["radius"]
        certified["frontier_move_families"] = record["move_families"]
        certified["frontier_raw_h2_wedge2_v"] = record["raw_h2_wedge2_v"]
        if certified["character_certified"]:
            counters_by_radius[record["radius"]]["character_certified_survivors"] += 1
        certified_records.append(certified)

    certified_records.sort(
        key=lambda item: (
            item["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"]
            if item["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"]
            is not None
            else 999,
            item["cohomology"]["wedge2_V"][2],
            item["frontier_radius"],
            max_abs_charge(item["matrix"]),
        )
    )
    certified_regular = [
        record
        for record in certified_records
        if record["character_certified"]
        and record["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"]
        is not None
    ]
    best_certified = certified_regular[0] if certified_regular else None
    target_records = [
        record
        for record in certified_regular
        if record["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"] <= 1
    ]

    if target_records:
        status = "target_found_h2_regular_multiplicity_le_one"
    elif best_certified is not None:
        status = "bounded_frontier_no_target_found"
    else:
        status = "bounded_frontier_no_character_certified_record"

    gates = {
        "starting_candidate_is_improved_5259_result": gate(
            start["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"] == 3
            and start["character_certified"],
            str(REPORTS / "vectorlike_obstruction_report.json"),
            "frontier starts from the certified one-move 5259/7914 deformation with three vectorlike pairs",
        ),
        "raw_z2_split_lift_compatibility_retained": gate(
            quotient["split_lift_7914"]["induced_picard_action_on_J0_to_J6"]
            == [0, 1, 2, 3, 4, 5, 6]
            and quotient["line_bundle_equivariance"][
                "direct_sum_equivariant_lift_exists"
            ],
            str(REPORTS / "cicy5259_quotient_wilson_line_report.json"),
            "the selected Z2 action lifts through the 7914 split and acts trivially on the full Picard basis",
        ),
        "bounded_graph_was_tested": gate(
            sum(item["unique_candidates"] for item in counters_by_radius.values()) > 0
            and max_radius >= 1,
            "frontier search counters",
            "bounded local graph was enumerated and gated",
        ),
        "certification_queue_was_attempted": gate(
            bool(certification_queue),
            "spectrum frontier records",
            "at least one spectrum-surviving frontier candidate was submitted to character certification",
        ),
        "target_status_is_consistent": gate(
            (status == "target_found_h2_regular_multiplicity_le_one")
            == bool(target_records),
            "certified frontier records",
            "status agrees with whether a q<=1 character-certified target exists",
        ),
    }
    if not target_records:
        gates["no_go_frontier_records_minimum"] = gate(
            best_certified is not None
            and best_certified["vectorlike_pair_prediction"][
                "h2_wedge2_regular_multiplicity"
            ]
            >= 2,
            "certified frontier records",
            "no character-certified radius/bound frontier record reached H2 regular multiplicity 0 or 1",
        )

    frontier_minima = {
        "after_slope_raw_h2_wedge2_v": min_or_none(
            minima["after_slope_raw_h2_wedge2_v"]
        ),
        "after_spectrum_raw_h2_wedge2_v": min_or_none(
            minima["after_spectrum_raw_h2_wedge2_v"]
        ),
        "after_character_certification_h2_regular_multiplicity": (
            best_certified["vectorlike_pair_prediction"][
                "h2_wedge2_regular_multiplicity"
            ]
            if best_certified
            else None
        ),
    }

    return {
        "scope": "CICY 5259/7914 local H2(wedge2 V) frontier search",
        "search_parameters": {
            "start": "new_5259_7914_candidate from vectorlike_obstruction_report.json",
            "max_radius": max_radius,
            "max_abs_charge_bound": max_abs_charge_bound,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "certification_limit": certification_limit,
            "seed": seed,
            "dedupe": "line-bundle summand permutation via sorted column vectors",
        },
        "move_families": {
            "single_column_row_dipole": {
                "raw_primitive_count": len(single_column),
                "c1_preserving_as_one_step_count": single_column_c1_preserving,
                "use_in_c1_preserving_graph": (
                    "not used as a one-step edge; paired dipoles are represented by "
                    "paired_row_column_rectangle moves"
                ),
            },
            "two_column_row_transfer": {"primitive_count": len(row_transfer)},
            "paired_row_column_rectangle": {"primitive_count": len(rectangles)},
        },
        "raw_z2_lift_compatibility": {
            "selected_5259_free_action_option": quotient[
                "selected_recorded_free_action_5259"
            ]["option_index"],
            "split_action_lift_certified": quotient["conclusion"][
                "split_action_lift_certified"
            ],
            "full_picard_action": quotient["split_lift_7914"][
                "induced_picard_action_on_J0_to_J6"
            ],
            "direct_sum_equivariant_lift_exists_for_starting_certificate": quotient[
                "line_bundle_equivariance"
            ]["direct_sum_equivariant_lift_exists"],
            "frontier_interpretation": (
                "because the lifted action fixes all seven Picard generators, raw "
                "divisor-class compatibility is automatic for every c1-preserving "
                "matrix in this 7914 basis; character certification remains the "
                "candidate-specific equivariant cohomology gate"
            ),
        },
        "starting_candidate": start,
        "counters_by_radius": {str(key): value for key, value in counters_by_radius.items()},
        "rejection_counters": dict(sorted(rejection_counters.items())),
        "frontier_minima": frontier_minima,
        "top_spectrum_frontier_records": spectrum_records[:25],
        "certification_queue_size": len(certification_queue),
        "certified_records": certified_records,
        "best_character_certified_record": best_certified,
        "target_records": target_records,
        "conclusion": {
            "status": status,
            "target_h2_regular_multiplicity": [0, 1],
            "target_found": bool(target_records),
            "best_h2_regular_multiplicity": frontier_minima[
                "after_character_certification_h2_regular_multiplicity"
            ],
            "best_raw_h2_wedge2_v_after_spectrum": frontier_minima[
                "after_spectrum_raw_h2_wedge2_v"
            ],
            "bounded_no_go_statement": (
                "No character-certified candidate with H2(wedge2 V) regular "
                "multiplicity 0 or 1 was found in this bounded radius/charge "
                "frontier."
                if not target_records
                else None
            ),
        },
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    conclusion = report["conclusion"]
    best = report["best_character_certified_record"]
    lines = [
        "# CICY 5259/7914 H2(wedge2 V) Frontier Search",
        "",
        f"Status: `{conclusion['status']}`",
        "",
        "## Search Bound",
        "",
        f"- max radius: `{report['search_parameters']['max_radius']}`",
        f"- max absolute charge: `{report['search_parameters']['max_abs_charge_bound']}`",
        f"- slope restarts: `{report['search_parameters']['slope_restarts']}`",
        f"- certification restarts: `{report['search_parameters']['certification_restarts']}`",
        "",
        "## Frontier Counts",
        "",
        f"- counters by radius: `{report['counters_by_radius']}`",
        f"- rejection counters: `{report['rejection_counters']}`",
        f"- certification queue size: `{report['certification_queue_size']}`",
        "",
        "## Minimum",
        "",
        f"- raw H2(wedge2 V) minimum after spectrum gates: `{conclusion['best_raw_h2_wedge2_v_after_spectrum']}`",
        f"- character-certified H2 regular multiplicity minimum: `{conclusion['best_h2_regular_multiplicity']}`",
    ]
    if best:
        lines.extend(
            [
                f"- best matrix: `{best['matrix']}`",
                f"- best cohomology `V/V*/wedge2V/wedge2V*`: `{best['cohomology']['V']}` / `{best['cohomology']['V_dual']}` / `{best['cohomology']['wedge2_V']}` / `{best['cohomology']['wedge2_V_dual']}`",
                f"- best vectorlike prediction: `{best['vectorlike_pair_prediction']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            (
                "A target candidate with H2(wedge2 V) regular multiplicity 0 or 1 was found."
                if conclusion["target_found"]
                else conclusion["bounded_no_go_statement"]
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-radius", type=int, default=2)
    parser.add_argument("--max-abs-charge", type=int, default=3)
    parser.add_argument("--slope-restarts", type=int, default=6)
    parser.add_argument("--slope-max-iterations", type=int, default=1200)
    parser.add_argument("--certification-restarts", type=int, default=20)
    parser.add_argument("--certification-limit", type=int, default=80)
    parser.add_argument("--seed", type=int, default=52597914)
    parser.add_argument("--progress-every", type=int, default=0)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_h2_frontier_search.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy5259_h2_frontier_search.md"),
    )
    args = parser.parse_args()
    report = build_report(
        max_radius=args.max_radius,
        max_abs_charge_bound=args.max_abs_charge,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        certification_limit=args.certification_limit,
        seed=args.seed,
        progress_every=args.progress_every,
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(
        "best_h2_regular_multiplicity="
        f"{report['conclusion']['best_h2_regular_multiplicity']}"
    )
    print(
        "best_raw_h2_wedge2_v_after_spectrum="
        f"{report['conclusion']['best_raw_h2_wedge2_v_after_spectrum']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
