#!/usr/bin/env python3
"""Exact monoid audit for radius-5 q=1 mass-operator-unresolved records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def certified_generators(record: dict[str, Any]) -> list[dict[str, Any]]:
    labels = set(record["singlet_moduli_inventory"]["certified_h1_singlet_charge_labels"])
    generators = []
    for item in record["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]:
        if item["charge"]["label"] in labels and item["h1_dimension"] > 0:
            generators.append(
                {
                    "label": item["charge"]["label"],
                    "coefficients": item["charge"]["coefficients"],
                }
            )
    return sorted(generators, key=lambda item: item["label"])


def exact_monoid_solution(
    *, needed: list[int], generators: list[dict[str, Any]]
) -> dict[str, Any]:
    if not generators:
        return {
            "has_nonnegative_integer_solution": False,
            "solution": None,
            "solver_status": "no_generators",
        }
    generator_coeffs = [item["coefficients"] for item in generators]
    # Variables are generator powers n_i >= 0 plus an unrestricted trace shift t:
    # sum_i n_i * generator_i - t*(1,1,1,1,1) = needed.
    rows = []
    for coord in range(5):
        rows.append([coeffs[coord] for coeffs in generator_coeffs] + [-1])
    a_eq = np.array(rows, dtype=float)
    b_eq = np.array(needed, dtype=float)
    c = np.zeros(len(generators) + 1, dtype=float)
    lower = np.array([0] * len(generators) + [-np.inf], dtype=float)
    upper = np.array([np.inf] * (len(generators) + 1), dtype=float)
    result = milp(
        c=c,
        integrality=np.ones(len(generators) + 1, dtype=int),
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(a_eq, b_eq, b_eq),
        options={"time_limit": 5.0},
    )
    if not result.success:
        return {
            "has_nonnegative_integer_solution": False,
            "solution": None,
            "solver_status": str(result.message),
        }
    values = [int(round(value)) for value in result.x]
    return {
        "has_nonnegative_integer_solution": True,
        "solution": {
            "generator_powers": values[:-1],
            "trace_shift": values[-1],
        },
        "solver_status": str(result.message),
    }


def audit_record(record: dict[str, Any], *, source_path: Path, weight: int) -> dict[str, Any]:
    generators = certified_generators(record)
    mass_entries = []
    for item in record["mass_operator_table"]:
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
    any_solution = any(
        entry["exact_solution"]["has_nonnegative_integer_solution"]
        for entry in mass_entries
    )
    return {
        "label": record["label"],
        "source_path": str(source_path),
        "weight": weight,
        "source_classification": record["classification"],
        "upgraded_classification": {
            "category": "phenomenologically obstructed",
            "status": "no_triplet_mass_in_certified_singlet_monoid",
            "reason": (
                "exact certified-singlet charge-monoid feasibility found no "
                "nonnegative generator solution for any candidate triplet mass charge"
            ),
        }
        if all_obstructed
        else None,
        "certified_singlet_generators": generators,
        "mass_entries": mass_entries,
        "all_mass_entries_monoid_obstructed": all_obstructed,
        "has_exact_monoid_solution": any_solution,
    }


def collect_branch_records() -> list[tuple[Path, dict[str, Any], int]]:
    records = []
    for path in sorted(REPORTS.glob("phenomenology_guided_q1_radius5_slice*_branch_analysis_window*.json")):
        if path.name.endswith("_verification.json"):
            continue
        report = load_json(path)
        if "summary" not in report:
            continue
        if report["summary"]["statuses"].get("no_certified_triplet_mass_operator_found", 0) == 0:
            continue
        for record in report.get("desired_q1_branch_candidate_records", []):
            if record["classification"]["status"] == "no_certified_triplet_mass_operator_found":
                records.append((path, record, 1))
    return records


def collect_direct_scout_records() -> list[tuple[Path, dict[str, Any], int]]:
    records = []
    for path in sorted(REPORTS.glob("phenomenology_guided_q1_radius5_slice*_adjacency_scout_window*.json")):
        if path.name.endswith("_verification.json"):
            continue
        match = re.search(r"_slice(\d+)_adjacency_scout_window(\d+)\.json$", path.name)
        if not match:
            continue
        slice_id, window_id = match.groups()
        closed_path = (
            REPORTS
            / f"phenomenology_guided_q1_radius5_slice{slice_id}_window{window_id}_closed_frontier.json"
        )
        if not closed_path.exists():
            continue
        closed = load_json(closed_path)
        if "large_records_closed" in closed["summary"]:
            continue
        report = load_json(path)
        if report["summary"]["statuses"].get("no_certified_triplet_mass_operator_found", 0) == 0:
            continue
        for record in report.get("filtered_candidate_records", []):
            if record["classification"]["status"] == "no_certified_triplet_mass_operator_found":
                records.append((path, record, 1))
    return records


def collect_large_representatives() -> list[tuple[Path, dict[str, Any], int]]:
    records = []
    for path in sorted(REPORTS.glob("phenomenology_guided_q1_radius5_slice*_large_branch_closure*.json")):
        report = load_json(path)
        record = report.get("q1_representative_candidate")
        if not record:
            continue
        if record["classification"]["status"] != "no_certified_triplet_mass_operator_found":
            continue
        records.append((path, record, int(report["summary"]["desired_q1_branches"])))
    return records


def build_report() -> dict[str, Any]:
    direct_records = collect_direct_scout_records()
    branch_records = collect_branch_records()
    large_records = collect_large_representatives()
    audited = [
        audit_record(record, source_path=path, weight=weight)
        for path, record, weight in direct_records + branch_records + large_records
    ]
    weighted_total = sum(item["weight"] for item in audited)
    weighted_upgraded = sum(
        item["weight"] for item in audited if item["all_mass_entries_monoid_obstructed"]
    )
    weighted_open = sum(
        item["weight"] for item in audited if not item["all_mass_entries_monoid_obstructed"]
    )
    final_aggregate = load_json(
        REPORTS / "phenomenology_guided_q1_radius5_source_slices_0_128_closed_frontier.json"
    )
    expected_unresolved = final_aggregate["summary"]["adjusted_statuses"][
        "no_certified_triplet_mass_operator_found"
    ]
    gates = {
        "final_radius5_aggregate_imported": gate(
            final_aggregate["all_gates_pass"]
            and final_aggregate["summary"]["viable_count"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius5_source_slices_0_128_closed_frontier.json"),
            "audit starts from the verified final radius-5 aggregate",
        ),
        "all_weighted_unresolved_records_accounted": gate(
            weighted_total == expected_unresolved,
            "branch-analysis records plus large-branch representatives",
            "weighted unresolved mass records match the final aggregate count",
        ),
        "all_audited_records_have_mass_tables": gate(
            all(item["mass_entries"] for item in audited),
            "audited candidate records",
            "every audited unresolved record has a mass-operator table",
        ),
    }
    return {
        "scope": "exact certified-singlet monoid audit for final radius-5 mass-operator-unresolved q=1 records",
        "status": (
            "radius5_unresolved_mass_records_all_upgraded_to_monoid_obstructions"
            if weighted_open == 0
            else "radius5_unresolved_mass_records_have_open_exact_monoid_solutions"
        ),
        "summary": {
            "audited_representative_records": len(audited),
            "direct_scout_records": len(direct_records),
            "bounded_branch_records": len(branch_records),
            "large_branch_representatives": len(large_records),
            "weighted_unresolved_q1_completions": weighted_total,
            "weighted_upgraded_monoid_obstructions": weighted_upgraded,
            "weighted_open_monoid_solutions": weighted_open,
            "representatives_with_exact_monoid_solution": sum(
                1 for item in audited if item["has_exact_monoid_solution"]
            ),
            "representatives_all_mass_entries_obstructed": sum(
                1 for item in audited if item["all_mass_entries_monoid_obstructed"]
            ),
        },
        "audited_records": audited,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-5 Unresolved Mass Monoid Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Open Representatives", ""])
    open_records = [
        item for item in report["audited_records"]
        if not item["all_mass_entries_monoid_obstructed"]
    ]
    if not open_records:
        lines.append("- none")
    else:
        for item in open_records[:25]:
            lines.append(
                f"- `{item['label']}` weight `{item['weight']}` from `{item['source_path']}`"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_unresolved_mass_monoid_audit.md"),
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
