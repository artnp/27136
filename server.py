#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Backend Server for Interactive Garden Plan
- ให้บริการเว็บเซิร์ฟเวอร์สำหรับหน้า index.html
- เปิดเว็บเบราว์เซอร์ให้อัตโนมัติทันที
- มี API รองรับการบันทึกข้อมูล data/plants.json จากหน้าเว็บลงเครื่องโดยตรง
- มี API รองรับการสั่งรัน ~github_update.bat จากหน้าเว็บ
"""

import os
import sys
import json
import socket
import webbrowser
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANTS_FILE = os.path.join(BASE_DIR, "data", "plants.json")
BAT_FILE = os.path.join(BASE_DIR, "~github_update.bat")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class GardenHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        # Prevent caching during local development
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/save-plants':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)
                
                os.makedirs(os.path.dirname(PLANTS_FILE), exist_ok=True)
                with open(PLANTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                resp = {"success": True, "message": "บันทึกข้อมูลลง data/plants.json เรียบร้อย"}
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                print(f"[✓] บันทึกข้อมูล data/plants.json เรียบร้อย ({len(data.get('plants', []))} ต้น)")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                resp = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                print(f"[!] บันทึกข้อมูลล้มเหลว: {e}")

        elif self.path == '/api/github-upload':
            try:
                if os.path.exists(BAT_FILE):
                    print("[*] กำลังสั่งรัน ~github_update.bat ...")
                    subprocess.Popen(['cmd.exe', '/c', BAT_FILE], cwd=BASE_DIR)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    resp = {"success": True, "message": "สั่งรัน ~github_update.bat เรียบร้อย"}
                    self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    resp = {"success": False, "error": "ไม่พบไฟล์ ~github_update.bat"}
                    self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                resp = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404, "Endpoint not found")

def open_browser_delayed(url):
    time.sleep(1.0)
    print(f"[i] กำลังเปิดเว็บเบราว์เซอร์: {url}")
    webbrowser.open(url)

def main():
    global PORT
    # If 8080 is in use, find next available port
    while is_port_in_use(PORT):
        PORT += 1

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, GardenHandler)
    url = f"http://localhost:{PORT}/index.html"

    print("=" * 60)
    print(" 🌱 Garden Plan Local Server กำลังทำงาน")
    print("=" * 60)
    print(f" URL: {url}")
    print(" กำลังเปิดหน้าเว็บให้อัตโนมัติ...")
    print(" กด Ctrl+C เพื่อหยุดเซิร์ฟเวอร์")
    print("=" * 60)

    # Launch browser in a background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[i] หยุดการทำงานของเซิร์ฟเวอร์เรียบร้อยครับ")
        httpd.server_close()

if __name__ == "__main__":
    main()
