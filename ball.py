from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import BulletRigidBodyNode, BulletSphereShape
from panda3d.core import NodePath, Vec3

from constants import (
    ASSET_DIRECTORY,
    ASSET_EXTENSION,
    GREEN_SURFACE_Z,
    SURFACE_FRICTION,
    SURFACE_RESTITUTION,
)

BALL_ASSET_NAME = "ball-blue"
BALL_BODY = "ball"

BALL_MASS = 1.0
ROLLING_RESISTANCE_CONSTANT = 0.12
ROLLING_DRAG = 0.7


class Ball:
    """Blue ball seated on the green as a dynamic Bullet sphere.

    Owns its visual model, rigid body, and node. Hand it the running ShowBase
    and the node to parent it under:

        self.ball = Ball(self, self.render)
    """

    def __init__(self, base: ShowBase, parent: NodePath) -> None:
        model = base.loader.loadModel(f"{ASSET_DIRECTORY}/{BALL_ASSET_NAME}{ASSET_EXTENSION}")

        # model can be aligned to the body origin (where the sphere sits).
        ball_min, ball_max = model.getTightBounds()
        radius = (ball_max.z - ball_min.z) / 2
        center = (ball_min + ball_max) / 2

        body = BulletRigidBodyNode(BALL_BODY)
        body.addShape(BulletSphereShape(radius))
        body.setMass(BALL_MASS)
        body.setFriction(SURFACE_FRICTION)
        body.setRestitution(SURFACE_RESTITUTION)

        nodepath = parent.attachNewNode(body)
        nodepath.setPos(0, 0.15, GREEN_SURFACE_Z + radius)

        # Park the visual model under the body, centered on the body origin.
        model.reparentTo(nodepath)
        model.setPos(-center)

        base.physics_world.attachRigidBody(body)
        body.setActive(False)

        self.model: NodePath = model
        self.body: BulletRigidBodyNode = body
        self.nodepath: NodePath = nodepath

    def is_rolling(self) -> bool:
        """True while the ball is still moving under physics."""
        return self.body.isActive()

    def launch(self, direction: Vec3, speed: float) -> None:
        """Send the ball off at speed along direction and wake the body."""
        self.body.setLinearVelocity(direction * speed)
        self.body.setActive(True)

    def apply_rolling_resistance(self, dt: float) -> bool:
        """Shave a constant amount of speed each frame.

        Returns True on the step the ball settles to a full stop, so the
        caller can set up the next shot.
        """
        if not self.body.isActive():
            return False

        velocity = self.body.getLinearVelocity()
        speed = Vec3(velocity.x, velocity.y, 0).length()
        if speed == 0:
            return False

        decrement = (ROLLING_RESISTANCE_CONSTANT + ROLLING_DRAG * speed) * dt
        if decrement >= speed:
            # Next step would cross zero -> settle to a full stop at near-zero speed.
            self.body.setLinearVelocity(Vec3(0, 0, 0))
            self.body.setAngularVelocity(Vec3(0, 0, 0))
            self.body.setActive(False)
            return True

        # Scale linear and spin together so the ball keeps rolling consistently
        scale = (speed - decrement) / speed
        self.body.setLinearVelocity(Vec3(velocity.x * scale, velocity.y * scale, velocity.z))
        self.body.setAngularVelocity(self.body.getAngularVelocity() * scale)
        return False
