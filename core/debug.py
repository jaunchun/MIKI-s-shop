"""Debug tools and cheats. Loaded only when config.DEBUG is True.

Two ways in:
  * hotkeys F1-F8 in the game window
  * commands typed in the terminal that started the game (type `help`)
To add a command, add a method called cmd_<name>; its docstring is the help text.
"""
import os
import queue
import sys
import threading
import time

from entities.door import Door
from entities.pickup import Pickup

# The engine module only exports the game keys, so these are raw GLFW key codes.
F1, F2, F3, F4, F5, F6, F7, F8 = range(290, 298)

HOTKEYS = {
    F1: "info",
    F2: "noclip",
    F3: "god",
    F4: "fullbright",
    F5: "reload",
    F6: "unlock",
    F7: "fast",
    F8: "tp start",
}

INFO_EVERY = 1.0        # seconds between status lines when `info` is on


class Debug:
    def __init__(self, game):
        self.game = game
        self.timescale = 1.0
        self.show_info = False
        self._last_info = 0.0
        self._fps = 60.0
        self._lines = queue.Queue()
        threading.Thread(target=self._read_terminal, daemon=True).start()
        print("[debug] cheats are ON. Type 'help' in this terminal, or press F1-F8 in the game window.")

    # ------------------------------------------------------------------
    # called every frame by Game.run(); returns the (scaled) dt
    # ------------------------------------------------------------------
    def update(self, dt):
        inp = self.game.inp
        for key, command in HOTKEYS.items():
            if inp.key_pressed(key):
                self.run(command)

        while True:
            try:
                line = self._lines.get_nowait()
            except queue.Empty:
                break
            self.run(line)

        if dt > 0:
            self._fps += (1.0 / dt - self._fps) * 0.1
        if self.show_info:
            now = time.time()
            if now - self._last_info >= INFO_EVERY:
                self._last_info = now
                print(self._status())
        return dt * self.timescale

    def run(self, line):
        """Run one command line, e.g. 'tp 0 -10'. Never raises."""
        parts = line.split()
        if not parts:
            return
        fn = getattr(self, "cmd_" + parts[0].lower(), None)
        if fn is None:
            print(f"[debug] unknown command '{parts[0]}' - type help")
            return
        try:
            msg = fn(parts[1:])
        except Exception as e:
            msg = f"error: {e}"
        if msg:
            print(f"[debug] {msg}")

    def shutdown(self, code=0):
        # The terminal thread is blocked reading stdin; a normal exit can print a scary error.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code)

    # ------------------------------------------------------------------
    def _read_terminal(self):
        while True:
            try:
                line = input()
            except (EOFError, OSError, ValueError):
                return
            self._lines.put(line)

    def _status(self):
        g, p = self.game, self.game.player
        focus = type(g.world.focus).__name__ if g.world.focus is not None else "-"
        flags = [name for name, on in (("noclip", p.noclip), ("god", p.god),
                                       ("fullbright", g.fullbright),
                                       (f"speed x{p.speed_mult:g}", p.speed_mult != 1.0),
                                       (f"time x{self.timescale:g}", self.timescale != 1.0)) if on]
        return (f"[debug] x={p.x:6.2f} z={p.z:6.2f} yaw={p.yaw:6.1f} | {self._fps:3.0f} fps | "
                f"{len(g.world.entities)} entities | looking at: {focus} | {' '.join(flags) or 'no cheats'}")

    def _doors(self):
        return [e for e in self.game.world.entities if isinstance(e, Door)]

    # ------------------------------------------------------------------
    # commands
    # ------------------------------------------------------------------
    def cmd_help(self, args):
        """help - list all commands"""
        docs = [getattr(self, n).__doc__.strip() for n in sorted(dir(self)) if n.startswith("cmd_")]
        return "commands:\n  " + "\n  ".join(docs)

    def cmd_info(self, args):
        """info - toggle the status line (F1)"""
        self.show_info = not self.show_info
        return f"status line {'on' if self.show_info else 'off'}"

    def cmd_pos(self, args):
        """pos - print your position and angle"""
        p = self.game.player
        return f"x={p.x:.2f} y={p.eye + p.y_off:.2f} z={p.z:.2f} yaw={p.yaw:.1f} pitch={p.pitch:.1f}"

    def cmd_tp(self, args):
        """tp x z [yaw] | tp start - teleport (F8 = tp start)"""
        g = self.game
        if args and args[0] == "start":
            g.player.teleport(*g.start)
            return "back at the start"
        if len(args) < 2:
            return "usage: tp x z [yaw]   or   tp start"
        yaw = float(args[2]) if len(args) > 2 else None
        g.player.teleport(float(args[0]), float(args[1]), yaw)
        return f"teleported to {float(args[0]):g}, {float(args[1]):g}"

    def cmd_noclip(self, args):
        """noclip - fly through walls, Space up / Ctrl down (F2)"""
        p = self.game.player
        p.set_noclip(not p.noclip)
        return f"noclip {'on (Space up, Ctrl down)' if p.noclip else 'off'}"

    def cmd_god(self, args):
        """god - toggle god mode (F3)"""
        p = self.game.player
        p.god = not p.god
        return f"god mode {'on' if p.god else 'off'}"

    def cmd_speed(self, args):
        """speed <multiplier> - e.g. speed 2.5"""
        if not args:
            return f"speed is x{self.game.player.speed_mult:g}   (usage: speed 2.5)"
        self.game.player.speed_mult = max(0.1, min(20.0, float(args[0])))
        return f"speed x{self.game.player.speed_mult:g}"

    def cmd_fast(self, args):
        """fast - toggle 3x speed (F7)"""
        p = self.game.player
        p.speed_mult = 1.0 if p.speed_mult != 1.0 else 3.0
        return f"speed x{p.speed_mult:g}"

    def cmd_fullbright(self, args):
        """fullbright - everything lit, fog off (F4)"""
        g = self.game
        g.fullbright = not g.fullbright
        g.apply_look()
        return f"fullbright {'on' if g.fullbright else 'off'}"

    def cmd_give(self, args):
        """give <item> - add an item id, e.g. give classroom_key"""
        if not args:
            return "usage: give <item>"
        self.game.player.items.update(args)
        return "you now have: " + ", ".join(sorted(self.game.player.items))

    def cmd_take(self, args):
        """take <item> - remove an item id"""
        for a in args:
            self.game.player.items.discard(a)
        return "you now have: " + (", ".join(sorted(self.game.player.items)) or "nothing")

    def cmd_items(self, args):
        """items - list your items"""
        return "items: " + (", ".join(sorted(self.game.player.items)) or "none")

    def cmd_spawn(self, args):
        """spawn <item> [name] - drop a pickup in front of you"""
        if not args:
            return "usage: spawn <item> [name]"
        p = self.game.player
        fx, fz = p.forward()
        pos = (p.x + fx * 1.2, 1.0, p.z + fz * 1.2)
        self.game.world.add(Pickup(pos, item=args[0], name=" ".join(args[1:]) or args[0]))
        return f"spawned {args[0]}"

    def cmd_ents(self, args):
        """ents - list all entities"""
        lines = []
        for i, e in enumerate(self.game.world.entities):
            where = e.interact_point() if e.interactable else "-"
            if where != "-":
                where = f"({where[0]:.1f}, {where[1]:.1f})"
            lines.append(f"{i:3}  {type(e).__name__:<10} {where}")
        return f"{len(lines)} entities\n  " + "\n  ".join(lines)

    def cmd_open(self, args):
        """open - open every door"""
        doors = self._doors()
        for d in doors:
            d.open = True
        return f"opened {len(doors)} doors"

    def cmd_close(self, args):
        """close - close every door"""
        doors = self._doors()
        for d in doors:
            d.open = False
        return f"closed {len(doors)} doors"

    def cmd_unlock(self, args):
        """unlock - unlock every door (F6)"""
        doors = [d for d in self._doors() if d.key is not None]
        for d in doors:
            d.key = None
        return f"unlocked {len(doors)} doors"

    def cmd_reload(self, args):
        """reload - reload the current map, keep your position (F5)"""
        self.game.reload_map()

    def cmd_map(self, args):
        """map <file> - load another map, e.g. map maps/test_room.json"""
        if not args:
            return f"current map: {self.game.map_path}   (usage: map maps/test_room.json)"
        self.game.load_map(args[0])

    def cmd_time(self, args):
        """time <scale> - slow motion or speed-up, e.g. time 0.2 (1 = normal)"""
        if not args:
            return f"time scale is {self.timescale:g}   (usage: time 0.2)"
        self.timescale = max(0.0, min(5.0, float(args[0])))
        return f"time scale {self.timescale:g}"

    def cmd_quit(self, args):
        """quit - close the game"""
        self.game.app.quit()
