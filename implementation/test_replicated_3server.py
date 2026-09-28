import random

import pytest

from replicated_3server import distribute, make_servers, reveal


def test_all_three_servers_reconstruct():
    random.seed(0)
    values = [random.randint(0, 1000) for _ in range(10)]
    servers = make_servers()
    distribute(values, servers)
    assert reveal(servers) == sum(values) % servers[0].modulus


@pytest.mark.parametrize("dropped_id", [0, 1, 2])
def test_tolerates_any_single_server_dropping(dropped_id):
    random.seed(1)
    values = [random.randint(0, 1000) for _ in range(10)]
    servers = make_servers()
    distribute(values, servers)

    survivors = [s for s in servers if s.server_id != dropped_id]
    assert len(survivors) == 2
    assert reveal(survivors) == sum(values) % servers[0].modulus


def test_fails_with_only_one_server():
    values = [1, 2, 3]
    servers = make_servers()
    distribute(values, servers)
    with pytest.raises(ValueError):
        reveal(servers[:1])


def test_distribute_can_skip_an_offline_server_from_the_start():
    """A server that's offline for the whole round never even receives
    shares -- distribute() should not crash, and the remaining 2 should
    still reconstruct correctly."""
    random.seed(2)
    values = [random.randint(0, 1000) for _ in range(5)]
    servers = make_servers()
    online = [s for s in servers if s.server_id != 1]
    distribute(values, online)
    assert reveal(online) == sum(values) % servers[0].modulus


def test_detects_disagreeing_servers_as_tamper_evidence():
    values = [100, 200]
    servers = make_servers()
    distribute(values, servers)
    # Tamper with server 0's view of column 2 (also held by server 1).
    servers[0]._partial_sums[2] += 1
    with pytest.raises(ValueError):
        reveal([servers[0], servers[1]])
