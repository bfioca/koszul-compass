#!/usr/bin/env python3
"""Resolve radius-3 medium-small backlog line patterns by E2 characters."""

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

MEDIUM_SMALL_LINES = [
    [0, 0, 2, 0, 2, -1, 0],
    [0, 0, -2, 0, -2, 1, 0],
    [-2, 2, 0, 1, -1, 0, 0],
    [2, -2, 0, -1, 1, 0, 0],
    [0, 2, 0, 2, 0, -1, -1],
    [0, -2, 0, -2, 0, 1, 1],
    [0, -1, 2, 2, 0, -1, 0],
    [0, 1, -2, -2, 0, 1, 0],
    [2, 0, 2, 0, 0, -1, -1],
    [-2, 0, -2, 0, 0, 1, 1],
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    audit = load_json(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json")
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
        for line in MEDIUM_SMALL_LINES
    ]
    medium_small_items = [
        record
        for record in audit["records"]
        if record["audit"].get("priority_bucket") == "medium_priority_small_map_backlog"
    ]
    audited_lines = {
        tuple(block["line_bundle"])
        for record in medium_small_items
        for block in record["audit"]["missing_character_blocks"]
    }
    gates = {
        "imports_medium_small_records": gate(
            len(medium_small_items) == 6,
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "probe targets the six medium-priority small-map unresolved records",
        ),
        "all_audited_lines_covered": gate(
            audited_lines == {tuple(line) for line in MEDIUM_SMALL_LINES},
            "medium-small audited missing line blocks",
            "all audited medium-small line patterns are covered by the E2 probe",
        ),
        "all_e2_maps_are_equivariant": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in records),
            "medium-small E1 first-page maps",
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
            "medium-small first-page complexes",
            "all consecutive d1 compositions vanish",
        ),
        "all_records_have_actual_characters": gate(
            len(records) == len(MEDIUM_SMALL_LINES)
            and all(record["actual"] for record in records),
            "medium-small E2 character computation",
            "every medium-small line pattern has a computed actual character",
        ),
    }
    return {
        "scope": "medium-priority radius-3 small-map E2 character probe",
        "status": "medium_small_e2_characters_resolved",
        "records": records,
        "resolved_actuals": {
            str(record["line_bundle"]): record["actual"] for record in records
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Medium-Small E2 Probe",
        "",
        f"Status: `{report['status']}`",
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
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_small_e2_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"records={len(report['records'])}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
