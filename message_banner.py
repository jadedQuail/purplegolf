from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode

TEXT_COLOR = (1, 1, 1, 1)
SHADOW_COLOR = (0, 0, 0, 1)
POSITION = (0, 0.7)
SCALE = 0.17


class MessageBanner:
    """Large text across the top-center of the screen for game messages."""

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self.text: OnscreenText = OnscreenText(
            text="",
            pos=POSITION,
            scale=SCALE,
            fg=TEXT_COLOR,
            shadow=SHADOW_COLOR,
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.text.hide()

    def show(self, message: str) -> None:
        """Display message across the top of the screen."""
        self.text.setText(message)
        self.text.show()

    def hide(self) -> None:
        """Clear the banner."""
        self.text.hide()
