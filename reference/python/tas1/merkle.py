# SPDX-License-Identifier: CC0-1.0
"""TAS-1 §4.4 — Merkle tree construction.

Pair-hash matches OpenZeppelin's MerkleProof.commutativeKeccak256:
    h(a, b) = keccak256(min(a, b) || max(a, b))

Tree construction promotes odd nodes unchanged to the next layer.
Inclusion proofs are the ordered sibling hashes encountered on the
leaf-to-root walk.
"""

from __future__ import annotations

from eth_utils import keccak


def hash_pair(a: bytes, b: bytes) -> bytes:
    """OpenZeppelin commutativeKeccak256."""
    if a < b:
        return keccak(a + b)
    return keccak(b + a)


def build_tree(leaves: list[bytes]) -> tuple[bytes, list[list[bytes]]]:
    """Build a sort-pair Merkle tree.

    Returns (root, layers). layers[0] is the leaf list; layers[-1] is
    [root]. Used by build_proof to walk siblings from leaf to root.
    """
    if not leaves:
        raise ValueError("cannot build tree over empty leaves")

    layers: list[list[bytes]] = [list(leaves)]
    while len(layers[-1]) > 1:
        prev = layers[-1]
        next_layer: list[bytes] = []
        for i in range(0, len(prev), 2):
            if i + 1 == len(prev):
                next_layer.append(prev[i])  # promote odd node unchanged
            else:
                next_layer.append(hash_pair(prev[i], prev[i + 1]))
        layers.append(next_layer)
    return layers[-1][0], layers


def build_proof(layers: list[list[bytes]], leaf_index: int) -> list[bytes]:
    """Walk leaf -> root, collecting siblings."""
    proof: list[bytes] = []
    idx = leaf_index
    for layer in layers[:-1]:
        if idx % 2 == 1:
            proof.append(layer[idx - 1])
        elif idx + 1 < len(layer):
            proof.append(layer[idx + 1])
        idx //= 2
    return proof


def verify_inclusion(proof: list[bytes], root: bytes, leaf: bytes) -> bool:
    """Reconstruct root from leaf + proof; True iff matches."""
    h = leaf
    for sibling in proof:
        h = hash_pair(h, sibling)
    return h == root
