#!/usr/bin/env python3
"""Evaluate the two character branches for the final sign-conflict record."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import sector_record  # noqa: E402
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    SECTOR_LABELS,
    SECTOR_TARGET_KEYS,
    apply_monoid_obstruction_override,
    prediction_from_characters,
)
from build_phenomenology_guided_q1_radius3_medium_small_rank_resolved import (  # noqa: E402
    apply_exact_monoid_obstruction_override,
)

WINDOW_REPORTS = {
    "window2": REPORTS / "phenomenology_guided_q1_radius3_adjacency_scout_window2.json",
}

CONFLICT_LINES = {
    (-1, 2, 0, 1, 1, -1, 0),
    (1, -2, 0, -1, -1, 1, 0),
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def rep(plus: int, minus: int) -> dict[str, Any]:
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def load_candidate() -> tuple[dict[str, Any], int]:
    report = load_json(WINDOW_REPORTS["window2"])
    for index, record in enumerate(report["certified_records"]):
        if report["filtered_candidate_records"][index]["label"] == "radius3_adjacency_filtered_16":
            return record, index
    raise KeyError("window2/radius3_adjacency_filtered_16 not found")


def apply_branch(
    characters: dict[str, Any], *, actual: dict[str, Any], method: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = copy.deepcopy(characters)
    filled = []
    unresolved = []
    for sector_key, sector in resolved.items():
        for cert in sector["line_certificates"]:
            line = tuple(cert["line_bundle"])
            if not cert["actual_character_computed"] and line in CONFLICT_LINES:
                cert["actual"] = copy.deepcopy(actual)
                cert["method"] = method
                cert["actual_character_computed"] = True
                filled.append(
                    {
                        "sector": sector_key,
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "actual": cert["actual"],
                        "method": method,
                    }
                )
            elif not cert["actual_character_computed"] and any(cert["cohomology"]):
                unresolved.append(
                    {
                        "sector": sector_key,
                        "summand_pair": cert.get("summand_pair"),
                        "line_bundle": cert["line_bundle"],
                        "cohomology": cert["cohomology"],
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
        "filled_blocks": filled,
        "unresolved_blocks": unresolved,
        "filled_block_count": len(filled),
        "unresolved_block_count": len(unresolved),
    }


def build_branch_certificate(
    *,
    branch_label: str,
    actual: dict[str, Any],
    method: str,
    conf: list[list[int]],
    base_record: dict[str, Any],
) -> dict[str, Any]:
    characters, resolution = apply_branch(base_record["characters"], actual=actual, method=method)
    resolved = copy.deepcopy(base_record)
    resolved["characters"] = characters
    resolved["sign_conflict_branch_resolution"] = resolution
    resolved["character_certified"] = all(
        sector["all_characters_computed"] for sector in characters.values()
    )
    resolved["vectorlike_pair_prediction"] = prediction_from_characters(characters)
    resolved["source_window"] = "window2"
    resolved["source_filtered_label"] = "radius3_adjacency_filtered_16"
    filtered = candidate_certificate_from_5259_record(
        label=f"window2_radius3_adjacency_filtered_16_{branch_label}",
        record=resolved,
        conf=conf,
    )
    filtered["source_window"] = "window2"
    filtered["source_filtered_label"] = "radius3_adjacency_filtered_16"
    filtered["sign_conflict_branch_resolution"] = resolution
    if resolved["character_certified"]:
        apply_monoid_obstruction_override(filtered)
        apply_exact_monoid_obstruction_override(filtered)
    return filtered


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    sign_conflict = load_json(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    base, _ = load_candidate()
    regular_actual = {"H1": rep(1, 1), "H2": rep(1, 1)}
    nonregular_actual = {"H1": rep(2, 0), "H2": rep(2, 0)}
    branches = [
        build_branch_certificate(
            branch_label="regular_plus_rank_removed_branch",
            actual=regular_actual,
            method="sign_conflict_branch_plus_rank_removed_regular",
            conf=conf,
            base_record=base,
        ),
        build_branch_certificate(
            branch_label="nonregular_minus_rank_removed_branch",
            actual=nonregular_actual,
            method="sign_conflict_branch_minus_rank_removed_nonregular",
            conf=conf,
            base_record=base,
        ),
    ]
    gates = {
        "imports_sign_conflict": gate(
            sign_conflict["all_gates_pass"]
            and sign_conflict["status"] == "character_certificate_blocked_by_sign_constraint_conflict",
            str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_probe.json"),
            "branch analysis starts from the verified sign-conflict probe",
        ),
        "both_branches_certified": gate(
            len(branches) == 2
            and all(record["character_certificate"]["character_certified"] for record in branches),
            "sign-conflict branch certificates",
            "both abstract rank-character branches produce complete character certificates",
        ),
        "regular_branch_filtered": gate(
            branches[0]["spectrum_certificate"]["desired_q1_three_family_signature"]
            and branches[0]["classification"]["category"] != "viable",
            "regular branch phenomenology filter",
            "the branch that would preserve the desired q=1 signature is not viable",
        ),
        "nonregular_branch_rejected": gate(
            not branches[1]["spectrum_certificate"]["desired_q1_three_family_signature"]
            and branches[1]["classification"]["status"]
            == "rejected_spectrum_signature_not_q1_three_family",
            "nonregular branch phenomenology filter",
            "the nonregular branch loses the desired q=1 signature",
        ),
        "no_branch_viable": gate(
            all(record["classification"]["category"] != "viable" for record in branches),
            "sign-conflict branch certificates",
            "neither mathematically possible branch is viable under the current filter",
        ),
    }
    return {
        "scope": "branch analysis for final radius-3 sign-conflict candidate",
        "status": "sign_conflict_branches_nonviable_under_current_filter",
        "base_candidate": "window2/radius3_adjacency_filtered_16",
        "branch_certificates": branches,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Sign-Conflict Branch Analysis",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- base candidate: `{report['base_candidate']}`",
        "",
        "## Branches",
        "",
    ]
    for record in report["branch_certificates"]:
        lines.append(
            "- "
            f"`{record['label']}`: `{record['classification']['category']}` / "
            f"`{record['classification']['status']}`; prediction "
            f"`{record['spectrum_certificate']['vectorlike_prediction']}`"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "The sign conflict prevents selecting a certified character branch from "
                "the current basis data. However, the two dimension-compatible rank "
                "branches are both nonviable under the current phenomenology filter."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_sign_conflict_branch_analysis.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    for record in report["branch_certificates"]:
        print(record["label"], record["classification"], record["spectrum_certificate"]["vectorlike_prediction"])
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
