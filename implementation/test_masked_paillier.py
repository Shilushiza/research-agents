import random

from masked_paillier import aggregate_ciphertexts, masked_encrypt, setup_masked_participants
from paillier import keygen
from threshold_paillier import deal_shares, threshold_decrypt


def test_masked_aggregation_recovers_true_sum():
    kp = keygen(bits=128)
    n_robots = 5
    participants = setup_masked_participants(n_robots, kp.public)
    random.seed(0)
    values = [random.randint(0, 1000) for _ in range(n_robots)]
    sid = "round-1"

    ciphertexts = [
        masked_encrypt(p, x, sid, kp.public) for p, x in zip(participants, values)
    ]
    total_c = aggregate_ciphertexts(ciphertexts, kp.public)
    result = kp.private.decrypt(total_c)

    assert result == sum(values) % kp.public.n


def test_masked_aggregation_works_under_threshold_decryption_too():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=3)
    n_robots = 4
    participants = setup_masked_participants(n_robots, kp.public)
    values = [10, 20, 30, 40]
    sid = "round-2"

    ciphertexts = [
        masked_encrypt(p, x, sid, kp.public) for p, x in zip(participants, values)
    ]
    total_c = aggregate_ciphertexts(ciphertexts, kp.public)

    assert threshold_decrypt(total_c, servers) == sum(values) % kp.public.n


def test_decrypting_a_single_ciphertext_does_not_reveal_its_value():
    """The whole point of combining PRSS with Paillier: decrypting one
    robot's ciphertext in isolation should NOT give back its true value --
    only decrypting the *aggregate* of all participants' ciphertexts should.
    """
    kp = keygen(bits=128)
    n_robots = 4
    participants = setup_masked_participants(n_robots, kp.public)
    sid = "round-3"
    x0 = 555

    c0 = masked_encrypt(participants[0], x0, sid, kp.public)
    decrypted_alone = kp.private.decrypt(c0)

    assert decrypted_alone != x0
    # it decrypts to x0 + mask, which is indistinguishable from random
    # without knowing the PRF key structure behind the mask
