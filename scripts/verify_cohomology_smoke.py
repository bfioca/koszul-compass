#!/usr/bin/env python3
"""pyCICY cohomology smoke checks for known Oxford SU(5) models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import line_bundle_index, triple_intersections
from string_theory.cohomology import (
    bundle_line_summands,
    cohomology_record,
    dual,
    sum_cohomologies,
    su5_upstairs_spectrum_checks,
    wedge2_line_summands,
)
from string_theory.mathematica import load_assignment, rules_to_dict

from verify_gut_benchmarks import iter_models


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def verify(limit: int) -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    cicys = {entry["Num"]: entry for entry in cicy_entries}
    intersections = {num: triple_intersections(entry["Conf"]) for num, entry in cicys.items()}
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")

    checked = []
    failures = []
    for index, (cicy, symmetry_order, matrix) in enumerate(iter_models(cicys, line_bundle_sums), start=1):
        if index > limit:
            break
        d = intersections[cicy["Num"]]
        line_records = []
        for line_bundle in bundle_line_summands(matrix):
            record = cohomology_record(cicy["Conf"], line_bundle)
            record["rr_index"] = line_bundle_index(line_bundle, d, cicy["C2"])
            record["euler_matches_rr"] = record["euler"] == record["rr_index"]
            line_records.append(record)

        wedge_records = []
        for line_bundle in wedge2_line_summands(matrix):
            record = cohomology_record(cicy["Conf"], line_bundle)
            record["rr_index"] = line_bundle_index(line_bundle, d, cicy["C2"])
            record["euler_matches_rr"] = record["euler"] == record["rr_index"]
            wedge_records.append(record)

        dual_line_records = [cohomology_record(cicy["Conf"], dual(record["line_bundle"])) for record in line_records]
        dual_wedge_records = [cohomology_record(cicy["Conf"], dual(record["line_bundle"])) for record in wedge_records]

        v_cohomology = sum_cohomologies([item["cohomology"] for item in line_records])
        v_dual_cohomology = sum_cohomologies([item["cohomology"] for item in dual_line_records])
        wedge2_v_cohomology = sum_cohomologies([item["cohomology"] for item in wedge_records])
        wedge2_v_dual_cohomology = sum_cohomologies([item["cohomology"] for item in dual_wedge_records])
        spectrum = su5_upstairs_spectrum_checks(
            symmetry_order=symmetry_order,
            v_cohomology=v_cohomology,
            v_dual_cohomology=v_dual_cohomology,
            wedge2_v_cohomology=wedge2_v_cohomology,
            wedge2_v_dual_cohomology=wedge2_v_dual_cohomology,
        )

        record = {
            "model_index": index,
            "cicy": cicy["Num"],
            "h11": cicy["H11"],
            "symmetry_order": symmetry_order,
            "matrix": matrix,
            "V_cohomology": v_cohomology,
            "V_dual_cohomology": v_dual_cohomology,
            "wedge2_V_cohomology": wedge2_v_cohomology,
            "wedge2_V_dual_cohomology": wedge2_v_dual_cohomology,
            "su5_upstairs_spectrum": spectrum,
            "line_records": line_records,
            "wedge2_line_records": wedge_records,
        }
        checked.append(record)
        if not all(item["euler_matches_rr"] for item in line_records + wedge_records):
            failures.append(record)
        elif not all(spectrum["checks"].values()):
            failures.append(record)

    return {
        "dataset": "GUTall.m",
        "checked_models": len(checked),
        "failures": failures,
        "checked": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json-out", default=str(REPORTS / "gut_cohomology_smoke.json"))
    args = parser.parse_args()

    result = verify(args.limit)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"checked_models={result['checked_models']}")
    print(f"failures={len(result['failures'])}")
    print(f"json_out={out}")
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    sys.exit(main())
