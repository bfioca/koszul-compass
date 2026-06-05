#!/usr/bin/env python3
"""Verify equivariant first-page map-rank probe."""

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
    path = REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.json"
    md_path = REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe.md"
    sign_path = REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.json"
    report = load_json(path)
    sign_probe = load_json(sign_path)
    md_text = md_path.read_text(encoding="utf-8")
    raw = report["raw_pycicy_map_split"]
    equivariant = report["equivariant_filtered_map_split"]

    verification_gates = {
        "builder_gates_pass": gate(
            report["all_gates_pass"] and all(item["pass"] for item in report["gates"].values()),
            str(path),
            "equivariant first-page builder gates pass",
        ),
        "uses_verified_e1_signs": gate(
            sign_probe["all_gates_pass"]
            and report["representative_line"] == sign_probe["representative_line"],
            f"{path}, {sign_path}",
            "first-page rank split is tied to the verified E1 basis-sign probe",
        ),
        "raw_map_mixes_eigenspaces": gate(
            raw["cross_eigen_nonzero_entries"] > 0
            and raw["rank_total"] == 4,
            str(path),
            "unrestricted pyCICY generic map is not the quotient-equivariant map",
        ),
        "filtered_map_is_block_diagonal": gate(
            equivariant["cross_eigen_nonzero_entries"] == 0
            and equivariant["rank_total"] == 4
            and equivariant["rank_plus"] == 2
            and equivariant["rank_minus"] == 2,
            str(path),
            "equation-character filtering yields the first-page equivariant rank split",
        ),
        "source_target_multiplicities_match_dimensions": gate(
            report["source_sign_multiplicities"] == {"+": 3, "-": 4}
            and report["target_sign_multiplicities"] == {"+": 2, "-": 2},
            str(path),
            "source and target eigenspace dimensions match the representative E1 entries",
        ),
        "markdown_matches_report": gate(
            "Status: `equivariant_first_page_rank_split_computed`" in md_text
            and "rank_+=2" in md_text
            and "rank_-=2" in md_text
            and "cross-eigenspace nonzeros: `0`" in md_text,
            str(md_path),
            "markdown exposes the first-page rank split and block-diagonal check",
        ),
    }
    return {
        "scope": "verification for equivariant first-page map-rank probe",
        "all_gates_pass": all(item["pass"] for item in verification_gates.values()),
        "gates": verification_gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius2_equivariant_first_page_probe_verification.json"
        ),
    )
    args = parser.parse_args()
    result = verify()
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
