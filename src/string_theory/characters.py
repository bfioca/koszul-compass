"""Targeted equivariant character computations for CICY 7484."""

from __future__ import annotations

from typing import Any

from .cohomology import cohomology_record, wedge2_line_summands


CHARACTERS = ["1", "a", "b", "ab"]
IRREP_CHARACTER_VALUES = {
    "1": {"1": 1, "a": 1, "b": 1, "ab": 1},
    "a": {"1": 1, "a": -1, "b": 1, "ab": -1},
    "b": {"1": 1, "a": 1, "b": -1, "ab": -1},
    "ab": {"1": 1, "a": -1, "b": -1, "ab": 1},
}


def _clean_complex(value: complex, tolerance: float = 1e-9) -> int | float:
    if abs(value.imag) < tolerance:
        real = value.real
        rounded = round(real)
        if abs(real - rounded) < tolerance:
            return int(rounded)
        return real
    raise ValueError(f"unexpected non-real character value {value}")


def complete_homogeneous_trace(eigenvalues: list[complex], degree: int) -> complex:
    """Trace of `Sym^degree` from eigenvalues of the underlying representation."""

    coeffs = [0j for _ in range(degree + 1)]
    coeffs[0] = 1 + 0j
    for eigenvalue in eigenvalues:
        updated = coeffs[:]
        for total_degree in range(1, degree + 1):
            power = eigenvalue
            for used in range(1, total_degree + 1):
                updated[total_degree] += power * coeffs[total_degree - used]
                power *= eigenvalue
        coeffs = updated
    return coeffs[degree]


def cicy7484_z2xz2_factor_eigenvalues() -> dict[str, list[list[complex]]]:
    i = 1j
    return {
        "1": [[1, 1], [1, 1], [1, 1, 1, 1]],
        "a": [[1, -1], [1, -1], [1, -1, 1, -1]],
        "b": [[1, -1], [1, -1], [1, -1, 1, -1]],
        "ab": [[i, -i], [i, -i], [i, -i, i, -i]],
    }


def projective_factor_line_character(
    *, degree: int, dimension: int, eigenvalues: list[complex]
) -> tuple[int, dict[str, int | float]]:
    """Return `(cohomology_degree, character)` for one projective factor."""

    if degree >= 0:
        return 0, {
            "trace": _clean_complex(complete_homogeneous_trace(eigenvalues, degree)),
            "dimension": int(complete_homogeneous_trace([1] * len(eigenvalues), degree).real),
        }
    if degree <= -dimension - 1:
        dual_degree = -degree - dimension - 1
        determinant = 1 + 0j
        for eigenvalue in eigenvalues:
            determinant *= eigenvalue
        trace = (1 / determinant) * complete_homogeneous_trace(eigenvalues, dual_degree)
        identity_dim = complete_homogeneous_trace([1] * len(eigenvalues), dual_degree)
        return dimension, {
            "trace": _clean_complex(trace),
            "dimension": int(identity_dim.real),
        }
    return -1, {"trace": 0, "dimension": 0}


def ambient_line_cohomology_character(line_bundle: list[int]) -> dict[str, Any]:
    """Character of the unique nonzero ambient cohomology of a product line bundle."""

    ambient_dimensions = [1, 1, 3]
    factor_eigenvalues = cicy7484_z2xz2_factor_eigenvalues()
    total_degree = 0
    traces = {character: 1 for character in CHARACTERS}
    dimension = 1
    for factor_index, degree in enumerate(line_bundle):
        identity_factor = projective_factor_line_character(
            degree=degree,
            dimension=ambient_dimensions[factor_index],
            eigenvalues=factor_eigenvalues["1"][factor_index],
        )
        if identity_factor[0] < 0:
            return {"nonzero": False, "cohomology_degree": None, "dimension": 0, "character": {}}
        total_degree += identity_factor[0]
        dimension *= identity_factor[1]["dimension"]
        for character in CHARACTERS:
            factor = projective_factor_line_character(
                degree=degree,
                dimension=ambient_dimensions[factor_index],
                eigenvalues=factor_eigenvalues[character][factor_index],
            )
            traces[character] *= factor[1]["trace"]
    return {
        "nonzero": dimension != 0,
        "cohomology_degree": total_degree,
        "dimension": dimension,
        "character": {character: int(traces[character]) for character in CHARACTERS},
    }


def _sub(a: list[int], b: list[int]) -> list[int]:
    return [x - y for x, y in zip(a, b)]


def z2xz2_irrep_multiplicities(trace: dict[str, int]) -> dict[str, int] | None:
    """Decompose a `Z2 x Z2` trace vector into irrep multiplicities."""

    multiplicities = {}
    for irrep, values in IRREP_CHARACTER_VALUES.items():
        numerator = sum(trace[group_element] * values[group_element] for group_element in CHARACTERS)
        if numerator % 4:
            return None
        multiplicity = numerator // 4
        if multiplicity < 0:
            return None
        multiplicities[irrep] = multiplicity
    return multiplicities


def _is_regular_multiplicity(multiplicities: dict[str, int] | None) -> int | None:
    if multiplicities is None:
        return None
    values = list(multiplicities.values())
    return values[0] if all(value == values[0] for value in values) else None


