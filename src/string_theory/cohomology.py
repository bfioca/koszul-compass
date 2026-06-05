"""pyCICY-backed line-bundle cohomology helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Any


def ensure_pycicy_compat() -> None:
    """Patch pyCICY legacy access patterns for modern SymPy/NumPy."""

    import numpy as np
    import sympy as sp

    if not hasattr(sp, "numbers"):
        sp.numbers = sp.core.numbers
    if not hasattr(np, "int"):
        np.int = int


def pycicy_config(conf: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Convert Oxford degree-only rows to pyCICY rows `[ambient_dim, degrees...]`."""

    return tuple(tuple([sum(row) - 1, *row]) for row in conf)


@lru_cache(maxsize=256)
def make_pycicy(config: tuple[tuple[int, ...], ...]):
    ensure_pycicy_compat()
    from pyCICY import CICY

    return CICY([list(row) for row in config])


def line_cohomology(conf: list[list[int]], line_bundle: list[int]) -> list[int]:
    import numpy as np

    manifold = make_pycicy(pycicy_config(conf))
    original_array = np.array

    def legacy_safe_array(*args, **kwargs):
        try:
            return original_array(*args, **kwargs)
        except ValueError as error:
            if "inhomogeneous shape" not in str(error) or "dtype" in kwargs:
                raise
            return original_array(*args, dtype=object, **kwargs)

    # pyCICY has a legacy logging path that calls np.array on ragged polynomial
    # degree tables. Modern NumPy raises there before the actual map rank logic.
    np.array = legacy_safe_array
    try:
        cohomology = manifold.line_co(line_bundle)
    finally:
        np.array = original_array
    return [int(round(float(x))) for x in cohomology]


def euler_from_cohomology(cohomology: list[int]) -> int:
    return sum(((-1) ** degree) * value for degree, value in enumerate(cohomology))


def bundle_line_summands(matrix: list[list[int]]) -> list[list[int]]:
    cols = len(matrix[0]) if matrix else 0
    return [[row[col] for row in matrix] for col in range(cols)]


def wedge2_line_summands(matrix: list[list[int]]) -> list[list[int]]:
    cols = len(matrix[0]) if matrix else 0
    rows = len(matrix)
    return [
        [matrix[row][a] + matrix[row][b] for row in range(rows)]
        for a in range(cols)
        for b in range(a + 1, cols)
    ]


def trivial_summand_indices(matrix: list[list[int]]) -> list[int]:
    rows = len(matrix)
    return [
        index
        for index, column in enumerate(zip(*matrix))
        if list(column) == [0] * rows
    ]


def line_bundle_sum_quality_diagnostic(
    *,
    matrix: list[list[int]],
    v_cohomology: list[int],
    v_dual_cohomology: list[int],
) -> dict[str, Any]:
    """Record regularity diagnostics that old Oxford scans often filtered on."""

    trivial_indices = trivial_summand_indices(matrix)
    return {
        "trivial_summand_indices": trivial_indices,
        "trivial_summand_count": len(trivial_indices),
        "has_trivial_summand": bool(trivial_indices),
        "h0_v": v_cohomology[0],
        "h0_v_dual": v_dual_cohomology[0],
        "has_bundle_global_sections": v_cohomology[0] > 0
        or v_dual_cohomology[0] > 0,
        "regular_nontrivial_summand_scan_style": (
            not trivial_indices
            and v_cohomology[0] == 0
            and v_dual_cohomology[0] == 0
        ),
        "interpretation": (
            "trivial summands/global sections are mathematically checkable but "
            "may imply enhanced structure group or gauge-sector caveats relative "
            "to regular SU(5) line-bundle scan assumptions"
        ),
    }


def dual(line_bundle: list[int]) -> list[int]:
    return [-x for x in line_bundle]


def sum_cohomologies(items: list[list[int]]) -> list[int]:
    if not items:
        return [0, 0, 0, 0]
    return [sum(item[i] for item in items) for i in range(4)]


