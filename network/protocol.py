"""网络协议 - 消息收发"""

import socket
import json
import struct
from typing import Optional


def send_msg(sock: socket.socket, data: dict):
    msg = json.dumps(data).encode("utf-8")
    sock.sendall(struct.pack(">I", len(msg)) + msg)


def recv_msg(sock: socket.socket) -> Optional[dict]:
    try:
        raw_len = sock.recv(4)
        if not raw_len:
            return None
        msg_len = struct.unpack(">I", raw_len)[0]
        data = b""
        while len(data) < msg_len:
            chunk = sock.recv(min(msg_len - len(data), 4096))
            if not chunk:
                return None
            data += chunk
        return json.loads(data.decode("utf-8"))
    except (ConnectionResetError, ConnectionAbortedError, json.JSONDecodeError):
        return None
