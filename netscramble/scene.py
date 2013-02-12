from gi.repository import GObject #pylint: disable=E0611
import time

class Scene(object):
    """Manages drawing to a DrawingArea using Cairo.

    So far all this does is control the render loop so it stops when it's not
    being locked.
    """

    def __init__(self, drawing_area, framerate):
        self.framerate = framerate
        self.drawing_area = drawing_area
        self.locking_objs = {}

        # for profiling
        self.tick_start_time = None
        self.ticks = 0

    def tick_once(self):
        """Redraw once."""
        self.drawing_area.queue_draw()

    def tick_lock(self, locking_obj):
        """Redraw until tick_unlock(locking_obj) is called."""
        already_locked = len(self.locking_objs) > 0
        self.locking_objs[locking_obj] = True
        if not already_locked:
            # start ticking
            self._tick()

    def tick_unlock(self, locking_obj):
        """Stop redrawing if called for every locking_obj."""
        del self.locking_objs[locking_obj]

    def _tick(self):
        """Redraw and create timeout for the next redraw."""
        # if this is the first tick since being locked
        if self.tick_start_time == None:
            self.tick_start_time = time.time()
            self.ticks = 0
        # if ticking is locked
        if self.locking_objs.keys():
            self.ticks += 1
            self.drawing_area.queue_draw()
            GObject.timeout_add(1000 / self.framerate, self._tick)
        else:
            elapsed = time.time() - self.tick_start_time
            print "{} frames, {} seconds, {} fps".format(self.ticks, elapsed,
                                                         self.ticks / elapsed)
            self.tick_start_time = None
        return False # stop timeout from reoccurring automatically

