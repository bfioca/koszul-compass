#!/usr/bin/env python3
"""Verify the exact monoid audit for the selected radius-4 mass-bound row."""

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
    path = REPORTS / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit.md"
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    solution_tuples = [
        entry["exact_solution"]["solution_tuples_n_then_trace_shift"][0]
        for entry in report["mass_entries"]
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side exact monoid gates passed",
        ),
        "target_and_status_match": gate(
            report["candidate"]
            == "batch2:window2_radius4_adjacency_filtered_4_known_line_resolved"
            and report["source_classification"]["status"]
            == "no_certified_triplet_mass_operator_found"
            and report["upgraded_classification"]["status"]
            == "no_triplet_mass_in_certified_singlet_monoid",
            str(path),
            "the unique mass-bound row is upgraded to a monoid obstruction",
        ),
        "generator_basis_match": gate(
            [item["label"] for item in report["certified_singlet_generators"]]
            == ["e1-e4", "e2-e0", "e3-e0", "e4-e0"],
            str(path),
            "certified H1 singlet generator labels are preserved",
        ),
        "all_entries_exactly_obstructed": gate(
            report["all_mass_entries_monoid_obstructed"]
            and len(report["mass_entries"]) == 3
            and all(entry["certified_singlet_monoid_obstructed"] for entry in report["mass_entries"])
            and solution_tuples
            == [
                ["-1", "0", "0", "0", "0"],
                ["-1", "1", "-1", "0", "0"],
                ["0", "0", "-1", "1", "0"],
            ],
            str(path),
            "each exact charge-cone solution requires a negative generator coefficient",
        ),
        "markdown_exposes_upgrade": gate(
            "upgraded_status: `no_triplet_mass_in_certified_singlet_monoid`" in md_text
            and "exact nonnegative monoid solve is decisive" in md_text,
            str(md_path),
            "markdown states the exact monoid upgrade",
        ),
    }
    return {
        "scope": "verification for selected radius-4 mass-bound exact monoid audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit_verification.json"
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
