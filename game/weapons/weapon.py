"""武器定义"""

from enum import Enum, auto
from .ammunition import Magazine


class WeaponType(Enum):
    PISTOL = "pistol"
    RIFLE = "rifle"
    SHOTGUN = "shotgun"
    SMG = "smg"
    SNIPER = "sniper"
    LASER = "laser"


class Weapon:
    """武器基类"""

    def __init__(self, weapon_id: str, name: str, wtype: WeaponType,
                 damage: int, fire_rate: int, bullet_speed: float,
                 magazine_size: int, pellets: int = 1, spread: float = 0.0,
                 color: tuple = (255, 215, 0), unlocked: bool = True):
        self.weapon_id = weapon_id
        self.name = name
        self.wtype = wtype
        self.damage = damage
        self.fire_rate = fire_rate  # 每秒发射次数
        self.bullet_speed = bullet_speed
        self.magazine = Magazine(magazine_size)
        self.pellets = pellets
        self.spread = spread
        self.color = color
        self.unlocked = unlocked

        # 冷却以帧计算（60fps）
        self.cooldown_frames = max(1, 60 // fire_rate)
        self.current_cooldown = 0

    @property
    def is_automatic(self) -> bool:
        return self.wtype in (WeaponType.RIFLE, WeaponType.SMG, WeaponType.LASER)

    def can_shoot(self) -> bool:
        return self.current_cooldown <= 0 and not self.magazine.is_empty()

    def shoot(self) -> bool:
        if not self.can_shoot():
            return False
        if not self.magazine.shoot():
            return False
        self.current_cooldown = self.cooldown_frames
        return True

    def update(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def reload(self) -> bool:
        return self.magazine.reload()

    def to_dict(self) -> dict:
        return {
            "weapon_id": self.weapon_id,
            "name": self.name,
            "wtype": self.wtype.value,
            "damage": self.damage,
            "fire_rate": self.fire_rate,
            "bullet_speed": self.bullet_speed,
            "magazine": self.magazine.to_dict(),
            "pellets": self.pellets,
            "spread": self.spread,
            "color": self.color,
            "unlocked": self.unlocked,
            "current_cooldown": self.current_cooldown,
        }

    def from_dict(self, data: dict):
        self.weapon_id = data.get("weapon_id", self.weapon_id)
        self.name = data.get("name", self.name)
        self.wtype = WeaponType(data.get("wtype", self.wtype.value))
        self.damage = data.get("damage", self.damage)
        self.fire_rate = data.get("fire_rate", self.fire_rate)
        self.bullet_speed = data.get("bullet_speed", self.bullet_speed)
        self.magazine.from_dict(data.get("magazine", {}))
        self.pellets = data.get("pellets", self.pellets)
        self.spread = data.get("spread", self.spread)
        self.color = tuple(data.get("color", self.color))
        self.unlocked = data.get("unlocked", self.unlocked)
        self.current_cooldown = data.get("current_cooldown", self.current_cooldown)

    def copy(self):
        """返回一个独立副本"""
        w = Weapon(
            self.weapon_id, self.name, self.wtype, self.damage,
            self.fire_rate, self.bullet_speed, self.magazine.capacity,
            self.pellets, self.spread, self.color, self.unlocked
        )
        w.magazine.current = self.magazine.current
        w.current_cooldown = self.current_cooldown
        return w
