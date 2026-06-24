"""枪械系统测试"""

import pytest
import pygame

pygame.init()


class TestAmmunition:
    def test_default_magazine_has_capacity(self):
        from game.weapons.ammunition import Magazine

        mag = Magazine(capacity=30)
        assert mag.current == 30
        assert mag.capacity == 30

    def test_shoot_consumes_ammo(self):
        from game.weapons.ammunition import Magazine

        mag = Magazine(capacity=10)
        assert mag.shoot() is True
        assert mag.current == 9

    def test_empty_magazine_cannot_shoot(self):
        from game.weapons.ammunition import Magazine

        mag = Magazine(capacity=1)
        mag.shoot()
        assert mag.shoot() is False
        assert mag.current == 0

    def test_reload_refills(self):
        from game.weapons.ammunition import Magazine

        mag = Magazine(capacity=10)
        for _ in range(5):
            mag.shoot()
        mag.reload()
        assert mag.current == 10

    def test_reload_while_full_does_nothing(self):
        from game.weapons.ammunition import Magazine

        mag = Magazine(capacity=10)
        assert mag.reload() is False
        assert mag.current == 10


class TestWeapon:
    def test_weapon_has_basic_stats(self):
        from game.weapons.weapon import Weapon, WeaponType

        w = Weapon(weapon_id="rifle", name="突击步枪", wtype=WeaponType.RIFLE,
                   damage=25, fire_rate=8, bullet_speed=18, magazine_size=30)
        assert w.name == "突击步枪"
        assert w.damage == 25
        assert w.magazine.capacity == 30

    def test_pistol_is_semi_auto(self):
        from game.weapons.weapon import Weapon, WeaponType

        w = Weapon(weapon_id="pistol", name="手枪", wtype=WeaponType.PISTOL,
                   damage=15, fire_rate=4, bullet_speed=14, magazine_size=12)
        assert w.is_automatic is False

    def test_rifle_is_automatic(self):
        from game.weapons.weapon import Weapon, WeaponType

        w = Weapon(weapon_id="rifle", name="步枪", wtype=WeaponType.RIFLE,
                   damage=20, fire_rate=10, bullet_speed=18, magazine_size=30)
        assert w.is_automatic is True

    def test_shotgun_fires_multiple_projectiles(self):
        from game.weapons.weapon import Weapon, WeaponType

        w = Weapon(weapon_id="shotgun", name="霰弹枪", wtype=WeaponType.SHOTGUN,
                   damage=12, fire_rate=1, bullet_speed=12, magazine_size=8,
                   pellets=5)
        assert w.pellets == 5

    def test_weapon_can_shoot_respects_cooldown(self):
        from game.weapons.weapon import Weapon, WeaponType

        w = Weapon(weapon_id="pistol", name="手枪", wtype=WeaponType.PISTOL,
                   damage=15, fire_rate=1, bullet_speed=14, magazine_size=12)
        assert w.can_shoot() is True
        w.shoot()
        assert w.can_shoot() is False


class TestArmory:
    def test_get_default_weapon(self):
        from game.weapons.armory import Armory

        armory = Armory()
        w = armory.get("rifle")
        assert w is not None
        assert w.weapon_id == "rifle"

    def test_get_unknown_weapon_returns_default(self):
        from game.weapons.armory import Armory

        armory = Armory()
        w = armory.get("does_not_exist")
        assert w.weapon_id == "pistol"

    def test_list_unlocked_weapons(self):
        from game.weapons.armory import Armory

        armory = Armory()
        weapons = armory.list_unlocked([])
        assert "pistol" in weapons
        assert "laser" in weapons


class TestWeaponEntityIntegration:
    def test_player_has_equipped_weapon(self):
        from game.entities import Player
        from game.weapons.weapon import Weapon, WeaponType

        player = Player(0, 0, player_id=0)
        weapon = Weapon(weapon_id="rifle", name="突击步枪", wtype=WeaponType.RIFLE,
                        damage=25, fire_rate=8, bullet_speed=18, magazine_size=30)
        player.equip_weapon(weapon)
        assert player.weapon is weapon

    def test_player_shoot_uses_weapon_bullet_speed(self):
        from game.entities import Player
        from game.weapons.weapon import Weapon, WeaponType

        player = Player(100, 0, player_id=0)
        player.facing_right = True
        weapon = Weapon(weapon_id="rifle", name="突击步枪", wtype=WeaponType.RIFLE,
                        damage=25, fire_rate=8, bullet_speed=18, magazine_size=30)
        player.equip_weapon(weapon)
        bullets = player.shoot_with_weapon()
        assert len(bullets) == 1
        assert bullets[0].speed == 18

    def test_shotgun_creates_multiple_bullets(self):
        from game.entities import Player
        from game.weapons.weapon import Weapon, WeaponType

        player = Player(100, 0, player_id=0)
        player.facing_right = True
        weapon = Weapon(weapon_id="shotgun", name="霰弹枪", wtype=WeaponType.SHOTGUN,
                        damage=12, fire_rate=1, bullet_speed=12, magazine_size=8,
                        pellets=5, spread=0.2)
        player.equip_weapon(weapon)
        bullets = player.shoot_with_weapon()
        assert len(bullets) == 5