def cicy7484_wedge2_h2_single_source_character_certificate(
    matrix: list[list[int]], conf: list[list[int]]
) -> dict[str, Any]:
    """Compute actual `H^2(wedge^2 V)` character when single-source terms suffice."""

    q1 = [row[0] for row in conf]
    q2 = [row[1] for row in conf]
    shifts = [
        {"label": "0", "shift": [0, 0, 0], "koszul_degree": 0},
        {"label": "q1", "shift": q1, "koszul_degree": 1},
        {"label": "q2", "shift": q2, "koszul_degree": 1},
        {
            "label": "q1+q2",
            "shift": [q1[i] + q2[i] for i in range(3)],
            "koszul_degree": 2,
        },
    ]
    contributions = []
    total_character = {character: 0 for character in CHARACTERS}
    accounted_dimension = 0
    target_dimension = 0
    for line_bundle in wedge2_line_summands(matrix):
        cohomology = cohomology_record(conf, line_bundle)["cohomology"]
        target_dimension += cohomology[2]
        if cohomology[2] == 0:
            continue
        sources = []
        for shift in shifts:
            ambient_bundle = _sub(line_bundle, shift["shift"])
            ambient = ambient_line_cohomology_character(ambient_bundle)
            if not ambient["nonzero"]:
                continue
            if ambient["cohomology_degree"] - shift["koszul_degree"] == 2:
                sources.append(
                    {
                        "koszul_label": shift["label"],
                        "koszul_degree": shift["koszul_degree"],
                        "ambient_line_bundle": ambient_bundle,
                        **ambient,
                    }
                )
        if len(sources) != 1 or sources[0]["dimension"] != cohomology[2]:
            return {
                "scope": "single-source H2(wedge2 V) character certificate",
                "character_computed": False,
                "reason": "non-single-source term or dimension mismatch",
                "target_h2_dimension": target_dimension,
                "accounted_h2_dimension": accounted_dimension,
                "line_bundle": line_bundle,
                "sources": sources,
            }
        source = sources[0]
        accounted_dimension += source["dimension"]
        for character in CHARACTERS:
            total_character[character] += source["character"][character]
        contributions.append(
            {
                "line_bundle": line_bundle,
                "h2_dimension": cohomology[2],
                "source": source,
            }
        )
    multiplicities = z2xz2_irrep_multiplicities(total_character)
    regular_multiplicity = _is_regular_multiplicity(multiplicities)
    return {
        "scope": "single-source H2(wedge2 V) character certificate",
        "character_computed": accounted_dimension == target_dimension,
        "target_h2_dimension": target_dimension,
        "accounted_h2_dimension": accounted_dimension,
        "character_order": CHARACTERS,
        "h2_character": total_character,
        "h2_irrep_multiplicities": multiplicities,
        "h2_regular_multiplicity": regular_multiplicity,
        "contributions": contributions,
    }


def cicy7484_actual_wedge2_z2xz2_character_certificate(
    matrix: list[list[int]], conf: list[list[int]], group_order: int = 4
) -> dict[str, Any]:
    """Actual `wedge^2 V` character certificate from H2 plus Lefschetz."""

    h2_certificate = cicy7484_wedge2_h2_single_source_character_certificate(matrix, conf)
    h2_multiplicities = h2_certificate.get("h2_irrep_multiplicities")
    if not h2_certificate["character_computed"] or h2_multiplicities is None:
        return {
            "scope": "actual Z2xZ2 wedge2 cohomology character certificate",
            "character_computed": False,
            "h2_certificate": h2_certificate,
        }
    h1_total = 0
    h2_total = h2_certificate["target_h2_dimension"]
    for line_bundle in wedge2_line_summands(matrix):
        cohomology = cohomology_record(conf, line_bundle)["cohomology"]
        h1_total += cohomology[1]
    virtual_regular_multiplicity = (h1_total - h2_total) // group_order
    h1_multiplicities = {
        irrep: multiplicity + virtual_regular_multiplicity
        for irrep, multiplicity in h2_multiplicities.items()
    }
    per_irrep_pairs = {
        irrep: [h1_multiplicities[irrep], h2_multiplicities[irrep]]
        for irrep in CHARACTERS
    }
    best_irrep = min(CHARACTERS, key=lambda irrep: (per_irrep_pairs[irrep][1], per_irrep_pairs[irrep][0]))
    h2_regular = h2_certificate["h2_regular_multiplicity"]
    h1_regular = (
        h2_regular + virtual_regular_multiplicity
        if h2_regular is not None
        else None
    )
    h1_character = {
        "1": h1_total,
        **{character: h2_certificate["h2_character"][character] for character in CHARACTERS[1:]},
    }
    return {
        "scope": "actual Z2xZ2 wedge2 cohomology character certificate",
        "character_computed": True,
        "method": "single-source H2 character decomposition plus free-Lefschetz virtual regularity",
        "h2_certificate": h2_certificate,
        "h1_total": h1_total,
        "h2_total": h2_total,
        "virtual_regular_multiplicity": virtual_regular_multiplicity,
        "h1_regular_multiplicity": h1_regular,
        "h2_regular_multiplicity": h2_regular,
        "h1_character": h1_character,
        "h2_character": h2_certificate["h2_character"],
        "h1_irrep_multiplicities": h1_multiplicities,
        "h2_irrep_multiplicities": h2_multiplicities,
        "per_irrep_pairs": per_irrep_pairs,
        "best_irrep_by_vectorlike_content": best_irrep,
        "best_per_character_pair": per_irrep_pairs[best_irrep],
        "per_character_pair": [h1_regular, h2_regular] if h1_regular is not None else None,
        "actual_three_family_no_vectorlike_pair": [3, 0] in per_irrep_pairs.values(),
        "actual_mssm_one_higgs_pair_without_triplets": [4, 1] in per_irrep_pairs.values(),
    }
