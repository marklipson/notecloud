import os
from notecloud.api import API
from notecloud.util import parse_note
import json
import mimetypes
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
#from urllib.parse import parse_qs

PORT = 15301
API_ROOT = "/api/"
API_NOTE = "note/"
WEB_ROOT = os.path.join(os.path.dirname(__file__), "web")
api = API()


class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        content = None
        path = self.path
        query = ""
        resp_code = 200
        if "?" in path:
            path, query = self.path.split("?")[:2]
        if path.startswith(API_ROOT):
            try:
                rel = path[len(API_ROOT):]
                if rel.startswith(API_NOTE):
                    rel = rel[len(API_NOTE):]
                    if rel:
                        note_content = api.read_note(rel)
                        props = parse_note(note_content)
                        content = {"path": rel, "content": note_content, "props": props}
                    else:
                        args = parse_qs(query)
                        spec = args.get("spec", [""])[0]
                        results, highlights = api.search_notes(spec)
                        content = {"results": results, "highlights": highlights}
            except Exception as err:
                content = {"error": str(err)}
                resp_code = 501
        else:
            content_path = os.path.join(WEB_ROOT, self.path[1:])
            if os.path.exists(content_path):
                with open(content_path) as f:
                    content = f.read()
        if content is not None:
            self.send_response(resp_code)
            if isinstance(content, dict):
                self.send_header('Content-type', "application/javascript")
                self.end_headers()
                self.wfile.write(json.dumps(content))
            else:
                mime_type = mimetypes.guess_type(self.path) or "text/plain"
                self.send_header('Content-type', mime_type[0])
                self.end_headers()
                self.wfile.write(content)
        else:
            self.send_response(404)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Not found: %s" % self.path)

    def do_POST(self):
        resp = None
        post_data = self.rfile.read(int(self.headers['Content-Length']))
        if self.path.startswith(API_ROOT):
            rel = self.path[len(API_ROOT):]
            if rel.startswith(API_NOTE):
                rel = rel[len(API_NOTE):]
                content = post_data
                if rel:
                    path = api.write_note(rel, content)
                else:
                    path = api.new_note(content)
                resp = {"path": path, "props": parse_note(content)}
        if resp is not None:
            self.send_response(200)
            self.send_header('Content-type','application/javascript')
            self.end_headers()
            self.wfile.write(json.dumps(resp, indent=2))
        else:
            self.send_response(404)
            self.send_header('Content-type','text/plain')
            self.end_headers()
            self.wfile.write("Not found: %s" % self.path)


if __name__ == "__main__":
    server = HTTPServer(('', PORT), WebHandler)
    print("http://localhost:%d/index.html" % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
