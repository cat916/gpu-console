from ipaddress import IPv4Address, IPv4Network


class IpPoolExhausted(Exception):
    pass


class IpPool:
    def __init__(self, network: IPv4Network) -> None:
        _gateway, *assignable = network.hosts()
        self._assignable = set(assignable)
        self._allocated: set[IPv4Address] = set()

    def allocate(self) -> IPv4Address:
        free = self._assignable - self._allocated
        if not free:
            raise IpPoolExhausted
        address = min(free)
        self._allocated.add(address)
        return address

    def release(self, address: IPv4Address) -> None:
        self._allocated.discard(address)
