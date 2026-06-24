"""角色动作系统测试"""

import pytest
import pygame

pygame.init()


class TestPlayerStateMachine:
    def test_initial_state_is_idle(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        assert sm.state == PlayerState.IDLE

    def test_crouch_input_transitions_to_crouch(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(crouch=True)
        assert sm.state == PlayerState.CROUCH

    def test_dash_input_transitions_to_dash(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(dash=True)
        assert sm.state == PlayerState.DASH

    def test_dash_has_duration(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(dash=True)
        assert sm.state == PlayerState.DASH
        for _ in range(sm.dash_duration):
            sm.update()
        assert sm.state == PlayerState.IDLE

    def test_melee_input_transitions_to_melee(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(melee=True)
        assert sm.state == PlayerState.MELEE

    def test_melee_has_duration(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(melee=True)
        assert sm.state == PlayerState.MELEE
        for _ in range(melee_duration := sm.melee_duration):
            sm.update()
        assert sm.state == PlayerState.IDLE

    def test_cannot_crouch_while_jumping(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.set_state(PlayerState.JUMP)
        sm.handle_input(crouch=True)
        assert sm.state == PlayerState.JUMP

    def test_dash_has_cooldown(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(dash=True)
        assert sm.state == PlayerState.DASH
        # run out dash duration
        for _ in range(sm.dash_duration):
            sm.update()
        assert sm.state == PlayerState.IDLE
        # try to dash again immediately
        sm.handle_input(dash=True)
        assert sm.state == PlayerState.IDLE

    def test_serialization_includes_state(self):
        from game.player_state import ActionStateMachine, PlayerState

        sm = ActionStateMachine()
        sm.handle_input(dash=True)
        data = sm.to_dict()
        assert data["state"] == "dash"

        sm2 = ActionStateMachine()
        sm2.from_dict(data)
        assert sm2.state == PlayerState.DASH


class TestPlayerActionIntegration:
    def test_player_has_action_state_machine(self):
        from game.entities import Player
        from game.player_state import ActionStateMachine

        player = Player(0, 0, player_id=0)
        assert hasattr(player, "action_sm")
        assert isinstance(player.action_sm, ActionStateMachine)

    def test_player_crouch_changes_hitbox(self):
        from game.entities import Player

        player = Player(0, 0, player_id=0)
        original_height = player.rect.height
        player.crouch()
        assert player.rect.height < original_height

    def test_player_dash_sets_velocity(self):
        from game.entities import Player

        player = Player(100, 0, player_id=0)
        player.facing_right = True
        start_x = player.rect.x
        player.start_dash()
        player.update([])
        assert player.rect.x > start_x

    def test_player_melee_creates_hitbox(self):
        from game.entities import Player

        player = Player(100, 0, player_id=0)
        player.facing_right = True
        player.melee_attack()
        assert player.melee_hitbox is not None
