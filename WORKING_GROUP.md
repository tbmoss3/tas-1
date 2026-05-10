# TAS-1 Working Group

> **Status:** Founding phase. Open to additional members.

## What this is

TAS-1 is a CC0 public-domain standard for cryptographic attribution of
work in decentralized AI training runs. The **TAS-1 Working Group** is
an open consortium of organizations that adopt, implement, and contribute
to the standard.

The Working Group exists so that no single organization owns the standard.
TAS-1's value to any one implementer scales with adoption by every other
implementer; that requires a governance posture that is credibly neutral
to all of them.

## Authorship vs. Working Group

- **Author of TAS-1:** Benton Moss. Independent author of the spec.
- **Working Group members:** organizations that have implemented TAS-1
  (at least Level A) or are actively integrating it. Members do not
  acquire authorship rights over the spec; they participate in its
  evolution as peers.

The split is deliberate: an individual author keeps spec discipline
focused; an open working group keeps adoption credible across competing
implementers.

## Founding members

| Organization | Role | Reference contribution |
|---|---|---|
| **Kardashev Protocol** | Founding member | First reference implementations (Python lab-client + Solidity Registry, Base Sepolia commit `949584d`); first production-bound deployment of Level A. |

## Open invitation

The following organizations are explicitly invited to join the Working
Group as peer members. Inclusion in this list reflects the spec's
acknowledgment of their work in the decentralized-training space; it is
not a claim of endorsement by them.

- Templar / post-Templar successor projects (Covenant-72B lineage)
- Macrocosmos AI (IOTA, Bittensor SN9)
- Pluralis Research (Protocol Learning)
- Gensyn (Verde, RL Swarm)
- Prime Intellect (INTELLECT series, Environments Hub)
- Nous Research (Psyche, DisTrO)
- Any other team building decentralized model-training, attribution, or
  inference-revenue infrastructure

If your organization fits the spirit of the above and is not listed,
please open an issue or PR — the list reflects current attention, not
the limit of who is welcome.

## How to join

Open a pull request that adds your organization to the **Founding
members** table above, including:

1. Organization name and primary contact (GitHub handle or email).
2. Reference implementation link or attestation of intent to ship one
   within ~90 days.
3. Conformance level claimed or targeted (A or B; see spec §5).
4. One-line description of how your project uses or will use TAS-1.

A maintainer (initially: the spec author) will review for spec
compliance and merge. There is no application fee, no exclusivity
clause, no veto power for existing members over new members. The bar
is "you are doing the work the standard describes."

## Membership commitments

By joining the Working Group, a member organization agrees to:

1. **Implement at least Level A.** Pass the conformance suite against
   `test-vectors/`. Self-attest publicly (in your README, docs, or
   release notes).
2. **Participate in spec discussion.** Open issues / file PRs on
   ambiguities, propose extensions, review others' proposals. There is
   no required cadence; participation is expected on the matters that
   affect your implementation.
3. **Attribute the standard.** Reference TAS-1 (and the Working Group)
   in your public-facing material when describing your attribution
   layer. CC0 does not require this; the Working Group asks it as a
   matter of professional practice.
4. **No fees, no exclusivity, no MFN clauses.** Membership is gratis.
   Members are free to operate competing products, fork the standard,
   or leave at any time. The standard is CC0 — there is nothing to
   capture by trying to lock anyone in.

## Governance

While the Working Group is in its founding phase (fewer than three
external members), the spec author serves as the de facto editor. Spec
PRs are merged at the editor's discretion after public review.

Once at least two organizations beyond the founding member have shipped
Level A implementations, the Working Group commits to:

1. **Move the canonical repository to a neutral GitHub organization**
   (e.g., `tas-standard/tas-1`), with the current `tbmoss3/tas-1` URL
   redirecting.
2. **Adopt a lightweight RFC-style proposal process.** One member
   organization, one vote on substantive spec changes. Editor breaks
   ties on procedural matters.
3. **Publish a `GOVERNANCE.md`** documenting the proposal track,
   conflict resolution, and a documented veto rule (e.g., a member
   may block a change that would break their existing Level A
   implementation, with a defined sunset window).

This is the same shape as how ERC-20 evolved under the Ethereum
Foundation: small editorial circle, broad implementer community, no
single foundation controlling the spec even when one foundation
operated the most-used implementation. The aim here is to reach that
posture before the standard ossifies, not after.

## Long-term direction

If TAS-1 sees broad adoption (~5 production deployments across ~3
chains), the Working Group will evaluate moving the standard to an
institutionally-anchored standards track:

- Ethereum Foundation EIP track (most likely fit; spec is EVM-shaped)
- Linux Foundation AI working group
- Independent foundation along the lines of the Ethereum / Apache /
  Linux Foundation models

The decision will be made by the Working Group at the time, on the
evidence then available. The current setup is intentionally minimal so
the standard can move without governance overhead until adoption
warrants it.

## License

This document and the TAS-1 specification are released under
**CC0 1.0 Universal**. Reference implementations are released under
**MIT**. Membership in the Working Group does not change either
license.
