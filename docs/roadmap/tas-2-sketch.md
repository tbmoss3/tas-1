# TAS-2 Sketch — Multi-Validator Quorum (Exploratory Design)

> **Status:** Design exploration. **NOT a published standard.** This document
> will become a proper TAS-2 specification only after (a) TAS-1 has external
> Working Group adopters with production experience to inform the design
> choices, and (b) the Working Group has reached rough consensus on the
> open questions below. Do not implement against this sketch.
>
> **Author:** Benton Moss
> **Working Group input wanted from:** Macrocosmos (CLASP), Templar
> successors (Gauntlet + OpenSkill experience), Pluralis (intrinsic
> attribution), Gensyn (Verde / REE), and any team running a multi-validator
> attribution scheme in production today.

---

## Why this exists, and why now

TAS-1 v1 acknowledges its own central limitation in §Security Considerations:
**the lab is the trust anchor.** A malicious lab can refuse to commit honest
contributions, fabricate commitments, or selectively reorder cycles. TAS-1
makes lab behavior auditable but not enforceable.

TAS-2 is the version of the standard that removes the lab from the trust
anchor by requiring **multi-validator attestation** before a contribution
record is anchored on chain. The idea is not novel — Templar's Gauntlet
system, Macrocosmos's CLASP scoring, and prior validator-bonded designs in
non-AI substrates (Bittensor, Cosmos) all converge on the same primitives:
a stake-bonded validator set, a score-aggregation rule, slashing for
provably divergent reports.

**What's novel about doing this as a TAS standard** is the same thing that
was novel about TAS-1: writing down the bytes on the wire and the leaf
semantics so that a quorum receipt produced by network A can be verified
by tooling from network B. Without a standard, every project will continue
to ship its own incompatible quorum scheme.

This sketch exists *now* (rather than after TAS-2 is implemented) because
it serves as **recruiting collateral for the TAS-1 Working Group.** A team
considering TAS-1 adoption deserves to see the trajectory the standard
intends to follow. A team with production validator-quorum experience —
Templar successors, Macrocosmos, Gensyn — deserves a place to weigh in on
what TAS-2 should standardize before any of it is normative.

## Forward-compatibility constraints

TAS-2 is constrained by what TAS-1 v1 has already committed to:

1. **Layer 1 leaf format (`§4.2`) MUST remain byte-equivalent.** A TAS-1
   Lab Commitment is still a Lab Commitment under TAS-2. Existing v1
   adopters' Layer 1 trees do not break.
2. **Layer 2 leaf format (`§4.3`) MUST remain byte-equivalent at the leaf
   level.** TAS-2 may add new leaf encodings (validator attestations, loss
   reports) but the Contribution Record leaf does not change.
3. **The chain interface (`ITAS1Registry`) MUST extend, not replace.**
   TAS-2 introduces `ITAS2Registry extends ITAS1Registry`. A TAS-1 Level
   A implementation upgrades to TAS-2 by *adding* validator-related
   functions, not by reshaping the existing ones.
4. **Replay protection (`§4.5`) extends.** The same `consumedLeaves` set
   prevents Layer 2 double-credit; a new validator-attestation set
   prevents validator double-vote.

These constraints exist so that TAS-1 adopters do not face a forced
migration when TAS-2 ships.

## The four design axes

The design space is open. The Working Group's choice on each axis should
be informed by which choices have been validated in production, not by
this sketch's preferences.

### Axis 1 — Validator set composition

**The question:** Who can be a validator, and how do they enter / exit?

**Existing approaches in the field:**
- **Templar (Bittensor SN3):** Validator set = Bittensor validators with
  stake on SN3. Score: Gauntlet system with OpenSkill rankings updated
  per epoch. Exit: stake unbonding period.
- **Macrocosmos IOTA (Bittensor SN9):** CLASP-based scoring with
  pipeline-stage attribution. Validators rotate through pipeline stages.
- **Bittensor general:** Permissionless registration with stake
  threshold; tao-locked.
- **Cosmos / Tendermint:** Top-N by stake, bonded validator set, formal
  governance rotations.

**For TAS-2 to standardize:** the *interface* (what bytes describe a
validator's identity, stake, status), not the *policy* (how validators
are selected, how stake thresholds are set). Policy stays implementer's
choice; the interface stays interoperable.

**Open question for the Working Group:** is `(address validator, uint256 stake, uint256 bondedAt, uint256 unbondingAt)` enough? Or does the standard need to anchor more (e.g., capability declarations, slashing history)?

### Axis 2 — Score aggregation

**The question:** Given N validators each report a contributor's
loss-delta (or weight) for a cycle, how is the canonical value derived?

**Existing approaches:**
- **Templar / Gauntlet:** OpenSkill ranking aggregated per cycle; the
  median (not mean) of validator loss-delta reports is treated as ground
  truth, with outlier reports flagged.
- **Bittensor general:** Yuma Consensus — weighted median of validator
  scores.
- **Pluralis Protocol Learning:** weight is intrinsic to the architecture
  (no participant has full model), so the validator quorum question
  becomes "did the gradient even verify against the contributor's held
  shards" rather than "is this loss-delta honest."
- **Optimistic / fraud-proof:** treat one validator's report as canonical
  with a challenge window (TAS-3 territory; deferred).

**For TAS-2 to standardize:** the *byte format of a `LossReport` leaf*
(cycle, contributor, validator, lossDelta, signature) and the *aggregation
function* (median? truncated mean? Yuma-style?). Different protocols may
need different aggregation rules; the question is whether to standardize
one or to make it a per-run parameter.

