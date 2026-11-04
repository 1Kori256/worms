import random
import unittest
from scripts.game_instance import BOARD_SIZE, GameInstance


class GameTests(unittest.TestCase):
    def game(self, players=1):
        game = GameInstance(0, clock=lambda: self.now, rng=random.Random(7))
        for _ in range(players):
            game.add_player()
        return game

    def setUp(self):
        self.now = 0.0

    def tick(self, game):
        self.now += 0.25
        game.update()

    def test_waits_for_space_and_tick(self):
        game = self.game()
        self.tick(game)
        self.assertEqual(game.worms[0][0], (5, 5))
        game.ready()
        self.now += 0.24
        game.update()
        self.assertEqual(game.worms[0][0], (5, 5))
        self.now += 0.01
        game.update()
        self.assertEqual(game.worms[0][0], (6, 5))
        game.update()
        self.assertEqual(game.worms[0][0], (6, 5))

    def test_ready_during_match_does_not_delay_tick(self):
        game = self.game()
        game.ready()
        self.now = 0.2
        game.ready()
        self.now = 0.25
        game.update()
        self.assertEqual(game.worms[0][0], (6, 5))

    def test_timers_are_independent(self):
        a, b = self.game(), self.game()
        a.ready()
        b.ready()
        self.now = 0.25
        a.update()
        b.update()
        self.assertEqual(a.worms[0], b.worms[0])
        self.assertEqual(b.worms[0][0], (6, 5))

    def test_stall_moves_once(self):
        game = self.game()
        game.ready()
        self.now = 10
        game.update()
        self.assertEqual(game.worms[0][0], (6, 5))

    def test_reversal_is_ignored(self):
        game = self.game()
        game.ready()
        game.turn(0, (-1, 0))
        self.tick(game)
        self.assertEqual(game.worms[0][0], (6, 5))

    def test_one_turn_per_tick(self):
        game = self.game()
        game.ready()
        game.turn(0, (1, 0))
        game.turn(0, (0, -1))
        game.turn(0, (-1, 0))
        self.tick(game)
        self.assertEqual(game.worms[0][0], (5, 4))
        game.turn(0, (-1, 0))
        self.tick(game)
        self.assertEqual(game.worms[0][0], (4, 4))

    def test_eating_grows_on_arrival(self):
        game = self.game()
        game.food = (6, 5)
        game.ready()
        self.tick(game)
        self.assertEqual(len(game.worms[0]), 4)
        self.assertEqual(game.worms[0][0], (6, 5))
        self.assertNotIn(game.food, game.worms[0])

    def test_food_only_on_free_playable_cells(self):
        game = self.game(4)
        occupied = {cell for worm in game.worms for cell in worm}
        for _ in range(200):
            x, y = game.generate_pos()
            self.assertTrue(0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE)
            self.assertNotIn((x, y), occupied)
        game.worms = [[(x, y) for x in range(30) for y in range(30) if (x, y) != (29, 29)]]
        self.assertEqual(game.generate_pos(), (29, 29))
        game.worms[0].append((29, 29))
        self.assertIsNone(game.generate_pos())

    def test_wall_collision(self):
        for head, direction in (((29, 5), (1, 0)), ((0, 5), (-1, 0)),
                                ((5, 0), (0, -1)), ((5, 29), (0, 1))):
            with self.subTest(head=head):
                game = self.game(3)
                game.worms[0] = [head, (10, 10), (10, 11)]
                game.directions[0] = direction
                game.ready()
                self.tick(game)
                self.assertEqual(game.worms[0], [])
                self.assertTrue(game.started)

    def test_self_collision(self):
        game = self.game(3)
        game.worms[0] = [(5, 5), (5, 6), (6, 6), (6, 5), (7, 5)]
        game.ready()
        self.tick(game)
        self.assertEqual(game.worms[0], [])

    def test_departing_tail_is_free(self):
        game = self.game()
        game.worms[0] = [(5, 5), (5, 6), (6, 6), (6, 5)]
        game.ready()
        self.tick(game)
        self.assertEqual(game.worms[0][0], (6, 5))

    def test_other_body_collision(self):
        game = self.game(3)
        game.worms[1] = [(6, 4), (6, 5), (6, 6)]
        game.ready()
        self.tick(game)
        self.assertEqual(game.worms[0], [])

    def test_head_on_collision_is_simultaneous(self):
        game = self.game(4)
        game.worms[1] = [(7, 5), (8, 5), (9, 5)]
        game.directions[1] = (-1, 0)
        game.ready()
        self.tick(game)
        self.assertEqual(game.worms[:2], [[], []])
        self.assertTrue(game.started)

    def test_swapping_heads_kills_both(self):
        game = self.game(4)
        game.worms[1] = [(6, 5), (7, 5), (8, 5)]
        game.directions[1] = (-1, 0)
        game.ready()
        self.tick(game)
        self.assertEqual(game.worms[:2], [[], []])

    def test_winner_resets_and_can_start_again(self):
        game = self.game(2)
        game.worms[0] = [(29, 5), (28, 5), (27, 5)]
        game.ready()
        self.tick(game)
        self.assertFalse(game.started)
        self.assertEqual(game.winner, 1)
        self.assertEqual(game.worms[0][0], (5, 5))
        game.ready()
        self.assertTrue(game.started)
        self.assertIsNone(game.winner)

    def test_solo_practice_and_death(self):
        game = self.game()
        game.ready()
        self.tick(game)
        self.assertTrue(game.started)
        game.worms[0] = [(29, 5), (28, 5), (27, 5)]
        self.tick(game)
        self.assertFalse(game.started)
        self.assertEqual(game.worms[0][0], (5, 5))

    def test_disconnect_and_rejoin_preserve_player_ids(self):
        game = self.game(3)
        game.disconnect(1)
        self.assertEqual(game.worms[1], [])
        self.assertTrue(game.connected[2])
        self.assertEqual(game.add_player(), 1)
        self.assertEqual(game.connected, [True, True, True])
        game.worms[1].append((1, 1))
        game.reset()
        self.assertEqual(len(game.worms[1]), 3)

    def test_started_and_full_rooms_reject_new_players(self):
        game = self.game(4)
        with self.assertRaises(ValueError):
            game.add_player()
        game = self.game()
        game.ready()
        with self.assertRaises(ValueError):
            game.add_player()


if __name__ == "__main__":
    unittest.main()
