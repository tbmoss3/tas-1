// SPDX-License-Identifier: CC0-1.0
pragma solidity ^0.8.20;

/// @title TAS-1 Training Attribution Standard — Registry Interface
/// @notice The minimum on-chain surface a TAS-1 conformant chain
///         implementation MUST expose. Implementations MAY add fields
///         (tier, anchor lab, conversion rates, monetization layers)
///         but MUST preserve the lifecycle and event semantics
///         specified in `spec/v1.md` §4.5.
/// @dev    Spec: https://github.com/tbmoss3/tas-1/blob/main/spec/v1.md
interface ITAS1Registry {
    // ─── Events ─────────────────────────────────────────────────────

    /// Emitted when a training run is registered. Implementations MAY
    /// emit additional fields in extended events; they MUST also emit
    /// this canonical form for cross-implementation indexing.
    event TrainingRunRegistered(
        bytes32 indexed runId,
        address indexed registerer,
        uint256 contributionWindowEnd
    );

    /// Emitted when a Lab Commitment / Contribution Aggregate root is
    /// anchored for a (run, sync_cycle).
    event ProofBundleSubmitted(
        bytes32 indexed runId,
        uint256 indexed syncCycle,
        bytes32 merkleRoot,
        uint256 totalNodes
    );

    /// Emitted when a contributor's Layer 2 leaf is consumed and
    /// `weight` is credited to `contributor` under `runId`.
    event ContributionRecorded(
        bytes32 indexed runId,
        address indexed contributor,
        uint256 weight,
        uint8 contributionType,
        uint256 syncCycle
    );

    // ─── Functions ──────────────────────────────────────────────────

    /// Anchor a Merkle root for a (run, sync_cycle). MUST reject:
    ///   - duplicate (runId, syncCycle) submissions
    ///   - submissions after the run's contribution window has closed
    ///   - submissions to a closed run
    ///   - submissions from any party other than the run registerer
    ///     (or a delegated framework address; implementation choice)
    function submitProofBundle(
        bytes32 runId,
        bytes32 merkleRoot,
        uint256 totalNodes,
        uint256 syncCycle
    ) external;

    /// Redeem a Layer 2 inclusion proof and credit `weight` to
    /// `contributor` under `runId`. MUST:
    ///   - reconstruct the leaf per §4.3
    ///   - verify inclusion against the previously-anchored root
    ///   - reject if the leaf has already been consumed
    ///   - mark consumed atomically with the credit
    function recordContribution(
        bytes32 runId,
        address contributor,
        uint256 weight,
        uint8 contributionType,
        uint256 syncCycle,
        bytes32[] calldata merkleProof
    ) external;
}
