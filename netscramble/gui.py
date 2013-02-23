#!/usr/bin/env python2.7

from gi.repository import Gtk, GLib #pylint: disable=E0611
import time

from netscramble import res
from netscramble import game, scene, grid_view
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


class MainWindow(scene.Scene):
    """Wrapper for the GtkWindow."""

    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file(res("glade/window1.glade"))
        builder.connect_signals(self)
        self.window = builder.get_object("window1")
        self.drawing_area = builder.get_object("drawingarea1")

        super(MainWindow, self).__init__(self.drawing_area, 60)

        self.clicks = 0
        self.start_time = None # when the current game started
        self.submitted_score = False
        self.render_matrix = None
        self.render_matrix_inverted = None
        self.game_grid = None
        self.grid_view = None
        self.on_new_game_action_activate(None)
        new_game_f = lambda: self.on_new_game_action_activate(None)
        self.score_dialog = ScoreDialog(self.window, new_game_f)

        self.window.show()

    def on_window1_destroy(self, widget, data=None):
        """End process when window is closed."""
        Gtk.main_quit()

    def on_drawingarea1_button_release_event(self, widget, event, data=None):
        """Handle mouse button presses."""
        cell_pos = self.grid_view.get_grid_coord_at((event.x, event.y))
        if cell_pos and event.button == 1: # left
            tile = self.game_grid.get(*cell_pos)
            # TODO: this logic is ugly
            self.tick_lock(tile)
            self.grid_view.rotate_cell(cell_pos, self._check_game_over,
                                       lambda: self.tick_unlock(tile))
            self.clicks += 1
        elif cell_pos and event.button == 3: # right
            self.grid_view.toggle_cell_lock(cell_pos)
            self.tick_once()

    def _check_game_over(self):
        """Add score if the game is over."""
        if game.is_game_over(self.game_grid) and not self.submitted_score:
            self.submitted_score = True
            self.score_dialog.show_and_add_score(
                GLib.get_real_name(), int(time.time()), self.clicks,
                int(time.time() - self.start_time))

    def on_drawingarea1_draw(self, widget, cr, _data=None):
        """Draw in the drawing area."""
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        with Timer(False): # TODO
            self.grid_view.update(1.0 / 60) # TODO: assumes 60 fps
            self.grid_view.draw(cr, (width, height))

    def on_new_game_action_activate(self, action, data=None):
        """Start a new game."""
        self.clicks = 0
        self.start_time = time.time()
        self.submitted_score = False
        self.game_grid = game.new_game_grid()
        self.grid_view = grid_view.GridView(self.game_grid)
        self.tick_once()

    def on_view_scores_action_activate(self, action, data=None):
        """Show the scores dialog."""
        self.score_dialog.show()

def main():
    """Start the game."""
    MainWindow()
    Gtk.main()

if __name__ == "__main__":
    main()