**Open question for the Working Group:** does TAS-2 specify a single
aggregation function (highest interoperability) or expose `aggregationRule`
as a per-run enum (highest flexibility)? The trade-off is identical to
the hash-agility question raised in TAS-1's EM thread.

### Axis 3 — Bond and slashing

**The question:** What does a validator stake, and what causes them to
lose it?

**Existing approaches:**
- **Templar:** TAO stake on SN3; slashing via emission reduction rather
  than direct burn.
- **Bittensor general:** Yuma slashing for validators whose weights
  diverge from consensus; recovery via rebonding.
- **Cosmos:** Direct stake slashing on double-sign; partial slashing on
  liveness failures.
- **Eigenlayer-style restaking:** slashing conditions are application-defined
  on top of restaked ETH/LSTs.

**For TAS-2 to standardize:** the *evidence format* for a slashable event
(divergent report + the actual aggregated value + sufficient validator
quorum for the alternative). The actual stake denomination and slashing
percentages stay implementer's choice — a Bittensor TAS-2 implementation
slashes TAO; an EVM-native implementation slashes whatever the lab's
chosen bond token is.

**Open question for the Working Group:** does TAS-2 require a specific
slashing condition (e.g., "report differs from aggregated value by more
than K standard deviations"), or does it specify only the *evidence
format* and let implementations define the threshold? The trade-off is
between hard interoperability of slashing logic and flexibility for
different attack-cost models.

### Axis 4 — Divergence handling

**The question:** What happens when validators honestly disagree?

This is the subtlest of the four axes and the one most worth the
Working Group's collective experience. Honest disagreement is not the
same as malicious divergence:

- A validator may sample a different mini-batch and produce a different
  loss-delta on the same gradient. This is *measurement noise*, not
  dishonesty.
- A validator may be temporarily out-of-sync on the model state (e.g.,
  applied a different prior cycle's aggregated update). This is
  *liveness*, not dishonesty.
- A validator may have hardware that produces fp32 results that differ
  in the last bit from the canonical aggregated state. This is
  *determinism boundary*, not dishonesty.

**For TAS-2 to standardize:** the *boundary between "noise" and
"divergence"* — likely a tolerance parameter (`epsilon`) below which
disagreement is non-slashable. Exact tolerance is implementation-defined;
the *byte format that records "tolerance was exceeded by this much"* is
not.

**Open question for the Working Group:** anyone running validator quorum
in production today has fought this fight. What does experience say is
the right tolerance shape — absolute, relative, or hybrid?

## Sketched chain interface

```solidity
// NOT NORMATIVE. Subject to Working Group review.

interface ITAS2Registry is ITAS1Registry {
    // §TAS-2.1 — Validator state
    function registerValidator(uint256 stake) external;
    function unbondValidator() external;
    function getValidator(address validator) external view
        returns (uint256 stake, uint256 bondedAt, uint256 unbondingAt);

    // §TAS-2.2 — Loss reports (one validator → one contributor → one cycle)
    function submitLossReport(
        bytes32 runId,
        uint256 syncCycle,
        address contributor,
        int256  lossDelta,         // canonical units TBD
        bytes calldata signature   // EIP-191 over (runId,cycle,contributor,lossDelta)
    ) external;

    // §TAS-2.3 — Aggregated contribution record (replaces unilateral lab
    // recordContribution from TAS-1 §4.5 once quorum threshold is met)
    function recordQuorumContribution(
        bytes32 runId,
        uint256 syncCycle,
        address contributor,
        uint256 weight,            // derived from aggregated lossDelta
        bytes32 evidenceRoot       // Merkle root over the validator reports
    ) external;

    // §TAS-2.4 — Slashing
    function challengeReport(
        bytes32 runId,
        uint256 syncCycle,
        address divergentValidator,
        bytes32 evidenceRoot
    ) external;
}
```

This is illustrative scaffolding. The function signatures, the event
shapes, and the Merkle-evidence format are all open questions the
Working Group should resolve.

## What this sketch is not

- **Not a release.** No tag, no version number, no conformance vectors.
- **Not normative.** Implementers MUST NOT cite this document as a
  standard. Use it as design context only.
- **Not exhaustive.** TAS-3 (optimistic fraud proofs) and TAS-4 (zk
  audit checkpoints) sit one and two layers further from the lab-trust
  anchor; both are anticipated but not sketched here.

## When this becomes TAS-2

The transition from sketch to numbered spec happens when the TAS-1
Working Group has:

1. **At least two external members** (besides the founding member,
   Kardashev Protocol) shipping Level A or Level B TAS-1 implementations
   in production.
2. **At least one member** running a validator quorum in production
   under their own attribution scheme — i.e., someone who can speak to
   the four axes above from operational experience.
3. **Rough consensus** on the chain interface, the loss-report leaf
   format, the aggregation rule, and the slashing evidence format.

Until then, this sketch exists to make the trajectory legible, not to
prescribe it.

## Get involved

If you have production experience running validator quorums for
gradient or contribution attribution — Templar, Macrocosmos, Gensyn,
Pluralis, or anywhere else — the four open questions above are exactly
where your input changes the outcome. Open an issue at
[github.com/tbmoss3/tas-1/issues](https://github.com/tbmoss3/tas-1/issues)
or join the TAS-1 Working Group via [`WORKING_GROUP.md`](../../WORKING_GROUP.md).
