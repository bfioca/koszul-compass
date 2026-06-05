#!/usr/bin/env python3
"""Verify the radius-3 unresolved frontier audit."""

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


def verify() -> dict[str, Any]:
    path = REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["records"]
    no_mass = [
        record
        for record in records
        if record["audit"]["kind"] == "certified_record_without_triplet_mass"
    ]
    missing = [
        record
        for record in records
        if record["audit"]["kind"] == "missing_character_or_charge_level_data"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side audit gates passed",
        ),
        "all_unresolved_records_present": gate(
            len(records) == 34
            and report["summary"]["unresolved_records"] == 34
            and len(missing) == 32
            and len(no_mass) == 2,
            str(path),
            "audit contains the full unresolved frontier split into missing-character and no-mass records",
        ),
        "no_mass_records_strengthened": gate(
            all(
                record["audit"]["recommended_classification"]
                == "phenomenologically obstructed"
                and record["audit"]["recommended_status"]
                == "no_triplet_mass_in_certified_singlet_monoid"
                for record in no_mass
            ),
            str(path),
            "both character-certified no-mass records are strengthened to obstruction",
        ),
        "missing_blocks_recorded": gate(
            report["summary"]["missing_character_block_count"] > 0
            and report["summary"]["unique_missing_block_patterns"] > 0
            and all(
                record["audit"]["missing_character_block_count"] > 0
                for record in missing
            ),
            str(path),
            "missing-character records include explicit unresolved line-block data",
        ),
        "priority_buckets_present": gate(
            "high_priority_q1_or_adjacent_small_map"
            in report["summary"]["priority_buckets"]
            and report["summary"]["trace_feasible_missing_character_records"] >= 1,
            str(path),
            "audit identifies trace-feasible high-priority unresolved records",
        ),
        "markdown_exposes_summary": gate(
            "Status: `radius3_unresolved_frontier_triaged`" in md_text
            and "unresolved_records: `34`" in md_text
            and "Common Missing Blocks" in md_text,
            str(md_path),
            "markdown exposes the audit summary and common missing blocks",
        ),
    }
    return {
        "scope": "verification for radius-3 unresolved frontier audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
