"""配置加载 - 从 config.json 读取"""

import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.json"
_config: dict | None = None


def load_config() -> dict:
    global _config
    if _config is not None:
        return _config
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _config = json.load(f)
        except (json.JSONDecodeError, IOError):
            _config = _default_config()
    else:
        _config = _default_config()
    return _config


def _default_config() -> dict:
    return {
        "lobby": {"width": 1024, "height": 640, "max_players": 8},
        "game": {"width": 800, "height": 500},
        "npc": {
            "enabled": False,
            "llm": {"api_key": "", "model": "gpt-4o-mini", "base_url": "https://api.openai.com/v1", "timeout": 30},
            "list": [],
        },
    }


def get_lobby_config() -> dict:
    return load_config().get("lobby", {})


def get_game_config() -> dict:
    return load_config().get("game", {})


def get_npc_config() -> dict:
    return load_config().get("npc", {})
