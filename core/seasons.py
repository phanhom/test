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
    },
    "winter": {
        "name": "冬",
        "sky_top": (240, 248, 255),
        "sky_bottom": (230, 230, 250),
        "ground": (245, 245, 255),
        "ground_accent": (220, 220, 240),
        "tree_color": (105, 105, 105),
        "flower_color": (255, 250, 250),
        "particle_color": (255, 255, 255),
    },
}

SEASON_ORDER = ["spring", "summer", "autumn", "winter"]


def get_season_config(season: str) -> dict:
    return SEASONS.get(season, SEASONS["spring"])


def get_next_season(season: str) -> str:
    idx = SEASON_ORDER.index(season) if season in SEASON_ORDER else 0
    return SEASON_ORDER[(idx + 1) % len(SEASON_ORDER)]
