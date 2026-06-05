#!/usr/bin/env python3
"""Resolve remaining low-priority radius-3 singleton line patterns by E2 characters."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius3_large_e2_probe import compute_e2  # noqa: E402
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def resolved_keys(path: Path) -> set[tuple[str | None, str | None]]:
    if not path.exists():
        return set()
    report = load_json(path)
    return {
        (record.get("source_window"), record.get("source_filtered_label"))
        for record in report.get("filtered_candidate_records", [])
        if record["classification"]["category"] != "unresolved"
    }


def remaining_low_items(audit: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = set()
    for filename in [
        "phenomenology_guided_q1_radius3_high_priority_rank_resolved.json",
        "phenomenology_guided_q1_radius3_medium_three_family_rank_resolved.json",
        "phenomenology_guided_q1_radius3_medium_small_rank_resolved.json",
        "phenomenology_guided_q1_radius3_low_repeated_rank_resolved.json",
    ]:
        resolved |= resolved_keys(REPORTS / filename)
    items = []
    for record in audit["records"]:
        if record["audit"].get("priority_bucket") != "low_priority_nonq1_or_large_map_backlog":
            continue
        if (record["window"], record["label"]) in resolved:
            continue
        items.append(record)
    return items


def remaining_lines(items: list[dict[str, Any]]) -> list[list[int]]:
    repeated = load_json(REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe.json")
    covered = {tuple(record["line_bundle"]) for record in repeated["records"]}
    lines = []
    seen = set()
    for item in items:
        for block in item["audit"]["missing_character_blocks"]:
            line = tuple(block["line_bundle"])
            if line in covered or line in seen:
                continue
            seen.add(line)
            lines.append(list(line))
    return lines


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
    repeated = load_json(REPORTS / "phenomenology_guided_q1_radius3_low_repeated_e2_probe.json")
    items = remaining_low_items(audit)
    lines = remaining_lines(items)
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    records = [
        compute_e2(
            manifold=manifold,
            conf=conf,
            line_bundle=line,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        )
        for line in lines
    ]
    all_covered = {tuple(record["line_bundle"]) for record in repeated["records"]}
    all_covered |= {tuple(record["line_bundle"]) for record in records}
    fully_covered = []
    for item in items:
        missing = {
            tuple(block["line_bundle"])
            for block in item["audit"]["missing_character_blocks"]
        }
        if missing <= all_covered:
            fully_covered.append(
                {
                    "window": item["window"],
                    "label": item["label"],
                    "missing_character_block_count": item["audit"][
                        "missing_character_block_count"
                    ],
                }
            )
    gates = {
        "remaining_low_items_identified": gate(
            len(items) == 15,
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "after previous closures, fifteen low-priority records remain",
        ),
        "remaining_patterns_processed": gate(
            len(records) == len(lines) == 46,
            "remaining low-priority singleton line patterns",
            "all remaining low-priority singleton patterns were processed",
        ),
        "all_e2_maps_are_equivariant": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in records),
            "remaining low-priority E1 first-page maps",
            "all d1 maps are block diagonal in reconstructed Z2 eigenspaces",
        ),
        "all_e2_complexes_are_valid": gate(
            all(
                all(
                    item["composition_rank"] == 0 and item["nonzero_entries"] == 0
                    for item in record["compositions"]
                )
                for record in records
            ),
            "remaining low-priority first-page complexes",
            "all consecutive d1 compositions vanish",
        ),
        "all_remaining_low_records_covered": gate(
            len(fully_covered) == 15,
            "remaining low-priority records",
            "the repeated and singleton E2 probes together cover all remaining low-priority records",
        ),
    }
    return {
        "scope": "remaining low-priority radius-3 singleton E2 character probe",
        "status": "low_remaining_e2_characters_resolved",
        "records": records,
        "fully_covered_low_records": fully_covered,
        "resolved_actuals": {
            str(record["line_bundle"]): record["actual"] for record in records
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Low Remaining E2 Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- singleton line patterns resolved: `{len(report['records'])}`",
        f"- fully covered low records: `{len(report['fully_covered_low_records'])}`",
        "",
    ]
    for record in report["records"]:
        lines.append(f"- `{record['line_bundle']}`: actual `{record['actual']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_low_remaining_e2_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"records={len(report['records'])}")
    print(f"fully_covered={len(report['fully_covered_low_records'])}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
