# SPDX-License-Identifier: CC0-1.0
"""TAS-1 Training Attribution Standard — reference implementation."""

from .gradient_hash import gradient_hash, serialize_tensor
from .leaves import layer1_leaf, layer2_leaf
from .merkle import build_proof, build_tree, hash_pair, verify_inclusion

__version__ = "0.1.0"

__all__ = [
    "gradient_hash",
    "serialize_tensor",
    "layer1_leaf",
    "layer2_leaf",
    "build_tree",
    "build_proof",
    "verify_inclusion",
    "hash_pair",
]
