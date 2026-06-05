#!/usr/bin/env python3
"""Probe the minimal cup-product mass-rank gate for the frozen q=1 lead."""

from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cohomology import (  # noqa: E402
    cohomology_record,
    dual,
    ensure_pycicy_compat,
    make_pycicy,
    pycicy_config,
)

EXPECTED_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
EXPECTED_OPERATOR = "5bar_02*5_24*S_40"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def vector_sum(*vectors: list[int]) -> list[int]:
    return [sum(vector[index] for vector in vectors) for index in range(len(vectors[0]))]


def select_pair_certificate(
    *,
    dossier: dict[str, Any],
    sector: str,
    pair: list[int],
) -> dict[str, Any]:
    certificates = dossier["spectrum_and_character_certificate"]["character_certificate"][
        "characters"
    ][sector]["line_certificates"]
    for certificate in certificates:
        if certificate.get("summand_pair") == pair:
            return certificate
    raise KeyError(f"missing {sector} certificate for pair {pair}")


def pycicy_capability_probe(conf: list[list[int]]) -> dict[str, Any]:
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    method_names = [
        name
        for name in dir(manifold)
        if any(
            needle in name.lower()
            for needle in ("cup", "product", "ring", "basis", "poly", "map", "rank")
        )
    ]
    map_methods = {}
    for name in [
        "line_co",
        "_line_to_BBW",
        "Leray",
        "_rank_map",
        "_single_map",
        "_higher_map",
        "_makepoly",
        "_orth_space_map",
    ]:
        attr = getattr(manifold, name, None)
        map_methods[name] = {
            "available": attr is not None,
            "signature": str(inspect.signature(attr)) if attr is not None else None,
        }
    single_map_source = inspect.getsource(manifold._single_map)
    named_cup_methods = []
    for name in method_names:
        lowered = name.lower()
        if "cup" in lowered or "ring" in lowered:
            named_cup_methods.append(name)
        elif "product" in lowered and lowered not in {"is_directproduct"}:
            named_cup_methods.append(name)
    return {
        "pycicy_class": f"{type(manifold).__module__}.{type(manifold).__name__}",
        "method_names_with_relevant_tokens": method_names,
        "named_cup_or_ring_methods": named_cup_methods,
        "map_method_signatures": map_methods,
        "single_map_is_equation_multiplication_hook": (
            "normal section used for the map" in single_map_source
            and "self.moduli" in single_map_source
        ),
        "has_exposed_trilinear_cup_product_api": bool(named_cup_methods),
        "local_string_theory_wrapper_has_product_api": False,
    }


