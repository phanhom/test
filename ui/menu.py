"""主菜单"""

import pygame
from game.constants import FPS, WHITE, GRAY, YELLOW
from game.skins import SKINS
from core.save_data import get_coins, get_owned_skins


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.title_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 28)
        self.selected = 0
        self.options = ["单人游戏", "创建房间", "加入房间"]
        self.ip_input = ""
        self.input_mode = False
        self.skin_p1 = 0
        self.skin_p2 = 1
        self.map_index = 0

    def run(self):
        running = True
        result = None

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if self.input_mode:
                        if event.key == pygame.K_RETURN:
                            self.input_mode = False
                            if self.selected == 2 and self.ip_input:
                                result = ("join", self.ip_input, [self.skin_p1, self.skin_p2])
                                running = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.ip_input = self.ip_input[:-1]
                        elif event.unicode.isdigit() or event.unicode == ".":
                            self.ip_input += event.unicode
                    else:
                        if event.key == pygame.K_UP:
                            self.selected = (self.selected - 1) % len(self.options)
                        elif event.key == pygame.K_DOWN:
                            self.selected = (self.selected + 1) % len(self.options)
                        elif event.key == pygame.K_LEFT:
                            owned = get_owned_skins() or [0]
                            if self.selected == 0:
                                idx = owned.index(self.skin_p1) if self.skin_p1 in owned else 0
                                self.skin_p1 = owned[(idx - 1) % len(owned)]
                            elif self.selected in (1, 2):
                                idx = owned.index(self.skin_p2) if self.skin_p2 in owned else 0
                                self.skin_p2 = owned[(idx - 1) % len(owned)]
                        elif event.key == pygame.K_RIGHT:
                            owned = get_owned_skins() or [0]
                            if self.selected == 0:
                                idx = owned.index(self.skin_p1) if self.skin_p1 in owned else 0
                                self.skin_p1 = owned[(idx + 1) % len(owned)]
                            elif self.selected in (1, 2):
                                idx = owned.index(self.skin_p2) if self.skin_p2 in owned else 0
                                self.skin_p2 = owned[(idx + 1) % len(owned)]
                        elif event.key == pygame.K_RETURN:
                            if self.selected == 0:
                                result = ("single", [self.skin_p1])
                                running = False
                            elif self.selected == 1:
                                result = ("host", [self.skin_p1, self.skin_p2])
                                running = False
                            elif self.selected == 2:
                                self.input_mode = True
                                self.ip_input = ""

            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        return result

    def draw(self):
        self.screen.fill((30, 50, 80))
        title = self.title_font.render("合金弹头", True, YELLOW)
        self.screen.blit(title, (self.width // 2 - 100, 80))

        for i, opt in enumerate(self.options):
            color = WHITE if i == self.selected else GRAY
            text = self.font.render(f"> {opt} <" if i == self.selected else opt, True, color)
            self.screen.blit(text, (self.width // 2 - 120, 200 + i * 60))

        skin_p1_name = SKINS[self.skin_p1]["name"]
        skin_p2_name = SKINS[self.skin_p2]["name"]
        skin_text = self.small_font.render(
            f"P1: {skin_p1_name}  |  P2: {skin_p2_name}  (←→切换)", True, GRAY
        )
        self.screen.blit(skin_text, (self.width // 2 - 180, 380))
        coins = get_coins()
        coin_text = self.small_font.render(f"金币: {coins} (游戏得分兑换)", True, YELLOW)
        self.screen.blit(coin_text, (self.width // 2 - 120, 420))

        if self.input_mode:
            hint = self.small_font.render("输入主机 IP:", True, WHITE)
            self.screen.blit(hint, (self.width // 2 - 180, 400))
            pygame.draw.rect(self.screen, WHITE, (self.width // 2 - 150, 430, 300, 35), 2)
            ip_text = self.font.render(self.ip_input or "_", True, WHITE)
            self.screen.blit(ip_text, (self.width // 2 - 140, 432))

        ctrl = self.small_font.render("↑↓选择  Enter确认  ←→切换皮肤", True, GRAY)
        self.screen.blit(ctrl, (self.width // 2 - 150, self.height - 30))
