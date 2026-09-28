import random

from prss import PRIME, Participant, aggregate, recover_dropped_mask, setup_round


def _make_participants(n: int) -> list[Participant]:
    return [Participant(pid=i, n_participants=n) for i in range(n)]


def test_masks_sum_to_zero_full_participation():
    participants = _make_participants(5)
    setup_round(participants, recovery_threshold=3)
    sid = "round-1"
    masks = [p.mask(sid) for p in participants]
    assert sum(masks) % PRIME == 0


def test_masks_are_round_dependent():
    participants = _make_participants(4)
    setup_round(participants, recovery_threshold=2)
    m1 = participants[0].mask("round-1")
    m2 = participants[0].mask("round-2")
    assert m1 != m2


def test_end_to_end_aggregation_recovers_true_sum():
    random.seed(0)
    n = 6
    participants = _make_participants(n)
    setup_round(participants, recovery_threshold=4)
    sid = "round-42"

    true_values = {p.pid: random.randint(0, 1000) for p in participants}
    masks = {p.pid: p.mask(sid) for p in participants}
    masked_contributions = {
        pid: (val + masks[pid]) % PRIME for pid, val in true_values.items()
    }

    server_view = {pid: (val - masks[pid]) % PRIME for pid, val in masked_contributions.items()}
    # server_view reconstructs masked_contributions - masks == true_values here
    # only because we subtracted masks locally for this assertion; in the real
    # protocol the server never learns individual masks. What the server
    # actually computes is the *sum* of masked contributions, which should
    # equal the sum of true values once all masks cancel.
    total = aggregate(masked_contributions, {pid: 0 for pid in true_values}, modulus=PRIME)
    assert total % PRIME == sum(true_values.values()) % PRIME
    del server_view  # illustrative only, not part of the real protocol


def test_dropout_recovery_reconstructs_correct_mask():
    n = 5
    participants = _make_participants(n)
    setup_round(participants, recovery_threshold=3)
    sid = "round-7"

    dropped = participants[2]
    expected_mask = dropped.mask(sid)

    survivors = [p for p in participants if p.pid != dropped.pid]
    recovered_mask = recover_dropped_mask(dropped.pid, survivors, sid)

    assert recovered_mask == expected_mask


def test_dropout_recovery_below_threshold_raises_or_is_wrong():
    """With fewer than the recovery threshold of surviving holders, the
    reconstructed seed (and hence mask) should not match the true one --
    this is the Shamir secrecy guarantee showing up as a side effect."""
    n = 5
    participants = _make_participants(n)
    setup_round(participants, recovery_threshold=4)
    sid = "round-9"

    dropped = participants[0]
    expected_mask = dropped.mask(sid)
    too_few_survivors = [p for p in participants if p.pid != dropped.pid][:2]

    recovered_mask = recover_dropped_mask(dropped.pid, too_few_survivors, sid)
    assert recovered_mask != expected_mask
