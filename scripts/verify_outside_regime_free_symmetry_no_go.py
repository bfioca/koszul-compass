#!/usr/bin/env python3
"""Verify the outside-regime free-symmetry no-go audit."""

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


def verify() -> dict[str, Any]:
    no_go = load_json(REPORTS / "outside_regime_free_symmetry_no_go.json")
    targets = load_json(REPORTS / "outside_regime_targets.json")
    higgs = load_json(REPORTS / "outside_regime_higgs_candidate_certificate.json")
    best_7484 = load_json(REPORTS / "best_candidate_certificate.json")

    pool = no_go["target_pool_audit"]
    geometry_table = no_go["favourable_geometry_gate_table"]
    nonfav_free = no_go["nonfavourable_recorded_free_symmetry_targets"]
    ranked = no_go["ranked_comparison"]

    gates = {
        "conclusion_is_geometry_no_go": gate(
            no_go["conclusion"]["status"]
            == "no_quotient_compatible_favourable_target_in_current_cicylist"
            and no_go["conclusion"]["no_go_is_at_geometry_selection_gate"]
            and not no_go["conclusion"]["construction_found"],
            "reports/outside_regime_free_symmetry_no_go.json",
            "report concludes no favourable recorded-free target exists",
        ),
        "target_counts_match_parser_report": gate(
            pool["canonical_h11_ge_7_known_nonempty_symmetry_count"]
            == targets["candidate_pool"][
                "canonical_h11_ge_7_known_nonempty_symmetry_count"
            ]
            == 108
            and pool["canonical_h11_ge_7_known_free_symmetry_count"]
            == targets["candidate_pool"]["canonical_h11_ge_7_known_free_symmetry_count"]
            == 62
            and pool["favourable_h11_ge_7_known_nonempty_symmetry_count"]
            == targets["candidate_pool"][
                "favourable_h11_ge_7_known_nonempty_symmetry_count"
            ]
            == 3
            and pool["favourable_h11_ge_7_known_free_symmetry_count"]
            == targets["candidate_pool"][
                "favourable_h11_ge_7_known_free_symmetry_count"
            ]
            == 0,
            "reports/outside_regime_targets.json",
            "no-go report agrees with regenerated target-pool report",
        ),
        "favourable_gate_table_complete": gate(
            [row["num"] for row in geometry_table] == [2544, 3929, 4335]
            and all(row["free_symmetry_option_count"] == 0 for row in geometry_table)
            and all(
                row["first_failing_gate_for_quotient_compatible_goal"]
                == "free_symmetry_required_for_wilson_line_descent"
                for row in geometry_table
            ),
            "reports/outside_regime_free_symmetry_no_go.json",
            "all immediate favourable targets fail at recorded-free-symmetry gate",
        ),
        "nonfavourable_free_targets_recorded": gate(
            len(nonfav_free) == 62
            and all(
                not row["favourable_by_h11_equals_num_projective_factors"]
                for row in nonfav_free
            )
            and all(row["free_symmetry_option_count"] > 0 for row in nonfav_free),
            "reports/outside_regime_free_symmetry_no_go.json",
            "all recorded-free h11>=7 targets are non-favourable in current metadata",
        ),
        "cicy2544_comparison_preserved": gate(
            ranked[0]["geometry"] == "CICY 2544"
            and not ranked[0]["quotient_compatible"]
            and ranked[0]["spectrum"] == higgs["spectrum"]
            and ranked[0]["quality"] == higgs["quality"],
            "reports/outside_regime_higgs_candidate_certificate.json",
            "ranked comparison preserves clean upstairs CICY2544 one-Higgs evidence",
        ),
        "cicy7484_comparison_preserved": gate(
            ranked[1]["geometry"] == "CICY 7484"
            and ranked[1]["quotient_compatible"]
            and ranked[1]["spectrum"] == best_7484["spectrum"]
            and ranked[1]["quality"] == best_7484["quality_caveat"],
            "reports/best_candidate_certificate.json",
            "ranked comparison preserves CICY7484 lift-compatible comparison evidence",
        ),
    }
    return {
        "scope": "verification for outside-regime free-symmetry no-go audit",
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_free_symmetry_no_go_verification.json"),
    )
    args = parser.parse_args()

    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"all_gates_pass={result['all_gates_pass']}")
    print(f"json_out={out}")
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
