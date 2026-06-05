#!/usr/bin/env python3
"""Verify the bounded radius-3 obstruction certificate."""

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
    path = REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side bounded certificate gates passed",
        ),
        "frontier_counts_match": gate(
            summary["raw_q1_spectrum_survivors"] == 64
            and summary["phenomenologically_obstructed"] == 63
            and summary["unresolved"] == 1
            and summary["viable"] == 0,
            str(path),
            "bounded certificate has the expected final radius-3 counts",
        ),
        "only_sign_conflict_unresolved": gate(
            report["unresolved_records"]
            and len(report["unresolved_records"]) == 1
            and report["unresolved_records"][0]["key"] == "window2/radius3_adjacency_filtered_16",
            str(path),
            "the only unresolved record is the known high-priority sign conflict",
        ),
        "all_records_have_final_sections": gate(
            len(report["final_candidate_records"]) == 64
            and all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in report["final_candidate_records"]
            ),
            str(path),
            "all final candidate records expose required report sections",
        ),
        "markdown_exposes_summary": gate(
            "Status: `no_viable_candidate_found_radius3_bounded_frontier_one_character_conflict`"
            in md_text
            and "phenomenologically_obstructed: `63`" in md_text
            and "unresolved: `1`" in md_text,
            str(md_path),
            "markdown exposes bounded obstruction summary",
        ),
    }
    return {
        "scope": "verification for bounded radius-3 obstruction certificate",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_bounded_obstruction_certificate_verification.json"),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
