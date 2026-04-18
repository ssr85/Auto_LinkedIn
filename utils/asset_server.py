import http.server
import socketserver
import os
import sys

PORT = 8080
DIRECTORY = "output/images"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Allow CORS for Figma Plugin
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

def run_server():
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
        
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving assets at http://localhost:{PORT}")
        print(f"Directory: {os.path.abspath(DIRECTORY)}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server()
