FROM rust:1-slim-bookworm AS build

WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY src ./src
RUN cargo build --release --locked

FROM debian:bookworm-slim

COPY --from=build /build/target/release/gpu-console-dns /usr/local/bin/gpu-console-dns

EXPOSE 1053/udp

CMD ["gpu-console-dns"]
