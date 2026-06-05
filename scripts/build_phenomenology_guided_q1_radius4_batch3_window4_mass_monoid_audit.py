#!/usr/bin/env python3
"""Exact singlet-monoid audit for batch-3 window-4 mass-bound q=1 rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SOURCE = REPORTS / "phenomenology_guided_q1_radius4_adjacency_scout_batch3_window4.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def exact_solution(needed: list[int], generators: list[list[int]]) -> dict[str, Any]:
    coeffs = sp.symbols(f"n0:{len(generators)}", integer=True, nonnegative=True)
    trace_shift = sp.symbols("trace_shift", integer=True)
    equations = [
        sum(coeffs[i] * generators[i][j] for i in range(len(generators)))
        - trace_shift
        - needed[j]
        for j in range(5)
    ]
    solution = sp.linsolve(equations, (*coeffs, trace_shift))
    if solution is sp.EmptySet:
        return {
            "solution_tuples_n_then_trace_shift": [],
            "has_integer_solution": False,
            "has_nonnegative_integer_solution": False,
        }
    tuples = []
    has_nonnegative = False
    for item in solution:
        values = [sp.simplify(value) for value in item]
        tuples.append([str(value) for value in values])
        if all(value.is_integer for value in values) and all(value >= 0 for value in values[:-1]):
            has_nonnegative = True
    return {
        "solution_tuples_n_then_trace_shift": tuples,
        "has_integer_solution": bool(tuples),
        "has_nonnegative_integer_solution": has_nonnegative,
    }


def certified_generators(record: dict[str, Any]) -> list[dict[str, Any]]:
    labels = set(record["singlet_moduli_inventory"]["certified_h1_singlet_charge_labels"])
    out = []
    for item in record["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]:
        if item["charge"]["label"] in labels and item["h1_dimension"] > 0:
            out.append(
                {
                    "label": item["charge"]["label"],
                    "coefficients": item["charge"]["coefficients"],
                }
            )
    return sorted(out, key=lambda item: item["label"])


def build_report() -> dict[str, Any]:
    source = load_json(SOURCE)
    targets = [
        record
        for record in source["filtered_candidate_records"]
        if record["classification"]["status"] == "no_certified_triplet_mass_operator_found"
    ]
    audited = []
    for record in targets:
        generators = certified_generators(record)
        generator_coeffs = [item["coefficients"] for item in generators]
        entries = []
        for mass in record["mass_operator_table"]:
            solution = exact_solution(
                mass["needed_singlet_charge"]["coefficients"], generator_coeffs
            )
            entries.append(
                {
                    "fivebar": mass["fivebar"],
                    "five": mass["five"],
                    "needed_singlet_charge": mass["needed_singlet_charge"],
                    "degree_le_2_hit_count": len(
                        mass.get("certified_singlet_monomial_hits_degree_le_2", [])
                    ),
                    "exact_solution": solution,
                    "certified_singlet_monoid_obstructed": not solution[
                        "has_nonnegative_integer_solution"
                    ],
                }
            )
        all_obstructed = all(item["certified_singlet_monoid_obstructed"] for item in entries)
        audited.append(
            {
                "candidate": record["label"],
                "source_classification": record["classification"],
                "upgraded_classification": {
                    "category": "phenomenologically obstructed",
                    "status": "no_triplet_mass_in_certified_singlet_monoid",
                    "reason": (
                        "no certified H1 singlet monomial can neutralize any candidate "
                        "triplet mass charge with nonnegative generator powers"
                    ),
                }
                if all_obstructed
                else None,
                "certified_singlet_generators": generators,
                "mass_entries": entries,
                "all_mass_entries_monoid_obstructed": all_obstructed,
            }
        )
    gates = {
        "source_window_verified": gate(
            source["all_gates_pass"]
            and source["summary"]["statuses"].get("no_certified_triplet_mass_operator_found") == 4,
            str(SOURCE),
            "audit starts from the verified batch-3 window-4 scout with four mass-bound rows",
        ),
        "all_mass_bound_rows_audited": gate(
            len(audited) == 4,
            str(SOURCE),
            "all batch-3 window-4 mass-bound q=1 rows were audited",
        ),
        "all_mass_entries_obstructed": gate(
            all(item["all_mass_entries_monoid_obstructed"] for item in audited),
            "exact trace-shifted nonnegative singlet monoid solves",
            "every mass-bound row is upgraded to a certified singlet-monoid triplet-mass obstruction",
        ),
    }
    return {
        "scope": "exact monoid audit for batch-3 window-4 mass-bound q=1 rows",
        "status": "batch3_window4_mass_bound_rows_upgraded_to_monoid_obstructions",
        "audited_candidates": audited,
        "summary": {
            "mass_bound_rows": len(targets),
            "upgraded_obstructions": sum(
                1 for item in audited if item["all_mass_entries_monoid_obstructed"]
            ),
            "open_mass_bound_uncertainties": sum(
                1 for item in audited if not item["all_mass_entries_monoid_obstructed"]
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Batch-3 Window-4 Mass Monoid Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Candidates", ""])
    for candidate in report["audited_candidates"]:
        lines.append(
            f"- `{candidate['candidate']}`: "
            f"`{candidate['upgraded_classification']['status'] if candidate['upgraded_classification'] else None}`"
        )
        for entry in candidate["mass_entries"]:
            lines.append(
                f"  - `{entry['fivebar']} x {entry['five']}` needs "
                f"`{entry['needed_singlet_charge']['label']}`; solution "
                f"`{entry['exact_solution']['solution_tuples_n_then_trace_shift']}`; "
                f"obstructed `{entry['certified_singlet_monoid_obstructed']}`"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_batch3_window4_mass_monoid_audit.md"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
