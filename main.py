import argparse
import os
import pygame

import scripts.utilities as utilities
from scripts.window import Window
from scripts.input import Input
from scripts.renderer import Renderer
from scripts.virtual_space import VrtSpace
from scripts.network import Network


class App:
    def __init__(self):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.config = utilities.load_config(os.path.join(self.path, "config"))
        self.window = Window(self)
        self.input = Input(self)
        self.vrt_space = VrtSpace(self)
        self.renderer = Renderer(self)
        self.n = None
        self.caption = None

    def web_init(self, host=None, port=5555):
        self.n = Network(self, host, port)
        self.player_id = self.n.player

    def update(self):
        self.input.update()
        if not self.input.running:
            return False
        self.game_instance = self.n.send(
            self.input.direction, self.input.keyboard_variables["ready"])
        self.vrt_space.update()
        self.renderer.render()
        self.window.render_screen()
        status = "Playing" if self.game_instance.started else "Space to start"
        if not self.game_instance.started and self.game_instance.winner is not None:
            status = f"Player {self.game_instance.winner + 1} won! — {status}"
        caption = f"{self.config['window']['caption']} — Player {self.player_id + 1} — {status}"
        if caption != self.caption:
            pygame.display.set_caption(caption)
            self.caption = caption
        return True

    def run(self):
        while self.update():
            pass

    def menu(self):
        # Keep the original menu and font, rendered once rather than every frame.
        font = pygame.font.Font(None, 150)
        text = font.render("Click to Play!", True, (255, 255, 255))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return True
            self.window.window.fill((30, 30, 30))
            self.window.window.blit(text, text.get_rect(center=self.window.window.get_rect().center))
            pygame.display.flip()
            self.window.clock.tick(60)

    def close(self):
        if self.n is not None:
            self.n.close()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Červy: a multiplayer snake game")
    parser.add_argument("host", nargs="?", help="server address (default: localhost)")
    parser.add_argument("--port", type=int, default=5555)
    args = parser.parse_args()
    app = App()
    try:
        if app.menu():
            app.web_init(args.host, args.port)
            app.run()
    except (OSError, ValueError, ConnectionError) as error:
        parser.exit(1, f"Connection error: {error}\nStart server.py first, then reconnect.\n")
    finally:
        app.close()


if __name__ == "__main__":
    main()
