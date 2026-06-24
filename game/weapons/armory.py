"""武器库 - 管理所有可用武器"""

from .weapon import Weapon, WeaponType


class Armory:
    """武器库，提供武器模板与解锁查询"""

    _WEAPONS = [
        Weapon("pistol", "手枪", WeaponType.PISTOL, 15, 4, 14, 12,
               color=(255, 215, 0), unlocked=True),
        Weapon("rifle", "突击步枪", WeaponType.RIFLE, 25, 8, 18, 30,
               color=(100, 100, 100), unlocked=True),
        Weapon("smg", "冲锋枪", WeaponType.SMG, 12, 15, 16, 35,
               color=(34, 139, 34), unlocked=True),
        Weapon("shotgun", "霰弹枪", WeaponType.SHOTGUN, 12, 2, 12, 8,
               pellets=5, spread=0.15, color=(160, 82, 45), unlocked=False),
        Weapon("sniper", "狙击枪", WeaponType.SNIPER, 80, 1, 28, 5,
               color=(50, 50, 80), unlocked=False),
        Weapon("laser", "激光枪", WeaponType.LASER, 20, 12, 22, 25,
               color=(0, 255, 255), unlocked=True),
    ]

    def __init__(self):
        self._by_id = {w.weapon_id: w for w in self._WEAPONS}

    def get(self, weapon_id: str) -> Weapon:
        """获取武器模板副本；不存在返回手枪"""
        w = self._by_id.get(weapon_id)
        if w is None:
            w = self._by_id["pistol"]
        return w.copy()

    def list_all(self) -> list[str]:
        return list(self._by_id.keys())

    def list_unlocked(self, unlocked_ids: list[str] = None) -> list[str]:
        """返回已解锁武器 id 列表。"""
        unlocked_ids = set(unlocked_ids or [])
        return [
            wid for wid, w in self._by_id.items()
            if w.unlocked or wid in unlocked_ids
        ]

    def unlock_weapon(self, weapon_id: str):
        if weapon_id in self._by_id:
            self._by_id[weapon_id].unlocked = True
