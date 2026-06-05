#!/usr/bin/env python3
"""Verify the CICY 2544 exact-chiral to one-Higgs deformation line."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_outside_regime_candidate_certificate import novelty_context
from string_theory.cicy import bundle_c1, bundle_c2, bundle_index, triple_intersections, wedge2_index
from string_theory.novelty import novelty_record
from string_theory.slope import find_slope_zero, intersection_tensor
from verify_family_candidate import cohomology_and_spectrum


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def interpolate_polynomial(values: dict[int, int]) -> list[str]:
    """Return coefficients c_i for p(n)=sum_i c_i n^i."""

    xs = list(values)
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


def add_matrix(base: list[list[int]], direction: list[list[int]], n: int) -> list[list[int]]:
    return [
        [base[row][col] + n * direction[row][col] for col in range(5)]
        for row in range(len(base))
    ]


def verify(*, n_min: int, n_max: int, restarts: int, max_iterations: int) -> dict[str, Any]:
    exact = load_json(REPORTS / "outside_regime_candidate_certificate.json")
    higgs = load_json(REPORTS / "outside_regime_higgs_candidate_certificate.json")
    target_pool = load_json(REPORTS / "outside_regime_targets.json")
    cicy_num = exact["construction"]["cicy"]
    target = next(
        item
        for item in target_pool["immediate_favourable_targets"]
        if item["num"] == cicy_num
    )
    cicy = {
        "Num": cicy_num,
        "H11": target["h11"],
        "Conf": target["conf"],
        "C2": target["c2"],
    }
    base = exact["construction"]["matrix"]
    higgs_matrix = higgs["construction"]["matrix"]
    direction = [
        [higgs_matrix[row][col] - base[row][col] for col in range(5)]
        for row in range(cicy["H11"])
    ]
    intersections = triple_intersections(cicy["Conf"])
    tensor = intersection_tensor(intersections, cicy["H11"])
    novelty = novelty_context()
    records = []

    for n in range(n_min, n_max + 1):
        matrix = add_matrix(base, direction, n)
        c1 = bundle_c1(matrix)
        try:
            index_v = bundle_index(matrix, intersections, cicy["C2"])
            index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
            c2_v = bundle_c2(matrix, intersections)
        except ValueError as exc:
            records.append(
                {
                    "n": n,
                    "matrix": matrix,
                    "c1": c1,
                    "error": str(exc),
                    "passes_algebraic_gates": False,
                    "passes_current_hard_gates": False,
                }
            )
            continue
        anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
        algebraic = {
            "c1_zero": c1 == [0] * cicy["H11"],
            "index_v": index_v == -3,
            "index_wedge2_v": index_wedge2_v == -3,
            "anomaly_nonnegative_ambient": all(value >= 0 for value in anomaly),
        }
        slope = None
        cohomology = None
        novelty_records = None
        hard_checks = dict(algebraic)
        if all(algebraic.values()):
            slope = find_slope_zero(
                matrix,
                tensor,
                tolerance=1e-7,
                restarts=restarts,
                max_iterations=max_iterations,
                seed=2544500 + n,
            )
            cohomology = cohomology_and_spectrum(cicy, 1, matrix)
            spectrum = cohomology["su5_upstairs_spectrum"]
            quality = cohomology["line_bundle_sum_quality"]
            novelty_records = {
                name: novelty_record(
                    cicy_num=cicy_num,
                    symmetry_order=1,
                    matrix=matrix,
                    conf=cicy["Conf"],
                    dataset_keys=keys,
                )
                for name, keys in novelty["key_sets"].items()
            }
            hard_checks.update(
                {
                    "slope_zero_numerical": slope.feasible,
                    "su5_net_chirality": all(spectrum["checks"].values())
                    and spectrum["upstairs_anti_10"] == 0,
                    "regular_nontrivial_quality": quality[
                        "regular_nontrivial_summand_scan_style"
                    ],
                    "implemented_novelty": novelty_records["combined"][
                        "novel_under_row_and_column_permutation"
                    ],
                }
            )
        records.append(
            {
                "n": n,
                "matrix": matrix,
                "c1": c1,
                "index_v": index_v,
                "index_wedge2_v": index_wedge2_v,
                "c2_v": c2_v,
                "anomaly": anomaly,
                "algebraic_checks": algebraic,
                "slope_search": slope.as_dict() if slope is not None else None,
                "cohomology_and_spectrum": cohomology,
                "novelty": novelty_records,
                "hard_checks": hard_checks,
                "passes_algebraic_gates": all(algebraic.values()),
                "passes_current_hard_gates": all(hard_checks.values()),
            }
        )

    polynomial_ns = {-2, -1, 0, 1, 2}
    index_values = {
        n: bundle_index(add_matrix(base, direction, n), intersections, cicy["C2"])
        for n in polynomial_ns
    }
    wedge_values = {
        n: wedge2_index(add_matrix(base, direction, n), intersections, cicy["C2"])
        for n in polynomial_ns
    }
    anomaly_values = {
        component: {
            n: [
                tx - v
                for tx, v in zip(
                    cicy["C2"],
                    bundle_c2(add_matrix(base, direction, n), intersections),
                )
            ][component]
            for n in polynomial_ns
        }
        for component in range(cicy["H11"])
    }
    hard_records = [record for record in records if record["passes_current_hard_gates"]]
    one_higgs_records = [
        record
        for record in hard_records
        if record["cohomology_and_spectrum"]["su5_upstairs_spectrum"][
            "higgs_pair_candidates_upstairs"
        ]
        == 1
    ]
    exact_chiral_records = [
        record
        for record in hard_records
        if record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]["upstairs_5"]
        == 0
    ]
    return {
        "family": {
            "cicy": cicy_num,
            "base_label": exact["construction"]["label"],
            "higgs_label": higgs["construction"]["label"],
            "base_matrix": base,
            "direction": direction,
            "formula_interpretation": "K(n)=base+n*direction; n=0 is exact-chiral, n=1 is one-Higgs-pair.",
            "hard_gate_segment_in_checked_window": [
                record["n"] for record in hard_records
            ],
            "exact_chiral_n_values": [record["n"] for record in exact_chiral_records],
            "one_higgs_n_values": [record["n"] for record in one_higgs_records],
        },
        "polynomial_certificates": {
            "index_v_coefficients": interpolate_polynomial(index_values),
            "index_wedge2_v_coefficients": interpolate_polynomial(wedge_values),
            "anomaly_coefficients_by_component": {
                str(component): interpolate_polynomial(values)
                for component, values in anomaly_values.items()
            },
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-min", type=int, default=-5)
    parser.add_argument("--n-max", type=int, default=5)
    parser.add_argument("--restarts", type=int, default=32)
    parser.add_argument("--max-iterations", type=int, default=3000)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_higgs_deformation_line.json"),
    )
    args = parser.parse_args()

    result = verify(
        n_min=args.n_min,
        n_max=args.n_max,
        restarts=args.restarts,
        max_iterations=args.max_iterations,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"hard_gate_segment={result['family']['hard_gate_segment_in_checked_window']}")
    print(f"exact_chiral_n_values={result['family']['exact_chiral_n_values']}")
    print(f"one_higgs_n_values={result['family']['one_higgs_n_values']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
