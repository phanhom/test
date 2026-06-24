"""武器拾取道具"""

import pygame
from .armory import Armory
from .weapon import Weapon


class WeaponPickup(pygame.sprite.Sprite):
    """地图上的武器拾取箱"""

    WIDTH = 30
    HEIGHT = 20

    def __init__(self, x: float, y: float, weapon_id: str):
        super().__init__()
        self.weapon_id = weapon_id
        self.armory = Armory()
        self.weapon = self.armory.get(weapon_id)
        self.image = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.image.fill(self.weapon.color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def pickup(self) -> Weapon:
        return self.armory.get(self.weapon_id)

    def to_dict(self) -> dict:
        return {
            "x": self.rect.x,
            "y": self.rect.y,
            "weapon_id": self.weapon_id,
        }

    @staticmethod
    def from_dict(data: dict) -> "WeaponPickup":
        return WeaponPickup(data.get("x", 0), data.get("y", 0), data.get("weapon_id", "pistol"))

    def draw(self, surface):
        pygame.draw.rect(surface, self.weapon.color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
