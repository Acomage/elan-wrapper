#!/usr/bin/env python3
import argparse
import ssl
import os
import mimetypes
import shutil
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote
from pathlib import Path


def build_handler(root: Path, data_json: Path):
    class Handler(SimpleHTTPRequestHandler):
        # disable directory listing
        def list_directory(self, path):
            self.send_error(403, f"Directory listing {path} disabled")
            return None

        def do_GET(self):
            if self.path in ("", "/"):
                self._send_file(data_json, "application/json; charset=utf-8")
                return
            # strip leading /
            rel = unquote(self.path.lstrip("/"))
            target = (root / rel).resolve()
            # security: stay inside root
            if not str(target).startswith(str(root.resolve()) + os.sep):
                self.send_error(404)
                return
            if target.is_dir():
                # Optional: serve data.json if someone hits a directory root
                index_candidate = target / "data.json"
                if index_candidate.exists():
                    self._send_file(index_candidate, "application/json; charset=utf-8")
                else:
                    self.send_error(404)
                return
            if target.exists():
                ctype = (
                    mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                )
                self._send_file(target, ctype)
            else:
                self.send_error(404)

        def _send_file(self, path: Path, ctype: str):
            try:
                size = path.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                with open(path, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            except Exception as e:
                self.log_error("error sending file %s: %s", path, e)
                if not self.wfile.closed:
                    self.send_error(500)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8443)  # 443 needs root
    parser.add_argument("--root", default="mirror")
    parser.add_argument("--cert", default="mirror/server.crt")
    parser.add_argument("--key", default="mirror/server.key")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    data_json = root / "data.json"
    if not data_json.exists():
        raise SystemExit(f"Missing {data_json}")

    Handler = build_handler(root, data_json)

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=args.cert, keyfile=args.key)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    print(
        f"Serving HTTPS on https://release.lean-lang.org:{args.port} (mapped to {args.host}) root={root}"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
