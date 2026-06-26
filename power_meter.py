from direct.gui.DirectGui import DirectWaitBar
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task

RANGE = 100
MIN = 0
FILL_SPEED = 100

SWEEP_UP = 1
SWEEP_DOWN = -1

BAR_COLOR = (1, 0, 0, 1)
FRAME_COLOR = (0.2, 0.2, 0.2, 1)
FRAME_SIZE = (-0.35, 0.35, -0.04, 0.04)
POSITION = (0, 0, -0.85)

TASK_NAME = "charge_power_meter"


class PowerMeter:
    """Red-on-gray bar at the bottom of the screen that charges a putt.

    While charging, the bar sweeps up and down between empty and full; release
    freezes it, and `fraction()` reports how full it landed. Construct it with
    the running ShowBase:

        self.power_meter = PowerMeter(self)
    """

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self.bar: DirectWaitBar = DirectWaitBar(
            value=MIN,
            range=RANGE,
            barColor=BAR_COLOR,
            frameColor=FRAME_COLOR,
            frameSize=FRAME_SIZE,
            pos=POSITION,
        )
        self.direction: int = SWEEP_UP

    def start_charge(self) -> None:
        """Reset to empty and sweep the bar up and down each frame."""
        self.bar["value"] = MIN
        self.direction = SWEEP_UP
        self.base.taskMgr.add(self._charge, TASK_NAME)

    def stop(self) -> None:
        """Freeze the bar wherever it landed."""
        self.base.taskMgr.remove(TASK_NAME)

    def fraction(self) -> float:
        """How full the meter is, from 0.0 (empty) to 1.0 (full)."""
        span = RANGE - MIN
        return (self.bar["value"] - MIN) / span

    def _charge(self, task: Task) -> int:
        """Advance the meter one frame, bouncing off the min and max ends."""
        value = self.bar["value"]
        value += self.direction * FILL_SPEED * self.base.clock.getDt()

        if value >= RANGE:
            value = RANGE
            self.direction = SWEEP_DOWN
        elif value <= MIN:
            value = MIN
            self.direction = SWEEP_UP

        self.bar["value"] = value
        return task.cont
