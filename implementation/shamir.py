"""(t, n)-threshold Shamir secret sharing over a prime field.

Formalized in research/tex/03_shamir_secret_sharing_mpc.tex and used as a
building block by prss.py (dropout recovery) and
compartmented_secret_sharing.py (household-weighted sharing).

A random polynomial of degree t-1 is built with the secret as its constant
term; each participant gets one point on it. Any t points reconstruct the
polynomial (and hence the secret) via Lagrange interpolation; fewer than t
points give no information about it (information-theoretic secrecy).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

# A 127-bit Mersenne prime -- large enough to hold typical secrets used in
# this project (model deltas, non-conformity scores scaled to integers) and
# small enough for fast pure-Python modular arithmetic.
DEFAULT_PRIME = 2**127 - 1


@dataclass(frozen=True)
class Share:
    x: int
    y: int


def split(secret: int, t: int, n: int, prime: int = DEFAULT_PRIME) -> list[Share]:
    """Split `secret` into `n` shares such that any `t` of them reconstruct it.

    Shares are handed out at x = 1, 2, ..., n (x = 0 is reserved for the
    secret itself and is never given to a participant).
    """
    if not (1 <= t <= n):
        raise ValueError("require 1 <= t <= n")
    if not (0 <= secret < prime):
        raise ValueError("secret must be in [0, prime)")

    # Random coefficients a_1..a_{t-1}; a_0 is the secret.
    coeffs = [secret] + [secrets.randbelow(prime) for _ in range(t - 1)]

    def eval_poly(x: int) -> int:
        result = 0
        for c in reversed(coeffs):
            result = (result * x + c) % prime
        return result

    return [Share(x=i, y=eval_poly(i)) for i in range(1, n + 1)]


def _lagrange_coefficient(shares: list[Share], i: int, prime: int) -> int:
    xi = shares[i].x
    num, den = 1, 1
    for j, sj in enumerate(shares):
        if j == i:
            continue
        num = (num * (-sj.x)) % prime
        den = (den * (xi - sj.x)) % prime
    return (num * pow(den, -1, prime)) % prime


def reconstruct(shares: list[Share], prime: int = DEFAULT_PRIME) -> int:
    """Reconstruct the secret from >= t shares via Lagrange interpolation
    at x=0. Passing fewer than the original t shares silently returns a
    wrong value rather than raising -- that is inherent to the scheme (the
    caller is the one who knows what t was used at split-time).
    """
    if not shares:
        raise ValueError("need at least one share")
    total = 0
    for i in range(len(shares)):
        total = (total + shares[i].y * _lagrange_coefficient(shares, i, prime)) % prime
    return total
