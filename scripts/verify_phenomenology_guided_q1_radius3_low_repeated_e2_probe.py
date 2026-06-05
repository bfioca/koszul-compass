#!/usr/bin/env python3
"""Verify the low-priority repeated-pattern E2 probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side low repeated E2 gates passed",
        ),
        "expected_coverage": gate(
            len(report["records"]) == 18
            and len(report["fully_covered_low_records"]) == 6,
            str(path),
            "eighteen repeated patterns cover six low-priority records",
        ),
        "actuals_present": gate(
            all(record["actual"] for record in report["records"]),
            str(path),
            "all repeated patterns have actual character records",
        ),
        "markdown_exposes_summary": gate(
            "Status: `low_repeated_e2_characters_resolved`" in md_text
            and "fully covered low records: `6`" in md_text,
            str(md_path),
            "markdown exposes low repeated E2 summary",
        ),
    }
    return {
        "scope": "verification for low-priority repeated-pattern E2 probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
