from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import Vec3

from ball import Ball

CAMERA_BACK_DISTANCE = 5.0
CAMERA_HEIGHT = 3.5
GAME_CAMERA_TASK_NAME = "update_game_camera"


class GameCamera:
    """Gameplay view: sits behind and above the ball, then trails it as it rolls.

    Holds the ball it tracks and frames each putt from behind, aimed at the hole
    (the App supplies the ball-to-hole direction). Construct it with the running
    ShowBase and the ball to follow:

        self.game_camera = GameCamera(self, self.ball)
    """

    def __init__(self, base: ShowBase, ball: Ball) -> None:
        self.base: ShowBase = base
        self.ball: Ball = ball
        self.active: bool = True
        # Camera-to-ball offset captured at contact, used to trail the ball while it rolls
        self.follow_offset: Vec3 = Vec3(0, 0, 0)
        base.taskMgr.add(self._follow, GAME_CAMERA_TASK_NAME)

    def position_behind(self, to_hole: Vec3) -> None:
        """Park behind and above the ball, opposite the hole, aimed at the ball."""
        ball_pos = self.ball.nodepath.getPos(self.base.render)

        # Sit CAMERA_BACK_DISTANCE behind the ball, opposite the hole
        self.base.camera.setPos(
            ball_pos.x - to_hole.x * CAMERA_BACK_DISTANCE,
            ball_pos.y - to_hole.y * CAMERA_BACK_DISTANCE,
            ball_pos.z + CAMERA_HEIGHT,
        )
        self.base.camera.lookAt(self.ball.nodepath)

    def capture_follow_offset(self) -> None:
        """Freeze the current framing so the camera can trail the rolling ball."""
        ball_pos = self.ball.nodepath.getPos(self.base.render)
        self.follow_offset = self.base.camera.getPos(self.base.render) - ball_pos

    def _follow(self, task: Task) -> int:
        """Trail the ball while it rolls, holding the framing from the putt."""
        if self.active and self.ball.is_rolling():
            ball_pos = self.ball.nodepath.getPos(self.base.render)
            self.base.camera.setPos(ball_pos + self.follow_offset)
            self.base.camera.lookAt(self.ball.nodepath)
        return task.cont
