"""游戏实体: 玩家、敌人、子弹"""

import pygame
from .constants import GRAVITY, JUMP_FORCE, BULLET_SPEED, GROUND_Y, SCREEN_WIDTH, WHITE, YELLOW, RED
from .skins import SKINS


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, player_id: int = 0, skin_id: int = 0, season: str = "spring"):
        super().__init__()
        self.player_id = player_id
        self.skin_id = skin_id % len(SKINS)
        self.season = season  # 当前季节
        self.width = 40
        self.height = 50
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.facing_right = True
        self.on_ground = False

    def update(self, platforms: list):
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

        # 地面
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # 平台碰撞
        for (px, py, pw, ph) in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if self.vel_y > 0 and self.rect.bottom > py and self.rect.top < py + ph:
                if self.rect.centerx > px and self.rect.centerx < px + pw:
                    if self.rect.bottom - self.vel_y <= py:
                        self.rect.bottom = py
                        self.vel_y = 0
                        self.on_ground = True
                        break

    def set_season(self, season: str):
        """更新当前季节"""
        self.season = season

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False

    def to_dict(self):
        return {
            "x": self.rect.x, "y": self.rect.y,
            "facing_right": self.facing_right,
            "vel_y": self.vel_y,
            "skin_id": self.skin_id,
        }

    def from_dict(self, d: dict):
        self.rect.x = d.get("x", self.rect.x)
        self.rect.y = d.get("y", self.rect.y)
        self.facing_right = d.get("facing_right", self.facing_right)
        self.vel_y = d.get("vel_y", self.vel_y)
        self.skin_id = d.get("skin_id", self.skin_id) % len(SKINS)

    def draw(self, surface):
        # 获取季节装备配置
        from core.seasons import get_season_equipment
        season_equipment = get_season_equipment(self.season)
        
        # 使用季节装备颜色
        body_color = season_equipment["body"]
        gun_color = season_equipment["gun"]
        accessory_color = season_equipment["accessory"]
        
        # 绘制身体（使用季节装备颜色）
        pygame.draw.rect(surface, body_color, self.rect)
        
        # 绘制头部
        head_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 5, 20, 18)
        pygame.draw.rect(surface, (255, 220, 180), head_rect)
        
        # 绘制枪械（使用季节装备颜色）
        gun_x = self.rect.right if self.facing_right else self.rect.left - 25
        pygame.draw.rect(surface, gun_color, (gun_x, self.rect.top + 25, 25, 8))
        
        # 绘制季节装饰（如帽子、围巾等）
        if self.season == "winter":
            # 冬季：绘制围巾
            scarf_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 20, 30, 6)
            pygame.draw.rect(surface, accessory_color, scarf_rect)
        elif self.season == "summer":
            # 夏季：绘制太阳镜
            glasses_rect = pygame.Rect(self.rect.x + 12, self.rect.y + 10, 16, 4)
            pygame.draw.rect(surface, (0, 0, 0), glasses_rect)
        elif self.season == "spring":
            # 春季：绘制花朵装饰
            flower_center = (self.rect.x + 20, self.rect.y + 5)
            pygame.draw.circle(surface, accessory_color, flower_center, 4)
        elif self.season == "autumn":
            # 秋季：绘制叶子装饰
            leaf_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 2, 10, 6)
            pygame.draw.ellipse(surface, accessory_color, leaf_rect)
        
        # 绘制玩家标签
        font = pygame.font.Font(None, 24)
        label = font.render(f"P{self.player_id + 1}", True, WHITE)
        surface.blit(label, (self.rect.x, self.rect.y - 18))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner_id: int = 0):
        super().__init__()
        self.owner_id = owner_id
        self.image = pygame.Surface((15, 5))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction

    def update(self):
        self.rect.x += BULLET_SPEED * self.direction
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed: float = 2.0, eid: int = 0):
        super().__init__()
        self.eid = eid
        self.width = 35
        self.height = 45
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = -1
        self.speed = speed

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def draw(self, surface):
        pygame.draw.rect(surface, RED, self.rect)
        head_rect = pygame.Rect(self.rect.x + 8, self.rect.y + 5, 18, 15)
        pygame.draw.rect(surface, (255, 200, 180), head_rect)
