use std::collections::HashMap;

pub fn parse_line(line: &str) -> HashMap<String, String> {
    let mut out = HashMap::new();
    for pair in line.split(';') {
        let mut parts = pair.splitn(2, '=');
        if let (Some(k), Some(v)) = (parts.next(), parts.next()) {
            if !k.is_empty() {
                out.insert(k.trim().to_string(), v.trim().to_string());
            }
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_kv() {
        let map = parse_line("alt=12.3;speed=4.2;mode=AUTO");
        assert_eq!(map.get("alt").unwrap(), "12.3");
        assert_eq!(map.get("mode").unwrap(), "AUTO");
    }
}
