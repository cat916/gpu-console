import os
from dataclasses import dataclass
from ipaddress import IPv4Network


@dataclass(frozen=True)
class Settings:
    provision_delay_seconds: float = 5.0
    deprovision_delay_seconds: float = 2.0
    dns_zone: str = "gpu.internal"
    dns_ttl_seconds: int = 5
    instance_network: IPv4Network = IPv4Network("10.0.0.0/24")

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            provision_delay_seconds=float(
                os.environ.get("PROVISION_DELAY_SECONDS", defaults.provision_delay_seconds)
            ),
            deprovision_delay_seconds=float(
                os.environ.get("DEPROVISION_DELAY_SECONDS", defaults.deprovision_delay_seconds)
            ),
            dns_zone=os.environ.get("DNS_ZONE", defaults.dns_zone),
            dns_ttl_seconds=int(os.environ.get("DNS_TTL_SECONDS", defaults.dns_ttl_seconds)),
            instance_network=IPv4Network(
                os.environ.get("INSTANCE_NETWORK", str(defaults.instance_network))
            ),
        )
