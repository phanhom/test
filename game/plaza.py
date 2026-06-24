"""广场场景 - 可走动的 Lobby"""

import pygame
import math
from typing import Optional
from .player_state import ActionStateMachine, PlayerState


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
        self.normal_height = 48
        self.crouch_height = 28
        self.on_ground = False
        self.action_sm = ActionStateMachine()


class Plaza:
    """可走动的广场"""
    GRAVITY = 0.5
    JUMP_FORCE = -11
    MOVE_SPEED = 4
    DASH_SPEED = 10
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

    def update_player(self, player_id: int, left: bool, right: bool, jump: bool,
                      crouch: bool = False, melee: bool = False, dash: bool = False):
        if player_id not in self.players:
            return
        p = self.players[player_id]
        p.action_sm.update()

        prev_state = p.action_sm.state
        p.action_sm.handle_input(
            left=left, right=right, jump=jump, crouch=crouch,
            melee=melee, dash=dash, on_ground=p.on_ground
        )

        # 蹲伏调整高度
        if p.action_sm.state == PlayerState.CROUCH:
            p.height = p.crouch_height
        elif p.height != p.normal_height:
            p.y -= p.normal_height - p.crouch_height
            p.height = p.normal_height

        speed = self.DASH_SPEED if p.action_sm.state == PlayerState.DASH else self.MOVE_SPEED
        if p.action_sm.state == PlayerState.CROUCH:
            speed *= 0.3

        if left:
            p.vel_x = -speed
            p.facing_right = False
        if right:
            p.vel_x = speed
            p.facing_right = True
        if not left and not right:
            p.vel_x *= 0.8

        if jump and p.on_ground and p.action_sm.state not in (PlayerState.DASH, PlayerState.MELEE, PlayerState.CROUCH):
            p.vel_y = self.JUMP_FORCE
            p.on_ground = False
            p.action_sm.set_state(PlayerState.JUMP)

        p.x += p.vel_x
        p.y += p.vel_y
        p.vel_y += self.GRAVITY

        p.x = max(0, min(self.world_width - p.width, p.x))

        p.on_ground = False
        for (px, py, pw, ph) in self.platforms:
            if p.vel_y > 0 and p.y + p.height > py and p.y < py + ph:
                if p.x + p.width > px and p.x < px + pw:
                    if p.y + p.height - p.vel_y <= py:
                        p.y = py - p.height
                        p.vel_y = 0
                        p.on_ground = True
                        if p.action_sm.state == PlayerState.JUMP:
                            p.action_sm.set_state(PlayerState.IDLE)
                        break
        else:
            if p.y + p.height > self.ground_y:
                p.y = self.ground_y - p.height
                p.vel_y = 0
                p.on_ground = True
                if p.action_sm.state == PlayerState.JUMP:
                    p.action_sm.set_state(PlayerState.IDLE)
            elif p.action_sm.state not in (PlayerState.JUMP, PlayerState.DASH, PlayerState.MELEE):
                p.action_sm.set_state(PlayerState.JUMP)

        self.camera_x = p.x - self.screen_width // 2 + p.width // 2
        self.camera_x = max(0, min(self.world_width - self.screen_width, self.camera_x))

    def get_positions(self) -> dict:
        return {
            pid: {"x": p.x, "y": p.y, "facing_right": p.facing_right,
                  "action": p.action_sm.to_dict(), "height": p.height}
            for pid, p in self.players.items()
        }

    def apply_positions(self, positions: dict):
        for pid, pos in positions.items():
            if pid in self.players:
                p = self.players[pid]
                p.x = pos.get("x", p.x)
                p.y = pos.get("y", p.y)
                p.facing_right = pos.get("facing_right", True)
                p.height = pos.get("height", p.normal_height)
                p.action_sm.from_dict(pos.get("action", {}))
