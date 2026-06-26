from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletDebugNode,
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
    BulletWorld,
)
from panda3d.core import Vec3

from ball import Ball
from club import Club
from constants import (
    ASSET_DIRECTORY,
    ASSET_EXTENSION,
    GREEN_SURFACE_Z,
    SURFACE_FRICTION,
    SURFACE_RESTITUTION,
)
from orbit_camera import OrbitCamera
from power_meter import PowerMeter

TILE_SIZE = 1.0

# Physics
GRAVITY = (0, 0, -9.81)
PHYSICS_TASK_NAME = "step_physics"

MAX_PUTT_SPEED = 5.0 # Ball speed at a full power bar; scaled down by fill percentage

# Hold this key and release to take a putt swing
SWING_KEY = "space"
SWING_RELEASE_EVENT = f"{SWING_KEY}-up"
TOGGLE_CAMERA_KEY = "c"

# Gameplay camera placement, relative to the ball
CAMERA_BACK_DISTANCE = 5.0
CAMERA_HEIGHT = 3.5
GAME_CAMERA_TASK_NAME = "update_game_camera"

# Asset model names (files under ASSET_DIRECTORY)
TILE_START = "start"
TILE_STRAIGHT = "straight"
TILE_HOLE_ROUND = "hole-round"

# Scene-graph node names
COURSE_NODE = "course"
PHYSICS_DEBUG_NODE = "physics_debug"
HOLE_NODE = "hole"

# Physics body names (used to identify bodies in collisions)
TILE_BODY = "tile"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.setup_physics()

        self.course = self.render.attachNewNode(COURSE_NODE)

        self.build_course(course=self.course)

        # Ball is a world-space physics body, parented straight to render
        self.ball = Ball(self, self.render)

        ball_pos = self.ball.nodepath.getPos(self.render)
        hole_pos = self.hole_nodepath.getPos(self.render)
        self.club = Club(self, self.course, ball_pos, hole_pos)

        self.orbit_camera = OrbitCamera(self, self.course, enabled=False)
        self.setup_game_camera()
        self.power_meter = PowerMeter(self)

        # Camera-to-ball offset captured at contact, used to trail the ball while it rolls
        self.camera_follow_offset = Vec3(0, 0, 0)

        # Keys
        self.accept(TOGGLE_CAMERA_KEY, self.toggle_camera)
        self.accept(SWING_KEY, self.start_power_charge)
        self.accept(SWING_RELEASE_EVENT, self.swing_club)

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
        if self.ball.apply_rolling_resistance(dt):
            self.set_up_next_shot()
        return task.cont

    def set_up_next_shot(self):
        """Positions camera and club to be ready for next shot."""
        ball_pos = self.ball.nodepath.getPos(self.render)
        hole_pos = self.hole_nodepath.getPos(self.render)
        self.club.aim_behind(ball_pos, hole_pos)
        if self.game_camera_active:
            self.position_game_camera()

    def setup_game_camera(self):
        """Default gameplay view: parked behind and above the ball, aimed at it."""
        self.game_camera_active = True
        self.position_game_camera()
        self.taskMgr.add(self.update_game_camera, GAME_CAMERA_TASK_NAME)

    def start_power_charge(self):
        """Begin charging the meter, unless a stroke or roll is in progress."""
        if self.club.is_swinging() or self.ball.is_rolling():
            return
        self.power_meter.start_charge()

    def ball_to_hole_direction(self):
        """Unit vector from the ball to the hole, flattened to the horizontal plane."""
        to_hole = self.hole_nodepath.getPos(self.render) - self.ball.nodepath.getPos(self.render)
        to_hole.z = 0
        if to_hole.length() > 0:
            to_hole.normalize()
        return to_hole

    def position_game_camera(self):
        ball_pos = self.ball.nodepath.getPos(self.render)
        to_hole = self.ball_to_hole_direction()

        # Sit CAMERA_BACK_DISTANCE behind the ball, opposite the hole
        self.camera.setPos(
            ball_pos.x - to_hole.x * CAMERA_BACK_DISTANCE,
            ball_pos.y - to_hole.y * CAMERA_BACK_DISTANCE,
            ball_pos.z + CAMERA_HEIGHT,
        )
        self.camera.lookAt(self.ball.nodepath)

    def update_game_camera(self, task):
        """Trail the ball while it rolls, holding the framing from the putt."""
        if self.game_camera_active and self.ball.is_rolling():
            ball_pos = self.ball.nodepath.getPos(self.render)
            self.camera.setPos(ball_pos + self.camera_follow_offset)
            self.camera.lookAt(self.ball.nodepath)
        return task.cont

    def toggle_camera(self):
        """Swap between the gameplay camera (default) and the orbit dev camera."""
        self.game_camera_active = not self.game_camera_active
        if self.game_camera_active:
            self.orbit_camera.disable()
            self.position_game_camera()
        else:
            self.orbit_camera.enable()

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

        hole_tile = self.load_tile(parent=course, name=TILE_HOLE_ROUND, x=0, y=4, heading=180)
        self.place_hole(parent=hole_tile)

    def place_hole(self, parent):
        """Mark the cup so we can aim shots and the camera at it later."""
        hole = parent.attachNewNode(HOLE_NODE)

        # Cup sits at the center of the hole tile, on the green surface
        hole.setPos(0, 0, GREEN_SURFACE_Z)
        self.hole_nodepath = hole
        return hole

    def swing_club(self):
        """Take a putt swing, unless a stroke or roll is already underway."""
        # Releasing space stops the meter wherever it landed
        self.power_meter.stop()

        # Block a new putt while the club is still swinging or the ball is still rolling
        if self.club.is_swinging() or self.ball.is_rolling():
            return

        self.club.swing(self.on_ball_contact)

    def on_ball_contact(self):
        """Club has reached the ball at address — launch the putt."""
        # Prevent camera from flipping its position pre-hit
        ball_pos = self.ball.nodepath.getPos(self.render)
        self.camera_follow_offset = self.camera.getPos(self.render) - ball_pos

        # Launch the ball straight at the hole, harder the fuller the power bar was
        launch_speed = MAX_PUTT_SPEED * self.power_meter.fraction()
        self.ball.launch(self.ball_to_hole_direction(), launch_speed)


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
