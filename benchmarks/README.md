# Golden Benchmarks

Candidate search is frozen until the benchmark ladder can reproduce published
positive controls under their original conventions. These fixtures are small,
immutable excerpts from upstream source corpora; they are not search outputs.

## SMS202 Model 1710

`sms202/model_1710_source.m` contains the verbatim body identified as record
1710 by the legacy regex scout in the local Oxford `sms202.m` corpus associated with
[arXiv:1202.1757](https://arxiv.org/abs/1202.1757). The expectation manifest
records the SHA-256 of both the fixture and its original 54 MB corpus.

The structural parser finds 2,113 records, rather than the regex scout's 2,012,
and locates this model at structured index 1811. Both IDs are preserved in the
manifest so older atlas artifacts remain traceable without treating their
regex-generated IDs as canonical source positions.

This is an intentionally demanding first control:

- CICY 7487, quotient order 4, symmetry number 3;
- determinant-trivial five-summand line bundle;
- upstairs `h^1(V)=12`, hence three families after the order-four quotient;
- published `IsSM=True`, one Higgs pair, Wilson-line and equivariant data;
- Yukawa ranks `[2, 2]` and `[1, 1]`;
- dimension-four and dimension-five proton flags both `[False, False]`.

The benchmark parser reconstructs every list/integer/boolean field used by the
certificate. It then independently applies the recorded summand linearisations
and Wilson characters to the published cohomology-character tables. This
reproduces three chiral families, no anti-10s, zero colored triplet pairs, and
one electroweak Higgs pair. Symbolic Mathematica fields not yet interpreted,
including operator expressions, are retained verbatim and checked by
field-level hashes so unsupported expressions cannot be silently omitted.

Run the certificate and tests with:

```bash
uv sync --extra dev
uv run python scripts/verify_sms202_golden_benchmark.py
uv run python scripts/verify_sms202_golden_benchmark.py --corpus ../../data/raw/sms202.m
uv run pytest -q
```

## Claim Boundary

Passing this benchmark certifies exact source ingestion, low-level invariant
reconstruction, and the character/Wilson projection of the published source
tables. It does **not** yet reconstruct those cohomology characters, operator
classifications, or Yukawa/cup-product ranks from CICY geometry. Those are the
next benchmark gates. Search promotion remains frozen until they pass or
produce a precise convention-discrepancy report.

## Geometry-Derived Character Gate

The separate geometry calculation now reproduces all 25 model-1710 sector
character tables from the raw CICY7487 equations, coordinate action, and
equivariant Koszul maps. Three exact 16-to-12 maps have certified generic
rank 12; all other sectors resolve by E1/E2 support. Direct kernel/cokernel
actions, Serre duality, and Riemann-Roch cross-check the result.

This establishes the generic character and quotient-spectrum control on
the recorded smooth free family, whose nonemptiness is a published input.
It does not certify a particular integer polynomial point as smooth.
Operator classifications and cup/Yukawa maps remain pending; candidate
search stays paused.

See [the full calculation and conventions](sms202/model_1710_geometry_report.md)
and [the regenerated certificate](sms202/model_1710_geometry_certificate.json).

```bash
python scripts/verify_sms202_geometry_benchmark.py
python scripts/verify_sms202_geometry_benchmark.py --corpus ../../data/raw/sms202.m
```
