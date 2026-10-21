# GPU Console

Launch GPU instances, watch them come up, and reach them by name. Every running instance gets a
hostname in a private zone that resolves over real DNS.

```
$ dig @127.0.0.1 -p 1053 train-01.gpu.internal +short
10.0.0.2
```

## Running it

You need [uv](https://docs.astral.sh/uv/), Node 24 (the repo pins it in `.node-version`),
[Yarn](https://classic.yarnpkg.com/) and a Rust toolchain.

```sh
make install
make dev
```

`make dev` starts three processes: the API on :8000, the DNS server on :1053, and the console on
[localhost:5173](http://localhost:5173). Launch an instance, wait about five seconds for it to
reach Running, then resolve its hostname with the `dig` command the detail page gives you.

| Command | What it does |
| --- | --- |
| `make dev` | All three processes |
| `make backend` / `make dns` / `make frontend` | One at a time |
| `make test` | pytest, vitest and cargo test |
| `make lint` | ruff, oxlint, rustfmt and clippy |
| `make api` | Regenerate `openapi.json`, then the frontend's types from it |

Ports are overridable: `make dev BACKEND_PORT=8001 DNS_PORT=1054 FRONTEND_PORT=3000`.

### With Docker

```sh
docker compose up --build
```

The console is on [localhost:8080](http://localhost:8080), the API on :8001 and DNS on :1053.
Nginx serves the built frontend and proxies `/api` to the backend, so there is no dev server and
no proxy target to configure. Override with `FRONTEND_PORT`, `BACKEND_PORT`, `DNS_PORT` or
`DNS_ZONE`.

## How it fits together

```
frontend/  React + MUI, polls the API every 2s
backend/   FastAPI: the instance lifecycle and the record set
dns/       Rust: an authoritative server for gpu.internal, polls the backend every 2s
```

The backend owns the state. It publishes `GET /api/dns/records` — one A record per running
instance — and the DNS server polls that, so the two can start in either order and neither needs
to know when the other restarts.

Provisioning is simulated: `FakeProvider` sleeps, and no GPU is ever allocated. Everything else is
real, including the DNS.

### The API

`POST /api/instances` accepts a launch and returns 202 immediately with a provisioning instance;
`DELETE` does the same in reverse. Both return the instance so the console can show the new state
without waiting. Errors carry a code: `name_taken`, `network_full`, `invalid_state`,
`validation_failed`. Full spec in [`backend/openapi.json`](backend/openapi.json), or browse it at
[localhost:8000/docs](http://localhost:8000/docs) while the backend runs.

### The DNS server

`dns/` refactors the wire format from dnsweekend, a
recursive resolver built from [Implement DNS in a Weekend](https://implement-dns.wizardzines.com/),
into an authoritative server for the zone. Parsing had to become fallible, because packets now
arrive from the network rather than from a root server we chose to query, and name decoding had to
start following compression pointers rather than stopping at them.

It answers A records for names in the zone, `NXDOMAIN` for names in the zone that no instance
holds, `REFUSED` outside the zone, and `NOTIMP` for other query types. Port 1053 keeps it out of
root's way.

## Decisions worth knowing

The vocabulary in the code — launch and delete, provisioning/running/deleting/failed, instance
type, image, hostname — is defined in [CONTEXT.md](CONTEXT.md), and it is the same vocabulary in
the API, the UI and this README.

**An address is reserved when a launch is accepted**, not when provisioning finishes. Otherwise two
launches racing for the last address both pass the capacity check and one fails five seconds later.
A launch with no address free is refused up front with `network_full`.

**A failed instance keeps its address.** If a teardown half-finished, the machine may still be
using it, so handing it to a new instance risks a collision. It is released only once a delete
succeeds.

**Only running instances resolve.** A record appears when the instance reaches Running and
disappears the moment deletion starts, while the name stays reserved until the instance is gone.

**One team, one namespace.** Instances have no owner and names are unique console-wide, because
hostnames share a single zone. [ADR 0001](docs/adr/0001-single-tenant-global-namespace.md) records
why per-owner namespaces were rejected.

## Known limitations

- **Instances live in memory.** Restarting the backend forgets them. A real provider would be the
  source of truth, and the backend would reconcile against it on startup.
- **No stop and start**, no resize, and no cost tracking beyond the hourly price shown at launch.
- **No auth.** Anyone who can reach the API can launch and delete.
- **UDP only, one question per query**, which is what `dig` and a resolver stub send.
