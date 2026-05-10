# TAS-4 Sketch — ZK Audit Checkpoints (Exploratory Design)

> **Status:** Design exploration. **NOT a published standard.** This document
> will become a proper TAS-4 specification only after (a) TAS-3 is
> normative and shipped, (b) at least one Working Group member has
> operational experience with zk-ML proving systems at production cost,
> and (c) the WG has rough consensus on the open questions below. Do
> not implement against this sketch.
>
> **Author:** Benton Moss
> **Working Group input wanted from:** zk-ML proving system teams (EZKL,
> Modulus Labs, Polyhedra, RiscZero, Succinct), Kaizen / zkLoRA paper
> authors, anyone running production zk-ML proofs at training time
> (rather than inference time).

---

## Why this exists

TAS-3's optimistic fraud proofs reduce trust to a single-honest-party
assumption: as long as one challenger is willing and able to dispute
fraudulent claims within the challenge window, fraud is detected and
slashed. That is a substantial improvement over TAS-2's honest-majority
assumption, but it depends on three things continuing to be true:

1. **Honest challengers are economically motivated.** The bond
   economics in TAS-3 must reward challenge participation enough to
   counterbalance the cost of detecting fraud.
2. **The DA layer remains available.** A long enough DA outage during
   the challenge window can let a fraudulent record finalize.
3. **The challenge window is long enough.** A short window denies
   honest challengers the time to detect, prepare, and submit
   evidence.

TAS-4 removes all three dependencies by **anchoring zero-knowledge
proofs of training-step correctness alongside contribution receipts**.
A receipt with a valid zk proof is finalized immediately on chain
without requiring a challenge window, because the proof itself is the
evidence. There is nothing to dispute.

The technical basis is **Kaizen** (Abbaszadeh et al, eprint 2024/162,
CCS '24, *Kaizen: Zero-Knowledge Proofs of Training for Deep Neural
Networks*) and **zkLoRA**-class proving systems for parameter-efficient
fine-tuning, both already cited in TAS-1 §4.6.4. Adjacent infrastructure
(EZKL, Modulus Labs, RiscZero, SP1) is the proving-system substrate.

The reason TAS-4 sits at the end of the roadmap rather than at the
beginning is **cost.** As of 2026, zk-ML proving for full training is
real but expensive — single-step proofs are tractable, full-cycle
proofs are at the bleeding edge of practicality, full-trajectory
proofs remain research-grade. TAS-4 may be specified before the cost
profile clears production, with implementations adopting it in stages
as the substrate matures.

## Forward-compatibility constraints

TAS-4 is constrained by what TAS-1, TAS-2, and TAS-3 commit to:

1. **TAS-1 leaf formats unchanged.** Layer 1 and Layer 2 leaves remain
   byte-equivalent. A TAS-4 zk proof attaches to a contribution
   receipt as a separate commitment; the receipt itself does not
   change shape.
2. **TAS-2 quorum interface unchanged.** TAS-4 proofs may *replace*
   the quorum (single proof = single source of truth) or *augment* it
   (proof attached to a quorum-recorded receipt). Implementations may
   choose; the spec must permit both.
3. **TAS-3 challenge mechanism remains usable.** A receipt without an
   accompanying TAS-4 proof falls back to TAS-3 challenge semantics. A
   receipt *with* a valid TAS-4 proof bypasses the challenge window
   entirely.
4. **Proof-system agility.** Same shape as TAS-1's hash agility
   (§4.1.2): the standard fixes a verifier interface but is silent on
   which proving system is used (Plonk, Halo2, STARK, Risc0 zkVM,
   SP1 zkVM, etc.).

## The four design axes

### Axis 1 — Proof granularity

**The question:** What is the unit of computation a single TAS-4 proof
covers?

**Options:**
- **Per-gradient** — each gradient's correctness against a known prior
  model state is independently provable. Cleanest cryptographic story
  but the most expensive in aggregate (one proof per gradient × number
  of contributors × number of cycles).
- **Per-cycle** — a single proof covers all of a cycle's accepted
  gradients and the resulting aggregated model update. The most
  natural fit for the existing per-cycle commitment structure of TAS-1.
- **Per-checkpoint** — proofs anchored at training-checkpoint boundaries
  (every K cycles). Coarser but cheaper; matches how Kaizen-style
  systems propose to operate in practice.
- **Per-trajectory** — a single proof for the entire training run.
  Bleeding-edge research; not feasible at frontier-model scale today.

**Most plausible:** per-checkpoint, with the checkpoint cadence
declared per run. Per-cycle is the natural fit if proving cost falls
sufficiently; per-checkpoint is the realistic 2026–2028 fit.

**Open question for the WG:** is the checkpoint cadence standardized
(e.g., every K cycles where K is a power of 2 for tree balance), or
is it fully implementer-declared at run registration?

### Axis 2 — What is being proven

**The question:** A zk proof can attest many things about a training
step. Which thing matters for attribution?

**Candidate claims:**
- **Gradient correctness** — "the gradient hash X is the correct
  fp32-canonical gradient produced by running the loss function on
  contributor Y's claimed batch under the prior model state Z." This
  is the strongest claim and the hardest to prove (model state Z
  alone is hundreds of MB).
- **Aggregation correctness** — "given the set of accepted gradients
  with hashes {X1...Xn}, the aggregated model update was computed
  correctly." Cheaper (the aggregation function is small); doesn't
  prove individual gradient integrity.
