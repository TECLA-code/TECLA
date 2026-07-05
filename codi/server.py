#!/usr/bin/env python3
import http.server
import socketserver
import sys
import os
import json
import subprocess

# Serveix sempre des del directori d'aquest script (codi/), passi el que passi
# el cwd de qui l'engega (p. ex. el harness de preview).
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Port: variable d'entorn PORT (preview) > argument > 8080 per defecte.
PORT = int(os.environ.get('PORT') or (sys.argv[1] if len(sys.argv) > 1 else 8080))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, format, *args):
        pass  # silencia els logs de cada request

    def do_OPTIONS(self):
        # CORS només per a /sys/volume (cal quan la web s'obre via file:// i la
        # crida és cross-origin). Els fitxers servits NO porten CORS: així cap
        # web de tercers pot llegir-los des del navegador.
        if self.path == '/sys/volume':
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/sys/volume':
            try:
                length = int(self.headers.get('Content-Length', 0))
                data = json.loads(self.rfile.read(length))
                vol = max(0, min(100, int(data.get('value', 50))))
                subprocess.run(
                    ['osascript', '-e', f'set volume output volume {vol}'],
                    check=False, capture_output=True
                )
                self._json(200, {'ok': True, 'volume': vol})
            except Exception as e:
                self._json(500, {'ok': False, 'error': str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')  # només respostes JSON de /sys/volume
        self.end_headers()
        self.wfile.write(body)

socketserver.TCPServer.allow_reuse_address = True

def start_server(port):
    try:
        with socketserver.TCPServer(("127.0.0.1", port), MyHTTPRequestHandler) as httpd:
            print(f"✓ Servidor TECLA al port {port}")
            print(f"  Obre: http://127.0.0.1:{port}/index.html")
            print("  Ctrl+C per aturar\n")
            httpd.serve_forever()
    except OSError as e:
        if e.errno in (48, 98, 10048):  # macOS=48, Linux=98, Windows=10048
            print(f"Port {port} ocupat, provant {port + 1}…")
            start_server(port + 1)
        else:
            raise

if __name__ == "__main__":
    try:
        start_server(PORT)
    except KeyboardInterrupt:
        print("\nServidor aturat.")
        sys.exit(0)
