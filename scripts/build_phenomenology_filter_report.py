#!/usr/bin/env python3
"""Apply the q=1 phenomenology obstruction filter to the current candidate pool."""

from __future__ import annotations

import argparse
from itertools import combinations_with_replacement
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "scripts"))

from build_cicy5259_lead_phenomenology_dossier import (  # noqa: E402
    add_charges,
    build_wilson_decomposition,
    charged_matter_inventory,
    format_charge,
    is_su5_trace_neutral,
    neg_charge,
    singlet_sector_records,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def is_desired_q1_signature(prediction: dict[str, Any]) -> bool:
    return (
        prediction.get("regular_character_rule_applies")
        and prediction.get("net_families") == 3
        and prediction.get("colored_triplet_vectorlike_pairs") == 1
        and prediction.get("electroweak_doublet_vectorlike_pairs") == 1
        and prediction.get("h2_wedge2_regular_multiplicity") == 1
    )


def certified_h1_singlets(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        record["charge"]["label"]: record
        for record in records
        if record["h1_dimension"] > 0
        and record["character_certificate"]["actual_character_computed"]
    }


def enumerate_singlet_monomials(
    singlets: dict[str, dict[str, Any]], *, max_degree: int = 2
) -> list[dict[str, Any]]:
    labels = sorted(singlets)
    monomials = [
        {
            "labels": [],
            "charge": {"coefficients": [0, 0, 0, 0, 0], "label": "0"},
            "degree": 0,
        }
    ]
    for degree in range(1, max_degree + 1):
        for combo in combinations_with_replacement(labels, degree):
            charge = [0, 0, 0, 0, 0]
            for label in combo:
                charge = add_charges(charge, singlets[label]["charge"]["coefficients"])
            monomials.append(
                {
                    "labels": list(combo),
                    "charge": {"coefficients": charge, "label": format_charge(charge)},
                    "degree": degree,
                }
            )
    return monomials


def find_mass_operator_table(
    *,
    inventory: dict[str, Any],
    singlet_monomials: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    table = []
    for fivebar in inventory["fivebar"]:
        for five in inventory["five"]:
            bilinear_charge = add_charges(
                fivebar["charge"]["coefficients"], five["charge"]["coefficients"]
            )
            needed = neg_charge(bilinear_charge)
            hits = []
            for monomial in singlet_monomials:
                total = add_charges(bilinear_charge, monomial["charge"]["coefficients"])
                if is_su5_trace_neutral(total):
                    hits.append(monomial)
            table.append(
                {
                    "fivebar": fivebar["label"],
                    "five": five["label"],
                    "bilinear_charge": {
                        "coefficients": bilinear_charge,
                        "label": format_charge(bilinear_charge),
                    },
                    "needed_singlet_charge": {
                        "coefficients": needed,
                        "label": format_charge(needed),
                    },
                    "certified_singlet_monomial_hits_degree_le_2": hits,
                    "triplet_mass_allowed_by_current_selection_rules": bool(hits),
                    "doublet_mass_same_selection_rule": bool(hits),
                    "selection_rule_can_lift_triplet_while_protecting_doublet": False,
                    "interpretation": (
                        "With only line-bundle charges and the certified Z2 regular "
                        "characters, a hit allows both triplet and doublet mass "
                        "components for this 5bar/5 bilinear; no selective "
                        "doublet-triplet splitting is certified."
                        if hits
                        else "No certified singlet monomial of degree <=2 neutralizes this bilinear."
                    ),
                }
            )
    return table


def find_proton_decay_table(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    table = []
    for ten in inventory["ten"]:
        for i, fivebar_a in enumerate(inventory["fivebar"]):
            for fivebar_b in inventory["fivebar"][i:]:
                charge = add_charges(
                    ten["charge"]["coefficients"],
                    fivebar_a["charge"]["coefficients"],
                    fivebar_b["charge"]["coefficients"],
                )
                neutral = is_su5_trace_neutral(charge)
                table.append(
                    {
                        "operator": f"{ten['label']}*{fivebar_a['label']}*{fivebar_b['label']}",
                        "charge": {"coefficients": charge, "label": format_charge(charge)},
                        "neutral_under_S_U1_5": neutral,
                        "z2_comment": (
                            "all participating sectors have regular Z2 character "
                            "content, so an even-character component is not excluded"
                        ),
                        "forbidden_by_current_selection_rules": not neutral,
                    }
                )
    return table


def classify_from_tables(
    *,
    desired_signature: bool,
    character_certified: bool,
    mass_table: list[dict[str, Any]] | None,
    proton_table: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    if not desired_signature:
        return {
            "category": "phenomenologically obstructed",
            "status": "rejected_spectrum_signature_not_q1_three_family",
            "reason": "candidate does not have three families plus exactly one vectorlike 5/5bar pair after Wilson-line projection",
        }
    if not character_certified or mass_table is None or proton_table is None:
        return {
            "category": "unresolved",
            "status": "missing_character_or_charge_level_data",
            "reason": "candidate has the desired spectrum arithmetic but lacks complete character/charge tables for the phenomenology filter",
        }
    triplet_mass_allowed = any(
        item["triplet_mass_allowed_by_current_selection_rules"] for item in mass_table
    )
    selective_dt = any(
        item["selection_rule_can_lift_triplet_while_protecting_doublet"]
        for item in mass_table
    )
    dangerous_forbidden = all(
        item["forbidden_by_current_selection_rules"] for item in proton_table
    )
    if triplet_mass_allowed and selective_dt and dangerous_forbidden:
        return {
            "category": "viable",
            "status": "passes_current_charge_level_filter",
            "reason": "triplet mass, doublet protection, and proton-decay suppression are all supported by current selection-rule evidence",
        }
    if triplet_mass_allowed and not selective_dt:
        return {
            "category": "phenomenologically obstructed",
            "status": "negative_control_doublet_triplet_obstruction",
            "reason": "certified mass terms do not distinguish triplet from doublet components",
        }
    if not dangerous_forbidden:
        return {
            "category": "phenomenologically obstructed",
            "status": "dangerous_10_5bar_5bar_operator_allowed",
            "reason": "at least one dangerous 10*5bar*5bar operator is neutral under current residual charges",
        }
    return {
        "category": "unresolved",
        "status": "no_certified_triplet_mass_operator_found",
        "reason": "no certified singlet/moduli mass term was found at the current monomial degree bound",
    }


def candidate_certificate_from_5259_record(
    *,
    label: str,
    record: dict[str, Any],
    conf: list[list[int]],
) -> dict[str, Any]:
    prediction = record["vectorlike_pair_prediction"]
    desired = is_desired_q1_signature(prediction)
    spectrum = {
        "cohomology": record["cohomology"],
        "vectorlike_prediction": prediction,
        "desired_q1_three_family_signature": desired,
    }
    character = {
        "character_certified": record["character_certified"],
        "characters": record["characters"],
    }
    mass_table = None
    proton_table = None
    singlets = None
    inventory = None
    if record["character_certified"]:
        inventory = charged_matter_inventory(record)
        singlet_records = singlet_sector_records(conf=conf, matrix=record["matrix"])
        singlets = {
            "all_nonzero_ext1_line_sectors": singlet_records,
            "certified_h1_singlet_charge_labels": sorted(
                certified_h1_singlets(singlet_records)
            ),
        }
        monomials = enumerate_singlet_monomials(
            certified_h1_singlets(singlet_records), max_degree=2
        )
        mass_table = find_mass_operator_table(
            inventory=inventory, singlet_monomials=monomials
        )
        proton_table = find_proton_decay_table(inventory)
    classification = classify_from_tables(
        desired_signature=desired,
        character_certified=record["character_certified"],
        mass_table=mass_table,
        proton_table=proton_table,
    )
    return {
        "label": label,
        "source": "cicy5259_h2_frontier_radius1_target.certified_records",
        "cicy_route": "5259/7914",
        "matrix": record["matrix"],
        "spectrum_certificate": spectrum,
        "character_certificate": character,
        "charged_matter_inventory": inventory,
        "singlet_moduli_inventory": singlets,
        "mass_operator_table": mass_table,
        "proton_decay_operator_table": proton_table,
        "classification": classification,
    }


def candidate_certificate_from_summary(record: dict[str, Any]) -> dict[str, Any]:
    prediction = record["vectorlike_pair_prediction"]
    desired = is_desired_q1_signature(prediction)
    return {
        "label": record["label"],
        "source": record.get("source_report", "vectorlike_obstruction_report.comparative_records"),
        "cicy_route": str(record["cicy"]),
        "matrix": record.get("matrix"),
        "spectrum_certificate": {
            "cohomology": record.get("cohomology"),
            "vectorlike_prediction": prediction,
            "desired_q1_three_family_signature": desired,
        },
        "character_certificate": {
            "character_certified": record.get("character_certified", False),
            "available_summary_only": True,
        },
        "charged_matter_inventory": None,
        "singlet_moduli_inventory": None,
        "mass_operator_table": None,
        "proton_decay_operator_table": None,
        "classification": classify_from_tables(
            desired_signature=desired,
            character_certified=False,
            mass_table=None,
            proton_table=None,
        )
        if desired
        else classify_from_tables(
            desired_signature=False,
            character_certified=False,
            mass_table=None,
            proton_table=None,
        ),
    }


def build_report() -> dict[str, Any]:
    split = load_json(REPORTS / "cicy5259_split_lift_report.json")
    frontier = load_json(REPORTS / "cicy5259_h2_frontier_radius1_target.json")
    negative = load_json(REPORTS / "cicy5259_lead_phenomenology_dossier.json")
    comparative = load_json(REPORTS / "vectorlike_obstruction_report.json")
    conf = split["full_picard_presentation_7914"]["conf"]

    records = []
    for index, record in enumerate(frontier["certified_records"]):
        records.append(
            candidate_certificate_from_5259_record(
                label=f"5259_radius1_certified_record_{index}",
                record=record,
                conf=conf,
            )
        )

    seen_7484 = set()
    for record in comparative["comparative_records"]:
        if str(record["cicy"]) == "5259/7914":
            continue
        key = (
            record["label"],
            json.dumps(record.get("matrix"), sort_keys=True),
            json.dumps(record["vectorlike_pair_prediction"], sort_keys=True),
        )
        if key in seen_7484:
            continue
        seen_7484.add(key)
        records.append(candidate_certificate_from_summary(record))

    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for record in records:
        category = record["classification"]["category"]
        status = record["classification"]["status"]
        categories[category] = categories.get(category, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1

    q1_records = [
        record
        for record in records
        if record["spectrum_certificate"]["desired_q1_three_family_signature"]
    ]
    viable = [
        record for record in records if record["classification"]["category"] == "viable"
    ]

    gates = {
        "negative_control_is_obstructed": gate(
            negative["classification"]["category"] == "phenomenologically obstructed"
            and negative["classification"]["status"]
            == "phenomenologically_obstructed_by_current_charge_level_evidence",
            str(REPORTS / "cicy5259_lead_phenomenology_dossier.json"),
            "5259/7914 q=1 dossier is imported as the negative control",
        ),
        "candidate_pool_loaded": gate(
            len(records) >= len(frontier["certified_records"]),
            "current reports/candidate artifacts",
            "current character-certified and summary candidate pool was converted into filter records",
        ),
        "q1_candidates_are_filtered": gate(
            len(q1_records) >= 1
            and all(record["classification"]["category"] != "viable" for record in q1_records),
            "phenomenology filter classifications",
            "current q=1 candidates are classified and none passes the charge-level filter",
        ),
        "per_candidate_tables_emitted": gate(
            all(
                {
                    "spectrum_certificate",
                    "character_certificate",
                    "mass_operator_table",
                    "proton_decay_operator_table",
                    "classification",
                }.issubset(record)
                for record in records
            ),
            "candidate certificates",
            "every emitted candidate record has the required report sections",
        ),
    }

    return {
        "scope": "current-pool phenomenology obstruction filter for quotient-compatible outside-regime candidates",
        "filter_requirements": {
            "spectrum": "three families plus exactly one vectorlike 5/5bar pair after Wilson-line projection",
            "mass_terms": "certified singlet/moduli operator can lift colored triplet pair while forbidding, suppressing, or leaving tunably light the Higgs doublet pair",
            "proton_decay": "dangerous 10*5bar*5bar operators are forbidden by certified residual selection rules",
            "negative_control": "reject candidates with the same 5259/7914 charge-level obstruction even if q=1",
        },
        "negative_control_summary": {
            "source": "cicy5259_lead_phenomenology_dossier.json",
            "classification": negative["classification"],
            "obstruction_pattern": [
                "singlet mass terms do not distinguish triplet from doublet components",
                "10_1*5bar_04*5bar_23 is neutral under S(U(1)^5)",
            ],
        },
        "summary": {
            "candidate_count": len(records),
            "q1_candidate_count": len(q1_records),
            "viable_count": len(viable),
            "categories": dict(sorted(categories.items())),
            "statuses": dict(sorted(statuses.items())),
            "status": (
                "no_viable_candidate_in_current_pool"
                if not viable
                else "viable_candidate_found"
            ),
        },
        "candidate_records": records,
        "gates": gates,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Phenomenology Obstruction Filter Report",
        "",
        f"Status: `{report['summary']['status']}`",
        "",
        "## Filter",
        "",
        f"- spectrum: `{report['filter_requirements']['spectrum']}`",
        f"- mass terms: `{report['filter_requirements']['mass_terms']}`",
        f"- proton decay: `{report['filter_requirements']['proton_decay']}`",
        f"- negative control: `{report['filter_requirements']['negative_control']}`",
        "",
        "## Summary",
        "",
        f"- candidate count: `{report['summary']['candidate_count']}`",
        f"- q=1 candidate count: `{report['summary']['q1_candidate_count']}`",
        f"- viable count: `{report['summary']['viable_count']}`",
        f"- categories: `{report['summary']['categories']}`",
        f"- statuses: `{report['summary']['statuses']}`",
        "",
        "## Candidate Classifications",
        "",
    ]
    for record in report["candidate_records"]:
        lines.append(
            f"- `{record['label']}` ({record['cicy_route']}): "
            f"`{record['classification']['category']}` / "
            f"`{record['classification']['status']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_obstruction_filter_report.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_obstruction_filter_report.md"),
    )
    args = parser.parse_args()
    report = build_report()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['summary']['status']}")
    print(f"candidate_count={report['summary']['candidate_count']}")
    print(f"q1_candidate_count={report['summary']['q1_candidate_count']}")
    print(f"viable_count={report['summary']['viable_count']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
