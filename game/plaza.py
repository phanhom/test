"""广场场景 - 可走动的 Lobby"""

import pygame
import math
from typing import Optional


class PlazaPlayer:
    """广场中的玩家"""
    def __init__(self, x: float, y: float, player_id: int, name: str = ""):
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.player_id = player_id
        self.name = name
        self.facing_right = True
        self.width = 36
        self.height = 48


class Plaza:
    """可走动的广场"""
    GRAVITY = 0.5
    JUMP_FORCE = -11
    MOVE_SPEED = 4
    GROUND_Y = 0  # 相对地面高度

    def __init__(self, width: int, height: int, world_width: int = 2048):
        self.screen_width = width
        self.screen_height = height
        self.world_width = world_width
        self.ground_y = height - 100
        self.players: dict[int, PlazaPlayer] = {}
        self.camera_x = 0
        self.platforms = self._get_platforms()

    def _get_platforms(self) -> list:
        """平台布局"""
        ground = self.ground_y
        return [
            (0, ground, self.world_width, self.screen_height - ground),
            (200, ground - 80, 120, 20),
            (500, ground - 120, 150, 20),
            (900, ground - 60, 100, 20),
            (1300, ground - 100, 140, 20),
        ]

    def add_player(self, player_id: int, name: str = "", x: float = None):
        if x is None:
            x = 100 + player_id * 80
        self.players[player_id] = PlazaPlayer(x, self.ground_y - 48, player_id, name)

    def update_player(self, player_id: int, left: bool, right: bool, jump: bool):
        if player_id not in self.players:
            return
        p = self.players[player_id]
        if left:
            p.vel_x = -self.MOVE_SPEED
            p.facing_right = False
        if right:
            p.vel_x = self.MOVE_SPEED
            p.facing_right = True
        if not left and not right:
            p.vel_x *= 0.8
        if jump:
            p.vel_y = self.JUMP_FORCE

        p.x += p.vel_x
        p.y += p.vel_y
        p.vel_y += self.GRAVITY

        p.x = max(0, min(self.world_width - p.width, p.x))

        for (px, py, pw, ph) in self.platforms:
            if p.vel_y > 0 and p.y + p.height > py and p.y < py + ph:
                if p.x + p.width > px and p.x < px + pw:
                    if p.y + p.height - p.vel_y <= py:
                        p.y = py - p.height
                        p.vel_y = 0
                        break
        else:
            if p.y + p.height > self.ground_y:
                p.y = self.ground_y - p.height
                p.vel_y = 0

        self.camera_x = p.x - self.screen_width // 2 + p.width // 2
        self.camera_x = max(0, min(self.world_width - self.screen_width, self.camera_x))

    def get_positions(self) -> dict:
        return {
            pid: {"x": p.x, "y": p.y, "facing_right": p.facing_right}
            for pid, p in self.players.items()
        }

    def apply_positions(self, positions: dict):
        for pid, pos in positions.items():
            if pid in self.players:
                self.players[pid].x = pos.get("x", self.players[pid].x)
                self.players[pid].y = pos.get("y", self.players[pid].y)
                self.players[pid].facing_right = pos.get("facing_right", True)
