use std::net::{Ipv4Addr, UdpSocket};
use std::sync::{Arc, RwLock};

use crate::wire::{
    ARecord, Header, MalformedPacket, Question, CLASS_IN, FLAG_AUTHORITATIVE,
    FLAG_RECURSION_DESIRED, FLAG_RESPONSE, RCODE_NAME_ERROR, RCODE_NOT_IMPLEMENTED, RCODE_NO_ERROR,
    RCODE_REFUSED, TYPE_A,
};
use crate::zone::Zone;

const MAX_UDP_PAYLOAD: usize = 512;

pub fn answer(query: &[u8], zone: &Zone) -> Result<Vec<u8>, MalformedPacket> {
    let (header, offset) = Header::parse(query)?;
    if header.question_count != 1 {
        return Ok(reply(&header, None, RCODE_NOT_IMPLEMENTED, None));
    }
    let (question, _) = Question::parse(query, offset)?;

    if question.qclass != CLASS_IN || !zone.contains_name(&question.name) {
        return Ok(reply(&header, Some(&question), RCODE_REFUSED, None));
    }
    if question.qtype != TYPE_A {
        return Ok(reply(&header, Some(&question), RCODE_NOT_IMPLEMENTED, None));
    }
    match zone.lookup(&question.name) {
        Some((ip, ttl)) => Ok(reply(
            &header,
            Some(&question),
            RCODE_NO_ERROR,
            Some(a_record(&question.name, ip, ttl)),
        )),
        None => Ok(reply(&header, Some(&question), RCODE_NAME_ERROR, None)),
    }
}

fn a_record(name: &str, ip: Ipv4Addr, ttl: u32) -> ARecord {
    ARecord {
        name: name.to_string(),
        ip,
        ttl,
    }
}

fn reply(
    query_header: &Header,
    question: Option<&Question>,
    rcode: u16,
    answer: Option<ARecord>,
) -> Vec<u8> {
    let header = Header {
        id: query_header.id,
        flags: FLAG_RESPONSE
            | FLAG_AUTHORITATIVE
            | (query_header.flags & FLAG_RECURSION_DESIRED)
            | rcode,
        question_count: question.is_some() as u16,
        answer_count: answer.is_some() as u16,
        authority_count: 0,
        additional_count: 0,
    };
    let mut bytes = header.to_bytes();
    if let Some(question) = question {
        bytes.extend(question.to_bytes());
    }
    if let Some(answer) = answer {
        bytes.extend(answer.to_bytes());
    }
    bytes
}

pub fn serve(socket: &UdpSocket, zone: &Arc<RwLock<Zone>>) -> std::io::Result<()> {
    let mut buffer = [0u8; MAX_UDP_PAYLOAD];
    loop {
        let (size, from) = socket.recv_from(&mut buffer)?;
        let response = {
            let zone = zone.read().expect("zone lock poisoned");
            answer(&buffer[..size], &zone)
        };
        match response {
            Ok(response) => {
                socket.send_to(&response, from)?;
            }
            Err(MalformedPacket) => eprintln!("dropped a malformed packet from {from}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::wire::{decode_name, encode_name};
    use crate::zone::DnsRecordResponse;

    fn query_for(name: &str, qtype: u16) -> Vec<u8> {
        let header = Header {
            id: 0xbeef,
            flags: FLAG_RECURSION_DESIRED,
            question_count: 1,
            answer_count: 0,
            authority_count: 0,
            additional_count: 0,
        };
        let question = Question {
            name: name.to_string(),
            qtype,
            qclass: CLASS_IN,
        };
        let mut bytes = header.to_bytes();
        bytes.extend(question.to_bytes());
        bytes
    }

    fn test_zone() -> Zone {
        let mut zone = Zone::new("gpu.internal");
        zone.replace(vec![DnsRecordResponse {
            name: "train-01.gpu.internal".to_string(),
            value: "10.0.0.2".to_string(),
            ttl: 5,
        }]);
        zone
    }

    fn response_header(response: &[u8]) -> Header {
        Header::parse(response).expect("response should parse").0
    }

    #[test]
    fn answers_a_known_name_with_its_address() {
        let response = answer(&query_for("train-01.gpu.internal", TYPE_A), &test_zone())
            .expect("query should be understood");

        let header = response_header(&response);
        assert_eq!(header.id, 0xbeef);
        assert_eq!(header.flags & 0x000f, RCODE_NO_ERROR);
        assert_eq!(header.answer_count, 1);
        assert!(header.flags & FLAG_RESPONSE != 0);
        assert!(header.flags & FLAG_AUTHORITATIVE != 0);

        let (_, answer_start) = Question::parse(&response, 12).expect("question should parse");
        let (name, offset) = decode_name(&response, answer_start).expect("answer name");
        assert_eq!(name, "train-01.gpu.internal");
        assert_eq!(&response[offset + 10..], &[10, 0, 0, 2]);
    }

    #[test]
    fn echoes_the_question_back() {
        let query = query_for("train-01.gpu.internal", TYPE_A);

        let response = answer(&query, &test_zone()).expect("query should be understood");

        assert_eq!(
            &response[12..12 + encode_name("train-01.gpu.internal").len() + 4],
            &query[12..]
        );
    }

    #[test]
    fn says_the_name_does_not_exist_when_no_instance_has_it() {
        let response = answer(&query_for("gone.gpu.internal", TYPE_A), &test_zone())
            .expect("query should be understood");

        let header = response_header(&response);
        assert_eq!(header.flags & 0x000f, RCODE_NAME_ERROR);
        assert_eq!(header.answer_count, 0);
    }

    #[test]
    fn refuses_names_outside_the_zone() {
        let response = answer(&query_for("example.com", TYPE_A), &test_zone())
            .expect("query should be understood");

        assert_eq!(response_header(&response).flags & 0x000f, RCODE_REFUSED);
    }

    #[test]
    fn does_not_implement_query_types_other_than_a() {
        let response = answer(&query_for("train-01.gpu.internal", 28), &test_zone())
            .expect("query should be understood");

        assert_eq!(
            response_header(&response).flags & 0x000f,
            RCODE_NOT_IMPLEMENTED
        );
    }

    #[test]
    fn keeps_the_recursion_desired_bit_of_the_query() {
        let response = answer(&query_for("train-01.gpu.internal", TYPE_A), &test_zone())
            .expect("query should be understood");

        assert!(response_header(&response).flags & FLAG_RECURSION_DESIRED != 0);
    }

    #[test]
    fn reports_a_truncated_packet_rather_than_panicking() {
        assert_eq!(answer(&[0x12, 0x34], &test_zone()), Err(MalformedPacket));
    }
}
