import math


class Player:
    SENS = 0.09                 # degrees per mouse count
    WALK, SPRINT, CROUCH = 2.5, 4.5, 1.2
    EYE, EYE_CROUCH = 1.65, 1.0
    RADIUS = 0.3
    SLOTS = 4

    def __init__(self, controls, start=(0.0, 0.0)):
        self.controls = controls
        self.x, self.z = start
        self.yaw = 0.0
        self.pitch = 0.0
        self.eye = self.EYE
        self.y_off = 0.0        # jump / fly offset
        self.vy = 0.0
        self.flashlight = True
        self.slot = 0
        self.items = set()      # item ids picked up, e.g. {"classroom_key"}

        # cheats (changed by core/debug.py)
        self.noclip = False
        self.god = False
        self.speed_mult = 1.0

    def forward(self):
        """Unit vector (x, z) the player is facing, ignoring up/down."""
        yaw = math.radians(self.yaw)
        return math.sin(yaw), -math.cos(yaw)

    def teleport(self, x, z, yaw=None):
        self.x, self.z = x, z
        if yaw is not None:
            self.yaw = yaw
        self.y_off = 0.0
        self.vy = 0.0

    def set_noclip(self, on):
        self.noclip = on
        if not on:
            self.y_off = max(0.0, self.y_off)   # come back above the floor, then gravity takes over
            self.vy = 0.0

    def update(self, dt, world):
        c = self.controls

        # look
        dx, dy = c.look()
        self.yaw += dx * self.SENS
        self.pitch = max(-85.0, min(85.0, self.pitch - dy * self.SENS))

        # move (normalised so diagonals aren't faster)
        mx, mz = c.move_axis()
        n = math.hypot(mx, mz)
        if n > 0:
            mx, mz = mx / n, mz / n

        crouching = c.held("crouch") and not self.noclip
        if crouching:
            speed = self.CROUCH
        elif c.held("sprint"):
            speed = self.SPRINT
        else:
            speed = self.WALK
        speed *= self.speed_mult

        yaw = math.radians(self.yaw)
        fx, fz = self.forward()
        rx, rz = math.cos(yaw), math.sin(yaw)     # right
        self.x += (fx * mz + rx * mx) * speed * dt
        self.z += (fz * mz + rz * mx) * speed * dt

        if self.noclip:
            # fly: Space up, Ctrl down, no walls, no gravity
            self.y_off += (float(c.held("jump")) - float(c.held("crouch"))) * speed * dt
            self.vy = 0.0
        else:
            self._collide(world.colliders())
            self._jump(dt, crouching)

        # crouch height easing
        target = self.EYE_CROUCH if crouching else self.EYE
        self.eye += (target - self.eye) * min(1.0, 10.0 * dt)

        # flashlight
        if c.pressed("flashlight"):
            self.flashlight = not self.flashlight

        # inventory slots: 1-4 and mouse wheel
        s = c.slot_pressed()
        if s is not None:
            self.slot = s
        wheel = c.scroll()
        if wheel:
            self.slot = (self.slot - int(math.copysign(1, wheel))) % self.SLOTS

        # actions
        if c.pressed("interact"):
            world.interact(self)
        if c.primary_pressed():
            self.use_item()

    def _jump(self, dt, crouching):
        if self.controls.pressed("jump") and self.y_off == 0.0 and not crouching:
            self.vy = 3.0
        if self.vy != 0.0 or self.y_off > 0.0:
            self.vy -= 9.8 * dt
            self.y_off += self.vy * dt
            if self.y_off <= 0.0:
                self.y_off = 0.0
                self.vy = 0.0

    def use_item(self):
        print(f"[player] use item in slot {self.slot + 1}")

    def _collide(self, boxes):
        """Circle vs axis-aligned boxes. boxes = [(x0, z0, x1, z1), ...]"""
        r = self.RADIUS
        for x0, z0, x1, z1 in boxes:
            cx = max(x0, min(self.x, x1))
            cz = max(z0, min(self.z, z1))
            dx, dz = self.x - cx, self.z - cz
            d2 = dx * dx + dz * dz
            if d2 >= r * r:
                continue
            if d2 > 1e-9:
                d = math.sqrt(d2)
                push = r - d
                self.x += dx / d * push
                self.z += dz / d * push
            else:  # centre is inside the box: leave through the nearest face
                left, right = self.x - x0, x1 - self.x
                top, bottom = self.z - z0, z1 - self.z
                m = min(left, right, top, bottom)
                if m == left:    self.x = x0 - r
                elif m == right: self.x = x1 + r
                elif m == top:   self.z = z0 - r
                else:            self.z = z1 + r

    def apply(self, renderer):
        renderer.set_camera((self.x, self.eye + self.y_off, self.z), self.yaw, self.pitch)
        renderer.set_flashlight(self.flashlight)
