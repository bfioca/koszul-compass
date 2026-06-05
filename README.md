# Koszul Compass

Evidence-first scout artifacts for a heterotic line-bundle search on the
CICY 5259/7914 route.

Koszul Compass packages a representative-feasibility refinement of a
radius-9 q=1 frontier. The central result is a selection-preserving
branch-character scout: obstructed branch character requests are replaced by
representative-feasible characters, while q=1 spectrum, matrix-level gates,
refined doublet-triplet/proton filters, singlet monoid support, and
representative realizability remain hard promotion gates.

## Background

This repository comes from a search for heterotic string compactifications with
line-bundle sums on complete intersection Calabi-Yau manifolds. The target
phenomenology is an SU(5)-type upstairs model which can descend through a free
quotient and Wilson line to a three-family Standard-Model-like spectrum.

In this setting, many quick filters are necessary but not sufficient. A bundle
can have the right index, spectrum counts, and charge-level selection rules
while still failing when the actual equivariant cohomology representatives are
examined. Koszul Compass focuses on that gap.

The working hierarchy is:

```text
q=1 spectrum
  -> Wilson-line component characters
  -> charge/character operator filters
  -> representative-level Koszul/E2 realizability
  -> cup-product mass-rank computation
  -> full phenomenology
```

Earlier scans found candidates that looked viable at the character-shadow
level but failed at the representative layer: the branch-level character
assignment requested by a mass operator was not realizable by the actual
equivariant Koszul complex. This package records the next refinement: replace
the obstructed branch requests by representative-feasible characters, then
rerun the q=1, topology, selection-rule, proton-protection, and representative
gates before promoting anything.

The scientific point is deliberately modest but useful: component characters
and branch completions are not enough by themselves. Candidate promotion should
wait until the representatives agree.

## Headline Result

The verified scout starts from 14 generation-pruned refined survivors and
enumerates 28 branch-character replacement variants.

- 24 variants lose the q=1 signature and are blocked before representative
  promotion.
- 4 variants preserve q=1, recomputed matrix gates, refined selection rules,
  proton protection, representative compatibility, and cup-product eligibility.
- The only compatible pattern is `5bar_12*5_12`, replacing
  `5_12:cup_H1_wedge2_V_dual` with the representative-feasible regular
  character `{+1,-1}`.

These rows are branch-character scout targets, not full mass-rank verified
MSSM models. The next physics step is an exact cup-product mass-rank dossier
for the promoted `5bar_12*5_12` block.

## Key Artifacts

- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout.md`
- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout.json`
- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout_verification.json`

Upstream verification anchors are also included:

- `reports/phenomenology_guided_q1_radius9_representative_generation_replay_rollup.*`
- `reports/phenomenology_guided_q1_radius9_representative_obstruction_escape_report.*`
- `reports/cicy5259_split_lift_report.*`

## Verification

The included report packet can be checked with:

```bash
uv run python scripts/verify_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py
uv run python -m py_compile scripts/build_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py scripts/verify_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py
```

The full builder depends on the larger local frontier report corpus that is
not packaged here because it is multi-gigabyte generated data. This repository
is intended as a compact, verified result packet plus source-code provenance.

## Status Vocabulary

- `character_shadow_viable`: passes spectrum and character-level selection
  summaries but has not yet passed representative realization.
- `representative_compatible`: branch character assignments are compatible
  with the representative-level Koszul/E2 realization gate.
- `cup_product_eligible`: representative-compatible mass target ready for an
  exact cup-product mass-rank computation.

## Catchphrase

Do not trust the shadow until the representatives point north.
