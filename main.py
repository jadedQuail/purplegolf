from direct.interval.IntervalGlobal import Func, LerpHprInterval, Sequence
from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletPlaneShape,
    BulletRigidBodyNode,
    BulletSphereShape,
    BulletWorld,
)
from panda3d.core import Vec3

from orbit_camera import OrbitCamera

TILE_SIZE = 1.0
ASSET_DIRECTORY = "kenney_minigolf-kit/GLB format"
ASSET_EXTENSION = ".glb"

# Top of the green in every kit tile (local z)
GREEN_SURFACE_Z = 0.0633

# Club orientation constants
CLUB_LIE_TILT = 13.7
CLUB_HEAD_OFFSET_X = -0.18
CLUB_HEAD_OFFSET_Y = 0.025

# Putt swing constants
SWING_BACK_PITCH_DEGREES = -25
SWING_THROUGH_PITCH_DEGREES = 25
SWING_BACK_TIME_SECONDS = 0.4
SWING_THROUGH_TIME_SECONDS = 0.25
SWING_RETURN_TIME_SECONDS = 0.3

# Club is at address (touching the ball) when the pivot pitch is 0,
# so the through-swing passes through contact at this pitch.
SWING_CONTACT_PITCH_DEGREES = 0

# Physics
GRAVITY = (0, 0, -9.81)
PHYSICS_TASK_NAME = "step_physics"

BALL_MASS = 1.0
BALL_DROP_HEIGHT = 0.5

# Key that triggers a putt swing
SWING_KEY = "space"

# Asset model names (files under ASSET_DIRECTORY)
TILE_START = "start"
TILE_STRAIGHT = "straight"
TILE_HOLE_ROUND = "hole-round"
BALL_BLUE = "ball-blue"
CLUB_BLUE = "club-blue"

# Scene-graph node names
COURSE_NODE = "course"
TEE_SETUP_NODE = "tee_setup"

# Physics body names (used to identify bodies in collisions)
GROUND_BODY = "ground"
BALL_BODY = "ball"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.setup_physics()

        self.course = self.render.attachNewNode(COURSE_NODE)

        self.build_course(course=self.course)

        # Static floor for physics bodies to land on
        self.place_ground(parent=self.render)

        # Grouping for items at the tee
        self.tee_setup = self.course.attachNewNode(TEE_SETUP_NODE)
        # Ball is a world-space physics body, not part of the static tee group
        self.place_ball(parent=self.render)
        self.place_club(parent=self.tee_setup)

        # Dev camera - so I can see the course more easily right now
        self.orbit_camera = OrbitCamera(self, self.course)

        # Press space to take a putt swing
        self.swing_sequence = None
        self.accept(SWING_KEY, self.swing_club)

    def setup_physics(self):
        """Stand up the Bullet world and step it every frame (no bodies yet)."""
        self.physics_world = BulletWorld()
        self.physics_world.setGravity(GRAVITY)
        self.taskMgr.add(self.step_physics, PHYSICS_TASK_NAME)

    def step_physics(self, task):
        """Advance the simulation by the time elapsed since the last frame."""
        dt = self.clock.getDt()
        self.physics_world.doPhysics(dt)
        return task.cont

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

    def place_ground(self, parent):
        """Physics floor for ball to land on"""

        # Infinite plane
        shape = BulletPlaneShape(Vec3(0, 0, 1), GREEN_SURFACE_Z)
        body = BulletRigidBodyNode(GROUND_BODY)
        body.addShape(shape)
        parent.attachNewNode(body)
        self.physics_world.attachRigidBody(body)
        self.ground_body = body
        return body

    def place_ball(self, parent):
        """Seat the ball on the green as a dynamic physics body."""
        ball = self.loader.loadModel(f"{ASSET_DIRECTORY}/{BALL_BLUE}{ASSET_EXTENSION}")

        # model can be aligned to the body origin (where the sphere sits).
        ball_min, ball_max = ball.getTightBounds()
        radius = (ball_max.z - ball_min.z) / 2
        center = (ball_min + ball_max) / 2

        shape = BulletSphereShape(radius)
        body = BulletRigidBodyNode(BALL_BODY)
        body.addShape(shape)
        body.setMass(BALL_MASS)

        ball_nodepath = parent.attachNewNode(body)
        # Ball center rests at surface + radius; the drop gap is temporary.
        ball_nodepath.setPos(0, 0.15, GREEN_SURFACE_Z + radius + BALL_DROP_HEIGHT)

        # Park the visual model under the body, centered on the body origin.
        ball.reparentTo(ball_nodepath)
        ball.setPos(-center)

        self.physics_world.attachRigidBody(body)

        # Save variables
        self.ball = ball
        self.ball_body = body
        self.ball_nodepath = ball_nodepath
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
        club.setPos(CLUB_HEAD_OFFSET_X, CLUB_HEAD_OFFSET_Y, GREEN_SURFACE_Z - club_min.z)

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

    def swing_club(self):
        """Play one putt stroke: back, through, then settle to rest."""
        # Ignore re-presses while a stroke is already playing.
        if self.swing_sequence is not None and self.swing_sequence.isPlaying():
            return
        pivot = self.club_pivot

        # Split swing so we can find the moment the club hits the ball (pitch = 0)
        half_through_time = SWING_THROUGH_TIME_SECONDS / 2
        
        self.swing_sequence = Sequence(
            LerpHprInterval(pivot, SWING_BACK_TIME_SECONDS, (0, SWING_BACK_PITCH_DEGREES, 0)),
            LerpHprInterval(pivot, half_through_time, (0, SWING_CONTACT_PITCH_DEGREES, 0)),
            Func(self.on_ball_contact),
            LerpHprInterval(pivot, half_through_time, (0, SWING_THROUGH_PITCH_DEGREES, 0)),
            LerpHprInterval(pivot, SWING_RETURN_TIME_SECONDS, (0, 0, 0)),
        )
        self.swing_sequence.start()

    def on_ball_contact(self):
        """Club has reached the ball at address — the putt is struck here."""
        print("[DIAG] contact")


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
