#!/usr/bin/env python3
"""Exact-kappa plane search for CICY 7484 lift-compatible candidates."""

from __future__ import annotations

import argparse
import json
from math import gcd
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
    sorted_matrix_key,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicy_symmetry import cicy_7484_topological_equivariance_report  # noqa: E402
from string_theory.symbolic_slope import (  # noqa: E402
    cicy_7484_kahler_ray_for_positive_kappa,
    cicy_7484_positive_kappa_ray_exists,
)

from search_cicy7484_even_global_candidates import novelty_for_matrix  # noqa: E402
from search_cicy7484_hyperplane_candidates import (  # noqa: E402
    load_cicy_7484,
    matrix_from_columns,
    novelty_key_sets,
    zero_sum_column_multisets,
)
from verify_family_candidate import BASE_SYMMETRY_ORDER, cohomology_and_spectrum  # noqa: E402


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def primitive_positive_kappas(kappa_max: int) -> list[list[int]]:
    kappas = []
    for p in range(1, kappa_max + 1):
        for q in range(1, kappa_max + 1):
            for r in range(1, kappa_max + 1):
                if gcd(gcd(p, q), r) != 1:
                    continue
                if cicy_7484_positive_kappa_ray_exists([p, q, r]):
                    kappas.append([p, q, r])
    return kappas


def columns_for_kappa(
    kappa: list[int], bound: int, *, allow_zero_column: bool = False
) -> list[tuple[int, int, int]]:
    p, q, r = kappa
    return [
        (x, y, z)
        for x in range(-bound, bound + 1)
        for y in range(-bound, bound + 1)
        for z in range(-bound, bound + 1)
        if (allow_zero_column or (x, y, z) != (0, 0, 0))
        and (x + y + z) % 2 == 0
        and p * x + q * y + r * z == 0
    ]


