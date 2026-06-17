from math import cos, pi, sin

from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import TextNode


class HelloWorldApp(ShowBase):
    def __init__(self):
        super().__init__()

        # Let the orbit task drive the camera instead of the mouse.
        self.disableMouse()

        # Grassy ground/environment.
        self.environment = self.loader.loadModel("models/environment")
        self.environment.reparentTo(self.render)
        self.environment.setScale(0.25)
        self.environment.setPos(-8, 42, 0)

        # Animated panda walking in place.
        self.panda = Actor(
            "models/panda-model",
            {"walk": "models/panda-walk4"},
        )
        self.panda.setScale(0.005)
        self.panda.reparentTo(self.render)
        self.panda.loop("walk")

        # On-screen greeting.
        self.title = OnscreenText(
            text="Hello, World!",
            pos=(0, -0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 1),
            align=TextNode.ACenter,
            mayChange=False,
        )

        self.taskMgr.add(self.spin_camera_task, "SpinCameraTask")

    def spin_camera_task(self, task):
        """Orbit the camera around the origin, looking at the scene."""
        # 6 degrees per second, frame-rate independent.
        angle_radians = task.time * (6.0 * pi / 180.0) * 3.0
        radius = 20.0
        self.camera.setPos(radius * sin(angle_radians), -radius * cos(angle_radians), 3)
        self.camera.lookAt(0, 0, 0)
        return Task.cont


if __name__ == "__main__":
    app = HelloWorldApp()
    app.run()