def cohomology_record(conf: list[list[int]], line_bundle: list[int]) -> dict[str, Any]:
    cohomology = line_cohomology(conf, line_bundle)
    return {
        "line_bundle": line_bundle,
        "cohomology": cohomology,
        "euler": euler_from_cohomology(cohomology),
    }


def su5_upstairs_spectrum_checks(
    *,
    symmetry_order: int,
    v_cohomology: list[int],
    v_dual_cohomology: list[int],
    wedge2_v_cohomology: list[int],
    wedge2_v_dual_cohomology: list[int],
) -> dict[str, Any]:
    """Classify the upstairs SU(5) GUT spectrum from bundle cohomologies.

    In the standard heterotic SU(5) line-bundle setup:
    - `H^1(X,V)` counts upstairs 10 multiplets.
    - `H^1(X,V*)` counts upstairs anti-10 multiplets.
    - `H^1(X,wedge^2 V)` counts upstairs 5bar-type multiplets.
    - `H^1(X,wedge^2 V*)` counts upstairs 5-type multiplets.

    Existing Oxford GUT models are expected to have no anti-10s and net
    three-generation chirality after quotienting by `|Gamma|`.
    """

    tens = v_cohomology[1]
    anti_tens = v_dual_cohomology[1]
    fivebars = wedge2_v_cohomology[1]
    fives = wedge2_v_dual_cohomology[1]
    expected = 3 * symmetry_order
    return {
        "upstairs_10": tens,
        "upstairs_anti_10": anti_tens,
        "upstairs_5bar": fivebars,
        "upstairs_5": fives,
        "net_10_chirality": tens - anti_tens,
        "net_5bar_chirality": fivebars - fives,
        "expected_upstairs_chirality": expected,
        "higgs_pair_candidates_upstairs": fives,
        "checks": {
            "three_family_10_chirality": tens - anti_tens == expected,
            "three_family_5bar_chirality": fivebars - fives == expected,
        },
        "diagnostics": {
            "no_anti_10": anti_tens == 0,
            "has_higgs_pair_candidate": fives > 0,
        },
    }


def free_quotient_regular_character_constraints(
    *, group_order: int, h1: int, h2: int
) -> dict[str, Any]:
    """Character constraints from Lefschetz for a free finite quotient.

    For an equivariant bundle over a freely acting group, the non-identity
    equivariant Euler traces vanish. For a quotient group of order `g`, this
    means the virtual representation `H^1 - H^2` must be `net/g` copies of the
    regular representation, when `net = h1 - h2` is divisible by `g`.

    This does not construct the representation. It records the constraints any
    equivariant lift must satisfy. If one cohomology side vanishes, the actual
    nonzero cohomology representation is forced to be regular.
    """

    net = h1 - h2
    divisible = net % group_order == 0
    per_character = net // group_order if divisible else None
    if per_character is None:
        h1_bounds = None
        h2_bounds = None
    elif per_character >= 0:
        h1_bounds = [per_character, per_character + h2]
        h2_bounds = [0, h2]
    else:
        h1_bounds = [0, h1]
        h2_bounds = [-per_character, -per_character + h1]

    forced_h1_regular_multiplicity = (
        per_character if divisible and h2 == 0 and per_character is not None and per_character >= 0 else None
    )
    forced_h2_regular_multiplicity = (
        -per_character if divisible and h1 == 0 and per_character is not None and per_character <= 0 else None
    )
    return {
        "group_order": group_order,
        "h1": h1,
        "h2": h2,
        "net_h1_minus_h2": net,
        "virtual_character_regular_by_free_lefschetz_if_lift_exists": divisible,
        "regular_virtual_multiplicity": per_character,
        "h1_multiplicity_per_character_bounds": h1_bounds,
        "h2_multiplicity_per_character_bounds": h2_bounds,
        "actual_h1_representation_forced_regular_multiplicity": forced_h1_regular_multiplicity,
        "actual_h2_representation_forced_regular_multiplicity": forced_h2_regular_multiplicity,
        "actual_representation_underdetermined": forced_h1_regular_multiplicity is None
        and forced_h2_regular_multiplicity is None,
    }


