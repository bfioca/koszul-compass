#!/usr/bin/env python3
"""Verify the radius-3 small-map rank probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_small_map_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    d1 = report["first_page_map"]["split"]
    d3 = report["higher_map"]["split"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side small-map probe gates passed",
        ),
        "target_line_and_dual_recorded": gate(
            report["line_bundle"] == [0, 2, 0, 2, -1, -1, 0]
            and report["dual_line_bundle"] == [0, -2, 0, -2, 1, 1, 0],
            str(path),
            "probe records the target line and Serre-dual line",
        ),
        "rank_splits_match": gate(
            d1["rank_total"] == 8
            and d1["rank_plus"] == 4
            and d1["rank_minus"] == 4
            and d3["rank_total"] == 0
            and d3["rank_plus"] == 0
            and d3["rank_minus"] == 0,
            str(path),
            "first-page and higher-map rank splits match the expected small-map resolution",
        ),
        "characters_regular": gate(
            report["resolved_characters"]["H1"]["regular_multiplicity"] == 1
            and report["resolved_characters"]["H2"]["regular_multiplicity"] == 1,
            str(path),
            "resolved H1 and H2 are regular Z2 representations",
        ),
        "markdown_exposes_summary": gate(
            "Status: `small_map_line_resolves_to_regular_h1_h2`" in md_text
            and "resolved characters" in md_text,
            str(md_path),
            "markdown exposes small-map result",
        ),
    }
    return {
        "scope": "verification for radius-3 small-map rank probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_small_map_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
