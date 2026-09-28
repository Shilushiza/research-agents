"""N-of-N distributed decryption for Paillier.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 2
("threshold-HE").

Scope, stated honestly: this implements full-participation (N-of-N)
distributed decryption -- every decryption server must take part, not an
arbitrary t-of-n subset. Genuine (t, n) threshold Paillier (Shoup's
Delta = n! Lagrange-interpolation-in-the-exponent construction, used by
Fouque-Poupard-Stern and Damgaard-Jurik) supports partial subsets and is
real future work, not implemented here -- it is a substantially more
intricate construction and getting the integer scaling subtly wrong would
silently produce a broken (not just less general) primitive. N-of-N still
gives the property this project actually needs: no single server (and not
even the combiner) ever holds enough to decrypt alone.

Why decryption needs two secrets split, not one: mu = lambda^{-1} mod n, and
since lambda(n) < n always holds for Paillier, knowing mu (and public n) is
enough to recover lambda exactly -- so mu is just as sensitive as lambda and
must be split too, not handed to a "trusted combiner" in the clear.

Protocol (semi-honest / honest-but-curious servers, matching threat-model
class A1 in 07_threat_model.tex):

  Setup (trusted dealer, once): split private_key.lam into n non-negative
  integers summing to it exactly (an integer composition -- no modular
  reduction, see the note in deal_lambda_shares); split private_key's mu
  into n integers summing to it mod n (ordinary additive secret sharing).
  Each server gets one lambda-share and one mu-share.

  Per ciphertext c:
    1. Each server computes partial_i = c^{lambda_share_i} mod n^2.
    2. The combiner multiplies all partial_i mod n^2 to get
       u = c^lambda mod n^2 (this alone reveals nothing about m without mu).
    3. The combiner computes L(u) (public arithmetic, no secret involved).
    4. Each server computes L(u) * mu_share_i mod n and returns it.
    5. The combiner sums these mod n to recover m.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from paillier import PrivateKey, PublicKey, l_function


def _integer_composition(total: int, parts: int) -> list[int]:
    """Split `total` into `parts` non-negative integers that sum to it
    exactly, via random cut points -- no modular reduction, so this is safe
    to use for splitting an exponent (lambda) without the group-order
    subtleties that modular exponent-sharing would introduce.
    """
    if parts < 2:
        raise ValueError("need at least 2 parts")
    cuts = sorted(secrets.randbelow(total + 1) for _ in range(parts - 1))
    points = [0, *cuts, total]
    return [points[i + 1] - points[i] for i in range(parts)]


@dataclass
class DecryptionServer:
    server_id: int
    lambda_share: int
    mu_share: int
    public: PublicKey

    def partial_lambda_decrypt(self, c: int) -> int:
        return pow(c, self.lambda_share, self.public.n_sq)

    def partial_mu_combine(self, l_of_u: int) -> int:
        return (l_of_u * self.mu_share) % self.public.n


def deal_shares(private_key: PrivateKey, n_servers: int) -> list[DecryptionServer]:
    """Trusted-dealer setup: split lam and mu across `n_servers` servers."""
    lambda_shares = _integer_composition(private_key.lam, n_servers)

    mu_shares = [secrets.randbelow(private_key.public.n) for _ in range(n_servers - 1)]
    mu_shares.append((private_key.mu - sum(mu_shares)) % private_key.public.n)

    return [
        DecryptionServer(
            server_id=i,
            lambda_share=lambda_shares[i],
            mu_share=mu_shares[i],
            public=private_key.public,
        )
        for i in range(n_servers)
    ]


def threshold_decrypt(c: int, servers: list[DecryptionServer]) -> int:
    """Run the full 5-step protocol described in the module docstring."""
    if len(servers) < 2:
        raise ValueError("need at least 2 decryption servers")
    public = servers[0].public
    n_sq = public.n_sq

    u = 1
    for s in servers:
        u = (u * s.partial_lambda_decrypt(c)) % n_sq

    l_of_u = l_function(u, public.n)

    m = 0
    for s in servers:
        m = (m + s.partial_mu_combine(l_of_u)) % public.n
    return m
