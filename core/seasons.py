"""四季系统 - 不同季节的视觉配置"""

SEASONS = {
    "spring": {
        "name": "春",
        "sky_top": (135, 206, 235),
        "sky_bottom": (176, 224, 230),
        "ground": (34, 139, 34),
        "ground_accent": (50, 205, 50),
        "tree_color": (34, 139, 34),
        "flower_color": (255, 182, 193),
        "particle_color": (255, 182, 193),
        # 春季装备：轻便的迷彩装备
        "equipment": {
            "body": (85, 107, 47),  # 橄榄绿
            "gun": (70, 70, 70),    # 深灰色枪械
            "accessory": (255, 182, 193),  # 粉色装饰（花朵）
        }
    },
    "summer": {
        "name": "夏",
        "sky_top": (135, 206, 250),
        "sky_bottom": (224, 255, 255),
        "ground": (60, 179, 113),
        "ground_accent": (50, 205, 50),
        "tree_color": (0, 100, 0),
        "flower_color": (255, 215, 0),
        "particle_color": (255, 255, 200),
        # 夏季装备：清凉的沙漠装备
        "equipment": {
            "body": (210, 180, 140),  # 沙漠黄
            "gun": (100, 90, 80),     # 棕色枪械
            "accessory": (255, 215, 0),  # 金色装饰（阳光）
        }
    },
    "autumn": {
        "name": "秋",
        "sky_top": (255, 218, 185),
        "sky_bottom": (255, 228, 196),
        "ground": (210, 180, 140),
        "ground_accent": (205, 133, 63),
        "tree_color": (139, 69, 19),
        "flower_color": (255, 140, 0),
        "particle_color": (255, 165, 0),
        # 秋季装备：温暖的森林装备
        "equipment": {
            "body": (139, 69, 19),   # 棕色
            "gun": (60, 40, 20),     # 深棕色枪械
            "accessory": (255, 140, 0),  # 橙色装饰（落叶）
        }
    },
    "winter": {
        "name": "冬",
        "sky_top": (240, 248, 255),
        "sky_bottom": (230, 230, 250),
        "ground": (245, 245, 255),
        "ground_acqucent": (220, 220, 240),
        "tree_color": (105, 105, 105),
        "flower_color": (255, 250, 250),
        "particle_color": (255, 255, 255),
        # 冬季装备：保暖的雪地装备
        "equipment": {
            "body": (200, 210, 220),  # 浅灰白
            "gun": (120, 130, 140),   # 冷灰色枪械
            "accessory": (100, 149, 237),  # 蓝色装饰（冰晶）
        }
    },
}

SEASON_ORDER = ["spring", "summer", "autumn", "winter"]


def get_season_config(season: str) -> dict:
    return SEASONS.get(season, SEASONS["spring"])


def get_next_season(season: str) -> str:
    idx = SEASON_ORDER.index(season) if season in SEASON_ORDER else 0
    return SEASON_ORDER[(idx + 1) % len(SEASON_ORDER)]


def get_season_equipment(season: str) -> dict:
    """获取指定季节的装备配置"""
    config = get_season_config(season)
    return config.get("equipment", {
        "body": (100, 100, 100),
        "gun": (80, 80, 80),
        "accessory": (200, 200, 200),
    })
