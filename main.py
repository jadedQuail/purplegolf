from direct.showbase.ShowBase import ShowBase

from orbit_camera import OrbitCamera

TILE_SIZE = 1.0
ASSET_DIRECTORY = "kenney_minigolf-kit/GLB format"
ASSET_EXTENSION = ".glb"

# Asset model names (files under ASSET_DIRECTORY)
TILE_START = "start"
TILE_STRAIGHT = "straight"
TILE_HOLE_ROUND = "hole-round"
BALL_BLUE = "ball-blue"

# Scene-graph node names
COURSE_NODE = "course"
TEE_SETUP_NODE = "tee_setup"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.course = self.render.attachNewNode(COURSE_NODE)

        self.build_course(course=self.course)

        # Grouping for items at the tee
        self.tee_setup = self.course.attachNewNode(TEE_SETUP_NODE)
        self.place_ball(parent=self.tee_setup)

        # Dev camera - so I can see the course more easily right now
        self.orbit_camera = OrbitCamera(self, self.course)

    def load_tile(self, parent, name, x, y, heading=0):
        """Load a tile by name and place it on the grid at (x, y)."""
        tile = self.loader.loadModel(f"{ASSET_DIRECTORY}/{name}{ASSET_EXTENSION}")
        tile.reparentTo(parent)
        tile.setPos(x * TILE_SIZE, y * TILE_SIZE, 0)
        tile.setH(heading)
        return tile

    def build_course(self, course):
        """Tee off, run down a short fairway, into the hole."""
        self.load_tile(parent=course, name=TILE_START, x=0, y=0)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=1)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=2)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=3)
        self.load_tile(parent=course, name=TILE_HOLE_ROUND, x=0, y=4, heading=180)

    def place_ball(self, parent):
        """Seat the ball on the green, centered on the start tile."""
        ball = self.loader.loadModel(f"{ASSET_DIRECTORY}/{BALL_BLUE}{ASSET_EXTENSION}")
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


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
