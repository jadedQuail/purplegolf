from direct.showbase.ShowBase import ShowBase

TILE_SIZE = 1.0
ASSET_DIRECTORY = "kenney_minigolf-kit/GLB format"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.course = self.render.attachNewNode("course")

        self.build_course(course=self.course)

        # Grouping for items at the tee
        self.tee_setup = self.course.attachNewNode("tee_setup")
        self.place_ball(parent=self.tee_setup)

        self.frame_camera(self.course)

    def load_tile(self, parent, name, x, y, heading=0):
        """Load a tile by name and place it on the grid at (x, y)."""
        tile = self.loader.loadModel(f"{ASSET_DIRECTORY}/{name}.glb")
        tile.reparentTo(parent)
        tile.setPos(x * TILE_SIZE, y * TILE_SIZE, 0)
        tile.setH(heading)
        return tile

    def build_course(self, course):
        """Tee off, run down a short fairway, into the hole."""
        self.load_tile(parent=course, name="start", x=0, y=0)
        self.load_tile(parent=course, name="straight", x=0, y=1)
        self.load_tile(parent=course, name="straight", x=0, y=2)
        self.load_tile(parent=course, name="straight", x=0, y=3)
        self.load_tile(parent=course, name="hole-round", x=0, y=4, heading=180)

    def place_ball(self, parent):
        """Seat the ball on the green, centered on the start tile."""
        ball = self.loader.loadModel(f"{ASSET_DIRECTORY}/ball-blue.glb")
        ball.reparentTo(parent)

        # Get top of course geometry
        _, course_max = self.course.getTightBounds()
        surface_z = course_max.z

        # Place ball on surface
        ball_min, _ = ball.getTightBounds()
        ball.setPos(0, 0, surface_z - ball_min.z)

        print("[DIAG] surface_z:", surface_z, "ball pos:", ball.getPos())

        self.ball = ball
        return ball

    def frame_camera(self, node):
        """Point the camera at a node so its whole extent is visible."""
        min_pt, max_pt = node.getTightBounds()
        center = (min_pt + max_pt) / 2
        size = (max_pt - min_pt).length()

        self.camera.setPos(center.x, min_pt.y - size * 0.8, center.z + size * 0.8)
        self.camera.lookAt(center)


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
