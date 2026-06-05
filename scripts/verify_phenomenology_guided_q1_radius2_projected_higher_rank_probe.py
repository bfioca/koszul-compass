#!/usr/bin/env python3
"""Verify projected higher-rank probe for the remaining dim-10 family."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "projected higher-rank probe builder gates pass",
        ),
        "negative_cokernel_hit": gate(
            report["first_page"]["+"]["target_cokernel_dimension"] == 0
            and report["first_page"]["-"]["target_cokernel_dimension"] == 1
            and report["first_page"]["+"]["projected_higher_rank"] == 0
            and report["first_page"]["-"]["projected_higher_rank"] == 1,
            str(path),
            "projected higher map hits the one-dimensional negative cokernel",
        ),
        "rank_split_is_regular_scenario": gate(
            report["effective_rank_split"] == {
                "rank_plus": 4,
                "rank_minus": 4,
                "total_rank": 8,
            }
            and report["resolved_characters"]["H1"]["regular_multiplicity"] == 1
            and report["resolved_characters"]["H2"]["regular_multiplicity"] == 1,
            str(path),
            "projected family resolves to the desired regular H1/H2 scenario",
        ),
        "markdown_matches_report": gate(
            "Status: `projected_family_resolves_to_desired_q1_character`" in md_text
            and "'rank_plus': 4" in md_text
            and "'rank_minus': 4" in md_text
            and "'regular_multiplicity': 1" in md_text,
            str(md_path),
            "markdown exposes the projected rank split and regular characters",
        ),
    }
    return {
        "scope": "verification for projected higher-rank dim-10 family probe",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_projected_higher_rank_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    Path(args.json_out).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
