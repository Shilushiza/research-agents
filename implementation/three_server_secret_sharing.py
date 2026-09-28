"""
Three-server additive secret sharing for secure summation of robot values.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 4
(Prio/ABY3-style multi-server split). Threat model: research/tex/07_threat_model.tex.

Each robot i splits its private value x_i into 3 additive shares mod p and sends
one share to each of 3 servers. Each server locally sums the shares it receives
across all robots -- no interaction between servers is needed for this step,
because summation is linear. The final aggregate sum(x_i) is recovered only by
combining all 3 partial sums at reveal time.

Security holds as long as the 3 servers do not all collude (informal assumption --
see 07_threat_model.tex, class A7). Any single server's view (its column of
shares) is individually uniformly random and reveals nothing about the x_i values
on its own -- demonstrated empirically in demo_no_single_server_leaks() below.

This is the plain 3-out-of-3 additive variant: correctness requires all 3 servers
to report their partial sum. It does not tolerate a dropped server. The natural
next step (documented, not implemented here) is to upgrade to ABY3-style
replicated 2-out-of-3 sharing, where each server holds 2 of the 3 shares per
value, so that losing 1 server still allows reconstruction.
"""

from __future__ import annotations

import secrets
import statistics
from dataclasses import dataclass, field

# A prime modulus for arithmetic (2**61 - 1, a Mersenne prime -- large enough
# that real robot values (bounded floats scaled to integers) never wrap around
# in the demo below, small enough to keep the numbers readable when printed).
MODULUS = 2**61 - 1


def split_secret(x: int, modulus: int = MODULUS) -> tuple[int, int, int]:
    """Split x into 3 additive shares mod `modulus`: x == s1 + s2 + s3 (mod p).

    s1, s2 are drawn uniformly at random; s3 is fixed so the sum is correct.
    Any single share, or any two shares without the third, is uniformly
    random and independent of x -- this is what makes a lone server's view
    uninformative.
    """
    if not (0 <= x < modulus):
        raise ValueError(f"x={x} must be in [0, modulus)")
    s1 = secrets.randbelow(modulus)
    s2 = secrets.randbelow(modulus)
    s3 = (x - s1 - s2) % modulus
    return s1, s2, s3


@dataclass
class Server:
    """One of the 3 non-colluding aggregation servers.

    A server never sees a robot's raw value x_i, only the one share routed
    to it. It can only ever compute a running sum of the shares it has
    received -- there is no operation in this class that reconstructs an
    individual robot's value.
    """

    server_id: int
    modulus: int = MODULUS
    _partial_sum: int = field(default=0, init=False)
    _shares_received: list[int] = field(default_factory=list, init=False)

    def receive_share(self, share: int) -> None:
        if not (0 <= share < self.modulus):
            raise ValueError("share out of range for this server's modulus")
        self._shares_received.append(share)
        self._partial_sum = (self._partial_sum + share) % self.modulus

    @property
    def partial_sum(self) -> int:
        return self._partial_sum

    @property
    def n_shares_received(self) -> int:
        return len(self._shares_received)


def reveal(servers: list[Server], modulus: int = MODULUS) -> int:
    """Combine the 3 servers' partial sums into the final aggregate.

    This is the only step where the true sum comes into existence -- and it
    requires cooperation from all 3 servers, matching the 3-out-of-3 additive
    scheme. No single server's partial_sum alone equals the true sum.
    """
    if len(servers) != 3:
        raise ValueError("this 3-out-of-3 scheme requires exactly 3 servers")
    total = 0
    for s in servers:
        total = (total + s.partial_sum) % modulus
    return total


def run_protocol(robot_values: list[int], modulus: int = MODULUS) -> int:
    """End-to-end run: N robots -> 3 servers -> revealed aggregate."""
    servers = [Server(server_id=i) for i in range(3)]
    for x in robot_values:
        shares = split_secret(x, modulus)
        for server, share in zip(servers, shares):
            server.receive_share(share)
    return reveal(servers, modulus)


def demo_correctness(robot_values: list[int]) -> None:
    expected = sum(robot_values) % MODULUS
    result = run_protocol(robot_values)
    print(f"robot values:     {robot_values}")
    print(f"expected sum:     {expected}")
    print(f"protocol result:  {result}")
    assert result == expected, "protocol produced the wrong aggregate"
    print("OK -- 3-server aggregation matches the plaintext sum.\n")


def demo_no_single_server_leaks(robot_values: list[int], n_trials: int = 200) -> None:
    """Empirically show that one server's view is statistically uninformative
    about the underlying robot values -- not a formal proof, but a sanity
    check that a lone server's shares don't trivially correlate with x_i.
    """
    server0_shares_across_trials: list[list[int]] = [[] for _ in robot_values]
    for _ in range(n_trials):
        for idx, x in enumerate(robot_values):
            s1, _s2, _s3 = split_secret(x)
            server0_shares_across_trials[idx].append(s1)

    print("Server 0's share of each robot's value, resampled over "
          f"{n_trials} independent runs of the protocol:")
    for idx, x in enumerate(robot_values):
        shares = server0_shares_across_trials[idx]
        mean_share = statistics.mean(shares)
        # A share drawn uniformly from [0, MODULUS) has mean ~MODULUS/2,
        # regardless of the secret x it is hiding -- the point being made
        # here is that mean_share does not track x at all.
        print(
            f"  robot value x={x:>6}  ->  mean share seen by server 0 = "
            f"{mean_share:.3e}  (uniform-random reference ~{MODULUS/2:.3e})"
        )
    print(
        "Server 0's shares cluster around MODULUS/2 regardless of x -- "
        "its view alone carries no information about the robots' values.\n"
    )


if __name__ == "__main__":
    import random

    random.seed(0)
    values = [random.randint(0, 1000) for _ in range(10)]

    print("=== Correctness: 3 servers reconstruct the true sum ===")
    demo_correctness(values)

    print("=== Privacy sanity check: no single server's view leaks x_i ===")
    demo_no_single_server_leaks(values[:4])