def verify(
    bound: int,
    kappa_max: int,
    progress: bool = False,
    selected_kappas: list[list[int]] | None = None,
    skip_kappa_max: int | None = None,
    min_column_count: int = 5,
    max_column_count: int | None = None,
    max_planes: int | None = None,
    allow_zero_column: bool = False,
) -> dict:
    cicy = load_cicy_7484()
    novelty_context = novelty_key_sets()
    intersections = triple_intersections(cicy["Conf"])
    expected_index = -3 * BASE_SYMMETRY_ORDER

    records = []
    plane_summaries = []
    seen_keys = set()
    candidate_plane_count = 0
    total_zero_sum_multisets = 0
    algebraic_survivor_count = 0
    kappas = (
        selected_kappas
        if selected_kappas is not None
        else primitive_positive_kappas(kappa_max)
    )
    for kappa in kappas:
        if skip_kappa_max is not None and max(kappa) <= skip_kappa_max:
            continue
        kahler = cicy_7484_kahler_ray_for_positive_kappa(kappa)
        if kahler is None:
            continue
        columns = columns_for_kappa(
            kappa, bound, allow_zero_column=allow_zero_column
        )
        if len(columns) < min_column_count:
            continue
        if max_column_count is not None and len(columns) > max_column_count:
            continue
        candidate_plane_count += 1
        if max_planes is not None and candidate_plane_count > max_planes:
            candidate_plane_count -= 1
            break
        zero_sum_indices = zero_sum_column_multisets(columns)
        total_zero_sum_multisets += len(zero_sum_indices)
        plane_algebraic = 0
        plane_spectrum = 0
        for indices in zero_sum_indices:
            matrix = matrix_from_columns(columns, indices)
            key = sorted_matrix_key(matrix)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            try:
                index_v = bundle_index(matrix, intersections, cicy["C2"])
                index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
                c2_v = bundle_c2(matrix, intersections)
            except ValueError:
                continue
            if index_v != expected_index or index_wedge2_v != expected_index:
                continue
            anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
            if not all(value >= 0 for value in anomaly):
                continue
            algebraic_survivor_count += 1
            plane_algebraic += 1
            cohomology = cohomology_and_spectrum(cicy, BASE_SYMMETRY_ORDER, matrix)
            spectrum = cohomology["su5_upstairs_spectrum"]
            if not all(spectrum["checks"].values()):
                continue
            equivariance = cicy_7484_topological_equivariance_report(
                RAW / "cicylist.m", matrix
            )
            if not equivariance["equivariant_line_bundle_sum_lift_exists"]:
                continue
            descent = cohomology["conditional_order4_descent_constraints"]
            actual_wedge2 = cicy7484_actual_wedge2_z2xz2_character_certificate(
                matrix, cicy["Conf"]
            )
            descent["raw_symmetry_equivariant_lift_available"] = True
            descent["actual_z2xz2_wedge2_character_certificate"] = actual_wedge2
            descent["full_wilson_line_spectrum_proven"] = (
                actual_wedge2["character_computed"]
                and descent["ten_sector"]["actual_h1_representation_forced_regular_multiplicity"]
                == 3
            )
            if "z2xz2_wilson_line_spectrum_envelope" in descent:
                envelope = descent["z2xz2_wilson_line_spectrum_envelope"]
                envelope["applicable_to_candidate_raw_symmetry"] = True
                envelope["actual_wilson_line_spectrum_proven"] = descent[
                    "full_wilson_line_spectrum_proven"
                ]
                envelope["actual_per_character_pair"] = actual_wedge2.get(
                    "per_character_pair"
                )
            plane_spectrum += 1
            records.append(
                {
                    "kappa_vector": kappa,
                    "matrix": matrix,
                    "summand_total_degrees": [sum(col) for col in zip(*matrix)],
                    "trivial_summand_count": sum(
                        all(value == 0 for value in col) for col in zip(*matrix)
                    ),
                    "c1": bundle_c1(matrix),
                    "index_v": index_v,
                    "index_wedge2_v": index_wedge2_v,
                    "anomaly": anomaly,
                    "max_entry_abs": max(abs(value) for row in matrix for value in row),
                    "exact_slope_polystability": {
                        "scope": "exact CICY 7484 positive-kappa plane search",
                        **kahler,
                        "line_bundle_summands_stable": True,
                        "all_summand_slopes_zero_on_exact_interior_ray": True,
                        "direct_sum_polystable_for_charge_matrix": True,
                    },
                    **cohomology,
                    "raw_symmetry_diagnostic": equivariance,
                    "novelty": novelty_for_matrix(matrix, cicy["Conf"], novelty_context),
                }
            )
            if progress:
                pair = actual_wedge2.get("per_character_pair")
                print(
                    f"record={len(records)} kappa={kappa} "
                    f"5bar/5={spectrum['upstairs_5bar']}/{spectrum['upstairs_5']} "
                    f"actual_pair={pair}",
                    flush=True,
                )
        if plane_algebraic:
            plane_summaries.append(
                {
                    "kappa_vector": kappa,
                    "candidate_column_count": len(columns),
                    "zero_sum_multiset_count": len(zero_sum_indices),
                    "algebraic_survivor_count": plane_algebraic,
                    "spectrum_and_lift_count": plane_spectrum,
                }
            )
            if progress:
                print(
                    f"summary kappa={kappa} columns={len(columns)} "
                    f"zero_sum={len(zero_sum_indices)} algebraic={plane_algebraic} "
                    f"spectrum_lift={plane_spectrum}",
                    flush=True,
                )

    def actual_pair(record: dict) -> list[int] | None:
        certificate = record["conditional_order4_descent_constraints"][
            "actual_z2xz2_wedge2_character_certificate"
        ]
        return certificate.get("per_character_pair") or certificate.get(
            "best_per_character_pair"
        )

    records.sort(
        key=lambda record: (
            actual_pair(record)[1] if actual_pair(record) is not None else 99,
            record["su5_upstairs_spectrum"]["upstairs_5"],
            record["max_entry_abs"],
        )
    )
    actual_character_records = [
        record
        for record in records
        if record["conditional_order4_descent_constraints"][
            "actual_z2xz2_wedge2_character_certificate"
        ]["character_computed"]
    ]
    return {
        "search": {
            "cicy": 7484,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "entry_bound": bound,
            "kappa_max": kappa_max,
            "selected_kappas": selected_kappas,
            "skip_kappa_max": skip_kappa_max,
            "min_column_count": min_column_count,
            "max_column_count": max_column_count,
            "max_planes": max_planes,
            "require_even_total_degree": True,
            "allow_zero_column": allow_zero_column,
            "ansatz": "primitive positive kappa planes with even-total columns",
            "candidate_kappa_plane_count": candidate_plane_count,
            "unique_zero_sum_multiset_count": len(seen_keys),
            "total_zero_sum_multiset_count": total_zero_sum_multisets,
            "algebraic_survivor_count": algebraic_survivor_count,
            "spectrum_lift_count": len(records),
            "actual_character_count": len(actual_character_records),
            "best_actual_pair": actual_pair(records[0]) if records else None,
            "plane_summaries": plane_summaries,
        },
        "best_candidate": records[0] if records else None,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bound", type=int, default=6)
    parser.add_argument("--kappa-max", type=int, default=30)
    parser.add_argument(
        "--kappa",
        action="append",
        default=None,
        help="Restrict to one primitive positive kappa vector, formatted as p,q,r. May be repeated.",
    )
    parser.add_argument(
        "--skip-kappa-max",
        type=int,
        default=None,
        help="Skip kappa vectors with max(p,q,r) less than or equal to this value.",
    )
    parser.add_argument("--min-column-count", type=int, default=5)
    parser.add_argument("--max-column-count", type=int, default=None)
    parser.add_argument("--max-planes", type=int, default=None)
    parser.add_argument(
        "--allow-zero-column",
        action="store_true",
        help="Include O_X as an allowed line-bundle summand in each kappa plane.",
    )
    parser.add_argument("--progress", action="store_true")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy7484_kappa_plane_search_bound6_kmax30.json"),
    )
    args = parser.parse_args()

    selected_kappas = None
    if args.kappa:
        selected_kappas = []
        for raw in args.kappa:
            parts = [int(part.strip()) for part in raw.split(",")]
            if len(parts) != 3 or any(part <= 0 for part in parts):
                raise ValueError(
                    f"invalid --kappa value {raw!r}; "
                    "expected p,q,r with positive integers"
                )
            common = gcd(gcd(parts[0], parts[1]), parts[2])
            selected_kappas.append([part // common for part in parts])

    result = verify(
        args.bound,
        args.kappa_max,
        progress=args.progress,
        selected_kappas=selected_kappas,
        skip_kappa_max=args.skip_kappa_max,
        min_column_count=args.min_column_count,
        max_column_count=args.max_column_count,
        max_planes=args.max_planes,
        allow_zero_column=args.allow_zero_column,
    )
    out = Path(args.json_out)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"candidate_kappa_plane_count={result['search']['candidate_kappa_plane_count']}")
    print(f"unique_zero_sum_multiset_count={result['search']['unique_zero_sum_multiset_count']}")
    print(f"algebraic_survivor_count={result['search']['algebraic_survivor_count']}")
    print(f"spectrum_lift_count={result['search']['spectrum_lift_count']}")
    print(f"actual_character_count={result['search']['actual_character_count']}")
    print(f"best_actual_pair={result['search']['best_actual_pair']}")
    if result["best_candidate"]:
        best = result["best_candidate"]
        spectrum = best["su5_upstairs_spectrum"]
        print(f"best_kappa={best['kappa_vector']}")
        print(f"best_matrix={best['matrix']}")
        print(f"best_spectrum={spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}")
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
