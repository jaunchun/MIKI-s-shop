import math

from entities.entity import Entity


class Patroller(Entity):
    """A red block that walks between points: a stand-in for a monster.
    points = [[x, z], [x, z], ...]   it loops through them forever."""

    def __init__(self, points, speed=1.2, color=(0.9, 0.05, 0.05)):
        super().__init__()
        self.points = points
        self.speed = speed
        self.color = color
        self.i = 0
        self.x, self.z = points[0]
        self.caught = False
        self.obj = None

    def on_spawn(self):
        self.obj = self.r.create_object(self.world.cube, self.color)
        self._apply()

    def on_remove(self):
        self.r.destroy_object(self.obj)

    def _apply(self):
        self.r.set_transform(self.obj, (self.x, 0.9, self.z), (0, 0, 0), (0.6, 1.8, 0.6))

    def update(self, dt, player):
        tx, tz = self.points[self.i]
        dx, dz = tx - self.x, tz - self.z
        d = math.hypot(dx, dz)
        step = self.speed * dt
        if d <= step:
            self.x, self.z = tx, tz
            self.i = (self.i + 1) % len(self.points)
        else:
            self.x += dx / d * step
            self.z += dz / d * step
        self._apply()

        dist = math.hypot(player.x - self.x, player.z - self.z)
        if dist < 0.8 and not self.caught and not player.god:
            self.caught = True
            self.world.say("It got you.")
        elif dist > 2.0:
            self.caught = False
