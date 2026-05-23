from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"T0 dashboard: http://{HOST}:{PORT}")
    server.serve_forever()
