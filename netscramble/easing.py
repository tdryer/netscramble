# TODO: need to solve t for x

def full_cubic_bezier(t, p0, p1, p2, p3):
    """Return point on cubic Bezier curve at t where t in [0, 1]."""
    res = [pow(1 - t, 3) * p0[i] + 3 * pow(1 - t, 2) * t * p1[i] + 3 * (1 - t) * pow(t, 2) * p2[i] + pow(t, 3) * p3[i] for i in xrange(2)]
    return tuple(res)

def cubic_bezier(t, x1, y1, x2, y2):
    return full_cubic_bezier(t, (0, 0), (x1, y1), (x2, y2), (1, 1))

linear = lambda t: t
ease_out = lambda t: cubic_bezier(t, 0, 0, 0, 1)[1]

#my_curve = ease_out
#import matplotlib.pyplot as plot
#xs = [cubic_bezier(t/100.0, 0, 0, 0, 1)[0] for t in range(100)]
#ys = [cubic_bezier(t/100.0, 0, 0, 0, 1)[1] for t in range(100)]
#plot.plot(xs, ys)
#plot.show()
