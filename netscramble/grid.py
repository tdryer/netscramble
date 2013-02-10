"""Generic grid classes."""

class Grid(object):
    """A 2D grid containing cells which can be any Python object.

    Coordinates are zero-indexed.
    """

    def __init__(self, width, height, edge_wrapping=False,
                 default_val=lambda x, y: None):
        """Create grid of specified size.

        default_val(x, y) returns the default value for the cell at x, y.

        If edge_wrapping is True, coordinate values wrap around edges.
        """
        self._width = width
        self._height = height
        self._edge_wrapping = edge_wrapping
        self._cells = [[default_val(x, y) for y in xrange(height)]
                       for x in xrange(width)]

    def __iter__(self):
        """Allow iteration over every (x, y, cell) in the grid."""
        return iter(((x, y, self.get(x, y))
                     for x in xrange(self._width)
                     for y in xrange(self._height)))

    def get(self, x, y):
        """Return the cell at grid position x, y.

        Raises IndexError if x, y is out of range.
        """
        return self._cells[x][y]

    def set(self, x, y, val):
        """Set the cell at grid position x, y to val.

        Raises IndexError if x, y is out of range.
        """
        self._cells[x][y] = val

    def get_size(self):
        """Return (width, height) of the grid."""
        return (self._width, self._height)


class WrappedGrid(Grid):
    """Grid subclass adding edge wrapping for coordinates."""

    def get(self, x, y):
        return self._cells[x % self._width][y % self._height]

    def set(self, x, y, val):
        self._cells[x % self._width][y % self._height] = val
