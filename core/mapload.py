"""Loads a map from a JSON file into the World. The format is described in DOCS.md."""
import json

from entities.door import Door
from entities.pickup import Pickup
from entities.registry import TYPES

TOP = {"name", "start", "fog", "ambient", "colors", "floors", "ceilings", "walls",
       "boxes", "doors", "pickups", "entities"}
FIELDS = {
    "floors":   {"from", "to", "y", "color"},
    "ceilings": {"from", "to", "y", "color"},
    "walls":    {"from", "to", "height", "thickness", "color", "alt_color", "repeat"},
    "boxes":    {"pos", "size", "color", "alt_color", "solid", "repeat"},
    "doors":    {"hinge", "dir", "swing", "width", "height", "key", "open", "color", "repeat"},
    "pickups":  {"pos", "item", "name", "color"},
    "entities": {"type", "args"},
}
GREY = [0.6, 0.6, 0.6]
DOOR_BROWN = [0.32, 0.18, 0.08]
PICKUP_GOLD = [0.9, 0.75, 0.1]


class MapError(Exception):
    """A problem in a map file. The message says where."""


def read_map(path):
    """Parse the JSON file. Raises MapError with line and column on a syntax error."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise MapError(f"map file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise MapError(f"{path}: JSON syntax error on line {e.lineno}, column {e.colno}: {e.msg}") from None


# ----------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------
def _need(item, key, where):
    if key not in item:
        raise MapError(f'{where} is missing "{key}"')
    return item[key]


def _vec(value, n, where, key):
    ok = (isinstance(value, (list, tuple)) and len(value) == n and
          all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value))
    if not ok:
        raise MapError(f'{where}: "{key}" must be a list of {n} numbers')
    return [float(v) for v in value]


def _rgb(colors, value, where):
    if isinstance(value, str):
        if value not in colors:
            raise MapError(f'{where}: unknown color "{value}" (add it to "colors" or write [r, g, b])')
        value = colors[value]
    return tuple(_vec(value, 3, where, "color"))


def _pick_color(colors, item, n, where, default=GREY):
    """alt_color is used for every second copy of a repeated element."""
    if n % 2 == 1 and "alt_color" in item:
        return _rgb(colors, item["alt_color"], where)
    return _rgb(colors, item.get("color", default), where)


def _offsets(item, where):
    """All (dx, dz) offsets produced by an item's optional "repeat"."""
    spec = item.get("repeat")
    if spec is None:
        return [(0.0, 0.0)]
    if isinstance(spec, dict):
        spec = [spec]
    if not isinstance(spec, list):
        raise MapError(f'{where}: "repeat" must be {{ ... }} or a list of them')
    offsets = [(0.0, 0.0)]
    for rep in spec:
        count = int(rep.get("count", 1))
        sx, sz = _vec(rep.get("step", [0, 0]), 2, where, "step")
        offsets = [(ox + i * sx, oz + i * sz) for (ox, oz) in offsets for i in range(count)]
    return offsets


def _check_keys(item, section, where):
    if not isinstance(item, dict):
        raise MapError(f"{where} must be an object like {{ ... }}")
    for k in item:
        if k not in FIELDS[section] and not k.startswith("_"):
            print(f'[map] warning: {where} has unknown field "{k}" (ignored)')


