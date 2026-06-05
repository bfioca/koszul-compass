#!/usr/bin/env python3
"""Build target-pool report for outside-old-regime CICY searches."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import ambient_dimensions, triple_intersections
from string_theory.cicylist import (
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
)


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


def intersection_summary(conf: list[list[int]]) -> dict:
    intersections = triple_intersections(conf)
    nonzero = {
        key: value for key, value in intersections.items() if value != 0
    }
    values = list(nonzero.values())
    return {
        "ambient_dimensions": list(ambient_dimensions(conf)),
        "nonzero_triple_intersection_count": len(nonzero),
        "max_abs_triple_intersection": max((abs(value) for value in values), default=0),
        "sample_nonzero_triple_intersections": [
            {"indices": list(key), "value": value}
            for key, value in sorted(nonzero.items())[:20]
        ],
    }


def build_report() -> dict:
    entries_text = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    paired = list(zip(metadata, entries_text))

    canonical_known_h11_ge7 = [
        (meta, entry)
        for meta, entry in paired
        if meta["Num"] <= 7890
        and meta["H11"] >= 7
        and meta["HasKnownNonemptySymmetryData"]
    ]
    canonical_free_h11_ge7 = [
        (meta, entry)
        for meta, entry in canonical_known_h11_ge7
        if meta["FreeSymmetryOptionCount"] > 0
    ]
    favourable_targets = [
        (meta, entry)
        for meta, entry in canonical_known_h11_ge7
        if meta["H11"] == meta["NumPs"]
    ]
    favourable_free_targets = [
        (meta, entry)
        for meta, entry in favourable_targets
        if meta["FreeSymmetryOptionCount"] > 0
    ]

    def compact_target(meta: dict, entry: str) -> dict:
        conf = parse_integer_list_rule(entry, "Conf")
        c2 = parse_integer_list_rule(entry, "C2")
        return {
            "num": meta["Num"],
            "h11": meta["H11"],
            "h21": meta["H21"],
            "eta": meta["Eta"],
            "num_projective_factors": meta["NumPs"],
            "num_polynomials": meta["NumPol"],
            "c2": c2,
            "conf": conf,
            "symmetry_option_count": meta["SymmetryOptionCount"],
            "free_symmetry_option_count": meta["FreeSymmetryOptionCount"],
            "favourable_by_h11_equals_num_projective_factors": meta["H11"]
            == meta["NumPs"],
            "intersection_summary": intersection_summary(conf),
        }

    h11_counts = Counter(meta["H11"] for meta, _ in canonical_known_h11_ge7)
    free_h11_counts = Counter(meta["H11"] for meta, _ in canonical_free_h11_ge7)
    favourable_h11_counts = Counter(meta["H11"] for meta, _ in favourable_targets)
    favourable_free_h11_counts = Counter(
        meta["H11"] for meta, _ in favourable_free_targets
    )
    old_regime_h11_values = list(range(2, 7))

    return {
        "scope": "outside-old-regime CICY target pool for line-bundle search",
        "old_gutall_regime": {
            "dataset": "GUTall.m",
            "h11_values": old_regime_h11_values,
            "note": "Known Oxford SU(5) GUT dataset uses favourable CICYs with h11 in {2,3,4,5,6}.",
        },
        "candidate_pool": {
            "canonical_h11_ge_7_known_nonempty_symmetry_count": len(
                canonical_known_h11_ge7
            ),
            "canonical_h11_ge_7_known_nonempty_symmetry_h11_counts": dict(
                sorted(h11_counts.items())
            ),
            "favourable_h11_ge_7_known_nonempty_symmetry_count": len(
                favourable_targets
            ),
            "favourable_h11_ge_7_known_nonempty_symmetry_h11_counts": dict(
                sorted(favourable_h11_counts.items())
            ),
            "canonical_h11_ge_7_known_free_symmetry_count": len(
                canonical_free_h11_ge7
            ),
            "canonical_h11_ge_7_known_free_symmetry_h11_counts": dict(
                sorted(free_h11_counts.items())
            ),
            "favourable_h11_ge_7_known_free_symmetry_count": len(
                favourable_free_targets
            ),
            "favourable_h11_ge_7_known_free_symmetry_h11_counts": dict(
                sorted(favourable_free_h11_counts.items())
            ),
            "immediate_favourable_target_nums": [
                meta["Num"] for meta, _ in favourable_targets
            ],
            "immediate_favourable_free_target_nums": [
                meta["Num"] for meta, _ in favourable_free_targets
            ],
        },
        "immediate_favourable_targets": [
            compact_target(meta, entry) for meta, entry in favourable_targets
        ],
        "free_known_symmetry_target_nums": [
            meta["Num"] for meta, _ in canonical_free_h11_ge7
        ],
        "nonfavourable_free_known_symmetry_targets": [
            compact_target(meta, entry)
            for meta, entry in canonical_free_h11_ge7
            if meta["H11"] != meta["NumPs"]
        ],
        "nonfavourable_known_symmetry_target_nums": [
            meta["Num"]
            for meta, _ in canonical_known_h11_ge7
            if meta["H11"] != meta["NumPs"]
        ],
        "next_step": {
            "recommended_search_scope": "Use the three favourable h11=7 known-symmetry targets for ambient-basis upstairs searches; treat the recorded free-symmetry target set as blocked by non-favourability until a favourable-basis/non-favourable verifier is implemented.",
            "why": "The favourable h11>=7 known-symmetry pool has no recorded free symmetry option, while every recorded free-symmetry h11>=7 target is non-favourable (H11 != NumPs) in the current CICY-list metadata.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_targets.json"),
    )
    args = parser.parse_args()

    result = build_report()
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    pool = result["candidate_pool"]
    print(
        "canonical_h11_ge_7_known_nonempty_symmetry_count="
        f"{pool['canonical_h11_ge_7_known_nonempty_symmetry_count']}"
    )
    print(
        "favourable_h11_ge_7_known_nonempty_symmetry_count="
        f"{pool['favourable_h11_ge_7_known_nonempty_symmetry_count']}"
    )
    print(
        "immediate_favourable_target_nums="
        f"{pool['immediate_favourable_target_nums']}"
    )
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
