# SPDX-License-Identifier: CC0-1.0
"""Verify that the Python reference impl matches the test vectors on disk.

Returns exit code 0 on full pass, 1 on any mismatch.

Usage:
    python run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

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

VECTORS = HERE.parent / "test-vectors"


def hx(b: bytes) -> str:
    return b.hex()


def unhex(s: str) -> bytes:
    return bytes.fromhex(s)


PASS, FAIL = 0, 0


def check(label: str, expected, actual) -> None:
    global PASS, FAIL
    if expected == actual:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}")
        print(f"        expected: {expected}")
        print(f"        actual:   {actual}")


def check_gradient_hash() -> None:
    print("Section 4.1 gradient hash")
    data = json.loads((VECTORS / "gradient-hash.json").read_text())
    for v in data["vectors"]:
        t = np.array(v["input"]["values"], dtype=np.float32).reshape(v["input"]["shape"])
        check(f"{v['id']} serialized", v["serialized_hex"], hx(serialize_tensor(t)))
        check(f"{v['id']} hash",       v["gradient_hash_hex"], hx(gradient_hash(t)))


def check_layer1() -> None:
    print("Section 4.2 Layer 1 leaves")
    data = json.loads((VECTORS / "layer1-leaves.json").read_text())
    for v in data["vectors"]:
        i = v["input"]
        leaf = layer1_leaf(i["contributor"], i["sync_cycle"], unhex(i["gradient_hash_hex"]))
        check(f"{v['id']} leaf", v["leaf_hex"], hx(leaf))


def check_layer2() -> None:
    print("Section 4.3 Layer 2 leaves")
    data = json.loads((VECTORS / "layer2-leaves.json").read_text())
    for v in data["vectors"]:
        i = v["input"]
        leaf = layer2_leaf(
            i["contributor"], i["weight"], i["contribution_type"], i["sync_cycle"]
        )
        check(f"{v['id']} leaf", v["leaf_hex"], hx(leaf))


def check_merkle() -> None:
    print("Section 4.4 Merkle trees")
    data = json.loads((VECTORS / "merkle-trees.json").read_text())
    for v in data["vectors"]:
        leaves = [unhex(h) for h in v["leaves_hex"]]
        root, layers = build_tree(leaves)
        check(f"{v['id']} root", v["root_hex"], hx(root))
        for i, expected_proof in enumerate(v["proofs"]):
            actual_proof = [hx(s) for s in build_proof(layers, i)]
            check(f"{v['id']} proof[{i}]", expected_proof, actual_proof)
            assert verify_inclusion(
                [unhex(s) for s in expected_proof], root, leaves[i]
            )


def main() -> int:
    check_gradient_hash()
    check_layer1()
    check_layer2()
    check_merkle()
    print(f"\n{PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
