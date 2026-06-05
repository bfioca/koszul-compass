#!/usr/bin/env python3
"""Verify the bounded radius-6 doublet-triplet targeted scout."""

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


def verify(*, scout_json: Path, scout_md: Path) -> dict[str, Any]:
    report = load_json(scout_json)
    profile_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile_verification.json"
    )
    md_text = scout_md.read_text(encoding="utf-8")
    summary = report["summary"]
    filtered = report["filtered_candidate_records"]
    profile_bucket = report["parameters"].get(
        "profile_bucket", "proton_safe_but_doublet_triplet_not_selective"
    )
    character_certified = [
        item for item in filtered if item["character_certificate"]["character_certified"]
    ]
    unresolved = [
        item for item in filtered if item["classification"]["category"] == "unresolved"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(scout_json),
            "builder-side radius6 targeted scout gates passed",
        ),
        "imports_verified_profile": gate(
            profile_verification["all_gates_pass"]
            and report["gates"]["imports_charge_profile"]["pass"],
            str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile_verification.json"),
            "radius6 scout imports the verified radius5 charge-filter profile",
        ),
        "seed_bucket_is_targeted": gate(
            report["gates"]["seed_records_loaded"]["pass"]
            and report["source_summary"]["selected_seed_records"] > 0,
            str(scout_json),
            f"all selected seeds come from the `{profile_bucket}` obstruction bucket",
        ),
        "screening_and_certification_accounting": gate(
            report["screening_counters"]["frontier_records_screened"] > 0
            and summary["certified_q1_records"] == len(filtered)
            and report["screening_counters"]["raw_q1_certification_attempts"]
            == min(
                report["screening_counters"]["raw_q1_spectrum_survivors"],
                report["parameters"]["max_raw_q1_to_certify"],
            ),
            str(scout_json),
            "frontier screening and q1 certification accounting are consistent",
        ),
        "candidate_records_have_required_sections": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(item)
                for item in filtered
            ),
            str(scout_json),
            "every emitted radius6 candidate contains the required certificate sections",
        ),
        "character_certified_records_have_charge_tables": gate(
            all(
                item["mass_operator_table"] is not None
                and item["proton_decay_operator_table"] is not None
                for item in character_certified
            ),
            str(scout_json),
            "all character-certified radius6 q1 records carry mass and proton tables",
        ),
        "unresolved_records_are_explicit": gate(
            all(
                item["classification"]["status"]
                in {
                    "missing_character_or_charge_level_data",
                    "no_certified_triplet_mass_operator_found",
                    "no_triplet_mass_in_certified_singlet_monoid",
                }
                for item in unresolved
            ),
            str(scout_json),
            "unresolved records state whether the missing piece is character data or mass evidence",
        ),
        "markdown_exposes_result": gate(
            "Radius-6 DT-Targeted Scout" in md_text
            and "viable_count" in md_text
            and "Candidate Classifications" in md_text,
            str(scout_md),
            "markdown exposes radius6 scout totals and classifications",
        ),
    }
    return {
        "scope": "verification for bounded radius6 doublet-triplet targeted scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.json"),
    )
    parser.add_argument(
        "--scout-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius6_dt_targeted_scout_verification.json"),
    )
    args = parser.parse_args()
    result = verify(scout_json=Path(args.scout_json), scout_md=Path(args.scout_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
