"""游戏主逻辑 - 整合地图、关卡、实体、聊天、武器"""

import pygame
import random
from .constants import *
from .entities import Player, Bullet, Enemy
from .skins import SKINS
from .maps import get_map
from .levels import LEVEL_CONFIGS
from .weapons.pickup import WeaponPickup
from .weapons.armory import Armory
from core.seasons import SEASON_ORDER, get_next_season
from .player_state import PlayerState


class Game:
    def __init__(self, screen, is_host: bool = False, is_client: bool = False,
                 player_skins: list = None, network=None):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.score = 0
        self.lives = 3
        self.current_level = 0
        self.enemies_killed_this_level = 0
        self.level_config = LEVEL_CONFIGS[0]
        self.current_map = get_map(0)
        self.enemy_spawn_timer = 0
        self.enemy_id_counter = 0
        self.shoot_cooldown = [0, 0]
        self.game_phase = "playing"
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)

        # 季节系统
        self.current_season = "spring"
        self.season_timer = 0
        self.season_cycle_time = 1800  # 30秒切换一次季节（60fps * 30）

        self.player_skins = player_skins or [0, 1]
        self.players: list[Player] = []
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()

        self.is_host = is_host
        self.is_client = is_client
        self.network = network
        self.player_count = 2 if (is_host or is_client) else 1

        self.chat = None
        if network:
            from ui.chat import ChatBox
            self.chat = ChatBox(screen, y=SCREEN_HEIGHT - 130)

        self._spawn_pickups()
        self._init_players()

    def _spawn_pickups(self):
        armory = Armory()
        ids = armory.list_unlocked(["shotgun", "sniper"])
        # 每张地图放 2 个武器箱
        for _ in range(2):
            wid = random.choice(ids)
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = GROUND_Y - 40
            self.pickups.add(WeaponPickup(x, y, wid))

    def _init_players(self):
        self.players.clear()
        spawns = self.current_map["spawns"]
        if self.player_count == 1:
            x, y = spawns[0]
            self.players.append(Player(x, y - 50, 0, self.player_skins[0], self.current_season))
        else:
            for i in range(2):
                x, y = spawns[i] if i < len(spawns) else spawns[0]
                self.players.append(Player(x, y - 50, i, self.player_skins[i], self.current_season))

    def _init_level(self):
        self.bullets.empty()
        self.enemies.empty()
        self.enemies_killed_this_level = 0
        self.enemy_spawn_timer = 0
        self.level_config = LEVEL_CONFIGS[min(self.current_level, len(LEVEL_CONFIGS) - 1)]
        self.current_map = get_map(self.current_level)
        spawns = self.current_map["spawns"]
        for i, p in enumerate(self.players):
            x, y = spawns[i] if i < len(spawns) else spawns[0]
            p.rect.x = x
            p.rect.y = y - 50
            p.vel_y = 0

    def spawn_enemy(self):
        side = random.choice(["left", "right"])
        x = -50 if side == "left" else SCREEN_WIDTH + 50
        enemy = Enemy(x, GROUND_Y - 45, self.level_config["enemy_speed"], self.enemy_id_counter)
        enemy.direction = 1 if side == "left" else -1
        self.enemy_id_counter += 1
        self.enemies.add(enemy)

    def serialize_state(self) -> dict:
        return {
            "players": [p.to_dict() for p in self.players],
            "player_skins": self.player_skins,
            "bullets": [{"x": b.rect.centerx, "y": b.rect.centery, "d": b.direction,
                         "s": b.speed, "c": b.image.get_at((0, 0))[:3], "dmg": b.damage} for b in self.bullets],
            "enemies": [{"x": e.rect.x, "y": e.rect.y, "d": e.direction} for e in self.enemies],
            "pickups": [p.to_dict() for p in self.pickups],
            "score": self.score,
            "lives": self.lives,
            "level": self.current_level,
            "enemies_killed": self.enemies_killed_this_level,
            "level_config": self.level_config,
            "map_id": self.current_map["id"],
            "paused": self.paused,
            "phase": self.game_phase,
        }

    def apply_state(self, state: dict):
        self.score = state.get("score", 0)
        self.lives = state.get("lives", 3)
        self.current_level = state.get("level", 0)
        self.enemies_killed_this_level = state.get("enemies_killed", 0)
        self.level_config = state.get("level_config", LEVEL_CONFIGS[0])
        self.paused = state.get("paused", False)
        self.game_phase = state.get("phase", "playing")
        self.player_skins = state.get("player_skins", self.player_skins)
        map_id = state.get("map_id", 0)
        from .maps import MAPS
        self.current_map = MAPS[map_id % len(MAPS)]

        for i, pd in enumerate(state.get("players", [])):
            if i < len(self.players):
                self.players[i].from_dict(pd)
                self.players[i].skin_id = self.player_skins[i] if i < len(self.player_skins) else pd.get("skin_id", 0)

        self.bullets.empty()
        for bd in state.get("bullets", []):
            color = tuple(bd.get("c", (255, 215, 0)))
            b = Bullet(bd["x"], bd["y"], bd["d"], speed=bd.get("s", BULLET_SPEED), damage=bd.get("dmg", 10), color=color)
            b.rect.center = (bd["x"], bd["y"])
            self.bullets.add(b)

        self.enemies.empty()
        for ed in state.get("enemies", []):
            e = Enemy(ed["x"], ed["y"], self.level_config.get("enemy_speed", 2), 0)
            e.direction = ed["d"]
            self.enemies.add(e)

        self.pickups.empty()
        for pd in state.get("pickups", []):
            self.pickups.add(WeaponPickup.from_dict(pd))

    def run(self):
        if self.is_client:
            self._run_client()
        else:
            self._run_host_or_single()

    def _run_host_or_single(self):
        while self.running:
            self.handle_events()
            if self.chat and self.network:
                self.chat.set_messages(self.network.get_chat_messages())
            if not self.paused and self.lives > 0:
                self.update()
                if self.is_host and self.network:
                    self.network.broadcast_state(self.serialize_state())
            self.draw()
            self.clock.tick(FPS)
            pygame.display.flip()

    def _run_client(self):
            keys_state = {"left": 0, "right": 0, "jump": 0, "crouch": 0, "shoot": 0, "melee": 0, "dash": 0}
            last_shoot = False
            last_melee = False
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not (self.chat and self.chat.input_active):
                        self.paused = not self.paused
                    if self.chat:
                        msg = self.chat.handle_event(event)
                        if msg:
                            self.network.send_chat(msg)

                if self.chat:
                    self.chat.set_messages(self.network.get_chat_messages())

                if not (self.chat and self.chat.input_active):
                    keys = pygame.key.get_pressed()
                    keys_state["left"] = 1 if keys[pygame.K_LEFT] else 0
                    keys_state["right"] = 1 if keys[pygame.K_RIGHT] else 0
                    keys_state["jump"] = 1 if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE] else 0
                    keys_state["crouch"] = 1 if keys[pygame.K_DOWN] else 0
                    shoot_now = keys[pygame.K_k]
                    keys_state["shoot"] = 1 if shoot_now and not last_shoot else 0
                    last_shoot = shoot_now
                    melee_now = keys[pygame.K_j]
                    keys_state["melee"] = 1 if melee_now and not last_melee else 0
                    last_melee = melee_now
                    keys_state["dash"] = 1 if keys[pygame.K_l] else 0
                self.network.send_input(keys_state)

            state = self.network.get_state()
            if state:
                self.apply_state(state)
                self.draw()
            else:
                self.screen.fill((30, 50, 80))
                font = pygame.font.Font(None, 48)
                text = font.render("等待主机开始游戏...", True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 24))

            self.clock.tick(FPS)
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.chat:
                msg = self.chat.handle_event(event)
                if msg:
                    if self.is_host and self.network:
                        self.network.broadcast_chat("主机", msg)
                    elif self.is_client and self.network:
                        self.network.send_chat(msg)
                if self.chat.input_active:
                    continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.paused = not self.paused
                elif event.key == pygame.K_e:
                    self._try_pickup_weapon(0)
                elif event.key == pygame.K_1:
                    self._switch_weapon_by_index(0, 0)
                elif event.key == pygame.K_2:
                    self._switch_weapon_by_index(0, 1)
                elif event.key == pygame.K_3:
                    self._switch_weapon_by_index(0, 2)
                elif event.key == pygame.K_r:
                    if self.players:
                        self.players[0].weapon.reload()

        if not self.paused and self.lives > 0:
            keys = pygame.key.get_pressed()

            # P1 输入处理
            if len(self.players) > 0 and not self.is_client:
                p1 = self.players[0]
                p1.handle_input(
                    left=keys[pygame.K_a],
                    right=keys[pygame.K_d],
                    jump=keys[pygame.K_w] or keys[pygame.K_SPACE],
                    crouch=keys[pygame.K_s],
                    shoot=keys[pygame.K_j],
                    melee=keys[pygame.K_k],
                    dash=keys[pygame.K_l],
                )
                # 射击由状态机触发或在 handle_input 中处理；这里保持原来的 shoot 调用
                if keys[pygame.K_j]:
                    self._shoot(0)

            # P2 / 联机客户端输入处理
            if len(self.players) > 1:
                if self.is_host and self.network and len(self.network.clients) > 0:
                    inp = self.network.get_input(1)
                    p2 = self.players[1]
                    p2.handle_input(
                        left=inp.get("left", 0),
                        right=inp.get("right", 0),
                        jump=inp.get("jump", 0),
                        crouch=inp.get("crouch", 0),
                        shoot=inp.get("shoot", 0),
                        melee=inp.get("melee", 0),
                        dash=inp.get("dash", 0),
                    )
                    if inp.get("shoot"):
                        self._shoot(1)
                    if inp.get("melee"):
                        self._melee(1)
                elif not self.is_client:
                    p2 = self.players[1]
                    p2.handle_input(
                        left=keys[pygame.K_LEFT],
                        right=keys[pygame.K_RIGHT],
                        jump=keys[pygame.K_UP],
                        crouch=keys[pygame.K_DOWN],
                        shoot=keys[pygame.K_k],
                        melee=keys[pygame.K_j],
                        dash=keys[pygame.K_l],
                    )
                    if keys[pygame.K_k]:
                        self._shoot(1)
                    if keys[pygame.K_j]:
                        self._melee(1)

    def _switch_weapon_by_index(self, player_id: int, index: int):
        if player_id >= len(self.players):
            return
        p = self.players[player_id]
        if index < len(p.weapon_inventory):
            p.switch_weapon(p.weapon_inventory[index])

    def _try_pickup_weapon(self, player_id: int):
        if player_id >= len(self.players):
            return
        p = self.players[player_id]
        for pickup in self.pickups:
            if p.rect.colliderect(pickup.rect):
                p.pickup_weapon(pickup.weapon)
                pickup.kill()
                break

    def _shoot(self, player_id: int):
        if player_id >= len(self.players):
            return
        p = self.players[player_id]
        if p.action_sm.state in (PlayerState.MELEE, PlayerState.DASH, PlayerState.HURT):
            return
        if p.weapon.can_shoot():
            bullets = p.shoot_with_weapon()
            self.bullets.add(*bullets)
            p.action_sm.set_state(PlayerState.SHOOT)

    def _melee(self, player_id: int):
        if player_id >= len(self.players):
            return
        p = self.players[player_id]
        if p.action_sm.state != PlayerState.MELEE or p.melee_hitbox is None:
            return
        # 近战攻击命中敌人
        for enemy in self.enemies:
            if p.melee_hitbox.colliderect(enemy.rect):
                enemy.kill()
                self.score += 150
                self.enemies_killed_this_level += 1
        p.melee_hitbox = None

    def update(self):
        # 更新季节系统
        self.season_timer += 1
        if self.season_timer >= self.season_cycle_time:
            self.season_timer = 0
            self.current_season = get_next_season(self.current_season)
            # 更新所有玩家的季节
            for player in self.players:
                player.set_season(self.current_season)

        for i in range(len(self.shoot_cooldown)):
            if self.shoot_cooldown[i] > 0:
                self.shoot_cooldown[i] -= 1

        platforms = self.current_map.get("platforms", [])
        for p in self.players:
            p.update(platforms)

        for bullet in self.bullets:
            bullet.update()

        for bullet in self.bullets:
            hit = pygame.sprite.spritecollide(bullet, self.enemies, True)
            if hit:
                bullet.kill()
                self.score += 100
                self.enemies_killed_this_level += 1

        for p in self.players:
            for pickup in self.pickups:
                if p.rect.colliderect(pickup.rect):
                    pickup.kill()
                    p.pickup_weapon(pickup.weapon)
                    break

        for enemy in self.enemies:
            enemy.update()

        for p in self.players:
            if pygame.sprite.spritecollide(p, self.enemies, True):
                self.lives -= 1
                p.action_sm.set_state(PlayerState.HURT)
                pygame.time.delay(500)

        for p in self.players:
            if p.weapon:
                p.weapon.update()

        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer >= self.level_config["spawn_interval"]:
            self.enemy_spawn_timer = 0
            if len(self.enemies) < 5:
                self.spawn_enemy()

    def draw_map(self):
        m = self.current_map
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(m["sky_top"][0] * (1 - t) + m["sky_bottom"][0] * t)
            g = int(m["sky_top"][1] * (1 - t) + m["sky_bottom"][1] * t)
            b = int(m["sky_top"][2] * (1 - t) + m["sky_bottom"][2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        ground_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
        pygame.draw.rect(self.screen, m["ground"], ground_rect)
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, m["ground_line"], (i, GROUND_Y), (i + 20, SCREEN_HEIGHT), 2)

        for (px, py, pw, ph) in m.get("platforms", []):
            pygame.draw.rect(self.screen, m["ground"], (px, py, pw, ph))
            pygame.draw.rect(self.screen, m["ground_line"], (px, py, pw, ph), 2)

    def draw(self):
        self.draw_map()
        for p in self.players:
            p.draw(self.screen)
        for bullet in self.bullets:
            self.screen.blit(bullet.image, bullet.rect)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for pickup in self.pickups:
            pickup.draw(self.screen)

        score_text = self.font.render(f"分数: {self.score}", True, WHITE)
        lives_text = self.font.render(f"生命: {self.lives}", True, RED)

        # 获取季节名称
        from core.seasons import get_season_config
        season_config = get_season_config(self.current_season)
        season_name = season_config["name"]

        level_text = self.font.render(
            f"关卡 {self.current_level + 1}/{len(LEVEL_CONFIGS)}: {self.level_config['name']} | "
            f"地图: {self.current_map['name']} | "
            f"季节: {season_name} | "
            f"消灭: {self.enemies_killed_this_level}/{self.level_config['enemies_to_kill']}",
            True, WHITE
        )
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))
        self.screen.blit(level_text, (10, 45))

        # 武器信息
        if self.players:
            p = self.players[0]
            w = p.weapon
            weapon_text = self.font.render(
                f"武器: {w.name} {w.magazine.current}/{w.magazine.capacity}", True, YELLOW
            )
            self.screen.blit(weapon_text, (10, 80))

        # 动作提示
        if self.players:
            actions = "/".join([p.action_sm.state.value for p in self.players])
            action_text = self.font.render(f"动作: {actions}", True, CYAN)
            self.screen.blit(action_text, (SCREEN_WIDTH // 2 - 80, 80))

        if self.is_host and self.network:
            conn_text = self.font.render(
                f"联机: {len(self.network.clients)}人 | IP:{self.network.get_local_ip()}", True, CYAN
            )
            self.screen.blit(conn_text, (SCREEN_WIDTH - 280, 45))

        if self.paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            pause_text = self.big_font.render("暂停 - 按 ESC 继续", True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 36))

        if self.lives <= 0:
            self.game_phase = "game_over"
        if self.game_phase == "game_over":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            game_over = self.big_font.render("游戏结束", True, RED)
            score_final = self.font.render(f"最终分数: {self.score}", True, WHITE)
            self.screen.blit(game_over, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(score_final, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 20))
        elif self.game_phase == "game_win":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            win_text = self.big_font.render("通关！", True, YELLOW)
            score_text = self.font.render(f"最终分数: {self.score}", True, WHITE)
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 20))

        if self.chat:
            self.chat.draw()

        if not self.is_client and self.enemies_killed_this_level >= self.level_config["enemies_to_kill"]:
            self._level_complete()

    def _level_complete(self):
        self.game_phase = "level_complete"
        self.current_level += 1
        if self.current_level >= len(LEVEL_CONFIGS):
            self.game_phase = "game_win"
            self._game_win()
        else:
            self._show_level_transition()

    def _show_level_transition(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        next_config = LEVEL_CONFIGS[self.current_level]
        next_map = get_map(self.current_level)
        level_text = self.big_font.render(f"关卡 {self.current_level + 1}", True, YELLOW)
        name_text = self.font.render(f"{next_config['name']} - {next_map['name']}", True, WHITE)
        next_text = self.font.render("按 空格 继续", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(next_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 20))
        pygame.display.flip()

        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                    return
                if e.type == pygame.KEYDOWN and (e.key == pygame.K_SPACE or e.key == pygame.K_RETURN):
                    waiting = False
            self.clock.tick(FPS)

        self.game_phase = "playing"
        self._init_level()

    def _game_win(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        win_text = self.big_font.render("通关！", True, YELLOW)
        score_text = self.font.render(f"最终分数: {self.score}", True, WHITE)
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 20))
        pygame.display.flip()

        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                    return
                if e.type == pygame.KEYDOWN:
                    waiting = False
            self.clock.tick(FPS)
        self.running = False
