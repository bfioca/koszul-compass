#!/usr/bin/env python3
"""Verify three-term E2 character probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "three-term E2 builder gates pass",
        ),
        "four_lines_resolved": gate(
            len(report["records"]) == 4
            and all(record["actual"] for record in report["records"]),
            str(path),
            "all four remaining line/dual three-term blocks have actual characters",
        ),
        "maps_block_diagonal": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in report["records"]),
            str(path),
            "all three-term first-page maps preserve eigenspaces",
        ),
        "markdown_matches_report": gate(
            "Status: `three_term_medium_characters_resolved`" in md_text
            and "[1, -1, 2, -1, 1, -1, 1]" in md_text
            and "'regular_multiplicity': 2" in md_text,
            str(md_path),
            "markdown exposes resolved three-term characters",
        ),
    }
    return {
        "scope": "verification for three-term E2 character probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_three_term_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
