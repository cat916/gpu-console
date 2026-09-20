use std::collections::HashMap;
use std::net::Ipv4Addr;

use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct DnsRecordResponse {
    pub name: String,
    pub value: String,
    pub ttl: u32,
}

#[derive(Debug, Default)]
pub struct Zone {
    suffix: String,
    records: HashMap<String, (Ipv4Addr, u32)>,
}

impl Zone {
    pub fn new(suffix: &str) -> Zone {
        Zone {
            suffix: suffix.to_lowercase(),
            records: HashMap::new(),
        }
    }

    pub fn replace(&mut self, records: Vec<DnsRecordResponse>) {
        self.records = records
            .into_iter()
            .filter_map(|record| {
                let ip = record.value.parse().ok()?;
                Some((record.name.to_lowercase(), (ip, record.ttl)))
            })
            .collect();
    }

    pub fn contains_name(&self, name: &str) -> bool {
        let name = name.to_lowercase();
        name == self.suffix || name.ends_with(&format!(".{}", self.suffix))
    }

    pub fn lookup(&self, name: &str) -> Option<(Ipv4Addr, u32)> {
        self.records.get(&name.to_lowercase()).copied()
    }

    #[cfg(test)]
    pub fn len(&self) -> usize {
        self.records.len()
    }
}

pub fn fetch_records(api_url: &str) -> Result<Vec<DnsRecordResponse>, ureq::Error> {
    let body = ureq::get(api_url).call()?.body_mut().read_to_string()?;
    Ok(serde_json::from_str(&body).map_err(std::io::Error::other)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn zone_with(records: Vec<(&str, &str)>) -> Zone {
        let mut zone = Zone::new("gpu.internal");
        zone.replace(
            records
                .into_iter()
                .map(|(name, value)| DnsRecordResponse {
                    name: name.to_string(),
                    value: value.to_string(),
                    ttl: 5,
                })
                .collect(),
        );
        zone
    }

    #[test]
    fn finds_a_record_whatever_the_case() {
        let zone = zone_with(vec![("train-01.gpu.internal", "10.0.0.2")]);

        assert_eq!(
            zone.lookup("TRAIN-01.GPU.INTERNAL"),
            Some((Ipv4Addr::new(10, 0, 0, 2), 5))
        );
    }

    #[test]
    fn knows_which_names_it_is_authoritative_for() {
        let zone = zone_with(vec![]);

        assert!(zone.contains_name("train-01.gpu.internal"));
        assert!(zone.contains_name("gpu.internal"));
        assert!(!zone.contains_name("example.com"));
        assert!(!zone.contains_name("notgpu.internal"));
    }

    #[test]
    fn drops_records_whose_address_is_not_ipv4() {
        let zone = zone_with(vec![
            ("train-01.gpu.internal", "10.0.0.2"),
            ("broken.gpu.internal", "not-an-ip"),
        ]);

        assert_eq!(zone.len(), 1);
        assert_eq!(zone.lookup("broken.gpu.internal"), None);
    }

    #[test]
    fn parses_the_api_payload() {
        let records: Vec<DnsRecordResponse> = serde_json::from_str(
            r#"[{"name": "train-01.gpu.internal", "type": "A", "value": "10.0.0.2", "ttl": 5}]"#,
        )
        .expect("payload should parse");

        assert_eq!(records[0].name, "train-01.gpu.internal");
        assert_eq!(records[0].ttl, 5);
    }
}
