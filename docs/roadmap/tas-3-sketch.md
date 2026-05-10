# TAS-3 Sketch — Optimistic Fraud Proofs (Exploratory Design)

> **Status:** Design exploration. **NOT a published standard.** This document
> will become a proper TAS-3 specification only after (a) TAS-2 is
> normative and shipped by at least one Working Group member, (b) one
> member has operational experience with floating-point fraud proofs
> (TAO-style tolerance-aware verification), and (c) the WG has rough
> consensus on the open questions below. Do not implement against this
> sketch.
>
> **Author:** Benton Moss
> **Working Group input wanted from:** any team with optimistic-rollup
> dispute-game experience (Arbitrum, Optimism), refereed-computation
> experience (Gensyn Verde, Truebit), or floating-point-tolerance
> verification experience (TAO authors, anyone running cross-hardware
> reproducibility audits in production).

---

## Why this exists

TAS-2's multi-validator quorum reduces lab trust by requiring honest
majority among validators. That is a meaningful improvement, but it
still rests on an honest-majority assumption: a colluding validator
super-majority can credit fabricated contributions or refuse to credit
honest ones, and there is no mechanism inside TAS-2 to overturn them.

TAS-3 reduces trust further by introducing an **optimistic challenge
mechanism**: any single honest party can dispute a recorded
contribution by demonstrating, via interactive bisection, that the
gradient computation does not reproduce within tolerance. A successful
challenge slashes the malicious validator quorum and rewrites the
contribution record. The honest-majority assumption falls back to a
single-honest-party assumption.

The technical basis is **TAO** (Yao et al, arxiv 2510.16028,
*Tolerance-Aware Optimistic Verification for Floating-Point Neural
Networks*), already cited in TAS-1 §4.6.4. TAO solves the problem that
makes naive optimistic-rollup-style bisection unusable for neural-net
training: floating-point computations are non-deterministic across
hardware, and a strict bit-equality bisection rule false-positives on
honest hardware divergence.

## Forward-compatibility constraints

TAS-3 is constrained by what TAS-1 and TAS-2 have already committed to:

1. **TAS-1 leaf formats unchanged.** Layer 1 and Layer 2 leaves remain
   byte-equivalent. A TAS-3 challenge does not modify the receipt; it
   triggers a separate state machine that may *invalidate* a receipt
   after the fact, recorded as a challenge outcome event.
2. **TAS-2 validator-quorum interface unchanged.** TAS-3 challenges run
   *against* the quorum's output; they do not replace the quorum.
3. **No new chain-side requirements on the contributor.** A contributor
   who only ever wants to submit gradients and redeem inclusion proofs
   should never need to know TAS-3 exists. Challenge participation is
   an opt-in role.
4. **Witness data-availability is required**, and is the single largest
   open question (see Axis 3 below).

## The four design axes

### Axis 1 — Bisection granularity

**The question:** What is the unit of disputed computation in the
bisection game?

**Options:**
- **Instruction-level** (Arbitrum, Optimism) — bisect down to a single
  EVM/WASM instruction. Cleanest dispute resolution but generates very
  long bisection games for any non-trivial computation. Almost certainly
  wrong granularity for neural-net training.
