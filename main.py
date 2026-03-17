#!/usr/bin/env python3
"""
合金弹头 - 主入口
支持: 单人、开房间多人、地图系统、皮肤、NPC、Lobby
"""

import pygame
import sys

from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, PORT
from game.game_logic import Game
from ui.menu import Menu
from ui.lobby import Lobby
from network.room_server import RoomServer
from network.room_client import RoomClient
from core.config_loader import get_lobby_config, get_game_config


def main():
    pygame.init()
    pygame.mixer.init()

    lobby_cfg = get_lobby_config()
    game_cfg = get_game_config()
    lobby_w = lobby_cfg.get("width", 1024)
    lobby_h = lobby_cfg.get("height", 640)
    game_w = game_cfg.get("width", 800)
    game_h = game_cfg.get("height", 500)

    screen = pygame.display.set_mode((lobby_w, lobby_h), pygame.RESIZABLE)
    pygame.display.set_caption("合金弹头 - Metal Slug")

    menu = Menu(screen)
    result = menu.run()

    if result == "quit":
        pygame.quit()
        sys.exit(0)

    mode = result[0]
    if mode == "join":
        host = result[1]
        skins = result[2] if len(result) > 2 else [0, 1]
    else:
        skins = result[1] if len(result) > 1 else [0, 1]
    if len(skins) == 1:
        skins = [skins[0], 1]

    game = None
    server = None
    client = None

    if mode == "single":
        pygame.display.set_mode((game_w, game_h), pygame.RESIZABLE)
        game = Game(screen, player_skins=skins)

    elif mode == "host":
        server = RoomServer(PORT)
        if not server.start():
            print("无法启动服务器，端口可能被占用")
            pygame.quit()
            sys.exit(1)
        print(f"房间码: {server.room_code}  |  IP: {server.get_local_ip()}:{PORT}")

        lobby = Lobby(screen, is_host=True, server=server, width=lobby_w, height=lobby_h)
        game_config = lobby.run()
        if game_config is None:
            server.stop()
            pygame.quit()
            sys.exit(0)

        player_count = min(game_config.get("player_count", 2), 2)  # 暂支持最多2人
        config_skins = game_config.get("skins", skins)[:2]
        game = Game(
            screen,
            is_host=True,
            player_skins=config_skins,
            network=server,
        )
        game.player_count = player_count
        game._init_players()

    elif mode == "join":
        client = RoomClient(host, PORT)
        if not client.connect():
            print("无法连接，请检查 IP 和网络")
            pygame.quit()
            sys.exit(1)

        lobby = Lobby(screen, is_host=False, client=client, width=lobby_w, height=lobby_h)
        game_config = lobby.run()
        if game_config is None:
            client.disconnect()
            pygame.quit()
            sys.exit(0)

        player_count = min(game_config.get("player_count", 2), 2)
        config_skins = game_config.get("skins", skins)[:2]
        game = Game(
            screen,
            is_client=True,
            player_skins=config_skins,
            network=client,
        )
        game.player_count = player_count
        game._init_players()

    if game:
        if mode != "single":
            pygame.display.set_mode((game_w, game_h), pygame.RESIZABLE)
        game.run()

    if server:
        server.stop()
    if client:
        client.disconnect()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
