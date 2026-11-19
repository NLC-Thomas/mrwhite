#!/usr/bin/env python3

import a2s
import json
import time
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVERS = {
    "chernarus": {
        "name": "Chernarus",
        "address": ("10.0.0.71", 2305),
        "battlemetrics": "https://www.battlemetrics.com/servers/dayz/28929482"
    },
    "deerisle": {
        "name": "DeerIsle",
        "address": ("10.0.0.72", 2306),
        "battlemetrics": "https://www.battlemetrics.com/servers/dayz/30381096"
    },
    "arsteinen": {
        "name": "Arsteinen",
        "address": ("10.0.0.74", 2307),
        "battlemetrics": "https://www.battlemetrics.com/servers/dayz/30700191"
    },
    "pripyat": {
        "name": "Pripyat",
        "address": ("10.0.0.76", 2505),
        "battlemetrics": "https://www.battlemetrics.com/servers/dayz/40464903"
    }
}

status_data = {}
status_lock = threading.Lock()


def check_server(server_id, config):
    try:
        info = a2s.info(config["address"], timeout=5)

        return {
            "id": server_id,
            "name": config["name"],
            "status": "online",
            "server_name": info.server_name,
            "map": info.map_name,
            "players": info.player_count,
            "max_players": info.max_players,
            "ping_ms": round(info.ping * 1000),
            "battlemetrics": config["battlemetrics"],
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "error": None
        }

    except Exception as error:
        return {
            "id": server_id,
            "name": config["name"],
            "status": "offline",
            "server_name": None,
            "map": None,
            "players": None,
            "max_players": None,
            "ping_ms": None,
            "battlemetrics": config["battlemetrics"],
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "error": str(error)
        }


def monitor_loop():
    global status_data

    while True:
        updated = {}

        for server_id, config in SERVERS.items():
            updated[server_id] = check_server(server_id, config)

        with status_lock:
            status_data = updated

        time.sleep(60)


class StatusHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/api/status":
            self.send_error(404)
            return

        with status_lock:
            response = json.dumps({
                "updated": datetime.now(timezone.utc).isoformat(),
                "servers": status_data
            }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", 8090), StatusHandler)
    print("Valhalla Calling monitor running on 127.0.0.1:8090")

    server.serve_forever()