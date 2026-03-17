"""房间大厅 - 更大布局、NPC 对话、聊天"""

import pygame
from game.constants import WHITE, GRAY, YELLOW, GREEN
from ui.chat import ChatBox
from ui.npc_dialogue import NPCDialogue


def _create_npcs(config: dict):
    """从 config 创建 NPC 列表"""
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
    for item in npc_config.get("list", []):
        npc = NPCEntity(
            npc_id=item.get("id", "npc"),
            name=item.get("name", "NPC"),
            role=item.get("role", ""),
            prompt=item.get("prompt", "你是一个NPC。"),
            x=item.get("x", 100),
            y=item.get("y", 400),
            llm_client=llm,
        )
        npcs.append(npc)
    return npcs


class Lobby:
    """大厅界面 - 支持更大布局和 NPC"""
    def __init__(self, screen, is_host: bool, server=None, client=None, width: int = 1024, height: int = 640):
        self.screen = screen
        self.width = width
        self.height = height
        self.is_host = is_host
        self.server = server
        self.client = client
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 64)
        self.ready = False
        self.started = False
        self.game_config = None
        self.chat = ChatBox(screen, y=height - 130, width=min(450, width - 40))
        self.dialogue = NPCDialogue(screen, width, height)

        from core.config_loader import load_config
        cfg = load_config()
        self.npcs = _create_npcs(cfg)
        self.selected_npc = None

    def run(self):
        while not self.started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                msg = self.dialogue.handle_event(event)
                if msg is not None:
                    if msg and self.selected_npc:
                        self.dialogue.set_loading(True)

                        def on_reply(reply: str):
                            self.dialogue.set_reply(reply)

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
                    for npc in self.npcs:
                        if npc.contains_point(*event.pos):
                            self.selected_npc = npc
                            self.dialogue.show(npc.name, "输入消息后按 Enter，我会用大模型回复。")
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
                            player_count = 1 + self.server.player_count()
                            self.started = True
                            self.game_config = {
                                "player_count": min(player_count, 8),
                                "skins": [0, 1, 2, 3, 4, 5][:player_count],
                            }
                            self.server.broadcast_game_start(self.game_config)

            if self.dialogue.visible and self.selected_npc and self.selected_npc.is_loading():
                self.dialogue.set_loading(True)
            elif self.dialogue.visible and self.selected_npc:
                reply = self.selected_npc.get_reply()
                if reply:
                    self.dialogue.set_reply(reply)
                    self.selected_npc.clear_reply()

            if self.is_host and self.server:
                lobby_state = self.server.get_lobby_state()
                self.server.broadcast_lobby(lobby_state)
                self.chat.set_messages(self.server.get_chat_messages())
            elif self.client:
                self.chat.set_messages(self.client.get_chat_messages())
                if self.client.game_started:
                    self.started = True
                    self.game_config = self.client.game_config or {}

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        return self.game_config

    def draw(self):
        self.screen.fill((25, 40, 65))
        title = self.big_font.render("房间大厅", True, YELLOW)
        self.screen.blit(title, (self.width // 2 - 100, 40))

        if self.is_host and self.server:
            code = self.server.room_code
            ip = self.server.get_local_ip()
            code_text = self.font.render(f"房间码: {code}  |  IP: {ip}:25565", True, WHITE)
            self.screen.blit(code_text, (self.width // 2 - 180, 110))

            lobby_state = self.server.get_lobby_state()
            players = [{"name": "主机 (你)", "ready": True}]
            players.extend(lobby_state.get("players", []))

            for i, p in enumerate(players):
                status = "已准备" if p["ready"] else "未准备"
                color = GREEN if p["ready"] else GRAY
                text = self.font.render(f"  {p['name']} - {status}", True, color)
                self.screen.blit(text, (self.width // 2 - 150, 160 + i * 38))

            hint = self.font.render("Enter 开始  |  点击 NPC 对话  |  下方聊天", True, WHITE)
            self.screen.blit(hint, (self.width // 2 - 200, 280))
        else:
            lobby = self.client.get_lobby() if self.client else None
            if lobby:
                code_text = self.font.render(f"房间: {lobby.get('room_code', '')}", True, WHITE)
                self.screen.blit(code_text, (self.width // 2 - 100, 110))
                for i, p in enumerate(lobby.get("players", [])):
                    status = "已准备" if p.get("ready") else "未准备"
                    color = GREEN if p.get("ready") else GRAY
                    text = self.font.render(f"  {p.get('name', '')} - {status}", True, color)
                    self.screen.blit(text, (self.width // 2 - 150, 160 + i * 38))
            else:
                wait_text = self.font.render("等待主机...", True, GRAY)
                self.screen.blit(wait_text, (self.width // 2 - 80, 200))

            status = "已准备" if self.ready else "未准备"
            self.screen.blit(
                self.font.render(f"你: {status}  (R 切换)  |  点击 NPC 对话", True, WHITE),
                (self.width // 2 - 180, 280),
            )

        for npc in self.npcs:
            self._draw_npc(npc)

        self.chat.draw()
        self.dialogue.draw()

    def _draw_npc(self, npc):
        """绘制 NPC 头像"""
        pygame.draw.rect(self.screen, (60, 80, 120), (npc.x, npc.y, npc.width, npc.height))
        pygame.draw.rect(self.screen, YELLOW, (npc.x, npc.y, npc.width, npc.height), 2)
        name_text = self.font.render(npc.name, True, WHITE)
        self.screen.blit(name_text, (npc.x + (npc.width - name_text.get_width()) // 2, npc.y + 35))
        role_text = pygame.font.Font(None, 22).render(npc.role, True, GRAY)
        self.screen.blit(role_text, (npc.x + (npc.width - role_text.get_width()) // 2, npc.y + 65))
