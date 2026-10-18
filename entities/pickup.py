import math

from entities.entity import Entity


class Pickup(Entity):
    """A small spinning block lying around. E picks it up and adds `item` to player.items."""

    interactable = True

    def __init__(self, pos, item, name=None, color=(0.9, 0.75, 0.1), size=0.25):
        super().__init__()
        self.pos = pos                  # (x, y, z)
        self.item = item                # id other code checks for, e.g. "classroom_key"
        self.name = name or item        # text shown to the player
        self.color = color
        self.size = size
        self.obj = None
        self.time = 0.0

    def on_spawn(self):
        self.obj = self.r.create_object(self.world.cube, self.color)
        self._apply()

    def on_remove(self):
        self.r.destroy_object(self.obj)

    def _apply(self):
        x, y, z = self.pos
        bob = 0.05 * math.sin(self.time * 2.0)
        s = self.size
        self.r.set_transform(self.obj, (x, y + bob, z), (0, self.time * 60.0, 0), (s, s, s))

    def update(self, dt, player):
        self.time += dt
        self._apply()

    def interact_point(self):
        return (self.pos[0], self.pos[2])

    def prompt(self):
        return f"pick up {self.name}"

    def interact(self, player):
        player.items.add(self.item)
        self.world.say(f"You picked up: {self.name}")
        self.destroy()
