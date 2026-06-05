#!/usr/bin/env python3
"""Exact monoid audit for the selected radius-4 mass-bound unresolved row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import sympy as sp

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def exact_monoid_solution(
    *, needed: list[int], generators: list[list[int]]
) -> dict[str, Any]:
    coeffs = sp.symbols(f"n0:{len(generators)}", integer=True, nonnegative=True)
    trace_shift = sp.symbols("trace_shift", integer=True)
    equations = [
        sum(coeffs[index] * generators[index][coord] for index in range(len(generators)))
        - trace_shift
        - needed[coord]
        for coord in range(5)
    ]
    solution = sp.linsolve(equations, (*coeffs, trace_shift))
    tuples = []
    has_nonnegative_integer_solution = False
    for item in solution:
        values = [sp.simplify(value) for value in item]
        tuples.append([str(value) for value in values])
        if all(value.is_integer for value in values) and all(value >= 0 for value in values[:-1]):
            has_nonnegative_integer_solution = True
    return {
        "equation": "sum_i n_i * generator_i = needed_singlet_charge + trace_shift*(1,1,1,1,1)",
        "solution_tuples_n_then_trace_shift": tuples,
        "has_nonnegative_integer_solution": has_nonnegative_integer_solution,
    }


def find_target_record() -> dict[str, Any]:
    report = load_json(REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json")
    targets = [
        record
        for record in report["filtered_candidate_records"]
        if record["classification"]["status"] == "no_certified_triplet_mass_operator_found"
    ]
    if len(targets) != 1:
        raise ValueError(f"expected one mass-bound unresolved row, found {len(targets)}")
    target = targets[0]
    target["batch"] = report["batch"]
    return target


def build_report() -> dict[str, Any]:
    target = find_target_record()
    certified_labels = set(
        target["singlet_moduli_inventory"]["certified_h1_singlet_charge_labels"]
    )
    certified = [
        item
        for item in target["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]
        if item["charge"]["label"] in certified_labels and item["h1_dimension"] > 0
    ]
    labels = [item["charge"]["label"] for item in certified]
    generators = [item["charge"]["coefficients"] for item in certified]
    mass_entries = []
    for item in target["mass_operator_table"]:
        solution = exact_monoid_solution(
            needed=item["needed_singlet_charge"]["coefficients"],
            generators=generators,
        )
        mass_entries.append(
            {
                "fivebar": item["fivebar"],
                "five": item["five"],
                "needed_singlet_charge": item["needed_singlet_charge"],
                "degree_le_2_hit_count": len(
                    item.get("certified_singlet_monomial_hits_degree_le_2", [])
                ),
                "exact_solution": solution,
                "certified_singlet_monoid_obstructed": not solution[
                    "has_nonnegative_integer_solution"
                ],
            }
        )

    all_obstructed = all(entry["certified_singlet_monoid_obstructed"] for entry in mass_entries)
    upgraded_classification = {
        "category": "phenomenologically obstructed",
        "status": "no_triplet_mass_in_certified_singlet_monoid",
        "reason": (
            "no certified H1 singlet monomial can neutralize any candidate triplet "
            "mass charge; exact nonnegative charge-cone solutions require negative "
            "certified-singlet generator coefficients"
        ),
    }
    gates = {
        "target_row_found": gate(
            target["batch"] == "batch2"
            and target["label"] == "window2_radius4_adjacency_filtered_4_known_line_resolved",
            str(REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"),
            "the unique mass-bound unresolved row is the expected selected radius-4 candidate",
        ),
        "certified_generators_present": gate(
            labels == ["e1-e4", "e2-e0", "e3-e0", "e4-e0"],
            "target singlet_moduli_inventory",
            "exact audit uses the certified H1 singlet charge generators for this row",
        ),
        "all_triplet_mass_entries_obstructed": gate(
            all_obstructed and len(mass_entries) == 3,
            "exact nonnegative singlet charge-cone solve",
            "every candidate triplet-pair bilinear requires a negative singlet-generator coefficient",
        ),
    }
    return {
        "scope": "exact monoid audit for selected radius-4 mass-bound unresolved row",
        "status": "mass_bound_unresolved_row_upgraded_to_monoid_obstruction"
        if all_obstructed
        else "mass_bound_unresolved_row_has_exact_monoid_solution",
        "candidate": f"{target['batch']}:{target['label']}",
        "source_classification": target["classification"],
        "upgraded_classification": upgraded_classification if all_obstructed else None,
        "certified_singlet_generators": [
            {"label": label, "coefficients": coeffs}
            for label, coeffs in zip(labels, generators)
        ],
        "mass_entries": mass_entries,
        "all_mass_entries_monoid_obstructed": all_obstructed,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Mass-Bound Exact Monoid Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- candidate: `{report['candidate']}`",
        f"- source_status: `{report['source_classification']['status']}`",
        f"- upgraded_status: `{report['upgraded_classification']['status'] if report['upgraded_classification'] else None}`",
        f"- all_mass_entries_monoid_obstructed: `{report['all_mass_entries_monoid_obstructed']}`",
        "",
        "## Certified Singlet Generators",
        "",
    ]
    for item in report["certified_singlet_generators"]:
        lines.append(f"- `{item['label']}`: `{item['coefficients']}`")
    lines.extend(["", "## Mass Entries", ""])
    for entry in report["mass_entries"]:
        lines.append(
            f"- `{entry['fivebar']} x {entry['five']}` needs "
            f"`{entry['needed_singlet_charge']['label']}`; "
            f"solution `{entry['exact_solution']['solution_tuples_n_then_trace_shift']}`; "
            f"obstructed `{entry['certified_singlet_monoid_obstructed']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The previous degree <= 2 mass audit was inconclusive for this row, "
                "but the exact nonnegative monoid solve is decisive: all candidate "
                "triplet mass charges require at least one negative certified-singlet "
                "generator coefficient. The row is therefore upgraded to a "
                "charge-level triplet-mass obstruction."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_mass_bound_exact_monoid_audit.md"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"all_gates_pass={report['all_gates_pass']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
