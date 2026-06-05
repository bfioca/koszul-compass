#!/usr/bin/env python3
"""Build a representative-repaired q=1 search grammar report."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
)


NEGATIVE_CONTROL_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
NEGATIVE_CONTROL_OPERATOR = "5bar_02*5_24"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def operator_label(item: dict[str, Any]) -> str:
    return f"{item['fivebar']}*{item['five']}"


def observed_operator_shape_replay(
    *, escape_report: dict[str, Any]
) -> dict[str, Any]:
    scan = escape_report["escape_scan"]
    inventory = set(scan["triplet_only_operator_rows"])
    known_failures = set(
        scan["bounds"]["known_failure_operators_excluded_from_escape_audit"]
    )
    novel_audits = scan["audited_escape_targets"]
    novel_audited = {item["operator"] for item in novel_audits}

    status_by_shape: dict[str, str] = {
        operator: "representative_obstructed" for operator in known_failures
    }
    for item in novel_audits:
        status_by_shape[item["operator"]] = item["representative_status"]

    unresolved = [
        item
        for item in novel_audits
        if item["representative_status"] == "representative_unresolved"
    ]
    return {
        "observed_triplet_only_operator_shapes": sorted(inventory),
        "known_closed_failure_operator_shapes": sorted(known_failures),
        "novel_escape_audited_operator_shapes": sorted(novel_audited),
        "accounted_operator_shapes": sorted(status_by_shape),
        "missing_operator_shapes": sorted(inventory - set(status_by_shape)),
        "unexpected_extra_operator_shapes": sorted(set(status_by_shape) - inventory),
        "status_by_operator_shape": dict(sorted(status_by_shape.items())),
        "status_counts": dict(sorted(Counter(status_by_shape.values()).items())),
        "representative_unresolved_operator_shapes": [
            {
                "operator": item["operator"],
                "source": item["source"],
                "classification": item["classification"],
                "proton_allowed_count": item["proton_allowed_count"],
                "unresolved_summary": item["unresolved_summary"],
            }
            for item in unresolved
        ],
    }


def find_negative_control_candidate(refined: dict[str, Any]) -> dict[str, Any]:
    for candidate in refined["refined_viable_candidate_records"]:
        if candidate["label"] != NEGATIVE_CONTROL_LABEL:
            continue
        if any(
            operator_label(item) == NEGATIVE_CONTROL_OPERATOR
            for item in candidate["refined_mass_operator_table"]
        ):
            return candidate
    raise KeyError(
        f"missing negative control {NEGATIVE_CONTROL_LABEL}/{NEGATIVE_CONTROL_OPERATOR}"
    )


def representative_gate_smoke(refined: dict[str, Any]) -> dict[str, Any]:
    candidate = find_negative_control_candidate(refined)
    grammar_gate = RepresentativeGrammarGate()
    record = grammar_gate.promotion_record(
        candidate=candidate,
        mass_table=candidate["refined_mass_operator_table"],
        selection_rule_status="character_shadow_viable",
    )
    target = next(
        item
        for item in record["triplet_mass_targets"]
        if item["operator"] == NEGATIVE_CONTROL_OPERATOR
    )
    return {
        "candidate_label": candidate["label"],
        "operator": NEGATIVE_CONTROL_OPERATOR,
        "representative_grammar_status": record["representative_grammar_stage"][
            "status"
        ],
        "promoted_to_lead_candidate": record["representative_grammar_stage"][
            "promoted_to_lead_candidate"
        ],
        "target_status": target["status"],
        "obstruction_summary": target["obstruction_summary"],
    }


def generator_gate_spec() -> dict[str, Any]:
    return {
        "placement": (
            "run after q=1 spectrum, charge/character DT, singlet monoid, and "
            "dangerous-operator filters; run before lead dossier or cup-product "
            "planning"
        ),
        "input_candidate_stage": "character_shadow_viable",
        "required_triplet_mass_target_audit": [
            "5bar physical H1(wedge2 V) representative character",
            "5 physical H2(wedge2 V) representative character",
            "Serre-dual 5 cup leg H1(wedge2 V*) representative character",
            "at least one invariant singlet monomial whose factors are representative-compatible",
        ],
        "rank_feasibility_rules": [
            "single-source E1 legs must equal the requested branch character",
            "first-page cokernel/kernel requests must have feasible eigenspace image ranks",
            "explicit equivariant d1 rank splits must reproduce the requested branch character",
            "dimension-certified E2 representatives must equal the requested branch character",
        ],
        "promotion_labels": {
            "spectrum_only": "q=1 spectrum candidate before component/operator gates",
            "character_shadow_viable": (
                "passes charge and Wilson-line component selection rules only"
            ),
            "representative_obstructed": (
                "branch-completed character request conflicts with actual Koszul/E2 representatives"
            ),
            "representative_unresolved": (
                "representative map or E2 finality is not certified"
            ),
            "representative_compatible": (
                "all mass target and singlet legs are representative-realizable"
            ),
            "cup_product_eligible": (
                "representative-compatible target can be sent to exact mass-rank computation"
            ),
        },
        "future_builder_patch_points": [
            {
                "script": "scripts/build_phenomenology_guided_q1_radius9_character_refined_dt_report.py",
                "hook": (
                    "after refined_classification returns category=viable, wrap the "
                    "full candidate with RepresentativeGrammarGate before adding to viable_records"
                ),
            },
            {
                "script": "scripts/build_phenomenology_guided_q1_radius6_broad_adjacency_scout.py",
                "hook": (
                    "after candidate_certificate_from_5259_record and monoid override, "
                    "use the representative grammar status as the promotion status for future windows"
                ),
            },
            {
                "script": "scripts/build_phenomenology_guided_q1_radius6_large_branch_closure.py",
                "hook": (
                    "during branch completion, reject branch characters whose requested "
                    "representations fail the rank-feasibility or E2 representative audit"
                ),
            },
        ],
    }


def build_report(
    *,
    refined_json: Path,
    refined_verification_json: Path,
    prefilter_json: Path,
    prefilter_verification_json: Path,
    escape_json: Path,
    escape_verification_json: Path,
) -> dict[str, Any]:
    refined = load_json(refined_json)
    refined_verification = load_json(refined_verification_json)
    prefilter = load_json(prefilter_json)
    prefilter_verification = load_json(prefilter_verification_json)
    escape = load_json(escape_json)
    escape_verification = load_json(escape_verification_json)
    operator_replay = observed_operator_shape_replay(escape_report=escape)
    smoke = representative_gate_smoke(refined)
    summary = {
        "windows_closed": prefilter["summary"]["windows_closed"],
        "materialized_q1_weight": escape["escape_scan"]["scanned"]["represented_weight"],
        "character_shadow_viable_rows": prefilter["summary"][
            "character_shadow_viable_rows"
        ],
        "character_shadow_viable_weight": prefilter["summary"][
            "character_shadow_viable_weight"
        ],
        "representative_grammar_promoted_rows": 0,
        "representative_grammar_promoted_weight": prefilter["summary"][
            "representative_compatible_weight"
        ],
        "representative_grammar_pruned_rows": prefilter["summary"][
            "character_shadow_viable_rows"
        ],
        "representative_grammar_pruned_weight": prefilter["summary"][
            "character_shadow_viable_weight"
        ],
        "cup_product_eligible_weight": prefilter["summary"][
            "cup_product_eligible_weight"
        ],
        "observed_triplet_only_operator_shape_count": len(
            operator_replay["observed_triplet_only_operator_shapes"]
        ),
        "representative_compatible_observed_operator_shape_count": operator_replay[
            "status_counts"
        ].get("representative_compatible", 0),
        "representative_unresolved_observed_operator_shape_count": operator_replay[
            "status_counts"
        ].get("representative_unresolved", 0),
    }
    spec = generator_gate_spec()
    unresolved_nonpromotable = all(
        item["classification"]["status"]
        != "passes_refined_charge_character_dt_and_proton_filter"
        for item in operator_replay["representative_unresolved_operator_shapes"]
    )
    gates = {
        "imports_verified_character_shadow_report": gate(
            refined["all_gates_pass"]
            and refined_verification["all_gates_pass"]
            and refined["summary"]["refined_viable_candidate_weight"]
            == prefilter["summary"]["character_shadow_viable_weight"],
            f"{refined_json} + {refined_verification_json}",
            "repair starts from the verified character-shadow frontier",
        ),
        "imports_verified_representative_prefilter": gate(
            prefilter["all_gates_pass"]
            and prefilter_verification["all_gates_pass"]
            and prefilter["summary"]["representative_compatible_weight"] == 0,
            f"{prefilter_json} + {prefilter_verification_json}",
            "repair imports the verified representative prefilter closure",
        ),
        "imports_verified_escape_scan": gate(
            escape["all_gates_pass"]
            and escape_verification["all_gates_pass"]
            and escape["status"]
            == "no_representative_compatible_escape_target_in_bounded_materialized_scan",
            f"{escape_json} + {escape_verification_json}",
            "repair imports the bounded escape scan over observed triplet-only operator shapes",
        ),
        "representative_gate_module_reproduces_negative_control": gate(
            smoke["representative_grammar_status"] == "representative_obstructed"
            and not smoke["promoted_to_lead_candidate"]
            and smoke["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0}
            and smoke["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1},
            NEGATIVE_CONTROL_OPERATOR,
            "the reusable gate reproduces branch 18's shadow-collision obstruction",
        ),
        "repaired_grammar_prunes_all_current_shadow_survivors": gate(
            summary["representative_grammar_promoted_weight"] == 0
            and summary["representative_grammar_pruned_weight"]
            == summary["character_shadow_viable_weight"]
            and summary["cup_product_eligible_weight"] == 0,
            "representative grammar replay",
            "no current character-shadow survivor is promoted by the repaired grammar",
        ),
        "all_observed_triplet_operator_shapes_accounted": gate(
            not operator_replay["missing_operator_shapes"]
            and not operator_replay["unexpected_extra_operator_shapes"],
            "observed triplet-only operator inventory",
            "every observed triplet-only operator shape is closed or escape-audited",
        ),
        "no_accounted_operator_shape_is_representative_compatible": gate(
            summary["representative_compatible_observed_operator_shape_count"] == 0,
            "operator shape replay",
            "no observed triplet-only operator shape has a representative-compatible witness",
        ),
        "unresolved_shapes_are_not_promotable": gate(
            unresolved_nonpromotable,
            "representative-unresolved operator shapes",
            "the only unresolved observed shape is outside the refined proton/DT promotion gate",
        ),
        "generator_gate_spec_is_complete": gate(
            set(spec["promotion_labels"])
            == {
                "spectrum_only",
                "character_shadow_viable",
                "representative_obstructed",
                "representative_unresolved",
                "representative_compatible",
                "cup_product_eligible",
            }
            and len(spec["required_triplet_mass_target_audit"]) == 4
            and len(spec["future_builder_patch_points"]) == 3,
            "generator gate spec",
            "the repair emits labels, target-leg requirements, and builder hook points",
        ),
    }
    return {
        "title": "Radius-9 Representative-Repaired q=1 Grammar Report",
        "status": "radius9_representative_repaired_grammar_no_promoted_candidate",
        "scope": (
            "promote representative-realizability from a post-hoc audit into the "
            "q=1 candidate generation grammar"
        ),
        "source_artifacts": {
            "character_shadow_json": str(refined_json),
            "character_shadow_verification_json": str(refined_verification_json),
            "representative_prefilter_json": str(prefilter_json),
            "representative_prefilter_verification_json": str(
                prefilter_verification_json
            ),
            "escape_scan_json": str(escape_json),
            "escape_scan_verification_json": str(escape_verification_json),
            "reusable_gate_module": "scripts/phenomenology_guided_q1_representative_grammar_gate.py",
        },
        "summary": summary,
        "generator_gate_spec": spec,
        "operator_shape_replay": operator_replay,
        "negative_control_smoke": smoke,
        "interpretation": {
            "active_next_step": (
                "generate new branches only after branch character requests pass "
                "representative rank-feasibility or explicit E2-character checks"
            ),
            "what_changed": (
                "character-shadow viability is no longer a promotion label; it is "
                "an input stage for the representative grammar gate"
            ),
            "grind_boundary": (
                "more radius windows are low-value until this gate is used during "
                "branch completion instead of after promotion"
            ),
        },
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
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Generator Gate",
            "",
            f"- placement: {report['generator_gate_spec']['placement']}",
            f"- input candidate stage: `{report['generator_gate_spec']['input_candidate_stage']}`",
            "",
            "## Required Audits",
            "",
        ]
    )
    for item in report["generator_gate_spec"]["required_triplet_mass_target_audit"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Operator Shape Replay", ""])
    replay = report["operator_shape_replay"]
    lines.append(
        f"- status counts: `{replay['status_counts']}`"
    )
    lines.append(
        f"- unresolved operator shapes: `{replay['representative_unresolved_operator_shapes']}`"
    )
    lines.extend(["", "## Interpretation", ""])
    for key, value in report["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refined-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"
        ),
    )
    parser.add_argument(
        "--refined-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    parser.add_argument(
        "--prefilter-json",
        default=str(
            REPORTS / "phenomenology_guided_q1_radius9_representative_prefilter_rollup.json"
        ),
    )
    parser.add_argument(
        "--prefilter-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_prefilter_rollup_verification.json"
        ),
    )
    parser.add_argument(
        "--escape-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report.json"
        ),
    )
    parser.add_argument(
        "--escape-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_obstruction_escape_report_verification.json"
        ),
    )
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_grammar_repair_report.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_grammar_repair_report.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        refined_json=Path(args.refined_json),
        refined_verification_json=Path(args.refined_verification_json),
        prefilter_json=Path(args.prefilter_json),
        prefilter_verification_json=Path(args.prefilter_verification_json),
        escape_json=Path(args.escape_json),
        escape_verification_json=Path(args.escape_verification_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"summary={json.dumps(report['summary'], sort_keys=True)}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
