# SMS202 Model 1710: Geometry-Derived Character Control

**Stopping result: exact match, on the generic smooth free locus of the
recorded invariant family.** All 25 published cohomology-character tables
match the independent calculation. The recorded linearisations and Wilson
line then give three chiral families, no anti-10s, no colored triplet pairs,
and one electroweak Higgs pair. Candidate search remains paused. Operator
classifications and cup/Yukawa calculations are still pending.

## Identity and Provenance

- Publication: Anderson, Gray, Lukas, Palti,
  [Heterotic Line Bundle Standard Models](https://arxiv.org/abs/1202.1757).
- Corpus: [Oxford sms202.m](https://www-thphys.physics.ox.ac.uk/projects/CalabiYau/linebundlemodels/sms202.m).
- Source key: `{7487,4,3}`; source `ModelNumber -> 23`.
- Legacy regex-scout index: `1710`; structured zero-based record index:
  `1811`, among `2113` structurally parsed records.
- Corpus SHA-256:
  `ee7d8d91e63237bd47891fbbb5f3827d9c4e4e82c60644ac23980c684d1ba991`.
- Model fixture: `model_1710_source.m`, unchanged, checked against the existing
  immutable `model_1710_expected.json` and full corpus.
- Geometry fixture: `cicy7487_source.m`, a verbatim complete entry from the
  corpus's `cicys` assignment. Its six symmetries retain their original order.
  Symmetry **3 is one-based**, hence list offset 2; no symmetry was chosen by
  inspecting a resulting spectrum.
- Geometry-entry SHA-256:
  `f5a663e9469ebbb95e1f5f9cf07d6ce51a536f4547f35ea74e30cf5df37ed006`.

`model_1710_geometry_manifest.json` pins the geometry fixture and identities.
`model_1710_geometry_certificate.json` records the reconstructed E1 terms,
exact matrices, rank minors, characters, comparisons, and implementation
hashes. Its verifier recomputes these quantities; it does not read a saved
certificate to establish a pass.

## Conventions and Inputs

The ambient space is `(P1)^5`, with equation degrees
`q1=(0,1,1,1,1)` and `q2=(2,1,1,1,1)`. The five bundle columns are

```text
L1 = ( 1,-1,-1, 1, 0)
L2 = ( 1,-1,-1, 0, 1)
L3 = ( 0, 1, 0,-2, 1)
L4 = ( 0, 0, 1, 1,-2)
L5 = (-2, 1, 1, 0, 0)
```

The group generators act in every P1 factor by `diag(1,-1)` and coordinate
exchange, respectively. Both act on `(p1,p2)` by `diag(1,-1)`. The raw
equivariant equation tuples provide four independent coefficients for `p1`
and twelve for `p2`. Their multidegrees, covariance, linear independence,
and completeness in the appropriate ambient character eigenspaces are
checked directly.

Characters are ordered `[1,a,b,ab]`, with bits
`[(0,0),(1,0),(0,1),(1,1)]` relative to the recorded generator order.
`GCoh`, `GCoh2`, and `GCohSing` describe the natural ambient lift before
the separate `EquivStr` twists. The latter twists only `L4` by `b`.
The Wilson fundamental characters are `1` for the triplet and `b` for
the doublet. Wedge and singlet pairs use lexicographic `a<b`; singlet
rows represent `La tensor Lb*`. Opposite orientations are calculated
separately as a Serre-duality check.

## Independent Calculation

The calculator receives only the geometry and the bundle matrix. Published
cohomology, characters, Higgs counts, and expected spectra do not enter its
map construction or rank choices.

1. Use Bott and Kunneth on each ambient line bundle. For `k>=0`, a P1 basis
   consists of ordinary degree-k monomials. For `k<=-2`, use Laurent Cech
   representatives with both exponents negative and sum k. A factor of
   degree -1 annihilates the ambient cohomology.
2. Pull back these representatives under the coordinate matrices. Exchanging
   the two Cech charts contributes a minus sign in H1. Tensor the result
   with the recorded exterior conormal character.
3. Form `E1^{-r,q}=H^q(A,L tensor wedge^r N*)`, with total degree `q-r`.
   Build d1 by actual polynomial multiplication and projection to the
   Laurent cohomology basis, including the alternating Koszul sign.
4. Check equivariance coefficient-by-coefficient across the entire polynomial
   family. Evaluate all maps at coefficients `1,...,16`, in the order of the
   nonzero recorded polynomial tuples. Exact rational ranks saturate the
   character-by-character dimension bounds. Nonzero minors certify generic
   rank: the determinant polynomial cannot be identically zero.
5. Compute kernel actions by restricting both generators to exact nullspace
   bases. Compute cokernel characters through the dual annihilator. These
   agree independently with character subtraction.
6. The E2 support leaves no possible nonzero d2 for these sectors. Higher
   differentials are absent in codimension two. The implementation stops
   with an explicit gap if a potentially nonzero d2 is encountered.

The only nonzero first-page maps in the 25 source sectors are:

| Sector | Source -> Target | Generic Rank | Image Characters | Nonzero 12-Minor |
| --- | --- | --- | --- | --- |
| L1 L2 | 16 -> 12 | 12 | [3,3,3,3] | 586376253 |
| L3 L5 | 16 -> 12 | 12 | [3,3,3,3] | 117510144 |
| L4 L5 | 16 -> 12 | 12 | [3,3,3,3] | -90839808 |

Each has regular four-dimensional kernel and zero cokernel. The dual
calculations have the corresponding injective maps. Their characters are
computed independently, rather than assigned by Serre duality.

The non-regular sectors are particularly useful controls:

- `H1(L3 L4)=H2(L3 L4)=[1,0,0,0]` before the `EquivStr` twist.
- `H1(L3 L4*)=H2(L3 L4*)=[3,2,2,2]` before that twist.

## Results and Cross-Checks

All 25 sector tables match all four cohomological degrees and all four
character multiplicities. Including duals and the structure sheaf gives
51 distinct line-bundle calculations. Independent checks include:

- Riemann-Roch indices from the configuration/intersections and recorded C2
  for all 50 charged calculations.
- Regular equivariant Euler characters for those 50 calculations.
- Serre duality for all 25 source sectors, with separately built dual maps.
- Trivial character on `H3(O_X)` and vanishing `H1(O_X),H2(O_X)`.
- Group laws, full-family polynomial covariance, and exact d1 intertwiners.
- Direct kernel/cokernel actions and explicit nonzero rank minors.

After the recorded linearisations, the aggregate characters are:

| Space | [1,a,b,ab] |
| --- | --- |
| H1(V) | [3,3,3,3] |
| H1(V*) | [0,0,0,0] |
| H1(wedge2 V) | [3,3,4,3] |
| H2(wedge2 V) | [0,0,1,0] |

The Wilson projection is fed these newly computed tables. It reproduces
the frozen downstairs result: three Q, up-antiquark, down-antiquark and
charged-antilepton families, four lepton/Higgs-down doublets, one Higgs-up
doublet, and zero colored triplets.

## Reproduce

From the Koszul Compass repository, using an environment with the declared
dependencies:

```bash
python scripts/verify_sms202_geometry_benchmark.py
python scripts/verify_sms202_geometry_benchmark.py --corpus ../../data/raw/sms202.m --output benchmarks/sms202/model_1710_geometry_certificate.json
python -m pytest -q
```

The first command needs only the packaged fixtures. The second also anchors
both fixtures to the full original corpus and regenerates the complete
certificate. It checks rather than changes the immutable expectations.
The executed local test suite passed **18 tests**, including wrong normal
action, Cech exchange sign, deleted polynomial, poisoned expected character,
rescaled polynomial basis, and unresolved higher-differential controls.
Tests ran in the existing parent workspace environment, since the public
checkout's environment does not contain pytest; no dependencies were added.

## Limits and Next Gate

The rank proof holds on a nonempty Zariski-open set in the full recorded
16-dimensional equivariant equation parameter space. Nonemptiness of its
smooth complete-intersection, free-action locus is inherited from the
published geometry classification. Since that locus is open, it intersects
the certified rank-open set. The integer rank witness itself has not been
certified smooth or free. Special cohomology-jumping loci are not covered.

This fixture has equal multiplicities for its three nontrivial baseline
characters, so it cannot alone distinguish every possible renaming of a
and b. The calculation declares and preserves the recorded generator order.

This is a geometry-derived character and quotient-spectrum positive control.
It is not an independent smoothness classification, a full phenomenology
certificate, or a validation of historical no-go claims on other geometries.
The remaining benchmark gates are operator classifications and actual
cup/Yukawa maps. Candidate search remains paused at this stopping result.
