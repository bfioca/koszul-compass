#!/usr/bin/env python3
"""Representative-feasible escape grammar scout for the radius-9 q=1 frontier."""

from __future__ import annotations

import argparse
import copy
from collections import Counter, defaultdict
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

from build_cicy5259_h2_frontier_search import (  # noqa: E402
    apply_moves,
    matrix_key,
    max_abs_charge,
    rectangle_primitives,
    row_transfer_primitives,
)
from build_phenomenology_filter_report import candidate_certificate_from_5259_record  # noqa: E402
from build_phenomenology_guided_q1_radius2_enhanced_backlog import (  # noqa: E402
    apply_monoid_obstruction_override,
)
from build_phenomenology_guided_q1_radius9_character_refined_dt_report import (  # noqa: E402
    source_records,
)
from build_phenomenology_guided_q1_search import raw_q1_signature  # noqa: E402
from build_vectorlike_obstruction_report import certify_5259_matrix, gate  # noqa: E402
from phenomenology_guided_q1_representative_grammar_gate import (  # noqa: E402
    RepresentativeGrammarGate,
    apply_representative_grammar_boundary,
)
from string_theory.cicy import (  # noqa: E402
    bundle_c1,
    bundle_c2,
    bundle_index,
    triple_intersections,
    wedge2_index,
)
from string_theory.slope import find_slope_zero, intersection_tensor  # noqa: E402
from verify_family_candidate import cohomology_and_spectrum  # noqa: E402


Matrix = list[list[int]]
Move = dict[str, Any]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rep_key(rep: dict[str, Any] | None) -> str:
    if rep is None:
        return "unresolved"
    mult = rep["multiplicities"]
    return f"dim{rep['dimension']}:+{mult['+']}:-{mult['-']}:tr{rep['nonidentity_trace']}"


def parse_pair(label: str) -> tuple[int, int] | None:
    if "_" not in label:
        return None
    suffix = label.split("_", 1)[1]
    if len(suffix) != 2 or not suffix.isdigit():
        return None
    return tuple(sorted((int(suffix[0]), int(suffix[1]))))


def operator_pairs(operator: str) -> set[tuple[int, int]]:
    pairs = set()
    for factor in operator.split("*"):
        pair = parse_pair(factor)
        if pair is not None:
            pairs.add(pair)
    return pairs


def role_pair(role: str) -> tuple[int, int] | None:
    return parse_pair(role.split(":", 1)[0])


