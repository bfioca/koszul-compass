#!/usr/bin/env python3
"""Verify the bounded radius-5 adjacency scout."""

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


def verify(*, scout_json: Path, scout_md: Path) -> dict[str, Any]:
    path = scout_json
    md_path = scout_md
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    summary = report["summary"]
    filtered = report["filtered_candidate_records"]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side radius5 scout gates passed",
        ),
        "radius4_no_go_imported": gate(
            report["gates"]["imports_radius4_no_go"]["pass"],
            str(path),
            "radius5 scout imports the verified selected radius4 no-go before expanding",
        ),
        "source_and_frontier_nonempty": gate(
            report["source_summary"]["available_radius4_q1_sources"] >= report[
                "source_summary"
            ]["selected_source_records"]
            > 0
            and report["screening_counters"]["frontier_records_screened"] > 0,
            str(path),
            "radius5 scout uses actual radius4 q1 sources and screens a nonempty frontier",
        ),
        "certified_records_have_required_tables": gate(
            summary["certified_q1_records"] == len(filtered)
            and all(
                item["spectrum_certificate"] is not None
                and item["character_certificate"] is not None
                and (
                    item["classification"]["category"] == "unresolved"
                    or (
                        item["mass_operator_table"] is not None
                        and item["proton_decay_operator_table"] is not None
                    )
                )
                for item in filtered
            ),
            str(path),
            "every radius5 certified q1 record has spectrum/character data and charge tables when character-certified",
        ),
        "classification_counts_match": gate(
            sum(summary["categories"].values()) == summary["certified_q1_records"]
            and sum(summary["statuses"].values()) == summary["certified_q1_records"],
            str(path),
            "classification category/status counts cover all certified q1 records",
        ),
        "markdown_exposes_scout": gate(
            "Radius-5 Adjacency Scout" in md_text
            and "certified_q1_records" in md_text
            and "viable_count" in md_text,
            str(md_path),
            "markdown exposes radius5 scout totals",
        ),
    }
    return {
        "scope": "verification for bounded radius5 adjacency scout",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scout-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.json"),
    )
    parser.add_argument(
        "--scout-md",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_adjacency_scout_verification.json"),
    )
    args = parser.parse_args()
    result = verify(scout_json=Path(args.scout_json), scout_md=Path(args.scout_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
