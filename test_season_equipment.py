#!/usr/bin/env python3
"""
测试季节装备系统
"""

import pygame
import sys

# 初始化pygame
pygame.init()

# 测试导入
try:
    from core.seasons import get_season_equipment, SEASONS, SEASON_ORDER
    from game.entities import Player
    print("✓ 模块导入成功")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 测试季节装备配置
print("\n=== 测试季节装备配置 ===")
for season in SEASON_ORDER:
    equipment = get_season_equipment(season)
    print(f"\n{season} 季节装备:")
    print(f"  身体颜色: {equipment['body']}")
    print(f"  枪械颜色: {equipment['gun']}")
    print(f"  装饰颜色: {equipment['accessory']}")

# 测试玩家实体
print("\n=== 测试玩家实体 ===")
screen = pygame.display.set_mode((800, 500))
pygame.display.set_caption("季节装备测试")

# 创建不同季节的玩家
players = []
for i, season in enumerate(SEASON_ORDER):
    player = Player(100 + i * 150, 300, player_id=i, skin_id=0, season=season)
    players.append(player)
    print(f"✓ 创建 {season} 季节玩家 {i+1}")

# 测试季节切换
print("\n=== 测试季节切换 ===")
test_player = Player(400, 300, player_id=0, skin_id=0, season="spring")
print(f"初始季节: {test_player.season}")

test_player.set_season("summer")
print(f"切换后季节: {test_player.season}")

# 简单的可视化测试
print("\n=== 可视化测试 ===")
print("按 ESC 退出，按 SPACE 切换季节")

current_season_idx = 0
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                current_season_idx = (current_season_idx + 1) % len(SEASON_ORDER)
                new_season = SEASON_ORDER[current_season_idx]
                for player in players:
                    player.set_season(new_season)
                print(f"切换到 {new_season} 季节")

    # 绘制
    screen.fill((135, 206, 235))  # 天空蓝背景
    
    # 绘制地面
    pygame.draw.rect(screen, (34, 139, 34), (0, 400, 800, 100))
    
    # 绘制玩家
    for i, player in enumerate(players):
        player.rect.x = 100 + i * 150
        player.rect.y = 350
        player.draw(screen)
        
        # 绘制季节标签
        font = pygame.font.Font(None, 24)
        season_name = SEASONS[SEASON_ORDER[i]]["name"]
        label = font.render(f"{season_name}", True, (255, 255, 255))
        screen.blit(label, (player.rect.x, player.rect.y - 30))

    # 绘制提示
    font = pygame.font.Font(None, 24)
    hint = font.render("按 SPACE 切换季节 | 按 ESC 退出", True, (255, 255, 255))
    screen.blit(hint, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
print("\n✓ 测试完成")