def build_exact_spaces(
    *,
    dossier: dict[str, Any],
    split: dict[str, Any],
) -> dict[str, Any]:
    conf = split["full_picard_presentation_7914"]["conf"]
    hit = dossier["mass_operator_table"]["triplet_only_hits"][0]
    fivebar_cert = select_pair_certificate(dossier=dossier, sector="wedge2_V", pair=[0, 2])
    physical_five_cert = select_pair_certificate(
        dossier=dossier, sector="wedge2_V", pair=[2, 4]
    )
    cup_five_cert = select_pair_certificate(
        dossier=dossier, sector="wedge2_V_dual", pair=[2, 4]
    )
    singlet = hit["invariant_singlet_monomials"][0]["singlet_factors"][0]

    fivebar_line = fivebar_cert["line_bundle"]
    physical_five_line = physical_five_cert["line_bundle"]
    cup_five_line = cup_five_cert["line_bundle"]
    singlet_line = singlet["line_bundle"]
    target_line = [0] * len(fivebar_line)
    line_sum = vector_sum(fivebar_line, cup_five_line, singlet_line)

    return {
        "operator": EXPECTED_OPERATOR,
        "component_selection_rule_spaces": {
            "fivebar_02_physical": {
                "sector": "H1(wedge2 V)",
                "line_bundle": fivebar_line,
                "cohomology": fivebar_cert["cohomology"],
                "pycicy_recomputed_cohomology": cohomology_record(conf, fivebar_line)[
                    "cohomology"
                ],
                "actual_character": fivebar_cert["actual"]["H1"],
                "certificate_method": fivebar_cert["method"],
                "sources": fivebar_cert["sources"],
            },
            "five_24_physical": {
                "sector": "H2(wedge2 V)",
                "line_bundle": physical_five_line,
                "cohomology": physical_five_cert["cohomology"],
                "pycicy_recomputed_cohomology": cohomology_record(conf, physical_five_line)[
                    "cohomology"
                ],
                "actual_character": physical_five_cert["actual"]["H2"],
                "certificate_method": physical_five_cert["method"],
                "sources": physical_five_cert["sources"],
            },
        },
        "serre_dual_cup_product_spaces": {
            "fivebar_02_cup_leg": {
                "sector": "H1(L_02)",
                "line_bundle": fivebar_line,
                "cohomology": fivebar_cert["cohomology"],
                "actual_character": fivebar_cert["actual"]["H1"],
                "certificate_method": fivebar_cert["method"],
            },
            "five_24_cup_leg": {
                "sector": "H1(L_24^*)",
                "line_bundle": cup_five_line,
                "cohomology": cup_five_cert["cohomology"],
                "pycicy_recomputed_cohomology": cohomology_record(conf, cup_five_line)[
                    "cohomology"
                ],
                "actual_character": cup_five_cert["actual"]["H1"],
                "certificate_method": cup_five_cert["method"],
                "sources": cup_five_cert["sources"],
                "serre_dual_to_physical_line": physical_five_line,
            },
            "singlet_S_40_cup_leg": {
                "sector": "H1(L_40)",
                "line_bundle": singlet_line,
                "cohomology": singlet["cohomology"],
                "pycicy_recomputed_cohomology": cohomology_record(conf, singlet_line)[
                    "cohomology"
                ],
                "actual_character": singlet["character_certificate"]["actual"]["H1"],
                "certificate_method": singlet["character_certificate"]["method"],
            },
            "target": {
                "sector": "H3(O_X)",
                "line_bundle": target_line,
                "cohomology": cohomology_record(conf, target_line)["cohomology"],
                "required_for_cubic": "H1(L_02) x H1(L_24^*) x H1(L_40) -> H3(O_X)",
            },
            "line_bundle_sum": line_sum,
            "line_bundle_sum_is_trivial": line_sum == target_line,
        },
    }


def build_mass_blocks(spaces: dict[str, Any]) -> dict[str, Any]:
    fivebar = spaces["serre_dual_cup_product_spaces"]["fivebar_02_cup_leg"][
        "actual_character"
    ]["multiplicities"]
    five_physical = spaces["component_selection_rule_spaces"]["five_24_physical"][
        "actual_character"
    ]["multiplicities"]
    five_cup = spaces["serre_dual_cup_product_spaces"]["five_24_cup_leg"][
        "actual_character"
    ]["multiplicities"]
    singlet = spaces["serre_dual_cup_product_spaces"]["singlet_S_40_cup_leg"][
        "actual_character"
    ]["multiplicities"]
    return {
        "wilson_line_assignment": {
            "color_triplet_character": "+",
            "weak_doublet_character": "-",
        },
        "triplet_block": {
            "fivebar_component_dimension": fivebar["+"],
            "five_physical_component_dimension": five_physical["+"],
            "five_cup_leg_component_dimension": five_cup["+"],
            "even_singlet_component_dimension": singlet["+"],
            "matrix_shape_after_singlet_vevs": [fivebar["+"], five_physical["+"]],
            "raw_trilinear_parameter_count": fivebar["+"] * five_cup["+"] * singlet["+"],
            "required_rank": 1,
            "rank_computed": False,
            "rank": None,
            "rank_status": "not_computed",
            "rank_condition": (
                "at least one even-singlet plus-sector cup coefficient must give a "
                "nonzero 2-by-1 triplet mass column"
            ),
        },
        "doublet_block": {
            "fivebar_component_dimension": fivebar["-"],
            "five_physical_component_dimension": five_physical["-"],
            "five_cup_leg_component_dimension": five_cup["-"],
            "even_singlet_component_dimension": singlet["+"],
            "matrix_shape_after_singlet_vevs": [fivebar["-"], five_physical["-"]],
            "raw_trilinear_parameter_count": fivebar["-"] * five_cup["-"] * singlet["+"],
            "required_rank": 0,
            "rank_computed": True,
            "rank": 0,
            "rank_status": "forced_zero_by_missing_fivebar_minus_component",
            "rank_condition": "rank zero is automatic because H1(L_02)_- has dimension zero",
        },
        "serre_dual_character_alignment": {
            "physical_five_h2_multiplicities": five_physical,
            "cup_five_h1_dual_multiplicities": five_cup,
            "same_z2_multiplicities": five_physical == five_cup,
        },
    }


