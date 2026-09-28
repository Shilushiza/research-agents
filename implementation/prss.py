"""PRSS-style sum-to-zero masking for secure aggregation, with Shamir-based
dropout recovery.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 1.

This implements the *pairwise-masking* instantiation of sum-to-zero secret
sharing (the practical construction used in Bonawitz et al.'s Practical
Secure Aggregation, and a degenerate N-of-N special case of the general
Cramer-Damgard-Ishai PRSS over maximal-unqualified sets described in the
formal writeup). It is scoped deliberately: the fully general (t, N)
construction over combinatorial designs of maximal-unqualified sets is a
larger undertaking and out of scope here.

Setup (once, offline): every ordered pair of participants (i, j) with i < j
shares a PRF key k_{i,j}. A participant i's mask for round `sid` is

    z_i(sid) = sum_{j>i} PRF(k_{i,j}, sid) - sum_{j<i} PRF(k_{j,i}, sid)  (mod p)

Summed over all i in the full participant set, this telescopes to exactly
zero: every PRF(k_{i,j}, sid) term appears once with +1 (contributed by i)
and once with -1 (contributed by j).

Dropout recovery: each participant's own long-term PRF seed is additionally
Shamir-shared among the others at setup time (shamir.py). If a participant
drops mid-round, the remaining participants can jointly reconstruct the
dropped party's seed and remove its masks from the aggregate -- mirroring
Bonawitz et al.'s recovery mechanism.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field

from shamir import Share, reconstruct, split

PRIME = 2**127 - 1

# Seeds are 256-bit (32 raw bytes) and must be shared *without* losing
# information to a modular reduction, so seed-sharing uses its own, wider
# Mersenne prime (2**521-1 > 2**256) -- kept separate from PRIME, which is
# sized for the aggregated values themselves, not for seed material.
SEED_SHARE_PRIME = 2**521 - 1


def _prf(key: bytes, sid: str, modulus: int = PRIME) -> int:
    """A PRF built from HMAC-SHA256, reduced into [0, modulus)."""
    digest = hmac.new(key, sid.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(digest, "big") % modulus


@dataclass
class Participant:
    """One robot taking part in a PRSS-masked aggregation round."""

    pid: int
    n_participants: int
    modulus: int = PRIME
    seed: bytes = field(default_factory=lambda: secrets.token_bytes(32))
    _pairwise_keys: dict[int, bytes] = field(default_factory=dict, init=False)
    _seed_shares_held: dict[int, Share] = field(default_factory=dict, init=False)

    def establish_pairwise_key(self, other: "Participant") -> None:
        """One-time setup: derive a shared PRF key with `other`, deterministic
        given both seeds so both sides compute the same key independently
        (in a real deployment this would run over an authenticated channel,
        e.g. via Diffie-Hellman; here the seeds stand in for that channel).
        """
        lo, hi = sorted((self.pid, other.pid))
        material = self.seed + other.seed if self.pid == lo else other.seed + self.seed
        key = hashlib.sha256(material + f":{lo}:{hi}".encode()).digest()
        self._pairwise_keys[other.pid] = key

    def mask(self, sid: str) -> int:
        """This participant's additive mask for round `sid`. Summed over all
        participants that were present when pairwise keys were set up, this
        is 0 mod `modulus`.
        """
        total = 0
        for other_pid, key in self._pairwise_keys.items():
            term = _prf(key, sid, self.modulus)
            total = (total + term) if other_pid > self.pid else (total - term)
        return total % self.modulus

    def distribute_seed_shares(self, others: list["Participant"], t: int) -> None:
        """Shamir-share this participant's own seed among `others`, so that
        if this participant drops mid-round, >= t of `others` can recover
        the seed (and hence this participant's masks) without it.
        """
        seed_int = int.from_bytes(self.seed, "big")
        shares = split(seed_int, t=t, n=len(others), prime=SEED_SHARE_PRIME)
        for other, share in zip(others, shares):
            other._seed_shares_held[self.pid] = share


def setup_round(participants: list[Participant], recovery_threshold: int) -> None:
    """One-time offline setup: establish all pairwise PRF keys and distribute
    seed shares for dropout recovery.
    """
    for a in participants:
        for b in participants:
            if a.pid != b.pid:
                a.establish_pairwise_key(b)
    for p in participants:
        others = [q for q in participants if q.pid != p.pid]
        p.distribute_seed_shares(others, t=recovery_threshold)


def aggregate(
    contributions: dict[int, int],
    masks: dict[int, int],
    modulus: int = PRIME,
) -> int:
    """Server-side: sum masked values received from participants who did
    respond this round. `contributions` and `masks` are keyed by pid.
    """
    total = 0
    for pid, value in contributions.items():
        total = (total + value + masks[pid]) % modulus
    return total


def recover_dropped_mask(
    dropped_pid: int,
    surviving_participants: list[Participant],
    sid: str,
    modulus: int = PRIME,
) -> int:
    """If `dropped_pid` went offline mid-round, the survivors combine the
    seed shares they were holding for it to reconstruct its seed, rebuild
    its pairwise keys, and recompute the mask it would have contributed --
    so the server can subtract it out of the aggregate.
    """
    shares = [p._seed_shares_held[dropped_pid] for p in surviving_participants
              if dropped_pid in p._seed_shares_held]
    if not shares:
        raise ValueError(f"no seed shares held for dropped participant {dropped_pid}")
    seed_int = reconstruct(shares, prime=SEED_SHARE_PRIME)
    # A correct reconstruction is always < 2**256 (the true seed's width);
    # an incorrect one (too few shares) can exceed it -- fold it back into
    # range rather than crashing, since a below-threshold reconstruction is
    # garbage either way and should simply fail to match the true mask.
    seed = (seed_int % (2**256)).to_bytes(32, "big")

    # Rebuild the dropped participant's mask using the recovered seed.
    total = 0
    for other in surviving_participants:
        lo, hi = sorted((dropped_pid, other.pid))
        material = seed + other.seed if dropped_pid == lo else other.seed + seed
        key = hashlib.sha256(material + f":{lo}:{hi}".encode()).digest()
        term = _prf(key, sid, modulus)
        total = (total + term) if other.pid > dropped_pid else (total - term)
    return total % modulus
