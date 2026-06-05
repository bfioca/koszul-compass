#!/usr/bin/env python3
"""Cross-dataset novelty diagnostics for the CICY 7484 family candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.mathematica import load_assignment, rules_to_dict
from string_theory.novelty import build_dataset_keys, novelty_record

from verify_family_candidate import BASE_CICY, BASE_SYMMETRY_ORDER, BASE_MATRIX, DIRECTION, add_matrix
from verify_gut_benchmarks import iter_models


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def gut_entries() -> tuple[list[tuple[int, int, list[list[int]]]], dict[int, list[list[int]]]]:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    cicys = {entry["Num"]: entry for entry in cicy_entries}
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")
    entries = [
        (cicy["Num"], symmetry_order, matrix)
        for cicy, symmetry_order, matrix in iter_models(cicys, line_bundle_sums)
    ]
    return entries, {num: entry["Conf"] for num, entry in cicys.items()}


def sms_entries() -> list[tuple[int, int, list[list[int]]]]:
    linebundles = load_assignment(str(RAW / "sms202.m"), "linebundles")
    entries: list[tuple[int, int, list[list[int]]]] = []
    for item in linebundles:
        cicy_num, symmetry_order, _symmetry_numbers = item[1]
        for matrix in item[2]:
            entries.append((cicy_num, symmetry_order, matrix))
    return entries


def verify(n_values: list[int]) -> dict:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms

    dataset_key_sets = {
        "GUTall": build_dataset_keys(gut, gut_confs),
        "sms202": build_dataset_keys(sms, None),
        "combined": build_dataset_keys(combined, gut_confs),
    }

    records = []
    conf = gut_confs[BASE_CICY]
    for n in n_values:
        matrix = add_matrix(BASE_MATRIX, DIRECTION, n)
        records.append(
            {
                "n": n,
                "matrix": matrix,
                "datasets": {
                    name: novelty_record(
                        cicy_num=BASE_CICY,
                        symmetry_order=BASE_SYMMETRY_ORDER,
                        matrix=matrix,
                        conf=conf,
                        dataset_keys=keys,
                    )
                    for name, keys in dataset_key_sets.items()
                },
            }
        )

    return {
        "candidate": {
            "cicy": BASE_CICY,
            "symmetry_order": BASE_SYMMETRY_ORDER,
            "base_matrix": BASE_MATRIX,
            "direction": DIRECTION,
        },
        "dataset_counts": {
            "GUTall": len(gut),
            "sms202": len(sms),
            "combined": len(combined),
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", nargs="*", type=int, default=[-1, 0, 1])
    parser.add_argument("--json-out", default=str(REPORTS / "candidate_novelty_7484_shift12.json"))
    args = parser.parse_args()

    result = verify(args.n)
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"dataset_counts={result['dataset_counts']}")
    for record in result["records"]:
        combined = record["datasets"]["combined"]
        print(
            f"n={record['n']} novel_column={combined['novel_under_column_permutation']} "
            f"novel_row_column={combined['novel_under_row_and_column_permutation']}"
        )
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
