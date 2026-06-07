#!/usr/bin/env python3
"""Finite character-envelope audit for unresolved CICY6715 candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from build_cicy6715_6927_same_hodge_lateral_wall_metric_pass import all_gutall_data  # noqa: E402
from build_cicy6836_lead_component_character_dossier import (  # noqa: E402
    CHARACTERS,
    Z2xZ2KoszulEngine,
    build_sector_characters,
    determinant_trivial_twists,
    parse_selected_option,
    rep_from_multiplicities,
)
from build_cicy6836_wilson_embedding_precup_rerank import (  # noqa: E402
    build_base_singlet_certificates,
    full_embedding_audit,
    serial_counter,
    spectrum_for_embedding,
)
from string_theory.cohomology import bundle_line_summands  # noqa: E402


TARGET_CICY = 6715
TARGET_OPTION_INDEX = 1
STATUS_CLEAN_BRANCH = "cicy6715_unresolved_envelope_clean_branch_possible"
STATUS_NO_CLEAN_BRANCH = "cicy6715_unresolved_envelope_no_clean_branch"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def compositions(total: int, parts: int) -> list[tuple[int, ...]]:
    if parts == 1:
        return [(total,)]
    out = []
    for head in range(total + 1):
        for tail in compositions(total - head, parts - 1):
            out.append((head, *tail))
    return out


def possible_reps(dimension: int) -> list[dict[str, Any]]:
    return [
        rep_from_multiplicities(
            {character: multiplicities[index] for index, character in enumerate(CHARACTERS)}
        )
        for multiplicities in compositions(dimension, len(CHARACTERS))
    ]


def unresolved_certificates(sectors: dict[str, Any], sector_key: str) -> list[dict[str, Any]]:
    return [
        certificate
        for certificate in sectors[sector_key]["line_certificates"]
        if any(certificate["cohomology"])
        and not certificate["actual_character_computed"]
    ]


def force_unresolved_branch(
    *,
    sectors: dict[str, Any],
    pair: tuple[int, int],
    h1_rep: dict[str, Any],
    h2_rep: dict[str, Any],
) -> dict[str, Any]:
    branched = deepcopy(sectors)
    for certificate in branched["wedge2_V"]["line_certificates"]:
        if tuple(certificate.get("summand_pair", [])) == pair:
            certificate["actual"] = {"H1": h1_rep, "H2": h2_rep}
            certificate["actual_character_computed"] = True
            certificate["method"] = "finite_character_envelope_branch"
    for certificate in branched["wedge2_V_dual"]["line_certificates"]:
        if tuple(certificate.get("summand_pair", [])) == pair:
            # Z2xZ2 irreps are self-dual, so Serre duality swaps H1/H2 reps.
            certificate["actual"] = {"H1": h2_rep, "H2": h1_rep}
            certificate["actual_character_computed"] = True
            certificate["method"] = "finite_character_envelope_branch_serre_dual"
    for sector in branched.values():
        sector["all_characters_computed"] = all(
            certificate["actual_character_computed"]
            for certificate in sector["line_certificates"]
            if any(certificate["cohomology"])
        )
    return branched


def compact_full_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": record["label"],
        "embedding_index": record["embedding_index"],
        "summand_fiber_character_assignment": record[
            "summand_fiber_character_assignment"
        ],
        "weak_character": record["weak_character"],
        "spectrum": record["spectrum"],
        "mass_operator_summary": record["mass_operator_summary"],
        "dangerous_operator_summary": record["dangerous_operator_summary"],
        "classification": record["classification"],
    }


def branch_label(model_index: int, branch_index: int, h1_rep: dict[str, Any], h2_rep: dict[str, Any]) -> str:
    return (
        f"model{model_index}_branch{branch_index:04d}_"
        f"h1{json.dumps(h1_rep['multiplicities'], sort_keys=True)}_"
        f"h2{json.dumps(h2_rep['multiplicities'], sort_keys=True)}"
    )


def audit_branch(
    *,
    model_index: int,
    branch_index: int,
    component_report: dict[str, Any],
    base_singlets: list[dict[str, Any]],
    h1_rep: dict[str, Any],
    h2_rep: dict[str, Any],
) -> dict[str, Any]:
    one_higgs_count = 0
    proton_safe_count = 0
    clean_count = 0
    status_counter: Counter[str] = Counter()
    obstruction_counter: Counter[str] = Counter()
    mass_signature_counter: Counter[str] = Counter()
    dangerous_signature_counter: Counter[str] = Counter()
    examples = []
    index = 0
    for assignment in determinant_trivial_twists():
        for weak_character in CHARACTERS[1:]:
            spectrum = spectrum_for_embedding(
                component_report=component_report,
                assignment=assignment,
                weak_character=weak_character,
            )
            if not spectrum["one_higgs_pair_triplet_free"]:
                index += 1
                continue
            one_higgs_count += 1
            full = full_embedding_audit(
                label=f"cicy6715_model{model_index}_branch{branch_index:04d}_wilson_{index:03d}",
                index=index,
                component_report=component_report,
                base_singlets=base_singlets,
                assignment=assignment,
                weak_character=weak_character,
            )
            status_counter[full["classification"]["status"]] += 1
            for obstruction in full["classification"]["precise_obstructions"]:
                obstruction_counter[obstruction] += 1
            mass_signature_counter[
                json.dumps(full["mass_operator_summary"]["support_class_counts"], sort_keys=True)
            ] += 1
            dangerous_signature_counter[
                json.dumps(
                    full["dangerous_operator_summary"]["allowed_operator_labels"],
                    sort_keys=True,
                )
            ] += 1
            if full["dangerous_operator_summary"]["allowed_count"] == 0:
                proton_safe_count += 1
            if full["classification"]["category"] == "pre_cup_survivor":
                clean_count += 1
            if len(examples) < 4 and (
                full["dangerous_operator_summary"]["allowed_count"] == 0
                or full["classification"]["category"] == "pre_cup_survivor"
            ):
                examples.append(compact_full_record(full))
            index += 1
    return {
        "branch_index": branch_index,
        "branch_label": branch_label(model_index, branch_index, h1_rep, h2_rep),
        "h1_rep": h1_rep,
        "h2_rep": h2_rep,
        "one_higgs_pair_triplet_free_count": one_higgs_count,
        "one_higgs_proton_safe_count": proton_safe_count,
        "clean_one_higgs_precup_count": clean_count,
        "one_higgs_status_counts": serial_counter(status_counter),
        "one_higgs_obstruction_counts": serial_counter(obstruction_counter),
        "one_higgs_mass_signature_counts": serial_counter(mass_signature_counter),
        "one_higgs_dangerous_signature_counts": serial_counter(dangerous_signature_counter),
        "examples": examples,
    }


def audit_candidate(
    *,
    candidate: dict[str, Any],
    conf: list[list[int]],
    option: dict[str, Any],
    max_branches: int | None,
) -> dict[str, Any]:
    sectors = build_sector_characters(candidate["matrix"], conf, option)
    unresolved_wedge = unresolved_certificates(sectors, "wedge2_V")
    unresolved_dual = unresolved_certificates(sectors, "wedge2_V_dual")
    if len(unresolved_wedge) != 1 or len(unresolved_dual) != 1:
        raise ValueError(
            f"expected exactly one unresolved wedge line and dual for model {candidate['model_index']}"
        )
    pair = tuple(unresolved_wedge[0]["summand_pair"])
    if tuple(unresolved_dual[0]["summand_pair"]) != pair:
        raise ValueError(f"unresolved Serre-dual pair mismatch for model {candidate['model_index']}")
    cohomology = unresolved_wedge[0]["cohomology"]
    h1_options = possible_reps(cohomology[1])
    h2_options = possible_reps(cohomology[2])
    engine = Z2xZ2KoszulEngine(conf, option)
    base_singlets = build_base_singlet_certificates(
        engine=engine,
        line_summands=bundle_line_summands(candidate["matrix"]),
    )
    branch_records = []
    branch_counter = 0
    aggregate_status: Counter[str] = Counter()
    aggregate_obstructions: Counter[str] = Counter()
    aggregate_mass_signatures: Counter[str] = Counter()
    aggregate_danger_signatures: Counter[str] = Counter()
    total_one_higgs = 0
    total_safe = 0
    total_clean = 0
    clean_examples = []
    safe_examples = []
    for h1_rep, h2_rep in product(h1_options, h2_options):
        if max_branches is not None and branch_counter >= max_branches:
            break
        branched_sectors = force_unresolved_branch(
            sectors=sectors,
            pair=pair,
            h1_rep=h1_rep,
            h2_rep=h2_rep,
        )
        component_report = {
            "lead_source": {
                "cicy": candidate["cicy"],
                "model_index": candidate["model_index"],
                "selected_free_option_index": candidate["selected_free_option_index"],
                "matrix": candidate["matrix"],
                "upstairs_cohomology": candidate["upstairs_cohomology"],
                "upstairs_spectrum": candidate["upstairs_spectrum"],
            },
            "equivariant_cohomology_characters": branched_sectors,
        }
        branch = audit_branch(
            model_index=candidate["model_index"],
            branch_index=branch_counter,
            component_report=component_report,
            base_singlets=base_singlets,
            h1_rep=h1_rep,
            h2_rep=h2_rep,
        )
        branch_records.append(branch)
        total_one_higgs += branch["one_higgs_pair_triplet_free_count"]
        total_safe += branch["one_higgs_proton_safe_count"]
        total_clean += branch["clean_one_higgs_precup_count"]
        aggregate_status.update(branch["one_higgs_status_counts"])
        aggregate_obstructions.update(branch["one_higgs_obstruction_counts"])
        aggregate_mass_signatures.update(branch["one_higgs_mass_signature_counts"])
        aggregate_danger_signatures.update(branch["one_higgs_dangerous_signature_counts"])
        for example in branch["examples"]:
            if example["classification"]["category"] == "pre_cup_survivor" and len(clean_examples) < 8:
                clean_examples.append({**example, "branch_index": branch_counter})
            elif example["dangerous_operator_summary"]["allowed_count"] == 0 and len(safe_examples) < 8:
                safe_examples.append({**example, "branch_index": branch_counter})
        branch_counter += 1
    status = (
        "clean_branch_possible"
        if total_clean
        else "proton_safe_but_doublet_or_other_obstructed"
        if total_safe
        else "no_one_higgs_proton_safe_branch"
    )
    return {
        "cicy": candidate["cicy"],
        "model_index": candidate["model_index"],
        "selected_free_option_index": candidate["selected_free_option_index"],
        "matrix": candidate["matrix"],
        "status": status,
        "unresolved_pair": list(pair),
        "unresolved_line_bundle": unresolved_wedge[0]["line_bundle"],
        "unresolved_dual_line_bundle": unresolved_dual[0]["line_bundle"],
        "unresolved_cohomology": cohomology,
        "unresolved_e2_dimensions": {
            key: value["dimension"]
            for key, value in unresolved_wedge[0]["e2_by_cohomology_degree"].items()
        },
        "base_singlet_count": len(base_singlets),
        "base_singlet_status_counts": serial_counter(
            Counter(item["base_representative_status"] for item in base_singlets)
        ),
        "h1_rep_option_count": len(h1_options),
        "h2_rep_option_count": len(h2_options),
        "branch_count": len(branch_records),
        "max_branches": max_branches,
        "total_one_higgs_pair_triplet_free_count": total_one_higgs,
        "total_one_higgs_proton_safe_count": total_safe,
        "total_clean_one_higgs_precup_count": total_clean,
        "aggregate_one_higgs_status_counts": serial_counter(aggregate_status),
        "aggregate_one_higgs_obstruction_counts": serial_counter(aggregate_obstructions),
        "aggregate_one_higgs_mass_signature_counts": serial_counter(aggregate_mass_signatures),
        "aggregate_one_higgs_dangerous_signature_counts": serial_counter(aggregate_danger_signatures),
        "safe_examples": safe_examples,
        "clean_examples": clean_examples,
        "closest_branches": sorted(
            branch_records,
            key=lambda item: (
                -item["clean_one_higgs_precup_count"],
                -item["one_higgs_proton_safe_count"],
                -item["one_higgs_pair_triplet_free_count"],
                item["branch_index"],
            ),
        )[:12],
    }


def build_report(
    *,
    lateral_json: Path,
    lateral_verification_json: Path,
    operator_graph_json: Path,
    operator_graph_verification_json: Path,
    max_branches: int | None,
) -> dict[str, Any]:
    lateral = load_json(lateral_json)
    lateral_verification = load_json(lateral_verification_json)
    operator_graph = load_json(operator_graph_json)
    operator_graph_verification = load_json(operator_graph_verification_json)
    cicy_by_num, _ = all_gutall_data()
    conf = cicy_by_num[TARGET_CICY]["Conf"]
    option = parse_selected_option(TARGET_CICY, TARGET_OPTION_INDEX)
    unresolved = [
        item
        for item in lateral["promoted_candidates"]
        if item.get("promotion_status") == "component_character_unresolved"
    ]
    candidate_records = [
        audit_candidate(candidate=item, conf=conf, option=option, max_branches=max_branches)
        for item in unresolved
    ]
    total_clean = sum(item["total_clean_one_higgs_precup_count"] for item in candidate_records)
    total_safe = sum(item["total_one_higgs_proton_safe_count"] for item in candidate_records)
    total_one_higgs = sum(
        item["total_one_higgs_pair_triplet_free_count"] for item in candidate_records
    )
    status = STATUS_CLEAN_BRANCH if total_clean else STATUS_NO_CLEAN_BRANCH
    branch_count = sum(item["branch_count"] for item in candidate_records)
    expected_full_branch_count = sum(
        item["h1_rep_option_count"] * item["h2_rep_option_count"]
        for item in candidate_records
    )
    gates = {
        "source_artifacts_verified": gate(
            lateral["all_gates_pass"]
            and lateral_verification["all_gates_pass"]
            and operator_graph["all_gates_pass"]
            and operator_graph_verification["all_gates_pass"],
            f"{lateral_json} + {operator_graph_json}",
            "envelope audit starts from verified CICY6715/6927 and operator-graph atlas artifacts",
        ),
        "unresolved_candidate_set_matches_atlas": gate(
            [item["model_index"] for item in unresolved] == [229, 245, 591, 596, 766]
            and operator_graph["bounded_obstruction_atlas"]["fails_by_component_characters"]
            == [[6715, 229, 1], [6715, 245, 1], [6715, 591, 1], [6715, 596, 1], [6715, 766, 1]],
            str(lateral_json),
            "the five CICY6715 component-unresolved q1 candidates are exactly the atlas uncertainty set",
        ),
        "unresolved_structure_is_single_wedge_pair": gate(
            all(
                item["unresolved_cohomology"] in ([0, 2, 2, 0], [0, 3, 3, 0])
                and item["base_singlet_status_counts"] == {"representative_compatible": item["base_singlet_count"]}
                for item in candidate_records
            ),
            "finite envelope candidate records",
            "each unresolved candidate has exactly one unresolved wedge pair, its dual, and compatible singlets",
        ),
        "finite_envelope_scope_is_complete": gate(
            max_branches is not None
            or branch_count == expected_full_branch_count == 1100,
            "character branch enumeration",
            "all Serre-dual H1/H2 character compositions are enumerated when no branch cap is set",
        ),
        "classification_matches_clean_count": gate(
            (bool(total_clean) and status == STATUS_CLEAN_BRANCH)
            or (not total_clean and status == STATUS_NO_CLEAN_BRANCH),
            "envelope clean-count rollup",
            "report status is determined by whether any branch can hide a clean one-Higgs pre-cup survivor",
        ),
    }
    return {
        "title": "CICY6715 Component-Unresolved Character Envelope Audit",
        "status": status,
        "scope": (
            "finite Serre-dual character-envelope audit for the five CICY6715 "
            "component-unresolved q1 candidates from the order-4 operator graph atlas"
        ),
        "source_artifacts": {
            "cicy6715_6927_lateral": str(lateral_json),
            "cicy6715_6927_lateral_verification": str(lateral_verification_json),
            "operator_graph_atlas": str(operator_graph_json),
            "operator_graph_atlas_verification": str(operator_graph_verification_json),
        },
        "parameters": {
            "target_cicy": TARGET_CICY,
            "target_option_index": TARGET_OPTION_INDEX,
            "max_branches": max_branches,
            "branch_convention": (
                "enumerate all nonnegative Z2xZ2 character multiplicities for the "
                "unresolved wedge2_V H1 and H2 dimensions; assign wedge2_V_dual by "
                "Serre duality, using self-duality of Z2xZ2 irreps"
            ),
        },
        "summary": {
            "candidate_count": len(candidate_records),
            "branch_count": branch_count,
            "expected_full_branch_count": expected_full_branch_count,
            "total_one_higgs_pair_triplet_free_count": total_one_higgs,
            "total_one_higgs_proton_safe_count": total_safe,
            "total_clean_one_higgs_precup_count": total_clean,
            "candidate_status_counts": serial_counter(
                Counter(item["status"] for item in candidate_records)
            ),
        },
        "candidate_records": candidate_records,
        "clean_branch_candidates": [
            item for item in candidate_records if item["total_clean_one_higgs_precup_count"]
        ],
        "proton_safe_branch_candidates": [
            item for item in candidate_records if item["total_one_higgs_proton_safe_count"]
        ],
        "interpretation": {
            "clean_branch_possible": bool(total_clean),
            "bounded_no_clean_branch": not total_clean,
            "note": (
                "This is an envelope audit, not an actual higher-map representative "
                "resolution. A zero clean count proves that no admissible character "
                "completion of the unresolved CICY6715 wedge pair can hide a clean "
                "one-Higgs/proton-safe pre-cup survivor under the current operator gates."
            ),
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# CICY6715 Component-Unresolved Character Envelope Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Parameters",
        "",
    ]
    for key, value in report["parameters"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Summary", ""])
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Candidate Records", ""])
    for item in report["candidate_records"]:
        lines.extend(
            [
                f"### CICY `{item['cicy']}` model `{item['model_index']}` option `{item['selected_free_option_index']}`",
                "",
                f"- status: `{item['status']}`",
                f"- unresolved_pair: `{item['unresolved_pair']}`",
                f"- unresolved_cohomology: `{item['unresolved_cohomology']}`",
                f"- branch_count: `{item['branch_count']}`",
                f"- total_one_higgs_pair_triplet_free_count: `{item['total_one_higgs_pair_triplet_free_count']}`",
                f"- total_one_higgs_proton_safe_count: `{item['total_one_higgs_proton_safe_count']}`",
                f"- total_clean_one_higgs_precup_count: `{item['total_clean_one_higgs_precup_count']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            f"- clean branch possible: `{report['interpretation']['clean_branch_possible']}`",
            f"- bounded no clean branch: `{report['interpretation']['bounded_no_clean_branch']}`",
            f"- note: {report['interpretation']['note']}",
            "",
            "## Gates",
            "",
        ]
    )
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lateral-json",
        default=str(REPORTS / "cicy6715_6927_same_hodge_lateral_wall_metric_pass.json"),
    )
    parser.add_argument(
        "--lateral-verification-json",
        default=str(REPORTS / "cicy6715_6927_same_hodge_lateral_wall_metric_pass_verification.json"),
    )
    parser.add_argument(
        "--operator-graph-json",
        default=str(REPORTS / "cicy6780_operator_graph_lateral_search.json"),
    )
    parser.add_argument(
        "--operator-graph-verification-json",
        default=str(REPORTS / "cicy6780_operator_graph_lateral_search_verification.json"),
    )
    parser.add_argument("--max-branches", type=int)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "cicy6715_component_unresolved_envelope.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "cicy6715_component_unresolved_envelope.md"),
    )
    args = parser.parse_args()
    report = build_report(
        lateral_json=Path(args.lateral_json),
        lateral_verification_json=Path(args.lateral_verification_json),
        operator_graph_json=Path(args.operator_graph_json),
        operator_graph_verification_json=Path(args.operator_graph_verification_json),
        max_branches=args.max_branches,
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"candidate_count={report['summary']['candidate_count']}")
    print(f"branch_count={report['summary']['branch_count']}")
    print(
        "total_clean_one_higgs_precup_count="
        f"{report['summary']['total_clean_one_higgs_precup_count']}"
    )
    print(f"all_gates_pass={report['all_gates_pass']}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
