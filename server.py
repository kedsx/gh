"""Serve the files beside this script to the local network."""

from __future__ import annotations

import argparse
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parent


def get_lan_ip() -> str:
    """Return the LAN address the PS4 should use to reach this PC."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect selects the outbound interface without sending a packet.
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


class HostHandler(SimpleHTTPRequestHandler):
    """Static file host with a small optional client progress-log endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        if request.path == "/ag_log":
            message = parse_qs(request.query).get("m", [""])[0]
            if message:
                safe_message = message[:500].replace("\r", " ").replace("\n", " ")
                print(f"[client-log] {self.client_address[0]}: {safe_message}", flush=True)
            self.send_response(204)
            self.end_headers()
            return

        super().do_GET()

    def end_headers(self) -> None:
        # Let the PS4 browser fetch the current copies after files are updated.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve this folder to the PS4 browser")
    parser.add_argument("port", nargs="?", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    server = ThreadingHTTPServer(
        ("0.0.0.0", args.port),
        HostHandler,
    )
    ip = get_lan_ip()
    print()
    print("  +-------------------------------------------------+")
    print("  |   Keds Webhost :: 14.00/14.02                   |")
    print("  +-------------------------------------------------+")
    print()
    print("  PC Host      ->  http://192.168.0.40:%d/" % args.port)
    print()
    print("  PS4 browser  ->  http://%s:%d/" % (ip, args.port))
    print()
    print("  Ctrl-C to stop.")
    print()
    print("  Serving folder: %s" % ROOT, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
