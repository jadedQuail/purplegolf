from direct.interval.IntervalGlobal import Func, LerpHprInterval, Sequence
from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletDebugNode,
    BulletRigidBodyNode,
    BulletSphereShape,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
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
PUTT_SPEED = 2.0
SURFACE_FRICTION = 0.6
# Bounciness
SURFACE_RESTITUTION = 0.8
ROLLING_RESISTANCE_CONSTANT = 0.12
ROLLING_DRAG = 0.7

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
PHYSICS_DEBUG_NODE = "physics_debug"

# Physics body names (used to identify bodies in collisions)
BALL_BODY = "ball"
TILE_BODY = "tile"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.setup_physics()

        self.course = self.render.attachNewNode(COURSE_NODE)

        self.build_course(course=self.course)

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
        self.setup_physics_debug()

    def setup_physics_debug(self):
        """Draw every collider in the world as wireframe, overlaid on the models."""
        debug_node = BulletDebugNode(PHYSICS_DEBUG_NODE)
        debug_node.showWireframe(True)

        debug_nodepath = self.render.attachNewNode(debug_node)
        debug_nodepath.show()

        self.physics_world.setDebugNode(debug_node)
        self.physics_debug_nodepath = debug_nodepath

    def step_physics(self, task):
        """Advance the simulation by the time elapsed since the last frame."""
        dt = self.clock.getDt()
        self.physics_world.doPhysics(dt)
        self.apply_rolling_resistance(dt)
        return task.cont

    def apply_rolling_resistance(self, dt):
        """Shave a constant amount of speed each frame"""
        if not self.ball_body.isActive():
            return

        velocity = self.ball_body.getLinearVelocity()
        speed = Vec3(velocity.x, velocity.y, 0).length()
        if speed == 0:
            return

        decrement = (ROLLING_RESISTANCE_CONSTANT + ROLLING_DRAG * speed) * dt
        if decrement >= speed:
            # Next step would cross zero -> settle to a full stop at near-zero speed.
            self.ball_body.setLinearVelocity(Vec3(0, 0, 0))
            self.ball_body.setAngularVelocity(Vec3(0, 0, 0))
            self.ball_body.setActive(False)
            return

        # Scale linear and spin together so the ball keeps rolling consistently
        scale = (speed - decrement) / speed
        self.ball_body.setLinearVelocity(Vec3(velocity.x * scale, velocity.y * scale, velocity.z))
        self.ball_body.setAngularVelocity(self.ball_body.getAngularVelocity() * scale)

    def load_tile(self, parent, name, x, y, heading=0):
        """Load a tile by name, place it on the grid at (x, y), and collider it."""
        tile = self.loader.loadModel(f"{ASSET_DIRECTORY}/{name}{ASSET_EXTENSION}")
        tile.reparentTo(parent)
        tile.setPos(x * TILE_SIZE, y * TILE_SIZE, 0)
        tile.setH(heading)
        self.make_tile_collider(tile)
        return tile

    def make_tile_collider(self, model):
        """Build a static collider that traces a tile's mesh"""
        mesh = BulletTriangleMesh()
        for geom_nodepath in model.findAllMatches("**/+GeomNode"):
            geom_node = geom_nodepath.node()
            # Keep each piece's placement relative to the tile root.
            transform = geom_nodepath.getTransform(model)
            for i in range(geom_node.getNumGeoms()):
                mesh.addGeom(geom_node.getGeom(i), True, transform)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        tile_body = BulletRigidBodyNode(TILE_BODY)
        tile_body.addShape(shape)
        tile_body.setFriction(SURFACE_FRICTION)
        tile_body.setRestitution(SURFACE_RESTITUTION)

        collider_nodepath = model.attachNewNode(tile_body)
        self.physics_world.attachRigidBody(tile_body)
        return collider_nodepath

    def build_course(self, course):
        """Tee off, run down a short fairway, into the hole."""
        self.load_tile(parent=course, name=TILE_START, x=0, y=0)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=1)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=2)
        self.load_tile(parent=course, name=TILE_STRAIGHT, x=0, y=3)
        self.load_tile(parent=course, name=TILE_HOLE_ROUND, x=0, y=4, heading=180)

    def place_ball(self, parent):
        """Seat the ball on the green as a dynamic physics body."""
        ball = self.loader.loadModel(f"{ASSET_DIRECTORY}/{BALL_BLUE}{ASSET_EXTENSION}")

        # model can be aligned to the body origin (where the sphere sits).
        ball_min, ball_max = ball.getTightBounds()
        radius = (ball_max.z - ball_min.z) / 2
        center = (ball_min + ball_max) / 2

        shape = BulletSphereShape(radius)
        ball_body = BulletRigidBodyNode(BALL_BODY)
        ball_body.addShape(shape)
        ball_body.setMass(BALL_MASS)
        ball_body.setFriction(SURFACE_FRICTION)
        ball_body.setRestitution(SURFACE_RESTITUTION)

        ball_nodepath = parent.attachNewNode(ball_body)
        ball_nodepath.setPos(0, 0.15, GREEN_SURFACE_Z + radius)

        # Park the visual model under the body, centered on the body origin.
        ball.reparentTo(ball_nodepath)
        ball.setPos(-center)

        self.physics_world.attachRigidBody(ball_body)

        # Save variables
        self.ball = ball
        self.ball_body = ball_body
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
        """Club has reached the ball at address — launch the putt."""
        self.ball_body.setLinearVelocity(Vec3(0, PUTT_SPEED, 0))
        self.ball_body.setActive(True)


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
