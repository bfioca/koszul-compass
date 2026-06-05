#!/usr/bin/env python3
"""Verify the improved three-point deformation segment through K_even."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.characters import cicy7484_actual_wedge2_z2xz2_character_certificate  # noqa: E402
from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicy_symmetry import cicy_7484_topological_equivariance_report  # noqa: E402

from search_cicy7484_even_global_candidates import novelty_for_matrix  # noqa: E402
from search_cicy7484_hyperplane_candidates import load_cicy_7484, novelty_key_sets  # noqa: E402
from verify_family_candidate import BASE_SYMMETRY_ORDER, cohomology_and_spectrum  # noqa: E402


REPORTS = ROOT / "reports"
RAW = ROOT / "data" / "raw"

BASE_MATRIX = [[-3, -2, 1, 2, 2], [1, -1, -2, 1, 1], [0, 1, 1, -1, -1]]
DIRECTION = [[0, -2, 0, 0, 2], [0, -1, 0, 0, 1], [0, 1, 0, 0, -1]]


def add_matrix(n: int) -> list[list[int]]:
    return [
        [BASE_MATRIX[row][col] + n * DIRECTION[row][col] for col in range(5)]
        for row in range(3)
    ]


def verify(n_min: int, n_max: int) -> dict:
    cicy = load_cicy_7484()
    intersections = triple_intersections(cicy["Conf"])
    novelty_context = novelty_key_sets()
    expected_index = -3 * BASE_SYMMETRY_ORDER

    records = []
    for n in range(n_min, n_max + 1):
        matrix = add_matrix(n)
        index_v = bundle_index(matrix, intersections, cicy["C2"])
        index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
        c2_v = bundle_c2(matrix, intersections)
        anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
        hard_checks = {
            "c1_zero": bundle_c1(matrix) == [0, 0, 0],
            "index_v": index_v == expected_index,
            "index_wedge2_v": index_wedge2_v == expected_index,
            "anomaly_nonnegative_ambient": all(value >= 0 for value in anomaly),
            "summand_total_degrees_even": all(
                sum(col) % 2 == 0 for col in zip(*matrix)
            ),
        }
        cohomology = None
        equivariance = None
        novelty = None
        actual_wedge2 = None
        if all(hard_checks.values()):
            cohomology = cohomology_and_spectrum(cicy, BASE_SYMMETRY_ORDER, matrix)
            spectrum = cohomology["su5_upstairs_spectrum"]
            hard_checks["su5_net_chirality"] = all(spectrum["checks"].values())
            equivariance = cicy_7484_topological_equivariance_report(
                RAW / "cicylist.m", matrix
            )
            hard_checks["raw_z2xz2_lift_exists"] = equivariance[
                "equivariant_line_bundle_sum_lift_exists"
            ]
            actual_wedge2 = cicy7484_actual_wedge2_z2xz2_character_certificate(
                matrix, cicy["Conf"]
            )
            hard_checks["actual_wedge2_character_computed"] = actual_wedge2[
                "character_computed"
            ]
            novelty = novelty_for_matrix(matrix, cicy["Conf"], novelty_context)
            hard_checks["novel_under_implemented_equivalences"] = novelty["datasets"][
                "combined"
            ]["novel_under_row_and_column_permutation"]

        records.append(
            {
                "n": n,
                "matrix": matrix,
                "c1": bundle_c1(matrix),
                "summand_total_degrees": [sum(col) for col in zip(*matrix)],
                "index_v": index_v,
                "index_wedge2_v": index_wedge2_v,
                "anomaly": anomaly,
                "hard_checks": hard_checks,
                "passes_hard_gates": all(hard_checks.values()),
                "cohomology_and_spectrum": cohomology,
                "raw_symmetry_diagnostic": equivariance,
                "actual_wedge2_character_certificate": actual_wedge2,
                "novelty": novelty,
            }
        )

    hard_records = [record for record in records if record["passes_hard_gates"]]
    best_record = min(
        hard_records,
        key=lambda record: record["actual_wedge2_character_certificate"][
            "best_per_character_pair"
        ][1],
    )
    return {
        "family": {
            "cicy": 7484,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "base_matrix": BASE_MATRIX,
            "direction": DIRECTION,
            "formula": [
                ["-3", "-2-2n", "1", "2", "2+2n"],
                ["1", "-1-n", "-2", "1", "1+n"],
                ["0", "1+n", "1", "-1", "-1-n"],
            ],
            "exact_kappa_vector": [1, 3, 5],
            "polynomial_certificates": {
                "index_v": "-12",
                "index_wedge2_v": "-12",
                "anomaly": [
                    "-4 (n - 1) (n + 3)",
                    "-12 (n^2 + 2 n - 1)",
                    "-4 (n - 1) (n + 3)",
                ],
                "hard_gate_integer_segment": [-2, -1, 0],
            },
            "hard_gate_segment": [record["n"] for record in hard_records],
            "best_actual_pair": best_record["actual_wedge2_character_certificate"][
                "best_per_character_pair"
            ],
            "best_n": best_record["n"],
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-min", type=int, default=-5)
    parser.add_argument("--n-max", type=int, default=5)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "k_even_improved_family.json"),
    )
    args = parser.parse_args()

    result = verify(args.n_min, args.n_max)
    out = Path(args.json_out)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"hard_gate_segment={result['family']['hard_gate_segment']}")
    print(f"best_n={result['family']['best_n']}")
    print(f"best_actual_pair={result['family']['best_actual_pair']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
