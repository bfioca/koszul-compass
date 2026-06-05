#!/usr/bin/env python3
"""Resolve the radius-3 medium-priority three-family record by E2 characters."""

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

MEDIUM_LINES = [
    [2, 0, 2, 0, 1, -1, -1],
    [-1, 0, -2, 0, -2, 1, 1],
    [-2, 0, -2, 0, -1, 1, 1],
    [1, 0, 2, 0, 2, -1, -1],
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
        for line in MEDIUM_LINES
    ]
    medium_items = [
        record
        for record in audit["records"]
        if record["audit"].get("priority_bucket") == "medium_priority_three_family"
    ]
    expected_actuals = {
        tuple([2, 0, 2, 0, 1, -1, -1]): {
            "H1": {"dimension": 2, "nonidentity_trace": -2, "multiplicities": {"+": 0, "-": 2}, "regular_multiplicity": None},
            "H2": {"dimension": 1, "nonidentity_trace": -1, "multiplicities": {"+": 0, "-": 1}, "regular_multiplicity": None},
        },
        tuple([-1, 0, -2, 0, -2, 1, 1]): {
            "H2": {"dimension": 1, "nonidentity_trace": -1, "multiplicities": {"+": 0, "-": 1}, "regular_multiplicity": None},
        },
        tuple([-2, 0, -2, 0, -1, 1, 1]): {
            "H1": {"dimension": 1, "nonidentity_trace": -1, "multiplicities": {"+": 0, "-": 1}, "regular_multiplicity": None},
            "H2": {"dimension": 2, "nonidentity_trace": -2, "multiplicities": {"+": 0, "-": 2}, "regular_multiplicity": None},
        },
        tuple([1, 0, 2, 0, 2, -1, -1]): {
            "H1": {"dimension": 1, "nonidentity_trace": -1, "multiplicities": {"+": 0, "-": 1}, "regular_multiplicity": None},
        },
    }
    gates = {
        "imports_single_medium_three_family_record": gate(
            len(medium_items) == 1,
            str(REPORTS / "phenomenology_guided_q1_radius3_unresolved_audit.json"),
            "probe targets the single medium-priority three-family unresolved record",
        ),
        "all_medium_lines_processed": gate(
            [record["line_bundle"] for record in records] == MEDIUM_LINES,
            "medium-three-family line list",
            "all four missing line/dual blocks were processed",
        ),
        "first_page_maps_are_equivariant": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in records),
            "medium-three-family E1 first-page maps",
            "all d1 maps are block diagonal in reconstructed Z2 eigenspaces",
        ),
        "e2_characters_match_expected": gate(
            all(record["actual"] == expected_actuals[tuple(record["line_bundle"])] for record in records),
            "medium-three-family E2 character computation",
            "E2 characters reproduce recorded cohomology dimensions with nonregular Z2 multiplicities",
        ),
    }
    return {
        "scope": "medium-priority radius-3 three-family E2 character probe",
        "status": "medium_three_family_e2_characters_resolved_nonregular",
        "target_record": {
            "window": medium_items[0]["window"] if medium_items else None,
            "label": medium_items[0]["label"] if medium_items else None,
            "source_radius2_record": medium_items[0]["source_radius2_record"] if medium_items else None,
        },
        "records": records,
        "resolved_actuals": {
            str(list(key)): value for key, value in expected_actuals.items()
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Medium Three-Family E2 Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- target record: `{report['target_record']}`",
    ]
    for record in report["records"]:
        lines.append(f"- `{record['line_bundle']}`: actual `{record['actual']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_medium_three_family_e2_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"target_record={report['target_record']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
