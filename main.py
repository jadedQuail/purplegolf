from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletDebugNode, BulletWorld
from panda3d.core import Quat, Vec3

from ball import Ball
from club import Club
from course import Course
from game_camera import GameCamera
from message_banner import MessageBanner
from orbit_camera import OrbitCamera
from power_meter import PowerMeter

# Physics
GRAVITY = (0, 0, -9.81)
PHYSICS_TASK_NAME = "step_physics"

MAX_PUTT_SPEED = 5.0 # Ball speed at a full power bar; scaled down by fill percentage

# Hold this key and release to take a putt swing
SWING_KEY = "space"
SWING_RELEASE_EVENT = f"{SWING_KEY}-up"
TOGGLE_CAMERA_KEY = "c"

AIM_LEFT_KEYS = ("arrow_left", "a")
AIM_RIGHT_KEYS = ("arrow_right", "d")
AIM_TURN_SPEED_DEGREES_PER_SEC = 25.0
AIM_TASK_NAME = "update_aim"

# Scene-graph node names
PHYSICS_DEBUG_NODE = "physics_debug"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.setup_physics()

        self.course = Course(self)

        # Ball is a world-space physics body, parented straight to render
        self.ball = Ball(self, self.render)

        ball_pos = self.ball.nodepath.getPos(self.render)
        hole_pos = self.course.hole.getPos(self.render)
        self.club = Club(self, self.course.root, ball_pos, hole_pos)

        self.aim_offset_degrees: float = 0.0
        self.aim_left_held: bool = False
        self.aim_right_held: bool = False
        self.ball_holed: bool = False
        self.stroke_count: int = 0
        self.start_time: float = self.clock.getFrameTime()

        self.orbit_camera = OrbitCamera(self, self.course.root, enabled=False)
        self.game_camera = GameCamera(self, self.ball)
        self.position_game_camera()
        self.power_meter = PowerMeter(self)
        self.message_banner = MessageBanner(self)
        self.message_banner.set_restart_command(self.restart_hole)

        self.bind_controls()
        self.taskMgr.add(self.update_aim, AIM_TASK_NAME)

    def bind_controls(self):
        """Wire up the camera, swing, and aim keys."""
        self.accept(TOGGLE_CAMERA_KEY, self.toggle_camera)
        self.accept(SWING_KEY, self.start_power_charge)
        self.accept(SWING_RELEASE_EVENT, self.swing_club)

        for key in AIM_LEFT_KEYS:
            self.accept(key, self.set_aim_left, [True])
            self.accept(f"{key}-up", self.set_aim_left, [False])
        for key in AIM_RIGHT_KEYS:
            self.accept(key, self.set_aim_right, [True])
            self.accept(f"{key}-up", self.set_aim_right, [False])

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
        is_ball_settled = self.ball.apply_rolling_resistance(dt)
        self.check_for_hole()
        if is_ball_settled and not self.ball_holed:
            self.set_up_next_shot()
        return task.cont

    def check_for_hole(self):
        """End the game the moment the ball settles into the bottom of the cup."""
        if self.ball_holed:
            return
        if self.course.is_ball_on_cup_bottom(self.ball.body):
            self.game_over()

    def game_over(self):
        """The ball is holed: congratulate the player and lock out further play."""
        self.ball_holed = True
        elapsed_seconds = self.clock.getFrameTime() - self.start_time
        self.message_banner.show_win(self.stroke_count, elapsed_seconds)
        self.power_meter.hide()
        self.ignore(SWING_KEY)
        self.ignore(SWING_RELEASE_EVENT)
        self.freeze_aim()

    def freeze_aim(self):
        """Unbind the aim keys and stop any turn in progress."""
        self.aim_left_held = False
        self.aim_right_held = False
        for key in AIM_LEFT_KEYS + AIM_RIGHT_KEYS:
            self.ignore(key)
            self.ignore(f"{key}-up")

    def restart_hole(self):
        """Reset the hole to its opening state for another attempt."""
        self.ball.reset()
        self.stroke_count = 0
        self.start_time = self.clock.getFrameTime()
        self.ball_holed = False
        self.message_banner.hide()
        self.power_meter.show()
        self.bind_controls()
        self.set_up_next_shot()

    def set_up_next_shot(self):
        """Positions camera and club to be ready for next shot."""
        self.aim_offset_degrees = 0.0
        self.aim_club()
        if self.game_camera.active:
            self.position_game_camera()

    def aim_club(self):
        """Point the club down the current aim line."""
        ball_pos = self.ball.nodepath.getPos(self.render)
        self.club.aim_along(ball_pos, self.compute_aim_direction())

    def is_shot_in_progress(self) -> bool:
        """True while the club is mid-stroke or the ball is still rolling."""
        return self.club.is_swinging() or self.ball.is_rolling()

    def start_power_charge(self):
        """Begin charging the meter, unless a stroke or roll is in progress."""
        if self.is_shot_in_progress():
            return
        self.power_meter.start_charge()

    def ball_to_hole_direction(self):
        """Unit vector from the ball to the hole, flattened to the horizontal plane."""
        to_hole = self.course.hole.getPos(self.render) - self.ball.nodepath.getPos(self.render)
        to_hole.z = 0
        if to_hole.length() > 0:
            to_hole.normalize()
        return to_hole

    def set_aim_left(self, held: bool):
        """Arrow key state: whether the player is holding left."""
        self.aim_left_held = held

    def set_aim_right(self, held: bool):
        """Arrow key state: whether the player is holding right."""
        self.aim_right_held = held

    def update_aim(self, task):
        """Each frame, swivel the aim while an arrow key is held (delay-free)."""
        direction = float(self.aim_left_held) - float(self.aim_right_held)
        if direction and not self.is_shot_in_progress():
            self.aim_offset_degrees += (
                direction * AIM_TURN_SPEED_DEGREES_PER_SEC * self.clock.getDt()
            )
            self.aim_club()
            if self.game_camera.active:
                self.position_game_camera()
        return task.cont

    def compute_aim_direction(self) -> Vec3:
        """Where the player is aiming: the line to the hole, turned by the aim offset."""
        direction = self.ball_to_hole_direction()
        if self.aim_offset_degrees:
            rotation = Quat()
            rotation.setFromAxisAngle(self.aim_offset_degrees, Vec3.up())
            direction = rotation.xform(direction)
        return direction

    def position_game_camera(self):
        """Frame the ball from behind, aimed down the current aim line."""
        self.game_camera.position_behind(self.compute_aim_direction())

    def toggle_camera(self):
        """Swap between the gameplay camera (default) and the orbit dev camera."""
        self.game_camera.active = not self.game_camera.active
        if self.game_camera.active:
            self.orbit_camera.disable()
            self.position_game_camera()
        else:
            self.orbit_camera.enable()

    def swing_club(self):
        """Take a putt swing, unless a stroke or roll is already underway."""
        # Releasing space stops the meter wherever it landed
        self.power_meter.stop()

        # Block a new putt while the club is still swinging or the ball is still rolling
        if self.is_shot_in_progress():
            return

        self.club.swing(self.on_ball_contact)

    def on_ball_contact(self):
        """Club has reached the ball at address — launch the putt."""
        # Prevent camera from flipping its position pre-hit
        self.game_camera.capture_follow_offset()

        # Launch the ball along the current aim, harder the fuller the power bar was
        launch_speed = MAX_PUTT_SPEED * self.power_meter.fraction()
        self.ball.launch(self.compute_aim_direction(), launch_speed)
        self.stroke_count += 1


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