def regular_virtual_character_envelope(
    *, group_order: int, h1: int, h2: int, sample_limit: int = 12
) -> dict[str, Any]:
    """Enumerate per-character spectrum possibilities from virtual regularity.

    If `H^1 - H^2 = m * regular`, then for each character `chi_i` the
    multiplicities satisfy `a_i - b_i = m`, `sum a_i = h1`, and `sum b_i = h2`.
    This envelope ignores the actual cohomology action; it records what is
    possible before that representation is computed.
    """

    constraints = free_quotient_regular_character_constraints(
        group_order=group_order,
        h1=h1,
        h2=h2,
    )
    regular_multiplicity = constraints["regular_virtual_multiplicity"]
    if regular_multiplicity is None:
        return {
            **constraints,
            "per_character_pairs": [],
            "allows_exact_three_family_no_vectorlike_pair": False,
        }

    pairs = [
        [regular_multiplicity + vectorlike, vectorlike]
        for vectorlike in range(h2 + 1)
        if regular_multiplicity + vectorlike >= 0
    ]
    return {
        **constraints,
        "per_character_pair_rule": "[regular_virtual_multiplicity + q, q]",
        "per_character_pairs": pairs,
        "sample_pair_distributions": [
            {
                "h1_per_character": [regular_multiplicity + q for q in distribution],
                "h2_per_character": list(distribution),
            }
            for distribution in _bounded_weak_compositions(h2, group_order, sample_limit)
        ],
        "allows_exact_three_family_no_vectorlike_pair": [3, 0] in pairs,
    }


def _bounded_weak_compositions(total: int, parts: int, limit: int) -> list[tuple[int, ...]]:
    out: list[tuple[int, ...]] = []

    def rec(remaining: int, slots: int, prefix: tuple[int, ...]) -> None:
        if len(out) >= limit:
            return
        if slots == 1:
            out.append((*prefix, remaining))
            return
        for value in range(remaining + 1):
            rec(remaining - value, slots - 1, (*prefix, value))
            if len(out) >= limit:
                return

    rec(total, parts, ())
    return out