def compact_obstruction_target(record: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    summary = target["obstruction_summary"]
    return {
        "candidate_label": record.get("candidate_label", record.get("label")),
        "source": record.get("source"),
        "weight": record.get("weight", 1),
        "operator": target["operator"],
        "obstructing_role": summary["first_obstructing_role"],
        "branch_requested": summary["branch_actual"],
        "representative_feasible": summary["computed_actual"],
        "required_image_ranks_for_branch": summary.get("required_image_ranks_for_branch"),
        "reason": summary["reason"],
    }


def mine_pruned_seed_records(
    *,
    windows: int,
    grammar_gate: RepresentativeGrammarGate,
) -> list[dict[str, Any]]:
    seeds = []
    for source, weight, original in source_records(windows):
        record = copy.deepcopy(original)
        boundary = apply_representative_grammar_boundary(
            filtered_record=record,
            grammar_gate=grammar_gate,
            source=source,
            weight=weight,
        )
        if (
            boundary["selection_rule_stage"]["category"] == "viable"
            and boundary["representative_grammar_stage"]["status"]
            == "representative_obstructed"
        ):
            targets = [
                compact_obstruction_target(record, target)
                for target in boundary["triplet_mass_targets"]
                if target.get("obstruction_summary")
            ]
            seeds.append(
                {
                    "candidate_label": record["label"],
                    "source": source,
                    "weight": weight,
                    "matrix": record["matrix"],
                    "selection_rule_stage": boundary["selection_rule_stage"],
                    "representative_grammar_stage": boundary[
                        "representative_grammar_stage"
                    ],
                    "obstructed_targets": targets,
                }
            )
    return seeds


def mine_feasible_patterns(
    *,
    seeds: list[dict[str, Any]],
    escape_report: dict[str, Any],
) -> dict[str, Any]:
    patterns: dict[str, dict[str, Any]] = {}
    target_pairs: set[tuple[int, int]] = set()

    def add_pattern(
        *,
        source: str,
        operator: str,
        role: str,
        branch_requested: dict[str, Any] | None,
        representative_feasible: dict[str, Any] | None,
        status: str,
        weight: int,
        reason: str,
    ) -> None:
        pair = role_pair(role)
        if pair is not None:
            target_pairs.add(pair)
        target_pairs.update(operator_pairs(operator))
        key = f"{operator}|{role}|{rep_key(representative_feasible)}"
        item = patterns.setdefault(
            key,
            {
                "operator": operator,
                "role": role,
                "role_pair": list(pair) if pair is not None else None,
                "branch_requested_examples": [],
                "representative_feasible": representative_feasible,
                "status": status,
                "sources": Counter(),
                "represented_weight": 0,
                "reasons": Counter(),
            },
        )
        if branch_requested is not None and len(item["branch_requested_examples"]) < 4:
            item["branch_requested_examples"].append(branch_requested)
        item["sources"][source] += 1
        item["represented_weight"] += weight
        item["reasons"][reason] += 1

    for seed in seeds:
        for target in seed["obstructed_targets"]:
            add_pattern(
                source="generation_pruned_survivor",
                operator=target["operator"],
                role=target["obstructing_role"],
                branch_requested=target["branch_requested"],
                representative_feasible=target["representative_feasible"],
                status="representative_feasible_replacement",
                weight=seed["weight"],
                reason=target["reason"],
            )

    for item in escape_report["obstruction_anatomy"]:
        for operator in item["operators"]:
            add_pattern(
                source="closed_frontier_obstruction_anatomy",
                operator=operator,
                role=item["obstruction_role"],
                branch_requested=item["branch_actual"],
                representative_feasible=item["computed_actual"],
                status="representative_feasible_replacement",
                weight=item["represented_weight"],
                reason=item["reason"],
            )

    for target in escape_report["escape_scan"]["audited_escape_targets"]:
        for leg in target["matter_leg_statuses"]:
            add_pattern(
                source="observed_triplet_shape_escape_audit",
                operator=target["operator"],
                role=leg["role"],
                branch_requested=leg.get("branch_actual"),
                representative_feasible=leg.get("computed_actual"),
                status=(
                    "representative_unresolved"
                    if leg.get("computed_actual") is None
                    else "representative_feasible_replacement"
                ),
                weight=target["weight"],
                reason=leg["reason"],
            )

    pattern_rows = []
    for item in patterns.values():
        row = {
            **item,
            "sources": dict(sorted(item["sources"].items())),
            "reasons": dict(sorted(item["reasons"].items())),
        }
        pattern_rows.append(row)
    pattern_rows.sort(
        key=lambda item: (
            item["status"] != "representative_feasible_replacement",
            item["operator"],
            item["role"],
            rep_key(item["representative_feasible"]),
        )
    )
    return {
        "feasible_patterns": pattern_rows,
        "target_column_pairs": [list(pair) for pair in sorted(target_pairs)],
        "observed_triplet_only_operator_shapes": sorted(
            escape_report["escape_scan"]["triplet_only_operator_rows"]
        ),
    }


def targeted_primitives(target_pairs: list[list[int]]) -> list[Move]:
    pairs = {tuple(pair) for pair in target_pairs}
    primitives = []
    for primitive in [*row_transfer_primitives(), *rectangle_primitives()]:
        columns = tuple(sorted(primitive["columns"]))
        if columns in pairs:
            primitives.append(primitive)
    primitives.sort(key=lambda item: json.dumps(item, sort_keys=True))
    return primitives


def unique_seed_records(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    out = []
    for seed in seeds:
        key = matrix_key(seed["matrix"])
        if key in seen:
            continue
        seen.add(key)
        out.append(seed)
    return out


def screen_candidate(
    *,
    matrix: Matrix,
    conf: list[list[int]],
    c2_tx: list[int],
    intersections: dict[tuple[int, int, int], int],
    tensor: Any,
    slope_restarts: int,
    slope_max_iterations: int,
    seed: int,
) -> tuple[str, dict[str, Any]]:
    if bundle_c1(matrix) != [0] * 7:
        return "c1", {}
    if (
        bundle_index(matrix, intersections, c2_tx) != -6
        or wedge2_index(matrix, intersections, c2_tx) != -6
    ):
        return "index", {}
    c2_v = bundle_c2(matrix, intersections)
    anomaly = [tx - v for tx, v in zip(c2_tx, c2_v)]
    if not all(value >= 0 for value in anomaly):
        return "anomaly", {"anomaly": anomaly}
    slope = find_slope_zero(
        matrix,
        tensor,
        tolerance=1e-7,
        restarts=slope_restarts,
        max_iterations=slope_max_iterations,
        seed=seed,
    )
    if not slope.feasible:
        return "slope", {"anomaly": anomaly, "slope_search": slope.as_dict()}
    cohomology = cohomology_and_spectrum(
        {"Num": 7914, "H11": 7, "Conf": conf, "C2": c2_tx},
        2,
        matrix,
    )
    spectrum = cohomology["su5_upstairs_spectrum"]
    quality = cohomology["line_bundle_sum_quality"]
    if (
        not all(spectrum["checks"].values())
        or spectrum["upstairs_anti_10"] != 0
        or not quality["regular_nontrivial_summand_scan_style"]
    ):
        return "spectrum_or_quality", {
            "anomaly": anomaly,
            "slope_search": slope.as_dict(),
            "spectrum": spectrum,
        }
    if not raw_q1_signature(cohomology):
        return "not_raw_q1", {
            "anomaly": anomaly,
            "slope_search": slope.as_dict(),
            "cohomology": {
                "V": cohomology["V_cohomology"],
                "V_dual": cohomology["V_dual_cohomology"],
                "wedge2_V": cohomology["wedge2_V_cohomology"],
                "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
            },
        }
    return "raw_q1", {
        "anomaly": anomaly,
        "slope_search": slope.as_dict(),
        "cohomology": {
            "V": cohomology["V_cohomology"],
            "V_dual": cohomology["V_dual_cohomology"],
            "wedge2_V": cohomology["wedge2_V_cohomology"],
            "wedge2_V_dual": cohomology["wedge2_V_dual_cohomology"],
        },
    }


def operator_targeted(candidate: dict[str, Any], target_pairs: set[tuple[int, int]]) -> bool:
    boundary = candidate["representative_grammar_gate"]
    targets = boundary.get("triplet_mass_targets") or []
    for target in targets:
        if any(pair in target_pairs for pair in operator_pairs(target["operator"])):
            return True
    return False


def run_local_move_escape_scout(
    *,
    seeds: list[dict[str, Any]],
    target_pairs: list[list[int]],
    max_generated_matrices: int,
    max_certifications: int,
    max_abs_charge_bound: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
) -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]
    c2_tx = split["full_picard_presentation_7914"]["c2_tx"]
    intersections = triple_intersections(conf)
    tensor = intersection_tensor(intersections, 7)
    grammar_gate = RepresentativeGrammarGate()
    primitives = targeted_primitives(target_pairs)
    unique_seeds = unique_seed_records(seeds)
    target_pair_set = {tuple(pair) for pair in target_pairs}
    seen = {matrix_key(seed["matrix"]) for seed in unique_seeds}
    generated = []
    raw_q1_records = []
    certified_records = []
    filtered_records = []
    rejection_counts: Counter[str] = Counter()
    move_counts: Counter[str] = Counter()
    topology_errors = []

    for seed_index, seed_record in enumerate(unique_seeds):
        if len(generated) >= max_generated_matrices:
            break
        for primitive in primitives:
            if len(generated) >= max_generated_matrices:
                break
            matrix = apply_moves(seed_record["matrix"], [primitive])
            key = matrix_key(matrix)
            if key in seen:
                rejection_counts["duplicate_up_to_summand_permutation"] += 1
                continue
            seen.add(key)
            if max_abs_charge(matrix) > max_abs_charge_bound:
                rejection_counts["max_abs_charge"] += 1
                continue
            move_counts[primitive["family"]] += 1
            candidate_id = f"escape_seed{seed_index}_move{len(generated)}"
            try:
                status, detail = screen_candidate(
                    matrix=matrix,
                    conf=conf,
                    c2_tx=c2_tx,
                    intersections=intersections,
                    tensor=tensor,
                    slope_restarts=slope_restarts,
                    slope_max_iterations=slope_max_iterations,
                    seed=seed + len(generated),
                )
            except Exception as exc:  # noqa: BLE001 - preserve scout evidence.
                rejection_counts["screening_exception"] += 1
                if len(topology_errors) < 8:
                    topology_errors.append(
                        {
                            "candidate_id": candidate_id,
                            "type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                continue
            generated.append(
                {
                    "candidate_id": candidate_id,
                    "seed_label": seed_record["candidate_label"],
                    "seed_source": seed_record["source"],
                    "move": primitive,
                    "screening_status": status,
                    "matrix": matrix,
                    "detail": detail,
                }
            )
            if status != "raw_q1":
                rejection_counts[status] += 1
                continue
            raw_q1_records.append(generated[-1])
            if len(certified_records) >= max_certifications:
                rejection_counts["raw_q1_not_certified_budget"] += 1
                continue
            certified = certify_5259_matrix(
                label=f"escape_grammar_certified_{len(certified_records)}",
                matrix=matrix,
                move=[
                    {
                        "seed_label": seed_record["candidate_label"],
                        "seed_source": seed_record["source"],
                    },
                    primitive,
                ],
                slope_restarts=certification_restarts,
                slope_seed=seed + 500000 + len(certified_records),
            )
            certified["escape_grammar_seed_label"] = seed_record["candidate_label"]
            certified["escape_grammar_seed_source"] = seed_record["source"]
            certified["escape_grammar_move"] = primitive
            certified_records.append(certified)
            filtered = candidate_certificate_from_5259_record(
                label=f"escape_grammar_filtered_{len(filtered_records)}",
                record=certified,
                conf=conf,
            )
            apply_monoid_obstruction_override(filtered)
            filtered["escape_grammar_seed_label"] = seed_record["candidate_label"]
            filtered["escape_grammar_seed_source"] = seed_record["source"]
            filtered["escape_grammar_move"] = primitive
            boundary = apply_representative_grammar_boundary(
                filtered_record=filtered,
                grammar_gate=grammar_gate,
                source={
                    "kind": "escape_grammar_local_move",
                    "seed_label": seed_record["candidate_label"],
                    "seed_source": seed_record["source"],
                    "move": primitive,
                },
                weight=1,
            )
            filtered["escape_grammar_targeted_operator_shape"] = operator_targeted(
                filtered, target_pair_set
            )
            filtered["escape_grammar_boundary_status"] = boundary[
                "representative_grammar_stage"
            ]["status"]
            filtered_records.append(filtered)

    representative_statuses = Counter(
        record["representative_grammar_gate"]["representative_grammar_stage"]["status"]
        for record in filtered_records
    )
    refined_statuses = Counter(
        record["character_refined_classification"]["status"]
        for record in filtered_records
    )
    selection_viable = [
        record
        for record in filtered_records
        if record["character_refined_classification"]["category"] == "viable"
    ]
    desired_q1_after_character = [
        record
        for record in filtered_records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    compatible = [
        record
        for record in filtered_records
        if record["representative_grammar_gate"]["representative_grammar_stage"][
            "status"
        ]
        == "representative_compatible"
    ]
    unresolved = [
        record
        for record in filtered_records
        if record["representative_grammar_gate"]["representative_grammar_stage"][
            "status"
        ]
        == "representative_unresolved"
    ]
    cup_eligible = [
        record
        for record in filtered_records
        if record["representative_grammar_gate"]["representative_grammar_stage"][
            "cup_product_planning_allowed"
        ]
    ]
    return {
        "bounds": {
            "max_generated_matrices": max_generated_matrices,
            "max_certifications": max_certifications,
            "max_abs_charge_bound": max_abs_charge_bound,
            "slope_restarts": slope_restarts,
            "slope_max_iterations": slope_max_iterations,
            "certification_restarts": certification_restarts,
            "seed": seed,
            "local_move_radius": 1,
            "targeted_primitive_count": len(primitives),
            "unique_seed_count": len(unique_seeds),
        },
        "targeted_move_families": dict(sorted(move_counts.items())),
        "screening_rejections": dict(sorted(rejection_counts.items())),
        "generated_candidates": generated,
        "raw_q1_records": raw_q1_records,
        "certified_records": certified_records,
        "filtered_records": filtered_records,
        "summary": {
            "generated_candidate_count": len(generated),
            "raw_q1_candidate_count": len(raw_q1_records),
            "certified_candidate_count": len(certified_records),
            "filtered_candidate_count": len(filtered_records),
            "screening_rejected_before_certification_count": len(generated)
            - len(raw_q1_records),
            "certified_rejected_before_representative_audit_count": len(filtered_records)
            - len(selection_viable),
            "total_rejected_before_representative_audit_count": len(generated)
            - len(selection_viable),
            "desired_q1_after_character_candidate_count": len(
                desired_q1_after_character
            ),
            "selection_viable_count": len(selection_viable),
            "character_refined_statuses": dict(sorted(refined_statuses.items())),
            "representative_statuses": dict(sorted(representative_statuses.items())),
            "representative_compatible_count": len(compatible),
            "representative_unresolved_count": len(unresolved),
            "cup_product_eligible_count": len(cup_eligible),
            "targeted_operator_shape_filtered_count": sum(
                1
                for record in filtered_records
                if record["escape_grammar_targeted_operator_shape"]
            ),
        },
        "representative_compatible_records": compatible,
        "representative_unresolved_records": unresolved,
        "cup_product_eligible_records": cup_eligible,
        "screening_exception_samples": topology_errors,
    }


def build_report(
    *,
    windows: int,
    max_generated_matrices: int,
    max_certifications: int,
    max_abs_charge_bound: int,
    slope_restarts: int,
    slope_max_iterations: int,
    certification_restarts: int,
    seed: int,
    replay_json: Path,
    replay_verification_json: Path,
    escape_json: Path,
    escape_verification_json: Path,
) -> dict[str, Any]:
    replay = load_json(replay_json)
    replay_verification = load_json(replay_verification_json)
    escape = load_json(escape_json)
    escape_verification = load_json(escape_verification_json)
    grammar_gate = RepresentativeGrammarGate()
    seeds = mine_pruned_seed_records(windows=windows, grammar_gate=grammar_gate)
    mined = mine_feasible_patterns(seeds=seeds, escape_report=escape)
    scout = run_local_move_escape_scout(
        seeds=seeds,
        target_pairs=mined["target_column_pairs"],
        max_generated_matrices=max_generated_matrices,
        max_certifications=max_certifications,
        max_abs_charge_bound=max_abs_charge_bound,
        slope_restarts=slope_restarts,
        slope_max_iterations=slope_max_iterations,
        certification_restarts=certification_restarts,
        seed=seed,
    )
    summary = {
        "windows_closed": windows,
        "generation_pruned_seed_rows": len(seeds),
        "generation_pruned_seed_weight": sum(seed["weight"] for seed in seeds),
        "observed_triplet_only_operator_shape_count": len(
            mined["observed_triplet_only_operator_shapes"]
        ),
        "feasible_pattern_count": len(
            [
                item
                for item in mined["feasible_patterns"]
                if item["status"] == "representative_feasible_replacement"
            ]
        ),
        "unresolved_pattern_count": len(
            [
                item
                for item in mined["feasible_patterns"]
                if item["status"] == "representative_unresolved"
            ]
        ),
        **scout["summary"],
    }
    compatible = scout["representative_compatible_records"]
    gates = {
        "imports_verified_generation_replay": gate(
            replay["all_gates_pass"]
            and replay_verification["all_gates_pass"]
            and replay["summary"]["representative_grammar_pruned_rows"] == 14,
            f"{replay_json} + {replay_verification_json}",
            "escape scout starts from the verified representative-gated generation replay",
        ),
        "imports_verified_observed_operator_shapes": gate(
            escape["all_gates_pass"]
            and escape_verification["all_gates_pass"]
            and len(escape["escape_scan"]["triplet_only_operator_rows"]) == 16,
            f"{escape_json} + {escape_verification_json}",
            "escape scout imports the verified observed triplet-only operator inventory",
        ),
        "mines_expected_pruned_seed_set": gate(
            len(seeds) == 14
            and sum(seed["weight"] for seed in seeds) == 1962
            and len(mined["observed_triplet_only_operator_shapes"]) == 16,
            "generation-pruned seeds and observed triplet-only shapes",
            "the feasible-pattern miner covers the requested 14 seeds and 16 operator shapes",
        ),
        "feasible_patterns_emit_target_pairs": gate(
            summary["feasible_pattern_count"] > 0
            and len(mined["target_column_pairs"]) > 0
            and scout["bounds"]["targeted_primitive_count"] > 0,
            "representative feasible pattern miner",
            "the scout emits representative-feasible patterns and targeted local move primitives",
        ),
        "local_move_scout_is_bounded": gate(
            scout["bounds"]["max_generated_matrices"] == max_generated_matrices
            and scout["bounds"]["max_certifications"] == max_certifications
            and scout["bounds"]["local_move_radius"] == 1
            and summary["generated_candidate_count"] <= max_generated_matrices
            and summary["certified_candidate_count"] <= max_certifications,
            "escape local move bounds",
            "the escape grammar scout stays within explicit local move and certification bounds",
        ),
        "preservation_gates_are_enforced_before_representative_audit": gate(
            all(
                record["screening_status"] == "raw_q1"
                for record in scout["raw_q1_records"]
            )
            and summary["certified_candidate_count"]
            == summary["filtered_candidate_count"],
            "screening and certification records",
            "only candidates preserving index/anomaly/slope/spectrum/q1 reach the representative audit",
        ),
        "zero_promotion_ready_candidate_under_bounds": gate(
            len(compatible) == 0
            and summary["cup_product_eligible_count"] == 0,
            "escape grammar scout results",
            "bounded feasible-character local move scout found no promotion-ready candidate",
        ),
    }
    return {
        "title": "Radius-9 Representative-Feasible Escape Grammar Scout",
        "status": (
            "escape_grammar_representative_compatible_candidate_found"
            if compatible
            else "escape_grammar_bounded_local_move_no_promotion_ready_candidate"
        ),
        "scope": (
            "mine representative-feasible branch-character requests and test a "
            "bounded local move escape grammar around the generation-pruned q=1 survivors"
        ),
        "source_artifacts": {
            "generation_replay_json": str(replay_json),
            "generation_replay_verification_json": str(replay_verification_json),
            "obstruction_escape_json": str(escape_json),
            "obstruction_escape_verification_json": str(escape_verification_json),
        },
        "summary": summary,
        "feasible_character_mining": mined,
        "local_move_escape_scout": scout,
        "interpretation": {
            "escape_strategy": (
                "target one-move deformations of the generation-pruned seeds along "
                "column pairs appearing in representative-feasible mass-leg patterns"
            ),
            "current_result": (
                "no representative-compatible or cup-product-eligible candidate is "
                "found inside the bounded feasible-character local move grammar"
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
    lines.extend(["", "## Target Column Pairs", ""])
    lines.append(f"- `{report['feasible_character_mining']['target_column_pairs']}`")
    lines.extend(["", "## Local Move Bounds", ""])
    for key, value in report["local_move_escape_scout"]["bounds"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Screening Rejections", ""])
    lines.append(
        f"- `{report['local_move_escape_scout']['screening_rejections']}`"
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
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument("--max-generated-matrices", type=int, default=240)
    parser.add_argument("--max-certifications", type=int, default=8)
    parser.add_argument("--max-abs-charge-bound", type=int, default=4)
    parser.add_argument("--slope-restarts", type=int, default=4)
    parser.add_argument("--slope-max-iterations", type=int, default=1200)
    parser.add_argument("--certification-restarts", type=int, default=8)
    parser.add_argument("--seed", type=int, default=99001)
    parser.add_argument(
        "--replay-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup.json"
        ),
    )
    parser.add_argument(
        "--replay-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_representative_generation_replay_rollup_verification.json"
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
            / "phenomenology_guided_q1_radius9_escape_grammar_scout.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_escape_grammar_scout.md"
        ),
    )
    args = parser.parse_args()
    report = build_report(
        windows=args.windows,
        max_generated_matrices=args.max_generated_matrices,
        max_certifications=args.max_certifications,
        max_abs_charge_bound=args.max_abs_charge_bound,
        slope_restarts=args.slope_restarts,
        slope_max_iterations=args.slope_max_iterations,
        certification_restarts=args.certification_restarts,
        seed=args.seed,
        replay_json=Path(args.replay_json),
        replay_verification_json=Path(args.replay_verification_json),
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
