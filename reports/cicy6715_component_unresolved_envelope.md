# CICY6715 Component-Unresolved Character Envelope Audit

Status: `cicy6715_unresolved_envelope_clean_branch_possible`

## Parameters

- target_cicy: `6715`
- target_option_index: `1`
- max_branches: `None`
- branch_convention: `enumerate all nonnegative Z2xZ2 character multiplicities for the unresolved wedge2_V H1 and H2 dimensions; assign wedge2_V_dual by Serre duality, using self-duality of Z2xZ2 irreps`

## Summary

- candidate_count: `5`
- branch_count: `1100`
- expected_full_branch_count: `1100`
- total_one_higgs_pair_triplet_free_count: `20544`
- total_one_higgs_proton_safe_count: `3456`
- total_clean_one_higgs_precup_count: `1728`
- candidate_status_counts: `{'clean_branch_possible': 1, 'no_one_higgs_proton_safe_branch': 3, 'proton_safe_but_doublet_or_other_obstructed': 1}`

## Candidate Records

### CICY `6715` model `229` option `1`

- status: `proton_safe_but_doublet_or_other_obstructed`
- unresolved_pair: `[3, 4]`
- unresolved_cohomology: `[0, 2, 2, 0]`
- branch_count: `100`
- total_one_higgs_pair_triplet_free_count: `2496`
- total_one_higgs_proton_safe_count: `1728`
- total_clean_one_higgs_precup_count: `0`

### CICY `6715` model `245` option `1`

- status: `no_one_higgs_proton_safe_branch`
- unresolved_pair: `[1, 2]`
- unresolved_cohomology: `[0, 2, 2, 0]`
- branch_count: `100`
- total_one_higgs_pair_triplet_free_count: `2496`
- total_one_higgs_proton_safe_count: `0`
- total_clean_one_higgs_precup_count: `0`

### CICY `6715` model `591` option `1`

- status: `no_one_higgs_proton_safe_branch`
- unresolved_pair: `[0, 1]`
- unresolved_cohomology: `[0, 3, 3, 0]`
- branch_count: `400`
- total_one_higgs_pair_triplet_free_count: `6528`
- total_one_higgs_proton_safe_count: `0`
- total_clean_one_higgs_precup_count: `0`

### CICY `6715` model `596` option `1`

- status: `no_one_higgs_proton_safe_branch`
- unresolved_pair: `[3, 4]`
- unresolved_cohomology: `[0, 3, 3, 0]`
- branch_count: `400`
- total_one_higgs_pair_triplet_free_count: `6528`
- total_one_higgs_proton_safe_count: `0`
- total_clean_one_higgs_precup_count: `0`

### CICY `6715` model `766` option `1`

- status: `clean_branch_possible`
- unresolved_pair: `[3, 4]`
- unresolved_cohomology: `[0, 2, 2, 0]`
- branch_count: `100`
- total_one_higgs_pair_triplet_free_count: `2496`
- total_one_higgs_proton_safe_count: `1728`
- total_clean_one_higgs_precup_count: `1728`

## Interpretation

- clean branch possible: `True`
- bounded no clean branch: `False`
- note: This is an envelope audit, not an actual higher-map representative resolution. A zero clean count proves that no admissible character completion of the unresolved CICY6715 wedge pair can hide a clean one-Higgs/proton-safe pre-cup survivor under the current operator gates.

## Gates

- source_artifacts_verified: `True` - envelope audit starts from verified CICY6715/6927 and operator-graph atlas artifacts
- unresolved_candidate_set_matches_atlas: `True` - the five CICY6715 component-unresolved q1 candidates are exactly the atlas uncertainty set
- unresolved_structure_is_single_wedge_pair: `True` - each unresolved candidate has exactly one unresolved wedge pair, its dual, and compatible singlets
- finite_envelope_scope_is_complete: `True` - all Serre-dual H1/H2 character compositions are enumerated when no branch cap is set
- classification_matches_clean_count: `True` - report status is determined by whether any branch can hide a clean one-Higgs pre-cup survivor
