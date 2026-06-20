from math import cos, radians, sin


class OrbitCamera:
    """Dev camera: left-drag to orbit a target node, mouse wheel to zoom.

    This is an inspection tool; the real gameplay camera comes later. Construct
    it with the running ShowBase and the node to orbit around:

        self.orbit_camera = OrbitCamera(self, self.course)
    """

    def __init__(self, base, target_node):
        self.base = base

        min_pt, max_pt = target_node.getTightBounds()
        self.target = (min_pt + max_pt) / 2
        self.distance = (max_pt - min_pt).length()
        self.yaw = 0.0
        self.pitch = 30.0
        self.dragging = False
        self.last_mouse = None

        # Drag to orbit, wheel to zoom.
        base.accept("mouse1", self._set_dragging, [True])
        base.accept("mouse1-up", self._set_dragging, [False])
        base.accept("wheel_up", self._zoom, [0.9])
        base.accept("wheel_down", self._zoom, [1.1])

        base.taskMgr.add(self._update, "orbit_camera")

    def _set_dragging(self, dragging):
        self.dragging = dragging
        if not dragging:
            self.last_mouse = None

    def _zoom(self, factor):
        self.distance *= factor

    def _update(self, task):
        mouse = self.base.mouseWatcherNode

        # While dragging, turn mouse movement into yaw/pitch changes.
        if self.dragging and mouse.hasMouse():
            x = mouse.getMouseX()  # normalized -1..1
            y = mouse.getMouseY()
            if self.last_mouse is not None:
                dx = x - self.last_mouse[0]
                dy = y - self.last_mouse[1]
                self.yaw -= dx * 180.0
                # Subtract dy so dragging up tilts the view up (non-inverted).
                # Clamp pitch so we never flip over the poles.
                self.pitch = max(5.0, min(85.0, self.pitch - dy * 180.0))
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