- **Validator-score correctness** — "given gradients X1..Xn and the
  validator's stated tolerance bounds, the recorded loss-deltas were
  computed correctly under the declared scoring rule." Useful for
  TAS-2 quorum integrity.
- **Pipeline-stage correctness** (Macrocosmos / Pluralis case) — "the
  forward pass at pipeline stage K produced the activations a stage
  K+1 then operated on." Bound to specific architectures.

**Most plausible:** TAS-4 specifies a *menu* of claim types (each with
a stable claim ID and a public-input/witness schema), and a per-run
declaration of which claims are required for attestation. Implementers
choose the claim set that matches their architecture and cost budget.

**Open question for the WG:** is the menu fixed in the spec (clean
interoperability), open per-implementation (maximum flexibility), or
governed by a registry-style add-process (closest analog to IANA)?

### Axis 3 — Verifier placement

**The question:** Does the chain itself verify TAS-4 proofs, or does
the chain only anchor proof commitments with off-chain verification?

**Trade-off:**
- **On-chain verification** — proof verifies in a transaction; failure
  is immediately slashable; expensive (Groth16 verification is cheap
  enough; STARK verification is borderline; Plonky3 / SP1 is heavier).
- **On-chain commitment, off-chain verification** — proof commitment
  posted on chain; off-chain verifiers (auditors, dispute parties)
  verify and challenge if invalid. Cheaper but reintroduces a form of
  challenge window, partially undoing TAS-4's premise.
- **Hybrid** — on-chain commitment with optional on-chain verification
  (called only on dispute). Most flexible; matches how Eigenlayer-AVS
  and Risc0's settlement model work as of 2026.

**Most plausible:** hybrid. The spec specifies the proof-commitment
format (always on-chain) and the verifier interface (callable on
demand). Implementations decide whether to require verification at
`submitProofBundle` time or only on dispute.

**Open question for the WG:** does the spec require an on-chain
verifier contract address per supported proving system, or just the
commitment format with verifier discovery being implementer's choice?

### Axis 4 — Cost economics and adoption ladder

**The question:** TAS-4 is the most expensive layer of the stack.
When does it make economic sense to adopt, and what does the spec do
to enable graduated adoption?

**Cost benchmarks (rough, 2026):**
- **Per-step proof on a small model (LoRA-scale, < 100M params):**
  feasible in seconds with EZKL / Modulus class systems.
- **Per-cycle proof on a frontier model (> 10B params):** minutes to
  hours per proof; sometimes economical for high-value claims, often
  not.
- **Full-trajectory proof:** research-grade.

**Plausible adoption ladder:**
1. **Light:** TAS-4 proofs for *aggregation correctness only* (cheap;
   useful for TAS-2 quorum integrity).
2. **Medium:** per-cycle proofs covering *validator scoring*
   (validator quorum integrity end-to-end).
3. **Heavy:** per-checkpoint proofs covering *gradient correctness*
   (full TAS-4).

**Open question for the WG:** does the spec name the adoption ladder
(implementations declare which rung they're on, similar to TAS-1's
Level A vs Level B), or stay silent and let market forces sort the
adoption rate?

## Sketched chain interface

```solidity
// NOT NORMATIVE. Subject to Working Group review.

interface ITAS4Verifier {
    // §TAS-4.1 — Proof commitment
    function commitTrainingProof(
        bytes32 runId,
        uint256 cycleStart,
        uint256 cycleEnd,
        uint8   claimType,         // gradient, aggregation, validator-score, ...
        bytes32 publicInputHash,   // hash of the public-inputs vector
        bytes32 proofCommitment    // hash of the actual proof blob
    ) external;

    // §TAS-4.2 — On-demand verification
    function verifyTrainingProof(
        bytes32 runId,
        uint256 cycleStart,
        uint256 cycleEnd,
        bytes calldata publicInputs,
        bytes calldata proofBlob
    ) external returns (bool);

    // §TAS-4.3 — Verifier registration (proving-system agility)
    function registerVerifier(
        uint8   provingSystemId,    // 0=Groth16, 1=Plonk, 2=STARK, ...
        address verifierContract
    ) external;
}
```

## What this sketch is not

- **Not a release.** No tag, no version, no conformance vectors.
- **Not normative.** Implementers MUST NOT cite this document as a
  standard. Use it as design context only.
- **Not a replacement for TAS-1/2/3.** TAS-4 augments the lower
  layers; it does not amputate them. A run may use only TAS-1, or
  TAS-1 + TAS-2, or any prefix of the stack.

## When this becomes TAS-4

The transition from sketch to numbered spec happens when:

1. **TAS-3 is normative** and shipped.
2. **At least one Working Group member** has run a zk-ML proving
   system in production at training time (not just inference time)
   for either gradient correctness or aggregation correctness.
3. **Cost benchmarks for at least one claim type** are published by
   the implementing member, so the spec can be designed around real
   economics rather than projected ones.
4. **Rough consensus** on the proof granularity, claim menu, verifier
   placement, and proving-system agility interface.

The cost criterion is what most distinguishes TAS-4 timing from
TAS-2/3 timing. The technical pieces exist; the economic substrate
needs another year or two of zk-ML proving-system maturation.

## Get involved

The four open questions above are where zk-ML proving-system
production experience changes the outcome. Open an issue at
[github.com/tbmoss3/tas-1/issues](https://github.com/tbmoss3/tas-1/issues)
or join the TAS-1 Working Group via
[`WORKING_GROUP.md`](../../WORKING_GROUP.md).
