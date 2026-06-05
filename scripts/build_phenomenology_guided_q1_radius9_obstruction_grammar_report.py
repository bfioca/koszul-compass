#!/usr/bin/env python3
"""Build a structural obstruction grammar report for radius-9 q=1 candidates."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import glob
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

STATUS_ORDER = [
    "dangerous_10_5bar_5bar_operator_allowed",
    "negative_control_doublet_triplet_obstruction",
    "no_triplet_mass_in_certified_singlet_monoid",
    "rejected_spectrum_signature_not_q1_three_family",
]

STATUS_ALIASES = {
    "no_certified_triplet_mass_operator_found": "no_triplet_mass_in_certified_singlet_monoid",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def parse_index_label(label: str, prefix: str) -> tuple[int, ...]:
    tail = label.removeprefix(prefix)
    return tuple(int(char) for char in tail if char.isdigit())


def operator_indices(operator: str) -> list[int]:
    pieces = operator.split("*")
    indices: list[int] = []
    for piece in pieces:
        if piece.startswith("10_"):
            indices.extend(parse_index_label(piece, "10_"))
        elif piece.startswith("5bar_"):
            indices.extend(parse_index_label(piece, "5bar_"))
    return indices


def is_trace_vector(coeffs: list[int]) -> bool:
    return len(coeffs) == 5 and all(item == coeffs[0] for item in coeffs)


def is_complement_partition(operator: str) -> bool:
    indices = operator_indices(operator)
    return sorted(indices) == [0, 1, 2, 3, 4] and len(set(indices)) == 5


def move_key(move: dict[str, Any] | None) -> str:
    if not move:
        return "unknown"
    family = move.get("family", "unknown")
    row = move.get("row")
    columns = ",".join(str(item) for item in move.get("columns", []))
    delta = move.get("delta")
    return f"{family};row={row};columns={columns};delta={delta}"


def compact_move(move: dict[str, Any] | None) -> dict[str, Any] | None:
    if not move:
        return None
    return {
        "family": move.get("family"),
        "row": move.get("row"),
        "columns": move.get("columns"),
        "delta": move.get("delta"),
    }


def character_summary(record: dict[str, Any]) -> dict[str, Any]:
    cert = record.get("character_certificate") or {}
    characters = cert.get("characters") or {}
    wedge2 = (characters.get("wedge2_V") or {}).get("cohomology_characters") or {}
    v_chars = (characters.get("V") or {}).get("cohomology_characters") or {}
    return {
        "character_certified": cert.get("character_certified"),
        "V_H1": v_chars.get("H1"),
        "wedge2_V_H1": wedge2.get("H1"),
        "wedge2_V_H2": wedge2.get("H2"),
    }


def charge_inventory_summary(record: dict[str, Any]) -> dict[str, Any]:
    inventory = record.get("charged_matter_inventory") or {}
    return {
        "ten": [
            {
                "label": item.get("label"),
                "charge": item.get("charge", {}).get("label"),
                "multiplicities": (item.get("character") or {}).get("multiplicities"),
            }
            for item in inventory.get("ten", [])
        ],
        "fivebar": [
            {
                "label": item.get("label"),
                "charge": item.get("charge", {}).get("label"),
                "multiplicities": (item.get("character") or {}).get("multiplicities"),
            }
            for item in inventory.get("fivebar", [])
        ],
        "five": [
            {
                "label": item.get("label"),
                "charge": item.get("charge", {}).get("label"),
                "multiplicities": (item.get("character") or {}).get("multiplicities"),
            }
            for item in inventory.get("five", [])
        ],
    }


def mass_summary(record: dict[str, Any]) -> dict[str, Any]:
    table = record.get("mass_operator_table") or []
    hits = [
        item
        for item in table
        if item.get("triplet_mass_allowed_by_current_selection_rules")
    ]
    selective = [
        item
        for item in table
        if item.get("selection_rule_can_lift_triplet_while_protecting_doublet")
    ]
    hit_summaries = []
    missing_needed = []
    for item in table:
        monomial_hits = item.get("certified_singlet_monomial_hits_degree_le_2") or []
        if monomial_hits:
            hit_summaries.append(
                {
                    "fivebar": item.get("fivebar"),
                    "five": item.get("five"),
                    "bilinear_charge": item.get("bilinear_charge", {}).get("label"),
                    "needed_singlet_charge": item.get(
                        "needed_singlet_charge", {}
                    ).get("label"),
                    "monomial_labels": [
                        hit.get("labels", hit.get("singlet_monomial", []))
                        for hit in monomial_hits
                    ],
                    "doublet_mass_same_selection_rule": item.get(
                        "doublet_mass_same_selection_rule"
                    ),
                }
            )
        else:
            missing_needed.append(
                item.get("needed_singlet_charge", {}).get("label")
            )
    return {
        "mass_entry_count": len(table),
        "triplet_mass_hit_count": len(hits),
        "selective_dt_hit_count": len(selective),
        "doublet_same_rule_hit_count": sum(
            1 for item in hits if item.get("doublet_mass_same_selection_rule")
        ),
        "hit_summaries": hit_summaries[:4],
        "missing_needed_singlet_charges": sorted(
            {item for item in missing_needed if item}
        ),
    }


def proton_summary(record: dict[str, Any]) -> dict[str, Any]:
    table = record.get("proton_decay_operator_table") or []
    allowed = [
        item
        for item in table
        if not item.get("forbidden_by_current_selection_rules")
    ]
    return {
        "operator_count": len(table),
        "allowed_count": len(allowed),
        "forbidden_count": len(table) - len(allowed),
        "allowed_operators": [
            {
                "operator": item.get("operator"),
                "charge": item.get("charge", {}).get("label"),
                "coefficients": item.get("charge", {}).get("coefficients"),
                "trace_neutral": is_trace_vector(
                    item.get("charge", {}).get("coefficients") or []
                ),
                "complement_partition": is_complement_partition(
                    item.get("operator", "")
                ),
            }
            for item in allowed[:6]
        ],
    }


def singlet_summary(record: dict[str, Any]) -> dict[str, Any]:
    singlets = record.get("singlet_moduli_inventory") or {}
    labels = singlets.get("certified_h1_singlet_charge_labels") or []
    return {
        "certified_h1_singlet_count": len(labels),
        "certified_h1_singlet_charge_labels": labels,
    }


def candidate_features(record: dict[str, Any], weight: int, source: dict[str, Any]) -> dict[str, Any]:
    classification = record.get("classification") or {}
    status = STATUS_ALIASES.get(classification.get("status"), classification.get("status"))
    mass = mass_summary(record)
    proton = proton_summary(record)
    singlets = singlet_summary(record)
    spectrum = record.get("spectrum_certificate") or {}
    prediction = spectrum.get("vectorlike_prediction") or {}
    return {
        "label": record.get("label"),
        "status": status,
        "category": classification.get("category"),
        "reason": classification.get("reason"),
        "weight": weight,
        "source": source,
        "move": compact_move(record.get("radius6_broad_move")),
        "radius6_filtered_label": record.get("radius6_filtered_label"),
        "spectrum": {
            "desired_q1_three_family_signature": spectrum.get(
                "desired_q1_three_family_signature"
            ),
            "vectorlike_prediction": prediction,
        },
        "characters": character_summary(record),
        "charges": charge_inventory_summary(record),
        "mass": mass,
        "proton": proton,
        "singlets": singlets,
        "feature_flags": {
            "triplet_mass_allowed": mass["triplet_mass_hit_count"] > 0,
            "selective_dt_evidence": mass["selective_dt_hit_count"] > 0,
            "mass_hit_has_same_doublet_rule": mass[
                "doublet_same_rule_hit_count"
            ]
            > 0,
            "proton_protected_by_charges": proton["allowed_count"] == 0,
            "dangerous_proton_allowed": proton["allowed_count"] > 0,
            "all_allowed_protons_are_trace_complement_partitions": bool(
                proton["allowed_count"]
            )
            and all(item["complement_partition"] for item in proton["allowed_operators"]),
            "has_certified_h1_singlets": singlets["certified_h1_singlet_count"] > 0,
        },
    }


def scout_move_index(window: int) -> dict[str, dict[str, Any]]:
    path = REPORTS / f"phenomenology_guided_q1_radius9_broad_adjacency_scout_window{window}.json"
    if not path.exists():
        return {}
    scout = load_json(path)
    moves = {}
    for record in scout.get("filtered_candidate_records", []):
        moves[record.get("label")] = record.get("radius6_broad_move")
    return moves


def iter_candidate_feature_records(windows: int) -> list[dict[str, Any]]:
    features = []
    for window in range(1, windows + 1):
        moves = scout_move_index(window)

        scout_path = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_adjacency_scout_window{window}.json"
        )
        if scout_path.exists():
            scout = load_json(scout_path)
            for record in scout.get("filtered_candidate_records", []):
                status = (record.get("classification") or {}).get("status")
                if status == "missing_character_or_charge_level_data":
                    continue
                if not record.get("spectrum_certificate", {}).get(
                    "desired_q1_three_family_signature"
                ):
                    continue
                source = {
                    "kind": "direct_scout",
                    "window": window,
                    "path": str(scout_path),
                }
                features.append(candidate_features(record, 1, source))

        branch_path = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_branch_analysis_window{window}.json"
        )
        if branch_path.exists():
            branch = load_json(branch_path)
            for record in branch.get("desired_q1_branch_candidate_records", []):
                label = record.get("radius6_filtered_label")
                if label in moves:
                    record = dict(record)
                    record["radius6_broad_move"] = moves[label]
                source = {
                    "kind": "bounded_branch",
                    "window": window,
                    "path": str(branch_path),
                }
                features.append(candidate_features(record, 1, source))

        pattern = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_window{window}_large_branch_closure_*.json"
        )
        for raw_path in sorted(glob.glob(str(pattern))):
            path = Path(raw_path)
            if path.name.endswith("_verification.json"):
                continue
            closure = load_json(path)
            desired = int(closure.get("summary", {}).get("desired_q1_branches", 0))
            if desired <= 0:
                continue
            record = closure.get("q1_representative_candidate")
            if not record:
                continue
            label = record.get("radius6_filtered_label") or closure.get(
                "summary", {}
            ).get("skipped_label")
            if label in moves:
                record = dict(record)
                record["radius6_broad_move"] = moves[label]
            source = {
                "kind": "large_branch_representative",
                "window": window,
                "path": str(path),
                "represented_q1_branches": desired,
            }
            features.append(candidate_features(record, desired, source))
    return features


def smallest_example(
    records: list[dict[str, Any]], predicate
) -> dict[str, Any] | None:
    matches = [record for record in records if predicate(record)]
    if not matches:
        return None
    return sorted(
        matches,
        key=lambda item: (
            item["weight"],
            item["mass"]["mass_entry_count"],
            item["proton"]["operator_count"],
            str(item["label"]),
        ),
    )[0]


def compact_example(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "label": record["label"],
        "status": record["status"],
        "weight": record["weight"],
        "source": record["source"],
        "move": record["move"],
        "spectrum": record["spectrum"],
        "charges": record["charges"],
        "mass": record["mass"],
        "proton": record["proton"],
        "singlets": record["singlets"],
    }


def weighted_feature_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, Counter[str]] = defaultdict(Counter)
    move_families: dict[str, Counter[str]] = defaultdict(Counter)
    singlet_labels: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        status = record["status"]
        weight = int(record["weight"])
        flags = record["feature_flags"]
        for key, value in flags.items():
            if value:
                by_status[status][key] += weight
        if record["move"]:
            move_families[status][move_key(record["move"])] += weight
        for label in record["singlets"]["certified_h1_singlet_charge_labels"]:
            singlet_labels[status][label] += weight
    return {
        "feature_flags_by_status": {
            status: dict(counter) for status, counter in by_status.items()
        },
        "top_move_patterns_by_status": {
            status: counter.most_common(8)
            for status, counter in move_families.items()
        },
        "top_certified_h1_singlets_by_status": {
            status: counter.most_common(12)
            for status, counter in singlet_labels.items()
        },
    }


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def build_report(windows: int) -> dict[str, Any]:
    rollup_path = REPORTS / (
        f"phenomenology_guided_q1_radius9_broad_windows1_{windows}_rollup.json"
    )
    rollup = load_json(rollup_path)
    summary = rollup["summary"]
    records = iter_candidate_feature_records(windows)
    weighted_statuses = Counter()
    unweighted_statuses = Counter()
    for record in records:
        weighted_statuses[record["status"]] += int(record["weight"])
        unweighted_statuses[record["status"]] += 1

    ranked = []
    adjusted_statuses = summary.get("adjusted_statuses", {})
    desired_count = summary["adjusted_desired_q1_candidates"]
    for status, count in sorted(
        adjusted_statuses.items(), key=lambda item: item[1], reverse=True
    ):
        if status == "rejected_spectrum_signature_not_q1_three_family":
            continue
        ranked.append(
            {
                "status": status,
                "weighted_count": count,
                "share_of_desired_q1": ratio(count, desired_count),
                "sampled_or_representative_weight": weighted_statuses.get(status, 0),
                "sampled_or_representative_records": unweighted_statuses.get(status, 0),
            }
        )

    examples = {
        "dangerous_10_5bar_5bar_operator_allowed": compact_example(
            smallest_example(
                records,
                lambda item: item["status"]
                == "dangerous_10_5bar_5bar_operator_allowed",
            )
        ),
        "negative_control_doublet_triplet_obstruction": compact_example(
            smallest_example(
                records,
                lambda item: item["status"]
                == "negative_control_doublet_triplet_obstruction",
            )
        ),
        "no_triplet_mass_in_certified_singlet_monoid": compact_example(
            smallest_example(
                records,
                lambda item: item["status"]
                == "no_triplet_mass_in_certified_singlet_monoid",
            )
        ),
    }
    closest = {
        "isolated_doublet_triplet_gate": compact_example(
            smallest_example(
                records,
                lambda item: item["feature_flags"]["triplet_mass_allowed"]
                and item["feature_flags"]["proton_protected_by_charges"]
                and not item["feature_flags"]["selective_dt_evidence"],
            )
        ),
        "isolated_triplet_mass_gate": compact_example(
            smallest_example(
                records,
                lambda item: (not item["feature_flags"]["triplet_mass_allowed"])
                and item["feature_flags"]["proton_protected_by_charges"],
            )
        ),
        "proton_failure_with_no_triplet_mass": compact_example(
            smallest_example(
                records,
                lambda item: (not item["feature_flags"]["triplet_mass_allowed"])
                and item["feature_flags"]["dangerous_proton_allowed"],
            )
        ),
        "triplet_mass_but_proton_unprotected": compact_example(
            smallest_example(
                records,
                lambda item: item["feature_flags"]["triplet_mass_allowed"]
                and item["feature_flags"]["dangerous_proton_allowed"],
            )
        ),
        "selective_dt_but_proton_unprotected": compact_example(
            smallest_example(
                records,
                lambda item: item["feature_flags"]["selective_dt_evidence"]
                and item["feature_flags"]["dangerous_proton_allowed"],
            )
        ),
    }

    cross_counts = Counter()
    allowed_proton_entries = 0
    complement_proton_entries = 0
    for record in records:
        weight = int(record["weight"])
        flags = record["feature_flags"]
        if flags["proton_protected_by_charges"] and not flags["selective_dt_evidence"]:
            cross_counts["proton_protected_without_dt_viability"] += weight
        if flags["triplet_mass_allowed"] and flags["dangerous_proton_allowed"]:
            cross_counts["triplet_mass_without_proton_protection"] += weight
        if flags["selective_dt_evidence"] and flags["dangerous_proton_allowed"]:
            cross_counts["dt_viability_without_proton_protection"] += weight
        if flags["selective_dt_evidence"] and flags["proton_protected_by_charges"]:
            cross_counts["dt_viability_with_proton_protection"] += weight
        for item in record["proton"]["allowed_operators"]:
            allowed_proton_entries += weight
            if item["complement_partition"] and item["trace_neutral"]:
                complement_proton_entries += weight

    window_highlights = {}
    for window in range(max(1, windows - 3), windows + 1):
        path = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_closed_frontier_window{window}.json"
        )
        if path.exists():
            window_highlights[str(window)] = load_json(path)["summary"]

    feature_counts = weighted_feature_counts(records)
    conclusions = {
        "dangerous_operator_charge_rule": (
            "In every mined representative with an allowed dangerous operator, "
            "the operator charge is a trace vector, usually e0+e1+e2+e3+e4. "
            "Equivalently, the 10 index and the two 5bar index-pairs form a "
            "partition of {0,1,2,3,4}. The Z2 character tables are regular "
            "enough that an even component is not excluded by the current data."
        ),
        "dangerous_operator_genericity": (
            "The dangerous operator is not logically forced by the q=1 spectrum "
            "grammar: the frontier contains proton-protected q=1 branches in the "
            "DT and no-triplet-mass classes. It is, however, the dominant closed "
            "obstruction by weighted count, so the q=1 grammar is highly "
            "correlated with complement-pair 5bar charge supports."
        ),
        "doublet_triplet_charge_rule": (
            "For every mined triplet-mass hit, the same line-bundle and Z2 "
            "selection rule also allows the corresponding doublet mass. Thus the "
            "5259-style obstruction is structurally forced inside the current "
            "charge-only grammar whenever a certified singlet monomial neutralizes "
            "a 5bar/5 bilinear and no extra doublet-specific symmetry or cup-product "
            "rank evidence is available."
        ),
        "singlet_monoid_rule": (
            "The no-triplet-mass class has proton protection but lacks a certified "
            "degree<=2 H1 singlet monoid element with the needed bilinear-neutralizing "
            "charge. These are isolated mass-availability failures rather than "
            "proton failures."
        ),
        "wilson_line_character_rule": (
            "The q=1 target fixes wedge2 regular multiplicities at H1=4 and H2=1. "
            "That gives the desired one-vectorlike-pair spectrum, but the regular "
            "Z2 character structure usually does not remove dangerous proton "
            "components or distinguish doublet from triplet masses at charge level."
        ),
    }
    gates = {
        "imports_verified_rollup": gate(
            summary.get("all_verified") and summary.get("windows_closed") == windows,
            str(rollup_path),
            f"radius-9 windows 1-{windows} rollup is verified",
        ),
        "no_viable_or_open_mass_solution": gate(
            summary.get("viable_count") == 0
            and summary.get("open_mass_monoid_solutions") == 0,
            str(rollup_path),
            "closed frontier has no viable candidate and no open mass-monoid solution",
        ),
        "candidate_examples_have_tables": gate(
            all(
                example is None
                or (
                    example["mass"]["mass_entry_count"] > 0
                    and example["proton"]["operator_count"] > 0
                )
                for example in examples.values()
            ),
            "radius-9 branch/scout/large candidate records",
            "representative obstruction examples include mass and proton tables",
        ),
        "dangerous_rule_observed": gate(
            allowed_proton_entries > 0
            and allowed_proton_entries == complement_proton_entries,
            "mined representative proton tables",
            "allowed dangerous proton entries are trace-neutral complement partitions",
        ),
        "no_selective_dt_seen": gate(
            cross_counts["dt_viability_with_proton_protection"] == 0
            and cross_counts["dt_viability_without_proton_protection"] == 0,
            "mined representative mass tables",
            "no mined q=1 branch has current charge-level selective DT evidence",
        ),
    }
    return {
        "title": f"Radius-9 Obstruction Grammar Report Through Window {windows}",
        "status": f"radius9_obstruction_grammar_windows1_{windows}_no_viable_candidate",
        "scope": f"radius-9 broad frontier windows 1-{windows}",
        "source_rollup": str(rollup_path),
        "summary": {
            "windows_closed": windows,
            "frontier_records_screened": summary["frontier_records_screened"],
            "frontier_records_after_window": summary[
                f"frontier_records_after_window{windows}"
            ],
            "adjusted_desired_q1_candidates": desired_count,
            "viable_count": summary["viable_count"],
            "open_mass_monoid_solutions": summary["open_mass_monoid_solutions"],
            "adjusted_statuses": adjusted_statuses,
            "ranked_q1_obstructions": ranked,
            "mined_representative_records": len(records),
            "mined_representative_weight": sum(record["weight"] for record in records),
        },
        "window_highlights": window_highlights,
        "representative_examples": examples,
        "closest_to_viable": closest,
        "feature_correlations": feature_counts,
        "cross_gate_counts_from_mined_representatives": dict(cross_counts),
        "allowed_proton_operator_partition_check": {
            "weighted_allowed_entries": allowed_proton_entries,
            "weighted_complement_partition_entries": complement_proton_entries,
            "all_allowed_entries_are_complement_partitions": (
                allowed_proton_entries == complement_proton_entries
                and allowed_proton_entries > 0
            ),
        },
        "structural_conclusions": conclusions,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        f"# {report['title']}",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- windows_closed: `{summary['windows_closed']}`",
        f"- frontier_records_screened: `{summary['frontier_records_screened']}`",
        f"- frontier_records_after_window: `{summary['frontier_records_after_window']}`",
        f"- adjusted_desired_q1_candidates: `{summary['adjusted_desired_q1_candidates']}`",
        f"- viable_count: `{summary['viable_count']}`",
        f"- open_mass_monoid_solutions: `{summary['open_mass_monoid_solutions']}`",
        f"- mined_representative_records: `{summary['mined_representative_records']}`",
        f"- mined_representative_weight: `{summary['mined_representative_weight']}`",
        "",
        "## Ranked Obstructions",
        "",
    ]
    for item in summary["ranked_q1_obstructions"]:
        lines.append(
            "- {status}: `{count}` ({share})".format(
                status=item["status"],
                count=item["weighted_count"],
                share=item["share_of_desired_q1"],
            )
        )
    lines += ["", "## Structural Conclusions", ""]
    for key, text in report["structural_conclusions"].items():
        lines.append(f"- {key}: {text}")
    lines += ["", "## Window Highlights", ""]
    for window, item in report["window_highlights"].items():
        lines.append(f"- window {window}: `{item.get('adjusted_statuses', {})}`")
    lines += ["", "## Closest-To-Viable Classes", ""]
    for key, example in report["closest_to_viable"].items():
        if example is None:
            lines.append(f"- {key}: `none observed`")
        else:
            lines.append(
                f"- {key}: `{example['label']}` / `{example['status']}` / "
                f"weight `{example['weight']}`"
            )
    lines += ["", "## Representative Examples", ""]
    for status in STATUS_ORDER:
        example = report["representative_examples"].get(status)
        if not example:
            continue
        lines.append(f"### {status}")
        lines.append("")
        lines.append(f"- label: `{example['label']}`")
        lines.append(f"- source: `{example['source']}`")
        lines.append(f"- move: `{example['move']}`")
        lines.append(f"- charges: `{example['charges']}`")
        lines.append(f"- mass: `{example['mass']}`")
        lines.append(f"- proton: `{example['proton']}`")
        lines.append(f"- singlets: `{example['singlets']}`")
        lines.append("")
    lines += ["## Gates", ""]
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=36)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_obstruction_grammar_windows1_36.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_obstruction_grammar_windows1_36.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(args.windows)
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(json_out)
    print(md_out)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
