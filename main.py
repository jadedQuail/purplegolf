from direct.showbase.ShowBase import ShowBase

from orbit_camera import OrbitCamera

TILE_SIZE = 1.0
ASSET_DIRECTORY = "kenney_minigolf-kit/GLB format"
ASSET_EXTENSION = ".glb"

# Top of the green in every kit tile (local z)
GREEN_SURFACE_Z = 0.0633

# Club orientation constants
CLUB_LIE_TILT = 13.7
CLUB_HEAD_OFFSET_X = -0.18

# Asset model names (files under ASSET_DIRECTORY)
TILE_START = "start"
TILE_STRAIGHT = "straight"
TILE_HOLE_ROUND = "hole-round"
BALL_BLUE = "ball-blue"
CLUB_BLUE = "club-blue"

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
        self.place_club(parent=self.tee_setup)

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

        # Place ball on green surface
        ball_min, _ = ball.getTightBounds()
        ball.setPos(0, 0.15, GREEN_SURFACE_Z - ball_min.z)

        print("[DIAG] surface_z:", GREEN_SURFACE_Z, "ball pos:", ball.getPos())

        self.ball = ball
        return ball

    def place_club(self, parent):
        """Rest the club on the green, head pointing down the lane (rough pass)."""
        club = self.loader.loadModel(f"{ASSET_DIRECTORY}/{CLUB_BLUE}{ASSET_EXTENSION}")
        club.reparentTo(parent)

        # Rotate face to look down the course
        club.setH(270)
        club.setP(CLUB_LIE_TILT)

        # Place club head on the green
        club_min, _ = club.getTightBounds()
        club.setPos(CLUB_HEAD_OFFSET_X, 0, GREEN_SURFACE_Z - club_min.z)

        self.club_pivot = self.add_swing_pivot(club, parent)
        self.club = club
        return club

    def add_swing_pivot(self, club, parent):
        """Set the pivot point to the top of the club"""
        club_min, club_max = club.getTightBounds(parent)
        pivot = parent.attachNewNode("club_pivot")
        # Pivot point set to top of club
        pivot.setPos(
            (club_min.x + club_max.x) / 2,
            (club_min.y + club_max.y) / 2,
            club_max.z,
        )
        club.wrtReparentTo(pivot)
        return pivot


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
