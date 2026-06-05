# Higher-Degree Candidate Dossier

Status: `higher_order_mass_map_pending_for_frozen_candidate`
Candidate: `radius6_broad_adjacency_filtered_10_branch_50`
Route: `5259/7914`
Operator: `5bar_02*5_34`
Monomial: `['e3-e2', 'e4-e0']`

## Certified Facts

- q=1 three-family spectrum is present in the audited radius-9 frontier
- physical 5bar H1, cup-dual 5 H1, and both singlet H1 factors are representative-compatible
- the selected degree-2 singlet monoid is charge-neutralizing and Z2-even at component level
- the operator has triplet support 1, doublet support 0, and zero dangerous 10*5bar*5bar hits under current selection rules

## Spectrum

- cohomology: `{'V': [0, 6, 0, 0], 'V_dual': [0, 0, 6, 0], 'wedge2_V': [0, 8, 2, 0], 'wedge2_V_dual': [0, 2, 8, 0]}`
- q=1 three-family signature: `True`
- vectorlike prediction: `{'colored_triplet_vectorlike_pairs': 1, 'electroweak_doublet_vectorlike_pairs': 1, 'h1_wedge2_regular_multiplicity': 4, 'h2_wedge2_regular_multiplicity': 1, 'net_families': 3, 'regular_character_rule_applies': True}`

## Operator

- bilinear charge: `{'coefficients': [1, 0, 1, -1, -1], 'label': 'e0+e2-e3-e4'}`
- needed singlet charge: `{'coefficients': [-1, 0, -1, 1, 1], 'label': '-e0-e2+e3+e4'}`
- monomial charge: `{'coefficients': [-1, 0, -1, 1, 1], 'label': '-e0-e2+e3+e4'}`
- total charge: `{'coefficients': [0, 0, 0, 0, 0], 'label': '0'}`
- total line-bundle sum: `[0, 0, 0, 0, 0, 0, 0]`
- triplet/doublet support: `1` / `0`
- dangerous proton operators allowed: `0`

## Representative Stack

- physical_5bar_H1_wedge2_V `5bar_02`: line `[1, 0, 1, -1, 0, 0, -1]`, H1 character `{'+': 1, '-': 1}`, representative `+1/-1`
- cup_dual_5_H1_wedge2_V_dual `5_34`: line `[1, 0, 2, 0, 0, -1, 0]`, H1 character `{'+': 1, '-': 0}`, representative `+1/-0`
- h1_singlet_insertion `e3-e2`: line `[-1, -1, -3, 0, 2, 1, 1]`, H1 character `{'+': 6, '-': 6}`, representative `+6/-6`
- h1_singlet_insertion `e4-e0`: line `[-1, 1, 0, 1, -2, 0, 0]`, H1 character `{'+': 2, '-': 2}`, representative `+2/-2`

## Ordinary Product Boundary

- O_X cohomology: `[1, 0, 0, 1]`
- ordinary H1 degree sum: `4`
- ordinary cup status: `not_a_simple_CY3_cubic_top_product`
- nonzero prefix counts: `{'1': 24, '2': 8}`
- all length-three prefixes have zero H3: `True`

## Higher-Order Frontier

- triplet block: `{'selection_rule_shape': ['+1/-1', '+1/-0'], 'matrix_dimensions_after_fixed_singlet_vevs': [1, 1], 'rank_needed_to_lift_colored_triplet_pair': 1, 'rank_status': 'pending_higher_order_mass_map'}`
- doublet block: `{'selection_rule_shape': [1, 0], 'matrix_dimensions_after_fixed_singlet_vevs': [1, 0], 'rank_needed_to_preserve_light_doublet_pair': 0, 'rank_status': 'selection_rule_forces_zero_for_this_operator'}`
- not claimed: `simple CY3 cubic cup-product mass-rank verification`

Minimal engine requirements:
- construct equivariant Koszul/Cech representatives for the four H1 legs
- implement multiplication plus homotopy/projection in the Koszul total complex
- evaluate the order-4 effective product or equivalent Massey/Yoneda representative
- insert singlet vev directions in the even invariant component of H1(e3-e2) x H1(e4-e0)
- compute the resulting 1x1 triplet block and confirm the doublet block remains zero

Pending assumptions:
- nonzero higher-order effective mass tensor
- choice of singlet vev directions with nonzero triplet coupling
- absence of additional higher-order proton or doublet couplings beyond the current selection table

## Gates

- starts_from_verified_higher_degree_search: `True` - dossier imports the verified higher-degree intersection search
- frozen_lead_identity_is_stable: `True` - first higher-degree lead identity, operator, monomial, source, and weight match
- q1_spectrum_is_reconstructed: `True` - source record reconstructs the q=1 three-family plus one vectorlike pair signature
- representative_stack_is_compatible: `True` - physical 5bar, cup 5, and singlet factors have representative-compatible characters
- charge_and_line_bundle_neutrality_hold: `True` - degree-2 singlet monoid neutralizes both SU(5) charge vector and 7914 line-bundle class
- triplet_only_and_proton_safe_selection_stack: `True` - current selection rules give triplet-only support and forbid every listed dangerous proton operator
- ordinary_cubic_cup_not_overclaimed: `True` - the dossier keeps the lead at higher-order pending status, not cubic cup-product rank status
