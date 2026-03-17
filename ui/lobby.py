"""房间大厅 - 可走动广场、四季、NPC 对话、聊天"""

import pygame
import math
import time
from game.constants import WHITE, GRAY, YELLOW, GREEN
from game.plaza import Plaza, PlazaPlayer
from core.seasons import get_season_config, get_next_season, SEASON_ORDER
from ui.chat import ChatBox
from ui.npc_dialogue import NPCDialogue


def _create_npcs(config: dict, world_width: int):
    from npc.npc_entity import NPCEntity
    from npc.llm_client import LLMClient

    npc_config = config.get("npc", {})
    if not npc_config.get("enabled", False):
        return []

    llm_cfg = npc_config.get("llm", {})
    api_key = llm_cfg.get("api_key", "")
    llm = LLMClient(
        api_key=api_key,
        model=llm_cfg.get("model", "gpt-4o-mini"),
        base_url=llm_cfg.get("base_url", "https://api.openai.com/v1"),
        timeout=llm_cfg.get("timeout", 30),
    ) if api_key else None

    npcs = []
    positions = [200, 550, 900, 1250, 1600][:len(npc_config.get("list", []))]
    for i, item in enumerate(npc_config.get("list", [])):
        x = item.get("x", positions[i] if i < len(positions) else 300)
        x = min(x, world_width - 100)
        npc = NPCEntity(
            npc_id=item.get("id", "npc"),
            name=item.get("name", "NPC"),
            role=item.get("role", ""),
            prompt=item.get("prompt", "你是一个NPC。"),
            x=int(x),
            y=0,
            llm_client=llm,
        )
        npcs.append(npc)
    return npcs


