import unittest

from netscramble import grid

class TestDefaultGrid(unittest.TestCase):

    w, h = 2, 3

    def setUp(self):
        self.g = grid.Grid(self.w, self.h, default_val=lambda x, y: (x, y))

    def test_default_val(self):
        for x in xrange(self.w):
            for y in xrange(self.h):
                self.assertEqual(self.g.get(x, y), (x, y))


class TestGrid(unittest.TestCase):

    w, h = 2, 3

    def setUp(self):
        self.g = grid.Grid(self.w, self.h)

    def test_get(self):
        self.assertIsNone(self.g.get(0, 1))

    def test_set(self):
        self.g.set(0, 1, "foo")
        self.assertEqual(self.g.get(0, 1), "foo")

    def test_boundaries(self):
        self.g.set(0, 0, "low")
        self.g.set(self.w - 1, self.h - 1, "high")
        self.assertEqual(self.g.get(0, 0), "low")
        self.assertEqual(self.g.get(self.w - 1, self.h - 1), "high")

    def test_cells_are_independent(self):
        self.g.set(0, 1, "foo")
        for x in xrange(self.w):
            for y in xrange(self.h):
                cell = self.g.get(x, y)
                if x == 0 and y == 1:
                    self.assertEqual(cell, "foo")
                else:
                    self.assertIsNone(cell)

    def test_get_size(self):
        self.assertEqual(self.g.get_size(), (self.w, self.h))

    def test_iter(self):
        self.g.set(0, 1, "foo")
        cells = [x for x in self.g]
        self.assertIn((0, 1, "foo"), cells)
        self.assertEqual(len(cells), self.w * self.h)

    def test_edge_wrapping(self):
        with self.assertRaises(IndexError):
            self.g.get(self.w, self.h - 1)
        with self.assertRaises(IndexError):
            self.g.set(self.w, self.h - 1, "val")


class TestWrappedGrid(TestGrid):

    def setUp(self):
        self.g = grid.WrappedGrid(self.w, self.h)

    # overrides test in TestGrid
    def test_edge_wrapping(self):
        self.g.set(self.w, self.h - 1, "foo")
        self.assertEqual(self.g.get(self.w, self.h - 1), "foo")
        self.assertEqual(self.g.get(0, self.h - 1), "foo")
        self.assertEqual(self.g.get(2 * self.w, -1), "foo")
