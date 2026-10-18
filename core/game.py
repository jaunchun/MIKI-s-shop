"""The Game ties everything together: window, world, player, debug tools, main loop."""
import os
import sys

import engine

import config
from core.controls import Controls
from core.mapload import MapError, build_map, read_map
from core.world import World
from entities.player import Player


def resolve(path):
    """Paths are relative to the project folder, unless they are absolute."""
    return path if os.path.isabs(path) else os.path.join(config.ROOT, path)


class Game:
    def __init__(self):
        self.app = engine.Application(config.WINDOW_W, config.WINDOW_H, config.TITLE)
        self.renderer = self.app.renderer
        self.inp = self.app.input
        self.controls = Controls(self.inp)
        self.world = World(self.renderer)
        self.player = Player(self.controls)

        self.map_path = config.MAP
        self.fog = ((0.02, 0.02, 0.03), 0.12)
        self.ambient = (0.10, 0.10, 0.13)
        self.start = (0.0, 0.0, 0.0)
        self.fullbright = False          # toggled by the debug tools

        if not self.load_map(self.map_path):
            raise MapError("could not load the starting map (see the message above)")

        self.debug = None
        if config.DEBUG:
            from core.debug import Debug     # only imported in debug mode
            self.debug = Debug(self)

        self.inp.set_cursor_locked(True)

    # ------------------------------------------------------------------
    def load_map(self, path, keep_position=False):
        """Read a map file and rebuild the world. Returns True on success."""
        path = resolve(path)
        try:
            data = read_map(path)            # syntax errors stop here: the old map stays
        except MapError as e:
            print(f"[map] {e}")
            return False
        self.world.clear()
        try:
            info = build_map(self.world, data)
        except MapError as e:
            print(f"[map] {e}  (fix the file, then reload)")
            return False
        self.map_path = path
        self.fog, self.ambient, self.start = info["fog"], info["ambient"], info["start"]
        if not keep_position:
            self.player.teleport(*self.start)
        self.apply_look()
        print(f"[map] loaded {os.path.basename(path)}")
        return True

    def reload_map(self):
        return self.load_map(self.map_path, keep_position=True)

    def apply_look(self):
        """Send fog and ambient light to the renderer (full-bright cheat included)."""
        fog_color, density = self.fog
        ambient = self.ambient
        if self.fullbright:
            ambient, density = (0.9, 0.9, 0.9), 0.0
        self.renderer.set_fog(fog_color, density)
        self.renderer.set_ambient(ambient)

    # ------------------------------------------------------------------
    def run(self):
        app, c, player, world = self.app, self.controls, self.player, self.world
        while app.running():
            dt = app.begin_frame()
            if self.debug:
                dt = self.debug.update(dt)

            if c.pressed("pause"):                       # Esc: free / lock the mouse
                self.inp.set_cursor_locked(not self.inp.cursor_locked)
            if c.pressed("inventory"):
                print("[ui] items:", sorted(player.items) or "none")

            if self.inp.cursor_locked:                   # Esc = pause: nothing updates
                player.update(dt, world)
                world.update(dt, player)

            player.apply(self.renderer)
            app.end_frame()

    def shutdown(self, code=0):
        if self.debug:
            self.debug.shutdown(code)        # does not return
        sys.exit(code)
