"""Animation easing functions using cubic bezier curves."""

def _cubic_bezier_parametric(t, p0, p1, p2, p3):
    """Return (x, y) on cubic bezier curve for t in [0, 1]."""
    return tuple([
        pow(1 - t, 3) * p0[i] +
        3 * pow(1 - t, 2) * t * p1[i] +
        3 * (1 - t) * pow(t, 2) * p2[i] +
        pow(t, 3) * p3[i]
        for i in xrange(2)])

def _cubic_bezier(x, p0, p1, p2, p3, tolerance=0.001, start=0, end=1):
    """Return y for given x on the cubic bezier curve using binary search."""
    midpoint = start + (end - start) / 2.0
    r_x, r_y = _cubic_bezier_parametric(midpoint, p0, p1, p2, p3)
    difference = r_x - x
    if abs(difference) < tolerance:
        return r_y
    elif difference < 0:
        return _cubic_bezier(x, p0, p1, p2, p3, start=midpoint, end=end)
    else:
        return _cubic_bezier(x, p0, p1, p2, p3, start=start, end=midpoint)


def cubic_bezier(x, x1, y1, x2, y2):
    """Return y for given x on cubic bezier curve with given control points.

    This is similar to the CSS3 cubic-bezier function. The curve always starts
    at (0, 0) and ends at (1, 1). The control points (x1, y1) and (x2, y2)
    define the shape of the curve.
    """
    return _cubic_bezier(x, (0, 0), (x1, y1), (x2, y2), (1, 1))

# create using http://cubic-bezier.com/
linear = lambda x: cubic_bezier(x, 0, 0, 1, 1)
ease = lambda x: cubic_bezier(x, .25, .1, .25, 1)
elastic_out = lambda x: cubic_bezier(x, .52, 0, .86, 1.26)