def su5_z2xz2_wilson_line_envelope(
    *,
    v_cohomology: list[int],
    wedge2_v_cohomology: list[int],
    sample_higgs_pair_counts: int = 3,
) -> dict[str, Any]:
    """Refined SU(5)-breaking envelope for a `Z2 x Z2` quotient.

    The CICY 7484 free order-four option has group structure `Z2 x Z2`.
    A simple SU(5) Wilson line may assign the fundamental `5` trivial
    character on the color triplet and a nontrivial order-two character on the
    weak doublet. The determinant condition holds because the weak character
    squares to one.

    This is still an envelope: it enumerates character distributions compatible
    with virtual regularity, but it does not compute the actual group action on
    cohomology.
    """

    characters = ["1", "a", "b", "ab"]
    nontrivial_characters = characters[1:]
    ten = free_quotient_regular_character_constraints(
        group_order=4,
        h1=v_cohomology[1],
        h2=v_cohomology[2],
    )
    fivebar = free_quotient_regular_character_constraints(
        group_order=4,
        h1=wedge2_v_cohomology[1],
        h2=wedge2_v_cohomology[2],
    )
    ten_forced_regular_three = (
        ten["actual_h1_representation_forced_regular_multiplicity"] == 3
    )
    fivebar_virtual_three = fivebar["regular_virtual_multiplicity"] == 3
    h2_fivebar = wedge2_v_cohomology[2]

    possible_higgs_pair_counts = (
        list(range(h2_fivebar + 1)) if fivebar_virtual_three else []
    )
    sample_counts = possible_higgs_pair_counts[: sample_higgs_pair_counts + 1]
    examples = []
    if fivebar_virtual_three:
        for weak_character in nontrivial_characters:
            for higgs_pairs in sample_counts:
                h2_distribution = {character: 0 for character in characters}
                h2_distribution[weak_character] = higgs_pairs
                remainder_targets = [
                    character
                    for character in characters
                    if character not in {"1", weak_character}
                ]
                h2_distribution[remainder_targets[-1]] = h2_fivebar - higgs_pairs
                h1_distribution = {
                    character: 3 + h2_distribution[character]
                    for character in characters
                }
                examples.append(
                    {
                        "weak_doublet_character": weak_character,
                        "higgs_doublet_pair_count": higgs_pairs,
                        "H1_wedge2V_multiplicity_by_character": h1_distribution,
                        "H2_wedge2V_multiplicity_by_character": h2_distribution,
                        "projected_5bar_matter": {
                            "dbar_triplets": 3,
                            "lepton_doublets": 3 + higgs_pairs,
                        },
                        "projected_5_matter": {
                            "triplets": 0,
                            "doublets": higgs_pairs,
                        },
                        "colored_triplet_vectorlike_pairs": 0,
                    }
                )

    allows_exact_chiral_no_pair = (
        ten_forced_regular_three and 0 in possible_higgs_pair_counts
    )
    allows_one_higgs_pair = ten_forced_regular_three and 1 in possible_higgs_pair_counts
    return {
        "scope": (
            "conditional Z2xZ2 Wilson-line spectrum envelope; actual cohomology "
            "character decomposition not constructed"
        ),
        "quotient_group_structure": [2, 2],
        "character_labels": characters,
        "su5_fundamental_character_split": [
            {
                "color_triplet_character": "1",
                "weak_doublet_character": weak_character,
                "determinant_condition_satisfied": True,
            }
            for weak_character in nontrivial_characters
        ],
        "ten_sector_exact_three_families_for_any_nontrivial_weak_character": (
            ten_forced_regular_three
        ),
        "fivebar_sector_virtual_regular_multiplicity_three": fivebar_virtual_three,
        "possible_higgs_doublet_pair_counts_without_colored_triplet_pairs": (
            possible_higgs_pair_counts
        ),
        "allows_exact_chiral_sm_matter_without_5_vectorlike_pairs": (
            allows_exact_chiral_no_pair
        ),
        "allows_mssm_matter_plus_one_higgs_pair_without_colored_triplet_pairs": (
            allows_one_higgs_pair
        ),
        "sample_character_distributions": examples,
        "actual_wilson_line_spectrum_proven": False,
    }


def su5_order4_descent_constraints(
    *,
    symmetry_order: int,
    v_cohomology: list[int],
    wedge2_v_cohomology: list[int],
    quotient_group_structure: list[int] | None = None,
) -> dict[str, Any]:
    """Conditional downstairs SU(5)-sector constraints for an order-four quotient."""

    ten = free_quotient_regular_character_constraints(
        group_order=symmetry_order,
        h1=v_cohomology[1],
        h2=v_cohomology[2],
    )
    fivebar = free_quotient_regular_character_constraints(
        group_order=symmetry_order,
        h1=wedge2_v_cohomology[1],
        h2=wedge2_v_cohomology[2],
    )
    fivebar_envelope = regular_virtual_character_envelope(
        group_order=symmetry_order,
        h1=wedge2_v_cohomology[1],
        h2=wedge2_v_cohomology[2],
    )
    result = {
        "scope": "conditional on a free order-four equivariant lift; Wilson-line cohomology action not constructed",
        "ten_sector": ten,
        "fivebar_sector": fivebar,
        "fivebar_sector_representation_envelope": fivebar_envelope,
        "checks": {
            "ten_sector_forced_three_families_per_character": ten[
                "actual_h1_representation_forced_regular_multiplicity"
            ]
            == 3,
            "fivebar_sector_net_three_families_per_character": fivebar[
                "regular_virtual_multiplicity"
            ]
            == 3,
            "fivebar_sector_allows_three_families_no_vectorlike_pair": fivebar_envelope[
                "allows_exact_three_family_no_vectorlike_pair"
            ],
        },
        "full_wilson_line_spectrum_proven": False,
    }
    if quotient_group_structure == [2, 2]:
        result["z2xz2_wilson_line_spectrum_envelope"] = (
            su5_z2xz2_wilson_line_envelope(
                v_cohomology=v_cohomology,
                wedge2_v_cohomology=wedge2_v_cohomology,
            )
        )
    return result
