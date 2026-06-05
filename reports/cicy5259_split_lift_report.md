# CICY 5259 split-lift audit

Status: `full_upstairs_split_lift_certified__quotient_descent_blocked`

## Result

- Missing seventh divisor obtained: yes.
- Route: ordinary ineffective split / configuration equivalence to favourable CICY 7914.
- Full upstairs SU(5) line-bundle certificate: yes, in the 7914 split presentation.
- Full quotient/Wilson-line certificate: no, still blocked by missing split-compatible equivariant data.

## Split

- selected redundant presentation: `7914`
- added split row index: `6`
- split columns merged back to 5259: `[0, 1, 2]`
- new divisor class: `J6`, the hyperplane class of the added P2 row
- contraction check: deleting row 6 and merging columns 0,1,2 exactly reconstructs the 5259 configuration

## Full Upstairs Certificate

- matrix lift: append zero charge on `J6` to the 5259 matrix
- c1: `[0, 0, 0, 0, 0, 0, 0]`
- index(V), index(wedge2 V): `-6`, `-6`
- c2(V): `[14, 8, 20, 12, 8, 34, 17]`
- anomaly c2(TX)-c2(V): `[10, 16, 4, 12, 16, 22, 19]`
- slope feasible: `True` with max normalized slope `9.920e-08`
- cohomology V / V* / wedge2 V / wedge2 V*: `[0, 6, 0, 0]` / `[0, 0, 6, 0]` / `[0, 16, 10, 0]` / `[0, 10, 16, 0]`
- upstairs spectrum 10/anti10/5bar/5: `6/0/16/10`

## Remaining Blocker

The split presentation supplies the full seven-divisor topology, but not the quotient descent. The missing data are:

- A selected 5259 free Z2 action lifted through the 7914 P2 split, including coordinate and polynomial action.
- The induced action on the full seven-dimensional Picard basis or an equivalent proof that the zero-extended line-bundle sum admits the required equivariant structure.
- Equivariant cohomology character decompositions for H*(X,V), H*(X,V*) and the wedge2 sectors.
- A Wilson-line character choice and projection check proving the downstairs standard-model spectrum.

So the old ambient-restricted 5259 breadcrumb is upgraded to a full upstairs split-lift certificate, but not to a full Wilson-line quotient certificate.
