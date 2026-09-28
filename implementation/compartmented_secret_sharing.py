"""Household-aware ("знают двое — знает семья") compartmented secret
sharing.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 3.
Reference construction: Simmons (CRYPTO 1990), Brickell (EUROCRYPT 1989/90),
systematized by Ghodosi, Pieprzyk, Safavi-Naini (ACISP 1998).

A flat (t, N)-Shamir scheme treats every robot as an independent trust unit,
which overcounts real collusion resistance when several robots share a
household (same Wi-Fi, same owner, same physical access). This module
implements the practical instantiation recommended in the writeup: each
household gets exactly *one* Shamir share (k_j = 1 per household, which the
writeup argues is almost always the realistic case for 1-3 robots per home),
broadcast to every robot in that household. Reconstruction then requires
shares from `tau` distinct households, not `tau` distinct robots -- i.e. the
threshold is counted over the household footprint h(S), not the raw
participant count |S|.

This is the non-verifiable instantiation. The stronger verifiable-weighted
construction discussed in the "Direction for improvement" section of the
writeup (Shehata et al., arXiv:2505.24289) is not implemented here -- it
needs Bulletproofs-style range proofs that are out of scope for this repo.
"""

from __future__ import annotations

from shamir import Share, reconstruct, split


def household_footprint(present_robots: set[int], household_of: dict[int, int]) -> int:
    """h(S): the number of distinct households represented among
    `present_robots` -- the quantity that should gate reconstruction,
    not len(present_robots).
    """
    return len({household_of[r] for r in present_robots if r in household_of})


def split_by_household(
    secret: int,
    households: dict[int, list[int]],
    tau: int,
) -> dict[int, Share]:
    """Split `secret` with one Shamir share per household (threshold `tau`
    households out of len(households)), and broadcast each household's
    single share to every robot in it.

    Returns a mapping robot_id -> Share.
    """
    household_ids = sorted(households)
    m = len(household_ids)
    if not (1 <= tau <= m):
        raise ValueError("tau must be between 1 and the number of households")

    household_shares = dict(zip(household_ids, split(secret, t=tau, n=m)))

    robot_shares: dict[int, Share] = {}
    for hid, robots in households.items():
        for robot in robots:
            robot_shares[robot] = household_shares[hid]
    return robot_shares


def reconstruct_from_robots(
    robot_shares: dict[int, Share],
    household_of: dict[int, int],
) -> int:
    """Reconstruct the secret from a set of robots' shares, deduplicating by
    household first -- two robots from the same household contribute only
    one effective share, matching the "one vote per household" rule.
    """
    seen_households: dict[int, Share] = {}
    for robot, share in robot_shares.items():
        hid = household_of[robot]
        seen_households.setdefault(hid, share)
    return reconstruct(list(seen_households.values()))
