"""Apply bindings to the key that generated each event."""

import pygame


class Input:
    def __init__(self, app):
        self.config = app.config["input"]
        self.keyboard_variables = {name: False for name, data in self.config.items()
                                   if data["device"] == "keyboard"}
        self.running = True
        self.direction = None

    def update(self):
        self.direction = None
        for name, data in self.config.items():
            if data["device"] == "keyboard" and data["trigger"] == "press":
                self.keyboard_variables[name] = False
        directions = {"move_up": (0, -1), "move_down": (0, 1),
                      "move_right": (1, 0), "move_left": (-1, 0)}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                for name, data in self.config.items():
                    if data["device"] != "keyboard" or data["binding"] != event.key:
                        continue
                    down = event.type == pygame.KEYDOWN
                    if data["trigger"] == "hold":
                        self.keyboard_variables[name] = down
                    elif down and not getattr(event, "repeat", False):
                        self.keyboard_variables[name] = (
                            not self.keyboard_variables[name] if data["trigger"] == "toggle" else True)
                        action = name.removesuffix("2")
                        if action in directions and self.direction is None:
                            self.direction = directions[action]
        if self.keyboard_variables["exit"]:
            self.running = False
