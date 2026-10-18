"""One place that knows about keys. Gameplay code asks for ACTIONS, not keys."""
import engine as e

BINDINGS = {
    "forward":    e.KEY_W,
    "back":       e.KEY_S,
    "left":       e.KEY_A,
    "right":      e.KEY_D,
    "interact":   e.KEY_E,
    "flashlight": e.KEY_F,
    "inventory":  e.KEY_TAB,
    "crouch":     e.KEY_CTRL,
    "jump":       e.KEY_SPACE,
    "sprint":     e.KEY_SHIFT,
    "pause":      e.KEY_ESC,
}
SLOT_KEYS = (e.KEY_1, e.KEY_2, e.KEY_3, e.KEY_4)


class Controls:
    def __init__(self, inp):
        self.inp = inp

    # keyboard actions
    def held(self, action):     return self.inp.key_down(BINDINGS[action])
    def pressed(self, action):  return self.inp.key_pressed(BINDINGS[action])
    def released(self, action): return self.inp.key_released(BINDINGS[action])

    def move_axis(self):
        """(strafe, forward) each in -1..1"""
        x = float(self.held("right")) - float(self.held("left"))
        z = float(self.held("forward")) - float(self.held("back"))
        return x, z

    def slot_pressed(self):
        """0..3 if 1-4 was pressed this frame, else None"""
        for i, key in enumerate(SLOT_KEYS):
            if self.inp.key_pressed(key):
                return i
        return None

    # mouse
    def look(self):            return self.inp.mouse_delta()
    def scroll(self):          return self.inp.scroll()
    def primary_pressed(self): return self.inp.mouse_pressed(e.M_LEFT)
    def primary_held(self):    return self.inp.mouse_down(e.M_LEFT)
    def secondary_pressed(self): return self.inp.mouse_pressed(e.M_RIGHT)
    def secondary_held(self):  return self.inp.mouse_down(e.M_RIGHT)
