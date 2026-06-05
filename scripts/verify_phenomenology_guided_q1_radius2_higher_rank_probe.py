#!/usr/bin/env python3
"""Verify representative residual q=1 higher-rank probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe.md"
    scenarios_path = REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"
    first_page_path = REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.json"
    report = load_json(path)
    scenarios = load_json(scenarios_path)
    first_page = load_json(first_page_path)
    md_text = md_path.read_text(encoding="utf-8")
    desired = scenarios["records"][0]["block_summaries"][0]["scenarios"][1]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "higher-rank probe builder gates pass",
        ),
        "starts_from_verified_first_page_split": gate(
            first_page["all_gates_pass"]
            and report["first_page_rank_split"]["rank_plus"] == 2
            and report["first_page_rank_split"]["rank_minus"] == 2,
            f"{path}, {first_page_path}",
            "higher probe starts from the verified equivariant first-page split",
        ),
        "higher_map_rank_one": gate(
            report["higher_map"]["rank"] == 1
            and report["higher_map"]["nonzero_entries"] == 1,
            str(path),
            "equivariant filtered higher map has total rank one",
        ),
        "calibration_is_equivariant": gate(
            report["calibrated_higher_target_signs"]["cross_eigen_nonzero_entries"] == 0
            and report["calibrated_higher_target_signs"]["multiplicities"]
            == {"+": 1, "-": 1}
            and report["calibrated_higher_target_signs"]["conflicts"] == [],
            str(path),
            "trace-zero higher target basis is calibrated without cross-eigenspace entries",
        ),
        "resolved_scenario_is_desired": gate(
            report["effective_rank_split"]["rank_plus"] == desired["rank_plus"]
            and report["effective_rank_split"]["rank_minus"] == desired["rank_minus"]
            and report["resolved_characters"]["H1"] == desired["H1"]
            and report["resolved_characters"]["H2"] == desired["H2"],
            f"{path}, {scenarios_path}",
            "representative residual block resolves to the desired regular q=1 scenario",
        ),
        "markdown_matches_report": gate(
            "Status: `representative_block_resolves_to_desired_q1_character`" in md_text
            and "'rank_plus': 2" in md_text
            and "'rank_minus': 3" in md_text
            and "'regular_multiplicity': 1" in md_text,
            str(md_path),
            "markdown exposes the resolved effective split and regular characters",
        ),
    }
    return {
        "scope": "verification for representative residual q=1 higher-rank probe",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_higher_rank_probe_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
