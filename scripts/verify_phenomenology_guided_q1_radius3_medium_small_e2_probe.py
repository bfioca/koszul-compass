#!/usr/bin/env python3
"""Verify the radius-3 medium-small E2 probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    regular_blocks = [
        record
        for record in report["records"]
        if any(rep["regular_multiplicity"] is not None for rep in record["actual"].values())
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side medium-small E2 gates passed",
        ),
        "ten_patterns_processed": gate(
            len(report["records"]) == 10,
            str(path),
            "all ten medium-small line patterns were processed",
        ),
        "some_regular_and_nonregular_content_seen": gate(
            0 < len(regular_blocks) < len(report["records"]),
            str(path),
            "the batch contains a mix of regular and nonregular resolved characters",
        ),
        "markdown_exposes_summary": gate(
            "Status: `medium_small_e2_characters_resolved`" in md_text
            and "actual" in md_text,
            str(md_path),
            "markdown exposes medium-small E2 results",
        ),
    }
    return {
        "scope": "verification for medium-priority radius-3 small-map E2 probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
