#!/usr/bin/env python3
"""Verify the map-rank capability audit."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_map_rank_capability.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_map_rank_capability.md"
    scenarios_path = REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"
    report = load_json(path)
    scenarios = load_json(scenarios_path)
    md_text = md_path.read_text(encoding="utf-8")
    methods = report["pycicy_private_methods"]
    probe = report["representative_block_probe"]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "map-rank capability builder gates pass",
        ),
        "scenario_frontier_imported": gate(
            scenarios["summary"]["records"] == 4
            and scenarios["summary"]["total_desired_q1_scenarios"] == 12,
            f"{scenarios_path}, {path}",
            "capability audit is tied to the verified high-priority map-scenario frontier",
        ),
        "pycicy_private_hooks_available": gate(
            methods["_rank_map"]["available"]
            and "rmap=False" in methods["_rank_map"]["signature"]
            and methods["_single_map"]["available"]
            and methods["_higher_map"]["available"]
            and methods["Leray"]["available"]
            and methods["_line_to_BBW"]["available"],
            str(path),
            "pyCICY exposes ordinary and higher-Leray private map construction/rank hooks",
        ),
        "representative_block_reproduces_rank_need": gate(
            probe["line_bundle"] == [1, 0, -2, -1, -1, 1, 0]
            and probe["pycicy_line_cohomology"] == [0, 2, 2, 0]
            and probe["line_cohomology_matches_report"] is True
            and probe["effective_rank_from_total_degree_dimensions"] == 5
            and probe["effective_rank_consistent_with_target_total"] is True
            and probe["has_zero_charge_so_pycicy_uses_higher_leray"] is True
            and probe["direct_first_page_target_dimension_for_E45_to_E35"] == 4
            and probe["effective_rank_exceeds_immediate_first_page_target"] is True,
            str(path),
            "representative block reproduces mixed H1/H2 dimensions and needs higher-Leray effective rank five",
        ),
        "missing_primitive_is_equivariant_split": gate(
            report["missing_primitive"]["name"] == "equivariant_koszul_map_rank_split"
            and "rank_plus" in report["missing_primitive"]["outputs"]
            and "rank_minus" in report["missing_primitive"]["outputs"]
            and report["status"]
            == "higher_leray_map_hooks_available_but_equivariant_split_missing",
            str(path),
            "higher-Leray map hooks exist but the missing certification primitive is the Z2 rank split",
        ),
        "markdown_matches_report": gate(
            "effective rank from total-degree dimensions: `5`" in md_text
            and "higher-Leray required: `True`" in md_text
            and "equivariant_koszul_map_rank_split" in md_text
            and "rank_+ / rank_-" in md_text,
            str(md_path),
            "markdown exposes effective rank, higher-Leray requirement, and missing equivariant split primitive",
        ),
    }
    return {
        "scope": "verification for map-rank capability audit",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_map_rank_capability_verification.json"
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
