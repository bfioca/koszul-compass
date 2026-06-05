#!/usr/bin/env python3
"""Character-refined DT filter for radius-9 q=1 candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import glob
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def multiplicities(item: dict[str, Any] | None) -> dict[str, int]:
    if not item:
        return {"+": 0, "-": 0}
    return {
        "+": int(((item.get("character") or {}).get("multiplicities") or {}).get("+", 0)),
        "-": int(((item.get("character") or {}).get("multiplicities") or {}).get("-", 0)),
    }


def singlet_multiplicities(record: dict[str, Any]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    singlets = record.get("singlet_moduli_inventory") or {}
    for item in singlets.get("all_nonzero_ext1_line_sectors", []):
        cert = item.get("character_certificate") or {}
        actual = cert.get("actual") or {}
        h1 = actual.get("H1") or {}
        mult = h1.get("multiplicities")
        if (
            item.get("h1_dimension", 0) > 0
            and cert.get("actual_character_computed")
            and mult is not None
        ):
            out[item["charge"]["label"]] = {
                "+": int(mult.get("+", 0)),
                "-": int(mult.get("-", 0)),
            }
    return out


def product_support(labels: list[str], singlets: dict[str, dict[str, int]]) -> dict[str, Any]:
    plus = 1
    minus = 0
    missing = []
    for label in labels:
        mult = singlets.get(label)
        if mult is None:
            missing.append(label)
            continue
        next_plus = plus * mult["+"] + minus * mult["-"]
        next_minus = plus * mult["-"] + minus * mult["+"]
        plus, minus = next_plus, next_minus
    return {
        "labels": labels,
        "even_component_count": plus,
        "odd_component_count": minus,
        "has_even_component": plus > 0 and not missing,
        "missing_singlet_character_labels": missing,
    }


def source_records(windows: int):
    for window in range(1, windows + 1):
        scout_path = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_adjacency_scout_window{window}.json"
        )
        if scout_path.exists():
            scout = load_json(scout_path)
            for record in scout.get("filtered_candidate_records", []):
                status = (record.get("classification") or {}).get("status")
                desired = record.get("spectrum_certificate", {}).get(
                    "desired_q1_three_family_signature"
                )
                if status != "missing_character_or_charge_level_data" and desired:
                    yield {
                        "kind": "direct_scout",
                        "window": window,
                        "path": str(scout_path),
                    }, 1, record

        branch_path = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_branch_analysis_window{window}.json"
        )
        if branch_path.exists():
            branch = load_json(branch_path)
            for record in branch.get("desired_q1_branch_candidate_records", []):
                yield {
                    "kind": "bounded_branch",
                    "window": window,
                    "path": str(branch_path),
                }, 1, record

        pattern = REPORTS / (
            f"phenomenology_guided_q1_radius9_broad_window{window}_large_branch_closure_*.json"
        )
        for raw_path in sorted(glob.glob(str(pattern))):
            path = Path(raw_path)
            if path.name.endswith("_verification.json"):
                continue
            closure = load_json(path)
            weight = int(closure.get("summary", {}).get("desired_q1_branches", 0))
            record = closure.get("q1_representative_candidate")
            if weight > 0 and record:
                yield {
                    "kind": "large_branch_representative",
                    "window": window,
                    "path": str(path),
                    "represented_q1_branches": weight,
                }, weight, record


def indexed_inventory(record: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    inventory = record.get("charged_matter_inventory") or {}
    return {
        "fivebar": {item["label"]: item for item in inventory.get("fivebar", [])},
        "five": {item["label"]: item for item in inventory.get("five", [])},
    }


def physical_five_component_inventory(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return physical 5-component characters from H2(wedge2 V).

    The charge inventory labels 5 fields through H1(wedge2 V*) by Serre duality,
    but the Wilson-line spectrum and component assignment use H2(wedge2 V).
    For DT support, the H2(wedge2 V) character is the physical component source.
    """

    characters = ((record.get("character_certificate") or {}).get("characters") or {})
    wedge2 = characters.get("wedge2_V") or {}
    out: dict[str, dict[str, Any]] = {}
    for cert in wedge2.get("line_certificates", []):
        actual = cert.get("actual") or {}
        if "H2" not in actual:
            continue
        a, b = cert["summand_pair"]
        out[f"5_{a}{b}"] = {
            "label": f"5_{a}{b}",
            "summand_pair": [a, b],
            "charge": {
                "coefficients": [
                    -1 if index in (a, b) else 0 for index in range(5)
                ],
                "label": f"-e{a}-e{b}",
            },
            "cohomology": cert["cohomology"],
            "character": actual["H2"],
            "physical_component_source": "H2(wedge2 V)",
            "serre_dual_inventory_label": f"5_{a}{b}",
        }
    return out


