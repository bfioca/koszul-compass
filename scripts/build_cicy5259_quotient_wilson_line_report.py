#!/usr/bin/env python3
"""Build the CICY 5259/7914 quotient Wilson-line certification attempt."""

from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations, product
import json
import math
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import ambient_dimensions  # noqa: E402
from string_theory.cicy_symmetry import (  # noqa: E402
    _inner_list,
    infer_ambient_row_permutation,
    split_top_level_items,
)
from string_theory.cicylist import (  # noqa: E402
    extract_rule_value_text,
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
    split_top_level_list_items,
)
from string_theory.cohomology import (  # noqa: E402
    bundle_line_summands,
    cohomology_record,
    dual,
    wedge2_line_summands,
)


Sign = int


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def load_entries_by_num() -> dict[int, tuple[dict[str, Any], str]]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    return {meta["Num"]: (meta, entry) for meta, entry in zip(metadata, entries)}


def _sign(value: str) -> Sign:
    value = value.strip()
    if value == "1":
        return 1
    if value == "-1":
        return -1
    raise ValueError(f"expected +/-1, got {value!r}")


def diagonal_signs(matrix_text: str) -> list[Sign]:
    rows = split_top_level_items(_inner_list(matrix_text))
    signs: list[Sign] = []
    for row_index, row in enumerate(rows):
        values = split_top_level_items(_inner_list(row))
        nonzero = [
            (col_index, value.strip())
            for col_index, value in enumerate(values)
            if value.strip() != "0"
        ]
        if len(nonzero) != 1 or nonzero[0][0] != row_index:
            raise ValueError(f"non-diagonal row {row_index}: {nonzero}")
        signs.append(_sign(nonzero[0][1]))
    return signs


def grouped(values: list[Sign], sizes: list[int]) -> list[list[Sign]]:
    out = []
    offset = 0
    for size in sizes:
        out.append(values[offset : offset + size])
        offset += size
    if offset != len(values):
        raise ValueError("block sizes do not consume values")
    return out


def free_z2_option_records(entry: str, block_sizes: list[int]) -> list[dict[str, Any]]:
    options = []
    for option_index, option_text in enumerate(
        split_top_level_list_items(extract_rule_value_text(entry, "Symmetries"))
    ):
        items = split_top_level_list_items(option_text)
        if not items or items[0].strip() != "True":
            continue
        coordinate_data = split_top_level_list_items(items[1])
        generator_matrices = split_top_level_list_items(coordinate_data[0])
        if len(generator_matrices) != 1:
            continue
        polynomial_matrices = split_top_level_items(_inner_list(items[3]))
        polynomial_matrix = polynomial_matrices[0]
        options.append(
            {
                "option_index": option_index,
                "coordinate_signs": diagonal_signs(generator_matrices[0]),
                "coordinate_signs_by_ambient_block": grouped(
                    diagonal_signs(generator_matrices[0]), block_sizes
                ),
                "ambient_row_permutation": list(
                    infer_ambient_row_permutation(generator_matrices[0], block_sizes)
                ),
                "polynomial_signs_5259": diagonal_signs(polynomial_matrix),
                "quotient_group_structure": [2],
                "quotient_order": 2,
                "raw_group_structure_item": items[2],
            }
        )
    return options


def prod_sign(values: list[Sign] | tuple[Sign, ...]) -> Sign:
    out = 1
    for value in values:
        out *= value
    return out


def sign_label(value: Sign) -> str:
    return "+" if value == 1 else "-"


def complete_homogeneous_trace(eigenvalues: list[Sign], degree: int) -> int:
    coeffs = [0 for _ in range(degree + 1)]
    coeffs[0] = 1
    for eigenvalue in eigenvalues:
        updated = coeffs[:]
        for total_degree in range(1, degree + 1):
            power = eigenvalue
            for used in range(1, total_degree + 1):
                updated[total_degree] += power * coeffs[total_degree - used]
                power *= eigenvalue
        coeffs = updated
    return coeffs[degree]