class Lobby:
    """大厅 - 可走动广场 + 四季"""
    def __init__(self, screen, is_host: bool, server=None, client=None, width: int = 1024, height: int = 640):
        self.screen = screen
        self.width = width
        self.height = height
        self.is_host = is_host
        self.server = server
        self.client = client
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.big_font = pygame.font.Font(None, 48)
        self.ready = False
        self.started = False
        self.game_config = None
        self.chat = ChatBox(screen, y=height - 110, width=min(400, width - 40))
        self.dialogue = NPCDialogue(screen, width, height)

        from core.config_loader import load_config, get_seasons_config
        cfg = load_config()
        lobby_cfg = cfg.get("lobby", {})
        world_w = lobby_cfg.get("world_width", 2048)
        self.plaza = Plaza(width, height, world_w)
        self.plaza.add_player(0, "主机", 150)
        self.npcs = _create_npcs(cfg, world_w)
        for npc in self.npcs:
            npc.y = self.plaza.ground_y - 90
        self.selected_npc = None

        season_cfg = get_seasons_config()
        self.season_enabled = season_cfg.get("enabled", True)
        self.current_season = season_cfg.get("current", "spring")
        self.cycle_seconds = season_cfg.get("cycle_seconds", 60)
        self.season_start_time = time.time()
        self.particles = []

    def _update_season(self):
        if not self.season_enabled:
            return
        elapsed = time.time() - self.season_start_time
        idx = int(elapsed / self.cycle_seconds) % len(SEASON_ORDER)
        self.current_season = SEASON_ORDER[idx]

    def _spawn_particles(self, season: str):
        import random
        if len(self.particles) < 15:
            cfg = get_season_config(season)
            c = cfg.get("particle_color", (255, 255, 255))
            self.particles.append({
                "x": random.randint(0, self.plaza.world_width),
                "y": -10,
                "vy": random.uniform(0.5, 2),
                "color": c,
                "size": random.randint(2, 6),
            })
        for p in self.particles[:]:
            p["y"] += p["vy"]
            if p["y"] > self.height + 20:
                self.particles.remove(p)

    def run(self):
        while not self.started:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                msg = self.dialogue.handle_event(event)
                if msg is not None:
                    if msg and self.selected_npc:
                        self.dialogue.set_loading(True)
                        def on_reply(r): self.dialogue.set_reply(r)
                        self.selected_npc.talk(msg, on_reply)
                    continue

                if self.dialogue.visible:
                    continue

                chat_msg = self.chat.handle_event(event)
                if chat_msg:
                    if self.is_host and self.server:
                        self.server.broadcast_chat("主机", chat_msg)
                    elif self.client:
                        self.client.send_chat(chat_msg)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    world_mx = mx + self.plaza.camera_x
                    for npc in self.npcs:
                        sx = npc.x - self.plaza.camera_x
                        if (sx <= mx <= sx + npc.width and
                                npc.y <= my <= npc.y + npc.height):
                            self.selected_npc = npc
                            self.dialogue.show(npc.name, "输入消息后按 Enter。")
                            break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.is_host:
                        return None
                    if event.key == pygame.K_r and not self.chat.input_active:
                        self.ready = not self.ready
                        if self.client:
                            self.client.send_ready(self.ready)
                    if (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE) and not self.chat.input_active:
                        if self.is_host and self.server:
                            self.started = True
                            self.game_config = {
                                "player_count": min(1 + self.server.player_count(), 8),
                                "skins": [0, 1, 2, 3, 4, 5][:8],
                            }
                            self.server.broadcast_game_start(self.game_config)

            if self.dialogue.visible and self.selected_npc:
                if self.selected_npc.is_loading():
                    self.dialogue.set_loading(True)
                else:
                    r = self.selected_npc.get_reply()
                    if r:
                        self.dialogue.set_reply(r)
                        self.selected_npc.clear_reply()

            self._update_season()
            self._spawn_particles(self.current_season)

            if self.is_host and self.server:
                keys = pygame.key.get_pressed()
                self.plaza.update_player(0, keys[pygame.K_a], keys[pygame.K_d],
                                         keys[pygame.K_w] or keys[pygame.K_SPACE])
                for i in range(self.server.player_count()):
                    inp = self.server.get_input(i)
                    pid = i + 1
                    if pid not in self.plaza.players:
                        self.plaza.add_player(pid, f"P{pid + 1}", 200 + pid * 100)
                    self.plaza.update_player(pid, inp.get("left"), inp.get("right"), inp.get("jump"))

                lobby_state = self.server.get_lobby_state()
                lobby_state["plaza_positions"] = self.plaza.get_positions()
                lobby_state["season"] = self.current_season
                self.server.broadcast_lobby(lobby_state)
                self.chat.set_messages(self.server.get_chat_messages())
            elif self.client:
                keys = pygame.key.get_pressed()
                self.client.send_input({
                    "left": 1 if keys[pygame.K_LEFT] else 0,
                    "right": 1 if keys[pygame.K_RIGHT] else 0,
                    "jump": 1 if keys[pygame.K_UP] or keys[pygame.K_SPACE] else 0,
                    "shoot": 0,
                })
                lobby = self.client.get_lobby()
                if lobby:
                    pos = lobby.get("plaza_positions", {})
                    for pid, ppos in pos.items():
                        if pid not in self.plaza.players:
                            name = "主机" if pid == 0 else f"P{pid+1}"
                            self.plaza.add_player(pid, name, ppos.get("x", 150))
                    self.plaza.apply_positions(pos)
                    if lobby.get("season"):
                        self.current_season = lobby["season"]
                    my_id = getattr(self.client, "player_id", 0) + 1
                    if my_id in self.plaza.players:
                        p = self.plaza.players[my_id]
                        self.plaza.camera_x = p.x - self.width // 2 + p.width // 2
                        self.plaza.camera_x = max(0, min(self.plaza.world_width - self.width, self.plaza.camera_x))
                self.chat.set_messages(self.client.get_chat_messages())
                if self.client.game_started:
                    self.started = True
                    self.game_config = self.client.game_config or {}

            self.draw()
            pygame.display.flip()

        return self.game_config

    def draw(self):
        season = get_season_config(self.current_season)
        for y in range(self.height):
            t = y / self.height
            r = int(season["sky_top"][0] * (1 - t) + season["sky_bottom"][0] * t)
            g = int(season["sky_top"][1] * (1 - t) + season["sky_bottom"][1] * t)
            b = int(season["sky_top"][2] * (1 - t) + season["sky_bottom"][2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

        cam = self.plaza.camera_x
        for (px, py, pw, ph) in self.plaza.platforms:
            sx = px - cam
            if -pw < sx < self.width + 50:
                pygame.draw.rect(self.screen, season["ground"], (sx, py, pw, ph))
                pygame.draw.rect(self.screen, season["ground_accent"], (sx, py, pw, ph), 2)

        for p in self.particles:
            sx = p["x"] - cam
            if 0 <= sx <= self.width:
                pygame.draw.circle(self.screen, p["color"], (int(sx), int(p["y"])), p["size"])

        for npc in self.npcs:
            sx = npc.x - cam
            if -100 < sx < self.width + 100:
                pygame.draw.rect(self.screen, (60, 80, 120), (sx, npc.y, npc.width, npc.height))
                pygame.draw.rect(self.screen, YELLOW, (sx, npc.y, npc.width, npc.height), 2)
                t = self.font.render(npc.name, True, WHITE)
                self.screen.blit(t, (sx + (npc.width - t.get_width()) // 2, npc.y + 30))

        for pid, p in sorted(self.plaza.players.items()):
            sx = p.x - cam
            if -50 < sx < self.width + 50:
                pygame.draw.rect(self.screen, (34, 139, 34) if pid == 0 else (0, 150, 150),
                                 (sx, p.y, p.width, p.height))
                pygame.draw.rect(self.screen, (255, 220, 180), (sx + 8, p.y + 6, 20, 18))
                label = self.font.render("主机" if pid == 0 else f"P{pid+1}", True, WHITE)
                self.screen.blit(label, (sx, p.y - 20))

        overlay = pygame.Surface((self.width, 75))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        season_name = season["name"]
        title = self.big_font.render(f"广场 · {season_name}", True, YELLOW)
        self.screen.blit(title, (20, 12))

        if self.is_host and self.server:
            code = self.server.room_code
            ip = self.server.get_local_ip()
            info = self.font.render(f"{code} | {ip}:25565", True, WHITE)
            self.screen.blit(info, (20, 48))
            for i, p in enumerate(self.server.get_lobby_state().get("players", [])):
                st = "✓" if p.get("ready") else "○"
                c = GREEN if p.get("ready") else GRAY
                t = self.font.render(f"{p.get('name','')}{st}", True, c)
                self.screen.blit(t, (self.width - 180 + i * 60, 48))
        else:
            lobby = self.client.get_lobby()
            if lobby:
                t = self.font.render(f"房间 {lobby.get('room_code','')}", True, WHITE)
                self.screen.blit(t, (20, 48))
            st = "✓" if self.ready else "○"
            t = self.font.render(f"你{st} R切换", True, GREEN if self.ready else GRAY)
            self.screen.blit(t, (self.width - 120, 48))

        hint = self.font.render("WASD/方向键 移动  Enter开始  ESC退出", True, GRAY)
        self.screen.blit(hint, (self.width // 2 - 180, 48))

        self.chat.draw()
        self.dialogue.draw()
