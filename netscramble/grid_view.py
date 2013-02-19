from math import pi

from netscramble.grid import Grid
from netscramble import game

def hex_to_rgb(value):
    """Convert hexadecimal to RGB tuple."""
    # from: http://stackoverflow.com/a/214657
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16)/255.0 for i in range(0, lv, lv/3))

def point_list_to_path(c, point_list):
    """Draw list of points to Cairo path."""
    c.move_to(*point_list[0])
    del point_list[0]
    for point in point_list:
        c.line_to(*point)
    c.close_path()

class CellView(object):
    """Renderer for a cell in the game grid."""

    MARGIN_SIZE = 0.025
    PIPE_THICKNESS = 0.1
    NODE_EDGE_WIDTH = 0.05
    BG_COL = hex_to_rgb("80b931")
    POWERED_PIPE_COL = hex_to_rgb("ffd47e")
    UNPOWERED_PIPE_COL = hex_to_rgb("ffffff")
    NODE_EDGE_COL = hex_to_rgb("808080")
    ORIGIN_EDGE_COL = hex_to_rgb("000000")
    NUM_STRIPES = 10
    ROTATION_RAD_PER_SEC = 4 * pi

    def __init__(self, game_cell):
        self.game_cell = game_cell
        self.is_locked = False
        self.rotation = None

    def update(self, elapsed):
        """Update animation by elapsed seconds."""
        if self.rotation:
            if self.rotation["rot"] >= self.rotation["end"]:
                self.rotation["on_end"]()
                self.rotation = None
            else:
                # TODO: could be above end, but gives pleasant bounce effect
                self.rotation["rot"] += self.ROTATION_RAD_PER_SEC * elapsed

    def _set_stripes_path(self, c, size, pos):
        """Set Cairo path for background stripes."""
        c.save()
        c.translate(1.0 / 2, 1.0 / 2)
        c.rotate(pi / 4)
        c.scale(1.3, 1.3)
        c.translate(-1.0 / 2, -1.0 / 2)
        w = 1.0 / self.NUM_STRIPES
        for i in xrange(self.NUM_STRIPES):
            if i % 2 == 0:
                c.rectangle(0, float(i)/self.NUM_STRIPES, 1, w)
        c.restore()

    def _get_pipe_path(self):
        """Return path for the cell's pipes scaled in 0-1."""
        pipes = self.game_cell.connections
        thickness = self.PIPE_THICKNESS
        # TODO: express this more compactly
        yield 0.5 - thickness, 0.5 - thickness
        if (0, -1) in pipes:
            yield 0.5 - thickness, 0
            yield 0.5 + thickness, 0
        yield 0.5 + thickness, 0.5 - thickness
        if (1, 0) in pipes:
            yield 1, 0.5 - thickness
            yield 1, 0.5 + thickness
        yield 0.5 + thickness, 0.5 + thickness
        if (0, 1) in pipes:
            yield 0.5 + thickness, 1
            yield 0.5 - thickness, 1
        yield 0.5 - thickness, 0.5 + thickness
        if (-1, 0) in pipes:
            yield 0, 0.5 + thickness
            yield 0, 0.5 - thickness

    def draw(self, c, pos, size):
        """Draw the cell."""
        margin = round(size * self.MARGIN_SIZE)
        tile = size - margin * 2
        left = pos[0] + margin
        top = pos[1] + margin

        # apply rotation
        c.save()
        if self.rotation:
            c.translate(pos[0] + size / 2, pos[1] + size / 2)
            c.rotate(self.rotation["rot"])
            c.translate(-pos[0] - size / 2, -pos[1] - size / 2)

        # draw tile background
        c.set_source_rgb(*self.BG_COL)
        c.rectangle(left, top, tile, tile)
        c.fill()

        # TODO: less overdraw
        # draw locked background
        if self.is_locked:
            c.save()
            c.set_source_rgba(0, 0, 0, 0.3)
            c.rectangle(left, top, tile, tile)
            c.fill_preserve()
            c.clip()
            c.translate(*pos)
            c.scale(size, size)
            self._set_stripes_path(c, size, pos)
            c.fill()
            c.restore()

        # draw pipes
        pipe_col = (self.POWERED_PIPE_COL if self.game_cell.is_powered
                    else self.UNPOWERED_PIPE_COL)
        c.set_source_rgb(*pipe_col)
        point_list_to_path(c, [(left + round(x * tile), top + round(y * tile))
                               for x, y in self._get_pipe_path()])
        c.fill()

        # draw node box
        if (len(self.game_cell.connections) == 1) and not self.game_cell.is_origin:
            c.rectangle(int(left + tile / 4), int(top + tile / 4),
                        int(tile / 2), int(tile / 2))
            c.set_source_rgb(*pipe_col)
            c.fill_preserve()
            # must be divisible by 2 to prevent anti aliasing
            c.set_line_width(int(round(self.NODE_EDGE_WIDTH * tile) / 2) * 2)
            c.set_source_rgb(*self.NODE_EDGE_COL)
            c.stroke()

        # draw origin circle
        if self.game_cell.is_origin:
            c.arc(left + size / 2, top + size / 2, size / 4, 0, 2 * pi)
            c.set_source_rgb(*pipe_col)
            c.fill_preserve()
            # must be divisible by 2 to prevent anti aliasing
            c.set_line_width(int(round(self.NODE_EDGE_WIDTH * tile) / 2) * 2)
            c.set_source_rgb(*self.ORIGIN_EDGE_COL)
            c.stroke()

        # unapply rotation
        c.restore()

