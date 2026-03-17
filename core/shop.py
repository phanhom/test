"""商店逻辑 - 商品、价格"""

from game.skins import SKINS


def get_shop_items() -> list:
    """获取商店商品列表 (皮肤)"""
    from core.config_loader import load_config
    from core.save_data import get_owned_skins

    cfg = load_config()
    shop_cfg = cfg.get("shop", {})
    items_cfg = shop_cfg.get("items", [])
    owned = set(get_owned_skins())

    if not items_cfg:
        items_cfg = [
            {"skin_id": i, "price": 50 + i * 30}
            for i in range(1, len(SKINS))
        ]

    items = []
    for it in items_cfg:
        sid = it.get("skin_id", 0)
        price = it.get("price", 100)
        skin = SKINS[sid] if sid < len(SKINS) else {"name": "?", "body": (128, 128, 128), "gun": (64, 64, 64)}
        items.append({
            "skin_id": sid,
            "name": skin["name"],
            "price": price,
            "owned": sid in owned,
            "body": skin["body"],
            "gun": skin["gun"],
        })
    return items
