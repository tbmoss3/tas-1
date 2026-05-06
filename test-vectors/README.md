# TAS-1 Test Vectors

Language-agnostic JSON test vectors for TAS-1 §4.1–§4.4.

## Files

- [`gradient-hash.json`](gradient-hash.json) — TV-1 through TV-3:
  scalar, rank-1, rank-2 gradient hashes
- [`layer1-leaves.json`](layer1-leaves.json) — TV-4: Layer 1 (Lab
  Commitment) leaf encoding
- [`layer2-leaves.json`](layer2-leaves.json) — TV-5: Layer 2
  (Contribution Record) leaf encoding
- [`merkle-trees.json`](merkle-trees.json) — TV-6 through TV-8:
  single-leaf, two-leaf, three-leaf (odd-promotion) tree
  construction and inclusion proofs

## Format

All hex values are lowercase, no `0x` prefix, no separators.

Each file is a JSON object with a top-level `"version"` field
(currently `"TAS-1 v1.0"`) and a `"vectors"` array.

## Regeneration

These files are produced by the conformance generator:

```bash
cd ../conformance
python generate.py
```

The generator imports the Python reference implementation from
`../reference/python/` and writes regenerated vectors back to this
directory. Implementations in other languages can verify against
these files without running the generator.
