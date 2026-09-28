"""ABY3-style replicated 2-out-of-3 additive secret sharing, tolerant to one
server dropping out.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, Mechanism 4
(citing Mohassel & Rindal, ABY3, ACM CCS 2018). Extends
three_server_secret_sharing.py's plain 3-out-of-3 scheme, whose stated
limitation was that it needs all 3 servers live.

Each robot's value x_i is still split into 3 additive shares
(x_i = s1 + s2 + s3 mod p), but now each server is given *two* of the three
shares, assigned cyclically:

    Server A (id 0): holds columns (1, 2)
    Server B (id 1): holds columns (2, 3)
    Server C (id 2): holds columns (3, 1)

Any 2 of the 3 servers, between them, hold all 3 columns -- so the true sum
is reconstructible from any 2 live servers, tolerating exactly 1 dropout.
As a side effect, when a column is reported by both servers that hold it,
the two values must agree; a mismatch flags server misbehaviour (not
pursued further here -- see 07_threat_model.tex class A2).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from three_server_secret_sharing import MODULUS, split_secret

# server_id -> (column_a, column_b), 1-indexed columns, cyclic assignment.
_COLUMN_ASSIGNMENT: dict[int, tuple[int, int]] = {
    0: (1, 2),
    1: (2, 3),
    2: (3, 1),
}


@dataclass
class ReplicatedServer:
    server_id: int
    modulus: int = MODULUS
    _partial_sums: dict[int, int] = field(default_factory=dict, init=False)

    @property
    def columns(self) -> tuple[int, int]:
        return _COLUMN_ASSIGNMENT[self.server_id]

    def receive_shares(self, share_by_column: dict[int, int]) -> None:
        """Receive this server's two shares (keyed by column number) for one
        robot's value, and fold them into the running per-column sums.
        """
        for col in self.columns:
            if col not in share_by_column:
                raise ValueError(f"server {self.server_id} expects column {col}")
            self._partial_sums[col] = (
                self._partial_sums.get(col, 0) + share_by_column[col]
            ) % self.modulus

    def partial_sum(self, column: int) -> int:
        if column not in self.columns:
            raise ValueError(f"server {self.server_id} does not hold column {column}")
        return self._partial_sums.get(column, 0)


def make_servers(modulus: int = MODULUS) -> list[ReplicatedServer]:
    return [ReplicatedServer(server_id=i, modulus=modulus) for i in range(3)]


def distribute(robot_values: list[int], servers: list[ReplicatedServer],
                modulus: int = MODULUS) -> None:
    by_id = {s.server_id: s for s in servers}
    for x in robot_values:
        s1, s2, s3 = split_secret(x, modulus)
        shares = {1: s1, 2: s2, 3: s3}
        for server_id, cols in _COLUMN_ASSIGNMENT.items():
            if server_id not in by_id:
                continue  # that server may be offline for the whole round
            by_id[server_id].receive_shares({c: shares[c] for c in cols})


def reveal(available_servers: list[ReplicatedServer], modulus: int = MODULUS) -> int:
    """Reconstruct the aggregate from whichever servers are currently live.
    Requires at least 2 servers (any 2, by the cyclic design, cover all 3
    columns between them) -- exactly the dropout tolerance this scheme adds
    over the plain 3-out-of-3 version.
    """
    if len(available_servers) < 2:
        raise ValueError(
            "need at least 2 of the 3 replicated servers to cover all 3 "
            "columns -- this scheme tolerates 1 dropout, not 2"
        )

    column_values: dict[int, int] = {}
    for server in available_servers:
        for col in server.columns:
            value = server.partial_sum(col)
            if col in column_values and column_values[col] != value:
                raise ValueError(
                    f"servers disagree on column {col}'s partial sum -- "
                    "possible faulty/malicious server (see 07_threat_model.tex, A2)"
                )
            column_values[col] = value

    missing = {1, 2, 3} - column_values.keys()
    if missing:
        raise ValueError(f"columns {missing} not covered by the available servers")

    return sum(column_values[c] for c in (1, 2, 3)) % modulus
