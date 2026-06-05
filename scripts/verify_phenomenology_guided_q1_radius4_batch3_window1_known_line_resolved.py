#!/usr/bin/env python3
"""Verify batch-3 window-1 radius-4 known-line resolution."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_batch3_known_line_resolved.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side batch-3 window-1 known-line gates passed",
        ),
        "all_unresolved_attempted": gate(
            report["summary"]["attempted_unresolved_records"] == 20
            and len(records) == 20,
            str(path),
            "all currently selected batch-3 unresolved records were attempted",
        ),
        "resolution_accounting_consistent": gate(
            report["summary"]["filled_blocks"]
            + report["summary"]["remaining_unresolved_blocks"]
            + report["summary"]["incompatible_known_actuals"]
            == 86
            and report["summary"]["filled_blocks"] == 38
            and report["summary"]["remaining_unresolved_blocks"] == 30
            and report["summary"]["incompatible_known_actuals"] == 18
            and report["summary"]["viable_count"]
            == sum(
                1
                for record in records
                if record["classification"]["category"] == "viable"
            ),
            str(path),
            "all combined missing character block outcomes are accounted as filled, unresolved, or incompatible",
        ),
        "required_sections_present": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in records
            ),
            str(path),
            "filtered record contains required deliverable sections",
        ),
        "markdown_exposes_result": gate(
            "Status:" in md_text
            and "attempted_unresolved_records: `20`" in md_text
            and "Candidate Classifications" in md_text,
            str(md_path),
            "markdown exposes the known-line resolution result",
        ),
    }
    return {
        "scope": "verification for selected batch-3 known-line resolution",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_known_line_resolved_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
