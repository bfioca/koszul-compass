#!/usr/bin/env python3
"""Verify the frozen lead q=1 candidate dossier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify(report_json: Path, report_md: Path, expected_label: str) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    if report["status"] == "lead_candidate_blocked_representative_prefilter_no_compatible_target":
        summary = report["representative_prefilter_summary"]
        gates = {
            "builder_gates_pass": gate(
                report.get("all_gates_pass")
                and all(item.get("pass") for item in report.get("gates", {}).values()),
                str(report_json),
                "builder-side blocked dossier gates passed",
            ),
            "lead_promotion_blocked": gate(
                not report["promotion_policy"]["lead_dossier_allowed"]
                and not report["promotion_policy"]["cup_product_planning_allowed"]
                and report["classification"]["current"]["status"]
                == "representative_prefilter_blocks_all_shadow_survivors",
                str(report_json),
                "lead and cup-product promotion are blocked without representative compatibility",
            ),
            "summary_matches_closed_prefilter": gate(
                summary["character_shadow_viable_weight"] == 1962
                and summary["representative_obstructed_weight"] == 1962
                and summary["representative_compatible_weight"] == 0
                and summary["representative_unresolved_weight"] == 0
                and summary["cup_product_eligible_weight"] == 0,
                str(report_json),
                "blocked dossier imports the closed representative-prefilter frontier",
            ),
            "markdown_exposes_block": gate(
                "Status: `lead_candidate_blocked_representative_prefilter_no_compatible_target`"
                in md_text
                and "lead dossier allowed: `False`" in md_text
                and "cup-product planning allowed: `False`" in md_text,
                str(report_md),
                "markdown exposes blocked lead promotion",
            ),
        }
        return {
            "scope": "verification for representative-prefilter-blocked lead candidate dossier",
            "all_gates_pass": all(item["pass"] for item in gates.values()),
            "gates": gates,
        }

    identity = report["candidate_identity"]
    spectrum = report["spectrum_and_character_certificate"]
    reconstructed = spectrum["reconstructed_wilson_line_spectrum"]
    mass = report["mass_operator_table"]
    hits = mass["triplet_only_hits"]
    proton = report["dangerous_operator_table"]
    cup = report["cup_product_frontier"]
    gates = {
        "builder_gates_pass": gate(
            report.get("all_gates_pass")
            and all(item.get("pass") for item in report.get("gates", {}).values()),
            str(report_json),
            "builder-side dossier gates passed",
        ),
        "expected_lead_frozen": gate(
            identity["label"] == expected_label
            and report["classification"]["current"]["category"] == "viable",
            str(report_json),
            "dossier freezes the expected refined viable lead candidate",
        ),
        "spectrum_is_q1": gate(
            reconstructed["ten_sector"]["three_family_10_sector"]
            and reconstructed["net_and_vectorlike"]["net_dbar_families"] == 3
            and reconstructed["net_and_vectorlike"]["net_lepton_doublet_families"] == 3
            and reconstructed["net_and_vectorlike"]["colored_triplet_vectorlike_pairs"] == 1
            and reconstructed["net_and_vectorlike"]["electroweak_doublet_vectorlike_pairs"] == 1
            and spectrum["spectrum_certificate"]["desired_q1_three_family_signature"],
            str(report_json),
            "Wilson-line reconstruction gives three families plus one vectorlike 5/5bar pair",
        ),
        "characters_are_certified": gate(
            spectrum["character_certificate"]["character_certified"]
            and all(
                sector["all_characters_computed"]
                for sector in spectrum["character_certificate"]["characters"].values()
            ),
            str(report_json),
            "all character sectors in the dossier are computed",
        ),
        "triplet_only_mass_frontier": gate(
            len(hits) >= 1
            and all(hit["triplet_pair_support"] > 0 for hit in hits)
            and all(hit["doublet_pair_support"] == 0 for hit in hits)
            and not any(
                item["doublet_mass_allowed_by_refined_selection_rules"]
                for item in mass["all_refined_entries"]
            ),
            str(report_json),
            "refined mass table has triplet support and no doublet-support mass entry",
        ),
        "physical_five_uses_h2_wedge": gate(
            all(hit["five_space"]["sector"] == "H2(wedge2 V)" for hit in hits)
            and all(
                item["five_component_character_source"] == "H2(wedge2 V)"
                for item in mass["all_refined_entries"]
            ),
            str(report_json),
            "mass frontier uses H2(wedge2 V) for physical 5 component characters",
        ),
        "dangerous_operators_all_forbidden": gate(
            len(proton) > 0
            and all(item["forbidden_by_current_selection_rules"] for item in proton)
            and all(not item["neutral_under_S_U1_5"] for item in proton),
            str(report_json),
            "all enumerated 10*5bar*5bar operators are non-neutral and forbidden",
        ),
        "cup_frontier_is_explicit": gate(
            cup["status"] == "pending_cup_product_mass_rank"
            and len(cup["maps_to_compute"]) == len(hits)
            and cup["current_selection_rule_dimension_check"][
                "candidate_vectorlike_triplet_pairs"
            ]
            == 1
            and cup["current_selection_rule_dimension_check"][
                "candidate_vectorlike_doublet_pairs"
            ]
            == 1
            and "actual nonzero cup/product coefficients for the triplet mass blocks"
            in cup["certified_vs_pending"]["pending"],
            str(report_json),
            "cup-product frontier records maps, rank conditions, and pending assumptions",
        ),
        "markdown_exposes_dossier": gate(
            f"label: `{expected_label}`" in md_text
            and "## Cup-Product Frontier" in md_text
            and "not claimed: `full MSSM model`" in md_text,
            str(report_md),
            "markdown exposes identity, cup frontier, and classification boundary",
        ),
    }
    return {
        "scope": "verification for frozen lead q=1 candidate dossier",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier.md"),
    )
    parser.add_argument(
        "--expected-label",
        default="radius6_broad_adjacency_filtered_4_branch_18",
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_lead_candidate_dossier_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify(
        report_json=Path(args.report_json),
        report_md=Path(args.report_md),
        expected_label=args.expected_label,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
