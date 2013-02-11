"""Game logic without any graphics."""

from random import randrange, choice

from netscramble import grid

# 4 cartesian directions
DIRECTIONS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

def rotate_cw(direction):
    """Return the given direction rotated 90 degrees clockwise.

    This uses the Cairo coordinate system (down is positive y).
    """
    return (direction[1] * -1, direction[0])

def opposite(direction):
    """Return the opposite of the given direction."""
    return rotate_cw(rotate_cw(direction))


class Cell(object):
    """Cell in the game grid."""

    def __init__(self):
        self.connections = [] # list of directions that the cell connects to
        self.is_origin = False # whether this cell is the power source
        self.is_powered = False # whether this cell is powered


def new_game_grid(width=10, height=7, grid_class=grid.WrappedGrid):
    """Return a new game grid for netscramble."""
    g = grid_class(width, height, default_val=lambda _x, _y: Cell())
    _generate_puzzle(g)
    _randomize_rotations(g)
    _update_power(g)
    return g

def _generate_puzzle(game_grid):
    """Overwrite the given game grid with a new puzzle."""
    w, h = game_grid.get_size()
    # set random cell to origin
    origin_x, origin_y = randrange(w), randrange(h)
    game_grid.get(origin_x, origin_y).is_origin = True
    # randomly connect connected cells to unconnected ones
    candidate_tiles = [(origin_x, origin_y)]
    while candidate_tiles:
        x, y = choice(candidate_tiles)
        filled_tile = _add_random_connection(game_grid, x, y)
        if filled_tile:
            candidate_tiles.append(filled_tile)
        else:
            candidate_tiles.remove((x, y))

def _add_random_connection(game_grid, x, y):
    """Connect the cell at (x,y) to random empty neighbor.

    If empty neighbor is found and connected, its coordinates are returned,
    otherwise None.
    """
    adj_coords = [(x+dx, y+dy) for dx, dy in DIRECTIONS]
    empty_adj_tiles = [(ax, ay, game_grid.get(ax, ay))
                       for ax, ay in adj_coords
                       if not game_grid.get(ax, ay).connections]
    if not empty_adj_tiles:
        return None
    tx, ty, cell = choice(empty_adj_tiles)
    cell.connections.append((x - tx, y - ty))
    game_grid.get(x, y).connections.append((tx - x, ty - y))
    return (tx, ty)

def _randomize_rotations(game_grid):
    """Randomly rotate every cell."""
    for x, y, _tile in game_grid:
        # rotate cell 0, 1, 2, or 3 times
        for _i in xrange(choice([0, 1, 2, 3])):
            rotate_tile(game_grid, x, y, update_power=False)

def _update_power(game_grid):
    """Update the power connections in game_grid."""
    for _x, _y, cell in game_grid:
        cell.is_powered = False
    orig_x, orig_y, _origin = _get_origin(game_grid)
    _update_tile_power(game_grid, orig_x, orig_y)

def _update_tile_power(game_grid, x, y):
    """Power a cell and any adjacent cells which are connected to it."""
    cell = game_grid.get(x, y)
    cell.is_powered = True
    for dx, dy in cell.connections:
        adj_tile = game_grid.get(x + dx, y + dy)
        if (not adj_tile.is_powered and
            opposite((dx, dy)) in adj_tile.connections):
            _update_tile_power(game_grid, x + dx, y + dy)

def rotate_tile(game_grid, x, y, update_power=True):
    """Rotate the cell at x, y clockwise."""
    c = game_grid.get(x, y)
    c.connections = [rotate_cw(d) for d in c.connections]
    if update_power:
        _update_power(game_grid)

def _get_origin(game_grid):
    """Return x, y, cell for the origin cell in the game_grid."""
    return [(x, y, cell) for x, y, cell in game_grid if cell.is_origin][0]

def is_game_over(game_grid):
    """Return True if every node is powered."""
    return [c for _x, _y, c in game_grid if len(c.connections) == 1 and
            not c.is_powered] == []
