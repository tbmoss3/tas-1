# SPDX-License-Identifier: CC0-1.0
"""TAS-1 §4.1 — Canonical gradient-tensor hashing.

A gradient tensor is serialized as:

    header     = u32_le(rank) || u32_le(dim_0) || ... || u32_le(dim_{rank-1})
    payload    = tensor as IEEE 754 binary32 little-endian, C-contiguous bytes
    serialized = header || payload
    gradient_hash = keccak256(serialized)

dtype is enforced as float32. Callers MUST cast fp16/bf16/fp64 tensors
to fp32 before hashing (this module performs the cast automatically for
any floating-point input dtype).
"""

from __future__ import annotations

import struct

import numpy as np
from eth_utils import keccak


def serialize_tensor(tensor: np.ndarray) -> bytes:
    """Encode a numpy ndarray as canonical TAS-1 bytes for hashing.

    Casts to float32 if the input is a different floating-point dtype.
    Rejects integer or complex dtypes — gradients must be real-valued
    floats.
    """
    if tensor.dtype.kind != "f":
        raise TypeError(
            f"gradient tensor must have float dtype; got {tensor.dtype}"
        )

    arr = np.ascontiguousarray(tensor.astype(np.float32))
    shape = arr.shape

    header = struct.pack("<I", len(shape))
    for dim in shape:
        header += struct.pack("<I", dim)

    return header + arr.tobytes(order="C")


def gradient_hash(tensor: np.ndarray) -> bytes:
    """Return the canonical 32-byte keccak256 hash of a gradient tensor."""
    return keccak(serialize_tensor(tensor))
