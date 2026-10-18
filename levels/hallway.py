"""A test school hallway built from boxes. Returns collision boxes for the player."""


def build_hallway(r):
    cube = r.load_mesh("cube")
    plane = r.load_mesh("plane")
    solids = []   # (x0, z0, x1, z1)

    def box(center, size, color, solid=True):
        obj = r.create_object(cube, color)
        r.set_transform(obj, center, (0, 0, 0), size)
        if solid:
            cx, _, cz = center
            sx, _, sz = size
            solids.append((cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2))
        return obj

    wall = (0.45, 0.42, 0.36)

    # floor: x -1.5..1.5, z -24..0
    floor = r.create_object(plane, (0.30, 0.28, 0.25))
    r.set_transform(floor, (0, 0, -12), (0, 0, 0), (3, 1, 24))

    # ceiling
    box((0, 3.05, -12), (3.4, 0.1, 24.4), (0.28, 0.28, 0.27), solid=False)

    # walls
    box((-1.6, 1.5, -12), (0.2, 3, 24.4), wall)    # left
    box(( 1.6, 1.5, -12), (0.2, 3, 24.4), wall)    # right
    box(( 0.0, 1.5, -24.1), (3.4, 3, 0.2), wall)   # far end
    box(( 0.0, 1.5,   0.1), (3.4, 3, 0.2), wall)   # behind the start

    # classroom doors (left wall)
    for i in range(5):
        box((-1.44, 1.1, -3 - i * 4.5), (0.12, 2.2, 1.0), (0.32, 0.18, 0.08), solid=False)

    # lockers (right wall)
    for i in range(18):
        color = (0.12, 0.22, 0.20) if i % 2 == 0 else (0.15, 0.16, 0.24)
        box((1.25, 1.0, -1.5 - i * 1.2), (0.5, 2.0, 1.0), color)

    # something to find at the end of the hall
    box((0, 0.5, -22.5), (0.5, 1.0, 0.5), (0.6, 0.05, 0.05))

    return solids
