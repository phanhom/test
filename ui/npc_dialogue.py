"""NPC 对话面板"""

import pygame
from typing import Optional

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 215, 0)


class NPCDialogue:
    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height
        self.x = (width - 400) // 2
        self.y = (height - 200) // 2
        self.panel_w = 400
        self.panel_h = 200
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 36)
        self.input_text = ""
        self.input_active = True
        self.input_rect = pygame.Rect(self.x + 20, self.y + self.panel_h - 50, self.panel_w - 40, 35)
        self.message = ""
        self.npc_name = ""
        self.visible = False
        self.loading = False

    def show(self, npc_name: str, initial_msg: str = ""):
        self.npc_name = npc_name
        self.message = initial_msg
        self.input_text = ""
        self.visible = True
        self.loading = False

    def hide(self):
        self.visible = False

    def set_reply(self, text: str):
        self.message = text
        self.loading = False

    def set_loading(self, loading: bool):
        self.loading = loading

    def handle_event(self, event) -> Optional[str]:
        """返回待发送的消息，或 None"""
        if not self.visible:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.input_active = self.input_rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                msg = self.input_text.strip()
                self.input_text = ""
                return msg if msg else None
            elif event.key == pygame.K_ESCAPE:
                self.hide()
                return None
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isprintable() and len(self.input_text) < 60:
                self.input_text += event.unicode
        return None

    def draw(self):
        if not self.visible:
            return
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (40, 50, 70), (self.x, self.y, self.panel_w, self.panel_h))
        pygame.draw.rect(self.screen, YELLOW, (self.x, self.y, self.panel_w, self.panel_h), 2)

        title = self.title_font.render(f"{self.npc_name}", True, YELLOW)
        self.screen.blit(title, (self.x + 20, self.y + 15))

        if self.loading:
            msg = self.font.render("思考中...", True, GRAY)
        else:
            msg = self.font.render(self.message or "点击输入框，输入后按 Enter 发送", True, WHITE)
        self.screen.blit(msg, (self.x + 20, self.y + 55))

        pygame.draw.rect(self.screen, (60, 60, 80), self.input_rect)
        pygame.draw.rect(self.screen, WHITE if self.input_active else GRAY, self.input_rect, 2)
        inp = self.font.render("> " + self.input_text + ("_" if self.input_active else ""), True, WHITE)
        self.screen.blit(inp, (self.input_rect.x + 5, self.input_rect.y + 5))

        hint = self.font.render("Enter 发送  ESC 关闭", True, GRAY)
        self.screen.blit(hint, (self.x + self.panel_w - 150, self.y + self.panel_h - 25))
