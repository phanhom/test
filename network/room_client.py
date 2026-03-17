"""
房间客户端 - 加入房间
"""

import socket
import threading
from typing import Optional, Callable

from .protocol import send_msg, recv_msg


class RoomClient:
    """房间客户端"""
    def __init__(self, host: str, port: int = 25565):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.player_id: int = 1
        self.running = False
        self.last_state: Optional[dict] = None
        self.last_lobby: Optional[dict] = None
        self.game_started = False
        self.game_config: Optional[dict] = None

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(0.1)
            self.running = True
            recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            recv_thread.start()
            # 等待 welcome
            import time
            for _ in range(50):
                if self.player_id is not None or self.game_config:
                    break
                time.sleep(0.1)
            return True
        except Exception:
            return False

    def _recv_loop(self):
        while self.running and self.sock:
            data = recv_msg(self.sock)
            if data is None:
                break
            if data.get("type") == "welcome":
                self.player_id = data.get("player_id", 1)
            elif data.get("type") == "lobby":
                self.last_lobby = data.get("data")
            elif data.get("type") == "game_start":
                self.game_started = True
                self.game_config = data.get("config", {})
            elif data.get("type") == "state":
                self.last_state = data.get("data")

    def send_input(self, keys: dict):
        if self.sock:
            try:
                send_msg(self.sock, {"type": "input", "keys": keys})
            except Exception:
                pass

    def send_ready(self, ready: bool):
        if self.sock:
            try:
                send_msg(self.sock, {"type": "ready", "ready": ready})
            except Exception:
                pass

    def send_name(self, name: str):
        if self.sock:
            try:
                send_msg(self.sock, {"type": "name", "name": name})
            except Exception:
                pass

    def get_state(self) -> Optional[dict]:
        return self.last_state

    def get_lobby(self) -> Optional[dict]:
        return self.last_lobby

    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
