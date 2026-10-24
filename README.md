# Koszul Compass

Benchmark-first verification tools and evidence artifacts for heterotic
line-bundle compactifications on CICY threefolds.

Koszul Compass began as a verifier-first candidate search and No-Go Atlas. Its
current research program is **benchmark first**: candidate generation is frozen
until the mathematical pipeline reproduces published positive controls under
their original conventions. Historical obstruction artifacts remain available,
but an engine-relative failure is not promoted to a geometric no-go.

The first golden control is legacy SMS202 scout model `1710` (source model 23)
on CICY7487. The repository now
contains its verbatim Mathematica source record, an immutable expectation
manifest, a delimiter-aware parser that retains unsupported symbolic fields,
and mutation-tested verification. This initial gate certifies source ingestion,
low-level invariant reconstruction, and the Wilson projection of the published
character tables. A separate exact Koszul calculation now also reproduces all
25 cohomology-character tables from the recorded geometry on its generic
smooth free locus. Operator classifications and cup products remain pending.

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

The benchmark ladder now has passing source-ingestion and geometry-derived
character controls, and zero end-to-end geometry-to-phenomenology controls.
SMS202 model `1710` reproduces all 25 sector character tables using exact
equivariant Koszul maps and kernel/cokernel actions. Applying the recorded
linearisations and Wilson line gives three families, no anti-10s, zero
colored triplet pairs, and one Higgs doublet pair. The calculation is generic
on the published smooth free family; Yukawa ranks and proton-safety labels
are still source data, not independently reconstructed coupling results.

The historical No-Go Atlas v0 records 48 scoped obstruction syndromes, 30
executable cheap prefilters, and 0 active survivor certificates.

Included syndromes cover:

- CICY 2544: clean upstairs one-Higgs SU(5), but no recorded free symmetry for
  Wilson-line descent in the current data.
- CICY 7484: quotient-compatible character machinery works, but the certified
  vectorlike sector remains too large.
- CICY 5259/7914: representative mismatch, top-degree mismatch,
  degree-one doublet-triplet inseparability, and higher-degree monoid
  downstream obstructions.
- CICY 5302/5273/6738/5425/5256 GUTall benchmark-pool passes: clean algebraic
  pools are either blocked by missing local raw free-action data or by missing
  geometry-specific promotion engines in the current compactification pipeline.

The former Branch 50 shadow-stage survivor is retired into the atlas as a
degree-law negative control. This is an atlas packet, not a full MSSM model
claim.

## Frozen Atlas Evidence

The CICY6715 unresolved-envelope report historically enumerated all `1100` Serre-dual
`Z2 x Z2` character completions for the five component-unresolved CICY6715
q=1 candidates. The envelope finds `1728` clean one-Higgs pre-cup branches,
all localized to CICY6715 model `766`.

The strongest branch is model `766`, branch `99`, where the unresolved
`wedge2_V` H1 and H2 characters are both all-trivial:

```json
{"1": 2, "a": 0, "ab": 0, "b": 0}
```

This is an existential envelope result only. It is retained as scoped evidence,
not an active search lead or a theorem-level no-go.

The CICY5256 benchmark-pool audit reproduces `2891` algebraically clean SU(5)
models with `0` algebraic failures and `6` recorded row-trivial free actions.
Ambient line-bundle lift readiness exists for all `763` order-2 rows and `544`
of the `2128` order-4 rows; the remaining `1584` order-4 rows are lift
obstructed. This remains a scoped current-engine gap, not a physical no-go for
CICY5256. Queue advancement is paused while the golden benchmark ladder is
built.

## Repository Boundary

Koszul Compass is intentionally the compact public evidence packet, not the
full exploratory search worktree. The split is:

- **This repository:** verified reports, compact replay scripts, public-facing
  obstruction summaries, and proof-carrying candidate or no-go certificates.
- **Search forks:** heavy frontier generation, large local corpora,
  experimental builder dependencies, and expensive representative or
  cup-product machinery.

