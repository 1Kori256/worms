import pygame
from scripts import utilities


class Renderer:
    def __init__(self, app):
        self.app = app
        self.board = pygame.Surface(app.window.base_resolution).convert()
        self.board.fill(app.config["window"]["background_color"])
        size = app.vrt_space.size
        for x in range(30):
            for y in range(30):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(self.board, (30, 30, 30),
                                     (x * size, y * size, size, size))

    def render(self):
        surface = self.app.window.app_window
        surface.blit(self.board, (0, 0))
        self.app.vrt_space.food.draw(surface)
        for worm in self.app.vrt_space.worms[:self.app.game_instance.active_players]:
            worm.draw(surface)
        utilities.debug(surface, self.app.window.font, (750, 10), self.app.window.fps)