- **Operator-level** (TAO's design) — bisect down to a single tensor
  operator (matmul, layernorm, softmax, etc.). Each operator has a
  well-defined input → output mapping verifiable on chain with a small
  evaluator contract. Bisection depth = O(log N) where N is the
  operator count of a forward+backward pass.
- **Gradient-step-level** — bisect down to a single optimizer step.
  Coarser; less precise about *where* the divergence happened, but
  cheaper to verify. Loses TAO's per-operator tolerance bounds.
- **Cycle-level** (no bisection) — single-round assertion: lab claims
  weight W; challenger claims weight W'; both compute and the chain
  picks. Untenable for any realistic gradient size.

**Most plausible:** operator-level, following TAO. Each operator is
small enough to evaluate in a single transaction with the right
evaluator contract.

**Open question for the WG:** is the operator catalog (matmul +
layernorm + softmax + GELU + ...) standardized in TAS-3, or is it
implementer's choice? Standardizing fixes the verifier; leaving it
open lets implementations mix in custom operators (e.g., flash
attention variants, quantization kernels).

### Axis 2 — Tolerance bounds

**The question:** Two honest validators on different hardware will
produce bit-different results for the same operator on the same input.
How does the bisection game distinguish "honest divergence" from
"malicious divergence"?

**This is the load-bearing problem.** It is what makes naive
optimistic-rollup designs unusable for neural-net training and what
TAO solves.

**Approaches:**
- **Per-operator empirical percentile bounds** (TAO) — for each
  operator, derive a tolerance ε from observed cross-hardware variance.
  Disagreement within ε is non-slashable; disagreement outside ε is
  slashable. The bounds are derived empirically from a corpus of
  honest-hardware runs.
- **Per-operator IEEE-754-derived bounds** — compute analytic worst-case
  rounding error for each operator under fp32 round-to-nearest-even.
  Tighter than empirical for some ops; loose for others (matmul over
  long reduction dimensions has empirically much smaller divergence
  than worst-case analysis).
- **Hybrid** (TAS-1 §4.6.4 gestures at this) — use IEEE-754 bounds as a
  hard ceiling; use empirical percentiles as the operative slashing
  threshold.

**Open question for the WG:** does TAS-3 specify *the* tolerance rule,
or specify the *interface* by which a per-run tolerance schedule is
declared and held to? The trade-off is interoperability vs accommodating
specialty hardware (TPUs, Blackwell fp8, Trainium) whose tolerance
profiles differ.

### Axis 3 — Witness data availability

**The question:** Who stores the gradient computation graph that a
challenge needs to bisect, and how is that storage attested?

**This is the second hardest problem.** Without the gradient computation
graph, there is nothing to bisect. With it, you need a DA commitment
that survives the challenge window.

**Approaches:**
- **Fully on-chain** — gas-prohibitive. Out.
- **Lab-side storage with a DA commitment** — lab posts a Merkle
  commitment over the gradient computation graph at `submitProofBundle`
  time; lab is obligated to serve any leaf on demand during the
  challenge window. Slashable for non-availability.
- **DA-layer storage** (Celestia, EigenDA, Avail) — lab posts the
  computation graph blob to a data-availability layer; the chain
  contract verifies the DA proof rather than holding the data.
- **Erasure-coded peer storage** — contributor and validators each hold
  shards; reconstructable on challenge.

**Most plausible:** DA-layer storage with a Celestia/EigenDA blob and
on-chain commitment. The economic and engineering primitives for this
exist as of 2026; the standardization burden is just choosing the
attestation format.

**Open question for the WG:** is the DA layer standardized (one
endpoint), declared per run (any approved DA layer), or fully open
(any DA layer with a verifiable inclusion proof contract on the same
chain)?

### Axis 4 — Challenge bond and window economics

**The question:** What does a challenger stake, what's the slashing
ratio on a failed challenge, and how long is the challenge window?

**Constraints:**
- **Bond too low** → griefing attack: spurious challenges raise lab
  operational cost without genuine fraud signal.
- **Bond too high** → only deep-pocketed challengers participate; small
  honest contributors can't dispute fraudulent omissions.
- **Window too short** → honest challengers don't have time to detect
  and prepare evidence.
- **Window too long** → contributor capital tied up in unredeemable
  receipts; on-chain consumed-leaves set bloats.

**Existing data points:**
- Arbitrum: ~7 day challenge window, no challenger bond required (Nitro
  fraud proofs).
- Optimism (Cannon): ~7 day window, ~ETH bond on assertion.
- Bittensor disputes: epoch-window, validator stake.

**Open question for the WG:** is the bond denominated in the lab's
stake token (slashable from the same pool as TAS-2 quorum stake), in a
neutral asset (ETH, USDC), or in a TAS-3-specific challenge bond?

## Sketched challenge contract interface

```solidity
// NOT NORMATIVE. Subject to Working Group review.

interface IChallengeManager {
    // §TAS-3.1 — Open a challenge against a recorded contribution
    function openChallenge(
        bytes32 runId,
        uint256 syncCycle,
        address contributor,
        bytes32 daCommitment    // commitment to gradient computation graph
    ) external payable returns (bytes32 challengeId);

    // §TAS-3.2 — Bisection step
    function bisect(
        bytes32 challengeId,
        bytes32 agreedAncestor,
        bytes32 leftRoot,
        bytes32 rightRoot
    ) external;

    // §TAS-3.3 — Operator-level resolution (terminal step)
    function assertOperator(
        bytes32 challengeId,
        uint256 operatorIdx,
        bytes calldata operatorInputs,
        bytes calldata claimedOutput,
        uint256 declaredTolerance
    ) external;

    // §TAS-3.4 — Resolution after operator assertion + on-chain replay
    function resolveChallenge(bytes32 challengeId) external;

    // §TAS-3.5 — DA non-availability claim
    function claimNonAvailability(
        bytes32 challengeId,
        bytes calldata daProofOfMissingLeaf
    ) external;
}
```

## What this sketch is not

- **Not a release.** No tag, no version, no conformance vectors.
- **Not normative.** Implementers MUST NOT cite this document as a
  standard. Use it as design context only.
- **Not a substitute for TAS-2.** TAS-3 challenges run against a
  TAS-2-recorded contribution; the standards are sequential, not
  alternative.

## When this becomes TAS-3

The transition from sketch to numbered spec happens when:

1. **TAS-2 is normative** and shipped by at least one Working Group
   member in production.
2. **At least one Working Group member** has run an
   optimistic-fraud-proof system in production for floating-point
   computation — Gensyn (Verde), an Arbitrum/Optimism team adapting
   their dispute game, or anyone implementing TAO directly.
3. **Rough consensus** on the bisection granularity, tolerance-bound
   rule, witness-DA attestation format, and bond economics.

## Get involved

The four open questions above are exactly where production experience
in floating-point dispute games (TAO, Gensyn Verde, Truebit
adaptations) changes the outcome. Open an issue at
[github.com/tbmoss3/tas-1/issues](https://github.com/tbmoss3/tas-1/issues)
or join the TAS-1 Working Group via
[`WORKING_GROUP.md`](../../WORKING_GROUP.md).