class GridView(object):
    """Renderer for the game grid.

    Don't scale/translate using the Cairo matrix since it makes the straight
    lines fuzzy.
    """

    def __init__(self, game_grid):
        self.game_grid = game_grid
        self.last_view_size = None
        # create copy of game_grid containing CellViews
        self.cell_view_grid = Grid(
            game_grid.get_size()[0],
            game_grid.get_size()[1],
            default_val=lambda x, y: CellView(game_grid.get(x, y))
        )

    def draw(self, c, size):
        """Draw grid view using given context and size."""
        self.last_view_size = size
        tile_size, left, top = self._get_metrics(self.cell_view_grid.get_size(),
                                                 size)
        # TODO: less awkward way of drawing rotating cells on top
        top_cells = [(x, y, cell_view) for x, y, cell_view
                     in self.cell_view_grid if cell_view.rotation]
        bottom_cells = [(x, y, cell_view) for x, y, cell_view
                        in self.cell_view_grid
                        if (x, y, cell_view) not in top_cells]
        for x, y, cell_view in bottom_cells:
            cell_view.draw(c, (left + x * tile_size, top + y * tile_size),
                           tile_size)
        for x, y, cell_view in top_cells:
            cell_view.draw(c, (left + x * tile_size, top + y * tile_size),
                           tile_size)

    def update(self, elapsed):
        """Update animations by elapsed seconds."""
        for _x, _y, cell_view in self.cell_view_grid:
            cell_view.update(elapsed)

    def _get_metrics(self, grid_size, view_size):
        """Return metrics for rendering the grid.

        Returns tile size, and top left location of the grid so it is as large
        as possible and centered.
        """
        tile_size = min(view_size[0] / grid_size[0],
                        view_size[1] / grid_size[1])
        empty_x = view_size[0] - (grid_size[0] * tile_size)
        empty_y = view_size[1] - (grid_size[1] * tile_size)
        return int(tile_size), empty_x / 2, empty_y / 2

    def get_grid_coord_at(self, pixel_position):
        """Translate pixel coordinates to grid coordinates."""
        pixel_position = (int(pixel_position[0]), int(pixel_position[1]))
        g_w, g_h = self.cell_view_grid.get_size()
        tile_size, left, top = self._get_metrics(self.cell_view_grid.get_size(),
                                                 self.last_view_size)
        x, y = pixel_position
        g_x, g_y = ((x - left) / tile_size, (y - top) / tile_size)
        if 0 <= g_x < g_w and 0 <= g_y < g_h:
            return g_x, g_y
        else:
            return None

    def toggle_cell_lock(self, grid_pos):
        """Toggle lock for cell at given pos."""
        is_locked = self.cell_view_grid.get(*grid_pos).is_locked
        self.cell_view_grid.get(*grid_pos).is_locked = not is_locked

    def rotate_cell(self, grid_pos, callback=None):
        "Set rotation animation for cell at given pos."""
        cell = self.cell_view_grid.get(*grid_pos)
        if not cell.is_locked:
            cell.rotation = {
                "start": 0,
                "end": pi / 2,
                "rot": 0,
                "on_end": lambda: (game.rotate_tile(self.game_grid, *grid_pos),
                                   callback()),
            }

