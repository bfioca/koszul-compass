#!/usr/bin/env python3
"""Verify the high-priority radius-3 rank-resolution pass."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    certified = [
        record
        for record in records
        if record["character_certificate"]["character_certified"]
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side high-priority rank-resolution gates passed",
        ),
        "expected_records_and_blocks": gate(
            report["summary"]["high_priority_records"] == 4
            and report["summary"]["filled_blocks"] == 6
            and report["summary"]["remaining_unresolved_blocks"] == 2,
            str(path),
            "four audited high-priority records were attempted and verified projected/small-map/large-E2 blocks were filled",
        ),
        "certified_records_no_viable": gate(
            report["summary"]["character_certified_records"] == len(certified) == 3
            and report["summary"]["desired_q1_records"] == 3
            and report["summary"]["viable_count"] == 0
            and all(record["classification"]["category"] != "viable" for record in records),
            str(path),
            "known rank data certifies three desired-q1 records and none is viable",
        ),
        "required_sections_exist": gate(
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
            "every high-priority record emits required deliverable sections",
        ),
        "markdown_exposes_summary": gate(
            "Status: `no_viable_candidate_found_after_known_rank_resolution`" in md_text
            and "filled_blocks: `6`" in md_text
            and "character_certified_records: `3`" in md_text,
            str(md_path),
            "markdown exposes rank-resolution summary",
        ),
    }
    return {
        "scope": "verification for high-priority radius-3 rank-resolution pass",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_high_priority_rank_resolved_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