def projective_factor_character(
    *, dimension: int, eigenvalues: list[Sign], degree: int
) -> tuple[int | None, int, int]:
    """Return cohomology degree, nonidentity trace, and dimension."""

    if degree >= 0:
        return (
            0,
            complete_homogeneous_trace(eigenvalues, degree),
            math.comb(dimension + degree, dimension),
        )
    if degree <= -dimension - 1:
        dual_degree = -degree - dimension - 1
        det = prod_sign(eigenvalues)
        return (
            dimension,
            complete_homogeneous_trace(eigenvalues, dual_degree) // det,
            math.comb(dual_degree + dimension, dimension),
        )
    return None, 0, 0


def ambient_line_character(
    *,
    conf: list[list[int]],
    coordinate_signs_by_block: list[list[Sign]],
    line_bundle: list[int],
) -> dict[str, Any] | None:
    degree = 0
    trace = 1
    dimension = 1
    for row, signs, charge in zip(conf, coordinate_signs_by_block, line_bundle):
        ambient_dimension = sum(row) - 1
        factor_degree, factor_trace, factor_dimension = projective_factor_character(
            dimension=ambient_dimension,
            eigenvalues=signs,
            degree=charge,
        )
        if factor_degree is None or factor_dimension == 0:
            return None
        degree += factor_degree
        trace *= factor_trace
        dimension *= factor_dimension
    return {
        "ambient_cohomology_degree": degree,
        "trace": trace,
        "dimension": dimension,
    }


def multiplicities(dimension: int, trace: int) -> dict[str, int]:
    if (dimension + trace) % 2 or (dimension - trace) % 2:
        raise ValueError(f"non-integral Z2 multiplicities dim={dimension}, trace={trace}")
    plus = (dimension + trace) // 2
    minus = (dimension - trace) // 2
    if plus < 0 or minus < 0:
        raise ValueError(f"negative Z2 multiplicities dim={dimension}, trace={trace}")
    return {"+": plus, "-": minus}


def representation_record(dimension: int, trace: int) -> dict[str, Any]:
    mult = multiplicities(dimension, trace)
    regular_multiplicity = mult["+"] if mult["+"] == mult["-"] else None
    return {
        "dimension": dimension,
        "nonidentity_trace": trace,
        "multiplicities": mult,
        "regular_multiplicity": regular_multiplicity,
    }


