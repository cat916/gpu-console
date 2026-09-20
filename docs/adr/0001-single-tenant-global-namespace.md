# Single tenant with one global Instance namespace

The console serves a single team: Instances have no owner, and a Name is unique across the whole console because every Hostname lives in the one DNS Zone. We rejected per-owner namespaces (a User or Project owning Instances, with Names unique per owner) because Hostnames would then collide across owners unless each owner also got their own DNS Zone, which is far more than this console needs.

## Consequences

Adding owners later means choosing between per-owner DNS Zones and a global Name registry, and migrating every existing Hostname accordingly.
