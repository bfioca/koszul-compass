#!/usr/bin/env python3
"""Summarize the first bounded radius-5 scout window after branch closure."""

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


def build_report(*, scout_json: Path, branch_json: Path, window_label: str) -> dict[str, Any]:
    scout = load_json(scout_json)
    branch = load_json(branch_json)
    adjusted_statuses = Counter(scout["summary"]["statuses"])
    adjusted_statuses.pop("missing_character_or_charge_level_data", None)
    adjusted_statuses.update(branch["summary"]["statuses"])

    gates = {
        "imports_radius5_scout": gate(
            scout["all_gates_pass"]
            and scout["summary"]["viable_count"] == 0,
            str(scout_json),
            "window closure starts from the verified radius5 scout",
        ),
        "imports_radius5_branch_closure": gate(
            branch["all_gates_pass"]
            and branch["summary"]["unresolved_records"]
            == scout["summary"]["statuses"].get("missing_character_or_charge_level_data", 0)
            and branch["summary"]["records_skipped"] == 0
            and branch["summary"]["viable_branches"] == 0,
            str(branch_json),
            "all missing-character radius5 records were branch-closed with no viable branch",
        ),
        "no_open_missing_character_records": gate(
            "missing_character_or_charge_level_data" not in adjusted_statuses,
            "adjusted radius5 window statuses",
            "branch closure removes all missing-character statuses from this window",
        ),
        "no_viable_candidate": gate(
            scout["summary"]["viable_count"] == 0 and branch["summary"]["viable_branches"] == 0,
            "radius5 scout and branch closure",
            "no certified record or branch completion passes the charge-level filter",
        ),
    }
    return {
        "scope": f"{window_label} bounded radius5 adjacency scout window after branch closure",
        "status": f"radius5_{window_label}_branch_closed_no_viable_candidate",
        "summary": {
            "radius4_sources_available": scout["source_summary"][
                "available_radius4_q1_sources"
            ],
            "radius4_sources_selected": scout["source_summary"][
                "selected_source_records"
            ],
            "frontier_records_screened": scout["screening_counters"][
                "frontier_records_screened"
            ],
            "frontier_records_after_window": scout["screening_counters"][
                "frontier_records_after_window"
            ],
            "raw_q1_spectrum_survivors": scout["summary"][
                "raw_q1_spectrum_survivors"
            ],
            "character_certified_q1_survivors": scout["summary"][
                "character_certified_q1_survivors"
            ],
            "missing_character_records_branch_closed": branch["summary"][
                "unresolved_records"
            ],
            "branch_completions_evaluated": branch["summary"]["branches_evaluated"],
            "desired_q1_branch_completions": branch["summary"]["desired_q1_branches"],
            "viable_count": 0,
            "adjusted_statuses": dict(sorted(adjusted_statuses.items())),
        },
        "interpretation": (
            f"The {window_label} bounded radius5 window produces new q=1 survivors, but every "
            "character-certified candidate or dimension-compatible character branch "
            "is rejected by the current 5259-derived charge-level filter. The window "
            "is closed; the broader radius5 frontier remains open beyond this window."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path, *, title: str) -> None:
    lines = [
        f"# {title}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", "", report["interpretation"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.json"),
    )
    parser.add_argument(
        "--branch-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_branch_analysis.json"),
    )
    parser.add_argument("--window-label", default="window1")
    parser.add_argument("--title", default="Radius-5 Window 1 Closed Frontier")
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_window1_closed_frontier.md"),
    )
    args = parser.parse_args()
    report = build_report(
        scout_json=Path(args.scout_json),
        branch_json=Path(args.branch_json),
        window_label=args.window_label,
    )
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path, title=args.title)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
