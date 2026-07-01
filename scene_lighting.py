from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, NodePath, Vec4

AMBIENT_COLOR = Vec4(0.45, 0.45, 0.5, 1.0)
SUN_COLOR = Vec4(0.9, 0.9, 0.85, 1.0)
SUN_HEADING = -50.0
SUN_PITCH = -60.0

AMBIENT_NODE = "ambient_light"
SUN_NODE = "sun_light"


class SceneLighting:
    """Basic scene lighting: a soft ambient fill plus one directional "sun"."""

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self._add_ambient()
        self._add_sun()
        base.render.setShaderAuto()

    def _add_ambient(self) -> None:
        """Flat fill so shadowed faces never go fully black."""
        light = AmbientLight(AMBIENT_NODE)
        light.setColor(AMBIENT_COLOR)
        self._attach(light)

    def _add_sun(self) -> None:
        """Directional key light angled across the course."""
        light = DirectionalLight(SUN_NODE)
        light.setColor(SUN_COLOR)
        nodepath = self._attach(light)
        nodepath.setHpr(SUN_HEADING, SUN_PITCH, 0)

    def _attach(self, light) -> NodePath:
        """Parent a light under render and switch it on for the whole scene."""
        nodepath = self.base.render.attachNewNode(light)
        self.base.render.setLight(nodepath)
        return nodepath
