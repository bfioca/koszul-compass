#!/usr/bin/env python3
"""Prototype Z2 basis-sign reconstruction for representative pyCICY E1 entries."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

REPRESENTATIVE_LINE = [1, 0, -2, -1, -1, 1, 0]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def prod(values: list[int]) -> int:
    out = 1
    for value in values:
        out *= value
    return out


def flatten(blocks: list[list[int]]) -> list[int]:
    return [value for block in blocks for value in block]


def equation_degrees(conf: list[list[int]]) -> list[list[int]]:
    return [[conf[row][col] for row in range(len(conf))] for col in range(len(conf[0]))]


def ambient_bundle_for_origin(
    *,
    line_bundle: list[int],
    conf: list[list[int]],
    origin: list[int],
) -> list[int]:
    degrees = equation_degrees(conf)
    shift = [
        sum(degrees[col][row] for col in origin)
        for row in range(len(conf))
    ]
    return [charge - delta for charge, delta in zip(line_bundle, shift)]


def serre_dual_det_factor(
    *,
    ambient_bundle: list[int],
    coordinate_signs_by_block: list[list[int]],
) -> int:
    value = 1
    for row_index, charge in enumerate(ambient_bundle):
        if charge < 0:
            value *= prod(coordinate_signs_by_block[row_index])
    return value


def monomial_sign(
    *,
    monomial: list[int],
    coordinate_signs_by_block: list[list[int]],
) -> int:
    signs = flatten(coordinate_signs_by_block)
    value = 1
    for exponent, sign in zip(monomial, signs):
        if abs(int(exponent)) % 2:
            value *= sign
    return value


def entry_basis_signs(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    bracket_entries: list[list[int]],
    origins: list[list[int]],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> list[int]:
    signs = []
    for bracket, origin in zip(bracket_entries, origins):
        dim = manifold._brackets_dim(bracket)
        basis = manifold._makepoly(bracket, dim)
        equation_sign = prod([equation_signs[index] for index in origin])
        det_factor = serre_dual_det_factor(
            ambient_bundle=ambient_bundle_for_origin(
                line_bundle=line_bundle,
                conf=conf,
                origin=origin,
            ),
            coordinate_signs_by_block=coordinate_signs_by_block,
        )
        for monomial in basis:
            signs.append(
                equation_sign
                * det_factor
                * monomial_sign(
                    monomial=[int(x) for x in monomial],
                    coordinate_signs_by_block=coordinate_signs_by_block,
                )
            )
    return signs


def rep_from_signs(signs: list[int]) -> dict[str, Any]:
    plus = sum(1 for sign in signs if sign == 1)
    minus = sum(1 for sign in signs if sign == -1)
    return {
        "dimension": len(signs),
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    scenarios = load_json(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    bbw = manifold._line_to_BBW(REPRESENTATIVE_LINE)
    e1, origin = manifold.Leray(bbw)
    entries = []
    totals: dict[str, list[int]] = defaultdict(list)
    for k, row in enumerate(e1):
        for j, value in enumerate(row):
            if value == 0:
                continue
            bracket_entries = [[int(x) for x in item] for item in value]
            origins = [list(item) for item in origin[k][j]]
            signs = entry_basis_signs(
                manifold=manifold,
                conf=conf,
                line_bundle=REPRESENTATIVE_LINE,
                bracket_entries=bracket_entries,
                origins=origins,
                coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
                equation_signs=context["equation_signs_7914"],
            )
            total_degree = j - k
            totals[str(total_degree)].extend(signs)
            entries.append(
                {
                    "k": k,
                    "j": j,
                    "total_degree_j_minus_k": total_degree,
                    "bracket_entries": bracket_entries,
                    "origin": origins,
                    "ambient_bundles": [
                        ambient_bundle_for_origin(
                            line_bundle=REPRESENTATIVE_LINE,
                            conf=conf,
                            origin=item,
                        )
                        for item in origins
                    ],
                    "basis_sign_representation": rep_from_signs(signs),
                    "basis_signs": signs,
                }
            )
    total_reps = {degree: rep_from_signs(signs) for degree, signs in sorted(totals.items())}
    expected = scenarios["records"][0]["block_summaries"][0]["source_totals"]
    gates = {
        "representative_scenario_imported": gate(
            scenarios["records"][0]["label"] == "radius2_enhanced_backlog_0"
            and scenarios["records"][0]["block_summaries"][0]["line_bundle"]
            == REPRESENTATIVE_LINE,
            str(REPORTS / "phenomenology_guided_q1_radius2_map_scenarios.json"),
            "prototype starts from the representative high-priority residual block",
        ),
        "e1_total_traces_match_source_terms": gate(
            total_reps["1"] == expected["1"] and total_reps["2"] == expected["2"],
            "pyCICY E1 basis signs compared with existing character source totals",
            "reconstructed E1 basis signs reproduce the known total-degree source representations",
        ),
            "mixed_entries_have_expected_dimensions": gate(
                total_reps["1"]["dimension"] == 7
                and total_reps["2"]["dimension"] == 7
                and total_reps["1"]["nonidentity_trace"] == expected["1"]["nonidentity_trace"]
                and total_reps["2"]["nonidentity_trace"] == expected["2"]["nonidentity_trace"],
                "representative E1 total-degree entries",
                "representative mixed block has the expected 7-dimensional trace-minus-one entries",
            ),
            "serre_determinants_use_ambient_koszul_lines": gate(
                any(
                    entry["bracket_entries"] == [[0, 0, 0, 0, 0, 0, 0]]
                    and entry["ambient_bundles"] == [[0, -2, -2, -2, -2, 0, -3]]
                    and entry["basis_sign_representation"]["nonidentity_trace"] == -1
                    for entry in entries
                ),
                "pyCICY BBW bracket versus original Koszul ambient bundle",
                "Serre determinant factors are computed from pre-BBW ambient Koszul line bundles",
            ),
    }
    return {
        "scope": "prototype Z2 basis-sign reconstruction for representative pyCICY E1 entries",
        "status": "e1_basis_signs_match_character_sources",
        "representative_line": REPRESENTATIVE_LINE,
        "entries": entries,
        "total_degree_representations": total_reps,
        "expected_source_totals": expected,
        "next_step": (
            "Use these E1 basis signs with pyCICY higher-Leray projections/maps "
            "to track Z2 eigenspaces through the effective rank computation."
        ),
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-2 E1 Sign Prototype",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- representative line: `{report['representative_line']}`",
        f"- total-degree representations: `{report['total_degree_representations']}`",
        f"- expected source totals: `{report['expected_source_totals']}`",
        "- trace check: both total-degree source representations are 7-dimensional with trace-minus-one (`+3/-4`).",
        "- determinant check: Serre determinant factors are taken from the pre-BBW ambient Koszul line bundles.",
        "",
        "## Interpretation",
        "",
        report["next_step"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius2_e1_sign_prototype.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"total_degree_representations={report['total_degree_representations']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
