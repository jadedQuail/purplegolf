from math import cos, radians, sin


class OrbitCamera:
    """Dev camera: left-drag to orbit, middle-drag to pan, mouse wheel to zoom.

    This is an inspection tool; the real gameplay camera comes later. Construct
    it with the running ShowBase and the node to orbit around:

        self.orbit_camera = OrbitCamera(self, self.course)
    """

    def __init__(self, base, target_node, enabled=True):
        self.base = base
        self.target_node = target_node

        self.dragging = False
        self.panning = False
        self.last_mouse = None
        self.enabled = enabled
        # Frame the target from the default angle/distance.
        self.reset()

        # Let the view get in close without near-plane clipping (default is 1.0).
        base.camLens.setNear(0.05)

        # Left-drag to orbit, middle-drag to pan, wheel to zoom.
        base.accept("mouse1", self._set_dragging, [True])
        base.accept("mouse1-up", self._set_dragging, [False])
        base.accept("mouse2", self._set_panning, [True])
        base.accept("mouse2-up", self._set_panning, [False])
        base.accept("wheel_up", self._zoom, [0.9])
        base.accept("wheel_down", self._zoom, [1.1])

        base.taskMgr.add(self._update, "orbit_camera")

    def reset(self):
        """Snap the orbit back to its default framing of the target."""
        min_pt, max_pt = self.target_node.getTightBounds()
        self.target = (min_pt + max_pt) / 2
        self.distance = (max_pt - min_pt).length()
        self.yaw = 0.0
        self.pitch = 30.0

    def enable(self):
        self.reset()
        self.enabled = True

    def disable(self):
        self.enabled = False
        self.last_mouse = None

    def _set_dragging(self, dragging):
        self.dragging = dragging
        if not dragging:
            self.last_mouse = None

    def _set_panning(self, panning):
        self.panning = panning
        if not panning:
            self.last_mouse = None

    def _zoom(self, factor):
        self.distance *= factor

    def _update(self, task):
        if not self.enabled:
            return task.cont

        mouse = self.base.mouseWatcherNode

        # While dragging, turn mouse movement into an orbit (mouse1) or pan (mouse2).
        if (self.dragging or self.panning) and mouse.hasMouse():
            x = mouse.getMouseX()  # normalized -1..1
            y = mouse.getMouseY()
            if self.last_mouse is not None:
                dx = x - self.last_mouse[0]
                dy = y - self.last_mouse[1]
                if self.dragging:
                    self.yaw -= dx * 180.0
                    # Subtract dy so dragging up tilts the view up (non-inverted).
                    # Clamp just short of straight up/down (the poles) so lookAt
                    # never gimbal-flips, but allow going below the green.
                    self.pitch = max(-85.0, min(85.0, self.pitch - dy * 180.0))
                else:
                    # Slide the target in the camera's own right/up plane, scaled
                    # by distance so the pan speed feels the same at any zoom.
                    # Move opposite the drag so the scene follows the cursor.
                    quat = self.base.camera.getQuat(self.base.render)
                    right = quat.getRight()
                    up = quat.getUp()
                    self.target = (
                        self.target
                        - right * (dx * self.distance)
                        - up * (dy * self.distance)
                    )
            self.last_mouse = (x, y)

        # Convert orbit angles + distance into a camera position around target.
        yaw, pitch = radians(self.yaw), radians(self.pitch)
        d = self.distance
        self.base.camera.setPos(
            self.target.x + d * sin(yaw) * cos(pitch),
            self.target.y - d * cos(yaw) * cos(pitch),
            self.target.z + d * sin(pitch),
        )
        self.base.camera.lookAt(self.target)
        return task.cont
