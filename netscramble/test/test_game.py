import unittest

from netscramble import game

class TestDirections(unittest.TestCase):

    def test_rotate_cw(self):
        for a, b in [((-1, 0), (0, -1)), ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
                     ((0, -1), (1, 0))]:
            self.assertEqual(game.rotate_cw(a), b)

    def test_opposite(self):
        for a, b in [((-1, 0), (1, 0)), ((0, 1), (0, -1)), ((1, 0), (-1, 0)),
                     ((0, -1), (0, 1))]:
            self.assertEqual(game.opposite(a), b)

class TestGameLogic(unittest.TestCase):

    def setUp(self):
        self.g = game.new_game_grid()

    def test_cells_are_independent(self):
        c1 = game.Cell()
        c2 = game.Cell()
        c1.is_origin = True
        c1.is_powered = True
        c1.connections.append((1, 0))
        self.assertNotEqual(c1.is_origin, c2.is_origin)
        self.assertNotEqual(c1.is_powered, c2.is_powered)
        self.assertNotEqual(c1.connections, c2.connections)

    def test_is_game_over(self):
        self.assertFalse(game.is_game_over(self.g))
        for _x, _y, cell in self.g:
            cell.is_powered = True
        self.assertTrue(game.is_game_over(self.g))
