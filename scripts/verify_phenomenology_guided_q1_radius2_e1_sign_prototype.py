#!/usr/bin/env python3
"""Verify representative E1 Z2 basis-sign reconstruction."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.md"
    scenarios_path = REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"
    report = load_json(path)
    scenarios = load_json(scenarios_path)
    md_text = md_path.read_text(encoding="utf-8")
    expected = scenarios["records"][0]["block_summaries"][0]["source_totals"]
    entries = report["entries"]
    total_reps = report["total_degree_representations"]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "E1 sign-prototype builder gates pass",
        ),
        "representative_block_matches_scenario_frontier": gate(
            scenarios["records"][0]["label"] == "radius2_enhanced_backlog_0"
            and report["representative_line"]
            == scenarios["records"][0]["block_summaries"][0]["line_bundle"],
            f"{path}, {scenarios_path}",
            "probe targets the representative unresolved high-priority wedge block",
        ),
        "total_degree_source_terms_reproduced": gate(
            total_reps["1"] == expected["1"] and total_reps["2"] == expected["2"],
            str(path),
            "reconstructed E1 basis signs reproduce the existing character source totals",
        ),
        "entry_dimensions_match_leray_shape": gate(
            [(entry["k"], entry["j"], entry["basis_sign_representation"]["dimension"]) for entry in entries]
            == [(1, 3, 2), (3, 5, 4), (4, 5, 7), (4, 6, 1)],
            str(path),
            "nonzero E1 entries have the expected pyCICY Leray dimensions",
        ),
        "ambient_serre_determinant_case_is_covered": gate(
            any(
                entry["bracket_entries"] == [[0, 0, 0, 0, 0, 0, 0]]
                and entry["ambient_bundles"] == [[0, -2, -2, -2, -2, 0, -3]]
                and entry["basis_sign_representation"]["nonidentity_trace"] == -1
                for entry in entries
            ),
            str(path),
            "verifier covers the pre-BBW ambient determinant sign case",
        ),
        "markdown_matches_report": gate(
            "Status: `e1_basis_signs_match_character_sources`" in md_text
            and "trace-minus-one" in md_text
            and str(total_reps["1"]) in md_text,
            str(md_path),
            "markdown exposes the matching trace data and interpretation",
        ),
    }
    return {
        "scope": "verification for representative E1 Z2 basis-sign reconstruction",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype_verification.json"
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
