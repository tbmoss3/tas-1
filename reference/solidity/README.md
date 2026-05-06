# TAS-1 Solidity Reference

Public-domain (CC0) reference for the on-chain side of TAS-1 §4.5.

## Files

- [`ITAS1Registry.sol`](ITAS1Registry.sol) — the canonical interface
  every TAS-1 conformant chain implementation MUST expose
- [`examples/MinimalRegistry.sol`](examples/MinimalRegistry.sol) — a
  bare-bones implementation of the interface (no fees, no tokens, no
  validator quorum, no fraud proofs). Production deployments are
  expected to subclass or compose this with their own economic logic.

## Solidity version

Targets `^0.8.20`. Newer compiler versions are fine; the interface
uses no features beyond what 0.8.20 supports.

## Dependencies

`MinimalRegistry.sol` is dependency-free. The OpenZeppelin
`MerkleProof` verification logic is inlined to keep the example
self-contained.

Production implementations SHOULD use the official OpenZeppelin
`MerkleProof.verifyCalldata` for gas efficiency and audit lineage.

## Conformance

The example targets TAS-1 v1.0 Level A. Level B requires off-chain
EIP-191 contributor signature verification, which lives at the
aggregator boundary, not on-chain.
