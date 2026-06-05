#!/usr/bin/env python3
"""Verify the radius-4 known-line resolution pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

BATCH_CONFIGS = {
    "batch1": {
        "report": REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json",
        "markdown": REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.md",
        "verification": REPORTS
        / "phenomenology_guided_q1_radius4_known_line_resolved_verification.json",
        "attempted": 21,
        "filled": 40,
        "remaining": 40,
        "incompatible": 14,
        "character_certified": 7,
        "categories": {"phenomenologically obstructed": 7, "unresolved": 14},
        "statuses": {
            "known_line_resolution_still_incomplete": 14,
            "negative_control_doublet_triplet_obstruction": 7,
        },
    },
    "batch2": {
        "report": REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json",
        "markdown": REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.md",
        "verification": REPORTS
        / "phenomenology_guided_q1_radius4_batch2_known_line_resolved_verification.json",
        "attempted": 24,
        "filled": 52,
        "remaining": 30,
        "incompatible": 12,
        "character_certified": 11,
        "categories": {"phenomenologically obstructed": 10, "unresolved": 14},
        "statuses": {
            "known_line_resolution_still_incomplete": 13,
            "negative_control_doublet_triplet_obstruction": 9,
            "no_certified_triplet_mass_operator_found": 1,
            "no_triplet_mass_in_certified_singlet_monoid": 1,
        },
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def has_required_sections(record: dict[str, Any]) -> bool:
    return {
        "spectrum_certificate",
        "character_certificate",
        "mass_operator_table",
        "proton_decay_operator_table",
        "classification",
    }.issubset(record)


def verify(batch: str) -> dict[str, Any]:
    config = BATCH_CONFIGS[batch]
    path = config["report"]
    md_path = config["markdown"]
    report = load_json(path)
    md_text = md_path.read_text(encoding="utf-8")
    records = report["filtered_candidate_records"]
    resolved = report["resolved_records"]
    certified = [
        item for item in resolved if item["character_certified"]
    ]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"],
            str(path),
            "builder-side known-line gates passed",
        ),
        "attempts_all_radius4_unresolved_records": gate(
            report["batch"] == batch
            and report["summary"]["attempted_unresolved_records"]
            == len(records)
            == config["attempted"],
            str(path),
            "all selected radius-4 unresolved records were attempted",
        ),
        "verified_known_lines_fill_blocks": gate(
            report["summary"]["filled_blocks"] == config["filled"]
            and report["summary"]["remaining_unresolved_blocks"] == config["remaining"]
            and report["summary"]["incompatible_known_actuals"] == config["incompatible"],
            str(path),
            "known-line probes filled the expected block count and recorded mismatches",
        ),
        "certified_records_are_filtered": gate(
            len(certified)
            == report["summary"]["character_certified_records"]
            == config["character_certified"]
            and all(
                record["classification"]["category"]
                in {"phenomenologically obstructed", "unresolved", "viable"}
                and record["classification"]["status"]
                not in {
                    "missing_character_or_charge_level_data",
                    "known_line_resolution_still_incomplete",
                }
                for record in records
                if record["character_certificate"]["character_certified"]
            ),
            str(path),
            "every newly character-certified record was rerun through the phenomenology filter",
        ),
        "classification_counts_match": gate(
            report["summary"]["categories"] == config["categories"]
            and report["summary"]["statuses"] == config["statuses"],
            str(path),
            "known-line resolution produces the expected classification distribution",
        ),
        "required_sections_present": gate(
            all(has_required_sections(record) for record in records)
            and all(
                record["mass_operator_table"] is not None
                and record["proton_decay_operator_table"] is not None
                for record in records
                if record["character_certificate"]["character_certified"]
            ),
            str(path),
            "all records have deliverable sections and certified records have mass/proton tables",
        ),
        "no_viable_candidate_found": gate(
            report["summary"]["viable_count"] == len(viable) == 0,
            str(path),
            "no newly resolved radius-4 record passes the charge-level filter",
        ),
        "markdown_exposes_summary": gate(
            "Status: `no_viable_candidate_found_after_known_line_resolution`" in md_text
            and f"Batch: `{batch}`" in md_text
            and f"filled_blocks: `{config['filled']}`" in md_text
            and any(status in md_text for status in config["statuses"]),
            str(md_path),
            "markdown exposes the known-line resolution summary",
        ),
    }
    return {
        "scope": "verification for radius-4 known-line resolution pass",
        "batch": batch,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", choices=sorted(BATCH_CONFIGS), default="batch1")
    parser.add_argument(
        "--json-out",
        default=None,
    )
    args = parser.parse_args()
    result = verify(args.batch)
    out = Path(args.json_out) if args.json_out else BATCH_CONFIGS[args.batch]["verification"]
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
