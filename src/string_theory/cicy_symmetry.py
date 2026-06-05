"""Lightweight CICY symmetry extraction for targeted certification reports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .cicy import sorted_matrix_key
from .cicylist import split_top_level_entries
from .novelty import permute_rows


def split_top_level_items(text: str) -> list[str]:
    """Split a Mathematica list body on commas outside nested structures."""

    items: list[str] = []
    start = 0
    brace_depth = 0
    bracket_depth = 0
    paren_depth = 0
    for pos, char in enumerate(text):
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth -= 1
        elif char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth -= 1
        elif (
            char == ","
            and brace_depth == 0
            and bracket_depth == 0
            and paren_depth == 0
        ):
            items.append(text[start:pos].strip())
            start = pos + 1
    items.append(text[start:].strip())
    return items


def _inner_list(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"expected Mathematica list, got {text[:80]!r}")
    return text[start + 1 : end]


def _extract_braced_value_after(text: str, marker: str) -> str:
    marker_pos = text.find(marker)
    if marker_pos < 0:
        raise ValueError(f"marker {marker!r} not found")
    start = text.find("{", marker_pos)
    if start < 0:
        raise ValueError(f"no braced value after {marker!r}")
    depth = 0
    for pos in range(start, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start : pos + 1]
    raise ValueError(f"unterminated braced value after {marker!r}")


def extract_cicy_entry(path: str | Path, cicy_number: int) -> str:
    text = Path(path).read_text(encoding="utf-8")
    for entry in split_top_level_entries(text):
        if re.search(rf"\bNum\s*->\s*{cicy_number}\b", entry):
            return entry
    raise ValueError(f"CICY {cicy_number} not found in {path}")


def _row_to_nonzero_columns(row_text: str) -> list[int]:
    entries = split_top_level_items(_inner_list(row_text))
    return [index for index, item in enumerate(entries) if item.strip() != "0"]


def _matrix_nonzero_columns_by_row(matrix_text: str) -> list[list[int]]:
    rows = split_top_level_items(_inner_list(matrix_text))
    return [_row_to_nonzero_columns(row) for row in rows]


def _block_index(index: int, block_sizes: list[int]) -> int:
    offset = 0
    for block, size in enumerate(block_sizes):
        if offset <= index < offset + size:
            return block
        offset += size
    raise ValueError(f"index {index} outside block sizes {block_sizes}")


def infer_ambient_row_permutation(matrix_text: str, block_sizes: list[int]) -> tuple[int, ...]:
    """Infer the ambient divisor-row action from a monomial coordinate matrix.

    The returned tuple maps each output ambient coordinate block to the input
    block from which its nonzero entries are drawn. This is the induced action
    relevant to line-bundle charge rows.
    """

    row_support = _matrix_nonzero_columns_by_row(matrix_text)
    total = sum(block_sizes)
    if len(row_support) != total:
        raise ValueError(f"expected {total} coordinate rows, got {len(row_support)}")

    permutation: list[int] = []
    output_start = 0
    for block_size in block_sizes:
        input_blocks: set[int] = set()
        for row_index in range(output_start, output_start + block_size):
            if len(row_support[row_index]) != 1:
                raise ValueError(f"row {row_index} is not monomial: {row_support[row_index]}")
            input_blocks.add(_block_index(row_support[row_index][0], block_sizes))
        if len(input_blocks) != 1:
            raise ValueError(f"output block mixes input blocks: {sorted(input_blocks)}")
        permutation.append(next(iter(input_blocks)))
        output_start += block_size
    return tuple(permutation)


def cicy_7484_symmetry_options(cicylist_path: str | Path) -> list[dict[str, Any]]:
    """Summarize raw `cicylist.m` symmetry options for CICY 7484."""

    entry = extract_cicy_entry(cicylist_path, 7484)
    symmetries = _extract_braced_value_after(entry, "Symmetries ->")
    options = split_top_level_items(_inner_list(symmetries))
    block_sizes = [2, 2, 4]

    summaries: list[dict[str, Any]] = []
    for option_index, option_text in enumerate(options):
        items = split_top_level_items(_inner_list(option_text))
        free_action = items[0] == "True"

        coordinate_data = split_top_level_items(_inner_list(items[1]))
        generator_matrices = split_top_level_items(_inner_list(coordinate_data[0]))
        group_descriptor = [int(value) for value in re.findall(r"-?\d+", coordinate_data[1])]
        if len(group_descriptor) != 2:
            raise ValueError(f"unexpected group descriptor {coordinate_data[1]!r}")
        quotient_group_structure = [int(value) for value in re.findall(r"-?\d+", items[2])]

        row_permutations = [
            infer_ambient_row_permutation(generator_matrix, block_sizes)
            for generator_matrix in generator_matrices
        ]
        summaries.append(
            {
                "option_index": option_index,
                "free_action": free_action,
                "quotient_order": group_descriptor[0],
                "generator_count": group_descriptor[1],
                "quotient_group_structure": quotient_group_structure,
                "ambient_coordinate_block_sizes": block_sizes,
                "generator_ambient_row_permutations": [
                    list(permutation) for permutation in row_permutations
                ],
                "all_generators_ambient_row_trivial": all(
                    permutation == tuple(range(len(block_sizes))) for permutation in row_permutations
                ),
            }
        )
    return summaries


def line_bundle_sum_invariant_under_row_permutation(
    matrix: list[list[int]], row_permutation: tuple[int, ...]
) -> bool:
    return sorted_matrix_key(matrix) == sorted_matrix_key(permute_rows(matrix, row_permutation))


def ambient_linearization_certificate(
    matrix: list[list[int]], option: dict[str, Any]
) -> dict[str, Any]:
    """Certify an equivariant lift for row-trivial ambient linear actions.

    The raw CICY symmetry data gives explicit linear coordinate actions on the
    ambient projective factors. If those actions do not permute ambient divisor
    rows, every summand `O(k_1,...,k_m)` is fixed as a divisor class and inherits
    an ambient linearization from the tensor powers of the projective `O(1)`
    bundles. The direct sum can therefore be made equivariant. Because the
    quotient group has order four, it is abelian, so the determinant
    linearization can be adjusted by twisting one summand by a character.
    """

    identity = list(range(len(matrix)))
    row_trivial = all(
        permutation == identity for permutation in option["generator_ambient_row_permutations"]
    )
    summand_count = len(matrix[0]) if matrix else 0
    summand_total_degrees = [
        sum(matrix[row][col] for row in range(len(matrix))) for col in range(summand_count)
    ]
    z2xz2_projective_commutator_scalars = (
        [-1 for _ in matrix]
        if option.get("quotient_group_structure") == [2, 2]
        and row_trivial
        and len(matrix) == 3
        else None
    )
    if z2xz2_projective_commutator_scalars is None:
        commutator_trivial_by_summand = None
        commutator_trivial_on_all_summands = row_trivial
        obstruction = None
    else:
        commutator_trivial_by_summand = [
            total_degree % 2 == 0 for total_degree in summand_total_degrees
        ]
        commutator_trivial_on_all_summands = all(commutator_trivial_by_summand)
        obstruction = None
        if not commutator_trivial_on_all_summands:
            obstruction = (
                "The two Z2xZ2 projective coordinate generators anticommute by "
                "a scalar -1 on each ambient factor; O(k1,k2,k3) linearizes only "
                "when k1+k2+k3 is even for this lift."
            )
    summand_linearizations_exist = row_trivial and commutator_trivial_on_all_summands
    return {
        "scope": "ambient linearized line-bundle-sum lift only",
        "option_index": option["option_index"],
        "free_action": option["free_action"],
        "quotient_order": option["quotient_order"],
        "generator_count": option["generator_count"],
        "quotient_group_structure": option.get("quotient_group_structure"),
        "all_generators_ambient_row_trivial": row_trivial,
        "individual_line_bundle_classes_fixed": row_trivial,
        "summand_count": summand_count,
        "summand_total_degrees": summand_total_degrees,
        "z2xz2_projective_commutator_scalars_by_ambient_factor": (
            z2xz2_projective_commutator_scalars
        ),
        "z2xz2_commutator_trivial_by_summand": commutator_trivial_by_summand,
        "z2xz2_projective_lift_commutator_trivial_on_all_summands": (
            commutator_trivial_on_all_summands
        ),
        "linearization_obstruction": obstruction,
        "ambient_projective_o1_linearizations_available": row_trivial
        and z2xz2_projective_commutator_scalars is None,
        "line_bundle_summand_linearizations_exist": summand_linearizations_exist,
        "direct_sum_equivariant_lift_exists": summand_linearizations_exist,
        "determinant_linearization_can_be_chosen_trivial": summand_linearizations_exist
        and option["quotient_order"] == 4,
        "cohomology_representation_or_wilson_line_action_computed": False,
    }


def cicy_7484_topological_equivariance_report(
    cicylist_path: str | Path, matrix: list[list[int]]
) -> dict[str, Any]:
    """Check topological line-bundle invariance against raw CICY 7484 symmetries.

    This records topological invariance and, for row-trivial ambient projective
    actions, checks whether the projective-lift commutator is trivial on every
    summand. It does not compute the induced representation on bundle
    cohomology or implement a Wilson-line projection.
    """

    options = []
    for option in cicy_7484_symmetry_options(cicylist_path):
        generator_checks = []
        for permutation in option["generator_ambient_row_permutations"]:
            invariant = line_bundle_sum_invariant_under_row_permutation(
                matrix, tuple(permutation)
            )
            generator_checks.append(
                {
                    "ambient_row_permutation": permutation,
                    "line_bundle_sum_invariant_up_to_columns": invariant,
                }
            )
        topologically_compatible = all(
            check["line_bundle_sum_invariant_up_to_columns"] for check in generator_checks
        )
        options.append(
            {
                **option,
                "generator_checks": generator_checks,
                "topological_line_bundle_sum_compatible": topologically_compatible,
                "ambient_linearization_certificate": ambient_linearization_certificate(
                    matrix, option
                )
                if option["free_action"] and topologically_compatible
                else None,
            }
        )

    compatible_free_order_four = [
        option["option_index"]
        for option in options
        if option["free_action"]
        and option["quotient_order"] == 4
        and option["topological_line_bundle_sum_compatible"]
    ]
    linearized_free_order_four = [
        option["option_index"]
        for option in options
        if option["option_index"] in compatible_free_order_four
        and option["ambient_linearization_certificate"] is not None
        and option["ambient_linearization_certificate"]["direct_sum_equivariant_lift_exists"]
        and option["ambient_linearization_certificate"][
            "determinant_linearization_can_be_chosen_trivial"
        ]
    ]
    return {
        "scope": "raw CICY symmetry topological invariance plus ambient linearized lift",
        "cicy": 7484,
        "matrix": matrix,
        "symmetry_options": options,
        "compatible_free_order_four_option_indices": compatible_free_order_four,
        "has_compatible_free_order_four_topological_action": bool(compatible_free_order_four),
        "linearized_free_order_four_option_indices": linearized_free_order_four,
        "equivariant_line_bundle_sum_lift_exists": bool(linearized_free_order_four),
        "wilson_line_representation_on_cohomology_proven": False,
    }
