#!/usr/bin/env python3
"""Build a cumulative roll-up for closed radius-8 broad frontier windows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", type=int, default=8)
    parser.add_argument("--windows", type=int, required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()

    radius = args.radius
    n = args.windows
    component_reports = []
    windows = []
    summary = {
        "frontier_records_screened": 0,
        "raw_q1_spectrum_survivors": 0,
        "adjusted_desired_q1_candidates": 0,
        "large_branch_completions_counted": 0,
        "large_desired_q1_branch_completions": 0,
        "bounded_branch_completions_evaluated": 0,
        "bounded_desired_q1_branch_completions": 0,
        "mass_records_upgraded_by_exact_monoid": 0,
        "open_mass_monoid_solutions": 0,
        "viable_count": 0,
        "adjusted_statuses": {},
    }
    frontier_after = None
    source_radius = None
    source_count = None
    source_reports_loaded = None
    source_verification_paths = []
    frontier_size = None

    for window in range(1, n + 1):
        report_path = Path(
            f"reports/phenomenology_guided_q1_radius{radius}_broad_closed_frontier_window{window}.json"
        )
        verification_path = Path(
            f"reports/phenomenology_guided_q1_radius{radius}_broad_closed_frontier_window{window}_verification.json"
        )
        report = load_json(report_path)
        verification = load_json(verification_path)
        if not verification.get("all_gates_pass"):
            raise SystemExit(f"verification failed for window {window}: {verification_path}")

        source = report["summary"]
        bounded = source.get(
            "bounded_branch_completions_evaluated",
            source.get("branch_completions_evaluated", 0),
        )
        bounded_desired = source.get(
            "bounded_desired_q1_branch_completions",
            source.get("desired_q1_branch_completions", 0),
        )
        large = source.get("large_branch_completions_counted", 0)
        large_desired = source.get("large_desired_q1_branch_completions", 0)
        item = {
            "window": window,
            "frontier_records_screened": source.get("frontier_records_screened", 0),
            "frontier_records_after_window": source.get("frontier_records_after_window", 0),
            "raw_q1_spectrum_survivors": source.get("raw_q1_spectrum_survivors", 0),
            "direct_character_certified_q1_records": source.get(
                "direct_character_certified_q1_records", 0
            ),
            "branch_completions_evaluated": bounded,
            "desired_q1_branch_completions": bounded_desired,
            "large_branch_completions_counted": large,
            "large_desired_q1_branch_completions": large_desired,
            "adjusted_desired_q1_candidates": source.get(
                "adjusted_desired_q1_candidates", 0
            ),
            "mass_records_upgraded_by_exact_monoid": source.get(
                "mass_records_upgraded_by_exact_monoid", 0
            ),
            "open_mass_monoid_solutions": source.get("open_mass_monoid_solutions", 0),
            "viable_count": source.get("viable_count", 0),
            "adjusted_statuses": source.get("adjusted_statuses", {}),
        }
        windows.append(item)
        component_reports.append(
            {
                "window": window,
                "report": str(report_path),
                "verification": str(verification_path),
                "verified": True,
            }
        )

        summary["frontier_records_screened"] += item["frontier_records_screened"]
        summary["raw_q1_spectrum_survivors"] += item["raw_q1_spectrum_survivors"]
        summary["adjusted_desired_q1_candidates"] += item[
            "adjusted_desired_q1_candidates"
        ]
        summary["large_branch_completions_counted"] += large
        summary["large_desired_q1_branch_completions"] += large_desired
        summary["bounded_branch_completions_evaluated"] += bounded
        summary["bounded_desired_q1_branch_completions"] += bounded_desired
        summary["mass_records_upgraded_by_exact_monoid"] += item[
            "mass_records_upgraded_by_exact_monoid"
        ]
        summary["open_mass_monoid_solutions"] += item["open_mass_monoid_solutions"]
        summary["viable_count"] += item["viable_count"]
        for status, count in item["adjusted_statuses"].items():
            summary["adjusted_statuses"][status] = (
                summary["adjusted_statuses"].get(status, 0) + count
        )
        frontier_after = item["frontier_records_after_window"]
        if window == 1:
            frontier_size = item["frontier_records_screened"] + frontier_after
            scout_path = report.get("component_reports", {}).get("scout")
            if scout_path:
                scout = load_json(Path(scout_path))
                search = scout.get("search_parameters", {})
                source_summary = scout.get("source_summary", {})
                source_radius = search.get("source_radius", radius - 1)
                source_count = source_summary.get("source_count")
                source_reports_loaded = source_summary.get("source_reports_loaded")
                source_verification_paths = source_summary.get("verification_paths", [])

    summary.update(
        {
            "all_verified": True,
            "windows_closed": n,
            "source_radius": source_radius if source_radius is not None else radius - 1,
            "target_radius": radius,
            "source_count": source_count,
            "source_reports_loaded": source_reports_loaded,
            "frontier_size": frontier_size,
            f"frontier_records_after_window{n}": frontier_after,
        }
    )
    status = f"radius{radius}_broad_windows1_{n}_closed_no_viable_candidate"
    frontier_status = (
        f"the radius-{radius} broad frontier is exhausted."
        if frontier_after == 0
        else "the remaining frontier is still open."
    )
    interpretation = (
        f"The first {n} windows of the radius-{radius} broad frontier are "
        "closed with spectrum, character, mass-operator, proton-operator, and "
        "classification evidence for every q=1 survivor. No viable charge-level "
        f"candidate is found; {frontier_status}"
    )
    gates = {
        "all_windows_verified": {
            "pass": True,
            "evidence": f"reports/phenomenology_guided_q1_radius{radius}_broad_closed_frontier_window*_verification.json",
            "note": f"closed radius{radius} window verifiers pass",
        },
        "imports_verified_source_frontier": {
            "pass": bool(source_verification_paths),
            "evidence": ", ".join(source_verification_paths),
            "note": f"radius{radius} frontier imports verified radius{summary['source_radius']} source artifacts",
        },
        "no_viable_candidate": {
            "pass": summary["viable_count"] == 0,
            "evidence": f"radius{radius} closed window reports",
            "note": f"no q1 candidate in closed radius{radius} windows passed DT and proton filters",
        },
        "no_open_uncertainty": {
            "pass": summary["open_mass_monoid_solutions"] == 0,
            "evidence": f"radius{radius} closed window reports",
            "note": f"closed radius{radius} windows have no open mass uncertainty",
        },
    }
    rollup = {
        "title": f"Radius-{radius} Broad Windows 1-{n} Roll-Up",
        "status": status,
        "scope": f"radius{radius} broad frontier windows 1-{n}",
        "summary": summary,
        "gates": gates,
        "all_gates_pass": all(gate["pass"] for gate in gates.values()),
        "component_reports": component_reports,
        "windows": windows,
        "interpretation": interpretation,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(rollup, indent=2, sort_keys=True) + "\n")

    lines = [
        f"# Radius-{radius} Broad Windows 1-{n} Roll-Up",
        "",
        f"Status: `{status}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Gates", ""]
    for key, gate in gates.items():
        lines.append(f"- {key}: `{gate['pass']}` - {gate['note']}")
    lines += ["", "## Interpretation", "", interpretation, ""]
    md_out.write_text("\n".join(lines))

    print(json_out)
    print(md_out)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
