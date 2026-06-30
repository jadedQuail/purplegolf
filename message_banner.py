from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode

TEXT_COLOR = (1, 1, 1, 1)
SHADOW_COLOR = (0, 0, 0, 1)
POSITION = (0, 0.7)
SCALE = 0.17

STROKES_SUBTITLE_POSITION = (0, 0.55)
STROKES_SUBTITLE_SCALE = 0.08

ELAPSED_SUBTITLE_POSITION = (0, 0.45)
ELAPSED_SUBTITLE_SCALE = 0.08

RESTART_BUTTON_POSITION = (0, 0, 0.325)
RESTART_BUTTON_SCALE = 0.08
RESTART_BUTTON_PAD = (0.3, 0.3)
RESTART_BUTTON_TEXT_SCALE = 0.7
RESTART_LABEL = "Restart"

WIN_MESSAGE = "You did it!"


class MessageBanner:
    """Large text across the top-center of the screen, with smaller lines beneath."""

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self.text: OnscreenText = self._make_line(POSITION, SCALE)
        self.strokes_subtitle: OnscreenText = self._make_line(
            STROKES_SUBTITLE_POSITION, STROKES_SUBTITLE_SCALE
        )
        self.elapsed_subtitle: OnscreenText = self._make_line(
            ELAPSED_SUBTITLE_POSITION, ELAPSED_SUBTITLE_SCALE
        )
        self.restart_button: DirectButton = DirectButton(
            text=RESTART_LABEL,
            scale=RESTART_BUTTON_SCALE,
            pos=RESTART_BUTTON_POSITION,
            pad=RESTART_BUTTON_PAD,
            text_scale=RESTART_BUTTON_TEXT_SCALE,
        )
        self.restart_button.hide()

    def _make_line(self, position: tuple[float, float], scale: float) -> OnscreenText:
        """Build one hidden, centered line of banner text."""
        line = OnscreenText(
            text="",
            pos=position,
            scale=scale,
            fg=TEXT_COLOR,
            shadow=SHADOW_COLOR,
            align=TextNode.ACenter,
            mayChange=True,
        )
        line.hide()
        return line

    def show_win(self, stroke_count: int, elapsed_seconds: float) -> None:
        """Congratulate the player and report the strokes and time the hole took."""
        self.show(WIN_MESSAGE, f"Strokes: {stroke_count}")
        self.elapsed_subtitle.setText(self.format_elapsed(elapsed_seconds))
        self.elapsed_subtitle.show()
        self.restart_button.show()

    def format_elapsed(self, elapsed_seconds: float) -> str:
        """Player-facing elapsed time, in seconds and milliseconds."""
        return f"Time Elapsed: {elapsed_seconds:.3f}s"

    def show(self, message: str, subtitle: str = "") -> None:
        """Display message across the top of the screen, with an optional smaller line below."""
        self.text.setText(message)
        self.text.show()
        self.strokes_subtitle.setText(subtitle)
        self.strokes_subtitle.show() if subtitle else self.strokes_subtitle.hide()

    def hide(self) -> None:
        """Clear the banner."""
        self.text.hide()
        self.strokes_subtitle.hide()
        self.elapsed_subtitle.hide()
        self.restart_button.hide()
