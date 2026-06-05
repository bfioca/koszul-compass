#!/usr/bin/env python3
"""Verify the non-favourable recorded-free extension report."""

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
    audit = load_json("nonfavourable_free_capability_audit.json")
    scout = load_json("nonfavourable_ambient_restricted_scout.json")
    report = load_json("nonfavourable_extension_report.json")
    cicy2544 = load_json("outside_regime_higgs_candidate_certificate.json")
    cicy7484 = load_json("best_candidate_certificate.json")
    md_text = (REPORTS / "nonfavourable_extension_report.md").read_text(
        encoding="utf-8"
    )

    best_hit = scout["best_spectrum_records"][0]
    hit_spectrum = best_hit["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    hit_quality = best_hit["cohomology_and_spectrum"]["line_bundle_sum_quality"]

    gates = {
        "capability_audit_covers_all_targets": gate(
            audit["conclusion"]["target_count"] == 62
            and len(audit["targets"]) == 62
            and audit["conclusion"]["full_nonfavourable_certifiable_target_count"]
            == 0
            and audit["conclusion"]["ambient_restricted_scoutable_target_count"]
            == 62,
            "reports/nonfavourable_free_capability_audit.json",
            "all 62 recorded-free non-favourable targets audited; none full-certifiable now",
        ),
        "cohomology_probe_succeeded_for_all_targets": gate(
            all(
                item["line_bundle_cohomology_interface"]["available"] is True
                and item["line_bundle_cohomology_interface"][
                    "zero_bundle_matches_calabi_yau_expectation"
                ]
                for item in audit["targets"]
            ),
            "reports/nonfavourable_free_capability_audit.json",
            "ambient-restricted pyCICY zero-bundle probe succeeded on every target",
        ),
        "small_scout_deterministic_counts": gate(
            scout["search"]["target_nums"] == [4185, 5259, 4078]
            and scout["search"]["samples_per_target"] == 10000
            and scout["search"]["algebraic_survivor_count"] == 1609
            and scout["search"]["slope_checked_count"] == 60
            and scout["search"]["slope_feasible_count"] == 1
            and scout["search"]["spectrum_pass_count"] == 1,
            "reports/nonfavourable_ambient_restricted_scout.json",
            "ambient-restricted scout produced the expected deterministic counts",
        ),
        "cicy5259_hit_has_expected_ambient_gates": gate(
            best_hit["cicy"] == 5259
            and best_hit["ambient_restricted_index_v"] == -6
            and best_hit["ambient_restricted_index_wedge2_v"] == -6
            and all(value >= 0 for value in best_hit["anomaly"])
            and best_hit["passes_ambient_restricted_slope_gate"]
            and best_hit["passes_upstairs_spectrum_gate"]
            and hit_spectrum["upstairs_10"] == 6
            and hit_spectrum["upstairs_anti_10"] == 0
            and hit_spectrum["upstairs_5bar"] == 16
            and hit_spectrum["upstairs_5"] == 10
            and hit_quality["regular_nontrivial_summand_scan_style"],
            "reports/nonfavourable_ambient_restricted_scout.json",
            "CICY5259 ambient-restricted breadcrumb passes sampled hard gates",
        ),
        "extension_report_conclusion_matches_evidence": gate(
            report["conclusion"]["status"]
            == "no_full_nonfavourable_quotient_candidate_yet"
            and not report["conclusion"]["candidate_found"]
            and report["conclusion"]["ambient_restricted_breadcrumb_found"]
            and all(item["pass"] for item in report["gate_checklist"].values()),
            "reports/nonfavourable_extension_report.json",
            "extension report records no full candidate and one ambient-restricted breadcrumb",
        ),
        "anchor_comparison_preserved": gate(
            report["ranked_comparison"][1]["spectrum"] == cicy2544["spectrum"]
            and report["ranked_comparison"][2]["spectrum"] == cicy7484["spectrum"]
            and report["ranked_comparison"][2]["full_quotient_certificate"] is True,
            "reports/nonfavourable_extension_report.json",
            "ranked comparison preserves CICY2544 and CICY7484 anchor evidence",
        ),
        "markdown_summary_present": gate(
            "targets audited: 62" in md_text
            and "CICY 5259" in md_text
            and "full non-favourable certifiable now: 0" in md_text,
            "reports/nonfavourable_extension_report.md",
            "markdown report includes target count, CICY5259 breadcrumb, and blocker count",
        ),
    }
    return {
        "scope": "verification for non-favourable recorded-free extension report",
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "nonfavourable_extension_report_verification.json"),
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
