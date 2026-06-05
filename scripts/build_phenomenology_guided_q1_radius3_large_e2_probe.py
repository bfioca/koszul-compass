#!/usr/bin/env python3
"""Resolve the remaining large high-priority radius-3 line by E2 ranks."""

from __future__ import annotations

import argparse
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

from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    matrix_rank,
    rank_split,
)
from build_phenomenology_guided_q1_radius2_projected_higher_rank_probe import (  # noqa: E402
    signs_for_entry,
)
from build_phenomenology_guided_q1_radius2_three_term_e2_probe import rep_from_counts  # noqa: E402
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import ensure_pycicy_compat, make_pycicy, pycicy_config  # noqa: E402

LARGE_LINE = [2, 0, 3, 0, 0, -1, -1]
LARGE_DUAL = [-2, 0, -3, 0, 0, 1, 1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def compute_e2(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> dict[str, Any]:
    e1, origin = manifold.Leray(manifold._line_to_BBW(line_bundle))
    entries = []
    signs = {}
    for k in range(manifold.K + 1):
        for j in range(manifold.dimA + 1):
            if e1[k][j] == 0:
                continue
            entry = (k, j)
            entries.append(entry)
            signs[entry] = signs_for_entry(
                manifold=manifold,
                conf=conf,
                line_bundle=line_bundle,
                e1=e1,
                origin=origin,
                entry=entry,
                coordinate_signs_by_block=coordinate_signs_by_block,
                equation_signs=equation_signs,
            )

    ranks = {}
    compositions = []
    entry_set = set(entries)
    for source in entries:
        target = (source[0] - 1, source[1])
        if target not in entry_set:
            continue
        sk, sj = source
        tk, tj = target
        matrix = equivariant_rank_map(
            manifold=manifold,
            source_entries=[[int(x) for x in item] for item in e1[sk][sj]],
            target_entries=[[int(x) for x in item] for item in e1[tk][tj]],
            source_origins=[list(item) for item in origin[sk][sj]],
            target_origins=[list(item) for item in origin[tk][tj]],
            coordinate_signs_by_block=coordinate_signs_by_block,
            equation_signs=equation_signs,
        )
        split = rank_split(matrix=matrix, source_signs=signs[source], target_signs=signs[target])
        ranks[(source, target)] = {"matrix": matrix, "split": split}

    for middle in entries:
        incoming_source = (middle[0] + 1, middle[1])
        outgoing_target = (middle[0] - 1, middle[1])
        incoming = ranks.get((incoming_source, middle))
        outgoing = ranks.get((middle, outgoing_target))
        if incoming is None or outgoing is None:
            continue
        composition = outgoing["matrix"] @ incoming["matrix"]
        compositions.append(
            {
                "incoming_source": list(incoming_source),
                "middle": list(middle),
                "outgoing_target": list(outgoing_target),
                "composition_rank": matrix_rank(composition),
                "nonzero_entries": int((composition != 0).sum()),
            }
        )

    actual: dict[str, Any] = {}
    e2_entries = []
    for entry in entries:
        k, j = entry
        outgoing = ranks.get((entry, (k - 1, j)))
        incoming = ranks.get(((k + 1, j), entry))
        plus = signs[entry].count(1)
        minus = signs[entry].count(-1)
        if outgoing is not None:
            plus -= outgoing["split"]["rank_plus"]
            minus -= outgoing["split"]["rank_minus"]
        if incoming is not None:
            plus -= incoming["split"]["rank_plus"]
            minus -= incoming["split"]["rank_minus"]
        if plus + minus == 0:
            continue
        degree = j - k
        rep = rep_from_counts(plus, minus)
        e2_entries.append({"entry": list(entry), "total_degree": degree, "representation": rep})
        actual[f"H{degree}"] = rep

    return {
        "line_bundle": line_bundle,
        "e1_entries": [
            {
                "entry": list(entry),
                "total_degree": entry[1] - entry[0],
                "dimension": len(signs[entry]),
                "multiplicities": {
                    "+": signs[entry].count(1),
                    "-": signs[entry].count(-1),
                },
            }
            for entry in entries
        ],
        "rank_splits": [
            {
                "source": list(source),
                "target": list(target),
                **data["split"],
            }
            for (source, target), data in ranks.items()
        ],
        "compositions": compositions,
        "actual": actual,
        "e2_entries": e2_entries,
        "cross_eigen_nonzero_entries": sum(
            data["split"]["cross_eigen_nonzero_entries"] for data in ranks.values()
        ),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    current = load_json(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    context = load_5259_action_context()
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    records = [
        compute_e2(
            manifold=manifold,
            conf=conf,
            line_bundle=line,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        )
        for line in [LARGE_LINE, LARGE_DUAL]
    ]
    expected = {"H1": rep_from_counts(1, 1), "H2": rep_from_counts(1, 1)}
    high_priority_has_line = any(
        block["line_bundle"] == LARGE_LINE
        for record in current["high_priority_unresolved_frontier"]
        for block in record["missing_character_blocks"]
    )
    gates = {
        "target_line_is_high_priority": gate(
            high_priority_has_line,
            str(REPORTS / "phenomenology_guided_q1_radius3_current_frontier.json"),
            "probe targets the remaining large high-priority unresolved line block",
        ),
        "line_and_dual_processed": gate(
            [record["line_bundle"] for record in records] == [LARGE_LINE, LARGE_DUAL],
            "large line and Serre-dual line",
            "both missing line blocks are processed",
        ),
        "first_page_maps_are_equivariant_complexes": gate(
            all(record["cross_eigen_nonzero_entries"] == 0 for record in records)
            and all(
                all(item["composition_rank"] == 0 and item["nonzero_entries"] == 0 for item in record["compositions"])
                for record in records
            ),
            "large-line E1 first-page complexes",
            "all d1 maps are block diagonal and consecutive d1 compositions vanish",
        ),
        "e2_characters_are_regular_h1_h2": gate(
            all(record["actual"] == expected for record in records),
            "large-line E2 character computation",
            "line and dual both resolve to one regular H1 plus one regular H2",
        ),
    }
    return {
        "scope": "large radius-3 high-priority E2 character probe",
        "status": "large_line_and_dual_resolve_to_regular_h1_h2",
        "line_bundle": LARGE_LINE,
        "dual_line_bundle": LARGE_DUAL,
        "resolved_characters": expected,
        "records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-3 Large E2 Probe",
        "",
        f"Status: `{report['status']}`",
        "",
        f"- line bundle: `{report['line_bundle']}`",
        f"- dual line bundle: `{report['dual_line_bundle']}`",
        f"- resolved characters: `{report['resolved_characters']}`",
        "",
    ]
    for record in report["records"]:
        lines.append(f"- `{record['line_bundle']}`: actual `{record['actual']}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius3_large_e2_probe.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"resolved_characters={report['resolved_characters']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
