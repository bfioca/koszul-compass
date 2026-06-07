#!/usr/bin/env python3
"""Verify the CICY6715 unresolved-character envelope audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

EXPECTED_STATUS = "cicy6715_unresolved_envelope_clean_branch_possible"
EXPECTED_CANDIDATE_STATUS_COUNTS = {
    "clean_branch_possible": 1,
    "no_one_higgs_proton_safe_branch": 3,
    "proton_safe_but_doublet_or_other_obstructed": 1,
}
EXPECTED_CANDIDATE_SUMMARY = {
    229: {
        "status": "proton_safe_but_doublet_or_other_obstructed",
        "unresolved_pair": [3, 4],
        "unresolved_cohomology": [0, 2, 2, 0],
        "branch_count": 100,
        "total_one_higgs_pair_triplet_free_count": 2496,
        "total_one_higgs_proton_safe_count": 1728,
        "total_clean_one_higgs_precup_count": 0,
    },
    245: {
        "status": "no_one_higgs_proton_safe_branch",
        "unresolved_pair": [1, 2],
        "unresolved_cohomology": [0, 2, 2, 0],
        "branch_count": 100,
        "total_one_higgs_pair_triplet_free_count": 2496,
        "total_one_higgs_proton_safe_count": 0,
        "total_clean_one_higgs_precup_count": 0,
    },
    591: {
        "status": "no_one_higgs_proton_safe_branch",
        "unresolved_pair": [0, 1],
        "unresolved_cohomology": [0, 3, 3, 0],
        "branch_count": 400,
        "total_one_higgs_pair_triplet_free_count": 6528,
        "total_one_higgs_proton_safe_count": 0,
        "total_clean_one_higgs_precup_count": 0,
    },
    596: {
        "status": "no_one_higgs_proton_safe_branch",
        "unresolved_pair": [3, 4],
        "unresolved_cohomology": [0, 3, 3, 0],
        "branch_count": 400,
        "total_one_higgs_pair_triplet_free_count": 6528,
        "total_one_higgs_proton_safe_count": 0,
        "total_clean_one_higgs_precup_count": 0,
    },
    766: {
        "status": "clean_branch_possible",
        "unresolved_pair": [3, 4],
        "unresolved_cohomology": [0, 2, 2, 0],
        "branch_count": 100,
        "total_one_higgs_pair_triplet_free_count": 2496,
        "total_one_higgs_proton_safe_count": 1728,
        "total_clean_one_higgs_precup_count": 1728,
    },
}
EXPECTED_BRANCH99_MULTIPLICITIES = {"1": 2, "a": 0, "ab": 0, "b": 0}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def by_model(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(row["model_index"]): row for row in report["candidate_records"]}


def compact_candidate_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": row["status"],
        "unresolved_pair": row["unresolved_pair"],
        "unresolved_cohomology": row["unresolved_cohomology"],
        "branch_count": row["branch_count"],
        "total_one_higgs_pair_triplet_free_count": row[
            "total_one_higgs_pair_triplet_free_count"
        ],
        "total_one_higgs_proton_safe_count": row["total_one_higgs_proton_safe_count"],
        "total_clean_one_higgs_precup_count": row[
            "total_clean_one_higgs_precup_count"
        ],
    }


def verify(report_json: Path, report_md: Path) -> dict[str, Any]:
    report = load_json(report_json)
    md_text = report_md.read_text(encoding="utf-8")
    summary = report["summary"]
    rows = by_model(report)
    model766 = rows[766]
    strongest_branch = model766["closest_branches"][0]
    gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"]
            and all(item["pass"] for item in report["gates"].values()),
            str(report_json),
            "envelope builder gates all pass",
        ),
        "finite_character_envelope_scope_is_stable": gate(
            report["status"] == EXPECTED_STATUS
            and report["parameters"]["target_cicy"] == 6715
            and report["parameters"]["target_option_index"] == 1
            and report["parameters"]["max_branches"] is None
            and summary["candidate_count"] == 5
            and summary["branch_count"] == 1100
            and summary["expected_full_branch_count"] == 1100,
            str(report_json),
            "the five-candidate CICY6715 envelope enumerates all 1100 H1/H2 character branches",
        ),
        "candidate_split_is_stable": gate(
            summary["candidate_status_counts"] == EXPECTED_CANDIDATE_STATUS_COUNTS
            and {model: compact_candidate_summary(row) for model, row in rows.items()}
            == EXPECTED_CANDIDATE_SUMMARY,
            str(report_json),
            "per-model unresolved pairs, branch counts, and clean/proton-safe counts are fixed",
        ),
        "model766_is_only_live_envelope_candidate": gate(
            [row["model_index"] for row in report["clean_branch_candidates"]] == [766]
            and [row["model_index"] for row in report["proton_safe_branch_candidates"]]
            == [229, 766]
            and summary["total_one_higgs_pair_triplet_free_count"] == 20544
            and summary["total_one_higgs_proton_safe_count"] == 3456
            and summary["total_clean_one_higgs_precup_count"] == 1728,
            str(report_json),
            "only model 766 can hide clean one-Higgs pre-cup survivors in the finite envelope",
        ),
        "strongest_branch_is_named": gate(
            strongest_branch["branch_index"] == 99
            and strongest_branch["h1_rep"]["multiplicities"]
            == EXPECTED_BRANCH99_MULTIPLICITIES
            and strongest_branch["h2_rep"]["multiplicities"]
            == EXPECTED_BRANCH99_MULTIPLICITIES
            and strongest_branch["clean_one_higgs_precup_count"] == 192
            and strongest_branch["one_higgs_proton_safe_count"] == 192
            and strongest_branch["one_higgs_pair_triplet_free_count"] == 192
            and strongest_branch["one_higgs_status_counts"]
            == {"pre_cup_survivor_no_triplet_lifting_needed": 192},
            str(report_json),
            "model 766 branch 99 is the highest-ranked envelope completion and has all-trivial unresolved H1/H2 characters",
        ),
        "live_status_is_not_overclaimed": gate(
            report["interpretation"]["clean_branch_possible"] is True
            and report["interpretation"]["bounded_no_clean_branch"] is False
            and "not an actual higher-map representative resolution"
            in report["interpretation"]["note"],
            str(report_json),
            "the artifact records an existential envelope opening without claiming representative certification",
        ),
        "markdown_reports_live_envelope": gate(
            f"Status: `{EXPECTED_STATUS}`" in md_text
            and "branch_count: `1100`" in md_text
            and "total_clean_one_higgs_precup_count: `1728`" in md_text
            and "### CICY `6715` model `766` option `1`" in md_text
            and "clean branch possible: `True`" in md_text,
            str(report_md),
            "markdown exposes the live envelope headline and model 766 target",
        ),
    }
    return {
        "scope": "verification for CICY6715 component-unresolved character envelope audit",
        "all_gates_pass": all(item["pass"] for item in gates.values()),
        "summary": {
            "status": report["status"],
            "candidate_count": summary["candidate_count"],
            "branch_count": summary["branch_count"],
            "total_clean_one_higgs_precup_count": summary[
                "total_clean_one_higgs_precup_count"
            ],
            "live_model": 766,
            "strongest_branch": strongest_branch["branch_index"],
        },
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-json",
        default=str(REPORTS / "cicy6715_component_unresolved_envelope.json"),
    )
    parser.add_argument(
        "--report-md",
        default=str(REPORTS / "cicy6715_component_unresolved_envelope.md"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy6715_component_unresolved_envelope_verification.json"),
    )
    args = parser.parse_args()
    result = verify(Path(args.report_json), Path(args.report_md))
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