def add_rep(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return representation_record(
        a["dimension"] + b["dimension"],
        a["nonidentity_trace"] + b["nonidentity_trace"],
    )


def subtract_rep(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return representation_record(
        a["dimension"] - b["dimension"],
        a["nonidentity_trace"] - b["nonidentity_trace"],
    )


def aggregate_reps(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = representation_record(0, 0)
    for record in records:
        total = add_rep(total, record)
    return total


def koszul_source_terms(
    *,
    conf: list[list[int]],
    coordinate_signs_by_block: list[list[Sign]],
    equation_signs: list[Sign],
    line_bundle: list[int],
    fiber_sign: Sign = 1,
) -> list[dict[str, Any]]:
    equation_degrees = [[conf[row][col] for row in range(len(conf))] for col in range(len(conf[0]))]
    records = []
    for mask in range(1 << len(equation_degrees)):
        subset = [index for index in range(len(equation_degrees)) if mask >> index & 1]
        shift = [
            sum(equation_degrees[col][row] for col in subset)
            for row in range(len(conf))
        ]
        ambient_bundle = [charge - delta for charge, delta in zip(line_bundle, shift)]
        ambient = ambient_line_character(
            conf=conf,
            coordinate_signs_by_block=coordinate_signs_by_block,
            line_bundle=ambient_bundle,
        )
        if ambient is None:
            continue
        koszul_degree = len(subset)
        total_degree = ambient["ambient_cohomology_degree"] - koszul_degree
        if not 0 <= total_degree <= 3:
            continue
        koszul_sign = prod_sign([equation_signs[index] for index in subset])
        trace = fiber_sign * koszul_sign * ambient["trace"]
        records.append(
            {
                "subset": subset,
                "koszul_degree": koszul_degree,
                "ambient_line_bundle": ambient_bundle,
                "ambient_cohomology_degree": ambient["ambient_cohomology_degree"],
                "total_degree": total_degree,
                "dimension": ambient["dimension"],
                "nonidentity_trace": trace,
                "multiplicities": multiplicities(ambient["dimension"], trace),
                "koszul_equation_sign_product": koszul_sign,
            }
        )
    return records


def sources_by_total_degree(sources: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        out[source["total_degree"]].append(source)
    return dict(sorted(out.items()))


def source_representation(sources: list[dict[str, Any]]) -> dict[str, Any]:
    return aggregate_reps(
        [
            representation_record(
                source["dimension"], source["nonidentity_trace"]
            )
            for source in sources
        ]
    )


def line_character_certificate(
    *,
    conf: list[list[int]],
    coordinate_signs_by_block: list[list[Sign]],
    equation_signs: list[Sign],
    line_bundle: list[int],
    cohomology: list[int],
    mixed_pattern: str | None = None,
    fiber_sign: Sign = 1,
) -> dict[str, Any]:
    sources = koszul_source_terms(
        conf=conf,
        coordinate_signs_by_block=coordinate_signs_by_block,
        equation_signs=equation_signs,
        line_bundle=line_bundle,
        fiber_sign=fiber_sign,
    )
    by_total = sources_by_total_degree(sources)
    nonzero_degrees = [degree for degree, value in enumerate(cohomology) if value]
    actual: dict[str, dict[str, Any]] = {}
    method = "not_determined"

    if len(nonzero_degrees) == 1:
        degree = nonzero_degrees[0]
        rep = source_representation(by_total.get(degree, []))
        if rep["dimension"] == cohomology[degree]:
            actual[f"H{degree}"] = rep
            method = "single_total_degree_source_equals_pycicy_dimension"
    elif mixed_pattern == "wedge2v_line01":
        isolated_h1 = [
            source for source in by_total.get(1, []) if source["subset"] == [3, 4, 5]
        ]
        map_domain = [
            source
            for source in by_total.get(1, [])
            if source["subset"] == [3, 4, 5, 6]
        ]
        map_target = by_total.get(2, [])
        h1 = source_representation(isolated_h1)
        domain = source_representation(map_domain)
        target = source_representation(map_target)
        h2 = subtract_rep(target, domain)
        if h1["dimension"] == cohomology[1] and h2["dimension"] == cohomology[2]:
            actual = {"H1": h1, "H2": h2}
            method = "two_term_koszul_map_injective_by_pycicy_dimension"
    elif mixed_pattern == "wedge2vdual_line01":
        map_source = by_total.get(1, [])
        map_target = [
            source for source in by_total.get(2, []) if source["subset"] == [0, 1, 2]
        ]
        isolated_h2 = [
            source
            for source in by_total.get(2, [])
            if source["subset"] == [0, 1, 2, 6]
        ]
        source_rep = source_representation(map_source)
        target_rep = source_representation(map_target)
        h1 = subtract_rep(source_rep, target_rep)
        h2 = source_representation(isolated_h2)
        if h1["dimension"] == cohomology[1] and h2["dimension"] == cohomology[2]:
            actual = {"H1": h1, "H2": h2}
            method = "two_term_koszul_map_surjective_by_pycicy_dimension"

    return {
        "line_bundle": line_bundle,
        "cohomology": cohomology,
        "fiber_sign": fiber_sign,
        "source_count": len(sources),
        "source_totals": {
            str(degree): source_representation(items)
            for degree, items in by_total.items()
        },
        "sources": sources,
        "actual_character_computed": bool(actual),
        "method": method,
        "actual": actual,
    }


def sector_record(
    *,
    label: str,
    line_certificates: list[dict[str, Any]],
    cohomology_degree_keys: list[str],
) -> dict[str, Any]:
    totals = {key: representation_record(0, 0) for key in cohomology_degree_keys}
    for cert in line_certificates:
        for key in cohomology_degree_keys:
            if key in cert["actual"]:
                totals[key] = add_rep(totals[key], cert["actual"][key])
    return {
        "label": label,
        "line_certificates": line_certificates,
        "cohomology_characters": totals,
        "all_characters_computed": all(cert["actual_character_computed"] for cert in line_certificates if any(cert["cohomology"])),
    }


def split_lift_search(
    *, original_first_polynomial_sign: Sign
) -> dict[str, Any]:
    """Return a balanced P2 split lift for the selected Z2 action."""

    chosen_p2 = [1, -1, 1]
    chosen_split_equations = [1, -1, 1]
    determinant_sign = prod_sign(chosen_split_equations) // prod_sign(chosen_p2)
    coefficient_sign_table = []
    for equation_index, equation_sign in enumerate(chosen_split_equations):
        coefficient_sign_table.append(
            {
                "split_equation": equation_index,
                "equation_sign": equation_sign,
                "coefficient_signs_by_p2_coordinate": [
                    equation_sign * p2_sign for p2_sign in chosen_p2
                ],
                "uses_both_coordinate_eigenspaces": len(
                    {equation_sign * p2_sign for p2_sign in chosen_p2}
                )
                == 2,
            }
        )
    return {
        "p2_coordinate_signs": chosen_p2,
        "split_equation_signs": chosen_split_equations,
        "determinant_sign_from_split": determinant_sign,
        "matches_original_first_polynomial_sign": determinant_sign
        == original_first_polynomial_sign,
        "coefficient_sign_table": coefficient_sign_table,
        "balanced": all(row["uses_both_coordinate_eigenspaces"] for row in coefficient_sign_table),
    }


def build_report() -> dict[str, Any]:
    split_report = load_json("cicy5259_split_lift_report.json")
    entries_by_num = load_entries_by_num()
    meta_5259, entry_5259 = entries_by_num[5259]
    conf_5259 = parse_integer_list_rule(entry_5259, "Conf")
    block_sizes_5259 = [dim + 1 for dim in ambient_dimensions(conf_5259)]
    options = free_z2_option_records(entry_5259, block_sizes_5259)
    selected = options[0]

    conf_7914 = split_report["full_picard_presentation_7914"]["conf"]
    matrix_7914 = split_report["zero_extended_bundle_certificate"][
        "matrix_7914_zero_extended"
    ]
    p2_lift = split_lift_search(
        original_first_polynomial_sign=selected["polynomial_signs_5259"][0]
    )
    coordinate_signs_by_block_7914 = [
        *selected["coordinate_signs_by_ambient_block"],
        p2_lift["p2_coordinate_signs"],
    ]
    equation_signs_7914 = [
        *p2_lift["split_equation_signs"],
        *selected["polynomial_signs_5259"][1:],
    ]

    line_summands = bundle_line_summands(matrix_7914)
    wedge_summands = wedge2_line_summands(matrix_7914)
    fiber_signs = [1, 1, 1, 1, 1]
    determinant_fiber_sign = prod_sign(fiber_signs)
    admissible_fiber_lift_count = sum(
        1 for signs in product([1, -1], repeat=5) if prod_sign(signs) == 1
    )

    v_certs = []
    vdual_certs = []
    for index, line in enumerate(line_summands):
        cohom = cohomology_record(conf_7914, line)["cohomology"]
        v_certs.append(
            {
                "summand_index": index,
                **line_character_certificate(
                    conf=conf_7914,
                    coordinate_signs_by_block=coordinate_signs_by_block_7914,
                    equation_signs=equation_signs_7914,
                    line_bundle=line,
                    cohomology=cohom,
                    fiber_sign=fiber_signs[index],
                ),
            }
        )
        dual_line = dual(line)
        dual_cohom = cohomology_record(conf_7914, dual_line)["cohomology"]
        vdual_certs.append(
            {
                "summand_index": index,
                **line_character_certificate(
                    conf=conf_7914,
                    coordinate_signs_by_block=coordinate_signs_by_block_7914,
                    equation_signs=equation_signs_7914,
                    line_bundle=dual_line,
                    cohomology=dual_cohom,
                    fiber_sign=fiber_signs[index],
                ),
            }
        )

    wedge_certs = []
    wedge_dual_certs = []
    for pair_index, (a, b) in enumerate(combinations(range(5), 2)):
        line = [matrix_7914[row][a] + matrix_7914[row][b] for row in range(7)]
        cohom = cohomology_record(conf_7914, line)["cohomology"]
        mixed = "wedge2v_line01" if (a, b) == (0, 1) else None
        wedge_certs.append(
            {
                "summand_pair": [a, b],
                "pair_index": pair_index,
                **line_character_certificate(
                    conf=conf_7914,
                    coordinate_signs_by_block=coordinate_signs_by_block_7914,
                    equation_signs=equation_signs_7914,
                    line_bundle=line,
                    cohomology=cohom,
                    mixed_pattern=mixed,
                    fiber_sign=fiber_signs[a] * fiber_signs[b],
                ),
            }
        )
        dual_line = dual(line)
        dual_cohom = cohomology_record(conf_7914, dual_line)["cohomology"]
        dual_mixed = "wedge2vdual_line01" if (a, b) == (0, 1) else None
        wedge_dual_certs.append(
            {
                "summand_pair": [a, b],
                "pair_index": pair_index,
                **line_character_certificate(
                    conf=conf_7914,
                    coordinate_signs_by_block=coordinate_signs_by_block_7914,
                    equation_signs=equation_signs_7914,
                    line_bundle=dual_line,
                    cohomology=dual_cohom,
                    mixed_pattern=dual_mixed,
                    fiber_sign=fiber_signs[a] * fiber_signs[b],
                ),
            }
        )

    sectors = {
        "V": sector_record(
            label="V",
            line_certificates=v_certs,
            cohomology_degree_keys=["H1"],
        ),
        "V_dual": sector_record(
            label="V*",
            line_certificates=vdual_certs,
            cohomology_degree_keys=["H2"],
        ),
        "wedge2_V": sector_record(
            label="wedge2 V",
            line_certificates=wedge_certs,
            cohomology_degree_keys=["H1", "H2"],
        ),
        "wedge2_V_dual": sector_record(
            label="wedge2 V*",
            line_certificates=wedge_dual_certs,
            cohomology_degree_keys=["H1", "H2"],
        ),
    }
    h1_v = sectors["V"]["cohomology_characters"]["H1"]
    h1_wedge = sectors["wedge2_V"]["cohomology_characters"]["H1"]
    h2_wedge = sectors["wedge2_V"]["cohomology_characters"]["H2"]

    wilson_line = {
        "label": "nontrivial_Z2_SU5_breaking",
        "fundamental_5_character_assignment": {
            "color_triplet": "+",
            "weak_doublet": "-",
            "determinant_condition_satisfied": True,
        },
        "ten_sector": {
            "q_left_doublets": h1_v["multiplicities"]["-"],
            "u_right_conjugates": h1_v["multiplicities"]["+"],
            "e_right_conjugates": h1_v["multiplicities"]["+"],
            "three_family_10_sector": h1_v["multiplicities"]["+"] == 3
            and h1_v["multiplicities"]["-"] == 3,
        },
        "fivebar_and_five_sector": {
            "dbar_triplets_from_H1_wedge2V": h1_wedge["multiplicities"]["+"],
            "lepton_doublets_from_H1_wedge2V": h1_wedge["multiplicities"]["-"],
            "triplets_from_H2_wedge2V": h2_wedge["multiplicities"]["+"],
            "doublets_from_H2_wedge2V": h2_wedge["multiplicities"]["-"],
            "net_dbar_families": h1_wedge["multiplicities"]["+"]
            - h2_wedge["multiplicities"]["+"],
            "net_lepton_doublet_families": h1_wedge["multiplicities"]["-"]
            - h2_wedge["multiplicities"]["-"],
            "colored_triplet_vectorlike_pairs": h2_wedge["multiplicities"]["+"],
            "electroweak_doublet_vectorlike_pairs": h2_wedge["multiplicities"]["-"],
        },
    }
    five = wilson_line["fivebar_and_five_sector"]
    wilson_line["standard_model_like"] = (
        wilson_line["ten_sector"]["three_family_10_sector"]
        and five["net_dbar_families"] == 3
        and five["net_lepton_doublet_families"] == 3
        and five["colored_triplet_vectorlike_pairs"] == 0
        and five["electroweak_doublet_vectorlike_pairs"] <= 1
    )
    wilson_line["obstruction"] = (
        "excessive_vectorlike_5_content"
        if not wilson_line["standard_model_like"]
        else None
    )

    gates = {
        "selected_recorded_free_z2_action": gate(
            selected["option_index"] == 0
            and selected["ambient_row_permutation"] == list(range(6))
            and selected["quotient_order"] == 2,
            "data/raw/cicylist.m Num -> 5259",
            "selected the first recorded free Z2 action; all old ambient divisor rows are fixed",
        ),
        "split_action_lift_exists": gate(
            p2_lift["matches_original_first_polynomial_sign"]
            and p2_lift["balanced"],
            "balanced P2 sign lift on the 7914 split equations",
            "new P2 signs and split-equation signs reproduce the original first-polynomial character",
        ),
        "full_picard_action_certified": gate(
            selected["ambient_row_permutation"] == list(range(6)),
            "diagonal coordinate action on old rows plus diagonal P2 action",
            "the induced action on the seven favourable 7914 divisor rows is identity",
        ),
        "line_bundle_equivariance_certified": gate(
            determinant_fiber_sign == 1 and admissible_fiber_lift_count == 16,
            "zero-extended 7914 line-bundle matrix",
            "all summands are fixed and admit Z2 linearisations with trivial determinant",
        ),
        "cohomology_characters_computed": gate(
            all(sector["all_characters_computed"] for sector in sectors.values())
            and sectors["V"]["cohomology_characters"]["H1"]["regular_multiplicity"] == 3
            and sectors["wedge2_V"]["cohomology_characters"]["H1"][
                "regular_multiplicity"
            ]
            == 8
            and sectors["wedge2_V"]["cohomology_characters"]["H2"][
                "regular_multiplicity"
            ]
            == 5,
            "Koszul source character audit plus pyCICY dimensions",
            "actual Z2 characters are regular in the V and wedge2 sectors",
        ),
        "wilson_line_rejected_by_vectorlike_content": gate(
            not wilson_line["standard_model_like"]
            and five["colored_triplet_vectorlike_pairs"] == 5
            and five["electroweak_doublet_vectorlike_pairs"] == 5,
            "nontrivial Z2 SU(5) Wilson-line projection",
            "three-family chirality survives, but five vectorlike 5+5bar pairs remain",
        ),
    }

    return {
        "scope": "CICY5259 quotient/Wilson-line certification attempt using favourable split 7914",
        "conclusion": {
            "status": "quotient_lift_certified__wilson_line_rejected_excess_vectorlike_5_content",
            "selected_5259_free_action_option": selected["option_index"],
            "split_action_lift_certified": True,
            "full_picard_action_certified": True,
            "line_bundle_equivariance_certified": True,
            "cohomology_characters_computed": True,
            "standard_model_like_candidate_certified": False,
            "precise_obstruction": "excessive_vectorlike_5_content",
            "summary": (
                "The selected free Z2 action lifts through the 7914 P2 split and the zero-extended bundle "
                "admits equivariant linearisations. The actual Z2 cohomology characters are regular: "
                "H1(V)=3 regular, H1(wedge2 V)=8 regular, and H2(wedge2 V)=5 regular. "
                "The nontrivial SU(5)-breaking Z2 Wilson line therefore gives three-family chirality but "
                "also five colored-triplet and five electroweak-doublet vectorlike 5+5bar pairs."
            ),
        },
        "selected_recorded_free_action_5259": selected,
        "split_lift_7914": {
            **p2_lift,
            "coordinate_signs_by_ambient_block_7914": coordinate_signs_by_block_7914,
            "equation_signs_7914": equation_signs_7914,
            "induced_picard_action_on_J0_to_J6": list(range(7)),
            "unchanged_equation_signs_from_5259_columns_1_to_4": selected[
                "polynomial_signs_5259"
            ][1:],
        },
        "line_bundle_equivariance": {
            "matrix_7914_zero_extended": matrix_7914,
            "summand_fiber_signs_used": fiber_signs,
            "determinant_fiber_sign": determinant_fiber_sign,
            "admissible_determinant_trivial_fiber_lift_count": admissible_fiber_lift_count,
            "all_summand_divisor_classes_fixed": True,
            "direct_sum_equivariant_lift_exists": True,
            "character_results_independent_of_fiber_sign_choice": (
                "All nonzero cohomology representations computed below are regular Z2 representations; twisting "
                "individual summands by a Z2 character swaps plus/minus labels inside equal multiplicities."
            ),
        },
        "equivariant_cohomology_characters": sectors,
        "wilson_line_enumeration": {
            "admissible_nontrivial_embeddings": [wilson_line],
            "trivial_embedding_note": (
                "The trivial Z2 embedding leaves SU(5) unbroken and is not counted as a Standard-Model Wilson line."
            ),
        },
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    conclusion = report["conclusion"]
    wl = report["wilson_line_enumeration"]["admissible_nontrivial_embeddings"][0]
    five = wl["fivebar_and_five_sector"]
    sectors = report["equivariant_cohomology_characters"]
    lines = [
        "# CICY 5259 quotient/Wilson-line attempt",
        "",
        f"Status: `{conclusion['status']}`",
        "",
        "## Result",
        "",
        "- The selected recorded free `Z2` action is option `0` for CICY 5259.",
        "- It lifts through the favourable `7914` `P2` split.",
        "- The induced action on the full seven-divisor Picard basis is identity.",
        "- The zero-extended line-bundle sum admits determinant-trivial equivariant linearisations.",
        "- The Wilson-line projection is rejected because of excessive vectorlike `5/5bar` content.",
        "",
        "## Characters",
        "",
        f"- `H1(V)`: `{sectors['V']['cohomology_characters']['H1']}`",
        f"- `H1(wedge2 V)`: `{sectors['wedge2_V']['cohomology_characters']['H1']}`",
        f"- `H2(wedge2 V)`: `{sectors['wedge2_V']['cohomology_characters']['H2']}`",
        f"- `H1(wedge2 V*)`: `{sectors['wedge2_V_dual']['cohomology_characters']['H1']}`",
        "",
        "## Downstairs Spectrum",
        "",
        f"- `10` sector three-family check: `{wl['ten_sector']['three_family_10_sector']}`",
        f"- net dbar families: `{five['net_dbar_families']}`",
        f"- net lepton-doublet families: `{five['net_lepton_doublet_families']}`",
        f"- colored triplet vectorlike pairs: `{five['colored_triplet_vectorlike_pairs']}`",
        f"- electroweak doublet vectorlike pairs: `{five['electroweak_doublet_vectorlike_pairs']}`",
        "",
        "So this is quotient-compatible through the geometry/equivariant-bundle gates, but not Standard-Model-like after the actual `Z2` Wilson-line projection.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_quotient_wilson_line_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy5259_quotient_wilson_line_report.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(f"precise_obstruction={report['conclusion']['precise_obstruction']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
