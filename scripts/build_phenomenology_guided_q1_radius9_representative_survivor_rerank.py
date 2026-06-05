#!/usr/bin/env python3
"""Rerank refined q=1 survivors by representative-level realizability."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/codex-mpl-cache")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_phenomenology_guided_q1_radius2_e1_sign_prototype import (  # noqa: E402
    ambient_bundle_for_origin,
    entry_basis_signs,
    rep_from_signs,
)
from build_phenomenology_guided_q1_radius2_equivariant_first_page_probe import (  # noqa: E402
    equivariant_rank_map,
    rank_split,
)
from build_vectorlike_obstruction_report import load_5259_action_context  # noqa: E402
from string_theory.cohomology import (  # noqa: E402
    cohomology_record,
    ensure_pycicy_compat,
    make_pycicy,
    pycicy_config,
)

NEGATIVE_CONTROL_LABEL = "radius6_broad_adjacency_filtered_4_branch_18"
NEGATIVE_CONTROL_OPERATOR = "5bar_02*5_24"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def parse_pair(label: str) -> list[int]:
    return [int(char) for char in label.split("_", 1)[1]]


def rep_zero() -> dict[str, Any]:
    return {
        "dimension": 0,
        "nonidentity_trace": 0,
        "multiplicities": {"+": 0, "-": 0},
        "regular_multiplicity": 0,
    }


def rep_from_counts(plus: int, minus: int) -> dict[str, Any]:
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def add_rep(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    plus = a["multiplicities"]["+"] + b["multiplicities"]["+"]
    minus = a["multiplicities"]["-"] + b["multiplicities"]["-"]
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def sub_rank_from_rep(rep: dict[str, Any], split: dict[str, Any]) -> dict[str, Any]:
    plus = rep["multiplicities"]["+"] - split["rank_plus"]
    minus = rep["multiplicities"]["-"] - split["rank_minus"]
    return {
        "dimension": plus + minus,
        "nonidentity_trace": plus - minus,
        "multiplicities": {"+": plus, "-": minus},
        "regular_multiplicity": plus if plus == minus else None,
    }


def compact_entry_records(
    *,
    manifold: Any,
    conf: list[list[int]],
    line_bundle: list[int],
    coordinate_signs_by_block: list[list[int]],
    equation_signs: list[int],
) -> dict[str, Any]:
    e1, origin = manifold.Leray(manifold._line_to_BBW(line_bundle))
    entries = []
    for k, row in enumerate(e1):
        for j, value in enumerate(row):
            if value == 0:
                continue
            bracket_entries = [[int(x) for x in item] for item in value]
            origins = [list(item) for item in origin[k][j]]
            signs = entry_basis_signs(
                manifold=manifold,
                conf=conf,
                line_bundle=line_bundle,
                bracket_entries=bracket_entries,
                origins=origins,
                coordinate_signs_by_block=coordinate_signs_by_block,
                equation_signs=equation_signs,
            )
            entries.append(
                {
                    "k": k,
                    "j": j,
                    "total_degree": j - k,
                    "bracket_entries": bracket_entries,
                    "origins": origins,
                    "ambient_bundles": [
                        ambient_bundle_for_origin(
                            line_bundle=line_bundle,
                            conf=conf,
                            origin=item,
                        )
                        for item in origins
                    ],
                    "basis_signs": signs,
                    "basis_sign_representation": rep_from_signs(signs),
                }
            )
    return {
        "line_bundle": line_bundle,
        "cohomology": cohomology_record(conf, line_bundle)["cohomology"],
        "entries": entries,
    }


def aggregate_by_total_degree(line_audit: dict[str, Any]) -> dict[int, dict[str, Any]]:
    signs_by_degree: dict[int, list[int]] = defaultdict(list)
    for entry in line_audit["entries"]:
        signs_by_degree[entry["total_degree"]].extend(entry["basis_signs"])
    return {
        degree: rep_from_signs(signs)
        for degree, signs in sorted(signs_by_degree.items())
    }


def flatten_entries(entries: list[dict[str, Any]]) -> tuple[list[list[int]], list[list[int]], list[int]]:
    brackets: list[list[int]] = []
    origins: list[list[int]] = []
    signs: list[int] = []
    for entry in entries:
        brackets.extend(entry["bracket_entries"])
        origins.extend(entry["origins"])
        signs.extend(entry["basis_signs"])
    return brackets, origins, signs


def compute_map_split(
    *,
    manifold: Any,
    context: dict[str, Any],
    source_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    source_signs = [sign for entry in source_entries for sign in entry["basis_signs"]]
    target_signs = [sign for entry in target_entries for sign in entry["basis_signs"]]
    source_dims = [len(entry["basis_signs"]) for entry in source_entries]
    target_dims = [len(entry["basis_signs"]) for entry in target_entries]
    source_offsets = np.cumsum([0] + source_dims[:-1]).tolist()
    target_offsets = np.cumsum([0] + target_dims[:-1]).tolist()
    matrix = np.zeros((sum(target_dims), sum(source_dims)), dtype=np.int64)

    # The Koszul d1 map preserves the ambient cohomology degree j and sends
    # table position (k,j) to (k-1,j).  The previous flattened total-degree
    # implementation allowed cross-j origin matches, which are not d1 blocks.
    for source_index, source_entry in enumerate(source_entries):
        candidate_indexes = [
            target_index
            for target_index, target_entry in enumerate(target_entries)
            if target_entry["j"] == source_entry["j"]
            and target_entry["k"] == source_entry["k"] - 1
        ]
        if not candidate_indexes:
            continue
        source_brackets, source_origins, _ = flatten_entries([source_entry])
        candidate_entries = [target_entries[index] for index in candidate_indexes]
        target_brackets, target_origins, _ = flatten_entries(candidate_entries)
        block = equivariant_rank_map(
            manifold=manifold,
            source_entries=source_brackets,
            target_entries=target_brackets,
            source_origins=source_origins,
            target_origins=target_origins,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        )
        row_start_in_block = 0
        for target_index in candidate_indexes:
            rows = target_dims[target_index]
            matrix[
                target_offsets[target_index] : target_offsets[target_index] + rows,
                source_offsets[source_index] : source_offsets[source_index]
                + source_dims[source_index],
            ] += block[row_start_in_block : row_start_in_block + rows, :]
            row_start_in_block += rows
    split = rank_split(matrix=matrix, source_signs=source_signs, target_signs=target_signs)
    return {
        "matrix_shape": list(matrix.shape),
        "rank_split": split,
    }


def try_compute_map_split(
    *,
    manifold: Any,
    context: dict[str, Any],
    source_entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    try:
        return (
            compute_map_split(
                manifold=manifold,
                context=context,
                source_entries=source_entries,
                target_entries=target_entries,
            ),
            None,
        )
    except Exception as exc:  # noqa: BLE001 - preserve broad verifier evidence.
        return (
            None,
            {
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )


def required_image_ranks_for_cokernel(
    *, target_rep: dict[str, Any], desired_cokernel: dict[str, Any]
) -> dict[str, int]:
    return {
        "+": target_rep["multiplicities"]["+"] - desired_cokernel["multiplicities"]["+"],
        "-": target_rep["multiplicities"]["-"] - desired_cokernel["multiplicities"]["-"],
    }


def required_image_ranks_for_kernel(
    *, source_rep: dict[str, Any], desired_kernel: dict[str, Any]
) -> dict[str, int]:
    return {
        "+": source_rep["multiplicities"]["+"] - desired_kernel["multiplicities"]["+"],
        "-": source_rep["multiplicities"]["-"] - desired_kernel["multiplicities"]["-"],
    }


def ranks_feasible(
    *,
    required: dict[str, int],
    source_rep: dict[str, Any],
    target_rep: dict[str, Any],
) -> bool:
    return all(
        0 <= required[sign] <= min(
            source_rep["multiplicities"][sign],
            target_rep["multiplicities"][sign],
        )
        for sign in ("+", "-")
    )


def compute_e2_resolution(
    *,
    manifold: Any,
    context: dict[str, Any],
    line_audit: dict[str, Any],
) -> dict[str, Any]:
    entries = line_audit["entries"]
    entry_by_position = {(entry["k"], entry["j"]): entry for entry in entries}
    rank_splits: dict[tuple[tuple[int, int], tuple[int, int]], dict[str, Any]] = {}
    map_errors = []
    for source in entries:
        target = entry_by_position.get((source["k"] - 1, source["j"]))
        if target is None:
            continue
        split, error = try_compute_map_split(
            manifold=manifold,
            context=context,
            source_entries=[source],
            target_entries=[target],
        )
        if error is not None:
            map_errors.append(
                {
                    "source": [source["k"], source["j"]],
                    "target": [target["k"], target["j"]],
                    "error": error,
                }
            )
            continue
        assert split is not None
        rank_splits[((source["k"], source["j"]), (target["k"], target["j"]))] = split

    if map_errors:
        return {
            "status": "e2_unresolved",
            "reason": "equivariant E2 d1 map construction failed",
            "map_errors": map_errors,
            "actual": {},
        }

    actual: dict[str, Any] = {}
    e2_entries = []
    negative_residuals = []
    cross_eigen_nonzero_entries = 0
    for split in rank_splits.values():
        cross_eigen_nonzero_entries += split["rank_split"]["cross_eigen_nonzero_entries"]

    for entry in entries:
        outgoing = rank_splits.get(((entry["k"], entry["j"]), (entry["k"] - 1, entry["j"])))
        incoming = rank_splits.get(((entry["k"] + 1, entry["j"]), (entry["k"], entry["j"])))
        plus = entry["basis_signs"].count(1)
        minus = entry["basis_signs"].count(-1)
        if outgoing is not None:
            plus -= outgoing["rank_split"]["rank_plus"]
            minus -= outgoing["rank_split"]["rank_minus"]
        if incoming is not None:
            plus -= incoming["rank_split"]["rank_plus"]
            minus -= incoming["rank_split"]["rank_minus"]
        if plus < 0 or minus < 0:
            negative_residuals.append(
                {
                    "entry": [entry["k"], entry["j"]],
                    "plus": plus,
                    "minus": minus,
                }
            )
            continue
        if plus + minus == 0:
            continue
        cohomology_key = f"H{entry['total_degree']}"
        rep = rep_from_counts(plus, minus)
        actual[cohomology_key] = add_rep(actual.get(cohomology_key, rep_zero()), rep)
        e2_entries.append(
            {
                "entry": [entry["k"], entry["j"]],
                "total_degree": entry["total_degree"],
                "representation": rep,
            }
        )

    if negative_residuals:
        return {
            "status": "e2_unresolved",
            "reason": "equivariant E2 rank subtraction produced negative residual dimensions",
            "negative_residuals": negative_residuals,
            "actual": actual,
        }

    cohomology = line_audit["cohomology"]
    e2_dimensions = [0 for _ in cohomology]
    for key, rep in actual.items():
        degree = int(key[1:])
        if degree < len(e2_dimensions):
            e2_dimensions[degree] = rep["dimension"]
    final_by_dimension = e2_dimensions == cohomology
    return {
        "status": "e2_final_by_dimension" if final_by_dimension else "e2_unresolved",
        "reason": (
            "equivariant first-page E2 dimensions match pyCICY cohomology dimensions"
            if final_by_dimension
            else "equivariant first-page E2 dimensions do not match pyCICY cohomology dimensions"
        ),
        "actual": actual,
        "e2_entries": e2_entries,
        "rank_splits": [
            {
                "source": list(source),
                "target": list(target),
                **split["rank_split"],
            }
            for (source, target), split in sorted(rank_splits.items())
        ],
        "cross_eigen_nonzero_entries": cross_eigen_nonzero_entries,
        "e2_dimensions": e2_dimensions,
        "cohomology_dimensions": cohomology,
        "final_by_dimension": final_by_dimension,
    }


def audit_character_leg(
    *,
    manifold: Any,
    conf: list[list[int]],
    context: dict[str, Any],
    line_cache: dict[tuple[int, ...], dict[str, Any]],
    role: str,
    certificate: dict[str, Any],
    cohomology_key: str,
) -> dict[str, Any]:
    q = int(cohomology_key[1:])
    branch_actual = certificate.get("actual", {}).get(cohomology_key)
    line = certificate["line_bundle"]
    line_key = tuple(line)
    if line_key not in line_cache:
        line_cache[line_key] = compact_entry_records(
            manifold=manifold,
            conf=conf,
            line_bundle=line,
            coordinate_signs_by_block=context["coordinate_signs_by_block_7914"],
            equation_signs=context["equation_signs_7914"],
        )
    line_audit = line_cache[line_key]
    reps_by_degree = aggregate_by_total_degree(line_audit)
    degree_keys = sorted(reps_by_degree)
    base = {
        "role": role,
        "line_bundle": line,
        "cohomology_key": cohomology_key,
        "cohomology": certificate["cohomology"],
        "branch_method": certificate.get("method"),
        "branch_actual": branch_actual,
        "e1_total_degree_representations": {
            str(degree): rep for degree, rep in reps_by_degree.items()
        },
        "e1_entry_positions": [
            {
                "k": entry["k"],
                "j": entry["j"],
                "total_degree": entry["total_degree"],
                "dimension": entry["basis_sign_representation"]["dimension"],
                "multiplicities": entry["basis_sign_representation"]["multiplicities"],
                "origins": entry["origins"],
                "ambient_bundles": entry["ambient_bundles"],
            }
            for entry in line_audit["entries"]
        ],
    }
    if branch_actual is None:
        return {
            **base,
            "status": "representative_unresolved",
            "reason": "branch certificate has no actual character for the requested cohomology degree",
            "computed_actual": None,
        }
    if certificate["cohomology"][q] != branch_actual["dimension"]:
        return {
            **base,
            "status": "representative_obstructed",
            "reason": "branch actual dimension does not match pyCICY cohomology dimension",
            "computed_actual": None,
        }

    entries_by_degree: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for entry in line_audit["entries"]:
        entries_by_degree[entry["total_degree"]].append(entry)

    if degree_keys == [q]:
        computed = reps_by_degree[q]
        return {
            **base,
            "status": (
                "representative_compatible"
                if computed == branch_actual
                else "representative_obstructed"
            ),
            "reason": (
                "single total-degree E1 source equals the cohomology dimension"
                if computed == branch_actual
                else "single total-degree E1 source character disagrees with branch actual"
            ),
            "computed_actual": computed,
            "representative_method": "single_total_degree",
        }

    if degree_keys == [q - 1, q]:
        source_rep = reps_by_degree[q - 1]
        target_rep = reps_by_degree[q]
        required = required_image_ranks_for_cokernel(
            target_rep=target_rep,
            desired_cokernel=branch_actual,
        )
        feasible = ranks_feasible(
            required=required,
            source_rep=source_rep,
            target_rep=target_rep,
        )
        if not feasible:
            split, map_error = try_compute_map_split(
                manifold=manifold,
                context=context,
                source_entries=entries_by_degree[q - 1],
                target_entries=entries_by_degree[q],
            )
            computed = (
                None
                if split is None
                else sub_rank_from_rep(target_rep, split["rank_split"])
            )
        else:
            split, map_error = try_compute_map_split(
                manifold=manifold,
                context=context,
                source_entries=entries_by_degree[q - 1],
                target_entries=entries_by_degree[q],
            )
            computed = (
                None
                if split is None
                else sub_rank_from_rep(target_rep, split["rank_split"])
            )
        return {
            **base,
            "status": (
                "representative_obstructed"
                if not feasible
                else (
                    "representative_unresolved"
                    if map_error is not None
                    else (
                        "representative_compatible"
                        if computed == branch_actual
                        else "representative_obstructed"
                    )
                )
            ),
            "reason": (
                "branch cokernel character requires an impossible image-rank split"
                if not feasible
                else (
                    "equivariant first-page cokernel map construction failed"
                    if map_error is not None
                    else (
                        "explicit equivariant first-page cokernel character matches branch actual"
                        if computed == branch_actual
                        else "explicit equivariant first-page cokernel character disagrees with branch actual"
                    )
                )
            ),
            "computed_actual": computed,
            "representative_method": "first_page_cokernel",
            "source_representation": source_rep,
            "target_representation": target_rep,
            "required_image_ranks_for_branch": required,
            "required_image_ranks_feasible": feasible,
            "map_split": split,
            "map_error": map_error,
        }

    if degree_keys == [q, q + 1]:
        source_rep = reps_by_degree[q]
        target_rep = reps_by_degree[q + 1]
        required = required_image_ranks_for_kernel(
            source_rep=source_rep,
            desired_kernel=branch_actual,
        )
        feasible = ranks_feasible(
            required=required,
            source_rep=source_rep,
            target_rep=target_rep,
        )
        if not feasible:
            split, map_error = try_compute_map_split(
                manifold=manifold,
                context=context,
                source_entries=entries_by_degree[q],
                target_entries=entries_by_degree[q + 1],
            )
            computed = (
                None
                if split is None
                else sub_rank_from_rep(source_rep, split["rank_split"])
            )
        else:
            split, map_error = try_compute_map_split(
                manifold=manifold,
                context=context,
                source_entries=entries_by_degree[q],
                target_entries=entries_by_degree[q + 1],
            )
            computed = (
                None
                if split is None
                else sub_rank_from_rep(source_rep, split["rank_split"])
            )
        return {
            **base,
            "status": (
                "representative_obstructed"
                if not feasible
                else (
                    "representative_unresolved"
                    if map_error is not None
                    else (
                        "representative_compatible"
                        if computed == branch_actual
                        else "representative_obstructed"
                    )
                )
            ),
            "reason": (
                "branch kernel character requires an impossible image-rank split"
                if not feasible
                else (
                    "equivariant first-page kernel map construction failed"
                    if map_error is not None
                    else (
                        "explicit equivariant first-page kernel character matches branch actual"
                        if computed == branch_actual
                        else "explicit equivariant first-page kernel character disagrees with branch actual"
                    )
                )
            ),
            "computed_actual": computed,
            "representative_method": "first_page_kernel",
            "source_representation": source_rep,
            "target_representation": target_rep,
            "required_image_ranks_for_branch": required,
            "required_image_ranks_feasible": feasible,
            "map_split": split,
            "map_error": map_error,
        }

    e2_resolution = compute_e2_resolution(
        manifold=manifold,
        context=context,
        line_audit=line_audit,
    )
    if e2_resolution["status"] == "e2_final_by_dimension":
        computed = e2_resolution["actual"].get(cohomology_key, rep_zero())
        return {
            **base,
            "status": (
                "representative_compatible"
                if computed == branch_actual
                else "representative_obstructed"
            ),
            "reason": (
                "dimension-certified equivariant E2 character matches branch actual"
                if computed == branch_actual
                else "dimension-certified equivariant E2 character disagrees with branch actual"
            ),
            "computed_actual": computed,
            "representative_method": "dimension_certified_equivariant_e2",
            "e2_resolution": e2_resolution,
        }

    return {
        **base,
        "status": "representative_unresolved",
        "reason": e2_resolution["reason"],
        "computed_actual": None,
        "representative_method": "complex_or_higher_leray_unresolved",
        "e2_resolution": e2_resolution,
    }


def select_pair_certificate(
    candidate: dict[str, Any], *, sector: str, pair: list[int]
) -> dict[str, Any]:
    certificates = candidate["character_certificate"]["characters"][sector]["line_certificates"]
    for certificate in certificates:
        if certificate.get("summand_pair") == pair:
            return certificate
    raise KeyError(f"missing {sector} pair {pair} for {candidate['label']}")


def singlet_lookup(candidate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["charge"]["label"]: item
        for item in candidate["singlet_moduli_inventory"]["all_nonzero_ext1_line_sectors"]
    }


def audit_singlet_factor(
    *,
    manifold: Any,
    conf: list[list[int]],
    context: dict[str, Any],
    line_cache: dict[tuple[int, ...], dict[str, Any]],
    label: str,
    singlets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if label not in singlets:
        return {
            "role": f"singlet:{label}",
            "status": "representative_unresolved",
            "reason": "singlet label missing from inventory",
        }
    singlet = singlets[label]
    actual = singlet["character_certificate"].get("actual", {})
    if not actual:
        return {
            "role": f"singlet:{label}",
            "label": singlet["label"],
            "charge": singlet["charge"],
            "line_bundle": singlet["line_bundle"],
            "cohomology": singlet["cohomology"],
            "branch_method": singlet["character_certificate"].get("method"),
            "branch_actual": None,
            "status": "representative_unresolved",
            "reason": "singlet character certificate has no actual cohomology character",
        }
    if len(actual) > 1:
        return {
            "role": f"singlet:{label}",
            "label": singlet["label"],
            "charge": singlet["charge"],
            "line_bundle": singlet["line_bundle"],
            "cohomology": singlet["cohomology"],
            "branch_method": singlet["character_certificate"].get("method"),
            "branch_actual": actual,
            "status": "representative_unresolved",
            "reason": "singlet has multiple actual cohomology degrees; not used by this simple pre-cup filter",
        }
    cohomology_key = next(iter(actual))
    certificate = {
        "line_bundle": singlet["line_bundle"],
        "cohomology": singlet["cohomology"],
        "actual": actual,
        "method": singlet["character_certificate"].get("method"),
    }
    audit = audit_character_leg(
        manifold=manifold,
        conf=conf,
        context=context,
        line_cache=line_cache,
        role=f"singlet:{label}",
        certificate=certificate,
        cohomology_key=cohomology_key,
    )
    return {
        **audit,
        "label": singlet["label"],
        "charge": singlet["charge"],
    }


def classify_status(statuses: list[str]) -> str:
    if any(status == "representative_obstructed" for status in statuses):
        return "representative_obstructed"
    if any(status == "representative_unresolved" for status in statuses):
        return "representative_unresolved"
    return "representative_compatible"


def audit_triplet_operator(
    *,
    manifold: Any,
    conf: list[list[int]],
    context: dict[str, Any],
    line_cache: dict[tuple[int, ...], dict[str, Any]],
    candidate: dict[str, Any],
    operator: dict[str, Any],
) -> dict[str, Any]:
    fivebar_pair = parse_pair(operator["fivebar"])
    five_pair = parse_pair(operator["five"])
    fivebar_cert = select_pair_certificate(candidate, sector="wedge2_V", pair=fivebar_pair)
    five_physical_cert = select_pair_certificate(candidate, sector="wedge2_V", pair=five_pair)
    five_cup_cert = select_pair_certificate(candidate, sector="wedge2_V_dual", pair=five_pair)
    legs = [
        audit_character_leg(
            manifold=manifold,
            conf=conf,
            context=context,
            line_cache=line_cache,
            role=f"{operator['fivebar']}:physical_H1_wedge2_V",
            certificate=fivebar_cert,
            cohomology_key="H1",
        ),
        audit_character_leg(
            manifold=manifold,
            conf=conf,
            context=context,
            line_cache=line_cache,
            role=f"{operator['five']}:physical_H2_wedge2_V",
            certificate=five_physical_cert,
            cohomology_key="H2",
        ),
        audit_character_leg(
            manifold=manifold,
            conf=conf,
            context=context,
            line_cache=line_cache,
            role=f"{operator['five']}:cup_H1_wedge2_V_dual",
            certificate=five_cup_cert,
            cohomology_key="H1",
        ),
    ]
    singlets = singlet_lookup(candidate)
    monomial_audits = []
    for monomial in operator.get("invariant_singlet_monomial_hits_degree_le_2", []):
        factor_audits = [
            audit_singlet_factor(
                manifold=manifold,
                conf=conf,
                context=context,
                line_cache=line_cache,
                label=label,
                singlets=singlets,
            )
            for label in monomial["labels"]
        ]
        monomial_status = classify_status([audit["status"] for audit in factor_audits])
        monomial_audits.append(
            {
                "labels": monomial["labels"],
                "degree": monomial.get("degree"),
                "charge": monomial["charge"],
                "branch_z2_product_support": monomial.get("z2_product_support"),
                "factor_audits": factor_audits,
                "status": monomial_status,
            }
        )
    matter_status = classify_status([leg["status"] for leg in legs])
    if matter_status == "representative_obstructed":
        target_status = "representative_obstructed"
    elif matter_status == "representative_unresolved":
        target_status = "representative_unresolved"
    elif any(monomial["status"] == "representative_compatible" for monomial in monomial_audits):
        target_status = "representative_compatible"
    elif any(monomial["status"] == "representative_unresolved" for monomial in monomial_audits):
        target_status = "representative_unresolved"
    else:
        target_status = "representative_obstructed"

    obstructing_legs = [
        leg for leg in legs if leg["status"] == "representative_obstructed"
    ]
    unresolved_legs = [
        leg for leg in legs if leg["status"] == "representative_unresolved"
    ]
    return {
        "operator": f"{operator['fivebar']}*{operator['five']}",
        "fivebar": operator["fivebar"],
        "five": operator["five"],
        "branch_selection_rule": {
            "support_class": operator["character_refined_support_class"],
            "triplet_pair_support": operator["triplet_pair_support"],
            "doublet_pair_support": operator["doublet_pair_support"],
            "fivebar_character_multiplicities": operator["fivebar_character_multiplicities"],
            "five_character_multiplicities": operator["five_character_multiplicities"],
            "serre_dual_five_character_multiplicities": operator.get(
                "serre_dual_five_character_multiplicities"
            ),
        },
        "matter_and_cup_leg_audits": legs,
        "monomial_audits": monomial_audits,
        "status": target_status,
        "eligible_for_exact_cup_product_rank": target_status == "representative_compatible",
        "cup_product_rank_claim": "not_attempted_pre_cup_filter",
        "obstruction_summary": (
            {
                "first_obstructing_role": obstructing_legs[0]["role"],
                "reason": obstructing_legs[0]["reason"],
                "branch_actual": obstructing_legs[0].get("branch_actual"),
                "computed_actual": obstructing_legs[0].get("computed_actual"),
                "required_image_ranks_for_branch": obstructing_legs[0].get(
                    "required_image_ranks_for_branch"
                ),
            }
            if obstructing_legs
            else None
        ),
        "unresolved_summary": (
            {
                "first_unresolved_role": unresolved_legs[0]["role"],
                "reason": unresolved_legs[0]["reason"],
            }
            if unresolved_legs
            else None
        ),
    }


def stable_row_id(index: int, candidate: dict[str, Any]) -> str:
    source = candidate["source"]
    window = source.get("window", "na")
    kind = source.get("kind", "unknown")
    path_name = Path(source.get("path", "")).stem
    return f"{index:02d}:{candidate['label']}:{kind}:w{window}:{path_name}"


def build_report(*, refined_json: Path, refined_verification_json: Path, split_json: Path) -> dict[str, Any]:
    refined = load_json(refined_json)
    refined_verification = load_json(refined_verification_json)
    split = load_json(split_json)
    conf = split["full_picard_presentation_7914"]["conf"]
    ensure_pycicy_compat()
    manifold = make_pycicy(pycicy_config(conf))
    context = load_5259_action_context()
    line_cache: dict[tuple[int, ...], dict[str, Any]] = {}

    records = []
    target_statuses: Counter[str] = Counter()
    weighted_target_statuses: Counter[str] = Counter()
    row_statuses: Counter[str] = Counter()
    weighted_row_statuses: Counter[str] = Counter()
    compatible_targets = []
    unresolved_targets = []
    obstructed_targets = []

    for index, candidate in enumerate(refined["refined_viable_candidate_records"]):
        row_id = stable_row_id(index, candidate)
        triplet_operators = [
            item
            for item in candidate["refined_mass_operator_table"]
            if item["character_refined_support_class"] == "triplet_only_character_mass"
        ]
        target_audits = [
            audit_triplet_operator(
                manifold=manifold,
                conf=conf,
                context=context,
                line_cache=line_cache,
                candidate=candidate,
                operator=operator,
            )
            for operator in triplet_operators
        ]
        row_status = classify_status([target["status"] for target in target_audits])
        weight = candidate.get("weight", 1)
        row_statuses[row_status] += 1
        weighted_row_statuses[row_status] += weight
        for target in target_audits:
            target_statuses[target["status"]] += 1
            weighted_target_statuses[target["status"]] += weight
            target_record = {
                "row_id": row_id,
                "candidate_label": candidate["label"],
                "source": candidate["source"],
                "weight": weight,
                "matrix": candidate["matrix"],
                **target,
            }
            if target["status"] == "representative_compatible":
                compatible_targets.append(target_record)
            elif target["status"] == "representative_unresolved":
                unresolved_targets.append(target_record)
            else:
                obstructed_targets.append(target_record)
        records.append(
            {
                "row_id": row_id,
                "candidate_label": candidate["label"],
                "source": candidate["source"],
                "weight": weight,
                "classification": candidate["classification"],
                "triplet_mass_target_count": len(target_audits),
                "representative_status": row_status,
                "target_audits": target_audits,
            }
        )

    ranked_targets = compatible_targets + unresolved_targets + obstructed_targets
    first_eligible = compatible_targets[0] if compatible_targets else None
    negative = next(
        (
            target
            for target in ranked_targets
            if target["candidate_label"] == NEGATIVE_CONTROL_LABEL
            and target["operator"] == NEGATIVE_CONTROL_OPERATOR
        ),
        None,
    )
    summary = {
        "refined_report_status": refined["status"],
        "refined_report_all_gates_pass": refined["all_gates_pass"],
        "refined_verification_all_gates_pass": refined_verification["all_gates_pass"],
        "survivor_rows_audited": len(records),
        "survivor_row_weight": sum(record["weight"] for record in records),
        "triplet_mass_targets_audited": sum(
            record["triplet_mass_target_count"] for record in records
        ),
        "target_status_counts": dict(sorted(target_statuses.items())),
        "weighted_target_status_counts": dict(sorted(weighted_target_statuses.items())),
        "row_status_counts": dict(sorted(row_statuses.items())),
        "weighted_row_status_counts": dict(sorted(weighted_row_statuses.items())),
        "representative_compatible_target_count": len(compatible_targets),
        "representative_unresolved_target_count": len(unresolved_targets),
        "representative_obstructed_target_count": len(obstructed_targets),
        "first_representative_compatible_target": first_eligible,
        "all_targets_obstructed_or_unresolved": first_eligible is None,
        "all_targets_resolved_at_representative_layer": len(unresolved_targets) == 0,
        "all_targets_representative_obstructed": (
            first_eligible is None
            and len(unresolved_targets) == 0
            and len(obstructed_targets)
            == sum(record["triplet_mass_target_count"] for record in records)
        ),
    }
    gates = {
        "starts_from_corrected_refined_report": gate(
            refined["all_gates_pass"]
            and refined_verification["all_gates_pass"]
            and refined["summary"]["refined_viable_candidate_weight"] == 1962,
            f"{refined_json} + {refined_verification_json}",
            "rerank starts from the verified corrected character-refined q=1 survivor report",
        ),
        "all_viable_rows_audited": gate(
            summary["survivor_rows_audited"]
            == len(refined["refined_viable_candidate_records"])
            and summary["survivor_row_weight"]
            == refined["summary"]["refined_viable_candidate_weight"],
            "refined_viable_candidate_records",
            "every explicit survivor row and its represented weight are covered",
        ),
        "all_triplet_targets_audited": gate(
            summary["triplet_mass_targets_audited"]
            == sum(
                1
                for candidate in refined["refined_viable_candidate_records"]
                for item in candidate["refined_mass_operator_table"]
                if item["character_refined_support_class"] == "triplet_only_character_mass"
            ),
            "triplet_only_character_mass entries",
            "every proposed triplet-only mass target is audited",
        ),
        "negative_control_is_obstructed": gate(
            negative is not None
            and negative["status"] == "representative_obstructed"
            and negative["obstruction_summary"]["first_obstructing_role"]
            == "5bar_02:physical_H1_wedge2_V"
            and negative["obstruction_summary"]["computed_actual"]["multiplicities"]
            == {"+": 1, "-": 1}
            and negative["obstruction_summary"]["branch_actual"]["multiplicities"]
            == {"+": 2, "-": 0},
            NEGATIVE_CONTROL_LABEL,
            "known shadow-collision negative control fails at representative realizability",
        ),
        "no_cup_rank_overclaimed": gate(
            all(
                target["cup_product_rank_claim"] == "not_attempted_pre_cup_filter"
                for record in records
                for target in record["target_audits"]
            ),
            "target audits",
            "rerank stops at the pre-cup representative layer and makes no mass-rank claim",
        ),
        "rerank_result_is_decisive": gate(
            summary["representative_compatible_target_count"] == 0
            and summary["all_targets_representative_obstructed"],
            "representative status counts",
            "all corrected refined survivors are resolved as representative-obstructed",
        ),
    }
    return {
        "title": "Representative-Compatible Rerank of Corrected q=1 Survivors",
        "status": (
            "no_representative_compatible_cup_product_target_found"
            if first_eligible is None
            else "representative_compatible_cup_product_target_found"
        ),
        "scope": "corrected refined q=1 viable survivors from windows 1-45",
        "source_artifacts": {
            "refined_json": str(refined_json),
            "refined_verification_json": str(refined_verification_json),
            "split_json": str(split_json),
        },
        "shadow_layer_interpretation": {
            "branch_selection_rule_layer": "charge/Wilson-line component filter using branch-completed characters",
            "representative_layer": "explicit or bounded equivariant Koszul E1 realization of the requested cohomology characters",
            "cup_product_layer": "not attempted until representative compatibility is certified",
        },
        "summary": summary,
        "negative_control": negative,
        "ranked_targets": ranked_targets,
        "candidate_records": records,
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        "# Representative-Compatible q=1 Survivor Rerank",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
        f"- survivor rows audited: `{summary['survivor_rows_audited']}`",
        f"- represented survivor weight: `{summary['survivor_row_weight']}`",
        f"- triplet-only mass targets audited: `{summary['triplet_mass_targets_audited']}`",
        f"- target status counts: `{summary['target_status_counts']}`",
        f"- weighted target status counts: `{summary['weighted_target_status_counts']}`",
        f"- representative-compatible targets: `{summary['representative_compatible_target_count']}`",
        f"- all targets resolved at representative layer: `{summary['all_targets_resolved_at_representative_layer']}`",
        f"- all targets representative-obstructed: `{summary['all_targets_representative_obstructed']}`",
        f"- all targets obstructed or unresolved: `{summary['all_targets_obstructed_or_unresolved']}`",
        "",
        "## Negative Control",
        "",
    ]
    negative = report["negative_control"]
    if negative:
        obstruction = negative["obstruction_summary"]
        lines.extend(
            [
                f"- candidate: `{negative['candidate_label']}`",
                f"- operator: `{negative['operator']}`",
                f"- status: `{negative['status']}`",
                f"- obstructing leg: `{obstruction['first_obstructing_role']}`",
                f"- branch actual: `{obstruction['branch_actual']}`",
                f"- computed actual: `{obstruction['computed_actual']}`",
                f"- required image ranks: `{obstruction['required_image_ranks_for_branch']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Reranked Targets",
            "",
        ]
    )
    for target in report["ranked_targets"][:20]:
        lines.append(
            f"- `{target['candidate_label']}` `{target['operator']}` "
            f"weight `{target['weight']}` -> `{target['status']}`"
        )
        if target["obstruction_summary"]:
            lines.append(
                f"  - obstruction: `{target['obstruction_summary']['first_obstructing_role']}`; "
                f"{target['obstruction_summary']['reason']}"
            )
        elif target["unresolved_summary"]:
            lines.append(
                f"  - unresolved: `{target['unresolved_summary']['first_unresolved_role']}`; "
                f"{target['unresolved_summary']['reason']}"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "No corrected refined survivor row is ready for exact cup-product rank verification under this representative-realizability filter. Branch-level selection-rule facts remain useful, but any exact mass-rank attempt now needs a representative-compatible target first.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refined-json",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45.json"),
    )
    parser.add_argument(
        "--refined-verification-json",
        default=str(
            REPORTS
            / "phenomenology_guided_q1_radius9_character_refined_dt_windows1_45_verification.json"
        ),
    )
    parser.add_argument(
        "--split-json",
        default=str(REPORTS / "cicy5259_split_lift_report.json"),
    )
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius9_representative_survivor_rerank.md"),
    )
    args = parser.parse_args()
    report = build_report(
        refined_json=Path(args.refined_json),
        refined_verification_json=Path(args.refined_verification_json),
        split_json=Path(args.split_json),
    )
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, md_out)
    print(f"status={report['status']}")
    print(f"target_status_counts={report['summary']['target_status_counts']}")
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
