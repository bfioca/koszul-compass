#!/usr/bin/env python3
"""Branch-close the residual candidate from the top Serre-orbit closure."""

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
TOP_ORBIT = (0, 0, -2, 1, -1, 1, -1)
TOP_ORBIT_DUAL = tuple(-value for value in TOP_ORBIT)
RESIDUAL_ORBIT = (-2, 2, -1, -1, 1, 0, 1)
RESIDUAL_ORBIT_DUAL = tuple(-value for value in RESIDUAL_ORBIT)
TARGET_LABEL = "window6_radius4_adjacency_filtered_1_known_line_resolved"


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


def actual_for_branch(
    line: list[int],
    cohomology: list[int],
    *,
    top_trace: int,
    residual_trace: int,
) -> dict[str, Any]:
    tup = tuple(line)
    if tup == TOP_ORBIT:
        if cohomology != [0, 0, 1, 0]:
            raise ValueError((line, cohomology))
        return {"H2": rep(1, top_trace)}
    if tup == TOP_ORBIT_DUAL:
        if cohomology != [0, 1, 0, 0]:
            raise ValueError((line, cohomology))
        return {"H1": rep(1, top_trace)}
    if tup == RESIDUAL_ORBIT:
        if cohomology != [0, 2, 0, 0]:
            raise ValueError((line, cohomology))
        return {"H1": rep(2, residual_trace)}
    if tup == RESIDUAL_ORBIT_DUAL:
        if cohomology != [0, 0, 2, 0]:
            raise ValueError((line, cohomology))
        return {"H2": rep(2, residual_trace)}
    raise ValueError(line)