# ----------------------------------------------------------------------
# the builder
# ----------------------------------------------------------------------
def build_map(world, data):
    """Create everything in `data` inside the world.
    Returns {"start": (x, z, yaw), "fog": (color, density), "ambient": (r, g, b)}."""
    if not isinstance(data, dict):
        raise MapError("the map file must contain one JSON object { ... }")
    for k in data:
        if k not in TOP and not k.startswith("_"):
            print(f'[map] warning: unknown section "{k}" (ignored)')

    colors = data.get("colors", {})
    if not isinstance(colors, dict):
        raise MapError('"colors" must be an object like { "wall": [0.5, 0.5, 0.5] }')

    def section(name):
        items = data.get(name, [])
        if not isinstance(items, list):
            raise MapError(f'"{name}" must be a list [ ... ]')
        for i, item in enumerate(items):
            where = f"{name}[{i}]"
            _check_keys(item, name, where)
            yield where, item

    for where, it in section("floors"):
        x0, z0 = _vec(_need(it, "from", where), 2, where, "from")
        x1, z1 = _vec(_need(it, "to", where), 2, where, "to")
        world.floor(x0, z0, x1, z1, _rgb(colors, it.get("color", GREY), where), y=float(it.get("y", 0.0)))

    for where, it in section("ceilings"):
        x0, z0 = _vec(_need(it, "from", where), 2, where, "from")
        x1, z1 = _vec(_need(it, "to", where), 2, where, "to")
        world.ceiling(x0, z0, x1, z1, _rgb(colors, it.get("color", GREY), where), y=float(it.get("y", 3.0)))

    for where, it in section("walls"):
        a = _vec(_need(it, "from", where), 2, where, "from")
        b = _vec(_need(it, "to", where), 2, where, "to")
        height, thickness = float(it.get("height", 3.0)), float(it.get("thickness", 0.2))
        for n, (dx, dz) in enumerate(_offsets(it, where)):
            world.wall(a[0] + dx, a[1] + dz, b[0] + dx, b[1] + dz,
                       _pick_color(colors, it, n, where), height=height, thickness=thickness)

    for where, it in section("boxes"):
        x, y, z = _vec(_need(it, "pos", where), 3, where, "pos")
        size = tuple(_vec(_need(it, "size", where), 3, where, "size"))
        solid = bool(it.get("solid", True))
        for n, (dx, dz) in enumerate(_offsets(it, where)):
            world.box((x + dx, y, z + dz), size, _pick_color(colors, it, n, where), solid=solid)

    for where, it in section("doors"):
        hx, hz = _vec(_need(it, "hinge", where), 2, where, "hinge")
        direction = it.get("dir", "x")
        if direction not in ("x", "-x", "z", "-z"):
            raise MapError(f'{where}: "dir" must be "x", "-x", "z" or "-z"')
        for n, (dx, dz) in enumerate(_offsets(it, where)):
            world.add(Door((hx + dx, hz + dz), direction=direction,
                           swing=int(it.get("swing", 1)),
                           width=float(it.get("width", 1.0)),
                           height=float(it.get("height", 2.2)),
                           color=_rgb(colors, it.get("color", DOOR_BROWN), where),
                           key=it.get("key"),
                           start_open=bool(it.get("open", False))))

    for where, it in section("pickups"):
        x, y, z = _vec(_need(it, "pos", where), 3, where, "pos")
        item_id = _need(it, "item", where)
        world.add(Pickup((x, y, z), item=item_id, name=it.get("name"),
                         color=_rgb(colors, it.get("color", PICKUP_GOLD), where)))

    for where, it in section("entities"):
        name = _need(it, "type", where)
        if name not in TYPES:
            raise MapError(f'{where}: unknown entity type "{name}" (known: {", ".join(sorted(TYPES))})')
        try:
            world.add(TYPES[name](**it.get("args", {})))
        except TypeError as e:
            raise MapError(f'{where}: bad "args" for {name}: {e}') from None

    s = data.get("start", {})
    start = (float(s.get("x", 0.0)), float(s.get("z", 0.0)), float(s.get("yaw", 0.0)))
    f = data.get("fog", {})
    fog = (tuple(_vec(f.get("color", [0.02, 0.02, 0.03]), 3, "fog", "color")), float(f.get("density", 0.12)))
    ambient = tuple(_vec(data.get("ambient", [0.10, 0.10, 0.13]), 3, "map", "ambient"))
    return {"start": start, "fog": fog, "ambient": ambient}
