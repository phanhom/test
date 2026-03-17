"""
地图系统 - 不同地图有不同平台布局和视觉风格
平台格式: (x, y, width, height)
"""

from .constants import SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y

# 地图配置: 平台列表, 出生点, 天空色, 地面色, 平台色
MAPS = [
    {
        "id": 0,
        "name": "训练场",
        "platforms": [],  # 仅地面
        "spawns": [(80, GROUND_Y - 50), (220, GROUND_Y - 50), (400, GROUND_Y - 50), (580, GROUND_Y - 50)],
        "sky_top": (135, 206, 235),
        "sky_bottom": (176, 224, 230),
        "ground": (34, 139, 34),
        "ground_line": (50, 100, 50),
    },
    {
        "id": 1,
        "name": "沙漠前线",
        "platforms": [
            (150, 350, 120, 20),
            (500, 320, 100, 20),
            (300, 280, 80, 20),
        ],
        "spawns": [(80, GROUND_Y - 50), (220, GROUND_Y - 50), (400, GROUND_Y - 50), (580, GROUND_Y - 50)],
        "sky_top": (255, 220, 170),
        "sky_bottom": (245, 200, 150),
        "ground": (210, 180, 140),
        "ground_line": (180, 150, 100),
    },
    {
        "id": 2,
        "name": "工厂废墟",
        "platforms": [
            (100, 380, 80, 15),
            (250, 340, 100, 15),
            (450, 380, 90, 15),
            (600, 320, 70, 15),
        ],
        "spawns": [(80, GROUND_Y - 50), (250, GROUND_Y - 50), (420, GROUND_Y - 50), (620, GROUND_Y - 50)],
        "sky_top": (100, 100, 120),
        "sky_bottom": (80, 80, 100),
        "ground": (80, 80, 85),
        "ground_line": (60, 60, 65),
    },
    {
        "id": 3,
        "name": "雪地要塞",
        "platforms": [
            (200, 360, 150, 25),
            (50, 300, 100, 20),
            (550, 310, 120, 20),
        ],
        "spawns": [(80, GROUND_Y - 50), (220, GROUND_Y - 50), (400, GROUND_Y - 50), (580, GROUND_Y - 50)],
        "sky_top": (220, 235, 245),
        "sky_bottom": (200, 215, 230),
        "ground": (240, 248, 255),
        "ground_line": (220, 228, 235),
    },
    {
        "id": 4,
        "name": "丛林基地",
        "platforms": [
            (80, 370, 100, 18),
            (300, 330, 140, 18),
            (550, 370, 100, 18),
        ],
        "spawns": [(80, GROUND_Y - 50), (220, GROUND_Y - 50), (400, GROUND_Y - 50), (580, GROUND_Y - 50)],
        "sky_top": (100, 150, 100),
        "sky_bottom": (80, 130, 80),
        "ground": (34, 100, 34),
        "ground_line": (25, 80, 25),
    },
]


def get_map(level_index: int):
    """根据关卡索引获取地图 (循环使用)"""
    return MAPS[level_index % len(MAPS)]