def apply_branch(
    characters: dict[str, Any],
    *,
    top_trace: int,
    residual_trace: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    still_unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            if cert["actual_character_computed"] or not any(cert["cohomology"]):
                continue
            orbit = serre_orbit(cert["line_bundle"])
            if orbit not in {TOP_ORBIT, RESIDUAL_ORBIT}:
                still_unresolved.append(
                    {
                        "sector": sector_key,
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
                        "reason": "outside_top_residual_branch_orbits",
                    }
                )
                continue
            actual = actual_for_branch(
                cert["line_bundle"],
                cert["cohomology"],
                top_trace=top_trace,
                residual_trace=residual_trace,
            )
            cert["actual"] = actual
            cert["method"] = (
                "top_residual_bounded_branch_"
                f"top_trace_{top_trace:+d}_residual_trace_{residual_trace:+d}"
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
        "top_trace": top_trace,
        "residual_trace": residual_trace,
        "filled_blocks": filled,
        "filled_block_count": len(filled),
        "remaining_unresolved_blocks": still_unresolved,
        "remaining_unresolved_block_count": len(still_unresolved),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    source = load_json(SOURCE_REPORT)
    top_closure = load_json(
        REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.json"
    )
    conf = split["full_picard_presentation_7914"]["conf"]
    source_pair = [
        (resolved, filtered)
        for resolved, filtered in zip(
            source["resolved_records"], source["filtered_candidate_records"]
        )
        if filtered["label"] == TARGET_LABEL
    ]
    if len(source_pair) != 1:
        raise RuntimeError(f"expected one target candidate, found {len(source_pair)}")
    source_resolved, source_filtered = source_pair[0]

    branch_records = []
    for top_trace in [1, -1]:
        for residual_trace in [2, 0, -2]:
            certified = copy.deepcopy(source_resolved)
            characters, resolution = apply_branch(
                certified["characters"],
                top_trace=top_trace,
                residual_trace=residual_trace,
            )
            certified["characters"] = characters
            certified["top_residual_branch_resolution"] = resolution
            certified["character_certified"] = all(
                sector["all_characters_computed"] for sector in characters.values()
            )
            certified["vectorlike_pair_prediction"] = prediction_from_characters(characters)

            filtered = candidate_certificate_from_5259_record(
                label=(
                    f"batch2_{source_filtered['label']}"
                    f"_top_{top_trace:+d}_residual_{residual_trace:+d}"
                ),
                record=certified,
                conf=conf,
            )
            filtered["source_batch"] = "batch2"
            filtered["source_window"] = source_filtered["source_window"]
            filtered["source_filtered_label"] = source_filtered["source_filtered_label"]
            filtered["top_residual_branch_resolution"] = resolution
            if not certified["character_certified"]:
                filtered["classification"] = {
                    "category": "unresolved",
                    "status": "top_residual_branch_still_character_incomplete",
                    "reason": (
                        "top and residual Serre orbit branches were filled, but "
                        "other line-character blocks remain"
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
    gates = {
        "source_report_passes": gate(
            source["all_gates_pass"],
            str(SOURCE_REPORT),
            "residual closure starts from the passing batch-2 known-line report",
        ),
        "top_closure_identifies_one_residual_candidate": gate(
            top_closure["all_gates_pass"]
            and top_closure["summary"]["categories"]
            == {"phenomenologically obstructed": 8, "unresolved": 2},
            str(REPORTS / "phenomenology_guided_q1_radius4_top_orbit_branch_closure.json"),
            "top-orbit closure leaves one candidate unresolved under two top-sign branches",
        ),
        "six_branches_tested": gate(
            len(branch_records) == 6
            and sum(
                record["top_residual_branch_resolution"]["filled_block_count"]
                for record in branch_records
            )
            == 24
            and all(
                record["top_residual_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                == 0
                for record in branch_records
            ),
            "top residual branch records",
            "two top signs times three residual trace branches complete the candidate",
        ),
        "all_branches_classified": gate(
            dict(sorted(categories.items())) == {"phenomenologically obstructed": 6}
            and dict(sorted(statuses.items()))
            == {
                "dangerous_10_5bar_5bar_operator_allowed": 2,
                "rejected_spectrum_signature_not_q1_three_family": 4,
            },
            "top residual branch classifications",
            "every residual branch is classified by the phenomenology filter",
        ),
        "no_viable_branch_found": gate(
            len(viable) == 0,
            "top residual branch classifications",
            "no completion of the remaining top-orbit candidate is viable",
        ),
    }
    return {
        "scope": "bounded branch closure for the residual candidate from the top Serre orbit",
        "status": "no_viable_candidate_found_in_top_residual_branches"
        if not viable
        else "viable_candidate_found_in_top_residual_branches",
        "target_candidate": TARGET_LABEL,
        "orbits": {
            "top": {"representative": list(TOP_ORBIT), "dual": list(TOP_ORBIT_DUAL)},
            "residual": {
                "representative": list(RESIDUAL_ORBIT),
                "dual": list(RESIDUAL_ORBIT_DUAL),
            },
        },
        "summary": {
            "branch_count": len(branch_records),
            "filled_blocks": sum(
                record["top_residual_branch_resolution"]["filled_block_count"]
                for record in branch_records
            ),
            "remaining_unresolved_blocks": sum(
                record["top_residual_branch_resolution"][
                    "remaining_unresolved_block_count"
                ]
                for record in branch_records
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
        "# Radius-4 Top Residual Branch Closure",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- target candidate: `{report['target_candidate']}`",
        f"- top orbit: `{report['orbits']['top']}`",
        f"- residual orbit: `{report['orbits']['residual']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Branch Classifications", ""])
    for record in report["branch_records"]:
        res = record["top_residual_branch_resolution"]
        lines.append(
            "- "
            f"`{record['label']}`: "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; "
            f"filled `{res['filled_block_count']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The only candidate left incomplete by the top-orbit branch closure "
                "has one additional dimension-two Serre orbit. All six compatible "
                "top/residual character branches are nonviable: four lose the q=1 "
                "signature and two allow a dangerous 10*5bar*5bar operator."
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
            REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius4_top_residual_branch_closure.md"
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
