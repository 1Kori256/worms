from scripts.worm import Worm, Food, Block


class VrtSpace:
    def __init__(self, app):
        self.app = app
        self.size = 32
        self.food = Food(self.size)
        self.worms = [Worm(i, self.size, pos) for i, pos in enumerate(
            ((5, 5), (5, 25), (25, 5), (25, 25)))]
        self.previous_worms = None

    def update(self):
        state = self.app.game_instance
        self.food.pos = Block(*state.food) if state.food is not None else None
        if state.worms != self.previous_worms:
            for i, body in enumerate(state.worms):
                self.worms[i].body = [Block(*cell) for cell in body]
            self.previous_worms = state.worms
