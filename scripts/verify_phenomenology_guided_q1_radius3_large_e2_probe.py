#!/usr/bin/env python3
"""Verify the large radius-3 E2 probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    expected = {
        "H1": {
            "dimension": 2,
            "multiplicities": {"+": 1, "-": 1},
            "nonidentity_trace": 0,
            "regular_multiplicity": 1,
        },
        "H2": {
            "dimension": 2,
            "multiplicities": {"+": 1, "-": 1},
            "nonidentity_trace": 0,
            "regular_multiplicity": 1,
        },
    }
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side large E2 gates passed",
        ),
        "line_and_dual_recorded": gate(
            report["line_bundle"] == [2, 0, 3, 0, 0, -1, -1]
            and report["dual_line_bundle"] == [-2, 0, -3, 0, 0, 1, 1],
            str(path),
            "probe records the large line and Serre-dual line",
        ),
        "regular_characters_recorded": gate(
            report["resolved_characters"] == expected
            and all(record["actual"] == expected for record in report["records"]),
            str(path),
            "line and dual both resolve to regular H1 and H2",
        ),
        "markdown_exposes_summary": gate(
            "Status: `large_line_and_dual_resolve_to_regular_h1_h2`" in md_text
            and "resolved characters" in md_text,
            str(md_path),
            "markdown exposes large E2 result",
        ),
    }
    return {
        "scope": "verification for large radius-3 E2 probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
