#!/usr/bin/env python3
"""Rank missing line-character demands in the selected radius-4 frontier."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

KNOWN_LINE_REPORTS = [
    ("batch1", REPORTS / "phenomenology_guided_q1_radius4_known_line_resolved.json"),
    ("batch2", REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def neg(line: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(-value for value in line)


def serre_orbit_key(line: tuple[int, ...]) -> tuple[int, ...]:
    dual = neg(line)
    return min(line, dual)


def line_label(line: tuple[int, ...]) -> str:
    return "[" + ",".join(str(value) for value in line) + "]"


def candidate_id(batch: str, record: dict[str, Any]) -> str:
    return f"{batch}:{record['label']}"


def build_report() -> dict[str, Any]:
    loaded = [(batch, path, load_json(path)) for batch, path in KNOWN_LINE_REPORTS]
    records = [
        (batch, record)
        for batch, _path, report in loaded
        for record in report["filtered_candidate_records"]
    ]

    orbit_blocks: dict[tuple[int, ...], list[dict[str, Any]]] = defaultdict(list)
    candidate_missing_orbits: dict[str, set[tuple[int, ...]]] = defaultdict(set)
    candidate_metadata: dict[str, dict[str, Any]] = {}
    status_counts = Counter()
    raw_block_count = 0

    for batch, record in records:
        cid = candidate_id(batch, record)
        status_counts[record["classification"]["status"]] += 1
        candidate_metadata[cid] = {
            "batch": batch,
            "label": record["label"],
            "source_window": record["source_window"],
            "source_filtered_label": record["source_filtered_label"],
            "classification": record["classification"],
            "desired_q1": record["spectrum_certificate"][
                "desired_q1_three_family_signature"
            ],
            "vectorlike_prediction": record["spectrum_certificate"][
                "vectorlike_prediction"
            ],
        }
        for block in record["radius4_known_line_resolution"]["unresolved_blocks"]:
            raw_block_count += 1
            line = tuple(block["line_bundle"])
            orbit = serre_orbit_key(line)
            candidate_missing_orbits[cid].add(orbit)
            orbit_blocks[orbit].append(
                {
                    "candidate": cid,
                    "batch": batch,
                    "label": record["label"],
                    "line_bundle": list(line),
                    "sector": block["sector"],
                    "cohomology": block["cohomology"],
                    "reason": block["reason"],
                    "summand_index": block.get("summand_index"),
                    "summand_pair": block.get("summand_pair"),
                    "classification": record["classification"],
                }
            )

    candidates_by_missing_orbits = Counter(
        len(orbits)
        for cid, orbits in candidate_missing_orbits.items()
        if candidate_metadata[cid]["classification"]["status"]
        == "known_line_resolution_still_incomplete"
    )
    known_line_incomplete_candidates = [
        {
            **candidate_metadata[cid],
            "candidate": cid,
            "missing_serre_orbit_count": len(orbits),
            "missing_serre_orbits": [line_label(orbit) for orbit in sorted(orbits)],
        }
        for cid, orbits in candidate_missing_orbits.items()
        if candidate_metadata[cid]["classification"]["status"]
        == "known_line_resolution_still_incomplete"
    ]
    known_line_incomplete_candidates.sort(
        key=lambda item: (
            item["missing_serre_orbit_count"],
            item["batch"],
            item["source_window"],
            item["label"],
        )
    )

    demand_rows = []
    for orbit, blocks in orbit_blocks.items():
        candidate_set = sorted({block["candidate"] for block in blocks})
        sector_counts = Counter(block["sector"] for block in blocks)
        cohomology_counts = Counter(str(block["cohomology"]) for block in blocks)
        demand_rows.append(
            {
                "serre_orbit_representative": list(orbit),
                "dual_representative": list(neg(orbit)),
                "block_count": len(blocks),
                "candidate_count": len(candidate_set),
                "candidate_ids": candidate_set,
                "sector_counts": dict(sorted(sector_counts.items())),
                "cohomology_counts": dict(sorted(cohomology_counts.items())),
                "example_blocks": blocks[:6],
            }
        )
    demand_rows.sort(
        key=lambda row: (
            -row["candidate_count"],
            -row["block_count"],
            row["serre_orbit_representative"],
        )
    )

    mass_level_unresolved = [
        {
            **candidate_metadata[cid],
            "candidate": cid,
            "missing_serre_orbit_count": len(candidate_missing_orbits.get(cid, set())),
        }
        for cid in sorted(candidate_metadata)
        if candidate_metadata[cid]["classification"]["category"] == "unresolved"
        and candidate_metadata[cid]["classification"]["status"]
        != "known_line_resolution_still_incomplete"
    ]

    gates = {
        "source_reports_pass": gate(
            all(report["all_gates_pass"] for _batch, _path, report in loaded),
            ", ".join(str(path) for _batch, path, _report in loaded),
            "missing-line demand imports only passing known-line reports",
        ),
        "raw_block_count_matches_summaries": gate(
            raw_block_count
            == sum(
                report["summary"]["remaining_unresolved_blocks"]
                for _batch, _path, report in loaded
            )
            == 70,
            "known-line unresolved blocks",
            "raw unresolved-block count agrees with batch summaries",
        ),
        "frontier_status_counts_match": gate(
            dict(sorted(status_counts.items()))
            == {
                "known_line_resolution_still_incomplete": 27,
                "negative_control_doublet_triplet_obstruction": 16,
                "no_certified_triplet_mass_operator_found": 1,
                "no_triplet_mass_in_certified_singlet_monoid": 1,
            },
            "combined candidate classifications",
            "status counts match combined known-line frontier",
        ),
        "demand_rows_cover_all_blocks": gate(
            sum(row["block_count"] for row in demand_rows) == raw_block_count,
            "missing Serre-orbit demand rows",
            "ranked demand rows cover every missing block",
        ),
        "known_line_incomplete_candidates_ranked": gate(
            len(known_line_incomplete_candidates) == 27
            and all(
                item["missing_serre_orbit_count"] > 0
                for item in known_line_incomplete_candidates
            ),
            "known-line incomplete candidate list",
            "every character-incomplete candidate has a ranked missing-orbit list",
        ),
        "mass_level_unresolved_separated": gate(
            len(mass_level_unresolved) == 1
            and mass_level_unresolved[0]["classification"]["status"]
            == "no_certified_triplet_mass_operator_found",
            "mass-level unresolved records",
            "character-complete but mass-operator unresolved records are separated",
        ),
    }

    return {
        "scope": "ranked missing line-character demand for selected radius-4 frontier",
        "status": "missing_line_probe_queue_emitted",
        "summary": {
            "source_reports": [str(path) for _batch, path, _report in loaded],
            "candidate_records": len(records),
            "known_line_incomplete_candidates": len(known_line_incomplete_candidates),
            "mass_level_unresolved_candidates": len(mass_level_unresolved),
            "raw_missing_blocks": raw_block_count,
            "unique_missing_serre_orbits": len(demand_rows),
            "candidates_by_missing_serre_orbit_count": dict(
                sorted(candidates_by_missing_orbits.items())
            ),
            "status_counts": dict(sorted(status_counts.items())),
        },
        "top_missing_serre_orbits": demand_rows[:30],
        "all_missing_serre_orbits": demand_rows,
        "known_line_incomplete_candidates": known_line_incomplete_candidates,
        "mass_level_unresolved_candidates": mass_level_unresolved,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Missing Line Demand",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Top Missing Serre Orbits", ""])
    for row in report["top_missing_serre_orbits"][:15]:
        lines.append(
            "- "
            f"`{row['serre_orbit_representative']}` / "
            f"`{row['dual_representative']}`: "
            f"candidates `{row['candidate_count']}`, blocks `{row['block_count']}`, "
            f"sectors `{row['sector_counts']}`"
        )
    lines.extend(["", "## Lowest-Cost Candidate Unlocks", ""])
    for item in report["known_line_incomplete_candidates"][:15]:
        lines.append(
            "- "
            f"`{item['candidate']}`: missing orbits "
            f"`{item['missing_serre_orbit_count']}`, "
            f"`{item['classification']['status']}`"
        )
    lines.extend(["", "## Mass-Level Unresolved", ""])
    for item in report["mass_level_unresolved_candidates"]:
        lines.append(
            "- "
            f"`{item['candidate']}`: `{item['classification']['status']}`; "
            f"{item['classification']['reason']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The remaining selected radius-4 unknowns are now split into a "
                "character-computation queue and a separate mass-operator uncertainty. "
                "The Serre-orbit ranking identifies line-character probes with the "
                "largest expected unlock value for the q=1 obstruction filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius4_missing_line_demand.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
