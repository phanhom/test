"""
房间服务器 - 开房间多人游戏
支持大厅、准备状态、主机开始
"""

import socket
import threading
import random
import string
from typing import Optional, Dict, List

from .protocol import send_msg, recv_msg


def gen_room_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class RoomServer:
    """房间服务器 - 主机创建房间后运行"""
    MAX_PLAYERS = 8

    def __init__(self, port: int = 25565, max_players: int = None):
        self.port = port
        self.MAX_PLAYERS = max_players if max_players is not None else self._get_max_players()
        self.clients: List[socket.socket] = []
        self.client_data: Dict[int, dict] = {}  # player_id -> {input, ready, name}
        self.running = False
        self.server_sock: Optional[socket.socket] = None
        self.lock = threading.Lock()
        self.room_code = gen_room_code()
        self.game_started = False
        self.chat_messages: List[tuple] = []  # (sender, text)

    def _get_max_players(self) -> int:
        try:
            from core.config_loader import get_lobby_config
            return get_lobby_config().get("max_players", 8)
        except Exception:
            return 8

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self) -> bool:
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(("0.0.0.0", self.port))
            self.server_sock.listen(max(self.MAX_PLAYERS, 8))
            self.server_sock.settimeout(0.5)
            self.running = True
            accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            accept_thread.start()
            return True
        except OSError:
            return False

    def _accept_loop(self):
        while self.running and self.server_sock:
            try:
                client, _ = self.server_sock.accept()
                with self.lock:
                    player_id = len(self.clients)
                    if player_id < self.MAX_PLAYERS and not self.game_started:
                        self.clients.append(client)
                        self.client_data[player_id] = {
                            "input": {"left": 0, "right": 0, "jump": 0, "crouch": 0, "shoot": 0, "melee": 0, "dash": 0},
                            "ready": False,
                            "name": f"玩家{player_id + 2}",  # P1=主机
                        }
                        send_msg(client, {"type": "welcome", "player_id": player_id, "room_code": self.room_code})
                        recv_thread = threading.Thread(
                            target=self._recv_loop, args=(client, player_id), daemon=True
                        )
                        recv_thread.start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _recv_loop(self, client: socket.socket, player_id: int):
        while self.running:
            data = recv_msg(client)
            if data is None:
                break
            with self.lock:
                if data.get("type") == "input":
                    if player_id in self.client_data:
                        self.client_data[player_id]["input"] = data.get("keys", {})
                elif data.get("type") == "ready":
                    if player_id in self.client_data:
                        self.client_data[player_id]["ready"] = data.get("ready", False)
                elif data.get("type") == "name":
                    if player_id in self.client_data:
                        self.client_data[player_id]["name"] = data.get("name", f"玩家{player_id + 2}")
                elif data.get("type") == "chat":
                    sender = self.client_data.get(player_id, {}).get("name", f"P{player_id + 2}")
                    msg = data.get("message", "")[:100]
                    if msg:
                        self.chat_messages.append((sender, msg))
                        chat_msg = {"type": "chat", "sender": sender, "message": msg}
                        for c in self.clients:
                            try:
                                send_msg(c, chat_msg)
                            except Exception:
                                pass

    def get_input(self, player_id: int) -> dict:
        with self.lock:
            return self.client_data.get(player_id, {}).get("input", {"left": 0, "right": 0, "jump": 0, "crouch": 0, "shoot": 0, "melee": 0, "dash": 0}).copy()

    def get_lobby_state(self) -> dict:
        """获取大厅状态"""
        with self.lock:
            players = [{"id": i, "name": self.client_data.get(i, {}).get("name", f"P{i+2}"), "ready": self.client_data.get(i, {}).get("ready", False)}
                      for i in range(len(self.clients))]
            return {"players": players, "room_code": self.room_code, "host": "你"}

    def broadcast_lobby(self, state: dict):
        msg = {"type": "lobby", "data": state}
        with self.lock:
            for client in self.clients:
                try:
                    send_msg(client, msg)
                except Exception:
                    pass

    def broadcast_game_start(self, game_config: dict):
        """通知所有客户端游戏开始"""
        self.game_started = True
        msg = {"type": "game_start", "config": game_config}
        with self.lock:
            for client in self.clients:
                try:
                    send_msg(client, msg)
                except Exception:
                    pass

    def broadcast_chat(self, sender: str, message: str):
        """主机发送聊天并广播"""
        if message:
            with self.lock:
                self.chat_messages.append((sender, message))
                chat_msg = {"type": "chat", "sender": sender, "message": message}
                for c in self.clients:
                    try:
                        send_msg(c, chat_msg)
                    except Exception:
                        pass

    def get_chat_messages(self) -> List[tuple]:
        with self.lock:
            return list(self.chat_messages)

    def broadcast_state(self, state: dict):
        msg = {"type": "state", "data": state}
        with self.lock:
            dead = []
            for i, client in enumerate(self.clients):
                try:
                    send_msg(client, msg)
                except (BrokenPipeError, ConnectionResetError):
                    dead.append(i)
            for i in reversed(dead):
                self.clients.pop(i)
                if i in self.client_data:
                    del self.client_data[i]

    def player_count(self) -> int:
        with self.lock:
            return len(self.clients)

    def stop(self):
        self.running = False
        with self.lock:
            for c in self.clients:
                try:
                    c.close()
                except Exception:
                    pass
            self.clients.clear()
            self.client_data.clear()
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None
