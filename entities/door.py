import math

from entities.entity import Entity

_DIRS = {"x": (1, 0), "-x": (-1, 0), "z": (0, 1), "-z": (0, -1)}


def _rot(vx, vz, a):
    """Rotate a floor vector around the vertical axis the same way the renderer does."""
    c, s = math.cos(a), math.sin(a)
    return vx * c + vz * s, -vx * s + vz * c


class Door(Entity):
    """A hinged door. Press E to open or close it. Optionally locked with a key id.

    hinge      (x, z) of the hinge
    direction  where the CLOSED door points from the hinge: "x", "-x", "z" or "-z"
    swing      +1 or -1: which way it swings. If it swings into the wall, flip it.
    key        item id the player must carry to unlock it (None = not locked)
    """

    interactable = True

    def __init__(self, hinge, direction="x", swing=1, width=1.0, height=2.2,
                 thickness=0.08, color=(0.32, 0.18, 0.08), open_angle=100.0,
                 duration=0.6, key=None, start_open=False):
        super().__init__()
        self.hinge = hinge
        self.ux, self.uz = _DIRS[direction]
        self.swing = 1 if swing >= 0 else -1
        self.width, self.height, self.thickness = width, height, thickness
        self.color = color
        self.open_angle = open_angle
        self.duration = duration
        self.key = key
        self.open = start_open
        self.t = 1.0 if start_open else 0.0     # 0 = closed, 1 = fully open
        self.obj = None

        if self.ux != 0:
            self._size = (width, height, thickness)
        else:
            self._size = (thickness, height, width)

        # box that blocks the doorway while the door is (nearly) closed
        hx, hz = hinge
        x0, x1 = sorted((hx, hx + self.ux * width))
        z0, z1 = sorted((hz, hz + self.uz * width))
        if self.ux == 0:
            x0, x1 = x0 - thickness / 2, x1 + thickness / 2
        if self.uz == 0:
            z0, z1 = z0 - thickness / 2, z1 + thickness / 2
        self._closed_box = (x0, z0, x1, z1)

    # ---- lifecycle ----
    def on_spawn(self):
        self.obj = self.r.create_object(self.world.cube, self.color)
        self._apply()

    def on_remove(self):
        self.r.destroy_object(self.obj)

    def _angle_deg(self):
        ease = self.t * self.t * (3 - 2 * self.t)       # smooth start and stop
        return self.open_angle * ease

    def _apply(self):
        a = math.radians(self._angle_deg()) * self.swing
        ox, oz = _rot(self.ux, self.uz, a)
        cx = self.hinge[0] + ox * self.width / 2
        cz = self.hinge[1] + oz * self.width / 2
        self.r.set_transform(self.obj, (cx, self.height / 2, cz),
                             (0, math.degrees(a), 0), self._size)

    def update(self, dt, player):
        target = 1.0 if self.open else 0.0
        if self.t == target:
            return
        step = dt / self.duration
        if target > self.t:
            self.t = min(target, self.t + step)
        else:
            self.t = max(target, self.t - step)
        self._apply()

    def collider(self):
        return self._closed_box if self._angle_deg() < 15.0 else None

    # ---- interaction ----
    def interact_point(self):
        return (self.hinge[0] + self.ux * self.width / 2,
                self.hinge[1] + self.uz * self.width / 2)

    def prompt(self):
        if self.key is not None:
            return "locked door"
        return "close door" if self.open else "open door"

    def _blocked_by(self, player):
        x0, z0, x1, z1 = self._closed_box
        m = player.RADIUS + 0.05
        return x0 - m < player.x < x1 + m and z0 - m < player.z < z1 + m

    def interact(self, player):
        if self.key is not None:
            if self.key in player.items:
                self.key = None
                self.world.say("You unlock the door.")
            else:
                self.world.say("It's locked.")
                return
        if self.open:
            if self._blocked_by(player):
                self.world.say("You're standing in the doorway.")
                return
            self.open = False
        else:
            self.open = True
