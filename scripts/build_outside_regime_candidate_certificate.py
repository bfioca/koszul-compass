#!/usr/bin/env python3
"""Build a compact certificate for the best outside-regime candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from string_theory.novelty import build_dataset_keys, novelty_record
from verify_candidate_novelty import gut_entries, sms_entries


def load_json(name: str) -> Any:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def gate(status: bool, evidence: str, note: str) -> dict[str, Any]:
    return {"pass": status, "evidence": evidence, "note": note}


def novelty_context() -> dict[str, Any]:
    gut, gut_confs = gut_entries()
    sms = sms_entries()
    combined = gut + sms
    return {
        "dataset_counts": {
            "GUTall": len(gut),
            "sms202": len(sms),
            "combined": len(combined),
        },
        "key_sets": {
            "GUTall": build_dataset_keys(gut, gut_confs),
            "sms202": build_dataset_keys(sms, None),
            "combined": build_dataset_keys(combined, gut_confs),
        },
    }


def candidate_score(record: dict[str, Any]) -> tuple:
    spectrum = record["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    quality = record["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    return (
        spectrum["upstairs_anti_10"],
        spectrum["upstairs_5"],
        0 if quality["regular_nontrivial_summand_scan_style"] else 1,
        quality["trivial_summand_count"],
        record["max_entry_abs"],
        record.get("delta_l1", 0),
        sum(record["anomaly"]),
    )


def label_from_local_report(report_name: str, rank: int) -> str:
    if report_name == "outside_regime_local_deformations_delta1.json":
        return f"outside_h11_7_cicy2544_local_delta1_rank{rank}"
    stem = Path(report_name).stem
    suffix = stem.removeprefix("outside_regime_")
    suffix = suffix.replace("local_deformations_", "local_")
    suffix = suffix.replace("-", "_")
    return f"outside_h11_7_cicy2544_{suffix}_rank{rank}"


def best_candidate_record() -> tuple[dict[str, Any], dict[str, Any]]:
    local_candidates = []
    for local_report_path in sorted(REPORTS.glob("outside_regime_local_deformations*.json")):
        local = json.loads(local_report_path.read_text(encoding="utf-8"))
        for rank, record in enumerate(local.get("best_spectrum_records", []), start=1):
            local_candidates.append((candidate_score(record), local_report_path.name, rank, local, record))

    if local_candidates:
        _, report_name, rank, local, record = min(local_candidates)
        best = {**record, "cicy": local["search"]["cicy"]}
        base_context = local.get("base_context", {})
        return best, {
            "source": "local_deformation",
            "label": label_from_local_report(report_name, rank),
            "search_report": f"reports/{report_name}",
            "base_candidate_label": base_context.get(
                "base_candidate_label",
                "outside_h11_7_cicy2544_bound1_rank1",
            ),
            "base_search_report": base_context.get(
                "base_candidate_search_report",
                "reports/outside_regime_algebraic_scout_bound1_samples50000.json",
            ),
            "base_candidate_certificate": base_context.get(
                "base_candidate_certificate",
                "reports/outside_regime_candidate_certificate.json",
            ),
            "base_matrix": local["base_matrix"],
            "columns": best["columns"],
            "delta": best["delta"],
            "search": local["search"],
            "interpretation": local.get("interpretation"),
        }

    scout = load_json("outside_regime_algebraic_scout_bound1_samples50000.json")
    best = scout["best_spectrum_records"][0]
    return best, {
        "source": "algebraic_scout",
        "label": "outside_h11_7_cicy2544_bound1_rank1",
        "search_report": "reports/outside_regime_algebraic_scout_bound1_samples50000.json",
        "sample_index": best["sample_index"],
        "search": scout["search"],
    }


def build_certificate() -> dict[str, Any]:
    target_pool = load_json("outside_regime_targets.json")
    best, construction_context = best_candidate_record()
    target = next(
        item
        for item in target_pool["immediate_favourable_targets"]
        if item["num"] == best["cicy"]
    )
    spectrum = best["cohomology_and_spectrum"]["su5_upstairs_spectrum"]
    quality = best["cohomology_and_spectrum"]["line_bundle_sum_quality"]
    symmetry_order = abs(best["index_v"]) // 3
    novelty = {
        name: novelty_record(
            cicy_num=best["cicy"],
            symmetry_order=symmetry_order,
            matrix=best["matrix"],
            conf=target["conf"],
            dataset_keys=keys,
        )
        for name, keys in novelty_context()["key_sets"].items()
    }
    combined_novelty = novelty["combined"]

    construction = {
        "label": construction_context["label"],
        "cicy": best["cicy"],
        "h11": 7,
        "matrix": best["matrix"],
        "search_report": construction_context["search_report"],
        "target_pool_report": "reports/outside_regime_targets.json",
        "outside_old_gutall_regime": True,
        "source": construction_context["source"],
    }
    if construction_context["source"] == "local_deformation":
        construction.update(
            {
                "base_candidate_label": construction_context["base_candidate_label"],
                "base_search_report": construction_context["base_search_report"],
                "base_candidate_certificate": construction_context[
                    "base_candidate_certificate"
                ],
                "base_matrix": construction_context["base_matrix"],
                "local_deformation_columns": construction_context["columns"],
                "local_deformation_delta": construction_context["delta"],
                "local_deformation_search": construction_context["search"],
                "local_deformation_interpretation": construction_context[
                    "interpretation"
                ],
            }
        )
    else:
        construction["sample_index"] = construction_context["sample_index"]

    return {
        "scope": "best outside-GUTall favourable h11=7 SU(5) line-bundle candidate certified in current reports",
        "construction": construction,
        "gate_checklist": {
            "outside_regime_target": gate(
                best["cicy"]
                in target_pool["candidate_pool"]["immediate_favourable_target_nums"],
                "reports/outside_regime_targets.json",
                "CICY is a favourable h11=7 known-symmetry target outside GUTall h11<7 regime",
            ),
            "c1_zero": gate(
                best["c1"] == [0] * 7,
                construction_context["search_report"],
                f"c1(V)={best['c1']}",
            ),
            "index_chirality": gate(
                best["index_v"] == -3 and best["index_wedge2_v"] == -3,
                construction_context["search_report"],
                f"ind(V)={best['index_v']}, ind(wedge^2 V)={best['index_wedge2_v']}",
            ),
            "anomaly_effective": gate(
                all(value >= 0 for value in best["anomaly"]),
                construction_context["search_report"],
                f"ambient anomaly={best['anomaly']}",
            ),
            "slope_zero_numerical": gate(
                best["passes_slope_gate"],
                construction_context["search_report"],
                (
                    "max normalized slope="
                    f"{best['slope_search']['max_normalized_slope']:.3g}"
                ),
            ),
            "cohomology_spectrum": gate(
                best["passes_upstairs_spectrum_gate"]
                and spectrum["upstairs_anti_10"] == 0,
                construction_context["search_report"],
                (
                    f"upstairs 10/anti10/5bar/5="
                    f"{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
                    f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}"
                ),
            ),
            "regular_nontrivial_quality": gate(
                quality["regular_nontrivial_summand_scan_style"],
                construction_context["search_report"],
                (
                    f"trivial_summands={quality['trivial_summand_count']}, "
                    f"h0(V)={quality['h0_v']}, h0(V*)={quality['h0_v_dual']}"
                ),
            ),
            "implemented_novelty": gate(
                combined_novelty["novel_under_row_and_column_permutation"],
                "data/raw/GUTall.m + data/raw/sms202.m",
                "novel against GUTall+sms202 under implemented row/column equivalences",
            ),
        },
        "spectrum": {
            "upstairs_10": spectrum["upstairs_10"],
            "upstairs_anti_10": spectrum["upstairs_anti_10"],
            "upstairs_5bar": spectrum["upstairs_5bar"],
            "upstairs_5": spectrum["upstairs_5"],
            "net_10_chirality": spectrum["net_10_chirality"],
            "net_5bar_chirality": spectrum["net_5bar_chirality"],
            "expected_upstairs_chirality": spectrum["expected_upstairs_chirality"],
            "higgs_pair_candidates_upstairs": spectrum[
                "higgs_pair_candidates_upstairs"
            ],
        },
        "quality": {
            "trivial_summand_count": quality["trivial_summand_count"],
            "h0_v": quality["h0_v"],
            "h0_v_dual": quality["h0_v_dual"],
            "regular_nontrivial_summand_scan_style": quality[
                "regular_nontrivial_summand_scan_style"
            ],
        },
        "novelty": novelty,
        "wilson_line_applicability": {
            "evidence": "reports/outside_regime_targets.json",
            "cicylist_symmetry_option_count": target["symmetry_option_count"],
            "raw_free_symmetry_option_count": target["free_symmetry_option_count"],
            "wilson_line_descent_applicable_from_recorded_raw_symmetry": target[
                "free_symmetry_option_count"
            ]
            > 0,
            "status": (
                "not_applicable_from_recorded_raw_cicylist_symmetry"
                if target["free_symmetry_option_count"] == 0
                else "requires_line_bundle_equivariance_and_cohomology_action_check"
            ),
            "interpretation": (
                "The raw cicylist.m entry has known symmetry data but no recorded "
                "free symmetry option, so this certificate treats the model as an "
                "upstairs SU(5) GUT candidate rather than a Wilson-line MSSM candidate."
            ),
        },
        "caveats": [
            "This is a deterministic sampled scout plus local deformation hit, not an exhaustive outside-regime search.",
            "The slope-zero gate is numerical, not an exact poly-stability proof.",
            "The raw cicylist.m entry has known symmetry data but no recorded free symmetry option, so Wilson-line descent is not applicable from the recorded raw symmetry data.",
            (
                "The candidate is an exact chiral upstairs SU(5) spectrum with no "
                "upstairs vectorlike 5/5bar Higgs-pair candidate; it is not an "
                "exact MSSM spectrum."
                if spectrum["upstairs_5"] == 0
                else "The candidate is an upstairs SU(5) GUT spectrum with vectorlike 5/5bar pairs, not an exact MSSM spectrum."
            ),
        ],
    }


def write_markdown(certificate: dict[str, Any], path: Path) -> None:
    construction = certificate["construction"]
    spectrum = certificate["spectrum"]
    lines = [
        "# Outside-Regime Candidate Certificate",
        "",
        (
            f"Label: `{construction['label']}` on CICY `{construction['cicy']}` "
            f"with `h11={construction['h11']}`."
        ),
        "",
        "```text",
        str(construction["matrix"]),
        "```",
        "",
    ]
    if construction["source"] == "local_deformation":
        lines.extend(
            [
                (
                    "This candidate is the best spectrum-pass local deformation of "
                    f"`{construction['base_candidate_label']}` using columns "
                    f"`{construction['local_deformation_columns']}` and delta "
                    f"`{construction['local_deformation_delta']}`."
                ),
                "",
            ]
        )
    lines.extend(
        [
        "## Gates",
        "",
        ]
    )
    for name, record in certificate["gate_checklist"].items():
        status = "PASS" if record["pass"] else "FAIL"
        lines.append(f"- `{name}`: {status}. {record['note']} ({record['evidence']})")
    lines.extend(
        [
            "",
            "## Spectrum",
            "",
            (
                f"Upstairs `10/anti10/5bar/5` = "
                f"`{spectrum['upstairs_10']}/{spectrum['upstairs_anti_10']}/"
                f"{spectrum['upstairs_5bar']}/{spectrum['upstairs_5']}`."
            ),
            (
                f"Upstairs Higgs-pair candidates: "
                f"`{spectrum['higgs_pair_candidates_upstairs']}`."
            ),
            (
                f"Net chiralities: `10={spectrum['net_10_chirality']}`, "
                f"`5bar={spectrum['net_5bar_chirality']}`."
            ),
            "",
            "## Caveats",
            "",
        ]
    )
    for caveat in certificate["caveats"]:
        lines.append(f"- {caveat}")
    wilson = certificate["wilson_line_applicability"]
    lines.extend(
        [
            "",
            "## Wilson-Line Applicability",
            "",
            (
                f"Raw recorded symmetry options: `{wilson['cicylist_symmetry_option_count']}`; "
                f"recorded free options: `{wilson['raw_free_symmetry_option_count']}`."
            ),
            wilson["interpretation"],
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-out",
        default=str(REPORTS / "outside_regime_candidate_certificate.json"),
    )
    parser.add_argument(
        "--md-out",
        default=str(REPORTS / "outside_regime_candidate_certificate.md"),
    )
    args = parser.parse_args()

    certificate = build_certificate()
    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(certificate, md_out)
    print(f"label={certificate['construction']['label']}")
    print(f"cicy={certificate['construction']['cicy']}")
    print(
        "spectrum="
        f"{certificate['spectrum']['upstairs_10']}/"
        f"{certificate['spectrum']['upstairs_anti_10']}/"
        f"{certificate['spectrum']['upstairs_5bar']}/"
        f"{certificate['spectrum']['upstairs_5']}"
    )
    print(f"json_out={json_out}")
    print(f"md_out={md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