That boundary is part of the methodology. Search forks can move quickly and
carry bulky generated state, while Koszul Compass stays small enough to review,
clone, verify, and cite. New results should enter this repository only when
they have a clear artifact boundary: a report, a verifier, a scoped claim, and
an explicit pending gate if the result is not yet a full model certificate.

For the current frontier, Koszul Compass records the CICY6715 model `766`
branch `99` envelope target. The actual higher-map search for whether that
all-trivial character completion is representative-realizable belongs in the
search fork until it produces a verified certificate or a bounded no-go.

## Key Artifacts

Golden benchmark head:

- `benchmarks/sms202/model_1710_source.m`
- `benchmarks/sms202/model_1710_expected.json`
- `scripts/verify_sms202_golden_benchmark.py`
- `tests/test_sms202.py`
- `benchmarks/sms202/model_1710_geometry_report.md`
- `benchmarks/sms202/model_1710_geometry_certificate.json`
- `scripts/verify_sms202_geometry_benchmark.py`
- `tests/test_sms202_geometry.py`

Historical atlas packet:

- `reports/no_go_atlas_v0.md`
- `reports/no_go_atlas_v0.json`
- `reports/no_go_atlas_v0_verification.json`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.md`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.json`
- `reports/phenomenology_guided_q1_radius9_higher_degree_candidate_dossier_verification.json`
- `reports/cicy6715_component_unresolved_envelope.md`
- `reports/cicy6715_component_unresolved_envelope.json`
- `reports/cicy6715_component_unresolved_envelope_verification.json`
- `reports/cicy5256_gutall_benchmark_pool_engine_audit.md`
- `reports/cicy5256_gutall_benchmark_pool_engine_audit.json`
- `reports/cicy5256_gutall_benchmark_pool_engine_audit_verification.json`
- `reports/atlas_gap_queue_post_cicy5256_benchmark_advancement.md`
- `reports/atlas_gap_queue_post_cicy5256_benchmark_advancement.json`
- `reports/atlas_gap_queue_post_cicy5256_benchmark_advancement_verification.json`

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
uv sync --extra dev
uv run python scripts/verify_sms202_golden_benchmark.py
uv run python scripts/verify_sms202_geometry_benchmark.py
uv run pytest -q
uv run python scripts/verify_no_go_atlas_v0.py
uv run python -m py_compile scripts/no_go_atlas_prefilters.py scripts/build_no_go_atlas_v0.py scripts/verify_no_go_atlas_v0.py
uv run python scripts/verify_phenomenology_guided_q1_radius9_higher_degree_candidate_dossier.py
uv run python scripts/verify_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py
uv run python scripts/verify_cicy6715_component_unresolved_envelope.py
uv run python scripts/verify_cicy5256_gutall_benchmark_pool_engine_audit.py
uv run python scripts/verify_atlas_gap_queue_post_cicy5256_benchmark_advancement.py
uv run python -m py_compile scripts/build_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py scripts/verify_phenomenology_guided_q1_radius9_selection_preserving_branch_scout.py
```

The full builder depends on the larger local frontier report corpus that is
not packaged here because it is multi-gigabyte generated data. This repository
is intended as a compact, verified result packet plus source-code provenance.
Some builder scripts are included as provenance for local replay; the verifier
scripts are the intended compact-package checks.

## Status Vocabulary

- `source_ingestion_certified`: immutable published source record parses and
  reproduces its frozen low-level fields and invariants.
- `golden_benchmark_verified`: reserved for an independent reconstruction of
  the published quotient spectrum and operator/coupling result from geometry.
- `character_shadow_viable`: passes spectrum and character-level selection
  summaries but has not yet passed representative realization.
- `representative_compatible`: branch character assignments are compatible
  with the representative-level Koszul/E2 realization gate.
- `cup_product_eligible`: representative-compatible mass target ready for an
  exact cup-product mass-rank computation.

## Catchphrase

Do not trust the shadow until the representatives point north.
