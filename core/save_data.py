"""存档 - 金币、已购商品"""

import json
from pathlib import Path

SAVE_PATH = Path(__file__).parent.parent / "save_data.json"
COINS_PER_SCORE = 1  # 每 100 分 = 1 金币 (100分→1金币)


def _load() -> dict:
    if SAVE_PATH.exists():
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"coins": 0, "owned_skins": [0]}


def _save(data: dict):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def get_coins() -> int:
    return _load().get("coins", 0)


def get_owned_skins() -> list:
    return _load().get("owned_skins", [0])


def add_coins(amount: int):
    d = _load()
    d["coins"] = d.get("coins", 0) + amount
    _save(d)


def add_coins_from_score(score: int):
    """根据游戏分数增加金币"""
    coins = max(0, score // 100) * COINS_PER_SCORE
    if coins > 0:
        add_coins(coins)


def purchase_skin(skin_id: int, price: int) -> bool:
    """购买皮肤，成功返回 True"""
    d = _load()
    coins = d.get("coins", 0)
    owned = d.get("owned_skins", [0])
    if skin_id in owned:
        return True
    if coins >= price:
        d["coins"] = coins - price
        owned.append(skin_id)
        d["owned_skins"] = sorted(owned)
        _save(d)
        return True
    return False


def owns_skin(skin_id: int) -> bool:
    return skin_id in get_owned_skins()
