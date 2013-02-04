"""Logic for the game."""

from random import randrange, choice

DIR = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

def rotate_dir(d, clockwise=True):
    if clockwise:
        d = (d[1] * -1, d[0])
    else:
        d = (d[1], d[0] * -1)
    return d

def opposite_dir(d):
    return (d[0] * -1, d[1] * -1)

class Tile():

    def __init__(self):
        self.pipes = []
        self.is_origin = False
        self.is_powered = False

class TileGrid():

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._grid = []
        for x in xrange(0, width):
            g = []
            for y in xrange(0, height):
                g.append(Tile())
            self._grid.append(g)

        self.generate_puzzle()
        self._randomize_rotations()
        self.update_power()

    def set_tile(self, x, y, tile):
        self._grid[x % self.width][y % self.height] = tile

    def get_tile(self, x, y):
        return self._grid[x % self.width][y % self.height]

    def rotate_tile(self, x, y):
        t = self.get_tile(x, y)
        t.pipes = [rotate_dir(d) for d in t.pipes]
        self.update_power()

    def get_all_tiles(self):
        for x in xrange(0, self.width):
            for y in xrange(0, self.height):
                yield x, y, self.get_tile(x, y)

    def get_origin(self):
        return [(x, y, tile) for x, y, tile in self.get_all_tiles()
                if tile.is_origin][0]

    def update_power(self):
        for x, y, tile in self.get_all_tiles():
            tile.is_powered = False
        orig_x, orig_y, origin = self.get_origin()
        self._update_tile_power(orig_x, orig_y)

    def _update_tile_power(self, x, y):
        """Power a tile and any adjacent tiles which are connected to it."""
        tile = self.get_tile(x, y)
        tile.is_powered = True
        for dx, dy in tile.pipes:
            adj_tile = self.get_tile(x + dx, y + dy)
            if (not adj_tile.is_powered and
                    opposite_dir((dx, dy)) in adj_tile.pipes):
                self._update_tile_power(x + dx, y + dy)

    def is_game_over(self):
        for _, _, tile in self.get_all_tiles():
            if len(tile.pipes) == 1 and not tile.is_powered:
                return False
        return True

    def _randomize_rotations(self):
        # TODO: using rotate_tile updates power, inefficient
        for x, y, tile in self.get_all_tiles():
            # rotate time 0, 1, 2, or 3 times
            for _i in xrange(choice([0, 1, 2, 3])):
                self.rotate_tile(x, y)

    def generate_puzzle(self):
        """From blank grid, generate new puzzle."""
        # set random tile to origin
        rx, ry = randrange(0, self.width), randrange(0, self.height)
        self.get_tile(rx, ry).is_origin = True
        candidate_tiles = [(rx, ry)]
        while len(candidate_tiles) > 0:
            tx, ty = choice(candidate_tiles)
            filled_tile = self.add_random_connection(tx, ty)
            if filled_tile:
                candidate_tiles.append(filled_tile)
            else:
                candidate_tiles.remove((tx, ty))

    def add_random_connection(self, x, y):
        """Connect the cell at (x,y) to random empty neighbor."""
        adj_coords = [(x+dx, y+dy) for dx, dy in DIR.values()]
        empty_adj_tiles = [(ax, ay, self.get_tile(ax, ay))
                           for ax, ay in adj_coords
                           if len(self.get_tile(ax, ay).pipes) == 0]
        if len(empty_adj_tiles) == 0:
            return None
        tx, ty, tile = choice(empty_adj_tiles)
        tile.pipes.append((x - tx, y - ty))
        self.get_tile(x, y).pipes.append((tx - x, ty - y))
        return (tx, ty)

