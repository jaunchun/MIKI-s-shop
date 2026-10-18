"""The World: owns the map geometry, the colliders and every entity."""
import math


class World:
    def __init__(self, renderer):
        self.r = renderer
        self.cube = renderer.load_mesh("cube")
        self.plane = renderer.load_mesh("plane")
        self.solids = []        # static colliders: (x0, z0, x1, z1)
        self.entities = []
        self.objects = []       # renderer objects made by box/floor (so clear() can remove them)
        self.focus = None       # the entity the player is currently looking at

    # ------------------------------------------------------------------
    # map building
    # ------------------------------------------------------------------
    def box(self, center, size, color, solid=True):
        """Axis-aligned box. center=(x, y, z), size=(width, height, depth).
        solid=True also makes it a wall the player cannot walk through."""
        obj = self.r.create_object(self.cube, color)
        self.r.set_transform(obj, center, (0, 0, 0), size)
        self.objects.append(obj)
        if solid:
            cx, _, cz = center
            sx, _, sz = size
            self.solids.append((cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2))
        return obj

    def wall(self, x0, z0, x1, z1, color, height=3.0, thickness=0.2):
        """Straight wall along X or Z, centred on the line between the two points.
        Runs along X when the X distance is larger (z0 is used), otherwise along Z (x0 is used)."""
        if abs(x1 - x0) >= abs(z1 - z0):
            center = ((x0 + x1) / 2, height / 2, z0)
            size = (abs(x1 - x0), height, thickness)
        else:
            center = (x0, height / 2, (z0 + z1) / 2)
            size = (thickness, height, abs(z1 - z0))
        return self.box(center, size, color)

    def floor(self, x0, z0, x1, z1, color, y=0.0):
        """Flat floor between two corners at height y (not solid, you just walk on it)."""
        obj = self.r.create_object(self.plane, color)
        self.r.set_transform(obj, ((x0 + x1) / 2, y, (z0 + z1) / 2), (0, 0, 0),
                             (abs(x1 - x0), 1, abs(z1 - z0)))
        self.objects.append(obj)
        return obj

    def ceiling(self, x0, z0, x1, z1, color, y=3.0):
        """Thin slab whose underside is at height y (not solid)."""
        return self.box(((x0 + x1) / 2, y + 0.05, (z0 + z1) / 2),
                        (abs(x1 - x0), 0.1, abs(z1 - z0)), color, solid=False)

    def clear(self):
        """Remove the whole map and every entity (used when reloading a map)."""
        for e in list(self.entities):
            self.remove(e)
        for obj in self.objects:
            self.r.destroy_object(obj)
        self.objects.clear()
        self.solids.clear()
        self.focus = None

    # ------------------------------------------------------------------
    # entities
    # ------------------------------------------------------------------
    def add(self, entity):
        entity.world = self
        entity.alive = True
        entity.on_spawn()
        self.entities.append(entity)
        return entity

    def remove(self, entity):
        if entity in self.entities:
            entity.alive = False
            entity.on_remove()
            self.entities.remove(entity)
            if self.focus is entity:
                self.focus = None

    def update(self, dt, player):
        for e in list(self.entities):       # copy: entities may remove themselves
            if e.alive:
                e.update(dt, player)
        self._update_focus(player)

    def colliders(self):
        """Every box the player can bump into this frame: static walls + entity colliders."""
        boxes = list(self.solids)
        for e in self.entities:
            box = e.collider()
            if box is not None:
                boxes.append(box)
        return boxes

    # ------------------------------------------------------------------
    # interaction (the E key)
    # ------------------------------------------------------------------
    def _update_focus(self, player):
        fx, fz = player.forward()
        best, best_d = None, float("inf")
        for e in self.entities:
            if not e.interactable:
                continue
            ex, ez = e.interact_point()
            dx, dz = ex - player.x, ez - player.z
            d = math.hypot(dx, dz)
            if d > e.reach:
                continue
            if d > 0.6 and (dx * fx + dz * fz) / d < 0.5:   # must be roughly in front of you
                continue
            if d < best_d:
                best, best_d = e, d
        if best is not self.focus:
            self.focus = best
            if best is not None:
                self.say(f"[E] {best.prompt()}")

    def interact(self, player):
        if self.focus is not None and self.focus.alive:
            self.focus.interact(player)
            self.focus = None       # makes the prompt refresh on the next frame

    def say(self, text):
        """Messages to the player. Prints for now; hook a HUD up here later."""
        print(f"[game] {text}")
