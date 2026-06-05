#!/usr/bin/env python3
"""Summarize downloaded Oxford datasets and write provenance metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicylist import parse_cicy_metadata, summarize_cicy_metadata
from string_theory.mathematica import load_assignment, rules_to_dict


RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


SOURCES = {
    "cicylist.txt": "https://www-thphys.physics.ox.ac.uk/projects/CalabiYau/cicylist/cicylist.txt",
    "cicylist.m": "https://www-thphys.physics.ox.ac.uk/projects/CalabiYau/cicylist/cicylist.m",
    "GUTall.m": "https://www-thphys.physics.ox.ac.uk/projects/CalabiYau/linebundlemodels/GUTall.m",
    "sms202.m": "https://www-thphys.physics.ox.ac.uk/projects/CalabiYau/linebundlemodels/sms202.m",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_gut_models() -> dict:
    cicy_entries = [rules_to_dict(entry) for entry in load_assignment(str(RAW / "GUTall.m"), "Cicys")]
    line_bundle_sums = load_assignment(str(RAW / "GUTall.m"), "LineBundleSums")
    model_count = 0
    nonempty_rules = 0
    trivial_summand_count_distribution: dict[int, int] = {}
    for item in line_bundle_sums:
        models = item[2]
        model_count += len(models)
        if models:
            nonempty_rules += 1
        for matrix in models:
            trivial_count = trivial_summand_count(matrix)
            trivial_summand_count_distribution[trivial_count] = (
                trivial_summand_count_distribution.get(trivial_count, 0) + 1
            )
    return {
        "gut_cicy_entries": len(cicy_entries),
        "gut_line_bundle_sum_rules": len(line_bundle_sums),
        "gut_nonempty_rules": nonempty_rules,
        "gut_model_count": model_count,
        "gut_h11_values": sorted({entry["H11"] for entry in cicy_entries}),
        "trivial_summand_count_distribution": {
            str(key): value
            for key, value in sorted(trivial_summand_count_distribution.items())
        },
    }


def trivial_summand_count(matrix: list[list[int]]) -> int:
    rows = len(matrix)
    return sum(list(column) == [0] * rows for column in zip(*matrix))


def count_sms_models() -> dict:
    linebundles = load_assignment(str(RAW / "sms202.m"), "linebundles")
    model_count = 0
    trivial_summand_count_distribution: dict[int, int] = {}
    for item in linebundles:
        for matrix in item[2]:
            model_count += 1
            trivial_count = trivial_summand_count(matrix)
            trivial_summand_count_distribution[trivial_count] = (
                trivial_summand_count_distribution.get(trivial_count, 0) + 1
            )
    return {
        "model_count": model_count,
        "trivial_summand_count_distribution": {
            str(key): value
            for key, value in sorted(trivial_summand_count_distribution.items())
        },
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    cicy_entries = parse_cicy_metadata(str(RAW / "cicylist.m"))
    summary = {
        "sources": {
            name: {
                "url": url,
                "sha256": sha256(RAW / name),
                "bytes": (RAW / name).stat().st_size,
            }
            for name, url in SOURCES.items()
        },
        "cicylist": summarize_cicy_metadata(cicy_entries),
        "gutall": count_gut_models(),
        "sms202": count_sms_models(),
    }
    out = REPORTS / "dataset_summary.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"json_out={out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
