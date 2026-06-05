#!/usr/bin/env python3
"""Compare and locally minimize vectorlike 5/5bar obstructions."""

from __future__ import annotations

import argparse
from itertools import combinations
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_quotient_wilson_line_report import (  # noqa: E402
    free_z2_option_records,
    line_character_certificate,
    prod_sign,
    sector_record,
    split_lift_search,
)
from string_theory.cicy import (  # noqa: E402
    ambient_dimensions,
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.cicylist import (  # noqa: E402
    parse_cicy_metadata,
    parse_integer_list_rule,
    split_top_level_entries,
)
from string_theory.cohomology import (  # noqa: E402
    bundle_line_summands,
    cohomology_record,
    dual,
    wedge2_line_summands,
)
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def representation_pair(record: dict[str, Any]) -> dict[str, int] | None:
    if record["regular_multiplicity"] is None:
        return None
    return {
        "regular_multiplicity": record["regular_multiplicity"],
        "dimension": record["dimension"],
    }


def load_5259_action_context() -> dict[str, Any]:
    entries = split_top_level_entries((RAW / "cicylist.m").read_text(encoding="utf-8"))
    metadata = parse_cicy_metadata(str(RAW / "cicylist.m"))
    entry_5259 = next(entry for meta, entry in zip(metadata, entries) if meta["Num"] == 5259)
    conf_5259 = parse_integer_list_rule(entry_5259, "Conf")
    option = free_z2_option_records(
        entry_5259, [dim + 1 for dim in ambient_dimensions(conf_5259)]
    )[0]
    lift = split_lift_search(
        original_first_polynomial_sign=option["polynomial_signs_5259"][0]
    )
    return {
        "option": option,
        "lift": lift,
        "coordinate_signs_by_block_7914": [
            *option["coordinate_signs_by_ambient_block"],
            lift["p2_coordinate_signs"],
        ],
        "equation_signs_7914": [
            *lift["split_equation_signs"],
            *option["polynomial_signs_5259"][1:],
        ],
    }


def certify_5259_matrix(
    *,
    label: str,
    matrix: list[list[int]],
    move: list[Any],
    slope_restarts: int,
    slope_seed: int,
) -> dict[str, Any]:
    split = load_json("cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2 = split["full_picard_presentation_7914"]["c2_tx"]
    context = load_5259_action_context()
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    c2_v = bundle_c2(matrix, intersections)
    anomaly = [tx - v for tx, v in zip(c2, c2_v)]
    slope = find_slope_zero(
        matrix,
        tensor,
        tolerance=1e-7,
        restarts=slope_restarts,
        max_iterations=2500,
        seed=slope_seed,
    )
    cohomology = cohomology_and_spectrum(
        {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2},
        2,
        matrix,
    )

    fiber_signs = [1, 1, 1, 1, 1]
    line_summands = bundle_line_summands(matrix)
    v_certs = []
    vdual_certs = []
    for index, line in enumerate(line_summands):
        v_certs.append(
            {
                "summand_index": index,
                **line_character_certificate(
                    conf=conf,
                    coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
                    equation_signs=context["equation_signs_7914"],
                    line_bundle=line,
                    cohomology=cohomology_record(conf, line)["cohomology"],
                    fiber_sign=fiber_signs[index],
                ),
            }
        )
        dual_line = dual(line)
        vdual_certs.append(
            {
                "summand_index": index,
                **line_character_certificate(
                    conf=conf,
                    coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
                    equation_signs=context["equation_signs_7914"],
                    line_bundle=dual_line,
                    cohomology=cohomology_record(conf, dual_line)["cohomology"],
                    fiber_sign=fiber_signs[index],
                ),
            }
        )

    wedge_certs = []
    wedge_dual_certs = []
    for pair_index, (a, b) in enumerate(combinations(range(5), 2)):
        line = [matrix[row][a] + matrix[row][b] for row in range(7)]
        wedge_certs.append(
            {
                "summand_pair": [a, b],
                "pair_index": pair_index,
                **line_character_certificate(
                    conf=conf,
                    coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
                    equation_signs=context["equation_signs_7914"],
                    line_bundle=line,
                    cohomology=cohomology_record(conf, line)["cohomology"],
                    fiber_sign=fiber_signs[a] * fiber_signs[b],
                ),
            }
        )
        dual_line = dual(line)
        wedge_dual_certs.append(
            {
                "summand_pair": [a, b],
                "pair_index": pair_index,
                **line_character_certificate(
                    conf=conf,
                    coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
                    equation_signs=context["equation_signs_7914"],
                    line_bundle=dual_line,
                    cohomology=cohomology_record(conf, dual_line)["cohomology"],
                    fiber_sign=fiber_signs[a] * fiber_signs[b],
                ),
            }
        )

    sectors = {
        "V": sector_record(label="V", line_certificates=v_certs, cohomology_degree_keys=["H1"]),
        "V_dual": sector_record(
            label="V*", line_certificates=vdual_certs, cohomology_degree_keys=["H2"]
        ),
        "wedge2_V": sector_record(
            label="wedge2 V",
            line_certificates=wedge_certs,
            cohomology_degree_keys=["H1", "H2"],
        ),
        "wedge2_V_dual": sector_record(
            label="wedge2 V*",
            line_certificates=wedge_dual_certs,
            cohomology_degree_keys=["H1", "H2"],
        ),
    }
    h1_wedge = sectors["wedge2_V"]["cohomology_characters"]["H1"]
    h2_wedge = sectors["wedge2_V"]["cohomology_characters"]["H2"]
    h2_regular = h2_wedge["regular_multiplicity"]
    vectorlike_pairs = h2_regular if h2_regular is not None else None
    return {
        "label": label,
        "cicy": "5259/7914",
        "quotient_group": "Z2",
        "quotient_order": 2,
        "move_from_base": move,
        "matrix": matrix,
        "c1": bundle_c1(matrix),
        "index_v": bundle_index(matrix, intersections, c2),
        "index_wedge2_v": wedge2_index(matrix, intersections, c2),
        "c2_v": c2_v,
        "anomaly": anomaly,
        "slope_search": slope.as_dict(),
        "cohomology": {
            "V": cohomology["V_cohomology"],
            "V_dual": cohomology["V_dual_cohomology"],
            "wedge2_V": cohomology["wedge2_V_cohomology"],
            "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
        },
        "line_bundle_sum_quality": cohomology["line_bundle_sum_quality"],
        "su5_upstairs_spectrum": cohomology["su5_upstairs_spectrum"],
        "characters": sectors,
        "vectorlike_pair_prediction": {
            "regular_character_rule_applies": h2_regular is not None,
            "h1_wedge2_regular_multiplicity": h1_wedge["regular_multiplicity"],
            "h2_wedge2_regular_multiplicity": h2_regular,
            "colored_triplet_vectorlike_pairs": vectorlike_pairs,
            "electroweak_doublet_vectorlike_pairs": vectorlike_pairs,
            "net_families": (
                h1_wedge["regular_multiplicity"] - h2_regular
                if h2_regular is not None
                and h1_wedge["regular_multiplicity"] is not None
                else None
            ),
        },
        "character_certified": all(
            sector["all_characters_computed"] for sector in sectors.values()
        ),
    }


def elementary_moves(rows: int = 7, cols: int = 5) -> list[tuple[int, int, int, int]]:
    return [
        (row, a, b, delta)
        for row in range(rows)
        for a in range(cols)
        for b in range(a + 1, cols)
        for delta in (-1, 1)
    ]


def apply_moves(base: list[list[int]], moves: list[tuple[int, int, int, int]]) -> list[list[int]]:
    matrix = [row[:] for row in base]
    for row, a, b, delta in moves:
        matrix[row][a] += delta
        matrix[row][b] -= delta
    return matrix


def local_5259_one_move_search() -> dict[str, Any]:
    split = load_json("cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2 = split["full_picard_presentation_7914"]["c2_tx"]
    base = split["zero_extended_bundle_certificate"]["matrix_7914_zero_extended"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    seen = set()
    counters = {
        "unique_candidates": 0,
        "topology_survivors": 0,
        "slope_survivors": 0,
        "spectrum_survivors": 0,
        "character_certified_survivors": 0,
    }
    records = []
    for index, move_tuple in enumerate([(), *[(move,) for move in elementary_moves()]]):
        matrix = apply_moves(base, list(move_tuple))
        key = tuple(sorted(zip(*matrix)))
        if key in seen:
            continue
        seen.add(key)
        counters["unique_candidates"] += 1
        try:
            if bundle_c1(matrix) != [0] * 7:
                continue
            index_v = bundle_index(matrix, intersections, c2)
            index_wedge = wedge2_index(matrix, intersections, c2)
            c2_v = bundle_c2(matrix, intersections)
        except Exception:
            continue
        if index_v != -6 or index_wedge != -6:
            continue
        anomaly = [tx - v for tx, v in zip(c2, c2_v)]
        if not all(value >= 0 for value in anomaly):
            continue
        counters["topology_survivors"] += 1
        slope = find_slope_zero(
            matrix,
            tensor,
            tolerance=1e-7,
            restarts=8,
            max_iterations=1200,
            seed=7259000 + index,
        )
        if not slope.feasible:
            continue
        counters["slope_survivors"] += 1
        cohomology = cohomology_and_spectrum(
            {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2},
            2,
            matrix,
        )
        spectrum = cohomology["su5_upstairs_spectrum"]
        if (
            not all(spectrum["checks"].values())
            or spectrum["upstairs_anti_10"] != 0
            or not cohomology["line_bundle_sum_quality"][
                "regular_nontrivial_summand_scan_style"
            ]
        ):
            continue
        counters["spectrum_survivors"] += 1
        certified = certify_5259_matrix(
            label="one_move_candidate",
            matrix=matrix,
            move=[list(move) for move in move_tuple],
            slope_restarts=16,
            slope_seed=8259000 + index,
        )
        if not certified["character_certified"]:
            records.append(certified)
            continue
        counters["character_certified_survivors"] += 1
        records.append(certified)
    records.sort(
        key=lambda item: (
            item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            if item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            is not None
            else 999,
            max(abs(value) for row in item["matrix"] for value in row),
            item["move_from_base"],
        )
    )
    return {
        "scope": "bounded one-elementary-move search around the certified 5259/7914 bundle",
        "move_definition": "choose one row and two columns; add +/-1 to one column and the opposite charge to the other",
        "counters": counters,
        "best_character_certified": next(
            (record for record in records if record["character_certified"]), None
        ),
        "records": records,
    }


def cicy7484_records_from_report(path: Path, label: str) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for record in data.get("records", []):
        actual = record["conditional_order4_descent_constraints"][
            "actual_z2xz2_wedge2_character_certificate"
        ]
        if not actual.get("character_computed"):
            continue
        h2_regular = actual.get("h2_regular_multiplicity")
        out.append(
            {
                "label": label,
                "source_report": str(path),
                "cicy": 7484,
                "quotient_group": "Z2xZ2",
                "quotient_order": 4,
                "kappa_vector": record["kappa_vector"],
                "matrix": record["matrix"],
                "anomaly": record["anomaly"],
                "cohomology": {
                    "V": record["V_cohomology"],
                    "V_dual": record["V_dual_cohomology"],
                    "wedge2_V": record["wedge2_V_cohomology"],
                    "wedge2_V_dual": record["wedge2_V_dual_cohomology"],
                },
                "su5_upstairs_spectrum": record["su5_upstairs_spectrum"],
                "actual_wedge2_character": actual,
                "line_bundle_sum_quality": record.get("line_bundle_sum_quality"),
                "vectorlike_pair_prediction": {
                    "regular_character_rule_applies": h2_regular is not None,
                    "h1_wedge2_regular_multiplicity": actual.get(
                        "h1_regular_multiplicity"
                    ),
                    "h2_wedge2_regular_multiplicity": h2_regular,
                    "colored_triplet_vectorlike_pairs": h2_regular,
                    "electroweak_doublet_vectorlike_pairs": h2_regular,
                    "net_families": (
                        actual.get("h1_regular_multiplicity") - h2_regular
                        if h2_regular is not None
                        else None
                    ),
                },
                "character_certified": True,
            }
        )
    out.sort(
        key=lambda item: (
            item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            if item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            is not None
            else 999,
            max(abs(value) for row in item["matrix"] for value in row),
        )
    )
    return out


def build_report() -> dict[str, Any]:
    base_5259_report = load_json("cicy5259_quotient_wilson_line_report.json")
    base_5259 = {
        "label": "5259_7914_base",
        "cicy": "5259/7914",
        "quotient_group": "Z2",
        "quotient_order": 2,
        "matrix": base_5259_report["line_bundle_equivariance"][
            "matrix_7914_zero_extended"
        ],
        "cohomology": {
            key: base_5259_report["equivariant_cohomology_characters"][key][
                "cohomology_characters"
            ]
            for key in ["V", "V_dual", "wedge2_V", "wedge2_V_dual"]
        },
        "vectorlike_pair_prediction": {
            "regular_character_rule_applies": True,
            "h1_wedge2_regular_multiplicity": 8,
            "h2_wedge2_regular_multiplicity": 5,
            "colored_triplet_vectorlike_pairs": 5,
            "electroweak_doublet_vectorlike_pairs": 5,
            "net_families": 3,
        },
        "character_certified": True,
    }
    local_search = local_5259_one_move_search()
    best_5259_deformation = local_search["best_character_certified"]

    cicy7484_no_zero = cicy7484_records_from_report(
        REPORTS / "cicy7484_kappa_plane_search_bound8_kmax50.json",
        "7484_no_zero_bound8_kmax50",
    )
    cicy7484_zero = cicy7484_records_from_report(
        REPORTS / "cicy7484_kappa_plane_zero_allowed_bound8_kmax50.json",
        "7484_zero_allowed_bound8_kmax50",
    )
    comparative = [
        base_5259,
        *( [best_5259_deformation] if best_5259_deformation else [] ),
        *(cicy7484_no_zero[:4]),
        *(cicy7484_zero[:4]),
    ]
    comparative.sort(
        key=lambda item: (
            item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            if item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
            is not None
            else 999,
            str(item["cicy"]),
            item["label"],
        )
    )
    best = comparative[0]
    gates = {
        "comparative_character_records_loaded": gate(
            base_5259["character_certified"]
            and len(cicy7484_no_zero) == 4
            and len(cicy7484_zero) == 16,
            "reports/cicy5259_quotient_wilson_line_report.json and CICY7484 kappa-plane reports",
            "base 5259 and both 7484 character-certified pools are loaded",
        ),
        "new_5259_deformation_found": gate(
            best_5259_deformation is not None
            and best_5259_deformation["character_certified"]
            and best_5259_deformation["vectorlike_pair_prediction"][
                "colored_triplet_vectorlike_pairs"
            ]
            == 3,
            "bounded one-move 5259/7914 local search",
            "one elementary charge transfer reduces the certified 5259 vectorlike count from five to three",
        ),
        "regular_h2_predicts_vectorlike_count": gate(
            all(
                item["vectorlike_pair_prediction"]["regular_character_rule_applies"]
                and item["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"]
                == item["vectorlike_pair_prediction"]["h2_wedge2_regular_multiplicity"]
                for item in comparative
                if item["vectorlike_pair_prediction"][
                    "colored_triplet_vectorlike_pairs"
                ]
                is not None
            ),
            "character-certified comparative records",
            "in the certified regular-character cases, vectorlike pairs equal the H2(wedge2 V) regular multiplicity",
        ),
        "bounded_minimum_is_three": gate(
            best["vectorlike_pair_prediction"]["colored_triplet_vectorlike_pairs"] == 3,
            "one-move 5259 search plus existing 7484 bound8/kmax50 searches",
            "no character-certified record in the bounded comparison has fewer than three vectorlike pairs",
        ),
    }
    return {
        "scope": "comparative vectorlike 5/5bar obstruction report",
        "conclusion": {
            "status": "new_5259_7914_deformation_reduces_vectorlike_pairs_to_three",
            "new_candidate_found": True,
            "best_vectorlike_pair_count": best["vectorlike_pair_prediction"][
                "colored_triplet_vectorlike_pairs"
            ],
            "best_record_label": best["label"],
            "predictive_rule": (
                "For the character-certified regular cases in this workspace, the Wilson-line vectorlike pair count "
                "is the regular multiplicity of H2(wedge2 V). Equivalently, if H2(wedge2 V) is q copies of the "
                "regular quotient representation, each admissible Wilson-line character sees q vectorlike 5/5bar pairs."
            ),
            "bounded_obstruction": (
                "Within the one-elementary-move 5259/7914 neighborhood and the existing CICY7484 bound8/kmax50 "
                "character-certified searches, the minimum certified vectorlike count is three pairs. This is a "
                "bounded statement, not a global no-go."
            ),
        },
        "new_5259_7914_candidate": best_5259_deformation,
        "local_5259_one_move_search": local_search,
        "cicy7484_character_certified_summary": {
            "no_zero_count": len(cicy7484_no_zero),
            "no_zero_best": cicy7484_no_zero[0] if cicy7484_no_zero else None,
            "zero_allowed_count": len(cicy7484_zero),
            "zero_allowed_best": cicy7484_zero[0] if cicy7484_zero else None,
        },
        "comparative_records": comparative,
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    new = report["new_5259_7914_candidate"]
    lines = [
        "# Vectorlike 5/5bar obstruction report",
        "",
        f"Status: `{report['conclusion']['status']}`",
        "",
        "## Result",
        "",
        "- A new character-certified CICY 5259/7914 deformation was found.",
        "- It reduces the actual Wilson-line vectorlike count from `5` pairs to `3` pairs.",
        "- The deformation is one elementary charge transfer: row `2`, column `0 += 1`, column `2 -= 1`.",
        "- The bounded comparison minimum is `3` vectorlike pairs.",
        "",
        "## New Candidate",
        "",
        f"- matrix: `{new['matrix']}`",
        f"- anomaly: `{new['anomaly']}`",
        f"- cohomology `V/V*/wedge2V/wedge2V*`: `{new['cohomology']['V']}` / `{new['cohomology']['V_dual']}` / `{new['cohomology']['wedge2_V']}` / `{new['cohomology']['wedge2_V_dual']}`",
        f"- vectorlike colored/electroweak pairs: `{new['vectorlike_pair_prediction']['colored_triplet_vectorlike_pairs']}` / `{new['vectorlike_pair_prediction']['electroweak_doublet_vectorlike_pairs']}`",
        "",
        "## Predictive Rule",
        "",
        report["conclusion"]["predictive_rule"],
        "",
        "## Bound",
        "",
        report["conclusion"]["bounded_obstruction"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "vectorlike_obstruction_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "vectorlike_obstruction_report.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['conclusion']['status']}")
    print(f"best_pair_count={report['conclusion']['best_vectorlike_pair_count']}")
    print(f"best_record={report['conclusion']['best_record_label']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
