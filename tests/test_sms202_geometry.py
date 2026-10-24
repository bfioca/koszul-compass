from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import sympy as sp

from string_theory.sms202 import parse_linemodels, parse_simple_fields
from string_theory.sms202_geometry import (
    GeometryGap, ambient_action, ambient_basis, character_multiplicities,
    compare_published, compute_line, load_geometry, reconstruct, validate_geometry,
)


FIXTURES = Path(__file__).resolve().parents[1] / "benchmarks" / "sms202"


@pytest.fixture(scope="module")
def geometry():
    return load_geometry(FIXTURES / "cicy7487_source.m")


@pytest.fixture(scope="module")
def published():
    record = parse_linemodels((FIXTURES / "model_1710_source.m").read_text())[0]
    return parse_simple_fields(record, ("LineSum", "Coh", "Coh2", "CohSing", "GCoh", "GCoh2", "GCohSing"))


@pytest.fixture(scope="module")
def reconstruction(geometry, published):
    return reconstruct(geometry, published["LineSum"])


def test_cech_exchange_sign_on_p1_h1(geometry):
    degree = (-2, 0, 0, 0, 0)
    q, basis = ambient_basis(degree)
    assert q == 1 and len(basis) == 1
    actions = tuple(ambient_action(basis, degree, g) for g in geometry.coordinates)
    # The class 1/(x1*x2) changes sign when its two Cech charts are exchanged.
    assert actions[0] == actions[1] == sp.Matrix([[-1]])
    assert character_multiplicities(actions) == [0, 0, 0, 1]


def test_positive_p1_sections_have_no_cech_exchange_sign(geometry):
    degree = (2, 0, 0, 0, 0)
    q, basis = ambient_basis(degree)
    actions = tuple(ambient_action(basis, degree, g) for g in geometry.coordinates)
    assert q == 0
    assert character_multiplicities(actions) == [1, 1, 1, 0]


def test_every_published_sector_matches(reconstruction, published):
    assert all(compare_published(reconstruction, published).values())
    assert reconstruction["distinct_line_calculations"] == 51


def test_nonregular_higgs_and_singlet_characters(reconstruction):
    higgs = reconstruction["sectors"]["wedge2"][7]
    singlets = reconstruction["sectors"]["singlets"][7]
    assert higgs["cohomology_characters"][1:3] == [[1, 0, 0, 0]]*2
    assert singlets["cohomology_characters"][1:3] == [[3, 2, 2, 2]]*2
    assert higgs["maps"] == []


def test_three_rank_witnesses_and_direct_kernels(reconstruction):
    maps = [m for row in reconstruction["sectors"]["wedge2"] for m in row["maps"]]
    assert len(maps) == 3
    for entry in maps:
        matrix = sp.Matrix(entry["witness_matrix"])
        witness = entry["nonzero_minor"]
        assert matrix.extract(witness["rows"], witness["columns"]).det() == witness["determinant"] != 0
        assert entry["rank"] == 12
        assert entry["image_characters"] == [3, 3, 3, 3]
        assert entry["kernel_characters"] == [1, 1, 1, 1]
        assert entry["cokernel_characters"] == [0]*4
        assert entry["kernel_cokernel_actions_independently_restricted"]


def test_expected_character_poison_does_not_enter_calculation(reconstruction, published):
    poisoned = deepcopy(published)
    poisoned["GCoh2"][7][1] = [0, 1, 0, 0]
    checks = compare_published(reconstruction, poisoned)
    assert checks["GCoh2"] is False
    assert checks["Coh2"] is True
    assert reconstruction["sectors"]["wedge2"][7]["cohomology_characters"][1] == [1, 0, 0, 0]


def test_wrong_normal_action_is_rejected(geometry):
    bad = replace(geometry, equations=(sp.eye(2), geometry.equations[1]))
    with pytest.raises(GeometryGap, match="equation equivariance"):
        validate_geometry(bad)


def test_rank_is_not_assumed_from_ambient_dimensions(geometry):
    # Delete p1 while retaining the same ambient groups: the 16 -> 12 map can
    # no longer be surjective. A dimension-only calculation would miss this.
    bad = replace(geometry, polynomial_basis=tuple(
        (sp.Poly(0, *p.gens), q) for p, q in geometry.polynomial_basis
    ))
    with pytest.raises(GeometryGap, match="does not saturate"):
        compute_line(bad, (2, -2, -2, 1, 1))


def test_generic_character_does_not_depend_on_basis_normalization(geometry, published, reconstruction):
    rescaled = replace(geometry, polynomial_basis=tuple(
        tuple((i+2)*p for p in row) for i, row in enumerate(geometry.polynomial_basis)
    ))
    validate_geometry(rescaled)
    result = reconstruct(rescaled, published["LineSum"])
    assert all(compare_published(result, published).values())
    assert result["sectors"]["wedge2"][0]["maps"][0]["nonzero_minor"] != reconstruction["sectors"]["wedge2"][0]["maps"][0]["nonzero_minor"]


def test_dual_calculations_and_top_form(reconstruction):
    rows = [r for entries in reconstruction["sectors"].values() for r in entries]
    assert len(reconstruction["dual_calculations"]) == 25
    for row, dual in zip(rows, reconstruction["dual_calculations"]):
        assert row["cohomology_characters"] == dual["cohomology_characters"][::-1]
    assert reconstruction["structure_sheaf"]["cohomology_characters"] == [
        [1, 0, 0, 0], [0]*4, [0]*4, [1, 0, 0, 0]
    ]


def test_recorded_family_is_complete(reconstruction):
    assert [r["equivariant_family_dimension"] for r in reconstruction["polynomial_family"]] == [4, 12]


def test_potential_higher_map_is_unresolved_not_assumed_zero(geometry, monkeypatch):
    import string_theory.sms202_geometry as module

    def level():
        return {"terms": [], "basis": [()], "actions": (sp.eye(1), sp.eye(1)), "characters": [1, 0, 0, 0]}

    monkeypatch.setattr(module, "koszul_levels", lambda *_: {(2, 2): level(), (0, 1): level()})
    with pytest.raises(GeometryGap, match="potentially nonzero d2"):
        compute_line(geometry, (0,)*5)