def build_report(
    *,
    dossier_json: Path,
    dossier_verification_json: Path,
    split_json: Path,
) -> dict[str, Any]:
    dossier = load_json(dossier_json)
    dossier_verification = load_json(dossier_verification_json)
    split = load_json(split_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    spaces = build_exact_spaces(dossier=dossier, split=split)
    blocks = build_mass_blocks(spaces)
    capability = pycicy_capability_probe(conf)
    proton = dossier["dangerous_operator_table"]

    missing_primitives = [
        "explicit cocycle or quotient representatives for H1(L_02), whose character certificate is not single-source",
        "a trilinear cup-product routine H1(L_02) x H1(L_24^*) x H1(L_40) -> H3(O_X)",
        "reduction of products modulo the CICY defining equations in a Z2 eigenbasis",
        "rank extraction for the induced plus-sector 2-by-1 triplet mass column after singlet vevs",
    ]
    verdict = {
        "status": "unresolved_due_missing_cup_product_machinery",
        "mass_rank_verified": False,
        "selection_rule_status": "passes_charge_character_dt_and_proton_regression",
        "doublet_block_verdict": "rank_0_verified_by_component_dimension",
        "triplet_block_verdict": "rank_1_not_computed",
        "obstruction": None,
        "reason": (
            "The exact line-bundle and character gates allow a selective triplet mass, "
            "and the doublet block is forced rank zero. The local machinery exposes "
            "Koszul maps for line cohomology but no trilinear cup-product map or "
            "cohomology representatives, so the nonzero triplet column is not certified."
        ),
    }
    gates = {
        "starts_from_verified_frozen_lead": gate(
            dossier["all_gates_pass"]
            and dossier_verification["all_gates_pass"]
            and dossier["candidate_identity"]["label"] == EXPECTED_LABEL,
            f"{dossier_json} + {dossier_verification_json}",
            "mass-rank probe starts from the verified corrected lead dossier",
        ),
        "targets_expected_mass_operator": gate(
            len(dossier["mass_operator_table"]["triplet_only_hits"]) == 1
            and spaces["operator"] == EXPECTED_OPERATOR,
            EXPECTED_OPERATOR,
            "probe is scoped to the unique corrected triplet-only mass hit",
        ),
        "cup_product_line_sum_is_trivial": gate(
            spaces["serre_dual_cup_product_spaces"]["line_bundle_sum_is_trivial"],
            str(spaces["serre_dual_cup_product_spaces"]["line_bundle_sum"]),
            "the three cup-product line bundles multiply to O_X",
        ),
        "cohomology_groups_recomputed": gate(
            all(
                item["cohomology"] == item["pycicy_recomputed_cohomology"]
                for item in [
                    spaces["component_selection_rule_spaces"]["fivebar_02_physical"],
                    spaces["component_selection_rule_spaces"]["five_24_physical"],
                    spaces["serre_dual_cup_product_spaces"]["five_24_cup_leg"],
                    spaces["serre_dual_cup_product_spaces"]["singlet_S_40_cup_leg"],
                ]
            )
            and spaces["serre_dual_cup_product_spaces"]["target"]["cohomology"][3] == 1,
            "pyCICY line_co recomputation",
            "all source cohomology dimensions and H3(O_X) are independently reproduced",
        ),
        "component_blocks_identified": gate(
            blocks["triplet_block"]["matrix_shape_after_singlet_vevs"] == [2, 1]
            and blocks["doublet_block"]["matrix_shape_after_singlet_vevs"] == [0, 1]
            and blocks["serre_dual_character_alignment"]["same_z2_multiplicities"],
            "Z2 component multiplicities",
            "triplet and doublet blocks are identified with the correct physical and cup legs",
        ),
        "doublet_rank_zero_certified": gate(
            blocks["doublet_block"]["rank_computed"]
            and blocks["doublet_block"]["rank"] == 0,
            "H1(L_02)_- dimension zero",
            "doublet mass block is rank zero for representation-theoretic dimension reasons",
        ),
        "triplet_rank_not_overclaimed": gate(
            not blocks["triplet_block"]["rank_computed"]
            and verdict["status"] == "unresolved_due_missing_cup_product_machinery",
            "local cup-product capability probe",
            "triplet rank is left unresolved rather than inferred from selection rules",
        ),
        "dangerous_operator_regression_fixed": gate(
            len(proton) == 10
            and all(item["forbidden_by_current_selection_rules"] for item in proton)
            and all(not item["neutral_under_S_U1_5"] for item in proton),
            "dangerous 10*5bar*5bar table",
            "all dangerous operators remain forbidden under the corrected physical H2 convention",
        ),
        "no_exposed_cup_api": gate(
            not capability["has_exposed_trilinear_cup_product_api"]
            and capability["single_map_is_equation_multiplication_hook"],
            "pyCICY method audit",
            "available pyCICY maps are line-cohomology/Koszul maps, not a trilinear mass map",
        ),
    }
    return {
        "title": "Lead q=1 Minimal Cup-Product Mass-Rank Probe",
        "scope": f"{EXPECTED_LABEL}: {EXPECTED_OPERATOR}",
        "status": verdict["status"],
        "candidate_label": dossier["candidate_identity"]["label"],
        "candidate_route": dossier["candidate_identity"]["route"],
        "candidate_matrix": dossier["candidate_identity"]["matrix"],
        "source_artifacts": {
            "dossier_json": str(dossier_json),
            "dossier_verification_json": str(dossier_verification_json),
            "split_json": str(split_json),
        },
        "exact_spaces": spaces,
        "component_mass_blocks": blocks,
        "cup_product_construction_attempt": {
            "constructed": "selection_rule_level_block_only",
            "cup_product_map_constructed": False,
            "available_machinery": capability,
            "missing_primitives": missing_primitives,
            "minimal_computation_to_upgrade": {
                "map": "H1(L_02)_+ x H1(L_24^*)_+ x H1(L_40)_+ -> H3(O_X)_+",
                "triplet_matrix_shape": [2, 1],
                "doublet_matrix_shape": [0, 1],
                "pass_condition": "triplet rank 1 and doublet rank 0",
                "current_known_rank": {
                    "triplet": None,
                    "doublet": 0,
                },
            },
        },
        "dangerous_operator_regression": {
            "count": len(proton),
            "all_forbidden": all(
                item["forbidden_by_current_selection_rules"] for item in proton
            ),
            "operators": proton,
        },
        "verdict": verdict,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    spaces = report["exact_spaces"]
    blocks = report["component_mass_blocks"]
    verdict = report["verdict"]
    cup = report["cup_product_construction_attempt"]
    lines = [
        "# Lead q=1 Minimal Cup-Product Mass-Rank Probe",
        "",
        f"Status: `{report['status']}`",
        f"Candidate: `{report['candidate_label']}`",
        f"Operator: `{spaces['operator']}`",
        "",
        "## Exact Cup Product",
        "",
        "The selection-rule `5` component is physical `H2(wedge2 V)`, but the cubic cup-product leg is its Serre-dual `H1(wedge2 V*)` representative.",
        "",
        f"- `5bar_02`: `{spaces['serre_dual_cup_product_spaces']['fivebar_02_cup_leg']['sector']}` with line `{spaces['serre_dual_cup_product_spaces']['fivebar_02_cup_leg']['line_bundle']}` and character `{spaces['serre_dual_cup_product_spaces']['fivebar_02_cup_leg']['actual_character']['multiplicities']}`",
        f"- `5_24` physical: `H2(wedge2 V)` with line `{spaces['component_selection_rule_spaces']['five_24_physical']['line_bundle']}` and character `{spaces['component_selection_rule_spaces']['five_24_physical']['actual_character']['multiplicities']}`",
        f"- `5_24` cup leg: `{spaces['serre_dual_cup_product_spaces']['five_24_cup_leg']['sector']}` with line `{spaces['serre_dual_cup_product_spaces']['five_24_cup_leg']['line_bundle']}` and character `{spaces['serre_dual_cup_product_spaces']['five_24_cup_leg']['actual_character']['multiplicities']}`",
        f"- `S_40`: `{spaces['serre_dual_cup_product_spaces']['singlet_S_40_cup_leg']['sector']}` with line `{spaces['serre_dual_cup_product_spaces']['singlet_S_40_cup_leg']['line_bundle']}` and character `{spaces['serre_dual_cup_product_spaces']['singlet_S_40_cup_leg']['actual_character']['multiplicities']}`",
        f"- target: `{spaces['serre_dual_cup_product_spaces']['target']['sector']}` with cohomology `{spaces['serre_dual_cup_product_spaces']['target']['cohomology']}`",
        f"- line-bundle sum: `{spaces['serre_dual_cup_product_spaces']['line_bundle_sum']}`",
        "",
        "## Blocks",
        "",
        f"- triplet block: shape `{blocks['triplet_block']['matrix_shape_after_singlet_vevs']}`, required rank `{blocks['triplet_block']['required_rank']}`, current rank `{blocks['triplet_block']['rank']}`",
        f"- doublet block: shape `{blocks['doublet_block']['matrix_shape_after_singlet_vevs']}`, required rank `{blocks['doublet_block']['required_rank']}`, current rank `{blocks['doublet_block']['rank']}`",
        f"- doublet reason: `{blocks['doublet_block']['rank_status']}`",
        "",
        "## Construction Attempt",
        "",
        f"- cup-product map constructed: `{cup['cup_product_map_constructed']}`",
        f"- constructed level: `{cup['constructed']}`",
        f"- pyCICY cup/ring methods found: `{cup['available_machinery']['named_cup_or_ring_methods']}`",
        "",
        "Missing primitives:",
        "",
        *[f"- {item}" for item in cup["missing_primitives"]],
        "",
        "## Verdict",
        "",
        f"- status: `{verdict['status']}`",
        f"- doublet block: `{verdict['doublet_block_verdict']}`",
        f"- triplet block: `{verdict['triplet_block_verdict']}`",
        f"- mass-rank verified: `{verdict['mass_rank_verified']}`",
        "",
        verdict["reason"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dossier-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.json"),
    )
    parser.add_argument(
        "--dossier-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_lead_candidate_dossier_verification.json"
        ),
    )
    parser.add_argument(
        "--split-json",
        default=str(REPORTS / "cicy5259_split_lift_report.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_mass_rank_probe.md"),
    )
    args = parser.parse_args()
    report = build_report(
        dossier_json=Path(args.dossier_json),
        dossier_verification_json=Path(args.dossier_verification_json),
        split_json=Path(args.split_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(
        "triplet_rank="
        f"{report['component_mass_blocks']['triplet_block']['rank']} "
        "doublet_rank="
        f"{report['component_mass_blocks']['doublet_block']['rank']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
