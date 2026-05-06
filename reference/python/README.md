# TAS-1 Python Reference Implementation

Public-domain (CC0) reference implementation of TAS-1 §4.1–§4.4.

## Install

```bash
pip install -e .
```

## Use

```python
import numpy as np
from tas1 import (
    gradient_hash,
    layer1_leaf,
    layer2_leaf,
    build_tree,
    build_proof,
    verify_inclusion,
)

# §4.1 Gradient hash
g = np.array([1.0, 2.0, 3.0], dtype=np.float32)
h = gradient_hash(g)  # 32 bytes

# §4.2 Layer 1 leaf (off-chain Lab Commitment)
l1 = layer1_leaf("0x000000000000000000000000000000000000beef", sync_cycle=1, gradient_hash=h)

# §4.3 Layer 2 leaf (on-chain Contribution Record)
l2 = layer2_leaf(
    "0x000000000000000000000000000000000000beef",
    weight=1000,
    contribution_type=0,
    sync_cycle=1,
)

# §4.4 Merkle tree
root, layers = build_tree([l1, l2])
proof = build_proof(layers, leaf_index=0)
ok = verify_inclusion(proof, root, l1)
```

## Conformance

This implementation is the reference for TAS-1 v1.0 Level A. It does
not enforce §4.6.1 contributor signatures; that's a Level B property
layered on top by aggregators.

Run the conformance suite:

```bash
cd ../../conformance
python run.py
```
