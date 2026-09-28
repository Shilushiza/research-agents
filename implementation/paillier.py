"""Plain (single-key) Paillier additively homomorphic encryption.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 2.
Reference: Paillier, "Public-Key Cryptosystems Based on Composite Degree
Residuosity Classes", EUROCRYPT 1999.

Key sizes here are demonstration-scale (a few hundred bits per prime, not the
2048+ bits a production deployment would need) -- kept small so keygen and
the test suite run in well under a second. Everything else (encryption
correctness, additive homomorphism) is the real algorithm, not a toy
simplification.

threshold_paillier.py builds threshold decryption on top of the KeyPair
defined here.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from math import gcd

import sympy


def _random_prime(bits: int) -> int:
    lo = 1 << (bits - 1)
    hi = (1 << bits) - 1
    return sympy.randprime(lo, hi)


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def l_function(u: int, n: int) -> int:
    """The L function from Paillier's paper: L(u) = (u - 1) / n. Public --
    threshold_paillier.py needs it too, since combining partial decryptions
    means applying L to a jointly-computed u without either secret being
    revealed on its own.
    """
    return (u - 1) // n


_l = l_function  # short alias used internally in this module


@dataclass(frozen=True)
class PublicKey:
    n: int
    g: int

    @property
    def n_sq(self) -> int:
        return self.n * self.n

    def encrypt(self, m: int, r: int | None = None) -> int:
        if not (0 <= m < self.n):
            raise ValueError("plaintext must be in [0, n)")
        if r is None:
            r = secrets.randbelow(self.n - 1) + 1
            while gcd(r, self.n) != 1:
                r = secrets.randbelow(self.n - 1) + 1
        n_sq = self.n_sq
        return (pow(self.g, m, n_sq) * pow(r, self.n, n_sq)) % n_sq

    def add(self, c1: int, c2: int) -> int:
        """Homomorphic addition: Enc(m1) * Enc(m2) = Enc(m1 + m2)."""
        return (c1 * c2) % self.n_sq


@dataclass(frozen=True)
class PrivateKey:
    lam: int  # lambda(n) = lcm(p-1, q-1)
    mu: int   # mu = (L(g^lambda mod n^2))^{-1} mod n
    public: PublicKey

    def decrypt(self, c: int) -> int:
        n_sq = self.public.n_sq
        u = pow(c, self.lam, n_sq)
        return (_l(u, self.public.n) * self.mu) % self.public.n


@dataclass(frozen=True)
class KeyPair:
    public: PublicKey
    private: PrivateKey


def keygen(bits: int = 256) -> KeyPair:
    """Generate a Paillier keypair. `bits` is the size of each prime factor
    p, q (so n = p*q is ~2*bits wide) -- see the module docstring about the
    demonstration-scale default.
    """
    while True:
        p = _random_prime(bits)
        q = _random_prime(bits)
        if p == q:
            continue
        n = p * q
        if gcd(n, (p - 1) * (q - 1)) != 1:
            continue
        lam = _lcm(p - 1, q - 1)
        g = n + 1  # standard simplified generator choice (valid since gcd(n,lam)=1)
        n_sq = n * n
        u = pow(g, lam, n_sq)
        mu = pow(_l(u, n), -1, n)
        public = PublicKey(n=n, g=g)
        private = PrivateKey(lam=lam, mu=mu, public=public)
        return KeyPair(public=public, private=private)
