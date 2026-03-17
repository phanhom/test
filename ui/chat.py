"""聊天组件 - 大厅和游戏中复用"""

import pygame
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRAY, BLACK

MAX_MESSAGES = 8
MAX_LENGTH = 40
CHAT_HEIGHT = 120
INPUT_HEIGHT = 28


class ChatBox:
    def __init__(self, screen, x=10, y=None, width=380, height=CHAT_HEIGHT):
        self.screen = screen
        self.x = x
        self.y = y or (SCREEN_HEIGHT - height - 10)
        self.width = width
        self.height = height
        self.font = pygame.font.Font(None, 24)
        self.messages: list[tuple[str, str]] = []  # (sender, text)
        self.input_text = ""
        self.input_active = False
        self.input_rect = pygame.Rect(self.x, self.y + self.height - INPUT_HEIGHT - 4, self.width - 8, INPUT_HEIGHT - 4)

    def add_message(self, sender: str, text: str):
        if len(text) > MAX_LENGTH:
            text = text[:MAX_LENGTH - 3] + "..."
        self.messages.append((sender, text))
        if len(self.messages) > MAX_MESSAGES:
            self.messages.pop(0)

    def set_messages(self, msgs: list[tuple[str, str]]):
        self.messages = msgs[-MAX_MESSAGES:]

    def handle_event(self, event) -> str | None:
        """处理事件，Enter 发送时返回消息内容，否则返回 None"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.input_active = self.input_rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                msg = self.input_text.strip()
                self.input_text = ""
                return msg if msg else None
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isprintable() and len(self.input_text) < MAX_LENGTH:
                self.input_text += event.unicode
        return None

    def draw(self):
        # 背景
        surf = pygame.Surface((self.width, self.height))
        surf.set_alpha(200)
        surf.fill(BLACK)
        self.screen.blit(surf, (self.x, self.y))
        pygame.draw.rect(self.screen, GRAY, (self.x, self.y, self.width, self.height), 2)

        # 消息列表
        for i, (sender, text) in enumerate(self.messages[-MAX_MESSAGES:]):
            line = self.font.render(f"{sender}: {text}", True, WHITE)
            self.screen.blit(line, (self.x + 6, self.y + 4 + i * 22))

        # 输入框
        pygame.draw.rect(self.screen, (60, 60, 80) if self.input_active else (40, 40, 60), self.input_rect)
        pygame.draw.rect(self.screen, WHITE if self.input_active else GRAY, self.input_rect, 2)
        prompt = "> " + self.input_text + ("_" if self.input_active else "")
        inp_text = self.font.render(prompt, True, WHITE)
        self.screen.blit(inp_text, (self.input_rect.x + 4, self.input_rect.y + 4))
