# Koszul Compass

Evidence-first atlas artifacts for a heterotic line-bundle search across the
CICY 5259/7914, 7484, and 2544 routes.

Koszul Compass packages a compact, verified result packet for a verifier-first
heterotic compactification search. The current packet is a **No-Go Atlas v0**:
failed candidate classes are compressed into scoped obstruction syndromes with
cheap executable prefilters and replay counts, while the current higher-degree
survivor carries a proof-carrying certificate and a clearly marked pending
higher-order mass-map gate.

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
and branch completions are not enough by themselves, and even
representative-compatible selection rules are not yet mass-rank verification.
Candidate promotion should carry both a survival certificate and the nearest
no-go boundary.

## Headline Result

The No-Go Atlas v0 records 7 scoped obstruction syndromes, 6 executable cheap
prefilters, and 1 current survivor certificate.

Included syndromes cover:

- CICY 2544: clean upstairs one-Higgs SU(5), but no recorded free symmetry for
  Wilson-line descent in the current data.
- CICY 7484: quotient-compatible character machinery works, but the certified
  vectorlike sector remains too large.
- CICY 5259/7914: representative mismatch, top-degree mismatch,
  degree-one doublet-triplet inseparability, and higher-degree monoid
  downstream obstructions.

The survivor certificate freezes
`radius6_broad_adjacency_filtered_10_branch_50` with operator
`5bar_02*5_34` and monomial `['e3-e2', 'e4-e0']`. It passes the current
q=1, representative, charge/character, triplet-only, and proton-safety gates,
but it is **not** a simple CY3 cubic cup-product certificate. The pending gate
is the higher-order/effective mass-map rank computation.

This is an atlas and survivor packet, not a full MSSM model claim.

## Key Artifacts

- `reports/no_go_atlas_v0.md`
- `reports/no_go_atlas_v0.json`
- `reports/no_go_atlas_v0_verification.json`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.md`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier_verification.json`

Earlier representative-scout anchors are also included:

- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout.md`
- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout.json`
- `reports/phenomenology_guided_q1_radius9_selection_preserving_branch_scout_verification.json`

Upstream verification anchors:

- `reports/phenomenology_guided_q1_radius9_representative_generation_replay_rollup.*`
- `reports/phenomenology_guided_q1_radius9_representative_obstruction_escape_report.*`
- `reports/cicy5259_split_lift_report.*`

## Verification

The included report packet can be checked with:

```bash
uv run python scripts/verify_no_go_atlas_v0.py
uv run python -m py_compile scripts/no_go_atlas_prefilters.py scripts/build_no_go_atlas_v0.py scripts/verify_no_go_atlas_v0.py
uv run python scripts/verify_phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.py
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
