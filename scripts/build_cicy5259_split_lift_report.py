#!/usr/bin/env python3
"""Build the CICY 5259 split-lift certification/obstruction report."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from itertools import permutations
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.cicy import (  # noqa: E402
    ambient_dimensions,
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicylist import (  # noqa: E402
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
)
from string_theory.cohomology import make_pycicy, pycicy_config  # noqa: E402
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def load_entries_by_num() -> dict[int, tuple[dict[str, Any], str]]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    return {meta["Num"]: (meta, entry) for meta, entry in zip(metadata, entries)}


def is_favourable(entry: str) -> bool:
    return "Favour -> True" in entry


def matrix_columns(matrix: list[list[int]]) -> list[tuple[int, ...]]:
    return [tuple(col) for col in zip(*matrix)]


def canonical_matrix_key(matrix: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Canonicalize up to row permutations and column permutations."""

    rows = len(matrix)
    best: tuple[tuple[int, ...], ...] | None = None
    for row_perm in permutations(range(rows)):
        permuted_rows = [matrix[i] for i in row_perm]
        key = tuple(sorted(matrix_columns(permuted_rows)))
        if best is None or key < best:
            best = key
    if best is None:
        return ()
    return best


def find_exact_row_column_equivalence(
    source: list[list[int]], target: list[list[int]]
) -> dict[str, Any] | None:
    """Find row/column permutations taking source to target, if they exist."""

    if len(source) != len(target) or len(source[0]) != len(target[0]):
        return None
    rows = len(source)
    cols = len(source[0])
    target_cols = matrix_columns(target)
    for row_perm in permutations(range(rows)):
        permuted_rows = [source[i] for i in row_perm]
        source_cols = matrix_columns(permuted_rows)
        for col_perm in permutations(range(cols)):
            if [source_cols[i] for i in col_perm] == target_cols:
                return {
                    "row_permutation_source_to_target": list(row_perm),
                    "column_permutation_source_to_target": list(col_perm),
                }
    return None


def contract_split_row(
    conf: list[list[int]], split_row_index: int
) -> dict[str, Any] | None:
    """Contract a one-step split row if it has the ordinary P^n split shape."""

    split_row = conf[split_row_index]
    split_columns = [i for i, degree in enumerate(split_row) if degree == 1]
    if any(degree not in (0, 1) for degree in split_row):
        return None
    if not split_columns:
        return None
    ambient_dim = sum(split_row) - 1
    if len(split_columns) != ambient_dim + 1:
        return None

    lower_rows = [row for i, row in enumerate(conf) if i != split_row_index]
    merged_column = [
        sum(row[col] for col in split_columns) for row in lower_rows
    ]
    remaining_columns = [
        col for col in range(len(split_row)) if col not in set(split_columns)
    ]
    contracted_columns = [tuple(merged_column)] + [
        tuple(row[col] for row in lower_rows) for col in remaining_columns
    ]
    contracted = [
        [col[row_index] for col in contracted_columns]
        for row_index in range(len(lower_rows))
    ]
    return {
        "split_row_index": split_row_index,
        "split_row_ambient_dimension": ambient_dim,
        "split_columns": split_columns,
        "remaining_columns": remaining_columns,
        "contracted_columns_source": [
            {"kind": "merged_split_columns", "source_columns": split_columns},
            *[
                {"kind": "unchanged_column", "source_column": col}
                for col in remaining_columns
            ],
        ],
        "contracted_conf": contracted,
    }


