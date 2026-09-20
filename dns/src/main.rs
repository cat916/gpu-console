mod server;
mod wire;
mod zone;

use std::env;
use std::net::UdpSocket;
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::Duration;

use zone::{fetch_records, Zone};

const DEFAULT_PORT: u16 = 1053;
const DEFAULT_ZONE: &str = "gpu.internal";
const DEFAULT_API_URL: &str = "http://127.0.0.1:8000/api/dns/records";
const DEFAULT_POLL_SECONDS: u64 = 2;

fn env_or<T: std::str::FromStr>(name: &str, fallback: T) -> T {
    env::var(name)
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(fallback)
}

fn main() -> std::io::Result<()> {
    let port: u16 = env_or("DNS_PORT", DEFAULT_PORT);
    let zone_suffix = env::var("DNS_ZONE").unwrap_or_else(|_| DEFAULT_ZONE.to_string());
    let api_url = env::var("DNS_RECORDS_URL").unwrap_or_else(|_| DEFAULT_API_URL.to_string());
    let poll_interval = Duration::from_secs(env_or("DNS_POLL_SECONDS", DEFAULT_POLL_SECONDS));

    let zone = Arc::new(RwLock::new(Zone::new(&zone_suffix)));
    let socket = UdpSocket::bind(("127.0.0.1", port))?;
    println!("Serving {zone_suffix} on 127.0.0.1:{port}, records from {api_url}");

    let polled_zone = Arc::clone(&zone);
    thread::spawn(move || poll_records(&polled_zone, &api_url, poll_interval));

    server::serve(&socket, &zone)
}

fn poll_records(zone: &Arc<RwLock<Zone>>, api_url: &str, interval: Duration) {
    let mut last_error: Option<String> = None;
    loop {
        match fetch_records(api_url) {
            Ok(records) => {
                last_error = None;
                zone.write().expect("zone lock poisoned").replace(records);
            }
            Err(error) => {
                let message = error.to_string();
                if last_error.as_deref() != Some(&message) {
                    eprintln!("Can't read records from {api_url}: {message}");
                    last_error = Some(message);
                }
            }
        }
        thread::sleep(interval);
    }
}
