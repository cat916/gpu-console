use std::net::Ipv4Addr;

pub const CLASS_IN: u16 = 1;
pub const TYPE_A: u16 = 1;

pub const FLAG_RESPONSE: u16 = 1 << 15;
pub const FLAG_AUTHORITATIVE: u16 = 1 << 10;
pub const FLAG_RECURSION_DESIRED: u16 = 1 << 8;

pub const RCODE_NO_ERROR: u16 = 0;
pub const RCODE_NOT_IMPLEMENTED: u16 = 4;
pub const RCODE_REFUSED: u16 = 5;
pub const RCODE_NAME_ERROR: u16 = 3;

const MAX_LABEL_LENGTH: usize = 63;
const MAX_NAME_LENGTH: usize = 255;
const POINTER_MASK: u8 = 0xc0;

#[derive(Debug, PartialEq, Eq)]
pub struct MalformedPacket;

type Parsed<T> = Result<(T, usize), MalformedPacket>;

fn u16_at(data: &[u8], offset: usize) -> Result<u16, MalformedPacket> {
    let bytes = data.get(offset..offset + 2).ok_or(MalformedPacket)?;
    Ok(u16::from_be_bytes([bytes[0], bytes[1]]))
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Header {
    pub id: u16,
    pub flags: u16,
    pub question_count: u16,
    pub answer_count: u16,
    pub authority_count: u16,
    pub additional_count: u16,
}

impl Header {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::with_capacity(12);
        for field in [
            self.id,
            self.flags,
            self.question_count,
            self.answer_count,
            self.authority_count,
            self.additional_count,
        ] {
            bytes.extend(field.to_be_bytes());
        }
        bytes
    }

    pub fn parse(data: &[u8]) -> Parsed<Header> {
        Ok((
            Header {
                id: u16_at(data, 0)?,
                flags: u16_at(data, 2)?,
                question_count: u16_at(data, 4)?,
                answer_count: u16_at(data, 6)?,
                authority_count: u16_at(data, 8)?,
                additional_count: u16_at(data, 10)?,
            },
            12,
        ))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Question {
    pub name: String,
    pub qtype: u16,
    pub qclass: u16,
}

impl Question {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = encode_name(&self.name);
        bytes.extend(self.qtype.to_be_bytes());
        bytes.extend(self.qclass.to_be_bytes());
        bytes
    }

    pub fn parse(data: &[u8], offset: usize) -> Parsed<Question> {
        let (name, offset) = decode_name(data, offset)?;
        Ok((
            Question {
                name,
                qtype: u16_at(data, offset)?,
                qclass: u16_at(data, offset + 2)?,
            },
            offset + 4,
        ))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ARecord {
    pub name: String,
    pub ip: Ipv4Addr,
    pub ttl: u32,
}

impl ARecord {
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = encode_name(&self.name);
        bytes.extend(TYPE_A.to_be_bytes());
        bytes.extend(CLASS_IN.to_be_bytes());
        bytes.extend(self.ttl.to_be_bytes());
        bytes.extend(4u16.to_be_bytes());
        bytes.extend(self.ip.octets());
        bytes
    }
}

pub fn encode_name(name: &str) -> Vec<u8> {
    let mut bytes = Vec::with_capacity(name.len() + 2);
    for label in name.split('.').filter(|label| !label.is_empty()) {
        bytes.push(label.len() as u8);
        bytes.extend(label.as_bytes());
    }
    bytes.push(0);
    bytes
}

pub fn decode_name(data: &[u8], offset: usize) -> Parsed<String> {
    let mut name = String::new();
    let mut cursor = offset;
    let mut end_of_name = None;
    let mut jumps = 0;

    loop {
        let length = *data.get(cursor).ok_or(MalformedPacket)? as usize;
        if length & POINTER_MASK as usize == POINTER_MASK as usize {
            let pointer = (u16_at(data, cursor)? & 0x3fff) as usize;
            if pointer >= cursor {
                return Err(MalformedPacket);
            }
            jumps += 1;
            if jumps > MAX_NAME_LENGTH {
                return Err(MalformedPacket);
            }
            end_of_name.get_or_insert(cursor + 2);
            cursor = pointer;
            continue;
        }
        if length > MAX_LABEL_LENGTH {
            return Err(MalformedPacket);
        }
        if length == 0 {
            end_of_name.get_or_insert(cursor + 1);
            break;
        }
        let label = data
            .get(cursor + 1..cursor + 1 + length)
            .ok_or(MalformedPacket)?;
        if !name.is_empty() {
            name.push('.');
        }
        name.push_str(std::str::from_utf8(label).map_err(|_| MalformedPacket)?);
        if name.len() > MAX_NAME_LENGTH {
            return Err(MalformedPacket);
        }
        cursor += length + 1;
    }

    Ok((name, end_of_name.unwrap_or(cursor + 1)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encodes_a_name_as_length_prefixed_labels() {
        assert_eq!(
            encode_name("www.google.com"),
            vec![
                3, b'w', b'w', b'w', 6, b'g', b'o', b'o', b'g', b'l', b'e', 3, b'c', b'o', b'm', 0
            ]
        );
    }

    #[test]
    fn decodes_a_name_back() {
        let bytes = encode_name("train-01.gpu.internal");

        assert_eq!(
            decode_name(&bytes, 0),
            Ok(("train-01.gpu.internal".to_string(), bytes.len()))
        );
    }

    #[test]
    fn follows_a_compression_pointer_and_resumes_after_it() {
        let mut data = vec![0, 0];
        data.extend(encode_name("gpu.internal"));
        let pointer_at = data.len();
        data.extend([3, b'w', b'w', b'w', 0xc0, 0x02, 0xff]);

        assert_eq!(
            decode_name(&data, pointer_at),
            Ok(("www.gpu.internal".to_string(), data.len() - 1))
        );
    }

    #[test]
    fn rejects_a_pointer_that_does_not_move_backwards() {
        assert_eq!(decode_name(&[0xc0, 0x00], 0), Err(MalformedPacket));
    }

    #[test]
    fn rejects_a_name_that_runs_past_the_packet() {
        assert_eq!(decode_name(&[3, b'w', b'w'], 0), Err(MalformedPacket));
    }

    #[test]
    fn header_round_trips() {
        let header = Header {
            id: 0x1234,
            flags: 0x5678,
            question_count: 1,
            answer_count: 0,
            authority_count: 0,
            additional_count: 0,
        };

        assert_eq!(
            header.to_bytes(),
            vec![0x12, 0x34, 0x56, 0x78, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        );
        assert_eq!(Header::parse(&header.to_bytes()), Ok((header, 12)));
    }

    #[test]
    fn question_round_trips() {
        let question = Question {
            name: "www.google.com".to_string(),
            qtype: TYPE_A,
            qclass: CLASS_IN,
        };
        let bytes = question.to_bytes();

        assert_eq!(bytes.len(), 20);
        assert_eq!(Question::parse(&bytes, 0), Ok((question, 20)));
    }

    #[test]
    fn an_a_record_carries_its_address_in_four_bytes() {
        let record = ARecord {
            name: "train-01.gpu.internal".to_string(),
            ip: Ipv4Addr::new(10, 0, 0, 2),
            ttl: 5,
        };

        let bytes = record.to_bytes();

        assert_eq!(&bytes[bytes.len() - 6..], &[0, 4, 10, 0, 0, 2]);
    }
}
