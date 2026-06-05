#!/usr/bin/env python3
"""Verify the radius-3 sign-conflict probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side sign-conflict gates passed",
        ),
        "line_and_dual_recorded": gate(
            report["line_bundle"] == [-1, 2, 0, 1, 1, -1, 0]
            and report["dual_line_bundle"] == [1, -2, 0, -1, -1, 1, 0],
            str(path),
            "probe records the unresolved line and Serre-dual line",
        ),
        "conflict_is_explicit": gate(
            report["conflicts"]
            == [
                {
                    "first_page_requires": [-1],
                    "higher_map_requires": [1],
                    "naive_target_sign": -1,
                    "target_row": 0,
                }
            ],
            str(path),
            "the target-row sign conflict is explicit and reproducible",
        ),
        "markdown_exposes_conflict": gate(
            "Status: `character_certificate_blocked_by_sign_constraint_conflict`"
            in md_text
            and "conflicts:" in md_text,
            str(md_path),
            "markdown exposes conflict summary",
        ),
    }
    return {
        "scope": "verification for radius-3 sign-conflict probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
