#!/usr/bin/env python3
"""Branch-close the cumulative7 ninth orbit together with its residual orbit."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    representation_record,
    sector_record,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)

SOURCE_REPORT = REPORTS / "phenomenology_guided_q1_radius4_batch2_known_line_resolved.json"
NINTH_ORBIT = (-2, 0, -3, 0, 1, 1, 0)
NINTH_ORBIT_DUAL = tuple(-value for value in NINTH_ORBIT)
RESIDUAL_ORBIT = (-1, 0, -3, 0, 0, 1, 0)
RESIDUAL_ORBIT_DUAL = tuple(-value for value in RESIDUAL_ORBIT)
TARGET_CANDIDATE = "batch2:window3_radius4_adjacency_filtered_1_known_line_resolved"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep(dimension: int, trace: int) -> dict[str, Any]:
    return representation_record(dimension, trace)


def serre_orbit(line: list[int]) -> tuple[int, ...]:
    tup = tuple(line)
    dual = tuple(-value for value in tup)
    return min(tup, dual)


def actual_for_line(
    line: list[int],
    cohomology: list[int],
    *,
    ninth_trace: int,
    residual_h1_trace: int,
    residual_h2_trace: int,
) -> dict[str, Any]:
    tup = tuple(line)
    if tup == NINTH_ORBIT:
        if cohomology != [0, 0, 4, 0]:
            raise ValueError((line, cohomology))
        return {"H2": rep(4, ninth_trace)}
    if tup == NINTH_ORBIT_DUAL:
        if cohomology != [0, 4, 0, 0]:
            raise ValueError((line, cohomology))
        return {"H1": rep(4, ninth_trace)}
    if tup == RESIDUAL_ORBIT:
        if cohomology != [0, 2, 2, 0]:
            raise ValueError((line, cohomology))
        return {
            "H1": rep(2, residual_h1_trace),
            "H2": rep(2, residual_h2_trace),
        }
    if tup == RESIDUAL_ORBIT_DUAL:
        if cohomology != [0, 2, 2, 0]:
            raise ValueError((line, cohomology))
        return {
            "H1": rep(2, residual_h2_trace),
            "H2": rep(2, residual_h1_trace),
        }
    raise ValueError(line)


def apply_branch(
    characters: dict[str, Any],
    *,
    ninth_trace: int,
    residual_h1_trace: int,
    residual_h2_trace: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    still_unresolved = []
    branch_orbits = {NINTH_ORBIT, RESIDUAL_ORBIT}
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            orbit = serre_orbit(cert["line_bundle"])
            if orbit not in branch_orbits:
                still_unresolved.append(
                    {
                        "sector": sector_key,
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "outside_ninth_residual_branch_orbits",
                    }
                )
                continue
            actual = actual_for_line(
                cert["line_bundle"],
                cert["cohomology"],
                ninth_trace=ninth_trace,
                residual_h1_trace=residual_h1_trace,
                residual_h2_trace=residual_h2_trace,
            )
            cert["actual"] = actual
            cert["method"] = (
                "ninth_residual_bounded_branch_"
                f"ninth_trace_{ninth_trace:+d}_"
                f"residual_h1_{residual_h1_trace:+d}_"
                f"residual_h2_{residual_h2_trace:+d}"
            )
            cert["actual_character_computed"] = True
            filled.append(
                {
                    "sector": sector_key,
                    "line_bundle": cert["line_bundle"],
                    "cohomology": cert["cohomology"],
                    "actual": actual,
                }
            )

    for sector_key, target_keys in SECTOR_TARGET_KEYS.items():
        sector = resolved[sector_key]
        resolved[sector_key] = sector_record(
            label=SECTOR_LABELS[sector_key],
            line_certificates=sector["line_certificates"],
            cohomology_degree_keys=target_keys,
        )
    return resolved, {
        "ninth_trace": ninth_trace,
        "residual_h1_trace": residual_h1_trace,
        "residual_h2_trace": residual_h2_trace,
        "filled_blocks": filled,
        "filled_block_count": len(filled),
        "remaining_unresolved_blocks": still_unresolved,
        "remaining_unresolved_block_count": len(still_unresolved),
    }


def load_target_record() -> dict[str, Any]:
    report = load_json(SOURCE_REPORT)
    for resolved, filtered in zip(report["resolved_records"], report["filtered_candidate_records"]):
        if f"batch2:{filtered['label']}" == TARGET_CANDIDATE:
            return {"resolved": resolved, "filtered": filtered}
    raise RuntimeError(f"target candidate not found: {TARGET_CANDIDATE}")


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    cumulative7 = load_json(REPORTS / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier.json")
    cumulative7_verification = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier_verification.json"
    )
    ninth_partial = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_ninth_orbit_branch_closure.json"
    )
    ninth_partial_verification = load_json(
        REPORTS
        / "phenomenology_guided_q1_radius4_ninth_orbit_branch_closure_verification.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]
    target = load_target_record()
    branch_records = []
    for ninth_trace in [4, 2, 0, -2, -4]:
        for residual_h1_trace in [2, 0, -2]:
            for residual_h2_trace in [2, 0, -2]:
                certified = copy.deepcopy(target["resolved"])
                characters, resolution = apply_branch(
                    certified["characters"],
                    ninth_trace=ninth_trace,
                    residual_h1_trace=residual_h1_trace,
                    residual_h2_trace=residual_h2_trace,
                )
                certified["characters"] = characters
                certified["ninth_residual_branch_resolution"] = resolution
                certified["character_certified"] = all(
                    sector["all_characters_computed"] for sector in characters.values()
                )
                certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)
                filtered = candidate_certificate_from_5259_record(
                    label=(
                        f"batch2_{target['filtered']['label']}"
                        f"_ninth_{ninth_trace:+d}"
                        f"_residual_h1_{residual_h1_trace:+d}"
                        f"_h2_{residual_h2_trace:+d}"
                    ),
                    record=certified,
                    conf=conf,
                )
                filtered["source_batch"] = "batch2"
                filtered["source_window"] = target["filtered"]["source_window"]
                filtered["source_filtered_label"] = target["filtered"][
                    "source_filtered_label"
                ]
                filtered["ninth_residual_branch_resolution"] = resolution
                if not certified["character_certified"]:
                    filtered["classification"] = {
                        "category": "unresolved",
                        "status": "ninth_residual_branch_still_character_incomplete",
                        "reason": (
                            "the ninth and residual Serre orbit branches were filled, "
                            "but other missing line-character blocks remain"
                        ),
                    }
                else:
                    apply_monoid_obstruction_override(filtered)
                branch_records.append(filtered)

    categories = Counter(record["classification"]["category"] for record in branch_records)
    statuses = Counter(record["classification"]["status"] for record in branch_records)
    viable = [
        record for record in branch_records if record["classification"]["category"] == "viable"
    ]
    next_orbit = cumulative7["summary"]["next_probe_orbit"]
    gates = {
        "cumulative7_frontier_verified": gate(
            cumulative7["all_gates_pass"]
            and cumulative7_verification["all_gates_pass"]
            and next_orbit["serre_orbit_representative"] == list(NINTH_ORBIT),
            str(REPORTS / "phenomenology_guided_q1_radius4_cumulative7_adjusted_frontier.json"),
            "combined branch closure starts from the verified cumulative7 bottleneck",
        ),
        "ninth_partial_closure_verified": gate(
            ninth_partial["all_gates_pass"]
            and ninth_partial_verification["all_gates_pass"]
            and ninth_partial["summary"]["remaining_unresolved_blocks"] == 10,
            str(REPORTS / "phenomenology_guided_q1_radius4_ninth_orbit_branch_closure.json"),
            "ninth-only branch closure identifies a residual orbit for the same candidate",
        ),
        "target_candidate_loaded": gate(
            f"batch2:{target['filtered']['label']}" == TARGET_CANDIDATE,
            str(SOURCE_REPORT),
            "the single candidate touched by the cumulative7 next orbit is loaded",
        ),
        "all_trace_branches_tested": gate(
            len(branch_records) == 45
            and sum(
                record["ninth_residual_branch_resolution"]["filled_block_count"]
                for record in branch_records
            )
            == 180
            and all(
                record["ninth_residual_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in branch_records
            )
            and sum(
                1
                for record in branch_records
                if record["character_certificate"]["character_certified"]
            )
            == 45,
            "ninth/residual Serre orbit branch records",
            "five ninth traces times nine residual H1/H2 traces fully certify the candidate",
        ),
        "classification_counts_match": gate(
            dict(sorted(categories.items())) == {"phenomenologically obstructed": 45}
            and dict(sorted(statuses.items()))
            == {
                "negative_control_doublet_triplet_obstruction": 3,
                "rejected_spectrum_signature_not_q1_three_family": 42,
            },
            "ninth/residual Serre orbit branch classifications",
            "all combined branches are rejected by the q=1/phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            len(viable) == 0,
            "ninth/residual Serre orbit branch classifications",
            "no combined branch of the cumulative7 next candidate is viable",
        ),
    }
    return {
        "scope": "bounded branch closure for the cumulative7 ninth orbit and residual orbit",
        "status": "no_viable_candidate_found_in_ninth_residual_branches"
        if not viable
        else "viable_candidate_found_in_ninth_residual_branches",
        "target_candidate": TARGET_CANDIDATE,
        "orbits": {
            "ninth": {"representative": list(NINTH_ORBIT), "dual": list(NINTH_ORBIT_DUAL)},
            "residual": {
                "representative": list(RESIDUAL_ORBIT),
                "dual": list(RESIDUAL_ORBIT_DUAL),
            },
        },
        "summary": {
            "candidate_count": 1,
            "branch_count": len(branch_records),
            "filled_blocks": sum(
                record["ninth_residual_branch_resolution"]["filled_block_count"]
                for record in branch_records
            ),
            "remaining_unresolved_blocks": sum(
                record["ninth_residual_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                for record in branch_records
            ),
            "character_certified_branches": sum(
                1
                for record in branch_records
                if record["character_certificate"]["character_certified"]
            ),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
        },
        "branch_records": branch_records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-4 Ninth Residual Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- target candidate: `{report['target_candidate']}`",
        f"- ninth orbit: `{report['orbits']['ninth']}`",
        f"- residual orbit: `{report['orbits']['residual']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["ninth_residual_branch_resolution"]
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{res['filled_block_count']}`; "
            f"remaining `{res['remaining_unresolved_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The cumulative7 ninth-orbit candidate has one additional mixed-degree "
                "residual Serre orbit. The combined 45 trace completions close both "
                "orbits: 42 branches lose the q=1 signature and 3 q=1 survivors "
                "reproduce the negative-control doublet-triplet obstruction."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius4_ninth_residual_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_ninth_residual_branch_closure.md"
        ),
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
