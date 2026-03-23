from __future__ import annotations

import argparse
import json
import random
import socket
import time


def run_udp_stream(host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        payload = {
            "altitude_m": round(random.uniform(0, 25), 2),
            "speed_mps": round(random.uniform(0, 12), 2),
            "battery_pct": round(random.uniform(20, 100), 1),
            "ts": time.time(),
        }
        sock.sendto(json.dumps(payload).encode("utf-8"), (host, port))
        time.sleep(0.2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UADIB mock drone stream")
    parser.add_argument("--endpoint", default="mavlink://udp:127.0.0.1:14550")
    args = parser.parse_args()

    host, port = "127.0.0.1", 14550
    if ":" in args.endpoint:
        maybe_port = args.endpoint.rsplit(":", 1)[-1]
        if maybe_port.isdigit():
            port = int(maybe_port)
    run_udp_stream(host, port)
