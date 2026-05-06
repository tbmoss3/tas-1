# SPDX-License-Identifier: CC0-1.0
"""Generate canonical TAS-1 test vectors from the Python reference impl.

Writes JSON files to ../test-vectors/. Each file is language-agnostic;
implementations in any language can verify against the produced
vectors without running this script.

Usage:
    python generate.py

Requires the Python reference implementation to be installed:
    cd ../reference/python && pip install -e .
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Allow running without `pip install -e .` by adding the reference
# package to sys.path directly.
HERE = Path(__file__).resolve().parent
REF_PYTHON = HERE.parent / "reference" / "python"
if str(REF_PYTHON) not in sys.path:
    sys.path.insert(0, str(REF_PYTHON))

from tas1 import (  # noqa: E402
    build_proof,
    build_tree,
    gradient_hash,
    layer1_leaf,
    layer2_leaf,
    serialize_tensor,
    verify_inclusion,
)

OUT = HERE.parent / "test-vectors"
VERSION = "TAS-1 v1.0"


def hx(b: bytes) -> str:
    """Lowercase hex without 0x prefix."""
    return b.hex()


# ─── Test vectors ─────────────────────────────────────────────────────


def gradient_hash_vectors() -> dict:
    cases = []

    # TV-1: scalar zero
    t1 = np.array(0.0, dtype=np.float32)
    cases.append({
        "id": "TV-1",
        "description": "scalar zero (rank 0)",
        "input": {
            "dtype": "float32",
            "shape": list(t1.shape),
            "values": t1.tolist(),
        },
        "serialized_hex": hx(serialize_tensor(t1)),
        "gradient_hash_hex": hx(gradient_hash(t1)),
    })

    # TV-2: rank-1 ones
    t2 = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    cases.append({
        "id": "TV-2",
        "description": "rank-1 vector of ones, length 4",
        "input": {
            "dtype": "float32",
            "shape": list(t2.shape),
            "values": t2.tolist(),
        },
        "serialized_hex": hx(serialize_tensor(t2)),
        "gradient_hash_hex": hx(gradient_hash(t2)),
    })

    # TV-3: rank-2 small matrix
    t3 = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    cases.append({
        "id": "TV-3",
        "description": "rank-2 matrix [[1,2],[3,4]]",
        "input": {
            "dtype": "float32",
            "shape": list(t3.shape),
            "values": t3.tolist(),
        },
        "serialized_hex": hx(serialize_tensor(t3)),
        "gradient_hash_hex": hx(gradient_hash(t3)),
    })

    return {"version": VERSION, "vectors": cases}


def layer1_leaf_vectors() -> dict:
    # TV-4: build on TV-1 gradient hash
    g = gradient_hash(np.array(0.0, dtype=np.float32))
    contributor = "0x000000000000000000000000000000000000beef"
    cases = [{
        "id": "TV-4",
        "description": "Layer 1 leaf with TV-1 gradient and beef address at cycle 1",
        "input": {
            "contributor": contributor,
            "sync_cycle": 1,
            "gradient_hash_hex": hx(g),
        },
        "leaf_hex": hx(layer1_leaf(contributor, 1, g)),
    }]
    return {"version": VERSION, "vectors": cases}


def layer2_leaf_vectors() -> dict:
    contributor = "0x000000000000000000000000000000000000beef"
    cases = [{
        "id": "TV-5",
        "description": "Layer 2 leaf for compute contribution, weight 1000, cycle 1",
        "input": {
            "contributor": contributor,
            "weight": 1000,
            "contribution_type": 0,
            "sync_cycle": 1,
        },
        "leaf_hex": hx(layer2_leaf(contributor, 1000, 0, 1)),
    }]
    return {"version": VERSION, "vectors": cases}


def merkle_tree_vectors() -> dict:
    # Construct fixed leaves so vectors are reproducible.
    contributor = "0x000000000000000000000000000000000000beef"
    L0 = layer2_leaf(contributor, 100, 0, 1)
    L1 = layer2_leaf(contributor, 200, 0, 1)
    L2 = layer2_leaf(contributor, 300, 0, 1)

    cases = []

    # TV-6: single leaf
    root6, layers6 = build_tree([L0])
    cases.append({
        "id": "TV-6",
        "description": "single-leaf tree (root equals leaf)",
        "leaves_hex": [hx(L0)],
        "root_hex": hx(root6),
        "proofs": [[]],
    })
    assert verify_inclusion([], root6, L0)

    # TV-7: two leaves
    root7, layers7 = build_tree([L0, L1])
    proof_L0 = build_proof(layers7, 0)
    proof_L1 = build_proof(layers7, 1)
    cases.append({
        "id": "TV-7",
        "description": "two-leaf tree (commutative pair-hash)",
        "leaves_hex": [hx(L0), hx(L1)],
        "root_hex": hx(root7),
        "proofs": [
            [hx(s) for s in proof_L0],
            [hx(s) for s in proof_L1],
        ],
    })
    assert verify_inclusion(proof_L0, root7, L0)
    assert verify_inclusion(proof_L1, root7, L1)

    # TV-8: three leaves (odd-promotion)
    root8, layers8 = build_tree([L0, L1, L2])
    proof_T0 = build_proof(layers8, 0)
    proof_T1 = build_proof(layers8, 1)
    proof_T2 = build_proof(layers8, 2)
    cases.append({
        "id": "TV-8",
        "description": "three-leaf tree, odd node promoted unchanged",
        "leaves_hex": [hx(L0), hx(L1), hx(L2)],
        "root_hex": hx(root8),
        "proofs": [
            [hx(s) for s in proof_T0],
            [hx(s) for s in proof_T1],
            [hx(s) for s in proof_T2],
        ],
    })
    assert verify_inclusion(proof_T0, root8, L0)
    assert verify_inclusion(proof_T1, root8, L1)
    assert verify_inclusion(proof_T2, root8, L2)

    return {"version": VERSION, "vectors": cases}


# ─── Driver ───────────────────────────────────────────────────────────


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = [
        ("gradient-hash.json", gradient_hash_vectors()),
        ("layer1-leaves.json", layer1_leaf_vectors()),
        ("layer2-leaves.json", layer2_leaf_vectors()),
        ("merkle-trees.json", merkle_tree_vectors()),
    ]
    for name, payload in files:
        path = OUT / name
        path.write_text(json.dumps(payload, indent=2) + "\n")
        n = len(payload["vectors"])
        print(f"  wrote {path.name}  ({n} vector{'s' if n != 1 else ''})")
    print(f"done. {len(files)} files in {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
