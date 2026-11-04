import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import tempfile
import socket
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import pygame
from main import App
from scripts.game_instance import GameInstance
from scripts.worm import Worm, load_sprite
from scripts.network import Network
from server import GameServer


class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.app = App()
        game = GameInstance(0)
        game.add_player()
        self.app.game_instance = SimpleNamespace(**game.snapshot())
        self.app.player_id = 0
        self.app.vrt_space.update()
        pygame.event.clear()

    def tearDown(self):
        self.app.close()

    def test_sprites_shared_between_players(self):
        load_sprite.cache_clear()
        with patch("pygame.image.load", wraps=pygame.image.load) as load:
            a = Worm(0, 32, (5, 5))
            b = Worm(1, 32, (5, 25))
        self.assertEqual(load.call_count, 14)
        self.assertIs(a.head_up, b.head_up)

    def test_original_board_colors_and_no_trails(self):
        self.app.renderer.render()
        surface = self.app.window.app_window
        self.assertEqual(tuple(surface.get_at((1, 1)))[:3], (30, 30, 30))
        self.assertEqual(tuple(surface.get_at((33, 1)))[:3], (0, 0, 0))
        self.app.vrt_space.worms[0].body = []
        self.app.renderer.render()
        self.assertEqual(tuple(surface.get_at((5 * 32 + 16, 5 * 32 + 16)))[:3], (30, 30, 30))

    def test_unchanged_state_reuses_blocks(self):
        body = self.app.vrt_space.worms[0].body
        self.app.vrt_space.update()
        self.assertIs(self.app.vrt_space.worms[0].body, body)

    def test_arrow_and_wasd_keys(self):
        for key, expected in ((pygame.K_UP, (0, -1)), (pygame.K_DOWN, (0, 1)),
                              (pygame.K_LEFT, (-1, 0)), (pygame.K_RIGHT, (1, 0)),
                              (pygame.K_w, (0, -1)), (pygame.K_a, (-1, 0))):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.app.input.update()
            self.assertEqual(self.app.input.direction, expected)
            self.app.input.update()
            self.assertIsNone(self.app.input.direction)

    def test_unrelated_key_does_not_retrigger_ready(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.app.input.update()
        self.assertTrue(self.app.input.keyboard_variables["ready"])
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w))
        self.app.input.update()
        self.assertFalse(self.app.input.keyboard_variables["ready"])

    def test_menu_quit_returns_without_connecting(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.app.menu())
        self.assertIsNone(self.app.n)

    def test_in_game_quit_does_not_send_request(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        with patch.object(self.app, "n") as network:
            self.assertFalse(self.app.update())
            network.send.assert_not_called()

    def test_assets_work_from_another_directory(self):
        previous = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                app = App()
                self.assertEqual(len(app.vrt_space.worms), 4)
        finally:
            os.chdir(previous)

    def test_scaled_display_uses_full_surface(self):
        window = self.app.window
        window.scaled_resolution = (480, 320)
        window.window = pygame.display.set_mode(window.scaled_resolution)
        window.app_window.fill((20, 40, 60))
        window.render_screen()
        self.assertEqual(tuple(window.window.get_at((479, 319)))[:3], (20, 40, 60))

    def test_full_client_loop_with_second_player(self):
        server = GameServer()
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        threads = []
        peer = None

        def accept():
            connection, address = listener.accept()
            server.handle_client(connection, address)

        def start_connection():
            thread = threading.Thread(target=accept, daemon=True)
            thread.start()
            threads.append(thread)

        try:
            port = listener.getsockname()[1]
            start_connection()
            self.app.web_init(port=port)
            start_connection()
            peer = Network(self.app, port=port)
            self.app.update()
            self.assertEqual(self.app.game_instance.active_players, 2)
            now = [0.0]
            server.games[0].clock = lambda: now[0]
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            self.app.update()
            self.assertTrue(self.app.game_instance.started)
            now[0] = 0.25
            self.app.update()
            self.assertEqual(self.app.game_instance.worms[0][0], [6, 5])
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP))
            self.app.update()
            now[0] = 0.5
            self.app.update()
            state = peer.send()
            self.assertEqual(state.worms, self.app.game_instance.worms)
            head = self.app.vrt_space.worms[0].body[0]
            self.assertEqual((head.x, head.y), (6, 4))
            peer.close()
            threads[1].join(timeout=2)
            self.app.update()
            self.assertEqual(self.app.game_instance.connected, [True, False])
        finally:
            self.app.close()
            if peer is not None:
                peer.close()
            for thread in threads:
                thread.join(timeout=2)
            listener.close()
