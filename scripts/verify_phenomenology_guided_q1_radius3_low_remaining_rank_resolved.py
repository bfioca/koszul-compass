#!/usr/bin/env python3
"""Verify the remaining low-priority rank-resolved pass."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_low_remaining_rank_resolved.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_low_remaining_rank_resolved.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side low remaining rank-resolution gates passed",
        ),
        "expected_summary": gate(
            report["summary"]["records"] == 15
            and report["summary"]["filled_blocks"] == 74
            and report["summary"]["remaining_unresolved_blocks"] == 0
            and report["summary"]["character_certified_records"] == 15
            and report["summary"]["viable_count"] == 0,
            str(path),
            "all fifteen low remaining records are certified and no viable candidate appears",
        ),
        "all_records_classified": gate(
            sum(report["summary"]["categories"].values()) == 15
            and "unresolved" not in report["summary"]["categories"],
            str(path),
            "all low remaining records have final non-unresolved classifications",
        ),
        "markdown_exposes_summary": gate(
            "Status: `no_viable_candidate_found_after_low_remaining_resolution`" in md_text
            and "filled_blocks: `74`" in md_text,
            str(md_path),
            "markdown exposes low remaining rank-resolved summary",
        ),
    }
    return {
        "scope": "verification for remaining low-priority rank-resolved pass",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_low_remaining_rank_resolved_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
