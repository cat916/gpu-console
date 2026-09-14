from ipaddress import IPv4Network

import pytest

from app.settings import Settings


def test_defaults_match_the_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in [
        "PROVISION_DELAY_SECONDS",
        "DEPROVISION_DELAY_SECONDS",
        "DNS_ZONE",
        "DNS_TTL_SECONDS",
        "INSTANCE_NETWORK",
    ]:
        monkeypatch.delenv(name, raising=False)

    assert Settings.from_env() == Settings(
        provision_delay_seconds=5.0,
        deprovision_delay_seconds=2.0,
        dns_zone="gpu.internal",
        dns_ttl_seconds=5,
        instance_network=IPv4Network("10.0.0.0/24"),
    )


def test_reads_overrides_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROVISION_DELAY_SECONDS", "0.5")
    monkeypatch.setenv("DNS_ZONE", "console.internal")
    monkeypatch.setenv("INSTANCE_NETWORK", "10.1.0.0/16")

    settings = Settings.from_env()

    assert settings.provision_delay_seconds == 0.5
    assert settings.dns_zone == "console.internal"
    assert settings.instance_network == IPv4Network("10.1.0.0/16")
