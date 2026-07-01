from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode

TEXT_COLOR = (1, 1, 1, 1)
SHADOW_COLOR = (0, 0, 0, 1)

FRAME_COLOR = (0, 0, 0, 0.6)
FRAME_SIZE = (-0.95, 0.95, -0.55, 0.55)

HEADER_TEXT = "Instructions"
HEADER_POSITION = (0, 0.38)
HEADER_SCALE = 0.14

ACTION_COLUMN_X = -0.7
KEYS_COLUMN_X = 0
FIRST_ROW_Y = 0.18
ROW_SPACING = 0.18
ROW_SCALE = 0.08

GOT_IT_LABEL = "Got it"
GOT_IT_BUTTON_POSITION = (0, 0, -0.425)
GOT_IT_BUTTON_SCALE = 0.08
GOT_IT_BUTTON_PAD = (0.3, 0.3)
GOT_IT_BUTTON_TEXT_SCALE = 0.7

ROWS = (
    ("Aim Left", "A  /  Left Arrow"),
    ("Aim Right", "D  /  Right Arrow"),
    ("Take Shot", "Hold and Release Space"),
)


class InstructionsPanel:
    """Semi-transparent overlay listing the game's controls in two columns."""

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self.frame: DirectFrame = DirectFrame(
            frameColor=FRAME_COLOR,
            frameSize=FRAME_SIZE,
        )
        self._make_text(HEADER_TEXT, HEADER_POSITION, HEADER_SCALE, TextNode.ACenter)

        for index, (action, keys) in enumerate(ROWS):
            row_y = FIRST_ROW_Y - index * ROW_SPACING
            self._make_text(action, (ACTION_COLUMN_X, row_y), ROW_SCALE, TextNode.ALeft)
            self._make_text(keys, (KEYS_COLUMN_X, row_y), ROW_SCALE, TextNode.ALeft)

        self.got_it_button: DirectButton = DirectButton(
            text=GOT_IT_LABEL,
            scale=GOT_IT_BUTTON_SCALE,
            pos=GOT_IT_BUTTON_POSITION,
            pad=GOT_IT_BUTTON_PAD,
            text_scale=GOT_IT_BUTTON_TEXT_SCALE,
            command=self.hide,
            parent=self.frame,
        )

    def _make_text(
        self, text: str, position: tuple[float, float], scale: float, align: int
    ) -> OnscreenText:
        """Attach one line of text to the panel frame."""
        return OnscreenText(
            text=text,
            pos=position,
            scale=scale,
            fg=TEXT_COLOR,
            shadow=SHADOW_COLOR,
            align=align,
            parent=self.frame,
        )

    def show(self) -> None:
        """Bring the panel to the screen."""
        self.frame.show()

    def hide(self) -> None:
        """Remove the panel from the screen."""
        self.frame.hide()
