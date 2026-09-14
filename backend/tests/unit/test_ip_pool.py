from ipaddress import IPv4Address, IPv4Network

import pytest

from app.ip_pool import IpPool, IpPoolExhausted


def test_skips_gateway_and_allocates_lowest_free_address() -> None:
    pool = IpPool(IPv4Network("10.0.0.0/24"))

    assert pool.allocate() == IPv4Address("10.0.0.2")
    assert pool.allocate() == IPv4Address("10.0.0.3")


def test_released_address_is_reused_first() -> None:
    pool = IpPool(IPv4Network("10.0.0.0/24"))
    first = pool.allocate()
    pool.allocate()

    pool.release(first)

    assert pool.allocate() == first


def test_raises_when_exhausted() -> None:
    pool = IpPool(IPv4Network("10.0.0.0/30"))
    pool.allocate()

    with pytest.raises(IpPoolExhausted):
        pool.allocate()
