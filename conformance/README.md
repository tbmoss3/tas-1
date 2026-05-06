# TAS-1 Conformance Suite

Two scripts:

- [`generate.py`](generate.py) — produces canonical test vectors
  (JSON, language-agnostic) using the Python reference implementation.
  Writes to `../test-vectors/*.json`. Run this whenever the spec's
  byte formats change.
- [`run.py`](run.py) — verifies that the Python reference
  implementation matches the test vectors on disk. Returns exit code
  0 on full pass, 1 on any mismatch.

## Setup

Install the reference implementation:

```bash
cd ../reference/python
pip install -e .
```

## Generate test vectors

```bash
cd ../../conformance
python generate.py
```

## Verify conformance

```bash
python run.py
```

## Verifying a non-Python implementation

The `test-vectors/*.json` files are language-agnostic. To verify your
implementation:

1. Read `test-vectors/gradient-hash.json` and reproduce each
   `gradient_hash_hex` using your gradient-hash function on the listed
   tensor input.
2. Read `test-vectors/layer1-leaves.json` and reproduce each
   `leaf_hex` using your Layer 1 leaf construction.
3. Read `test-vectors/layer2-leaves.json` and reproduce each
   `leaf_hex` using your Layer 2 leaf construction.
4. Read `test-vectors/merkle-trees.json` and reproduce each `root_hex`
   and per-leaf `proof` using your tree-building and proof-walk logic.

Any mismatch indicates a non-conformant implementation.
