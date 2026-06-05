#!/usr/bin/env python3
"""Independently recheck the current outside-regime candidate certificate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.cicy import bundle_c1, bundle_c2, bundle_index, triple_intersections, wedge2_index
from string_theory.novelty import build_dataset_keys, novelty_record
from string_theory.slope import find_slope_zero, intersection_tensor
from verify_candidate_novelty import gut_entries, sms_entries
from verify_family_candidate import cohomology_and_spectrum


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def novelty_context() -> dict[str, Any]:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms
    return {
        "dataset_counts": {
            "GUTall": len(gut),
            "sms202": len(sms),
            "combined": len(combined),
        },
        "key_sets": {
            "GUTall": build_dataset_keys(gut, gut_confs),
            "sms202": build_dataset_keys(sms, None),
            "combined": build_dataset_keys(combined, gut_confs),
        },
    }


def verify(
    *,
    certificate_report: str,
    restarts: int,
    max_iterations: int,
    tolerance: float,
    seed: int,
) -> dict[str, Any]:
    certificate_path = Path(certificate_report)
    if not certificate_path.is_absolute():
        certificate_path = ROOT / certificate_path
    certificate = load_json(certificate_path)
    target_pool = load_json(REPORTS / "outside_regime_targets.json")
    construction = certificate["construction"]
    cicy_num = construction["cicy"]
    target = next(
        item
        for item in target_pool["immediate_favourable_targets"]
        if item["num"] == cicy_num
    )
    cicy = {
        "Num": cicy_num,
        "H11": target["h11"],
        "Conf": target["conf"],
        "C2": target["c2"],
    }
    matrix = construction["matrix"]
    intersections = triple_intersections(cicy["Conf"])
    tensor = intersection_tensor(intersections, cicy["H11"])
    c1 = bundle_c1(matrix)
    index_v = bundle_index(matrix, intersections, cicy["C2"])
    index_wedge2_v = wedge2_index(matrix, intersections, cicy["C2"])
    c2_v = bundle_c2(matrix, intersections)
    anomaly = [tx - v for tx, v in zip(cicy["C2"], c2_v)]
    slope = find_slope_zero(
        matrix,
        tensor,
        tolerance=tolerance,
        restarts=restarts,
        max_iterations=max_iterations,
        seed=seed,
    )
    cohomology = cohomology_and_spectrum(cicy, abs(index_v) // 3, matrix)
    spectrum = cohomology["su5_upstairs_spectrum"]
    quality = cohomology["line_bundle_sum_quality"]
    novelty = {
        name: novelty_record(
            cicy_num=cicy_num,
            symmetry_order=abs(index_v) // 3,
            matrix=matrix,
            conf=cicy["Conf"],
            dataset_keys=keys,
        )
        for name, keys in novelty_context()["key_sets"].items()
    }
    gates = {
        "c1_zero": c1 == [0] * cicy["H11"],
        "index_chirality": index_v == -3 and index_wedge2_v == -3,
        "anomaly_effective": all(value >= 0 for value in anomaly),
        "slope_zero_numerical_hardened": slope.feasible,
        "cohomology_spectrum": all(spectrum["checks"].values())
        and spectrum["upstairs_anti_10"] == 0,
        "regular_nontrivial_quality": quality["regular_nontrivial_summand_scan_style"],
        "implemented_novelty": novelty["combined"][
            "novel_under_row_and_column_permutation"
        ],
    }
    return {
        "scope": "independent recheck of current outside-regime candidate certificate",
        "construction": {
            "label": construction["label"],
            "cicy": cicy_num,
            "matrix": matrix,
            "certificate_report": str(certificate_path.relative_to(ROOT)),
        },
        "checks": {
            "c1": c1,
            "index_v": index_v,
            "index_wedge2_v": index_wedge2_v,
            "c2_v": c2_v,
            "anomaly": anomaly,
            "slope_search": slope.as_dict(),
            "cohomology_and_spectrum": cohomology,
            "novelty": novelty,
        },
        "gate_summary": gates,
        "all_gates_pass": all(gates.values()),
        "hardened_slope_parameters": {
            "restarts": restarts,
            "max_iterations": max_iterations,
            "tolerance": tolerance,
            "seed": seed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--certificate-report",
        default="reports/outside_regime_candidate_certificate.json",
    )
    parser.add_argument("--restarts", type=int, default=96)
    parser.add_argument("--max-iterations", type=int, default=8000)
    parser.add_argument("--tolerance", type=float, default=1e-7)
    parser.add_argument("--seed", type=int, default=2544999)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_candidate_independent_check.json"),
    )
    args = parser.parse_args()

    result = verify(
        certificate_report=args.certificate_report,
        restarts=args.restarts,
        max_iterations=args.max_iterations,
        tolerance=args.tolerance,
        seed=args.seed,
    )
    out = Path(args.json_out)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    spectrum = result["checks"]["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    print(f"label={result['construction']['label']}")
    print(f"all_gates_pass={result['all_gates_pass']}")
    print(
        "spectrum="
        f"{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
        f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
    )
    print(
        "hardened_slope="
        f"{result['checks']['slope_search']['max_normalized_slope']:.3g}"
    )
    print(f"json_out={out}")
    return 0 if result["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
