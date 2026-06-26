from typing import Callable

from direct.interval.IntervalGlobal import Func, LerpHprInterval, Sequence
from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath, Point3

from constants import ASSET_DIRECTORY, ASSET_EXTENSION, GREEN_SURFACE_Z

CLUB_ASSET_NAME = "club-blue"

CLUB_PIVOT_NODE = "club_pivot"
CLUB_ANCHOR_NODE = "club_anchor"

# Club orientation
CLUB_LIE_TILT = 13.7
CLUB_HEAD_OFFSET_X = -0.18
CLUB_HEAD_OFFSET_Y = 0.025

# Putt swing
SWING_BACK_PITCH_DEGREES = -25
SWING_THROUGH_PITCH_DEGREES = 25
SWING_BACK_TIME_SECONDS = 0.4
SWING_THROUGH_TIME_SECONDS = 0.25
SWING_RETURN_TIME_SECONDS = 0.3

# Club is at address (touching the ball) when the pivot pitch is 0,
# so the through-swing passes through contact at this pitch.
SWING_CONTACT_PITCH_DEGREES = 0


class Club:
    """Putter that rests behind the ball and swings on a pivot to strike it.

    Owns the model, the pivot it rotates about, and the anchor that holds it
    behind the ball. Construct it with the running ShowBase, the node to parent
    the club under, and the world-space ball and hole positions to aim from:

        self.club = Club(self, self.course, ball_pos, hole_pos)
    """

    def __init__(
        self, base: ShowBase, parent: NodePath, ball_pos: Point3, hole_pos: Point3
    ) -> None:
        self.base: ShowBase = base
        self.swing_sequence: Sequence | None = None

        club = base.loader.loadModel(f"{ASSET_DIRECTORY}/{CLUB_ASSET_NAME}{ASSET_EXTENSION}")
        club.reparentTo(parent)

        # Rotate face to look down the course
        club.setH(270)
        club.setP(CLUB_LIE_TILT)

        # Place club head on the green
        club_min, _ = club.getTightBounds()
        club.setPos(CLUB_HEAD_OFFSET_X, CLUB_HEAD_OFFSET_Y, GREEN_SURFACE_Z - club_min.z)

        self.club: NodePath = club
        self.pivot: NodePath = self._add_swing_pivot(club, parent)
        self.anchor: NodePath = base.render.attachNewNode(CLUB_ANCHOR_NODE)

        # Position the anchor before reparenting so the pivot keeps its world transform
        self.aim_behind(ball_pos, hole_pos)
        self.pivot.wrtReparentTo(self.anchor)

    def aim_behind(self, ball_pos: Point3, hole_pos: Point3) -> None:
        """Place the club behind the ball, aimed down the line to the hole."""
        self.anchor.setPos(ball_pos)
        self.anchor.lookAt(self.base.render, Point3(hole_pos.x, hole_pos.y, ball_pos.z))

    def is_swinging(self) -> bool:
        """True while the club is mid-stroke."""
        return self.swing_sequence is not None and self.swing_sequence.isPlaying()

    def swing(self, on_contact: Callable[[], None]) -> None:
        """Play one putt stroke: back, through contact, then settle to rest.

        Calls on_contact at the instant the club reaches the ball at address.
        """
        # Split swing so we can find the moment the club hits the ball (pitch = 0)
        half_through_time = SWING_THROUGH_TIME_SECONDS / 2

        self.swing_sequence = Sequence(
            LerpHprInterval(self.pivot, SWING_BACK_TIME_SECONDS, (0, SWING_BACK_PITCH_DEGREES, 0)),
            LerpHprInterval(self.pivot, half_through_time, (0, SWING_CONTACT_PITCH_DEGREES, 0)),
            Func(on_contact),
            LerpHprInterval(self.pivot, half_through_time, (0, SWING_THROUGH_PITCH_DEGREES, 0)),
            LerpHprInterval(self.pivot, SWING_RETURN_TIME_SECONDS, (0, 0, 0)),
        )
        self.swing_sequence.start()

    def _add_swing_pivot(self, club: NodePath, parent: NodePath) -> NodePath:
        """Set the pivot point to the top of the club."""
        club_min, club_max = club.getTightBounds(parent)
        pivot = parent.attachNewNode(CLUB_PIVOT_NODE)
        # Pivot point set to top of club
        pivot.setPos(
            (club_min.x + club_max.x) / 2,
            (club_min.y + club_max.y) / 2,
            club_max.z,
        )
        club.wrtReparentTo(pivot)
        return pivot
