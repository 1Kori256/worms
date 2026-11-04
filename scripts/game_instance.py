"""Shared match state. The server owns movement, food, and collisions."""

import random
import time

BOARD_SIZE = 30
TICK_SECONDS = 0.25
STARTS = ((5, 5), (5, 25), (25, 5), (25, 25))


class GameInstance:
    def __init__(self, id, clock=time.monotonic, rng=None):
        self.id = id
        self.clock = clock
        self.rng = rng if rng is not None else random.Random()
        self.worms = []
        self.connected = []
        self.directions = []
        self.pending = {}
        self.started = False
        self.winner = None
        self.last_update = self.clock()
        self.food = None

    @property
    def active_players(self):
        return len(self.worms)

    @property
    def empty(self):
        return not any(self.connected)

    def add_player(self):
        if self.started or sum(self.connected) >= 4:
            raise ValueError("This room is full or already playing")
        if False in self.connected:
            player = self.connected.index(False)
            self.connected[player] = True
        else:
            player = len(self.connected)
            self.connected.append(True)
        self.reset()
        return player

    def reset(self):
        self.worms = [
            [(x, y), (x - 1, y), (x - 2, y)] if connected else []
            for (x, y), connected in zip(STARTS, self.connected)
        ]
        self.directions = [(1, 0)] * len(self.worms)
        self.pending.clear()
        self.started = False
        self.winner = None
        self.food = self.generate_pos()
        self.last_update = self.clock()

    def disconnect(self, player):
        self.connected[player] = False
        self.worms[player] = []
        self.pending.pop(player, None)

    def ready(self):
        if not self.started:
            self.started = True
            self.winner = None
            self.last_update = self.clock()

    def turn(self, player, direction):
        if not self.started or not self.worms[player] or player in self.pending:
            return
        direction = tuple(direction)
        if direction not in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            raise ValueError("Invalid direction")
        current = self.directions[player]
        if direction != current and direction != (-current[0], -current[1]):
            self.pending[player] = direction

    def generate_pos(self):
        occupied = {cell for worm in self.worms for cell in worm}
        free = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE)
                if (x, y) not in occupied]
        return self.rng.choice(free) if free else None

    def update(self):
        now = self.clock()
        if not self.started or now - self.last_update < TICK_SECONDS:
            return
        # A stalled client cannot make the match jump several cells at once.
        self.last_update = now
        for player, direction in self.pending.items():
            self.directions[player] = direction
        self.pending.clear()

        heads = {}
        growing = set()
        occupied = set()
        for player, worm in enumerate(self.worms):
            if not worm:
                continue
            dx, dy = self.directions[player]
            heads[player] = (worm[0][0] + dx, worm[0][1] + dy)
            if heads[player] == self.food:
                growing.add(player)
            occupied.update(worm if player in growing else worm[:-1])

        for player, head in heads.items():
            x, y = head
            collision = (not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE)
                         or head in occupied
                         or sum(other == head for other in heads.values()) > 1)
            self.worms[player] = [] if collision else [head] + (
                self.worms[player] if player in growing else self.worms[player][:-1])

        if any(self.worms[player] for player in growing):
            self.food = self.generate_pos()
        alive = [player for player, worm in enumerate(self.worms) if worm]
        if not alive or (sum(self.connected) > 1 and len(alive) <= 1) or self.food is None:
            winner = alive[0] if len(alive) == 1 else None
            self.reset()
            self.winner = winner

    def snapshot(self):
        return {"id": self.id, "active_players": self.active_players,
                "worms": self.worms, "connected": self.connected,
                "food": self.food, "started": self.started, "winner": self.winner}
