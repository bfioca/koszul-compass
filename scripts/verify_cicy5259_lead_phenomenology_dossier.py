#!/usr/bin/env python3
"""Verify the CICY 5259/7914 lead phenomenology dossier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


EXPECTED_MATRIX = [
    [-1, 1, 1, 0, -1],
    [0, -1, 0, 0, 1],
    [0, 1, 0, -1, 0],
    [0, 1, -1, -1, 1],
    [1, 1, 0, -1, -1],
    [0, -1, 0, 1, 0],
    [0, 0, 0, 0, 0],
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    path = REPORTS / "cicy5259_lead_phenomenology_dossier.json"
    md_path = REPORTS / "cicy5259_lead_phenomenology_dossier.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    identity = report["candidate_identity"]
    wilson = report["wilson_line_decomposition"]
    inventory = report["charged_matter_inventory"]
    singlets = report["singlet_moduli_inventory"]
    mass = report["vectorlike_mass_analysis"]
    proton = report["proton_decay_and_residual_symmetry"]
    classification = report["classification"]
    dossier_gates = report["gates"]

    mass_04 = next(
        item
        for item in mass["candidate_mass_operators"]
        if item["fivebar"] == "5bar_04" and item["five"] == "5_14"
    )
    dangerous = proton["dimension_four_su5_operator_10_5bar_5bar"]

    verification_gates = {
        "classification_is_obstructed_not_mssm_like": gate(
            classification["category"] == "phenomenologically obstructed"
            and classification["status"]
            == "phenomenologically_obstructed_by_current_charge_level_evidence"
            and "no charge-level distinction between triplet and doublet vectorlike mass terms"
            in classification["not_mssm_like_after_vectorlike_mass_lifting_because"]
            and "dimension-four 10*5bar*5bar operator is not forbidden by line-bundle charges or Z2"
            in classification["not_mssm_like_after_vectorlike_mass_lifting_because"],
            str(path),
            "dossier classifies the frozen target as obstructed by charge-level Higgs/triplet and proton-decay evidence",
        ),
        "frozen_candidate_identity_matches_q1_target": gate(
            identity["matrix"] == EXPECTED_MATRIX
            and identity["anomaly"] == [14, 16, 4, 12, 16, 26, 21]
            and identity["cohomology"]["V"] == [0, 6, 0, 0]
            and identity["cohomology"]["V_dual"] == [0, 0, 6, 0]
            and identity["cohomology"]["wedge2_V"] == [0, 8, 2, 0]
            and identity["cohomology"]["wedge2_V_dual"] == [0, 2, 8, 0]
            and identity["vectorlike_prediction"][
                "h2_wedge2_regular_multiplicity"
            ]
            == 1,
            str(path),
            "candidate identity is the frozen 5259/7914 q=1 target",
        ),
        "certification_scope_is_explicit": gate(
            "7914" in report["certification_scope"]["relation_to_5259_route"]
            and "5259" in report["certification_scope"]["relation_to_5259_route"]
            and "Z2 cohomology character decompositions for V, V*, wedge2 V, wedge2 V*"
            in report["certification_scope"][
                "certified_in_favourable_7914_split_presentation"
            ],
            str(path),
            "dossier states that certification is in the favourable 7914 split presentation and relates it to the 5259 route",
        ),
        "wilson_line_components_are_decomposed": gate(
            wilson["ten_sector"]["three_family_10_sector"]
            and wilson["fivebar_sector"]["dbar_triplets"] == 4
            and wilson["fivebar_sector"]["lepton_doublets"] == 4
            and wilson["five_sector"]["triplets"] == 1
            and wilson["five_sector"]["doublets"] == 1
            and wilson["net_and_vectorlike"]["net_dbar_families"] == 3
            and wilson["net_and_vectorlike"]["net_lepton_doublet_families"] == 3
            and wilson["net_and_vectorlike"]["colored_triplet_vectorlike_pairs"]
            == 1
            and wilson["net_and_vectorlike"][
                "electroweak_doublet_vectorlike_pairs"
            ]
            == 1,
            str(path),
            "Wilson-line decomposition records three families plus one triplet and one doublet vectorlike pair",
        ),
        "charged_matter_sources_are_labelled": gate(
            [item["label"] for item in inventory["ten"]] == ["10_1", "10_4"]
            and [item["label"] for item in inventory["fivebar"]]
            == ["5bar_04", "5bar_23"]
            and [item["label"] for item in inventory["five"]] == ["5_14"],
            str(path),
            "charged matter inventory records the summand labels that enter mass and proton-decay operators",
        ),
        "certified_singlets_support_a_mass_operator": gate(
            singlets["certified_h1_singlet_charge_labels"]
            == ["e1-e4", "e3-e0", "e4-e0", "e4-e2"]
            and mass_04["bilinear_charge"]["label"] == "e0-e1"
            and mass_04["needed_singlet_charge"]["label"] == "-e0+e1"
            and mass_04["certified_singlet_monomial_hits"][0][
                "singlet_monomial"
            ]
            == ["e1-e4", "e4-e0"]
            and not mass["cup_product_status"]["computed"],
            str(path),
            "certified singlet charges allow a 5bar_04 x 5_14 mass monomial, but cup-product ranks are not computed",
        ),
        "no_selective_doublet_triplet_protection_claimed": gate(
            dossier_gates["no_doublet_triplet_selection_rule_found"]["pass"]
            and "does not protect exactly one light Higgs doublet pair"
            in mass["charge_level_result"],
            str(path),
            "dossier does not overclaim selective triplet lifting with one protected Higgs doublet pair",
        ),
        "dangerous_operator_is_not_forbidden": gate(
            dangerous["example"] == "10_1 * 5bar_04 * 5bar_23"
            and dangerous["charge"]["coefficients"] == [1, 1, 1, 1, 1]
            and dangerous["neutral_under_S_U1_5"]
            and dossier_gates["dangerous_operator_not_forbidden"]["pass"],
            str(path),
            "dossier records a line-bundle-neutral dangerous 10*5bar*5bar operator",
        ),
        "markdown_matches_dossier": gate(
            "Classification: `phenomenologically obstructed`" in md_text
            and "5bar_04 x 5_14" in md_text
            and "10_1 * 5bar_04 * 5bar_23" in md_text
            and "does not protect exactly one light Higgs doublet pair" in md_text,
            str(md_path),
            "markdown exposes classification, mass-term evidence, and proton-decay evidence",
        ),
    }
    return {
        "scope": "verification for CICY5259/7914 lead phenomenology dossier",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_lead_phenomenology_dossier_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
