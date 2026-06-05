#!/usr/bin/env python3
"""Verify the first kernel-preserving line-bundle deformation candidate."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import (
    bundle_c1,
    bundle_c2,
    bundle_index,
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.cohomology import (
    bundle_line_summands,
    cohomology_record,
    dual,
    line_bundle_sum_quality_diagnostic,
    sum_cohomologies,
    su5_upstairs_spectrum_checks,
    su5_order4_descent_constraints,
    wedge2_line_summands,
)
from string_theory.mathematica import load_assignment, rules_to_dict
from string_theory.slope import find_slope_zero, intersection_tensor

from verify_gut_benchmarks import iter_models


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


BASE_CICY = 7484
BASE_SYMMETRY_ORDER = 4
BASE_MATRIX = [[1, -4, 1, 1, 1], [3, 0, -1, -1, -1], [-1, 1, 0, 0, 0]]
DIRECTION = [[-1, 1, 0, 0, 0], [-1, 1, 0, 0, 0], [0, 0, 0, 0, 0]]


def add_matrix(matrix: list[list[int]], direction: list[list[int]], n: int) -> list[list[int]]:
    return [
        [matrix[row][col] + n * direction[row][col] for col in range(len(matrix[0]))]
        for row in range(len(matrix))
    ]


def interpolate_polynomial(values: dict[int, int]) -> list[str]:
    """Return rational coefficients c_i for p(n)=sum c_i n^i."""

    xs = list(values.keys())
    degree = len(xs) - 1
    coeffs = [Fraction(0) for _ in range(degree + 1)]
    for i, x_i in enumerate(xs):
        basis = [Fraction(1)]
        denom = Fraction(1)
        for j, x_j in enumerate(xs):
            if i == j:
                continue
            denom *= x_i - x_j
            basis = [Fraction(0), *basis]
            for power in range(len(basis) - 1):
                basis[power] -= x_j * basis[power + 1]
        scale = Fraction(values[x_i], 1) / denom
        for power, coeff in enumerate(basis):
            coeffs[power] += scale * coeff
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    return [str(coeff) for coeff in coeffs]


def cohomology_and_spectrum(cicy: dict, symmetry_order: int, matrix: list[list[int]]) -> dict:
    line_records = [cohomology_record(cicy["Conf"], line_bundle) for line_bundle in bundle_line_summands(matrix)]
    wedge_records = [cohomology_record(cicy["Conf"], line_bundle) for line_bundle in wedge2_line_summands(matrix)]
    dual_line_records = [cohomology_record(cicy["Conf"], dual(record["line_bundle"])) for record in line_records]
    dual_wedge_records = [cohomology_record(cicy["Conf"], dual(record["line_bundle"])) for record in wedge_records]

    v_cohomology = sum_cohomologies([item["cohomology"] for item in line_records])
    v_dual_cohomology = sum_cohomologies([item["cohomology"] for item in dual_line_records])
    wedge2_v_cohomology = sum_cohomologies([item["cohomology"] for item in wedge_records])
    wedge2_v_dual_cohomology = sum_cohomologies([item["cohomology"] for item in dual_wedge_records])
    spectrum = su5_upstairs_spectrum_checks(
        symmetry_order=symmetry_order,
        v_cohomology=v_cohomology,
        v_dual_cohomology=v_dual_cohomology,
        wedge2_v_cohomology=wedge2_v_cohomology,
        wedge2_v_dual_cohomology=wedge2_v_dual_cohomology,
    )
    descent = su5_order4_descent_constraints(
        symmetry_order=symmetry_order,
        v_cohomology=v_cohomology,
        wedge2_v_cohomology=wedge2_v_cohomology,
        quotient_group_structure=[2, 2],
    )
    return {
        "V_cohomology": v_cohomology,
        "V_dual_cohomology": v_dual_cohomology,
        "wedge2_V_cohomology": wedge2_v_cohomology,
        "wedge2_V_dual_cohomology": wedge2_v_dual_cohomology,
        "line_bundle_sum_quality": line_bundle_sum_quality_diagnostic(
            matrix=matrix,
            v_cohomology=v_cohomology,
            v_dual_cohomology=v_dual_cohomology,
        ),
        "su5_upstairs_spectrum": spectrum,
        "conditional_order4_descent_constraints": descent,
    }


def verify(n_min: int, n_max: int, tolerance: float) -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    cicys = {entry["Num"]: entry for entry in cicy_entries}
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")
    known_keys = {
        (cicy["Num"], symmetry_order, sorted_matrix_key(matrix))
        for cicy, symmetry_order, matrix in iter_models(cicys, line_bundle_sums)
    }

    cicy = cicys[BASE_CICY]
    d = triple_intersections(cicy["Conf"])
    tensor = intersection_tensor(d, cicy["H11"])
    expected_index = -3 * BASE_SYMMETRY_ORDER

    records = []
    for n in range(n_min, n_max + 1):
        matrix = add_matrix(BASE_MATRIX, DIRECTION, n)
        c2_v = bundle_c2(matrix, d)
        anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
        slope = find_slope_zero(matrix, tensor, tolerance=tolerance, restarts=20, max_iterations=2000, seed=91000 + n)
        cohomology = cohomology_and_spectrum(cicy, BASE_SYMMETRY_ORDER, matrix)
        hard_checks = {
            "c1_zero": bundle_c1(matrix) == [0] * cicy["H11"],
            "index_v": bundle_index(matrix, d, cicy["C2"]) == expected_index,
            "index_wedge2_v": wedge2_index(matrix, d, cicy["C2"]) == expected_index,
            "anomaly_nonnegative_ambient": all(value >= 0 for value in anomaly),
            "slope_zero_numerical": slope.feasible,
            "su5_net_chirality": all(cohomology["su5_upstairs_spectrum"]["checks"].values()),
        }
        records.append(
            {
                "n": n,
                "matrix": matrix,
                "novel_under_current_gutall_key": (
                    BASE_CICY,
                    BASE_SYMMETRY_ORDER,
                    sorted_matrix_key(matrix),
                )
                not in known_keys,
                "c1": bundle_c1(matrix),
                "index_v": bundle_index(matrix, d, cicy["C2"]),
                "index_wedge2_v": wedge2_index(matrix, d, cicy["C2"]),
                "c2_v": c2_v,
                "anomaly": anomaly,
                "slope_search": slope.as_dict(),
                **cohomology,
                "hard_checks": hard_checks,
                "passes_current_hard_gates": all(hard_checks.values()),
            }
        )

    index_v_values = {n: bundle_index(add_matrix(BASE_MATRIX, DIRECTION, n), d, cicy["C2"]) for n in range(-2, 2)}
    index_wedge_values = {n: wedge2_index(add_matrix(BASE_MATRIX, DIRECTION, n), d, cicy["C2"]) for n in range(-2, 2)}
    anomaly_values = {
        component: {
            n: [tx - v for tx, v in zip(cicy["C2"], bundle_c2(add_matrix(BASE_MATRIX, DIRECTION, n), d))][component]
            for n in range(-1, 2)
        }
        for component in range(cicy["H11"])
    }

    return {
        "family": {
            "cicy": BASE_CICY,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "base_matrix": BASE_MATRIX,
            "direction": DIRECTION,
            "formula": [
                ["1-n", "-4+n", "1", "1", "1"],
                ["3-n", "n", "-1", "-1", "-1"],
                ["-1", "1", "0", "0", "0"],
            ],
            "hard_gate_segment": [record["n"] for record in records if record["passes_current_hard_gates"]],
            "novel_hard_gate_segment": [
                record["n"]
                for record in records
                if record["passes_current_hard_gates"] and record["novel_under_current_gutall_key"]
            ],
        },
        "polynomial_certificates": {
            "index_v_coefficients": interpolate_polynomial(index_v_values),
            "index_wedge2_v_coefficients": interpolate_polynomial(index_wedge_values),
            "anomaly_coefficients_by_component": {
                str(component): interpolate_polynomial(values)
                for component, values in anomaly_values.items()
            },
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-min", type=int, default=-8)
    parser.add_argument("--n-max", type=int, default=8)
    parser.add_argument("--tolerance", type=float, default=1e-7)
    parser.add_argument("--json-out", default=str(REPORTS / "family_candidate_7484_shift12.json"))
    args = parser.parse_args()

    result = verify(args.n_min, args.n_max, args.tolerance)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"family_cicy={result['family']['cicy']}")
    print(f"hard_gate_segment={result['family']['hard_gate_segment']}")
    print(f"novel_hard_gate_segment={result['family']['novel_hard_gate_segment']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
