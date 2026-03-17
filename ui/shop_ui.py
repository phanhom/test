"""商店界面"""

import pygame
from game.skins import SKINS
from core.save_data import get_coins, get_owned_skins, purchase_skin
from core.shop import get_shop_items

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 215, 0)
GREEN = (50, 180, 80)


class ShopUI:
    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height
        self.visible = False
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 48)
        self.selected = 0
        self.items = []
        self._refresh()

    def _refresh(self):
        self.items = get_shop_items()

    def show(self):
        self.visible = True
        self._refresh()
        self.selected = 0

    def hide(self):
        self.visible = False

    def handle_event(self, event) -> bool:
        """处理事件，返回是否消费了事件"""
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True
            if event.key == pygame.K_LEFT:
                self.selected = max(0, self.selected - 1)
                return True
            if event.key == pygame.K_RIGHT:
                self.selected = min(len(self.items) - 1, self.selected + 1)
                return True
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._try_buy()
                return True
        return False

    def _try_buy(self):
        if not self.items:
            return
        it = self.items[self.selected]
        if it["owned"]:
            return
        if purchase_skin(it["skin_id"], it["price"]):
            self._refresh()

    def draw(self):
        if not self.visible:
            return
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 500, 380
        px = (self.width - panel_w) // 2
        py = (self.height - panel_h) // 2
        pygame.draw.rect(self.screen, (40, 50, 70), (px, py, panel_w, panel_h))
        pygame.draw.rect(self.screen, YELLOW, (px, py, panel_w, panel_h), 3)

        title = self.title_font.render("军需商店", True, YELLOW)
        self.screen.blit(title, (px + (panel_w - title.get_width()) // 2, py + 15))

        coins = get_coins()
        coin_text = self.font.render(f"金币: {coins}", True, YELLOW)
        self.screen.blit(coin_text, (px + panel_w - 120, py + 25))

        if not self.items:
            self.screen.blit(self.font.render("暂无商品", True, GRAY), (px + 180, py + 150))
            hint = self.font.render("ESC 关闭", True, GRAY)
            self.screen.blit(hint, (px + panel_w - 100, py + panel_h - 35))
            return

        it = self.items[self.selected]
        cx = px + panel_w // 2
        cy = py + 140

        pygame.draw.rect(self.screen, it["body"], (cx - 35, cy - 50, 70, 60))
        pygame.draw.rect(self.screen, (255, 220, 180), (cx - 25, cy - 45, 20, 18))
        pygame.draw.rect(self.screen, it["gun"], (cx + 15, cy - 25, 25, 8))

        name_text = self.font.render(it["name"], True, WHITE)
        self.screen.blit(name_text, (cx - name_text.get_width() // 2, cy + 25))

        if it["owned"]:
            status = self.font.render("已拥有", True, GREEN)
        else:
            status = self.font.render(f"价格: {it['price']} 金币", True, YELLOW)
        self.screen.blit(status, (cx - status.get_width() // 2, cy + 55))

        nav = f"  [{self.selected + 1}/{len(self.items)}]  "
        nav_text = self.font.render(nav, True, GRAY)
        self.screen.blit(nav_text, (cx - nav_text.get_width() // 2, cy + 90))

        hint = self.font.render("← → 选择  Enter 购买  ESC 关闭", True, GRAY)
        self.screen.blit(hint, (px + (panel_w - hint.get_width()) // 2, py + panel_h - 35))
