"""Minimal keep-alive pinger for Render free-tier instances (default: every 14 minutes)."""

import os
import sys
import time
import urllib.request

PING_URL = os.getenv("PING_URL", "http://127.0.0.1:8000/api/health")
INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL_SECONDS", "840"))  # 14 minutes (< 15m idle limit)


def ping_once(url: str) -> int:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return resp.status


def main() -> None:
    once = "--once" in sys.argv
    while True:
        try:
            status = ping_once(PING_URL)
            print(f"[keep-alive] {PING_URL} -> HTTP {status}", flush=True)
        except Exception as exc:
            print(f"[keep-alive] error pinging {PING_URL}: {exc}", flush=True)
            if once:
                sys.exit(1)
        if once:
            break
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
