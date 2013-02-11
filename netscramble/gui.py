#!/usr/bin/env python2.7

from gi.repository import Gtk, GLib #pylint: disable=E0611
import cairo # less broken than pygi, seems to be compatible
from math import pi
from collections import defaultdict
import time

from netscramble import res
#from netscramble.game import TileGrid
from netscramble import game
from netscramble.score_dialog import ScoreDialog

class Timer(object):
    """Context manager for simple benchmarking."""

    def __init__(self, print_result):
        self.print_result = print_result
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, _type, _value, _traceback):
        millis_elapsed = 1000 * (time.time() - self.start_time)
        if self.print_result:
            print "{} ms elapsed".format(round(millis_elapsed, 2))


def hex_to_rgb(value):
    # from: http://stackoverflow.com/a/214657
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16)/255.0 for i in range(0, lv, lv/3))

def set_render_matrix(c, grid_width, grid_height, width, height):
    """Set transformation matrix for rendering the grid.

    (0, 0) will be the top left of the top left grid tile, and each tile is 1
    by 1.
    """
    tile_size = min(width / grid_width, height / grid_height)
    empty_x = width - (grid_width * tile_size)
    empty_y = height - (grid_height * tile_size)
    c.translate(empty_x / 2, empty_y / 2)
    c.scale(tile_size, tile_size)

def render_tile_grid(c, width, height, game_grid, tile_lock):
    set_render_matrix(c, game_grid.get_size()[0], game_grid.get_size()[1], width, height)
    for x, y, tile in game_grid:
        c.save()
        c.translate(x, y)
        render_tile(c, tile, tile_lock[(x, y)])
        c.restore()
    # return the matrix so it can be used for input
    return c.get_matrix()

def set_stripes_path(c, num_stripes):
    c.save()
    c.translate(0.5, 0.5)
    c.rotate(pi / 4)
    c.scale(1.3, 1.3)
    c.translate(-0.5, -0.5)
    w = 1.0 / num_stripes
    for i in xrange(num_stripes):
        if i % 2 == 0:
            c.rectangle(0, float(i)/num_stripes, 1, w)
    c.restore()

def set_pipe_path(c, pipes, thickness):
    # TODO: express this more compactly
    c.move_to(0.5 - thickness, 0.5 - thickness)
    if (0, -1) in pipes:
        c.line_to(0.5 - thickness, 0)
        c.line_to(0.5 + thickness, 0)
    c.line_to(0.5 + thickness, 0.5 - thickness)
    if (1, 0) in pipes:
        c.line_to(1, 0.5 - thickness)
        c.line_to(1, 0.5 + thickness)
    c.line_to(0.5 + thickness, 0.5 + thickness)
    if (0, 1) in pipes:
        c.line_to(0.5 + thickness, 1)
        c.line_to(0.5 - thickness, 1)
    c.line_to(0.5 - thickness, 0.5 + thickness)
    if (-1, 0) in pipes:
        c.line_to(0, 0.5 + thickness)
        c.line_to(0, 0.5 - thickness)
    c.close_path()

def render_tile(c, tile, locked):
    """Draw 1x1 tile at (0, 0)."""
    margin_size = 0.025
    tile_size = 1 - margin_size * 2

    c.set_antialias(cairo.ANTIALIAS_NONE)

    # draw tile background
    bg_col = hex_to_rgb("80b931")
    c.set_source_rgb(*bg_col)
    c.rectangle(margin_size, margin_size, tile_size, tile_size)
    c.fill_preserve()
    c.clip()

    c.set_antialias(cairo.ANTIALIAS_DEFAULT)

    if locked:
        # draw cross-hatch for locked tiles
        c.set_source_rgba(0, 0, 0, 0.3)
        c.rectangle(margin_size, margin_size, tile_size, tile_size)
        c.fill()
        set_stripes_path(c, 10)
        c.fill()

    c.set_antialias(cairo.ANTIALIAS_NONE)

    # draw pipes
    pipe_col = hex_to_rgb("ffd47e") if tile.is_powered else hex_to_rgb("ffffff")
    c.set_source_rgb(*pipe_col)
    set_pipe_path(c, tile.connections, 0.10)
    c.fill()

    if (len(tile.connections) == 1) and not tile.is_origin:
        # draw node box
        c.rectangle(0.25, 0.25, 0.5, 0.5)
        c.set_source_rgb(*pipe_col)
        c.fill_preserve()
        c.set_line_width(0.05) # given in fraction of tile width
        c.set_source_rgb(*hex_to_rgb("808080"))
        c.stroke()

    c.set_antialias(cairo.ANTIALIAS_DEFAULT)

    if tile.is_origin:
        # draw origin circle
        c.arc(0.5, 0.5, 0.25, 0, 2*pi)
        c.set_source_rgb(*pipe_col)
        c.fill_preserve()
        c.set_line_width(0.05) # given in fraction of tile width
        c.set_source_rgb(*hex_to_rgb("000000"))
        c.stroke()



class MainWindow(object):
    """Wrapper for the GtkWindow."""

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(res("glade/window1.glade"))
        builder.connect_signals(self)
        self.window = builder.get_object("window1")
        self.drawingarea = builder.get_object("drawingarea1")

        self.clicks = 0
        self.start_time = None
        self.submitted_score = False
        self.tick_period = 1000/60
        self.render_matrix = None
        self.render_matrix_inverted = None
        self.game_grid = None
        self.tile_lock = None
        self.on_new_game_action_activate(None)
        new_game_f = lambda: self.on_new_game_action_activate(None)
        self.score_dialog = ScoreDialog(self.window, new_game_f)

        self.window.show()

    def on_window1_destroy(self, widget, data=None):
        """End process when window is closed."""
        Gtk.main_quit()

    def on_drawingarea1_button_release_event(self, widget, event, data=None):
        g_x, g_y = self.render_matrix_inverted.transform_point(event.x, event.y)
        g_x, g_y = int(g_x), int(g_y)
        if event.button == 1 and not self.tile_lock[(g_x, g_y)]: # left
            game.rotate_tile(self.game_grid, g_x, g_y)
            self.clicks += 1
        elif event.button == 3: # right
            self.tile_lock[(g_x, g_y)] = not self.tile_lock[(g_x, g_y)]
        self.drawingarea.queue_draw()
        if game.is_game_over(self.game_grid) and not self.submitted_score:
            self.submitted_score = True
            self.score_dialog.show_and_add_score(
                GLib.get_real_name(), int(time.time()), self.clicks,
                int(time.time() - self.start_time)
            )

    def on_drawingarea1_draw(self, widget, cr, _data=None):
        "Draw in the drawing area."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()

        with Timer(False): # TODO
            self.render_matrix = render_tile_grid(
                cr, width, height, self.game_grid, self.tile_lock
            )
        # TODO: need way to copy a matrix to avoid this
        self.render_matrix_inverted = cr.get_matrix()
        self.render_matrix_inverted.invert()

    def on_new_game_action_activate(self, action, data=None):
        self.clicks = 0
        self.start_time = time.time()
        self.submitted_score = False
        self.game_grid = game.new_game_grid()
        self.tile_lock = defaultdict(lambda: False)
        self.drawingarea.queue_draw()

    def on_view_scores_action_activate(self, action, data=None):
        self.score_dialog.show()

def main():
    """Start the game."""
    MainWindow()
    Gtk.main()

if __name__ == "__main__":
    main()
