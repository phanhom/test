"""游戏实体: 玩家、敌人、子弹"""

import pygame
from .constants import GRAVITY, JUMP_FORCE, BULLET_SPEED, GROUND_Y, SCREEN_WIDTH, WHITE, YELLOW, RED, PLAYER_SPEED
from .skins import SKINS
from .player_state import ActionStateMachine, PlayerState
from .weapons.weapon import Weapon, WeaponType
from .weapons.armory import Armory


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, player_id: int = 0, skin_id: int = 0, season: str = "spring"):
        super().__init__()
        self.player_id = player_id
        self.skin_id = skin_id % len(SKINS)
        self.season = season  # 当前季节
        self.width = 40
        self.height = 50
        self.normal_height = self.height
        self.crouch_height = 28
        self.image = pygame.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.facing_right = True
        self.on_ground = False

        # 动作系统
        self.action_sm = ActionStateMachine()
        self.dash_speed = PLAYER_SPEED * 2.5
        self.melee_hitbox = None
        self.melee_duration = self.action_sm.melee_duration

        # 武器系统
        self.armory = Armory()
        self.weapon = self.armory.get("pistol")
        self.weapon_inventory = ["pistol", "rifle"]
        self.weapon_index = 0

    def equip_weapon(self, weapon: Weapon):
        self.weapon = weapon

    def switch_weapon(self, weapon_id: str):
        if weapon_id in self.weapon_inventory:
            self.weapon = self.armory.get(weapon_id)

    def cycle_weapon(self, direction: int = 1):
        if not self.weapon_inventory:
            return
        self.weapon_index = (self.weapon_index + direction) % len(self.weapon_inventory)
        self.weapon = self.armory.get(self.weapon_inventory[self.weapon_index])

    def pickup_weapon(self, weapon: Weapon):
        if weapon.weapon_id not in self.weapon_inventory:
            self.weapon_inventory.append(weapon.weapon_id)
        self.weapon = weapon.copy()

    def shoot_with_weapon(self) -> list["Bullet"]:
        """使用当前武器射击，返回生成的子弹列表。"""
        if self.weapon is None or not self.weapon.shoot():
            return []
        bullets = []
        base_x = self.rect.right if self.facing_right else self.rect.left
        y = self.rect.centery
        direction = 1 if self.facing_right else -1
        for i in range(self.weapon.pellets):
            spread = 0.0
            if self.weapon.pellets > 1:
                spread = (i - (self.weapon.pellets - 1) / 2) * self.weapon.spread
            bullet = Bullet(base_x, y, direction, self.player_id,
                            speed=self.weapon.bullet_speed, damage=self.weapon.damage,
                            color=self.weapon.color, spread=spread)
            bullets.append(bullet)
        return bullets

    def update(self, platforms: list):
        self.action_sm.update()

        # 蹲伏调整碰撞盒
        if self.action_sm.state == PlayerState.CROUCH:
            if self.rect.height != self.crouch_height:
                self.rect.height = self.crouch_height
                self.rect.y += self.normal_height - self.crouch_height
        else:
            if self.rect.height != self.normal_height:
                self.rect.y -= self.normal_height - self.crouch_height
                self.rect.height = self.normal_height

        # 重力
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

        # 地面
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.vel_y = 0
            self.on_ground = True
            if self.action_sm.state == PlayerState.JUMP:
                self.action_sm.set_state(PlayerState.IDLE)
        else:
            self.on_ground = False
            if self.action_sm.state not in (PlayerState.JUMP, PlayerState.DASH, PlayerState.MELEE):
                self.action_sm.set_state(PlayerState.JUMP)

        # 平台碰撞
        for (px, py, pw, ph) in platforms:
            plat_rect = pygame.Rect(px, py, pw, ph)
            if self.vel_y > 0 and self.rect.bottom > py and self.rect.top < py + ph:
                if self.rect.centerx > px and self.rect.centerx < px + pw:
                    if self.rect.bottom - self.vel_y <= py:
                        self.rect.bottom = py
                        self.vel_y = 0
                        self.on_ground = True
                        if self.action_sm.state == PlayerState.JUMP:
                            self.action_sm.set_state(PlayerState.IDLE)
                        break

        # 清除过期近战 hitbox
        if self.melee_hitbox is not None:
            if self.action_sm.state != PlayerState.MELEE:
                self.melee_hitbox = None

    def handle_input(self, *, left=False, right=False, jump=False, crouch=False,
                     shoot=False, melee=False, dash=False):
        """处理输入并更新动作状态。"""
        prev_state = self.action_sm.state
        self.action_sm.handle_input(
            left=left, right=right, jump=jump, crouch=crouch,
            shoot=shoot, melee=melee, dash=dash, on_ground=self.on_ground
        )

        if self.action_sm.state == PlayerState.DASH and prev_state != PlayerState.DASH:
            self._start_dash()
        if self.action_sm.state == PlayerState.MELEE and prev_state != PlayerState.MELEE:
            self._start_melee()

        # 蹲伏时不能移动
        if self.action_sm.state != PlayerState.CROUCH:
            speed = self.dash_speed if self.action_sm.state == PlayerState.DASH else PLAYER_SPEED
            if left:
                self.rect.x -= speed
                self.facing_right = False
            if right:
                self.rect.x += speed
                self.facing_right = True
        else:
            # 蹲伏时可缓慢移动
            if left:
                self.rect.x -= PLAYER_SPEED * 0.3
                self.facing_right = False
            if right:
                self.rect.x += PLAYER_SPEED * 0.3
                self.facing_right = True

        self.rect.x = max(0, min(SCREEN_WIDTH - self.width, self.rect.x))

        if jump and self.on_ground and self.action_sm.state not in (PlayerState.DASH, PlayerState.MELEE, PlayerState.CROUCH):
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.action_sm.set_state(PlayerState.JUMP)

    def _start_dash(self):
        direction = 1 if self.facing_right else -1
        self.rect.x += self.dash_speed * direction

    def crouch(self):
        if self.action_sm.can_crouch():
            self.action_sm.set_state(PlayerState.CROUCH)
            if self.rect.height != self.crouch_height:
                self.rect.height = self.crouch_height
                self.rect.y += self.normal_height - self.crouch_height

    def start_dash(self):
        if self.action_sm.can_dash():
            self.action_sm.set_state(PlayerState.DASH)
            self._start_dash()

    def melee_attack(self):
        if self.action_sm.melee_cooldown <= 0:
            self.action_sm.set_state(PlayerState.MELEE)
            self.action_sm.melee_cooldown = self.action_sm.melee_cooldown_total
            self._start_melee()

    def _start_melee(self):
        w, h = 35, 30
        x = self.rect.right if self.facing_right else self.rect.left - w
        y = self.rect.centery - h // 2
        self.melee_hitbox = pygame.Rect(x, y, w, h)

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
            "action": self.action_sm.to_dict(),
            "width": self.width,
            "height": self.rect.height,
            "weapon": self.weapon.to_dict() if self.weapon else None,
            "weapon_inventory": list(self.weapon_inventory),
            "weapon_index": self.weapon_index,
        }

    def from_dict(self, d: dict):
        self.rect.x = d.get("x", self.rect.x)
        self.rect.y = d.get("y", self.rect.y)
        self.facing_right = d.get("facing_right", self.facing_right)
        self.vel_y = d.get("vel_y", self.vel_y)
        self.skin_id = d.get("skin_id", self.skin_id) % len(SKINS)
        self.action_sm.from_dict(d.get("action", {}))
        h = d.get("height", self.normal_height)
        self.rect.height = h
        self.weapon_inventory = d.get("weapon_inventory", self.weapon_inventory)
        self.weapon_index = d.get("weapon_index", self.weapon_index)
        wd = d.get("weapon")
        if wd:
            if self.weapon is None or self.weapon.weapon_id != wd.get("weapon_id"):
                self.weapon = self.armory.get(wd.get("weapon_id", "pistol"))
            self.weapon.from_dict(wd)
        else:
            self.weapon = self.armory.get("pistol")

    def draw(self, surface):
        # 获取季节装备配置
        from core.seasons import get_season_equipment
        season_equipment = get_season_equipment(self.season)

        # 使用季节装备颜色
        body_color = season_equipment["body"]
        gun_color = season_equipment["gun"]
        accessory_color = season_equipment["accessory"]

        state = self.action_sm.state

        # 冲刺时添加拖影效果
        if state == PlayerState.DASH:
            offset = -8 if self.facing_right else 8
            trail = self.rect.copy()
            trail.x += offset
            pygame.draw.rect(surface, (*body_color[:3], 180), trail)

        # 绘制身体（使用季节装备颜色）
        pygame.draw.rect(surface, body_color, self.rect)

        # 蹲伏时头部位置更低
        head_y = self.rect.y + 5 if state != PlayerState.CROUCH else self.rect.y + 2
        head_rect = pygame.Rect(self.rect.x + 10, head_y, 20, 18)
        pygame.draw.rect(surface, (255, 220, 180), head_rect)

        # 绘制枪械（使用武器颜色或季节装备颜色）
        if state != PlayerState.CROUCH and self.weapon:
            gun_color = self.weapon.color
            gun_x = self.rect.right if self.facing_right else self.rect.left - 25
            pygame.draw.rect(surface, gun_color, (gun_x, self.rect.top + 25, 28, 8))
        elif state != PlayerState.CROUCH:
            gun_x = self.rect.right if self.facing_right else self.rect.left - 25
            pygame.draw.rect(surface, gun_color, (gun_x, self.rect.top + 25, 25, 8))

        # 近战时绘制刀光
        if state == PlayerState.MELEE and self.melee_hitbox is not None:
            pygame.draw.rect(surface, (200, 200, 255), self.melee_hitbox, 2)

        # 绘制季节装饰（如帽子、围巾等）
        if self.season == "winter":
            scarf_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 20, 30, 6)
            pygame.draw.rect(surface, accessory_color, scarf_rect)
        elif self.season == "summer":
            glasses_rect = pygame.Rect(self.rect.x + 12, head_y + 5, 16, 4)
            pygame.draw.rect(surface, (0, 0, 0), glasses_rect)
        elif self.season == "spring":
            flower_center = (self.rect.x + 20, head_y)
            pygame.draw.circle(surface, accessory_color, flower_center, 4)
        elif self.season == "autumn":
            leaf_rect = pygame.Rect(self.rect.x + 15, head_y - 3, 10, 6)
            pygame.draw.ellipse(surface, accessory_color, leaf_rect)

        # 绘制玩家标签
        font = pygame.font.Font(None, 24)
        label = font.render(f"P{self.player_id + 1}", True, WHITE)
        surface.blit(label, (self.rect.x, self.rect.y - 18))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, owner_id: int = 0, speed: float = BULLET_SPEED,
                 damage: int = 10, color: tuple = YELLOW, spread: float = 0.0):
        super().__init__()
        self.owner_id = owner_id
        self.speed = speed
        self.damage = damage
        self.spread = spread
        self.image = pygame.Surface((15, 5))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction

    def update(self):
        self.rect.x += self.speed * self.direction
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
