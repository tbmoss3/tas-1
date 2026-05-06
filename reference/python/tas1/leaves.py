# SPDX-License-Identifier: CC0-1.0
"""TAS-1 §4.2 / §4.3 — Layer 1 and Layer 2 leaf encodings.

Layer 1 (off-chain Lab Commitment):
    leaf = keccak256(addr(20) || cycle(32_be) || gradient_hash(32))

Layer 2 (on-chain Contribution Record):
    leaf = keccak256(keccak256(abi.encode(
        address contributor,
        uint256 weight,
        uint8   contributionType,
        uint256 syncCycle
    )))

Both leaves are 32 bytes. The Layer 2 outer-keccak-of-inner-keccak
wrapping is the OpenZeppelin canonical form and prevents second-
preimage attacks at the leaf/intermediate-node boundary.
"""

from __future__ import annotations

from eth_abi import encode as abi_encode
from eth_utils import keccak


def _addr_bytes(contributor: str) -> bytes:
    """Normalize a 0x-prefixed (or bare) hex address to 20 bytes, lowercase."""
    raw = contributor.lower().removeprefix("0x")
    if len(raw) > 40:
        raise ValueError(
            f"address must be at most 20 bytes; got {len(raw) // 2}"
        )
    return bytes.fromhex(raw.rjust(40, "0"))


def layer1_leaf(
    contributor: str,
    sync_cycle: int,
    gradient_hash: bytes,
) -> bytes:
    """TAS-1 §4.2 Layer 1 leaf.

    Used by the lab to anchor (contributor, cycle, gradient) tuples
    in the per-cycle Lab Commitment Merkle tree.
    """
    if len(gradient_hash) != 32:
        raise ValueError(
            f"gradient_hash must be 32 bytes; got {len(gradient_hash)}"
        )
    if sync_cycle < 0 or sync_cycle >= 2**256:
        raise ValueError(f"sync_cycle out of uint256 range: {sync_cycle}")

    addr = _addr_bytes(contributor)
    cycle_bytes = sync_cycle.to_bytes(32, "big")
    return keccak(addr + cycle_bytes + gradient_hash)


def layer2_leaf(
    contributor: str,
    weight: int,
    contribution_type: int,
    sync_cycle: int,
) -> bytes:
    """TAS-1 §4.3 Layer 2 leaf.

    Byte-identical to the Solidity construction:
        keccak256(bytes.concat(keccak256(abi.encode(
            contributor, weight, contributionType, syncCycle
        ))))
    """
    if not (0 <= contribution_type <= 255):
        raise ValueError(
            f"contribution_type must fit in uint8; got {contribution_type}"
        )
    if weight < 0 or weight >= 2**256:
        raise ValueError(f"weight out of uint256 range: {weight}")
    if sync_cycle < 0 or sync_cycle >= 2**256:
        raise ValueError(f"sync_cycle out of uint256 range: {sync_cycle}")

    addr = _addr_bytes(contributor)
    encoded = abi_encode(
        ["address", "uint256", "uint8", "uint256"],
        [addr, weight, contribution_type, sync_cycle],
    )
    return keccak(keccak(encoded))
