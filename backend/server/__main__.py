"""Entry point: python -m server [--port PORT]"""
from __future__ import annotations

import os

import uvicorn

from server.ws_server import app


def main() -> None:
    port = int(os.environ.get("MAHJONG_PORT", "9000"))
    uvicorn.run(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
