#!/usr/bin/env python3
"""Profile charge-level obstructions across emitted radius-5 q=1 candidates."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": bool(status), "evidence": evidence, "note": note}


def candidate_weight(record: dict[str, Any], default: int = 1) -> int:
    if "_represented_q1_branches" in record:
        return int(record["_represented_q1_branches"])
    large = record.get("radius5_large_branch_representative")
    if isinstance(large, dict):
        return int(large.get("represented_q1_branches", default))
    return default


def mass_profile(mass_table: list[dict[str, Any]] | None) -> dict[str, Any]:
    table = mass_table or []
    allowed = [
        item for item in table if item.get("triplet_mass_allowed_by_current_selection_rules")
    ]
    selective = [
        item
        for item in table
        if item.get("selection_rule_can_lift_triplet_while_protecting_doublet")
    ]
    same_rule = [item for item in table if item.get("doublet_mass_same_selection_rule")]
    return {
        "mass_entries": len(table),
        "triplet_mass_allowed_entries": len(allowed),
        "selective_doublet_triplet_entries": len(selective),
        "same_rule_mass_entries": len(same_rule),
        "triplet_mass_allowed": bool(allowed),
        "selective_doublet_triplet_supported": bool(selective),
        "sample_allowed_entries": [
            {
                "fivebar": item.get("fivebar"),
                "five": item.get("five"),
                "needed_singlet_charge": item.get("needed_singlet_charge"),
                "hit_count": len(
                    item.get("certified_singlet_monomial_hits_degree_le_2", [])
                ),
            }
            for item in allowed[:3]
        ],
    }


def proton_profile(proton_table: list[dict[str, Any]] | None) -> dict[str, Any]:
    table = proton_table or []
    allowed = [
        item for item in table if not item.get("forbidden_by_current_selection_rules")
    ]
    return {
        "proton_entries": len(table),
        "dangerous_allowed_entries": len(allowed),
        "dangerous_all_forbidden": bool(table) and not allowed,
        "sample_allowed_operators": [
            {
                "operator": item.get("operator"),
                "charge": item.get("charge"),
            }
            for item in allowed[:5]
        ],
    }


def obstruction_profile(record: dict[str, Any]) -> dict[str, Any]:
    mass = mass_profile(record.get("mass_operator_table"))
    proton = proton_profile(record.get("proton_decay_operator_table"))
    if (
        mass["triplet_mass_allowed"]
        and mass["selective_doublet_triplet_supported"]
        and proton["dangerous_all_forbidden"]
    ):
        bucket = "passes_charge_level_filter"
    elif mass["triplet_mass_allowed"] and proton["dangerous_all_forbidden"]:
        bucket = "proton_safe_but_doublet_triplet_not_selective"
    elif (not mass["triplet_mass_allowed"]) and proton["dangerous_all_forbidden"]:
        bucket = "proton_safe_but_no_triplet_mass"
    elif mass["triplet_mass_allowed"] and not proton["dangerous_all_forbidden"]:
        bucket = "triplet_mass_but_dangerous_operator_allowed"
    else:
        bucket = "no_triplet_mass_and_dangerous_operator_allowed"
    classification = record.get("classification", {})
    return {
        "label": record.get("label"),
        "source": record.get("source"),
        "source_file": record.get("_source_file"),
        "weight": candidate_weight(record),
        "classification": classification,
        "profile_bucket": bucket,
        "spectrum_certificate": record.get("spectrum_certificate"),
        "mass_profile": mass,
        "proton_profile": proton,
        "matrix": record.get("matrix"),
    }


def iter_candidate_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        data = load_json(path)
        for record in data.get("desired_q1_branch_candidate_records", []):
            item = dict(record)
            item["_source_file"] = str(path)
            records.append(item)
        representative = data.get("q1_representative_candidate")
        if isinstance(representative, dict):
            item = dict(representative)
            item["_source_file"] = str(path)
            item["_represented_q1_branches"] = int(
                data.get("summary", {}).get("desired_q1_branches", 1)
            )
            records.append(item)
        for record in data.get("filtered_candidate_records", []):
            if not record.get("spectrum_certificate", {}).get(
                "desired_q1_three_family_signature"
            ):
                continue
            if record.get("mass_operator_table") is None:
                continue
            item = dict(record)
            item["_source_file"] = str(path)
            records.append(item)
    return records


def default_input_paths() -> list[Path]:
    final = load_json(REPORTS / "phenomenology_guided_q1_radius5_source_slices_0_128_closed_frontier.json")
    paths: list[Path] = []
    seen: set[Path] = set()

    def add_path(raw: str) -> None:
        path = Path(raw.strip())
        if not path.is_absolute():
            path = ROOT / path
        if path.name.endswith("_verification.json") or path in seen:
            return
        seen.add(path)
        paths.append(path)

    for slice_report in final["slice_reports"]:
        slice_path = Path(slice_report)
        if not slice_path.is_absolute():
            slice_path = ROOT / slice_path
        slice_data = load_json(slice_path)
        for window_report in slice_data["window_reports"]:
            window_path = Path(window_report)
            if not window_path.is_absolute():
                window_path = ROOT / window_path
            window_data = load_json(window_path)
            for gate_record in window_data.get("gates", {}).values():
                evidence = gate_record.get("evidence", "")
                for item in evidence.split(","):
                    raw = item.strip()
                    if raw.endswith(".json"):
                        add_path(raw)
    return paths


def build_report(paths: list[Path], *, sample_limit: int) -> dict[str, Any]:
    final_frontier = load_json(
        REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier.json"
    )
    final_verification = load_json(
        REPORTS
        / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier_verification.json"
    )
    records = iter_candidate_records(paths)
    profiles = [obstruction_profile(record) for record in records]
    bucket_counts = Counter(profile["profile_bucket"] for profile in profiles)
    weighted_bucket_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    weighted_status_counts: Counter[str] = Counter()
    for profile in profiles:
        weight = profile["weight"]
        status = profile["classification"].get("status", "missing_status")
        weighted_bucket_counts[profile["profile_bucket"]] += weight
        status_counts[status] += 1
        weighted_status_counts[status] += weight

    def samples(bucket: str) -> list[dict[str, Any]]:
        items = [profile for profile in profiles if profile["profile_bucket"] == bucket]
        items.sort(
            key=lambda item: (
                -item["weight"],
                item["classification"].get("status", ""),
                item["label"] or "",
            )
        )
        return items[:sample_limit]

    viable = [
        profile
        for profile in profiles
        if profile["profile_bucket"] == "passes_charge_level_filter"
    ]
    summary = {
        "input_files": len(paths),
        "candidate_records_indexed": len(records),
        "represented_q1_candidates": sum(profile["weight"] for profile in profiles),
        "viable_profile_count": len(viable),
        "profile_buckets": dict(sorted(bucket_counts.items())),
        "weighted_profile_buckets": dict(sorted(weighted_bucket_counts.items())),
        "classification_statuses": dict(sorted(status_counts.items())),
        "weighted_classification_statuses": dict(sorted(weighted_status_counts.items())),
        "final_frontier_viable_count": final_frontier["summary"]["viable_count"],
        "final_frontier_open_mass_bound_uncertainties": final_frontier["summary"][
            "open_mass_bound_uncertainties"
        ],
    }
    gates = {
        "imports_verified_post_monoid_frontier": gate(
            final_verification["all_gates_pass"]
            and final_frontier["summary"]["viable_count"] == 0
            and final_frontier["summary"]["open_mass_bound_uncertainties"] == 0,
            str(REPORTS / "phenomenology_guided_q1_radius5_post_monoid_closed_frontier_verification.json"),
            "charge-profile report is anchored to the verified post-monoid radius-5 frontier",
        ),
        "candidate_records_loaded": gate(
            len(records) > 0,
            "radius5 branch, large-branch, and adjacency candidate records",
            "detailed q=1 candidate records with mass/proton tables were indexed",
        ),
        "no_viable_profile_in_index": gate(
            len(viable) == 0,
            "computed charge-level profile buckets",
            "no indexed candidate satisfies triplet mass, selective doublet protection, and proton suppression",
        ),
        "negative_control_filter_is_active": gate(
            weighted_bucket_counts["proton_safe_but_doublet_triplet_not_selective"] > 0
            or weighted_bucket_counts["triplet_mass_but_dangerous_operator_allowed"] > 0,
            "charge-level obstruction profile buckets",
            "the report separates q=1 spectrum hits from the 5259-style charge-level obstructions",
        ),
    }
    return {
        "scope": "charge-level obstruction profile for emitted radius-5 q=1 candidate certificates",
        "status": (
            "viable_charge_profile_found"
            if viable
            else "no_viable_charge_profile_in_indexed_radius5_certificates"
        ),
        "summary": summary,
        "nearest_miss_samples": {
            bucket: samples(bucket)
            for bucket in [
                "proton_safe_but_doublet_triplet_not_selective",
                "proton_safe_but_no_triplet_mass",
                "triplet_mass_but_dangerous_operator_allowed",
                "no_triplet_mass_and_dangerous_operator_allowed",
            ]
        },
        "gates": gates,
        "all_gates_pass": all(item["pass"] for item in gates.values()),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Radius-5 Charge Filter Profile",
        "",
        f"Status: `{report['status']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Nearest Misses", ""])
    for bucket, samples in report["nearest_miss_samples"].items():
        lines.append(f"### `{bucket}`")
        if not samples:
            lines.append("")
            lines.append("- none indexed")
            lines.append("")
            continue
        for item in samples:
            lines.append(
                f"- `{item['label']}` weight `{item['weight']}` status "
                f"`{item['classification'].get('status')}` from `{item['source_file']}`"
            )
            if item["mass_profile"]["sample_allowed_entries"]:
                lines.append(
                    f"  - mass hits: `{item['mass_profile']['sample_allowed_entries']}`"
                )
            if item["proton_profile"]["sample_allowed_operators"]:
                lines.append(
                    f"  - dangerous operators: `{item['proton_profile']['sample_allowed_operators']}`"
                )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", default=None)
    parser.add_argument("--sample-limit", type=int, default=8)
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "phenomenology_guided_q1_radius5_charge_filter_profile.md"),
    )
    args = parser.parse_args()
    paths = [Path(item) for item in args.input] if args.input else default_input_paths()
    report = build_report(paths, sample_limit=args.sample_limit)
    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, md_path)
    print(f"status={report['status']}")
    print(f"summary={report['summary']}")
    print(f"json_out={json_path}")
    print(f"md_out={md_path}")
    return 0 if report["all_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