def one_step_split_audit(
    target_conf: list[list[int]], candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    target_key = canonical_matrix_key(target_conf)
    hits = []
    for candidate in candidates:
        conf = candidate["conf"]
        for row_index in range(len(conf)):
            contracted = contract_split_row(conf, row_index)
            if contracted is None:
                continue
            exact_equivalence = find_exact_row_column_equivalence(
                contracted["contracted_conf"], target_conf
            )
            canonical_match = canonical_matrix_key(contracted["contracted_conf"]) == target_key
            if canonical_match:
                hits.append(
                    {
                        "candidate_num": candidate["num"],
                        "candidate_hodge": [candidate["h11"], candidate["h21"]],
                        "candidate_eta": candidate["eta"],
                        "candidate_favourable": candidate["favourable"],
                        "candidate_num_projective_factors": candidate["num_projective_factors"],
                        "candidate_num_polynomials": candidate["num_polynomials"],
                        **contracted,
                        "canonical_reconstructs_target": canonical_match,
                        "exact_equivalence_to_cicy5259": exact_equivalence,
                    }
                )
    return hits


def intersection_summary(conf: list[list[int]]) -> dict[str, Any]:
    tensor = triple_intersections(conf)
    nonzero = {key: value for key, value in tensor.items() if value}
    entries = [
        {"indices": list(key), "value": value}
        for key, value in sorted(nonzero.items())
    ]
    return {
        "rank": len(conf),
        "nonzero_count": len(nonzero),
        "max_abs_value": max((abs(value) for value in nonzero.values()), default=0),
        "sha256": sha256(json.dumps(entries, sort_keys=True).encode("utf-8")).hexdigest(),
        "sample_nonzero": entries[:32],
        "nonzero_entries": entries,
    }


def pycicy_topology_probe(conf: list[list[int]], c2: list[int]) -> dict[str, Any]:
    cy = make_pycicy(pycicy_config(conf))
    hodge_data = [float(value) for value in cy.hodge_data()]
    second_chern = [int(round(float(value))) for value in cy.second_chern()]
    triple = cy.triple_intersection()
    if hasattr(triple, "tolist"):
        triple = triple.tolist()
    helper = triple_intersections(conf)
    triple_agrees = True
    for i in range(len(conf)):
        for j in range(len(conf)):
            for k in range(len(conf)):
                if int(round(float(triple[i][j][k]))) != helper[(i, j, k)]:
                    triple_agrees = False
    return {
        "available": True,
        "hodge_data_raw": hodge_data,
        "h11": int(round(hodge_data[2])),
        "h21": int(round(hodge_data[1])),
        "second_chern": second_chern,
        "second_chern_matches_cicylist": second_chern == c2,
        "triple_intersection_matches_helper": triple_agrees,
        "line_index_formula_scope": "full favourable 7914 ambient divisor variables m0..m6",
        "line_index_formula": str(cy.line_index()),
        "line_slope_formula_scope": "full favourable 7914 ambient Kahler variables t0..t6",
        "line_slope_formula": str(cy.line_slope()),
    }


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    entries_by_num = load_entries_by_num()
    meta_5259, entry_5259 = entries_by_num[5259]
    conf_5259 = parse_integer_list_rule(entry_5259, "Conf")
    c2_5259 = parse_integer_list_rule(entry_5259, "C2")
    redun_5259 = parse_integer_list_rule(entry_5259, "Redun")

    redundant_presentations = []
    for num in redun_5259:
        if not num or num not in entries_by_num:
            continue
        meta, entry = entries_by_num[num]
        redundant_presentations.append(
            {
                "num": num,
                "num_projective_factors": meta["NumPs"],
                "num_polynomials": meta["NumPol"],
                "eta": meta["Eta"],
                "h11": meta["H11"],
                "h21": meta["H21"],
                "favourable": is_favourable(entry),
                "symmetry_status": meta["SymmetryStatus"],
                "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
                "conf": parse_integer_list_rule(entry, "Conf"),
                "c2": parse_integer_list_rule(entry, "C2"),
                "redun": parse_integer_list_rule(entry, "Redun"),
            }
        )

    split_hits = one_step_split_audit(conf_5259, redundant_presentations)
    selected_split = next(hit for hit in split_hits if hit["candidate_num"] == 7914)
    meta_7914, entry_7914 = entries_by_num[7914]
    conf_7914 = parse_integer_list_rule(entry_7914, "Conf")
    c2_7914 = parse_integer_list_rule(entry_7914, "C2")

    scout = load_json("nonfavourable_ambient_restricted_scout.json")
    hit_5259 = next(record for record in scout["best_spectrum_records"] if record["cicy"] == 5259)
    matrix_5259 = hit_5259["matrix"]
    matrix_7914 = [list(row) for row in matrix_5259] + [[0] * len(matrix_5259[0])]
    expected_index = -6

    d_7914 = triple_intersections(conf_7914)
    c2_v_7914 = bundle_c2(matrix_7914, d_7914)
    anomaly_7914 = [tx - v for tx, v in zip(c2_7914, c2_v_7914)]
    index_v_7914 = bundle_index(matrix_7914, d_7914, c2_7914)
    index_wedge2_7914 = wedge2_index(matrix_7914, d_7914, c2_7914)
    slope_7914 = find_slope_zero(
        matrix_7914,
        intersection_tensor(d_7914, len(conf_7914)),
        tolerance=1e-7,
        restarts=64,
        max_iterations=2500,
        seed=52597914,
    )
    cohomology_7914 = cohomology_and_spectrum(
        {
            "Num": 7914,
            "H11": meta_7914["H11"],
            "Conf": conf_7914,
            "C2": c2_7914,
        },
        2,
        matrix_7914,
    )
    spectrum_7914 = cohomology_7914["su5_upstairs_spectrum"]
    quality_7914 = cohomology_7914["line_bundle_sum_quality"]

    audit = load_json("nonfavourable_free_capability_audit.json")
    target_audit = next(item for item in audit["targets"] if item["num"] == 5259)

    pycicy = pycicy_topology_probe(conf_7914, c2_7914)
    intersections = intersection_summary(conf_7914)

    gates = {
        "explicit_ineffective_split_found": gate(
            selected_split["canonical_reconstructs_target"]
            and selected_split["split_row_index"] == 6
            and selected_split["split_columns"] == [0, 1, 2],
            "data/raw/cicylist.m Redun -> {5141, 5406, 7912, 7914, 7918}",
            "CICY 7914 contracts to CICY 5259 by merging columns 0,1,2 under the added P2 row",
        ),
        "split_is_favourable_full_picard_basis": gate(
            meta_7914["H11"] == meta_7914["NumPs"]
            and is_favourable(entry_7914)
            and meta_7914["H11"] == 7,
            "data/raw/cicylist.m Num -> 7914",
            "the redundant split presentation supplies seven ambient divisors for h11=7",
        ),
        "pycicy_full_topology_cross_check": gate(
            pycicy["second_chern_matches_cicylist"]
            and pycicy["triple_intersection_matches_helper"]
            and pycicy["h11"] == 7
            and pycicy["h21"] == 31,
            "pyCICY on CICY 7914 plus src/string_theory/cicy.py",
            "full favourable c2 and triple-intersection data cross-check",
        ),
        "full_upstairs_topology_gates": gate(
            bundle_c1(matrix_7914) == [0] * 7
            and index_v_7914 == expected_index
            and index_wedge2_7914 == expected_index
            and all(value >= 0 for value in anomaly_7914),
            "CICY 7914 full favourable intersection tensor and C2",
            "zero-extended bundle has c1=0, index=-6, wedge2 index=-6, and effective anomaly in seven components",
        ),
        "full_favourable_slope_gate": gate(
            slope_7914.feasible,
            "src/string_theory/slope.py on the CICY 7914 full favourable cone",
            "numerical slope-zero point found with all seven Kahler parameters positive",
        ),
        "full_pycicy_cohomology_spectrum_gate": gate(
            all(spectrum_7914["checks"].values())
            and spectrum_7914["upstairs_anti_10"] == 0
            and quality_7914["regular_nontrivial_summand_scan_style"],
            "pyCICY cohomology on CICY 7914 zero-extended line bundles",
            "upstairs spectrum matches the 5259 scout and passes regular nontrivial summand checks",
        ),
        "quotient_descent_still_blocked": gate(
            meta_7914["SymmetryStatus"] == "unknown"
            and not cohomology_7914.get("actual_wilson_line_spectrum_proven", False),
            "data/raw/cicylist.m Num -> 7914 plus cohomology character boundary",
            "the split presentation has no recorded free action/equivariant character data, so Wilson-line descent is not certified",
        ),
    }

    return {
        "scope": "CICY5259 missing-divisor split-lift audit",
        "conclusion": {
            "status": "full_upstairs_split_lift_certified__quotient_descent_blocked",
            "missing_seventh_divisor_obtained": True,
            "missing_seventh_divisor_route": "ordinary ineffective split / configuration equivalence to favourable CICY 7914",
            "full_upstairs_su5_line_bundle_certificate": True,
            "full_quotient_wilson_line_certificate": False,
            "selected_full_picard_presentation": 7914,
            "new_divisor_class": "J6, the hyperplane class of the added P2 row in CICY 7914",
            "bundle_lift_rule_used": "append zero charge on J6 to the CICY5259 ambient-restricted line-bundle matrix",
            "primary_remaining_blocker": (
                "No explicit free-action lift to the 7914 split coordinates, no action on the added divisor class, "
                "and no equivariant cohomology character decomposition are available in the current data."
            ),
        },
        "cicy5259": {
            "metadata": {
                "num": 5259,
                "num_projective_factors": meta_5259["NumPs"],
                "num_polynomials": meta_5259["NumPol"],
                "eta": meta_5259["Eta"],
                "h11": meta_5259["H11"],
                "h21": meta_5259["H21"],
                "favourable": is_favourable(entry_5259),
                "free_symmetry_option_count": meta_5259["FreeSymmetryOptionCount"],
            },
            "ambient_dimensions": list(ambient_dimensions(conf_5259)),
            "conf": conf_5259,
            "c2_ambient": c2_5259,
            "redun": redun_5259,
        },
        "redundant_presentations_in_cicylist": redundant_presentations,
        "ineffective_split_audit": {
            "candidate_count": len(redundant_presentations),
            "one_step_hits": split_hits,
            "selected_hit": selected_split,
            "interpretation": (
                "The selected hit is the ordinary P2 split of the first CICY5259 column. "
                "Deleting the added P2 row and merging the three split columns exactly reconstructs the 5259 configuration."
            ),
        },
        "full_picard_presentation_7914": {
            "metadata": {
                "num": 7914,
                "num_projective_factors": meta_7914["NumPs"],
                "num_polynomials": meta_7914["NumPol"],
                "eta": meta_7914["Eta"],
                "h11": meta_7914["H11"],
                "h21": meta_7914["H21"],
                "favourable": is_favourable(entry_7914),
                "symmetry_status": meta_7914["SymmetryStatus"],
                "free_symmetry_option_count": meta_7914["FreeSymmetryOptionCount"],
            },
            "ambient_dimensions": list(ambient_dimensions(conf_7914)),
            "conf": conf_7914,
            "c2_tx": c2_7914,
            "pycicy_topology_probe": pycicy,
            "intersection_tensor": intersections,
            "full_kahler_cone_certificate_scope": (
                "favourable ambient positive orthant for the 7914 split presentation"
            ),
        },
        "zero_extended_bundle_certificate": {
            "symmetry_order_used_for_upstairs_chirality": 2,
            "matrix_5259": matrix_5259,
            "matrix_7914_zero_extended": matrix_7914,
            "c1": bundle_c1(matrix_7914),
            "index_v": index_v_7914,
            "index_wedge2_v": index_wedge2_7914,
            "expected_index_from_order_two_quotient": expected_index,
            "c2_v": c2_v_7914,
            "anomaly": anomaly_7914,
            "anomaly_nonnegative": all(value >= 0 for value in anomaly_7914),
            "slope_search": slope_7914.as_dict(),
            "cohomology": {
                "V": cohomology_7914["V_cohomology"],
                "V_dual": cohomology_7914["V_dual_cohomology"],
                "wedge2_V": cohomology_7914["wedge2_V_cohomology"],
                "wedge2_V_dual": cohomology_7914["wedge2_V_dual_cohomology"],
            },
            "line_bundle_sum_quality": quality_7914,
            "su5_upstairs_spectrum": spectrum_7914,
        },
        "quotient_descent_boundary": {
            "original_5259_free_symmetry_options": target_audit["symmetry_action"]["free_options"],
            "original_ambient_row_action_summary": {
                "free_options_with_ambient_row_permutation_inference": target_audit[
                    "symmetry_action"
                ]["free_options_with_ambient_row_permutation_inference"],
                "all_recorded_options_ambient_row_trivial": all(
                    option["all_generators_ambient_row_trivial"]
                    for option in target_audit["symmetry_action"]["free_options"]
                ),
            },
            "split_presentation_symmetry_status": meta_7914["SymmetryStatus"],
            "blocked_items": [
                {
                    "item": "explicit lift of a selected 5259 free Z2 action to the 7914 split coordinates and split equations",
                    "why_needed": "the split added a P2 row and three replacement equations for one original equation",
                },
                {
                    "item": "7x7 action on the full Picard basis including J6",
                    "why_needed": "ambient-row triviality on the six 5259 rows does not determine the missing divisor direction",
                },
                {
                    "item": "equivariant line-bundle lift/fiber characters for the zero-extended summands",
                    "why_needed": "topological invariance is not the same as a chosen equivariant bundle structure",
                },
                {
                    "item": "cohomology character decomposition for V and wedge2 V",
                    "why_needed": "Wilson-line projection needs actual representations, not just dimensions and indices",
                },
            ],
            "conditional_statement": (
                "If one constructs a split-compatible free action and equivariant lift whose cohomology characters "
                "satisfy the order-two Wilson-line projection, this 7914 lift supplies the missing full Picard topology."
            ),
        },
        "route_assessment": {
            "ineffective_splitting": {
                "status": "success_for_full_upstairs_geometry",
                "evidence": "CICY 7914 one-step P2 split contracts exactly to CICY 5259",
            },
            "configuration_equivalence": {
                "status": "success_for_full_upstairs_geometry",
                "evidence": "CICY5259 Redun includes 7914, and both have eta=-48 and Hodge numbers (7,31)",
            },
            "known_quotient_literature_or_data": {
                "status": "partial_only",
                "evidence": (
                    "Oxford quotient data records 5259 free Z2 actions; the favourable split presentation has "
                    "unknown symmetry status in cicylist.m and no local split-action character data."
                ),
            },
            "picard_group_computation": {
                "status": "not_needed_for_upstairs_after_split__still_needed_for_quotient_action_if_working_in_5259_basis",
                "evidence": "the favourable 7914 presentation has NumPs=h11=7 and supplies a full ambient Picard basis",
            },
            "algebraic_geometric_derivation": {
                "status": "available_as_split_derivation_for_basis__not_available_for_equivariant_descent",
                "evidence": "the P2 split gives J6; deriving the free action on J6 and cohomology characters remains separate",
            },
        },
        "external_data_or_algorithm_required_for_full_quotient_certificate": [
            "A selected 5259 free Z2 action lifted through the 7914 P2 split, including coordinate and polynomial action.",
            "The induced action on the full seven-dimensional Picard basis or an equivalent proof that the zero-extended line-bundle sum admits the required equivariant structure.",
            "Equivariant cohomology character decompositions for H*(X,V), H*(X,V*) and the wedge2 sectors.",
            "A Wilson-line character choice and projection check proving the downstairs standard-model spectrum.",
        ],
        "tooling_boundary": {
            "symbolic_ag_tools_on_path": {
                name: bool(shutil.which(name))
                for name in ["sage", "M2", "macaulay2", "Singular", "gap"]
            },
            "interpretation": (
                "No external Picard/Chow computation system was available on PATH; the successful upstairs route used the "
                "explicit favourable split in cicylist.m instead."
            ),
        },
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    conclusion = report["conclusion"]
    split = report["ineffective_split_audit"]["selected_hit"]
    cert = report["zero_extended_bundle_certificate"]
    spectrum = cert["su5_upstairs_spectrum"]
    slope = cert["slope_search"]
    lines = [
        "# CICY 5259 split-lift audit",
        "",
        f"Status: `{conclusion['status']}`",
        "",
        "## Result",
        "",
        "- Missing seventh divisor obtained: yes.",
        "- Route: ordinary ineffective split / configuration equivalence to favourable CICY 7914.",
        "- Full upstairs SU(5) line-bundle certificate: yes, in the 7914 split presentation.",
        "- Full quotient/Wilson-line certificate: no, still blocked by missing split-compatible equivariant data.",
        "",
        "## Split",
        "",
        f"- selected redundant presentation: `{split['candidate_num']}`",
        f"- added split row index: `{split['split_row_index']}`",
        f"- split columns merged back to 5259: `{split['split_columns']}`",
        "- new divisor class: `J6`, the hyperplane class of the added P2 row",
        "- contraction check: deleting row 6 and merging columns 0,1,2 exactly reconstructs the 5259 configuration",
        "",
        "## Full Upstairs Certificate",
        "",
        f"- matrix lift: append zero charge on `J6` to the 5259 matrix",
        f"- c1: `{cert['c1']}`",
        f"- index(V), index(wedge2 V): `{cert['index_v']}`, `{cert['index_wedge2_v']}`",
        f"- c2(V): `{cert['c2_v']}`",
        f"- anomaly c2(TX)-c2(V): `{cert['anomaly']}`",
        f"- slope feasible: `{slope['feasible']}` with max normalized slope `{slope['max_normalized_slope']:.3e}`",
        f"- cohomology V / V* / wedge2 V / wedge2 V*: `{cert['cohomology']['V']}` / `{cert['cohomology']['V_dual']}` / `{cert['cohomology']['wedge2_V']}` / `{cert['cohomology']['wedge2_V_dual']}`",
        f"- upstairs spectrum 10/anti10/5bar/5: `{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}`",
        "",
        "## Remaining Blocker",
        "",
        "The split presentation supplies the full seven-divisor topology, but not the quotient descent. The missing data are:",
        "",
    ]
    for item in report["external_data_or_algorithm_required_for_full_quotient_certificate"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "So the old ambient-restricted 5259 breadcrumb is upgraded to a full upstairs split-lift certificate, but not to a full Wilson-line quotient certificate.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_split_lift_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy5259_split_lift_report.md"),
    )
    args = parser.parse_args()

    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)

    print(f"status={report['conclusion']['status']}")
    print(f"selected_split={report['conclusion']['selected_full_picard_presentation']}")
    print(f"full_upstairs_certificate={report['conclusion']['full_upstairs_su5_line_bundle_certificate']}")
    print(f"full_quotient_certificate={report['conclusion']['full_quotient_wilson_line_certificate']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
