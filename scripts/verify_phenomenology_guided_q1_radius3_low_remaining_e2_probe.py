#!/usr/bin/env python3
"""Verify the remaining low-priority singleton E2 probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side low remaining E2 gates passed",
        ),
        "expected_coverage": gate(
            len(report["records"]) == 46
            and len(report["fully_covered_low_records"]) == 15,
            str(path),
            "forty-six singleton patterns cover fifteen remaining low-priority records",
        ),
        "actuals_present": gate(
            all(record["actual"] for record in report["records"]),
            str(path),
            "all singleton patterns have actual character records",
        ),
        "markdown_exposes_summary": gate(
            "Status: `low_remaining_e2_characters_resolved`" in md_text
            and "fully covered low records: `15`" in md_text,
            str(md_path),
            "markdown exposes low remaining E2 summary",
        ),
    }
    return {
        "scope": "verification for remaining low-priority singleton E2 probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
