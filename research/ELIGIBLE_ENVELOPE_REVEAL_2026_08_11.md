# Committed eligible-table reveal

The committed file `OUTBOX/ELL_PREBAND_ELIGIBLE_TABLE_2026_08_11.json` was opened only after
the frozen pass marks were merged to `main` at `3da8b23eba3e42894da7ec3486b416c77da22317`.
Its SHA-256 was rechecked immediately before opening and matched the published commitment:

`de1d0be9c9b36437cab185f8474e853d4c68161d915909ab5b2b906f5200c7a3`.

The file records development seed 1729 on earlier instrument commits `4678982` (answer stage)
and `b3b72b7` (interleaving/null policies):

| comparator | near | intermediate | far | overall |
|---|---:|---:|---:|---:|
| bm25 | 0.571429 | 0.437500 | 0.148810 | 0.385913 |
| direct-insight | 0.571429 | 0.386905 | 0.038690 | 0.332341 |
| exact-vector | 0.571429 | 0.354167 | 0.020833 | 0.315476 |
| fused-retrieval | 0.571429 | 0.437500 | 0.110119 | 0.373016 |

Every value is below the corresponding frozen seed-1729 q99.9 mark: 0.577381 near,
0.562500 intermediate, and 0.574405 far.

This table is **invalidated historical evidence**, not a frozen-instrument result. Its value is
governance evidence: the hash proves the eligible figures were not altered after the pass-mark
method or numbers were fixed. It must not be used to select the confirmatory comparator.
