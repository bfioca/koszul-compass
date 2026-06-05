#!/usr/bin/env python3
"""Aggregate verified radius-5 source-slice closures."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report(
    *,
    slice_reports: list[Path],
    slice_verifications: list[Path],
    title: str,
    status: str,
    scope: str,
) -> dict[str, Any]:
    slices = [load_json(path) for path in slice_reports]
    verifications = [load_json(path) for path in slice_verifications]
    adjusted_statuses: Counter[str] = Counter()
    for item in slices:
        adjusted_statuses.update(item["summary"]["adjusted_statuses"])

    summary = {
        "source_slices_closed": len(slices),
        "radius4_sources_closed": sum(
            item["summary"]["radius4_sources_selected"] for item in slices
        ),
        "frontier_records_screened": sum(
            item["summary"]["frontier_records_screened"] for item in slices
        ),
        "open_frontier_after_slices": sum(
            item["summary"]["frontier_records_after_final_window"] for item in slices
        ),
        "raw_q1_spectrum_survivors": sum(
            item["summary"]["raw_q1_spectrum_survivors"] for item in slices
        ),
        "character_certified_q1_survivors": sum(
            item["summary"]["character_certified_q1_survivors"] for item in slices
        ),
        "bounded_branch_completions_evaluated": sum(
            item["summary"]["bounded_branch_completions_evaluated"] for item in slices
        ),
        "large_branch_completions_counted": sum(
            item["summary"]["large_branch_completions_counted"] for item in slices
        ),
        "desired_q1_branch_completions": sum(
            item["summary"]["desired_q1_branch_completions"] for item in slices
        ),
        "viable_count": sum(item["summary"]["viable_count"] for item in slices),
        "adjusted_statuses": dict(sorted(adjusted_statuses.items())),
    }
    gates = {
        "all_slice_verifications_pass": gate(
            all(item["all_gates_pass"] for item in verifications),
            ", ".join(str(path) for path in slice_verifications),
            "all source-slice closure verifications pass",
        ),
        "all_slices_exhausted": gate(
            summary["open_frontier_after_slices"] == 0,
            ", ".join(str(path) for path in slice_reports),
            "all included source slices have exhausted local radius-5 frontiers",
        ),
        "no_viable_candidate": gate(
            summary["viable_count"] == 0,
            "aggregate adjusted classifications",
            "no included source slice contains a viable candidate",
        ),
    }
    return {
        "scope": scope,
        "status": status,
        "title": title,
        "summary": summary,
        "slice_reports": [str(path) for path in slice_reports],
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Source Slice Reports", ""])
    for item in report["slice_reports"]:
        lines.append(f"- `{item}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slice-report", action="append", required=True)
    parser.add_argument("--slice-verification", action="append", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--json-out", required=True)
    parser.add_argument("--md-out", required=True)
    args = parser.parse_args()
    slice_reports = [Path(item) for item in args.slice_report]
    slice_verifications = [Path(item) for item in args.slice_verification]
    if len(slice_reports) != len(slice_verifications):
        raise SystemExit("--slice-report and --slice-verification counts must match")
    report = build_report(
        slice_reports=slice_reports,
        slice_verifications=slice_verifications,
        title=args.title,
        status=args.status,
        scope=args.scope,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
