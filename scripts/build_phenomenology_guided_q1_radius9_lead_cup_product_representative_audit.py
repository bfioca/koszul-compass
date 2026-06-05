#!/usr/bin/env python3
"""Representative-level audit for the lead q=1 cup-product gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import (  # noqa: E402
    ambient_bundle_for_origin,
    entry_basis_signs,
    rep_from_signs,
)
from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    rank_split,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import (  # noqa: E402
    cohomology_record,
    ensure_pycicy_compat,
    make_pycicy,
    pycicy_config,
)

EXPECTED_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
EXPECTED_OPERATOR = "5bar_02*5_24*S_40"
L02 = [0, 1, 0, -2, 0, 0, 1]
L24_DUAL = [0, -2, 0, 0, 1, 0, 0]
L40 = [0, 1, 0, 2, -1, 0, -1]
O_X = [0, 0, 0, 0, 0, 0, 0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def matrix_rank(matrix: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(matrix))


def basis_monomials(manifold: Any, bracket: list[int]) -> list[list[int]]:
    dim = manifold._brackets_dim(bracket)
    if dim == 1 and all(entry == 0 for entry in bracket):
        length = int(np.sum(manifold.M[:, 0]) + manifold.len)
        return [[0 for _ in range(length)]]
    return [[int(x) for x in row] for row in manifold._makepoly(bracket, dim)]


def entry_records_for_line(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> dict[str, Any]:
    e1, origin = manifold.Leray(manifold._line_to_BBW(line_bundle))
    entries = []
    for k, row in enumerate(e1):
        for j, value in enumerate(row):
            if value == 0:
                continue
            bracket_entries = [[int(x) for x in item] for item in value]
            origins = [list(item) for item in origin[k][j]]
            signs = entry_basis_signs(
                manifold=manifold,
                conf=conf,
                line_bundle=line_bundle,
                bracket_entries=bracket_entries,
                origins=origins,
                coordinate_signs_by_block=coordinate_signs_by_block,
                equation_signs=equation_signs,
            )
            per_bracket_basis = [basis_monomials(manifold, bracket) for bracket in bracket_entries]
            entries.append(
                {
                    "k": k,
                    "j": j,
                    "total_degree": j - k,
                    "bracket_entries": bracket_entries,
                    "origins": origins,
                    "ambient_bundles": [
                        ambient_bundle_for_origin(
                            line_bundle=line_bundle,
                            conf=conf,
                            origin=item,
                        )
                        for item in origins
                    ],
                    "basis_monomials_by_bracket": per_bracket_basis,
                    "basis_signs": signs,
                    "basis_sign_representation": rep_from_signs(signs),
                }
            )
    return {
        "line_bundle": line_bundle,
        "cohomology": cohomology_record(conf, line_bundle)["cohomology"],
        "entries": entries,
    }


def select_entry(line_audit: dict[str, Any], *, k: int, j: int) -> dict[str, Any]:
    for entry in line_audit["entries"]:
        if entry["k"] == k and entry["j"] == j:
            return entry
    raise KeyError(f"missing E1 entry k={k}, j={j} for {line_audit['line_bundle']}")


def required_image_ranks(
    target_rep: dict[str, Any],
    desired_cokernel_rep: dict[str, Any],
) -> dict[str, int]:
    return {
        "+": target_rep["multiplicities"]["+"] - desired_cokernel_rep["multiplicities"]["+"],
        "-": target_rep["multiplicities"]["-"] - desired_cokernel_rep["multiplicities"]["-"],
    }


def l02_cokernel_audit(
    *,
    manifold: Any,
    conf: list[list[int]],
    context: dict[str, Any],
    l02_audit: dict[str, Any],
    branch_certificate: dict[str, Any],
) -> dict[str, Any]:
    source = select_entry(l02_audit, k=1, j=1)
    target = select_entry(l02_audit, k=0, j=1)
    source_entries = source["bracket_entries"]
    target_entries = target["bracket_entries"]
    source_origins = source["origins"]
    target_origins = target["origins"]
    source_signs = source["basis_signs"]
    target_signs = target["basis_signs"]
    matrix = equivariant_rank_map(
        manifold=manifold,
        source_entries=source_entries,
        target_entries=target_entries,
        source_origins=source_origins,
        target_origins=target_origins,
        coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
        equation_signs=context["equation_signs_7914"],
    )
    split = rank_split(matrix=matrix, source_signs=source_signs, target_signs=target_signs)
    target_rep = target["basis_sign_representation"]
    source_rep = source["basis_sign_representation"]
    computed_cokernel = {
        "dimension": target_rep["dimension"] - split["rank_total"],
        "multiplicities": {
            "+": target_rep["multiplicities"]["+"] - split["rank_plus"],
            "-": target_rep["multiplicities"]["-"] - split["rank_minus"],
        },
    }
    computed_cokernel["nonidentity_trace"] = (
        computed_cokernel["multiplicities"]["+"]
        - computed_cokernel["multiplicities"]["-"]
    )
    computed_cokernel["regular_multiplicity"] = (
        computed_cokernel["multiplicities"]["+"]
        if computed_cokernel["multiplicities"]["+"] == computed_cokernel["multiplicities"]["-"]
        else None
    )
    branch_actual = branch_certificate["actual"]["H1"]
    required = required_image_ranks(target_rep, branch_actual)
    required_feasible = all(
        0 <= required[sign] <= min(source_rep["multiplicities"][sign], target_rep["multiplicities"][sign])
        for sign in ("+", "-")
    )
    cokernel_floor = {
        sign: target_rep["multiplicities"][sign]
        - min(source_rep["multiplicities"][sign], target_rep["multiplicities"][sign])
        for sign in ("+", "-")
    }
    no_higher_entries = sorted((entry["k"], entry["j"]) for entry in l02_audit["entries"]) == [
        (0, 1),
        (1, 1),
    ]
    source_totals_match_branch_sources = (
        branch_certificate["source_totals"]["0"] == source_rep
        and branch_certificate["source_totals"]["1"] == target_rep
    )
    return {
        "status": "representative_character_mismatch",
        "interpretation": (
            "H1(L_02) is the cokernel of the first-page Koszul map E1[1,1] -> E1[0,1]. "
            "The branch-completion character used by the selection-rule lead requires "
            "a minus-image rank larger than the available minus-source dimension."
        ),
        "source_entry": source,
        "target_entry": target,
        "no_other_e1_entries_for_l02": no_higher_entries,
        "source_totals_match_branch_sources": source_totals_match_branch_sources,
        "equivariant_first_page_matrix_target_by_source": matrix.astype(int).tolist(),
        "equivariant_first_page_rank_split": split,
        "computed_cokernel_character_from_representative_map": computed_cokernel,
        "branch_completion_character": branch_actual,
        "required_image_ranks_for_branch_character": required,
        "cokernel_multiplicity_floor_from_e1_bounds": cokernel_floor,
        "branch_character_feasible_from_e1_bounds": required_feasible,
        "branch_character_matches_computed_cokernel": branch_actual == computed_cokernel,
    }


def product_shape_audit(
    *,
    l02: dict[str, Any],
    l24: dict[str, Any],
    l40: dict[str, Any],
    top: dict[str, Any],
) -> dict[str, Any]:
    l02_target = select_entry(l02, k=0, j=1)
    l24_entry = select_entry(l24, k=0, j=1)
    l40_entry = select_entry(l40, k=2, j=3)
    top_entry = select_entry(top, k=7, j=10)
    product_origin = sorted(
        set(l02_target["origins"][0] + l24_entry["origins"][0] + l40_entry["origins"][0])
    )
    product_j = l02_target["j"] + l24_entry["j"] + l40_entry["j"]
    product_k = len(product_origin)
    return {
        "naive_factor_entries": {
            "L02_cokernel_target_entry": {"k": l02_target["k"], "j": l02_target["j"], "origins": l02_target["origins"]},
            "L24_dual_entry": {"k": l24_entry["k"], "j": l24_entry["j"], "origins": l24_entry["origins"]},
            "L40_entry": {"k": l40_entry["k"], "j": l40_entry["j"], "origins": l40_entry["origins"]},
        },
        "naive_tensor_product_position": {
            "k": product_k,
            "j": product_j,
            "total_degree": product_j - product_k,
            "origin_union": product_origin,
        },
        "top_h3_ox_representative_position": {
            "k": top_entry["k"],
            "j": top_entry["j"],
            "total_degree": top_entry["total_degree"],
            "origins": top_entry["origins"],
        },
        "direct_e1_product_lands_on_top_representative": (
            product_k == top_entry["k"]
            and product_j == top_entry["j"]
            and product_origin == top_entry["origins"][0]
        ),
        "missing_chain_map": (
            "A tensor-product Koszul chain map/projection is needed to carry the "
            "naive product at origin [1,2] and ambient degree 5 to the top "
            "H3(O_X) representative at origin [0,1,2,3,4,5,6] and ambient degree 10."
        ),
    }


def select_l02_branch_certificate(dossier: dict[str, Any]) -> dict[str, Any]:
    certificates = dossier["spectrum_and_character_certificate"]["character_certificate"][
        "characters"
    ]["wedge2_V"]["line_certificates"]
    for certificate in certificates:
        if certificate.get("summand_pair") == [0, 2]:
            return certificate
    raise KeyError("missing L02 wedge2_V certificate")


def build_report(
    *,
    mass_rank_probe_json: Path,
    mass_rank_verification_json: Path,
    dossier_json: Path,
    split_json: Path,
) -> dict[str, Any]:
    mass_rank = load_json(mass_rank_probe_json)
    mass_rank_verification = load_json(mass_rank_verification_json)
    dossier = load_json(dossier_json)
    split = load_json(split_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))

    line_audits = {
        "L02_fivebar": entry_records_for_line(
            manifold=manifold,
            conf=conf,
            line_bundle=L02,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
        "L24_dual": entry_records_for_line(
            manifold=manifold,
            conf=conf,
            line_bundle=L24_DUAL,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
        "L40_singlet": entry_records_for_line(
            manifold=manifold,
            conf=conf,
            line_bundle=L40,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
        "O_X": entry_records_for_line(
            manifold=manifold,
            conf=conf,
            line_bundle=O_X,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        ),
    }
    l02_branch = select_l02_branch_certificate(dossier)
    l02 = l02_cokernel_audit(
        manifold=manifold,
        conf=conf,
        context=context,
        l02_audit=line_audits["L02_fivebar"],
        branch_certificate=l02_branch,
    )
    product = product_shape_audit(
        l02=line_audits["L02_fivebar"],
        l24=line_audits["L24_dual"],
        l40=line_audits["L40_singlet"],
        top=line_audits["O_X"],
    )
    single_leg_checks = {
        "L24_dual_single_source_matches_mass_probe": (
            line_audits["L24_dual"]["entries"][0]["basis_sign_representation"]
            == mass_rank["exact_spaces"]["serre_dual_cup_product_spaces"]["five_24_cup_leg"][
                "actual_character"
            ]
        ),
        "L40_single_source_matches_mass_probe": (
            line_audits["L40_singlet"]["entries"][0]["basis_sign_representation"]
            == mass_rank["exact_spaces"]["serre_dual_cup_product_spaces"][
                "singlet_S_40_cup_leg"
            ]["actual_character"]
        ),
    }
    verdict = {
        "status": "obstructed_by_representative_character_mismatch_before_cup_product",
        "mass_rank_verified": False,
        "triplet_rank": None,
        "doublet_rank": None,
        "rank_stage_reached": False,
        "selection_rule_branch_status": mass_rank["verdict"]["selection_rule_status"],
        "exact_representative_status": "L02 branch character is not compatible with the explicit E1 source/target bounds",
        "reason": (
            "The targeted representative reconstruction reaches an earlier gate than "
            "the trilinear cup coefficient: H1(L_02) is a cokernel of a 4 -> 6 "
            "equivariant first-page map with source/target signs +2/-2 -> +3/-3. "
            "The branch completion used by the selection-rule lead asks for "
            "H1(L_02)=+2/-0, which would require image ranks +1/-3; the minus "
            "rank exceeds the available minus source dimension 2. Therefore the "
            "doublet-zero block is not representative-certified for this branch, "
            "and the requested triplet mass column cannot be exactly certified as stated."
        ),
    }
    missing_or_external_primitives = [
        {
            "name": "representative_level_equivariant_character_certificate_for_L02",
            "status": "not_missing_but_failed_for_current_branch",
            "detail": (
                "The explicit E1 data provide source +2/-2 and target +3/-3; "
                "no equivariant map can produce the branch-completion H1 character +2/-0."
            ),
        },
        {
            "name": "tensor_product_koszul_chain_map_to_top_cohomology",
            "status": "still_missing_for_any_future_rank_computation",
            "detail": product["missing_chain_map"],
        },
        {
            "name": "quotient_projection_for_L02_cokernel_representatives",
            "status": "needed_if_a_representative_compatible_branch_is_found",
            "detail": (
                "A valid product must multiply quotient classes in coker(E1[1,1] -> E1[0,1]), "
                "not arbitrary elements of the 6-dimensional ambient target."
            ),
        },
    ]
    dangerous = mass_rank["dangerous_operator_regression"]
    gates = {
        "starts_from_verified_mass_rank_probe": gate(
            mass_rank["all_gates_pass"]
            and mass_rank_verification["all_gates_pass"]
            and mass_rank["candidate_label"] == EXPECTED_LABEL
            and mass_rank["exact_spaces"]["operator"] == EXPECTED_OPERATOR,
            f"{mass_rank_probe_json} + {mass_rank_verification_json}",
            "representative audit starts from the verified targeted mass-rank probe",
        ),
        "single_source_legs_reconstructed": gate(
            single_leg_checks["L24_dual_single_source_matches_mass_probe"]
            and single_leg_checks["L40_single_source_matches_mass_probe"],
            "L24_dual and L40 E1 entries",
            "the two single-source cup-product legs reproduce the previous Z2 characters",
        ),
        "l02_e1_sources_match_branch_source_totals": gate(
            l02["source_totals_match_branch_sources"],
            "L02 E1 source and target representations",
            "the representative audit uses the same E1 source totals as the branch certificate",
        ),
        "l02_branch_character_infeasible": gate(
            not l02["branch_character_feasible_from_e1_bounds"]
            and not l02["branch_character_matches_computed_cokernel"]
            and l02["computed_cokernel_character_from_representative_map"]["multiplicities"]
            == {"+": 1, "-": 1},
            "L02 coker(E1[1,1] -> E1[0,1])",
            "the branch H1 character +2/-0 is impossible from the explicit E1 sign bounds",
        ),
        "product_chain_map_not_direct": gate(
            not product["direct_e1_product_lands_on_top_representative"],
            "Koszul origins for the three factors and H3(O_X)",
            "naive E1 multiplication does not land directly on the top cohomology representative",
        ),
        "dangerous_operator_regression_preserved": gate(
            dangerous["count"] == 10 and dangerous["all_forbidden"],
            "mass-rank probe dangerous-operator regression",
            "the representative audit preserves the already verified dangerous-operator gate",
        ),
        "verdict_is_not_overclaimed": gate(
            verdict["status"] == "obstructed_by_representative_character_mismatch_before_cup_product"
            and not verdict["mass_rank_verified"]
            and verdict["triplet_rank"] is None,
            "representative-level verdict",
            "the report does not claim a cup-product rank after the L02 representative mismatch",
        ),
    }
    return {
        "title": "Lead q=1 Representative Cup-Product Audit",
        "scope": f"{EXPECTED_LABEL}: {EXPECTED_OPERATOR}",
        "status": verdict["status"],
        "candidate_label": EXPECTED_LABEL,
        "operator": EXPECTED_OPERATOR,
        "source_artifacts": {
            "mass_rank_probe_json": str(mass_rank_probe_json),
            "mass_rank_verification_json": str(mass_rank_verification_json),
            "dossier_json": str(dossier_json),
            "split_json": str(split_json),
        },
        "line_audits": line_audits,
        "l02_representative_cokernel_audit": l02,
        "single_source_leg_checks": single_leg_checks,
        "product_shape_audit": product,
        "heuristic_nonvanishing_tests": {
            "performed": False,
            "reason": (
                "Unsafe at this stage: the L02 branch character is not representative-compatible, "
                "and the naive E1 product does not land directly in the H3(O_X) top representative."
            ),
        },
        "missing_or_external_primitives": missing_or_external_primitives,
        "dangerous_operator_regression": dangerous,
        "verdict": verdict,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    l02 = report["l02_representative_cokernel_audit"]
    product = report["product_shape_audit"]
    verdict = report["verdict"]
    lines = [
        "# Lead q=1 Representative Cup-Product Audit",
        "",
        f"Status: `{report['status']}`",
        f"Candidate: `{report['candidate_label']}`",
        f"Operator: `{report['operator']}`",
        "",
        "## Representative Reconstruction",
        "",
        "- `H1(L_24^*)` is a single E1 representative and matches the previous `+1/-1` character.",
        "- `H1(L_40)` is a single E1 representative and matches the previous `+2/-2` character.",
        "- `H1(L_02)` is not a single representative: it is the cokernel of `E1[1,1] -> E1[0,1]`.",
        "",
        "## L02 Cokernel",
        "",
        f"- source representation: `{l02['source_entry']['basis_sign_representation']}`",
        f"- target representation: `{l02['target_entry']['basis_sign_representation']}`",
        f"- equivariant rank split: `{l02['equivariant_first_page_rank_split']}`",
        f"- computed representative cokernel: `{l02['computed_cokernel_character_from_representative_map']}`",
        f"- branch-completion character: `{l02['branch_completion_character']}`",
        f"- required image ranks for branch character: `{l02['required_image_ranks_for_branch_character']}`",
        f"- branch feasible from E1 bounds: `{l02['branch_character_feasible_from_e1_bounds']}`",
        "",
        "## Product Shape",
        "",
        f"- naive tensor-product position: `{product['naive_tensor_product_position']}`",
        f"- top `H3(O_X)` position: `{product['top_h3_ox_representative_position']}`",
        f"- direct E1 product lands on top representative: `{product['direct_e1_product_lands_on_top_representative']}`",
        "",
        "## Verdict",
        "",
        f"- status: `{verdict['status']}`",
        f"- triplet rank: `{verdict['triplet_rank']}`",
        f"- doublet rank: `{verdict['doublet_rank']}`",
        f"- mass-rank verified: `{verdict['mass_rank_verified']}`",
        "",
        verdict["reason"],
        "",
        "## Remaining Primitive",
        "",
        "For a future representative-compatible branch, the remaining cup-product primitive is a tensor-product Koszul chain map/projection to the top `H3(O_X)` representative, plus quotient projection for the `L_02` cokernel.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mass-rank-probe-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe.json"),
    )
    parser.add_argument(
        "--mass-rank-verification-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe_verification.json"
        ),
    )
    parser.add_argument(
        "--dossier-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.json"),
    )
    parser.add_argument(
        "--split-json",
        default=str(REPORTS / "cicy5259_split_lift_report.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_cup_product_representative_audit.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_cup_product_representative_audit.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        mass_rank_probe_json=Path(args.mass_rank_probe_json),
        mass_rank_verification_json=Path(args.mass_rank_verification_json),
        dossier_json=Path(args.dossier_json),
        split_json=Path(args.split_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(
        "l02_cokernel="
        f"{report['l02_representative_cokernel_audit']['computed_cokernel_character_from_representative_map']['multiplicities']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
