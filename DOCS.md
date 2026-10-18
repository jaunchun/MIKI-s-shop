# MIKI's shop - Game Guide

A low-poly horror game. **C++** draws everything (window, input, OpenGL renderer).
**Python** is the game itself (player, doors, enemies, map loading, debug tools).
Maps are plain **JSON** files, so you can change the level without touching code and without rebuilding.

## Contents
1. [Quick start](#1-quick-start)
2. [How the project is organised](#2-how-the-project-is-organised)
3. [Coordinates and units](#3-coordinates-and-units)
4. [Building the map (JSON)](#4.%20Building%20the%20map%20%28JSON%29)
5. [Entities (doors, pickups, enemies...)](#5-entities)
6. [Player and controls](#6-player-and-controls)
7. [Debug and cheats](#7-debug-and-cheats)
8. [Look and feel](#8-look-and-feel)
9. [Changing the C++ engine](#9-changing-the-c-engine)
10. [Troubleshooting](#10-troubleshooting)
11. [Working with a friend](#11-working-with-a-friend)
12. [Ideas for next steps](#12-ideas-for-next-steps)

---

## 1. Quick start

**Build the engine once** (turns the C++ into `engine.pyd`), then run the game:

1. Open the project folder in CLion, **Tools > CMake > Reload CMake Project**.
2. Pick the **`engine`** target, click the hammer (Build).
3. In the terminal (with the venv active): `python main.py`

**What needs a rebuild?**

| You changed | Rebuild? |
|---|---|
| a `.json` map, any `.py` file, `config.py` | **No.** Just run again (maps can even reload live, see F5) |
| anything in `engine/`, `input/`, `render/` (C++) | **Yes**, click Build, then restart the game |

**Controls**

| Key | Action |
|---|---|
| W A S D + mouse | move and look |
| Shift / Ctrl | sprint / crouch |
| Space | jump |
| E | interact (open doors, pick things up) |
| F | flashlight |
| 1-4 or mouse wheel | inventory slot |
| Left mouse | use item (placeholder) |
| Tab | print your items in the terminal |
| Esc | pause (frees the mouse, freezes the world) |

There is no on-screen text yet. Messages like `[E] open door` appear in the **terminal** you started the game from.

---

## 2. How the project is organised

```
MIKI-s-shop/
├─ config.py              settings: debug on/off, which map, window size
├─ main.py                starts the game
├─ maps/
│  ├─ school.json         the main level (edit me!)
│  └─ test_room.json      tiny two-room map with a locked door, good for testing
├─ core/
│  ├─ game.py             main loop, loads maps, ties everything together
│  ├─ world.py            map-building helpers, entities, collision, E-key targeting
│  ├─ mapload.py          reads a JSON map into the world
│  ├─ controls.py         key bindings (action name -> key)
│  └─ debug.py            cheats and debug tools
├─ entities/
│  ├─ entity.py           base class for everything that is not plain geometry
│  ├─ player.py
│  ├─ door.py  pickup.py  patroller.py
│  └─ registry.py         entity names a map can use: {"type": "Patroller"}
├─ engine/  input/  render/   the C++ engine (rebuild after editing)
├─ CMakeLists.txt
└─ engine.pyi             list of everything the C++ module offers (autocomplete)
```

**One frame of the game** (`Game.run()` in `core/game.py`):

```
app.begin_frame()      C++: poll keys and mouse, returns dt (seconds since last frame)
debug.update(dt)       hotkeys + commands typed in the terminal (debug only)
player.update(dt)      look, move, collide, handle E and other keys
world.update(dt)       every entity.update(), then "what is the player looking at?"
player.apply()         send the camera to the renderer
app.end_frame()        C++: draw the scene, swap buffers
```

Pause (Esc) skips the `player.update` / `world.update` lines, so everything freezes.

---

## 3. Coordinates and units

- **1 unit = 1 metre.**
- **Y is up.** The floor is `y = 0`. Walls are 3 high by default. The eye is at 1.65.
- On the floor plane you use **X** (left/right) and **Z**. At `yaw = 0` the player looks toward **-Z**.
  Positive yaw turns right. So "forward" in the starting direction means Z getting more negative.
- Boxes are placed by their **centre**. A box that sits on the floor has `y = height / 2`.
- Everything is axis-aligned (walls run along X or Z only). Collision is 2D (X and Z).

---

## 4. Building the map (JSON)

A map is one `.json` file in `maps/`. The game builds it when it starts (or when you reload).

### The smallest map

Save as `maps/mini.json`, then run `map maps/mini.json` in the debug terminal (or set `MAP` in `config.py`):

```json
{
  "start": { "x": 0, "z": 0, "yaw": 0 },
  "colors": { "wall": [0.45, 0.42, 0.36], "floor": [0.30, 0.28, 0.25] },
  "floors": [ { "from": [-3, -3], "to": [3, 3], "color": "floor" } ],
  "walls": [
    { "from": [-3, 3],  "to": [3, 3],  "color": "wall" },
    { "from": [-3, -3], "to": [3, -3], "color": "wall" },
    { "from": [-3, -3], "to": [-3, 3], "color": "wall" },
    { "from": [3, -3],  "to": [3, 3],  "color": "wall" }
  ]
}
```

### All sections

Every section is optional. Fields marked * are required.

| Section | What it makes | Fields |
|---|---|---|
| `name` | a label (ignored) | text |
| `start` | where the player spawns | `x`, `z`, `yaw` (degrees) |
| `fog` | distance fog | `color` [r,g,b], `density` (0.12 default, higher = thicker) |
| `ambient` | base light level when the flashlight is off | [r,g,b], default `[0.10, 0.10, 0.13]` |
| `colors` | named colours to reuse | `"name": [r, g, b]` |
| `floors` | flat floor | `from`* `to`* (corners `[x, z]`), `y` (0), `color` |
| `ceilings` | flat ceiling (underside at `y`) | `from`* `to`*, `y` (3), `color` |
| `walls` | a straight wall along X or Z | `from`* `to`* (`[x, z]`), `height` (3), `thickness` (0.2), `color`, `alt_color`, `repeat` |
| `boxes` | any block: desks, lockers, pillars | `pos`* (`[x, y, z]` centre), `size`* (`[w, h, d]`), `color`, `alt_color`, `solid` (true), `repeat` |
| `doors` | an openable door | `hinge`* (`[x, z]`), `dir` ("x" "-x" "z" "-z"), `swing` (1 or -1), `width` (1), `height` (2.2), `key`, `open` (false), `color`, `repeat` |
| `pickups` | an item you can pick up with E | `pos`* (`[x, y, z]`), `item`* (id text), `name`, `color` |
| `entities` | any custom entity by name | `type`*, `args` (see section 5) |

**Colours** are `[red, green, blue]`, each from 0 to 1. Write a name from `"colors"` or the three numbers directly: `"color": "wall"` or `"color": [0.5, 0.1, 0.1]`.

**Walls** run along whichever axis the two points are further apart on. They are **centred on the line** you give, so a wall with thickness 0.2 sticks out 0.1 to each side of it. Walls always have collision.

**Boxes** have collision unless you set `"solid": false` (use that for decoration like a blackboard, or a lintel above a door).

**Notes inside the file:** JSON has no comments. Start any key with an underscore and it is ignored, e.g. `"_note": "classroom 2"`.

**Typos:** unknown sections or fields print a warning in the terminal (`unknown field "colour"`) instead of being silently ignored. Wrong values stop the load with a message that names the section, e.g. `walls[3] is missing "to"`.

### `repeat`: lots of the same thing

Add `repeat` to copy a wall, box or door. `step` is `[dx, dz]` per copy.

```json
{ "pos": [1.25, 1.0, -1.5], "size": [0.5, 2.0, 1.0],
  "color": "locker_a", "alt_color": "locker_b",
  "repeat": { "count": 18, "step": [0, -1.2] } }
```

That is 18 lockers, one every 1.2 m along -Z, colours alternating. `alt_color` is used for every second copy.

A **list** of repeats makes a grid (each entry multiplies the one before):

```json
"repeat": [ { "count": 4, "step": [0, -5] },     // 4 rooms, 5 m apart
            { "count": 3, "step": [0, 1.5] },    // 3 rows of desks per room
            { "count": 2, "step": [-1.5, 0] } ]  // 2 columns
```

(Comments are shown above for explanation only. Remove them in the real file.)

### Doors

A door needs three things: a **gap** in the wall, a **hinge**, and a **lintel**.

1. **Cut the gap.** Split the wall into two pieces with a hole exactly as wide as the door (default 1.0).
   For a gap from z = -4.5 to z = -3.5 in the wall at x = -1.5:
   walls `[-1.5, 0] -> [-1.5, -3.5]` and `[-1.5, -4.5] -> [-1.5, -24]`.
2. **Place the hinge** at one end of the gap: `"hinge": [-1.5, -3.5]`.
3. **Point it across the gap** with `dir`: the direction the closed door extends from the hinge.
   From z = -3.5 to z = -4.5 is toward -Z, so `"dir": "-z"`.
4. **Pick the swing** so it opens into the room, not into the wall (table below). If it looks wrong, flip `swing` between 1 and -1.
5. **Add a lintel**, the strip of wall above the door (doors are 2.2 high, walls 3), or you will see a hole:
   `{ "pos": [-1.5, 2.6, -4], "size": [0.2, 0.8, 1.0], "color": "wall", "solid": false }`.
   It must be `"solid": false` or it blocks the doorway.

Which way does it open? (the free end of the door swings toward...)

| `dir` | `swing: 1` | `swing: -1` |
|---|---|---|
| "x"  | -Z | +Z |
| "-x" | +Z | -Z |
| "z"  | +X | -X |
| "-z" | -X | +X |

**Locked doors:** `"key": "classroom_key"`. The door stays locked until the player carries an item with that exact id. Items come from `pickups` (the `item` field) or the `give` debug command.

**Behaviour:** E opens or closes a door you are facing within 1.8 m. A door only blocks you when it is nearly closed. You can't close it while you are standing in the doorway.

### Example: two rooms and a locked door

`maps/test_room.json` is a finished example: start in room A, find the key on the table, unlock the door, enter room B.

### Walk-through: add a new classroom to `school.json`

1. Add 5 m of room behind the left wall: a divider wall (`from [-9.5, -26] to [-1.5, -26]`) and extend the back wall and floor/ceiling `from` corners.
2. Move the hallway's far end further out (the end wall and the right wall), or put the room on the other side.
3. Cut a 1 m gap in the hallway wall, add a door (`hinge`, `dir`, `swing`) and a lintel.
4. Add furniture with `boxes`, using `"solid": false` for anything flat on a wall.
5. Save, switch to the game, **press F5** (reload). If the map has a mistake, the terminal tells you where.

### Tips and common mistakes

- **Sit things on the floor:** `pos.y` is the centre, so use half of `size.h`.
- **Rooms are 0.1 m smaller than the coordinates** because walls are centred on their line.
- **No trailing commas** in JSON (`[1, 2, ]` is an error) and use a **dot** for decimals.
- **Walk through a wall?** It is probably a box with `"solid": false`.
- **Can't walk through a doorway?** The lintel is solid, or the gap is narrower than the door (the player is 0.6 m wide).
- **Need loops, randomness or generated rooms?** `World` has the same builders in Python (`world.box`, `wall`, `floor`, `ceiling`, `add`). Write a function that takes the world and call it from `Game.load_map` after `build_map(...)`.

### Live editing

Keep the game running, edit and save the JSON, click the game window and press **F5** (or type `reload` in the terminal). The map rebuilds and you stay where you are. If the JSON has a syntax error the old map stays and the error tells you the line and column.

### Switching maps

Type `map maps/test_room.json` in the terminal, or set `MAP` in `config.py`. Paths are relative to the project folder.

---

## 5. Entities

An **entity** is anything in the world that is not plain geometry and that has behaviour: doors, pickups, monsters, lights that flicker, buttons. Entities live in `entities/` and are added to the world with `world.add(...)` (the map loader does this for you).

### How an entity works

Every entity extends `Entity` (`entities/entity.py`) and overrides what it needs:

| Member | When it runs | What to do there |
|---|---|---|
| `on_spawn()` | once, when added to the world | create renderer objects: `self.r.create_object(self.world.cube, color)` |
| `update(dt, player)` | every frame | move, animate, think |
| `collider()` | every frame, for player collision | return a box `(x0, z0, x1, z1)` or `None` |
| `on_remove()` | when removed | destroy your renderer objects |
| `interactable` | class attribute | `True` = the player can target it and press E |
| `reach` | class attribute | how close the player must be (metres, 1.8) |
| `interact_point()` | when targeting | `(x, z)` used for distance and facing |
| `prompt()` | when targeted | text shown as `[E] <prompt>` |
| `interact(player)` | player pressed E on it | do the thing |

Useful things inside an entity:

- `self.r` is the renderer. `self.world.cube` is the cube mesh to build visuals from.
- `self.world.say("text")` shows a message to the player (the terminal for now).
- `self.destroy()` removes the entity.
- `player.items` is a set of item ids; `player.x`, `player.z`, `player.god`.

### Built-in entities

- **Door** (`entities/door.py`): hinged, animated, can be locked. Extra Python-only settings: `open_angle` (100), `duration` (0.6 s), `thickness`.
- **Pickup** (`entities/pickup.py`): a small spinning block. E adds its `item` id to `player.items` and removes it.
- **Patroller** (`entities/patroller.py`): a red block that walks between points. A stand-in for a monster; respects god mode.

### Make your own: a walkthrough

Goal: a red block that walks back and forth (this is `entities/patroller.py`).

**1. Create `entities/patroller.py`:**

```python
import math

from entities.entity import Entity


class Patroller(Entity):
    def __init__(self, points, speed=1.2, color=(0.7, 0.05, 0.05)):
        super().__init__()
        self.points = points          # [[x, z], [x, z], ...]
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
```

**2. Register the name** in `entities/registry.py` so maps can use it:

```python
from entities.patroller import Patroller
TYPES = {"Door": Door, "Pickup": Pickup, "Patroller": Patroller}
```

**3. Put it in a map** with the `entities` section. `args` become the constructor arguments:

```json
"entities": [
  { "type": "Patroller", "args": { "points": [[0, -6], [0, -20]], "speed": 1.2 } }
]
```

**4. Save and press F5.** To remove it, delete that line.

You can also add one from Python without a map: `world.add(Patroller([[0, -6], [0, -20]]))`.

### An interactable entity (a light switch, say)

```python
class Switch(Entity):
    interactable = True
    def __init__(self, pos):
        super().__init__()
        self.pos, self.on = pos, False
    def interact_point(self):
        return (self.pos[0], self.pos[1])           # (x, z)
    def prompt(self):
        return "turn off" if self.on else "turn on"
    def interact(self, player):
        self.on = not self.on
        self.world.say("Click.")
```

### An entity that blocks the player (a crate)

```python
def collider(self):
    return (self.x - 0.4, self.z - 0.4, self.x + 0.4, self.z + 0.4)   # x0, z0, x1, z1
```

### Rules of thumb

- Create renderer objects in `on_spawn`, never in `__init__` (the renderer isn't connected yet).
- Destroy them in `on_remove` or they stay on screen forever.
- Keep `update` cheap; it runs every frame for every entity.
- Rotation (`set_transform`'s 2nd argument) is in **degrees**, applied Y then X then Z.

---

## 6. Player and controls

**Tuning the player:** the constants at the top of `entities/player.py`.

| Constant | Meaning | Default |
|---|---|---|
| `SENS` | mouse sensitivity (degrees per mouse count) | 0.09 |
| `WALK`, `SPRINT`, `CROUCH` | speeds (m/s) | 2.5, 4.5, 1.2 |
| `EYE`, `EYE_CROUCH` | eye height (m) | 1.65, 1.0 |
| `RADIUS` | collision size (m) | 0.3 |
| `SLOTS` | inventory slots | 4 |

**Rebinding keys:** `BINDINGS` in `core/controls.py` maps an action name to a key. Change the key, nothing else:

```python
"flashlight": e.KEY_F,     # becomes  e.KEY_E, etc.
```

**Adding a new action:**

```python
# core/controls.py
BINDINGS["reload"] = ord("R")        # a raw key code, no rebuild needed
# anywhere in game code:
if controls.pressed("reload"): ...
```

The engine module exports only the keys the game uses (`KEY_W A S D E F TAB CTRL SPACE SHIFT ESC 1-4`, `M_LEFT`, `M_RIGHT`). For any other key, pass a raw GLFW key code:

| Keys | Code |
|---|---|
| letters | uppercase ASCII, `ord("R")` = 82 |
| digits | `ord("5")` = 53 |
| Space | 32 |
| Esc / Enter / Tab / Backspace | 256 / 257 / 258 / 259 |
| Right / Left / Down / Up arrows | 262 / 263 / 264 / 265 |
| F1 ... F12 | 290 ... 301 |
| Left Shift / Ctrl / Alt | 340 / 341 / 342 |

Codes must be below 350. (Prefer exporting a named constant in `engine/module.cpp` if lots of code uses the key.)

**Mouse:** `controls.primary_pressed()` (left), `secondary_held()` (right), `look()`, `scroll()`.

---

## 7. Debug and cheats

Controlled by `DEBUG` in `config.py`. Set it to `False` for a release: no cheats, no debug keys, no terminal commands (the debug file isn't even loaded).

There are two ways in:

- **Hotkeys** in the game window (laptops may need Fn).
- **Commands** typed in the **terminal that started the game**. Click that terminal, type, press Enter. The game keeps running; click back on the game window to continue. Commands also work while paused.

### Hotkeys

| Key | Same as command | Effect |
|---|---|---|
| F1 | `info` | print a status line every second |
| F2 | `noclip` | fly through walls (Space up, Ctrl down) |
| F3 | `god` | god mode (for your own enemies, the Patroller respects it) |
| F4 | `fullbright` | everything lit, fog off |
| F5 | `reload` | reload the current map, keep your position |
| F6 | `unlock` | unlock every door |
| F7 | `fast` | toggle 3x speed |
| F8 | `tp start` | back to the spawn point |

### Commands

| Command | Effect |
|---|---|
| `help` | list all commands |
| `info` | toggle the status line (position, fps, entity count, what you're looking at, active cheats) |
| `pos` | print your position and angle |
| `tp x z [yaw]` / `tp start` | teleport |
| `noclip` | toggle fly through walls |
| `god` | toggle god mode |
| `speed <multiplier>` | e.g. `speed 2.5` |
| `fast` | toggle 3x speed |
| `fullbright` | toggle full light, fog off |
| `give <item>` | add an item id, e.g. `give classroom_key` |
| `take <item>` | remove an item id |
| `items` | list your items |
| `spawn <item> [name]` | drop a pickup in front of you |
| `ents` | list all entities |
| `open` / `close` / `unlock` | affect every door |
| `reload` | reload the current map |
| `map <file>` | load another map, e.g. `map maps/test_room.json` |
| `time <scale>` | slow motion or speed-up, e.g. `time 0.2` (1 = normal) |
| `quit` | close the game |

A typo or bad argument prints an error and never crashes the game.

### Adding your own command

In `core/debug.py` add a method named `cmd_<name>`. The first line of its docstring is the help text. Return a string to print it:

```python
def cmd_heal(self, args):
    """heal - restore health"""
    self.game.player.health = 100
    return "healed"
```

Then type `heal`. To bind a hotkey, add a line to `HOTKEYS` (key code -> command text).

**Why the game exits oddly:** the terminal listener runs in a background thread. When the game closes, `Debug.shutdown` ends the process directly. This avoids a Python error about a blocked stdin on exit. It is normal.

---

## 8. Look and feel

**In the map JSON** (no rebuild): `fog.color`, `fog.density`, `ambient`.

**In C++ (rebuild needed)**, all in `render/renderer.cpp` unless noted:

| Want | Where |
|---|---|
| chunkier or sharper pixels | `kLowW` / `kLowH` in `engine/application.cpp` (320 x 240 now; smaller = chunkier) |
| less vertex wobble | in `kSceneVS`: delete the `ndc.xy = round(...)` line. More wobble: change `uRes * 0.5` to `uRes * 0.25` (both places in that line) |
| flashlight cone | `smoothstep(0.82, 0.93, cosAng)` in `kSceneFS`: closer to 1.0 = narrower |
| flashlight strength / range | `* 1.8` (strength) and the `atten` line (range) in `kSceneFS` |
| colour banding and dither | the two `32.0` values in `kPostFS`; lower = more banded |
| vignette | `smoothstep(0.35, 0.85, ...)` and `mix(0.45, 1.0, v)` in `kPostFS` |
| field of view | `glm::radians(70.0f)` in `Renderer::render` (or add `set_fov`, section 9) |

---

## 9. Changing the C++ engine

Python only sees what `engine/module.cpp` exposes. To add an engine feature you touch four places, then rebuild.

**Example: add `renderer.set_fov(degrees)`**

1. `render/renderer.h`: in the public part add `void set_fov(float degrees);` and in the private part add `float fov_ = 70.0f;`
2. `render/renderer.cpp`: add `void Renderer::set_fov(float degrees) { fov_ = degrees; }` and in `render()` change `glm::radians(70.0f)` to `glm::radians(fov_)`.
3. `engine/module.cpp`: in the `py::class_<Renderer>` chain add `.def("set_fov", &Renderer::set_fov)`.
4. `engine.pyi`: in `class Renderer` add `def set_fov(self, degrees: float) -> None: ...`
5. **Build**, restart the game, then `game.renderer.set_fov(85)` works.

**Engine API (what Python can call)**

```
engine.Application(width, height, title)
    .running()  .quit()  .begin_frame() -> dt  .end_frame()
    .input      .renderer

Input:    key_down(k)  key_pressed(k)  key_released(k)
          mouse_down(b)  mouse_pressed(b)  mouse_pos()  mouse_delta()  scroll()
          set_cursor_locked(bool)   cursor_locked

Renderer: load_mesh("cube" | "plane" | "path/to/model.obj") -> mesh id
          create_object(mesh, color) -> object id
          destroy_object(obj)   set_visible(obj, bool)   set_color(obj, color)
          set_transform(obj, pos, rot_degrees, scale)
          set_camera(pos, yaw, pitch)      set_flashlight(bool)
          set_fog(color, density)          set_ambient(color)
```

`key_pressed` is true only on the frame the key goes down; `key_down` while held.

**Your own models:** `r.load_mesh("assets/model.obj")` loads an OBJ (only `v` and `f` lines, flat shaded, triangles or polygons). Then `create_object` + `set_transform`.

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `module 'engine' has no attribute 'Application'` | Python found the `engine/` **folder**, not `engine.pyd`. Build the `engine` target, and check the `.pyd` is next to `main.py` and matches your Python version. |
| `DLL load failed while importing engine` | Missing MinGW DLL. `main.py` already adds CLion's folder; on a PC without CLion, uncomment the `-static` line in `CMakeLists.txt` and rebuild. |
| CMake: `Cannot run the interpreter` | `-DPython_EXECUTABLE=` in CLion's CMake options has a wrong path. Use the real `.venv/Scripts/python.exe` path in quotes. |
| Black screen or can't see anything | Fog may be too thick or you are inside a wall. Press F4 (fullbright), F2 (noclip), type `pos`. |
| `[map] ... JSON syntax error on line N` | Look at line N: trailing comma, missing quote or bracket. The old map is kept. |
| `[map] walls[3] is missing "to"` | That entry (counting from 0) lacks a required field. |
| `unknown color "x"` | Add it to `"colors"` or write `[r, g, b]`. |
| Walk through a wall | It is a box with `"solid": false`, or a floor/ceiling. |
| Stuck in a doorway | Gap narrower than 1 m, or the lintel is solid. |
| Door swings into the wall | Flip `swing`, or change `dir` (see the table in section 4). |
| Door doesn't react to E | Face it within 1.8 m. The terminal shows `[E] open door` when it is targeted. |
| Commands do nothing | You typed in the game window. Click the terminal instead. |
| Changed C++ but nothing changed | You didn't rebuild, or you ran an older `.pyd`. Build the `engine` target. |

---

## 11. Working with a friend

- **The contract** between the C++ side and the Python side is `engine.pyi`. When the C++ person adds a function, they add it to the `.pyi` too. The Python person can code against it before it exists.
- **Natural split:** one of you owns `engine/`, `input/`, `render/`, `CMakeLists.txt`; the other owns `core/`, `entities/`, `maps/`, `config.py`.
- **Map builders and programmers can work in parallel:** maps are data, so the level designer only touches `maps/*.json`.
- **Git:** commit source files only. `.gitignore` already skips `.venv/`, `cmake-build-*/`, `*.pyd` and `__pycache__/`. Each person builds their own `.pyd`.
- **Use the same Python version** if you copy a `.pyd` between machines (the name contains it, e.g. `cp313`). It's safer to just rebuild.

---

## 12. Ideas for next steps

- **Monster AI:** extend `Patroller`: chase when the player is close and in the flashlight beam, lose them after a while.
- **Sound** in C++ (miniaudio) with `play(name, x, y, z)`: footsteps, doors, ambient hum.
- **On-screen text** (HUD): replace `World.say` with real rendered text.
- **Textures** and a simple texture-per-object API in the renderer.
- **Flickering lights**: needs point lights in the shader; or fake it by animating `set_ambient` in an entity.
- **Collision in C++** once levels get big (lots of boxes make Python slow).
- **Save / load**: `player.items` and position are plain Python data, so `json.dump` them.
