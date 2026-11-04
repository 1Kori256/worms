"""Draw the original worm sprites. Game rules live in game_instance.py."""

from functools import lru_cache
from pathlib import Path
import pygame

IMAGE_DIR = Path(__file__).resolve().parent.parent / "data" / "images"
SPRITES = (
    "head_up", "head_down", "head_right", "head_left",
    "tail_up", "tail_down", "tail_right", "tail_left",
    "body_vertical", "body_horizontal", "body_tr", "body_tl", "body_br", "body_bl",
)


@lru_cache(maxsize=64)
def load_sprite(name, size):
    image = pygame.image.load(str(IMAGE_DIR / f"{name}.png")).convert_alpha()
    return pygame.transform.scale(image, (size, size))


class Block:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Block):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __sub__(self, other):
        return Block(self.x - other.x, self.y - other.y)


class Worm:
    def __init__(self, player_id, size, pos):
        self.player_id = player_id
        self.size = size
        self.body = [Block(*pos), Block(pos[0] - 1, pos[1]), Block(pos[0] - 2, pos[1])]
        for name in SPRITES:
            setattr(self, name, load_sprite(name, size))

    def update_head_image(self):
        head_relation = self.body[1] - self.body[0]
        if head_relation == Block(1,0): self.head = self.head_left
        elif head_relation == Block(-1,0): self.head = self.head_right
        elif head_relation == Block(0,1): self.head = self.head_up
        elif head_relation == Block(0,-1): self.head = self.head_down

    def update_tail_image(self):
        tail_relation = self.body[-2] - self.body[-1]
        if tail_relation == Block(1,0): self.tail = self.tail_left
        elif tail_relation == Block(-1,0): self.tail = self.tail_right
        elif tail_relation == Block(0,1): self.tail = self.tail_up
        elif tail_relation == Block(0,-1): self.tail = self.tail_down

    def draw(self, surface) -> None:
        if len(self.body) < 2:
            return
        self.update_head_image()
        self.update_tail_image()

        for index,block in enumerate(self.body):
            x_pos = int(block.x * self.size)
            y_pos = int(block.y * self.size)
            block_rect = pygame.Rect(x_pos, y_pos, self.size, self.size)

            if index == 0:
                surface.blit(self.head,block_rect)
            elif index == len(self.body) - 1:
                surface.blit(self.tail,block_rect)
            else:
                previous_block = self.body[index + 1] - block
                next_block = self.body[index - 1] - block
                if previous_block.x == next_block.x:
                    surface.blit(self.body_vertical, block_rect)
                elif previous_block.y == next_block.y:
                    surface.blit(self.body_horizontal, block_rect)
                else:
                    if previous_block.x == -1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == -1:
                        surface.blit(self.body_tl, block_rect)
                    elif previous_block.x == -1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == -1:
                        surface.blit(self.body_bl, block_rect)
                    elif previous_block.x == 1 and next_block.y == -1 or previous_block.y == -1 and next_block.x == 1:
                        surface.blit(self.body_tr, block_rect)
                    elif previous_block.x == 1 and next_block.y == 1 or previous_block.y == 1 and next_block.x == 1:
                        surface.blit(self.body_br, block_rect)


class Food:
    def __init__(self, size):
        self.size = size
        self.pos = None
        self.image = load_sprite("apple", size)

    def draw(self, surface):
        if self.pos is not None:
            surface.blit(self.image, (self.pos.x * self.size, self.pos.y * self.size))