def refined_mass_table(record: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = indexed_inventory(record)
    physical_five = physical_five_component_inventory(record)
    singlets = singlet_multiplicities(record)
    refined = []
    for item in record.get("mass_operator_table") or []:
        fivebar = inventory["fivebar"].get(item.get("fivebar"))
        five = physical_five.get(item.get("five"), inventory["five"].get(item.get("five")))
        serre_five = inventory["five"].get(item.get("five"))
        fivebar_mult = multiplicities(fivebar)
        five_mult = multiplicities(five)
        serre_five_mult = multiplicities(serre_five)
        monomial_supports = []
        for hit in item.get("certified_singlet_monomial_hits_degree_le_2") or []:
            support = product_support(hit.get("labels", []), singlets)
            monomial_supports.append({**hit, "z2_product_support": support})
        invariant_hits = [
            hit
            for hit in monomial_supports
            if hit["z2_product_support"]["has_even_component"]
        ]
        if invariant_hits:
            triplet_support = min(fivebar_mult["+"], five_mult["+"])
            doublet_support = min(fivebar_mult["-"], five_mult["-"])
        else:
            triplet_support = 0
            doublet_support = 0
        if not invariant_hits:
            support_class = "no_invariant_singlet_monomial"
        elif triplet_support > 0 and doublet_support == 0:
            support_class = "triplet_only_character_mass"
        elif triplet_support > 0 and doublet_support > 0:
            support_class = "triplet_and_doublet_character_mass"
        elif triplet_support == 0 and doublet_support > 0:
            support_class = "doublet_only_character_mass"
        else:
            support_class = "no_surviving_component_character_mass"

        refined.append(
            {
                "fivebar": item.get("fivebar"),
                "five": item.get("five"),
                "bilinear_charge": item.get("bilinear_charge"),
                "needed_singlet_charge": item.get("needed_singlet_charge"),
                "original_certified_singlet_monomial_hits_degree_le_2": item.get(
                    "certified_singlet_monomial_hits_degree_le_2"
                )
                or [],
                "invariant_singlet_monomial_hits_degree_le_2": invariant_hits,
                "fivebar_character_multiplicities": fivebar_mult,
                "five_character_multiplicities": five_mult,
                "five_component_character_source": (
                    (five or {}).get("physical_component_source")
                    or "H1(wedge2 V*) fallback"
                ),
                "serre_dual_five_character_multiplicities": serre_five_mult,
                "triplet_pair_support": triplet_support,
                "doublet_pair_support": doublet_support,
                "character_refined_support_class": support_class,
                "triplet_mass_allowed_by_refined_selection_rules": (
                    triplet_support > 0 and bool(invariant_hits)
                ),
                "doublet_mass_allowed_by_refined_selection_rules": (
                    doublet_support > 0 and bool(invariant_hits)
                ),
                "selection_rule_can_lift_triplet_while_protecting_doublet": (
                    support_class == "triplet_only_character_mass"
                ),
            }
        )
    return refined


def proton_allowed_count(record: dict[str, Any]) -> int:
    return sum(
        1
        for item in record.get("proton_decay_operator_table") or []
        if not item.get("forbidden_by_current_selection_rules")
    )


def refined_classification(record: dict[str, Any], mass_table: list[dict[str, Any]]) -> dict[str, Any]:
    proton_allowed = proton_allowed_count(record)
    triplet_only = [
        item
        for item in mass_table
        if item["character_refined_support_class"] == "triplet_only_character_mass"
    ]
    triplet_and_doublet = [
        item
        for item in mass_table
        if item["character_refined_support_class"]
        == "triplet_and_doublet_character_mass"
    ]
    doublet_only = [
        item
        for item in mass_table
        if item["character_refined_support_class"] == "doublet_only_character_mass"
    ]
    no_surviving = [
        item
        for item in mass_table
        if item["character_refined_support_class"]
        == "no_surviving_component_character_mass"
    ]
    has_triplet_support = bool(triplet_only or triplet_and_doublet)
    has_doublet_support = bool(triplet_and_doublet or doublet_only)
    if proton_allowed == 0 and triplet_only and not has_doublet_support:
        return {
            "category": "viable",
            "status": "passes_refined_charge_character_dt_and_proton_filter",
            "reason": (
                "a certified invariant singlet monomial supports a triplet-only "
                "5bar/5 mass entry, no refined mass entry supports the doublet "
                "pair, and all 10*5bar*5bar operators are forbidden by the "
                "current residual charge rules"
            ),
        }
    if proton_allowed > 0 and triplet_only and not has_doublet_support:
        return {
            "category": "phenomenologically obstructed",
            "status": "selective_dt_but_proton_unprotected",
            "reason": "the refined DT gate passes, but a dangerous 10*5bar*5bar operator is still allowed",
        }
    if has_doublet_support:
        return {
            "category": "phenomenologically obstructed",
            "status": "character_refined_doublet_mass_obstruction",
            "reason": "current refined selection rules allow at least one doublet-support mass entry",
        }
    if has_triplet_support:
        return {
            "category": "unresolved",
            "status": "triplet_support_present_but_proton_or_component_status_unresolved",
            "reason": "triplet support exists, but the refined gates do not establish a protected q=1 candidate",
        }
    if no_surviving:
        return {
            "category": "unresolved",
            "status": "charge_neutral_mass_hits_have_no_surviving_components",
            "reason": "charge-neutral mass hits occur only between Wilson-line components absent from the downstairs spectrum",
        }
    return {
        "category": "unresolved",
        "status": "no_character_refined_triplet_mass_operator_found",
        "reason": "no certified invariant degree<=2 singlet monomial supports a surviving triplet mass entry",
    }


def compact_record(
    *,
    source: dict[str, Any],
    weight: int,
    record: dict[str, Any],
    mass_table: list[dict[str, Any]],
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "label": record.get("label"),
        "source": source,
        "weight": weight,
        "old_classification": record.get("classification"),
        "refined_classification": classification,
        "refined_mass_support_classes": dict(
            Counter(item["character_refined_support_class"] for item in mass_table)
        ),
        "proton_allowed_count": proton_allowed_count(record),
    }


def full_candidate_record(
    *,
    source: dict[str, Any],
    weight: int,
    record: dict[str, Any],
    mass_table: list[dict[str, Any]],
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "label": record.get("label"),
        "source": source,
        "weight": weight,
        "cicy_route": record.get("cicy_route", "5259/7914"),
        "matrix": record.get("matrix"),
        "old_classification": record.get("classification"),
        "spectrum_certificate": record.get("spectrum_certificate"),
        "character_certificate": record.get("character_certificate"),
        "charged_matter_inventory": record.get("charged_matter_inventory"),
        "singlet_moduli_inventory": record.get("singlet_moduli_inventory"),
        "refined_mass_operator_table": mass_table,
        "proton_decay_operator_table": record.get("proton_decay_operator_table"),
        "classification": classification,
        "rank_status": {
            "cup_product_rank_computed": False,
            "reason": (
                "This report certifies the refined charge and Z2-character "
                "selection-rule support. Actual singlet-dependent mass-matrix "
                "rank is a stronger cup-product calculation not present in the "
                "current workspace."
            ),
        },
    }


def build_report(windows: int) -> dict[str, Any]:
    rollup_path = REPORTS / (
        f"phenomenology_guided_q1_radius9_broad_windows1_{windows}_rollup.json"
    )
    grammar_verification_path = REPORTS / (
        f"phenomenology_guided_q1_radius9_obstruction_grammar_windows1_{windows}_verification.json"
    )
    negative_path = REPORTS / "cicy5259_lead_phenomenology_dossier.json"
    rollup = load_json(rollup_path)
    grammar_verification = load_json(grammar_verification_path)
    negative = load_json(negative_path)

    compact_records = []
    viable_records = []
    weighted_classes: Counter[str] = Counter()
    unweighted_classes: Counter[str] = Counter()
    old_to_refined: Counter[str] = Counter()
    represented_weight = 0
    explicit_viable_count = 0
    representative_viable_weight = 0

    for source, weight, record in source_records(windows):
        represented_weight += weight
        mass_table = refined_mass_table(record)
        classification = refined_classification(record, mass_table)
        class_key = classification["status"]
        weighted_classes[class_key] += weight
        unweighted_classes[class_key] += 1
        old_status = (record.get("classification") or {}).get("status")
        old_to_refined[f"{old_status} -> {class_key}"] += weight
        compact_records.append(
            compact_record(
                source=source,
                weight=weight,
                record=record,
                mass_table=mass_table,
                classification=classification,
            )
        )
        if classification["category"] == "viable":
            representative_viable_weight += weight
            if source["kind"] != "large_branch_representative":
                explicit_viable_count += 1
            viable_records.append(
                full_candidate_record(
                    source=source,
                    weight=weight,
                    record=record,
                    mass_table=mass_table,
                    classification=classification,
                )
            )

    best_candidate = None
    if viable_records:
        best_candidate = sorted(
            viable_records,
            key=lambda item: (
                item["source"]["kind"] == "large_branch_representative",
                item["weight"],
                item["source"]["window"],
                item["label"],
            ),
        )[0]

    summary = rollup["summary"]
    gates = {
        "imports_verified_rollup": gate(
            summary.get("all_verified") and summary.get("windows_closed") == windows,
            str(rollup_path),
            "character-refined DT report starts from the verified radius-9 rollup",
        ),
        "imports_verified_obstruction_grammar": gate(
            grammar_verification.get("all_gates_pass"),
            str(grammar_verification_path),
            "character-refined DT report is synchronized with the verified obstruction grammar",
        ),
        "candidate_weight_matches_rollup": gate(
            represented_weight == summary.get("adjusted_desired_q1_candidates"),
            "radius-9 q=1 source records",
            "all adjusted desired q=1 candidates are represented exactly once by the refined scan",
        ),
        "negative_control_still_rejected": gate(
            negative["classification"]["category"] == "phenomenologically obstructed"
            and "10*5bar*5bar" in negative["classification"]["reason"],
            str(negative_path),
            "the original 5259/7914 lead remains the phenomenologically obstructed negative control",
        ),
        "refined_viable_candidate_found": gate(
            representative_viable_weight > 0 and explicit_viable_count > 0,
            "character-refined mass/proton scan",
            "at least one explicit q=1 candidate passes refined DT and proton gates",
        ),
    }
    if best_candidate:
        best_mass = best_candidate["refined_mass_operator_table"]
        gates["best_candidate_has_required_certificates"] = gate(
            best_candidate["spectrum_certificate"] is not None
            and best_candidate["character_certificate"] is not None
            and best_candidate["refined_mass_operator_table"] is not None
            and best_candidate["proton_decay_operator_table"] is not None,
            best_candidate["source"]["path"],
            "best refined candidate emits spectrum, character, mass, proton, and classification sections",
        )
        gates["best_candidate_passes_refined_dt_gate"] = gate(
            any(
                item["character_refined_support_class"] == "triplet_only_character_mass"
                for item in best_mass
            )
            and not any(
                item["doublet_mass_allowed_by_refined_selection_rules"]
                for item in best_mass
            ),
            best_candidate["label"],
            "best candidate has triplet-only mass support and no doublet-support mass entry",
        )
        gates["best_candidate_passes_proton_gate"] = gate(
            proton_allowed_count(best_candidate) == 0,
            best_candidate["label"],
            "all dangerous 10*5bar*5bar operators are forbidden for the best refined candidate",
        )

    return {
        "title": f"Radius-9 Character-Refined DT Report Through Window {windows}",
        "status": (
            f"radius9_character_refined_dt_windows1_{windows}_candidate_found"
            if representative_viable_weight
            else f"radius9_character_refined_dt_windows1_{windows}_no_candidate"
        ),
        "scope": (
            "refine the radius-9 q=1 obstruction filter by applying Wilson-line "
            "component characters to 5bar/5 mass entries"
        ),
        "source_rollup": str(rollup_path),
        "summary": {
            "windows_closed": windows,
            "represented_q1_weight": represented_weight,
            "unweighted_records_scanned": len(compact_records),
            "refined_viable_candidate_weight": representative_viable_weight,
            "explicit_refined_viable_candidate_count": explicit_viable_count,
            "weighted_refined_statuses": dict(sorted(weighted_classes.items())),
            "unweighted_refined_statuses": dict(sorted(unweighted_classes.items())),
            "old_to_refined_status_transitions": dict(sorted(old_to_refined.items())),
        },
        "refined_filter_rule": {
            "triplet_support": "5bar and 5 entries both have surviving + Wilson-line components",
            "doublet_support": "5bar and 5 entries both have surviving - Wilson-line components",
            "singlet_support": "at least one certified degree<=2 singlet monomial has an even Z2 component",
            "viable_current_filter": (
                "proton protected, at least one triplet-only mass entry, and no "
                "doublet-support mass entry"
            ),
        },
        "best_candidate": best_candidate,
        "refined_viable_candidate_records": viable_records,
        "all_refined_candidate_classifications": compact_records,
        "negative_control": {
            "source": str(negative_path),
            "classification": negative["classification"],
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
    lines.extend(["", "## Refined Rule", ""])
    for key, value in report["refined_filter_rule"].items():
        lines.append(f"- {key}: `{value}`")
    best = report["best_candidate"]
    lines.extend(["", "## Best Candidate", ""])
    if best is None:
        lines.append("No refined viable candidate found.")
    else:
        lines.extend(
            [
                f"- label: `{best['label']}`",
                f"- source: `{best['source']}`",
                f"- old classification: `{best['old_classification']}`",
                f"- refined classification: `{best['classification']}`",
                f"- spectrum: `{best['spectrum_certificate']['vectorlike_prediction']}`",
                f"- proton allowed count: `{proton_allowed_count(best)}`",
            ]
        )
        triplet_hits = [
            item
            for item in best["refined_mass_operator_table"]
            if item["character_refined_support_class"] == "triplet_only_character_mass"
        ]
        lines.append(f"- triplet-only mass hits: `{triplet_hits}`")
    lines.extend(["", "## Gates", ""])
    for key, item in report["gates"].items():
        lines.append(f"- {key}: `{item['pass']}` - {item['note']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windows", type=int, default=45)
    parser.add_argument(
        "--json-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"
        ),
    )
    parser.add_argument(
        "--md-out",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.md"
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
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
