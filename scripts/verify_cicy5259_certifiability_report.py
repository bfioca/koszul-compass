#!/usr/bin/env python3
"""Verify the CICY 5259 certifiability upgrade report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def verify() -> dict[str, Any]:
    report = load_json("cicy5259_certifiability_upgrade_report.json")
    scout = load_json("nonfavourable_ambient_restricted_scout.json")
    audit = load_json("nonfavourable_free_capability_audit.json")
    md_text = (REPORTS / "cicy5259_certifiability_upgrade_report.md").read_text(
        encoding="utf-8"
    )

    hit = next(record for record in scout["best_spectrum_records"] if record["cicy"] == 5259)
    target_audit = next(item for item in audit["targets"] if item["num"] == 5259)
    hit_spectrum = hit["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    hit_quality = hit["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    quantity = report["quantity_status"]

    gates = {
        "metadata_and_rank_defect": gate(
            report["metadata"]["num"] == 5259
            and report["metadata"]["h11"] == 7
            and report["metadata"]["num_projective_factors"] == 6
            and report["conclusion"]["rank_defect_h11_minus_num_projective_factors"]
            == 1
            and target_audit["rank_defect_h11_minus_num_projective_factors"] == 1,
            "reports/cicy5259_certifiability_upgrade_report.json",
            "CICY5259 rank defect is one",
        ),
        "pycicy_cross_check_recorded": gate(
            report["pycicy_probe"]["available"]
            and report["pycicy_probe"]["h11_matches_metadata"]
            and report["pycicy_probe"]["h21_matches_metadata"]
            and report["pycicy_probe"]["second_chern_matches_raw_ambient_c2"]
            and report["pycicy_probe"]["ambient_triple_intersection_matches_helper"]
            and report["pycicy_probe"]["zero_bundle_matches_calabi_yau_expectation"],
            "reports/cicy5259_certifiability_upgrade_report.json",
            "pyCICY cross-checks ambient hodge/c2/intersection/cohomology data",
        ),
        "ambient_breadcrumb_matches_scout": gate(
            report["ambient_restricted_breadcrumb"]["index_v"]
            == hit["ambient_restricted_index_v"]
            == -6
            and report["ambient_restricted_breadcrumb"]["index_wedge2_v"]
            == hit["ambient_restricted_index_wedge2_v"]
            == -6
            and report["ambient_restricted_breadcrumb"]["anomaly"] == hit["anomaly"]
            and report["ambient_restricted_breadcrumb"]["spectrum"]["upstairs_10"]
            == hit_spectrum["upstairs_10"]
            == 6
            and report["ambient_restricted_breadcrumb"]["spectrum"][
                "upstairs_anti_10"
            ]
            == hit_spectrum["upstairs_anti_10"]
            == 0
            and report["ambient_restricted_breadcrumb"]["quality"][
                "regular_nontrivial_summand_scan_style"
            ]
            == hit_quality["regular_nontrivial_summand_scan_style"]
            == True,
            "reports/nonfavourable_ambient_restricted_scout.json",
            "ambient-restricted CICY5259 breadcrumb matches scout evidence",
        ),
        "missing_full_geometry_recorded": gate(
            quantity["full_picard_divisor_basis"]["status"] == "missing"
            and quantity["full_h11_intersection_tensor"]["status"] == "missing"
            and quantity["full_h11_c2_tx"]["status"] == "missing"
            and quantity["full_kahler_mori_cone"]["status"] == "missing"
            and quantity["symmetry_action_on_full_picard_basis"]["status"]
            == "missing"
            and quantity["equivariant_cohomology_characters"]["status"] == "missing",
            "reports/cicy5259_certifiability_upgrade_report.json",
            "full non-favourable geometry and Wilson-line character blockers are explicit",
        ),
        "trust_boundary_present": gate(
            "ambient restricted triple intersections"
            in report["trust_classification"]["trustworthy_now"]
            and "treating ambient c2/anomaly as full anomaly"
            in report["trust_classification"]["suggestive_only"]
            and not report["conclusion"]["full_nonfavourable_candidate_certified"]
            and report["conclusion"]["ambient_restricted_breadcrumb_certified"],
            "reports/cicy5259_certifiability_upgrade_report.json",
            "report distinguishes ambient-certified facts from suggestive-only use",
        ),
        "markdown_summary_present": gate(
            "Status: `partial_ambient_certification_layer_only`" in md_text
            and "spectrum 10/anti10/5bar/5: 6/0/16/10" in md_text
            and "full Picard/divisor basis for CICY5259" in md_text,
            "reports/cicy5259_certifiability_upgrade_report.md",
            "markdown report summarizes status, spectrum, and missing Picard basis",
        ),
    }
    return {
        "scope": "verification for CICY5259 certifiability upgrade report",
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy5259_certifiability_upgrade_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"all_gates_pass={result['all_gates_pass']}")
    print(f"json_out={out}")
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
