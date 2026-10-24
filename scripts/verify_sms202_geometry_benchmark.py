#!/usr/bin/env python3
"""Reconstruct the SMS202 model 1710 characters from frozen geometric inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from string_theory.cicy import line_bundle_index, triple_intersections  # noqa: E402
from string_theory.mathematica import extract_assignment  # noqa: E402
from string_theory.sms202 import (  # noqa: E402
    derive_z2x2_downstairs_spectrum, digest_file, digest_text, parse_linemodels,
    parse_simple_fields, split_top_level, verify_golden_benchmark,
)
from string_theory.sms202_geometry import (  # noqa: E402
    GeometryGap, compare_published, load_geometry, reconstruct,
)


def verify(directory: Path, corpus: Path | None = None) -> dict:
    manifest = json.loads((directory / "model_1710_geometry_manifest.json").read_text())
    source = directory / manifest["model_fixture"]
    geometry_path = directory / "cicy7487_source.m"
    source_result = verify_golden_benchmark(source, directory / "model_1710_expected.json", corpus_path=corpus)
    checks = {"immutable_model_source": source_result.passed}
    checks["geometry_fixture_hash"] = digest_file(geometry_path) == manifest["geometry_fixture_sha256"]
    geometry_entry = extract_assignment(geometry_path.read_text(), "cicy_geometry").strip()
    checks["geometry_entry_hash"] = digest_text(geometry_entry) == manifest["geometry_entry_sha256"]
    if corpus is not None:
        checks["corpus_hash"] = digest_file(corpus) == manifest["corpus_sha256"]
        entries = split_top_level(extract_assignment(corpus.read_text(), "cicys")[1:-1])
        checks["geometry_verbatim_in_corpus"] = geometry_entry in entries
    record = parse_linemodels(source.read_text())[0]
    inputs = parse_simple_fields(record, ("LineSum", "Num", "ModelNumber", "EquivStr", "WLine"))
    checks["model_identity"] = inputs["Num"] == [7487, 4, 3] and inputs["ModelNumber"] == 23
    checks["symmetry_number_bound_to_model"] = inputs["Num"][2] == manifest["symmetry_number_one_based"]
    payload = {
        "benchmark": "sms202_cicy7487_model23_geometry_characters_v1",
        "identity": manifest,
        "claim_scope": "Generic smooth free members of the recorded invariant complete-intersection family",
        "smooth_free_locus": "Nonemptiness inherited from published geometry/action classification; integer rank witness is not a smoothness certificate",
        "checks": checks, "candidate_search_paused": True,
        "pending": ["operator classifications from geometry", "cup products and Yukawa ranks"],
        "implementation_sha256": {
            relative: digest_file(ROOT / relative) for relative in (
                "src/string_theory/sms202_geometry.py", "src/string_theory/sms202.py",
                "src/string_theory/cicy.py", "src/string_theory/mathematica.py",
                "scripts/verify_sms202_geometry_benchmark.py",
            )
        },
    }
    if not all(checks.values()):
        payload.update(status="input_provenance_failure", passed=False)
        return payload
    try:
        geometry = load_geometry(geometry_path, inputs["Num"][2])
        result = reconstruct(geometry, inputs["LineSum"])
    except GeometryGap as exc:
        payload.update(status="geometry_calculation_blocked", passed=False, first_gap=str(exc))
        return payload

    intersections = triple_intersections([list(row) for row in geometry.conf])
    rows = [row for entries in result["sectors"].values() for row in entries]
    rows += result["dual_calculations"]
    checks["riemann_roch_all_50_charged_calculations"] = all(
        sum((-1)**q*d for q, d in enumerate(row["dimensions"]))
        == line_bundle_index(row["charge"], intersections, list(geometry.c2)) for row in rows
    )
    checks["equivariant_euler_regular_all_50_charged_calculations"] = all(
        len({sum((-1)**q*row["cohomology_characters"][q][i] for q in range(4)) for i in range(4)}) == 1
        for row in rows
    )
    checks["serre_duality_all_25_sectors"] = all(row["serre_dual_verified"] for entries in result["sectors"].values() for row in entries)
    checks["canonical_top_character_trivial"] = result["structure_sheaf"]["cohomology_characters"][3] == [1, 0, 0, 0]
    checks["full_invariant_polynomial_family_verified"] = all(
        row["equivariant_family_dimension"] == row["recorded_basis_rank"]
        for row in result["polynomial_family"]
    )

    # Published cohomology is decoded only for comparison, after calculation.
    published = parse_simple_fields(record, ("Coh", "Coh2", "CohSing", "GCoh", "GCoh2", "GCohSing"))
    checks.update({f"published_{key}": value for key, value in compare_published(result, published).items()})
    computed_tables = {
        field: [row["cohomology_characters"] for row in result["sectors"][sector]]
        for field, sector in (("GCoh", "V"), ("GCoh2", "wedge2"), ("GCohSing", "singlets"))
    }
    downstairs = derive_z2x2_downstairs_spectrum({**inputs, **computed_tables})
    expected = json.loads((directory / "model_1710_expected.json").read_text())
    checks["downstairs_from_geometry_matches_frozen_result"] = downstairs == expected["derived"]["downstairs_spectrum"]
    payload.update(
        passed=all(checks.values()), status="geometry_characters_match" if all(checks.values()) else "benchmark_discrepancy",
        character_order=["1", "a", "b", "ab"], character_bits=[[0, 0], [1, 0], [0, 1], [1, 1]],
        downstairs=downstairs, reconstruction=result,
        matched_sector_tables=sum(
            row["cohomology_characters"] == expected_row
            for sector, field in (("V", "GCoh"), ("wedge2", "GCoh2"), ("singlets", "GCohSing"))
            for row, expected_row in zip(result["sectors"][sector], published[field])
        ),
        failed_checks=[name for name, value in checks.items() if not value],
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "benchmarks" / "sms202")
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--output", type=Path, help="Write the fully reconstructed certificate, including exact matrices.")
    args = parser.parse_args()
    payload = verify(args.fixtures, args.corpus)
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in payload.items() if k != "reconstruction"}, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
