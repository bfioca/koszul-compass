#!/usr/bin/env python3
"""Verify the radius-5 charge-filter profile artifact."""

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


def build_verification(report_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = load_json(report_path)
    final = load_json(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.json")
    final_verification = load_json(
        REPORTS
        / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier_verification.json"
    )
    summary = report["summary"]
    weighted_buckets = summary["weighted_profile_buckets"]
    samples = report["nearest_miss_samples"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(report_path),
            "charge-profile builder-side gates passed",
        ),
        "anchored_to_verified_final_frontier": gate(
            final_verification["all_gates_pass"]
            and final["summary"]["viable_count"] == summary["final_frontier_viable_count"] == 0
            and summary["final_frontier_open_mass_bound_uncertainties"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier_verification.json"),
            "profile is anchored to the verified post-monoid no-viable radius-5 frontier",
        ),
        "no_viable_charge_profile": gate(
            report["status"] == "no_viable_charge_profile_in_indexed_radius5_certificates"
            and summary["viable_profile_count"] == 0
            and weighted_buckets.get("passes_charge_level_filter", 0) == 0,
            str(report_path),
            "no indexed q=1 certificate passes triplet mass, doublet protection, and proton suppression",
        ),
        "nearest_miss_buckets_present": gate(
            weighted_buckets.get("proton_safe_but_doublet_triplet_not_selective", 0) > 0
            and weighted_buckets.get("proton_safe_but_no_triplet_mass", 0) > 0
            and weighted_buckets.get("triplet_mass_but_dangerous_operator_allowed", 0) > 0,
            str(report_path),
            "profile separates the main radius-5 obstruction modes for next-surface targeting",
        ),
        "sample_records_have_charge_tables": gate(
            all(
                "mass_profile" in item
                and "proton_profile" in item
                and "classification" in item
                and "spectrum_certificate" in item
                for bucket in samples.values()
                for item in bucket
            ),
            str(report_path),
            "nearest-miss samples retain spectrum, mass, proton, and classification evidence",
        ),
        "markdown_written": gate(
            markdown_path.exists()
            and "Radius-5 Charge Filter Profile" in markdown_path.read_text(encoding="utf-8"),
            str(markdown_path),
            "markdown summary was emitted",
        ),
    }
    return {
        "scope": "verification for radius5 charge-level obstruction profile",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.json"),
    )
    parser.add_argument(
        "--markdown",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile_verification.json"),
    )
    args = parser.parse_args()
    verification = build_verification(Path(args.report), Path(args.markdown))
    out = Path(args.json_out)
    out.write_text(json.dumps(verification, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
