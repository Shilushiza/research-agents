"""Combine PRSS sum-to-zero masking with Paillier encryption ("key-homomorphic
masking").

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, the
subsection "PRSS и Paillier не взаимоисключающие --
их можно совместить", citing LERNA (ASIACRYPT 2023),
DMSA-FL and V-MHESA.

Threshold-Paillier by itself does not stop a t-of-n coalition from
decrypting a single participant's ciphertext c_i instead of the intended
aggregate -- nothing in the protocol forbids that operation. Masking each
value before encrypting closes that gap: decrypting c_i alone yields
x_i + z_i, not x_i, and z_i is protected by a separate PRF-key structure
that the decryption coalition does not automatically hold.

    c_i = Enc(pk, (x_i + z_i(sid)) mod n),     sum_i z_i(sid) = 0 (mod n)
    prod_i c_i = Enc(pk, sum_i x_i (mod n))     -- masks cancel exactly as
                                                    in plain PRSS

Deliberately reuses prss.Participant (with modulus set to the Paillier
public key's n, so the sum-to-zero property lines up with Paillier's
plaintext space) and paillier.PublicKey -- no new cryptography, just the
composition described in the formal writeup.
"""

from __future__ import annotations

from paillier import PublicKey
from prss import Participant, setup_round


def masked_encrypt(participant: Participant, x: int, sid: str, public: PublicKey) -> int:
    if participant.modulus != public.n:
        raise ValueError(
            "participant must be set up with modulus == public.n for the "
            "sum-to-zero property to hold in the Paillier plaintext space"
        )
    masked_value = (x + participant.mask(sid)) % public.n
    return public.encrypt(masked_value)


def aggregate_ciphertexts(ciphertexts: list[int], public: PublicKey) -> int:
    acc = public.encrypt(0)
    for c in ciphertexts:
        acc = public.add(acc, c)
    return acc


def setup_masked_participants(n_robots: int, public: PublicKey) -> list[Participant]:
    participants = [Participant(pid=i, n_participants=n_robots, modulus=public.n)
                     for i in range(n_robots)]
    setup_round(participants, recovery_threshold=max(2, n_robots - 1))
    return participants
