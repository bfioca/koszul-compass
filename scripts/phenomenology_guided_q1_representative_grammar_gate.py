#!/usr/bin/env python3
"""Representative-realizability gate for q=1 phenomenology searches."""

from __future__ import annotations

from collections import Counter
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

from build_phenomenology_guided_q1_radius9_representative_survivor_rerank import (  # noqa: E402
    audit_triplet_operator,
)
from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    full_candidate_record,
    refined_classification,
    refined_mass_table,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import (  # noqa: E402
    ensure_pycicy_compat,
    make_pycicy,
    pycicy_config,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def triplet_only_mass_operators(mass_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in mass_table
        if item.get("character_refined_support_class") == "triplet_only_character_mass"
    ]


def classify_target_statuses(statuses: list[str]) -> str:
    if "representative_compatible" in statuses:
        return "representative_compatible"
    if "representative_unresolved" in statuses:
        return "representative_unresolved"
    return "representative_obstructed"


class RepresentativeGrammarGate:
    """Audit branch-completed character data before candidate promotion.

    This is intentionally a generator-facing wrapper around the conservative
    representative audit. Future frontier builders can call this after the
    q=1 spectrum and charge/character DT/proton gates, before labeling a branch
    as a lead candidate or cup-product target.
    """

    def __init__(self, *, split_json: Path | None = None) -> None:
        split_path = split_json or REPORTS / "cicy5259_split_lift_report.json"
        split = load_json(split_path)
        self.conf = split["full_picard_presentation_7914"]["conf"]
        ensure_pycicy_compat()
        self.manifold = make_pycicy(pycicy_config(self.conf))
        self.context = load_5259_action_context()
        self.line_cache: dict[tuple[int, ...], dict[str, Any]] = {}

    def audit_target(
        self, *, candidate: dict[str, Any], operator: dict[str, Any]
    ) -> dict[str, Any]:
        return audit_triplet_operator(
            manifold=self.manifold,
            conf=self.conf,
            context=self.context,
            line_cache=self.line_cache,
            candidate=candidate,
            operator=operator,
        )

    def audit_candidate(
        self, *, candidate: dict[str, Any], mass_table: list[dict[str, Any]]
    ) -> dict[str, Any]:
        operators = triplet_only_mass_operators(mass_table)
        target_audits = [
            self.audit_target(candidate=candidate, operator=operator)
            for operator in operators
        ]
        status = classify_target_statuses(
            [target["status"] for target in target_audits]
        )
        eligible = [
            target
            for target in target_audits
            if target["eligible_for_exact_cup_product_rank"]
        ]
        return {
            "status": status,
            "target_status_counts": dict(
                sorted(Counter(target["status"] for target in target_audits).items())
            ),
            "triplet_mass_target_count": len(target_audits),
            "cup_product_eligible_target_count": len(eligible),
            "target_audits": target_audits,
        }

    def promotion_record(
        self,
        *,
        candidate: dict[str, Any],
        mass_table: list[dict[str, Any]],
        selection_rule_status: str,
    ) -> dict[str, Any]:
        audit = self.audit_candidate(candidate=candidate, mass_table=mass_table)
        promoted = audit["status"] == "representative_compatible"
        return {
            "candidate_label": candidate.get("label"),
            "source": candidate.get("source"),
            "weight": candidate.get("weight", 1),
            "selection_rule_stage": {
                "status": selection_rule_status,
            },
            "representative_grammar_stage": {
                "status": audit["status"],
                "promoted_to_lead_candidate": promoted,
                "cup_product_planning_allowed": audit[
                    "cup_product_eligible_target_count"
                ]
                > 0,
                "target_status_counts": audit["target_status_counts"],
            },
            "triplet_mass_targets": [
                {
                    "operator": target["operator"],
                    "status": target["status"],
                    "eligible_for_exact_cup_product_rank": target[
                        "eligible_for_exact_cup_product_rank"
                    ],
                    "obstruction_summary": target.get("obstruction_summary"),
                    "unresolved_summary": target.get("unresolved_summary"),
                }
                for target in audit["target_audits"]
            ],
        }


def first_gate_reason(record: dict[str, Any]) -> str:
    for target in record["triplet_mass_targets"]:
        obstruction = target.get("obstruction_summary")
        if obstruction:
            return (
                f"{target['operator']} fails {obstruction['first_obstructing_role']}: "
                f"{obstruction['reason']}"
            )
    for target in record["triplet_mass_targets"]:
        unresolved = target.get("unresolved_summary")
        if unresolved:
            return (
                f"{target['operator']} unresolved at "
                f"{unresolved['first_unresolved_role']}: {unresolved['reason']}"
            )
    return "no representative-compatible triplet mass target is available"


def classification_from_representative_gate(record: dict[str, Any]) -> dict[str, str]:
    stage = record["representative_grammar_stage"]
    if stage["status"] == "representative_compatible":
        return {
            "category": "viable",
            "status": "representative_compatible",
            "reason": (
                "the q=1 candidate passes refined charge/character filters and "
                "all required triplet-mass legs are representative-realizable"
            ),
        }
    if stage["status"] == "representative_unresolved":
        return {
            "category": "unresolved",
            "status": "representative_grammar_unresolved",
            "reason": first_gate_reason(record),
        }
    return {
        "category": "phenomenologically obstructed",
        "status": "representative_grammar_obstructed",
        "reason": first_gate_reason(record),
    }


def apply_representative_grammar_boundary(
    *,
    filtered_record: dict[str, Any],
    grammar_gate: RepresentativeGrammarGate,
    source: dict[str, Any] | None = None,
    weight: int = 1,
) -> dict[str, Any]:
    """Attach the refined-selection and representative-promotion boundary.

    The input record is the filtered candidate emitted by the phenomenology
    builders.  It is mutated in place so old reports retain their source
    classification while new reports expose the stronger promotion boundary.
    """

    mass_table = refined_mass_table(filtered_record)
    selection = refined_classification(filtered_record, mass_table)
    filtered_record["character_refined_classification"] = selection
    filtered_record["character_refined_mass_support_classes"] = dict(
        sorted(
            Counter(item["character_refined_support_class"] for item in mass_table).items()
        )
    )

    if selection["category"] != "viable":
        boundary = {
            "selection_rule_stage": selection,
            "representative_grammar_stage": {
                "status": "not_evaluated_selection_rule_not_viable",
                "promoted_to_lead_candidate": False,
                "cup_product_planning_allowed": False,
                "target_status_counts": {},
            },
            "triplet_mass_targets": [],
        }
        filtered_record["representative_grammar_gate"] = boundary
        return boundary

    candidate = full_candidate_record(
        source=source or filtered_record.get("source") or {},
        weight=weight,
        record=filtered_record,
        mass_table=mass_table,
        classification=selection,
    )
    boundary = grammar_gate.promotion_record(
        candidate=candidate,
        mass_table=mass_table,
        selection_rule_status=selection["status"],
    )
    boundary["selection_rule_stage"] = selection
    filtered_record["pre_representative_classification"] = filtered_record.get(
        "classification"
    )
    filtered_record["representative_grammar_gate"] = boundary
    filtered_record["classification"] = classification_from_representative_gate(boundary)
    return boundary
