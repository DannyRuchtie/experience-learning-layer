# Frozen-scorer instrument pass marks

**Source state:** `main` at `12772c3a18c8de36473e1cdbcf2c747d73443e67`.
**Scorer digest:** `sha256:6fbd052bb3372a87ace54b1439e78217e8de0c73c69aca36150a87967ccafee3`.
**Partition:** development only. The sealed partition was not generated.
**Eligible conditions executed:** none.

The pass mark is the direct nearest-rank q99.9 of each seed and stratum's fixed-output,
gold-trajectory-permuted null distribution, maximised over the five null policies. The comparison
is strict: an eligible score must be greater than its corresponding mark. This is the latest
pre-measurement ruling and removes `X` as a separately chosen parameter; older p95-plus-X wording
is superseded rather than added on top of q99.9.

Each seed used 10,000 permutations with permutation RNG seed 90009. At q99.9 this supplies roughly
ten tail observations instead of the approximately one tail observation available from 1,000
permutations. Repeating the full 80,000-permutation run produced a byte-identical artifact.

## Pass marks and primary corridor

| seed | near q99.9 | intermediate q99.9 | far q99.9 | far oracle | far corridor after 0.05 |
|---:|---:|---:|---:|---:|---:|
| 1729 | 0.577381 | 0.562500 | 0.574405 | 0.809524 | 0.185119 |
| 11 | 0.574405 | 0.589286 | 0.574405 | 0.806548 | 0.182143 |
| 42 | 0.592262 | 0.580357 | 0.568452 | 0.773810 | 0.155357 |
| 101 | 0.559524 | 0.559524 | 0.586310 | 0.866071 | 0.229762 |
| 777 | 0.586310 | 0.589286 | 0.556548 | 0.880952 | 0.274405 |
| 2026 | 0.583333 | 0.577381 | 0.568452 | 0.901786 | 0.283333 |
| 31337 | 0.583333 | 0.574405 | 0.571429 | 0.860119 | 0.238690 |
| 8080 | 0.559524 | 0.589286 | 0.568452 | 0.758929 | 0.140476 |

Every seed/stratum retains a non-empty interval between q99.9 and the oracle ceiling after reserving
the preregistered 0.05 target effect. On the primary far stratum, the mean pass mark is 0.571057,
the worst-seed mark is 0.586310, and the minimum effect-reserved corridor is 0.140476.

## Reproducibility

Canonical artifact: `research/FROZEN_BAND_MEASUREMENT_2026_08_11.json`.
Artifact SHA-256: `5bba9aea9f6cd5948072db58ad632942deb982355edb817d907987c5503e0637`.

Environment: macOS Darwin 25.6.0 arm64; Python 3.14.6; Pydantic 2.13.4; pytest 9.1.1;
Ruff 0.16.2; mypy 2.3.0. Measurement command:

```bash
PYTHONPATH=src python script/measure_frozen_bands.py \
  --source-commit 12772c3a18c8de36473e1cdbcf2c747d73443e67 \
  --permutations 10000 \
  --output research/FROZEN_BAND_MEASUREMENT_2026_08_11.json
```

The committed eligible table remained unopened during both runs. Its independently checked
SHA-256 was still `de1d0be9c9b36437cab185f8474e853d4c68161d915909ab5b2b906f5200c7a3`.

## Monte-Carlo stability of the pass marks (added by Darwin, 2026-08-11)

The byte-identical rerun above used the same permutation seed (`90009`), so it demonstrates
**determinism, not stability**. Same-seed reproduction is explicitly not evidence of robustness —
see `statistics.reproduction_requirement` in the contract, added after the generator seed was found
to vary surface text but not structure. The right evidence is variation across *permutation* seeds.

Measured independently on seed 1729, far stratum, `uniform-random-visible`, 10,000 permutations:

| permutation seed | far q99.9 | as a count |
|---:|---:|---:|
| 90009 | 0.574405 | 193/336 |
| 1 | 0.577381 | 194/336 |
| 2 | 0.574405 | 193/336 |
| 3 | 0.574405 | 193/336 |
| 4 | 0.577381 | 194/336 |

Spread **0.002976**, sd **0.001458** — exactly one task, and **2.1%** of the 0.140476 minimum
effect-reserved corridor. The pass marks are stable at 10,000 permutations.

This also independently reproduces the reported seed-1729 far q99.9 of `0.574405` using a separate
script, alongside the far-oracle column, which matches an earlier independent measurement across all
eight seeds.
