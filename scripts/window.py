from collections import deque
import os
import pygame


class Window:
    def __init__(self, app):
        config = app.config["window"]
        pygame.init()
        self.base_resolution = tuple(config["base_resolution"])
        self.scaled_resolution = tuple(config["scaled_resolution"])
        self.window = pygame.display.set_mode(self.scaled_resolution)
        pygame.display.set_caption(config["caption"])
        self.app_window = pygame.Surface(self.base_resolution).convert()
        self.clock = pygame.time.Clock()
        self.dt = 0.001
        self.fps = 0
        self.frame_history = deque(maxlen=100)
        self.font = pygame.font.Font(os.path.join(app.path, "data", "font", "game_font.ttf"), 8)

    def render_screen(self):
        if self.base_resolution == self.scaled_resolution:
            self.window.blit(self.app_window, (0, 0))
        else:
            pygame.transform.scale(self.app_window, self.scaled_resolution, self.window)
        pygame.display.flip()
        self.dt = max(self.clock.tick(60) / 1000, 0.001)
        self.frame_history.append(self.dt)
        self.fps = round(len(self.frame_history) / sum(self.frame_history))
