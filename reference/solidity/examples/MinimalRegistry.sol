// SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.20;

import {ITAS1Registry} from "../ITAS1Registry.sol";

/// @title  Minimal TAS-1 Level A Registry
/// @notice Bare-bones reference implementation of ITAS1Registry.
///         Anyone can register a run; the registerer is the only
///         address allowed to submit proof bundles for that run.
///         Contributors redeem inclusion proofs permissionlessly.
/// @dev    This implementation is intentionally minimal — no fees,
///         no token issuance, no validator quorum, no fraud proofs.
///         Production deployments are expected to subclass or compose
///         this with their own economic logic.
contract MinimalRegistry is ITAS1Registry {
    struct Run {
        address registerer;
        uint256 contributionWindowEnd;
        bool closed;
    }

    mapping(bytes32 => Run) public runs;
    mapping(bytes32 => mapping(uint256 => bytes32)) public proofBundleRoots;
    mapping(bytes32 => mapping(uint256 => bool)) public proofBundleSubmitted;
    mapping(bytes32 => mapping(bytes32 => bool)) public consumedLeaves;
    mapping(bytes32 => mapping(address => uint256)) public contributorWeight;

    error RunAlreadyRegistered();
    error RunNotRegistered();
    error NotRegisterer();
    error WindowClosed();
    error RunClosed();
    error DuplicateSyncCycle();
    error RootNotSubmitted();
    error LeafAlreadyConsumed();
    error InvalidMerkleProof();

    event TrainingRunClosed(bytes32 indexed runId);

    function registerTrainingRun(
        bytes32 runId,
        uint256 contributionWindowEnd
    ) external {
        if (runs[runId].registerer != address(0)) revert RunAlreadyRegistered();
        runs[runId] = Run({
            registerer: msg.sender,
            contributionWindowEnd: contributionWindowEnd,
            closed: false
        });
        emit TrainingRunRegistered(runId, msg.sender, contributionWindowEnd);
    }

    function submitProofBundle(
        bytes32 runId,
        bytes32 merkleRoot,
        uint256 totalNodes,
        uint256 syncCycle
    ) external {
        Run storage run = runs[runId];
        if (run.registerer == address(0)) revert RunNotRegistered();
        if (msg.sender != run.registerer) revert NotRegisterer();
        if (run.closed) revert RunClosed();
        if (block.timestamp >= run.contributionWindowEnd) revert WindowClosed();
        if (proofBundleSubmitted[runId][syncCycle]) revert DuplicateSyncCycle();

        proofBundleRoots[runId][syncCycle] = merkleRoot;
        proofBundleSubmitted[runId][syncCycle] = true;

        emit ProofBundleSubmitted(runId, syncCycle, merkleRoot, totalNodes);
    }

    function recordContribution(
        bytes32 runId,
        address contributor,
        uint256 weight,
        uint8 contributionType,
        uint256 syncCycle,
        bytes32[] calldata merkleProof
    ) external {
        Run storage run = runs[runId];
        if (run.registerer == address(0)) revert RunNotRegistered();
        if (run.closed) revert RunClosed();
        if (!proofBundleSubmitted[runId][syncCycle]) revert RootNotSubmitted();

        bytes32 leaf = keccak256(
            bytes.concat(
                keccak256(
                    abi.encode(contributor, weight, contributionType, syncCycle)
                )
            )
        );

        if (consumedLeaves[runId][leaf]) revert LeafAlreadyConsumed();

        bytes32 root = proofBundleRoots[runId][syncCycle];
        if (_processProof(merkleProof, leaf) != root) revert InvalidMerkleProof();

        consumedLeaves[runId][leaf] = true;
        contributorWeight[runId][contributor] += weight;

        emit ContributionRecorded(
            runId,
            contributor,
            weight,
            contributionType,
            syncCycle
        );
    }

    function closeTrainingRun(bytes32 runId) external {
        Run storage run = runs[runId];
        if (run.registerer == address(0)) revert RunNotRegistered();
        if (msg.sender != run.registerer) revert NotRegisterer();
        if (run.closed) revert RunClosed();
        run.closed = true;
        emit TrainingRunClosed(runId);
    }

    // ─── Inlined OpenZeppelin MerkleProof (commutative) ─────────────

    function _processProof(bytes32[] calldata proof, bytes32 leaf)
        private
        pure
        returns (bytes32)
    {
        bytes32 computed = leaf;
        uint256 n = proof.length;
        for (uint256 i = 0; i < n; i++) {
            computed = _hashPair(computed, proof[i]);
        }
        return computed;
    }

    function _hashPair(bytes32 a, bytes32 b) private pure returns (bytes32) {
        return a < b
            ? keccak256(abi.encodePacked(a, b))
            : keccak256(abi.encodePacked(b, a));
    }
}
