"""NPC 实体 - 可配置、可对话"""

import threading
from typing import Optional, Callable

from .llm_client import LLMClient


class NPCEntity:
    def __init__(self, npc_id: str, name: str, role: str, prompt: str, x: int, y: int,
                 llm_client: Optional[LLMClient] = None):
        self.id = npc_id
        self.name = name
        self.role = role
        self.prompt = prompt
        self.x = x
        self.y = y
        self.width = 80
        self.height = 100
        self.llm = llm_client
        self._reply: Optional[str] = None
        self._loading = False
        self._lock = threading.Lock()

    def contains_point(self, px: int, py: int) -> bool:
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def talk(self, user_input: str, on_reply: Optional[Callable[[str], None]] = None):
        """异步请求 LLM 回复"""
        if not self.llm:
            reply = "（未配置大模型，请在 config.json 中设置 api_key）"
            self._reply = reply
            if on_reply:
                on_reply(reply)
            return

        self._loading = True
        self._reply = None

        def _do():
            try:
                system = f"{self.prompt}\n你的角色是：{self.role}，名字是{self.name}。"
                reply = self.llm.chat(system, user_input)
                with self._lock:
                    self._reply = reply
                    self._loading = False
                if on_reply:
                    on_reply(reply)
            except Exception:
                with self._lock:
                    self._reply = "请求失败"
                    self._loading = False
                if on_reply:
                    on_reply("请求失败")

        threading.Thread(target=_do, daemon=True).start()

    def get_reply(self) -> Optional[str]:
        with self._lock:
            return self._reply

    def is_loading(self) -> bool:
        return self._loading

    def clear_reply(self):
        with self._lock:
            self._reply = None
