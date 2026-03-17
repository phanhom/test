"""房间大厅 - 等待玩家、准备、开始"""

import pygame
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WHITE, GRAY, YELLOW, GREEN


class Lobby:
    """大厅界面"""
    def __init__(self, screen, is_host: bool, server=None, client=None):
        self.screen = screen
        self.is_host = is_host
        self.server = server
        self.client = client
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 56)
        self.ready = False
        self.started = False
        self.game_config = None

    def run(self):
        """运行大厅，返回 (started, game_config) 或 None"""
        while not self.started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.is_host:
                        return None
                    if event.key == pygame.K_r:
                        self.ready = not self.ready
                        if self.client:
                            self.client.send_ready(self.ready)
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.is_host and self.server:
                            # 主机开始游戏
                            player_count = 1 + self.server.player_count()
                            self.started = True
                            self.game_config = {
                                "player_count": min(player_count, 4),
                                "skins": [0, 1, 2, 3][:player_count],
                            }
                            self.server.broadcast_game_start(self.game_config)

            if self.is_host and self.server:
                lobby_state = self.server.get_lobby_state()
                self.server.broadcast_lobby(lobby_state)
            elif self.client:
                lobby = self.client.get_lobby()
                if lobby:
                    pass  # 用于显示
                if self.client.game_started:
                    self.started = True
                    self.game_config = self.client.game_config or {}

            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        return self.game_config

    def draw(self):
        self.screen.fill((30, 50, 80))
        title = self.big_font.render("房间大厅", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 80, 60))

        if self.is_host and self.server:
            code = self.server.room_code
            ip = self.server.get_local_ip()
            code_text = self.font.render(f"房间码: {code}  |  IP: {ip}:25565", True, WHITE)
            self.screen.blit(code_text, (SCREEN_WIDTH // 2 - 150, 130))

            lobby_state = self.server.get_lobby_state()
            players = [{"name": "主机 (你)", "ready": True}]
            players.extend(lobby_state.get("players", []))

            for i, p in enumerate(players):
                status = "已准备" if p["ready"] else "未准备"
                color = GREEN if p["ready"] else GRAY
                text = self.font.render(f"  {p['name']} - {status}", True, color)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 120, 180 + i * 40))

            hint = self.font.render("按 Enter 开始游戏", True, WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - 100, 350))
        else:
            lobby = self.client.get_lobby() if self.client else None
            if lobby:
                code_text = self.font.render(f"房间: {lobby.get('room_code', '')}", True, WHITE)
                self.screen.blit(code_text, (SCREEN_WIDTH // 2 - 80, 130))
                for i, p in enumerate(lobby.get("players", [])):
                    status = "已准备" if p.get("ready") else "未准备"
                    color = GREEN if p.get("ready") else GRAY
                    text = self.font.render(f"  {p.get('name', '')} - {status}", True, color)
                    self.screen.blit(text, (SCREEN_WIDTH // 2 - 120, 180 + i * 40))
            else:
                wait_text = self.font.render("等待主机...", True, GRAY)
                self.screen.blit(wait_text, (SCREEN_WIDTH // 2 - 80, 200))

            status = "已准备" if self.ready else "未准备"
            self.screen.blit(self.font.render(f"你: {status}  (R 切换)", True, WHITE), (SCREEN_WIDTH // 2 - 100, 350))
