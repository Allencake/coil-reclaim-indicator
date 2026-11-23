#!/usr/bin/env python3
"""接收 coil_reclaim.pine 发来的 JSON 数据包，存到本地给 Agent 读。

只用 Python 标准库，不用装任何东西。

    python3 examples/webhook_receiver.py --port 8080 --token 你的密码

TradingView 只往 80/443 端口发 webhook，所以要用隧道给它一个 https 地址，比如：

    cloudflared tunnel --url http://localhost:8080

警报里的 Webhook URL 填：https://<隧道地址>/webhook?token=你的密码

存放位置（默认 packets/ 目录）：
    packets/latest.json                  最新一个包（任何图表）
    packets/<时间>_<品种>_<事件>.json      每个包单独一份
    packets/all.jsonl                    全部包，一行一个
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

EXPECTED_SCHEMA = "coil-reclaim/v1"
BODY_LIMIT = 32 * 1024


def slug(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "-", str(value)).strip("-")[:60] or "x"


def make_handler(folder: Path, token: str):
    class PacketHandler(BaseHTTPRequestHandler):
        def send_json(self, code: int, payload: dict) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if urlsplit(self.path).path == "/health":
                self.send_json(200, {"ok": True, "folder": str(folder)})
            else:
                self.send_json(404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            parts = urlsplit(self.path)
            if parts.path != "/webhook":
                return self.send_json(404, {"ok": False, "error": "not found"})
            if token:
                given = parse_qs(parts.query).get("token", [""])[0] or self.headers.get("X-Token", "")
                if given != token:
                    return self.send_json(401, {"ok": False, "error": "token 不对"})

            size = int(self.headers.get("Content-Length") or 0)
            if not 0 < size <= BODY_LIMIT:
                return self.send_json(400, {"ok": False, "error": "body 为空或太大"})
            try:
                packet = json.loads(self.rfile.read(size).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self.send_json(400, {"ok": False, "error": "不是合法 JSON"})
            if not isinstance(packet, dict) or packet.get("schema") != EXPECTED_SCHEMA:
                return self.send_json(400, {"ok": False, "error": f"schema 应为 {EXPECTED_SCHEMA}"})

            now = datetime.now(timezone.utc)
            packet["received_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            folder.mkdir(parents=True, exist_ok=True)
            pretty = json.dumps(packet, ensure_ascii=False, indent=2)
            name = f"{now.strftime('%Y%m%dT%H%M%S%fZ')}_{slug(packet.get('symbol'))}_{slug(packet.get('event'))}.json"
            (folder / name).write_text(pretty, encoding="utf-8")
            tmp = folder / "latest.json.tmp"
            tmp.write_text(pretty, encoding="utf-8")
            tmp.replace(folder / "latest.json")
            with (folder / "all.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(packet, ensure_ascii=False) + "\n")

            print(f"{packet['received_at']}  {packet.get('event')}  {packet.get('symbol')}  "
                  f"{packet.get('session')}  {packet.get('bias')}  {packet.get('status')}", flush=True)
            self.send_json(200, {"ok": True, "saved": name})

        def log_message(self, fmt, *args) -> None:
            pass

    return PacketHandler


def main() -> None:
    ap = argparse.ArgumentParser(description="接收 Coil Reclaim 指标的 webhook 数据包")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址，默认只监听本机（隧道够用）")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--token", default="", help="可选：webhook 地址里要带的 ?token=")
    ap.add_argument("--dir", default="packets", help="保存目录")
    args = ap.parse_args()

    folder = Path(args.dir).resolve()
    if not args.token:
        print("提示：没设 --token，知道地址的人都能往里发包。", file=sys.stderr)
    print(f"监听 http://{args.host}:{args.port}/webhook ，保存到 {folder}", flush=True)
    ThreadingHTTPServer((args.host, args.port), make_handler(folder, args.token)).serve_forever()


if __name__ == "__main__":
    main()
