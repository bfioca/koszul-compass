"""Exact generic equivariant Koszul calculation for the SMS202 CICY7487 control.

Only the recorded codimension-two (P1)^5 presentation is supported. Cohomology
is computed in Laurent Cech bases, with the chart-exchange sign on H1(P1).
Published dimensions and characters are not inputs to this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.parsing.mathematica import parse_mathematica

from .mathematica import extract_assignment, parse_mathematica_expr
from .sms202 import parse_record, parse_simple_fields, split_top_level


BITS = ((0, 0), (1, 0), (0, 1), (1, 1))
VARIABLES = sp.symbols("x1:11")


class GeometryGap(ValueError):
    """A calculation outside the independently implemented mathematical scope."""


@dataclass(frozen=True)
class Geometry:
    conf: tuple[tuple[int, ...], ...]
    coordinates: tuple[sp.Matrix, ...]
    equations: tuple[sp.Matrix, ...]
    polynomial_basis: tuple[tuple[sp.Poly, ...], ...]
    c2: tuple[int, ...]


def load_geometry(path: Path, symmetry_number: int = 3) -> Geometry:
    entry = extract_assignment(path.read_text(), "cicy_geometry").strip()
    record = parse_record(entry, source_key=(7487,), index=0)
    fields = parse_simple_fields(record, ("Num", "Conf", "C2"))
    if fields["Num"] != 7487 or fields["Conf"] != [
        [0, 2], [1, 1], [1, 1], [1, 1], [1, 1]
    ]:
        raise GeometryGap("expected the recorded CICY7487 (P1)^5 configuration")
    options = split_top_level(record.fields["Symmetries"][1:-1])
    option = split_top_level(options[symmetry_number - 1][1:-1])
    coordinate_data = parse_mathematica_expr(option[1])
    if option[0] != "True" or coordinate_data[1] != [4, 2]:
        raise GeometryGap("expected the recorded free order-four action")
    if parse_mathematica_expr(option[2]) != [True, [2, 2]]:
        raise GeometryGap("expected Z2 x Z2")
    coordinates = tuple(sp.Matrix(m) for m in coordinate_data[0])
    equations = tuple(sp.Matrix(m) for m in parse_mathematica_expr(option[3]))
    basis = tuple(
        tuple(sp.Poly(p, *VARIABLES, domain=sp.ZZ) for p in row)
        for row in parse_mathematica(option[4])
        if any(p != 0 for p in row)
    )
    geometry = Geometry(
        tuple(tuple(row) for row in fields["Conf"]),
        coordinates, equations, basis, tuple(fields["C2"]),
    )
    validate_geometry(geometry)
    return geometry


def validate_geometry(geometry: Geometry) -> None:
    if len(geometry.coordinates) != 2 or len(geometry.equations) != 2:
        raise GeometryGap("expected two generators")
    for matrix in geometry.coordinates:
        if matrix.shape != (10, 10):
            raise GeometryGap("coordinate matrix must be 10 by 10")
        for i in range(10):
            support = [(j, matrix[i, j]) for j in range(10) if matrix[i, j]]
            if len(support) != 1 or support[0][1] not in (-1, 1):
                raise GeometryGap("only signed monomial coordinate actions supported")
            if support[0][0] // 2 != i // 2:
                raise GeometryGap("ambient-factor permutations not implemented")
        if matrix * matrix != sp.eye(10):
            raise GeometryGap("generator must square to the identity")
    for matrix in geometry.equations:
        if matrix.shape != (2, 2) or not matrix.is_diagonal():
            raise GeometryGap("only diagonal equation actions supported")
        if any(matrix[i, i] not in (-1, 1) for i in range(2)):
            raise GeometryGap("equation action must have signs on its diagonal")
    for row in geometry.polynomial_basis:
        if len(row) != 2:
            raise GeometryGap("polynomial basis must consist of equation pairs")
        for equation, polynomial in enumerate(row):
            for exponent, _ in polynomial.terms():
                if polynomial.is_zero:
                    continue
                degree = [exponent[2*j] + exponent[2*j+1] for j in range(5)]
                if degree != [r[equation] for r in geometry.conf]:
                    raise GeometryGap("polynomial basis has wrong multidegree")
            for generator, matrix in enumerate(geometry.coordinates):
                substitution = {
                    VARIABLES[i]: sum(matrix[i, j] * VARIABLES[j] for j in range(10))
                    for i in range(10)
                }
                transformed = sp.Poly(
                    polynomial.as_expr().xreplace(substitution), *VARIABLES
                )
                if transformed != geometry.equations[generator][equation, equation] * polynomial:
                    raise GeometryGap("polynomial basis violates equation equivariance")
    polynomial_family_certificate(geometry)


def ambient_basis(degree: tuple[int, ...]) -> tuple[int, list[tuple[int, ...]]]:
    if -1 in degree:
        return -1, []
    factors = [
        [(a, k-a) for a in (range(k+1) if k >= 0 else range(k+1, 0))]
        for k in degree
    ]
    return sum(k <= -2 for k in degree), [
        tuple(value for pair in entry for value in pair) for entry in product(*factors)
    ]


def ambient_action(
    basis: list[tuple[int, ...]], degree: tuple[int, ...], matrix: sp.Matrix
) -> sp.Matrix:
    """Pull back Laurent representatives, including Cech cover orientation."""
    lookup = {exponent: i for i, exponent in enumerate(basis)}
    result = sp.zeros(len(basis))
    rows = [next((j, int(matrix[i, j])) for j in range(10) if matrix[i, j]) for i in range(10)]
    cover_sign = (-1) ** sum(
        degree[j] <= -2 and rows[2*j][0] == 2*j+1 for j in range(5)
    )
    for column, exponent in enumerate(basis):
        target = [0] * 10
        scalar = cover_sign
        for power, (index, sign) in zip(exponent, rows):
            target[index] += power
            if sign == -1 and power % 2:
                scalar *= -1
        result[lookup[tuple(target)], column] = scalar
    return result


def character_multiplicities(actions: tuple[sp.Matrix, sp.Matrix]) -> list[int]:
    a, b = actions
    n = a.rows
    if a*a != sp.eye(n) or b*b != sp.eye(n) or a*b != b*a:
        raise GeometryGap("ambient lift does not define a Z2 x Z2 representation")
    traces = (n, sp.trace(a), sp.trace(b), sp.trace(a*b))
    values = [
        (traces[0] + (-1)**u * traces[1] + (-1)**v * traces[2]
         + (-1)**(u+v) * traces[3]) / sp.Integer(4)
        for u, v in BITS
    ]
    if any(not x.is_Integer or x < 0 for x in values):
        raise GeometryGap("invalid character multiplicities")
    return [int(x) for x in values]


def projector(actions: tuple[sp.Matrix, sp.Matrix], bits: tuple[int, int]) -> sp.Matrix:
    a, b = actions
    u, v = bits
    return (sp.eye(a.rows) + (-1)**u*a) * (sp.eye(a.rows) + (-1)**v*b) / 4


def polynomial_family_certificate(geometry: Geometry) -> list[dict[str, Any]]:
    certificate = []
    total_expected = 0
    full_columns = []
    for equation in range(2):
        degree = tuple(row[equation] for row in geometry.conf)
        _, basis = ambient_basis(degree)
        actions = tuple(ambient_action(basis, degree, g) for g in geometry.coordinates)
        bits = tuple(0 if g[equation, equation] == 1 else 1 for g in geometry.equations)
        expected_dimension = character_multiplicities(actions)[BITS.index(bits)]
        coefficients = sp.Matrix([
            [row[equation].coeff_monomial(exponent) for row in geometry.polynomial_basis]
            for exponent in basis
        ])
        full_columns.append(coefficients)
        if coefficients.rank() != expected_dimension:
            raise GeometryGap("recorded polynomial family does not span the equation eigenspace")
        certificate.append({
            "equation": equation, "degree": list(degree), "character_bits": list(bits),
            "ambient_section_dimension": len(basis), "equivariant_family_dimension": expected_dimension,
            "recorded_basis_rank": int(coefficients.rank()),
        })
        total_expected += expected_dimension
    if sp.Matrix.vstack(*full_columns).rank() != total_expected:
        raise GeometryGap("recorded tuples do not span the joint equation family")
    return certificate


def koszul_levels(geometry: Geometry, charge: tuple[int, ...]) -> dict:
    levels: dict = {}
    for r in range(3):
        for origin in combinations(range(2), r):
            degree = tuple(charge[j] - sum(geometry.conf[j][i] for i in origin) for j in range(5))
            q, basis = ambient_basis(degree)
            if not basis:
                continue
            actions = tuple(
                ambient_action(basis, degree, matrix)
                * sp.prod(geometry.equations[g][i, i] for i in origin)
                for g, matrix in enumerate(geometry.coordinates)
            )
            level = levels.setdefault((r, q), {"terms": [], "basis": [], "actions": []})
            level["terms"].append({
                "origin": list(origin), "degree": list(degree), "dimension": len(basis),
                "characters": character_multiplicities(actions),
            })
            level["basis"].extend((origin, exponent) for exponent in basis)
            level["actions"].append(actions)
    for level in levels.values():
        level["actions"] = tuple(sp.diag(*(pair[g] for pair in level["actions"])) for g in range(2))
        level["characters"] = character_multiplicities(level["actions"])
    return levels


def multiplication_matrix(source: dict, target: dict, polynomials: tuple[sp.Poly, ...]) -> sp.Matrix:
    lookup = {entry: i for i, entry in enumerate(target["basis"])}
    result = sp.zeros(len(lookup), len(source["basis"]))
    for column, (origin, exponent) in enumerate(source["basis"]):
        for position, equation in enumerate(origin):
            remaining = origin[:position] + origin[position+1:]
            for monomial, coefficient in polynomials[equation].terms():
                if not coefficient:
                    continue
                output = tuple(x+y for x, y in zip(exponent, monomial))
                row = lookup.get((remaining, output))
                if row is not None:
                    result[row, column] += (-1)**position * coefficient
    return result


def minor_witness(matrix: sp.Matrix, rank: int) -> dict[str, Any]:
    if not rank:
        return {"rows": [], "columns": [], "determinant": 1}
    columns = list(matrix.rref()[1])
    rows = list(matrix[:, columns].T.rref()[1])
    determinant = matrix.extract(rows, columns).det()
    if len(rows) != rank or determinant == 0:
        raise GeometryGap("failed to produce an exact nonzero minor")
    return {"rows": rows, "columns": columns, "determinant": int(determinant)}


def subspace_characters(vectors: list[sp.Matrix], actions: tuple[sp.Matrix, sp.Matrix]) -> list[int]:
    if not vectors:
        return [0]*4
    basis = sp.Matrix.hstack(*vectors)
    restricted = []
    for action in actions:
        solution, parameters = basis.gauss_jordan_solve(action*basis)
        if parameters.rows:
            raise GeometryGap("subspace action is not uniquely determined")
        if basis*solution != action*basis:
            raise GeometryGap("subspace is not invariant")
        restricted.append(solution)
    return character_multiplicities(tuple(restricted))


def compute_line(geometry: Geometry, charge: tuple[int, ...]) -> dict[str, Any]:
    """Compute characters on a nonempty Zariski-open set of invariant equations."""
    if len(charge) != 5:
        raise GeometryGap("expected five ambient charges")
    levels = koszul_levels(geometry, charge)
    e2 = {key: list(level["characters"]) for key, level in levels.items()}
    maps = []
    matrices = {}
    coefficients = list(range(1, len(geometry.polynomial_basis)+1))
    for (r, q), source in levels.items():
        target = levels.get((r-1, q))
        if target is None:
            continue
        # Check the entire polynomial family, not merely the integer witness.
        family = [multiplication_matrix(source, target, row) for row in geometry.polynomial_basis]
        for matrix in family:
            for a, b in zip(source["actions"], target["actions"]):
                if b*matrix != matrix*a:
                    raise GeometryGap("Koszul multiplication is not equivariant")
        matrix = sp.zeros(len(target["basis"]), len(source["basis"]))
        for coefficient, component in zip(coefficients, family):
            matrix += coefficient * component
        ranks = [int((matrix * projector(source["actions"], bits)).rank()) for bits in BITS]
        upper = [min(a, b) for a, b in zip(source["characters"], target["characters"])]
        if ranks != upper:
            raise GeometryGap(f"integer witness does not saturate character rank bounds for {charge}")
        kernel = subspace_characters(matrix.nullspace(), source["actions"])
        # The annihilator of the image computes the dual cokernel. All Z2 x Z2
        # irreducibles are self-dual; transpose is inverse-transpose here.
        cokernel = subspace_characters(matrix.T.nullspace(), tuple(a.T for a in target["actions"]))
        if kernel != [a-b for a, b in zip(source["characters"], ranks)]:
            raise GeometryGap("direct kernel action disagrees with character subtraction")
        if cokernel != [a-b for a, b in zip(target["characters"], ranks)]:
            raise GeometryGap("direct cokernel action disagrees with character subtraction")
        for i, rank in enumerate(ranks):
            e2[(r, q)][i] -= rank
            e2[(r-1, q)][i] -= rank
        matrices[(r, q)] = matrix
        maps.append({
            "source": [r, q], "target": [r-1, q],
            "shape": list(matrix.shape), "rank": sum(ranks),
            "source_characters": source["characters"],
            "target_characters": target["characters"], "image_characters": ranks,
            "kernel_characters": kernel, "cokernel_characters": cokernel,
            "kernel_cokernel_actions_independently_restricted": True,
            "family_equivariance_verified": True,
            "generic_rank_upper_bounds_saturated": True,
            "nonzero_minor": minor_witness(matrix, sum(ranks)),
            "witness_matrix": [list(map(int, matrix.row(i))) for i in range(matrix.rows)],
        })
    for (r, q), matrix in matrices.items():
        following = matrices.get((r-1, q))
        if following is not None and following*matrix != sp.zeros(following.rows, matrix.cols):
            raise GeometryGap("d1 squared is nonzero")
    if any(x < 0 for chars in e2.values() for x in chars):
        raise GeometryGap("inconsistent E2 dimensions")
    for (r, q), characters in e2.items():
        if r == 2 and sum(characters) and sum(e2.get((0, q-1), [])):
            raise GeometryGap("a potentially nonzero d2 requires an unimplemented higher map")
    cohomology = [[0]*4 for _ in range(4)]
    for (r, q), characters in e2.items():
        if sum(characters) and not 0 <= q-r <= 3:
            raise GeometryGap("cohomology outside the CY3 degree range")
        if 0 <= q-r <= 3:
            cohomology[q-r] = [a+b for a, b in zip(cohomology[q-r], characters)]
    return {
        "charge": list(charge), "cohomology_characters": cohomology,
        "dimensions": [sum(row) for row in cohomology],
        "e1": [{"r": r, "q": q, "characters": level["characters"], "terms": level["terms"]}
               for (r, q), level in sorted(levels.items())],
        "maps": maps, "e2_degenerates_by_support": True,
        "coefficient_witness": coefficients,
    }


def reconstruct(geometry: Geometry, line_sum: list[list[int]]) -> dict[str, Any]:
    if len(line_sum) != 5 or any(len(row) != 5 for row in line_sum):
        raise GeometryGap("expected five line-bundle columns in five ambient rows")
    columns = list(zip(*line_sum))
    pairs = list(combinations(range(5), 2))
    sectors = {
        "V": [(f"L{a+1}", k) for a, k in enumerate(columns)],
        "wedge2": [(f"L{a+1}L{b+1}", tuple(x+y for x, y in zip(columns[a], columns[b]))) for a, b in pairs],
        "singlets": [(f"L{a+1}/L{b+1}", tuple(x-y for x, y in zip(columns[a], columns[b]))) for a, b in pairs],
    }
    cache = {}

    def result(charge):
        if charge not in cache:
            cache[charge] = compute_line(geometry, charge)
        return cache[charge]

    canonical = result((0,)*5)
    if canonical["cohomology_characters"] != [[1, 0, 0, 0], [0]*4, [0]*4, [1, 0, 0, 0]]:
        raise GeometryGap("the action on H3(O_X) is not trivial")
    output = {"sectors": {}, "structure_sheaf": canonical,
              "polynomial_family": polynomial_family_certificate(geometry)}
    for name, entries in sectors.items():
        output["sectors"][name] = []
        for label, charge in entries:
            direct = result(charge)
            dual = result(tuple(-x for x in charge))
            if direct["cohomology_characters"] != list(reversed(dual["cohomology_characters"])):
                raise GeometryGap(f"independent Serre-dual calculation disagrees for {label}")
            output["sectors"][name].append({"label": label, **direct, "serre_dual_verified": True})
    output["distinct_line_calculations"] = len(cache)
    output["dual_calculations"] = [
        {"label": label, **result(tuple(-x for x in charge))}
        for entries in sectors.values() for label, charge in entries
    ]
    return output


def compare_published(reconstruction: dict, fields: dict) -> dict[str, bool]:
    """Compare only after reconstruction; these values never choose any map."""
    checks = {}
    for sector, dimension_field, character_field in (
        ("V", "Coh", "GCoh"), ("wedge2", "Coh2", "GCoh2"),
        ("singlets", "CohSing", "GCohSing"),
    ):
        rows = reconstruction["sectors"][sector]
        checks[dimension_field] = [r["dimensions"] for r in rows] == fields[dimension_field]
        checks[character_field] = [r["cohomology_characters"] for r in rows] == fields[character_field]
    return checks
