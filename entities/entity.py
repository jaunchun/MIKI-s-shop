class Entity:
    """Base class for everything in the world that is not plain map geometry."""

    interactable = False    # True: the player can target it and press E
    reach = 1.8             # how close (metres) the player must be to interact

    def __init__(self):
        self.world = None
        self.alive = True

    @property
    def r(self):
        """The renderer (only valid after the entity has been added to a world)."""
        return self.world.r

    # ---- lifecycle hooks: override what you need ----
    def on_spawn(self):
        """Called by world.add(). Create your renderer objects here."""

    def on_remove(self):
        """Call ed when the entity is removed. Destroy your renderer objects here."""

    def update(self, dt, player):
        """Called every frame."""

    def collider(self):
        """Return a box (x0, z0, x1, z1) the player cannot walk through, or None."""
        return None

    # ---- interaction ----
    def interact_point(self):
        """(x, z) used to measure distance and facing for interaction."""
        return (0.0, 0.0)

    def prompt(self):
        """Short text shown as '[E] <prompt>' while the player looks at it."""
        return "use"

    def interact(self, player):
        """Called when the player presses E while looking at this entity."""

    def destroy(self):
        self.world.remove(self)
