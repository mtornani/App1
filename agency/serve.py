"""Server statico per provare la console in locale.

    python agency/serve.py          -> http://localhost:8787/web/

Serve la cartella `agency/`, cosi' il percorso relativo ../state/index.json
usato dalla PWA risolve esattamente come su GitHub Pages.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """Disattiva la cache: in sviluppo vuoi vedere subito le modifiche."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()


def main() -> int:
    parser = argparse.ArgumentParser(description="Server statico per la console dell'agenzia.")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    handler = functools.partial(NoCacheHandler, directory=str(ROOT))
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print(f"Console su http://localhost:{args.port}/web/  (Ctrl+C per fermare)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nFermato.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
