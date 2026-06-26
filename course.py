from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
)
from panda3d.core import NodePath

from constants import (
    ASSET_DIRECTORY,
    ASSET_EXTENSION,
    GREEN_SURFACE_Z,
    SURFACE_FRICTION,
    SURFACE_RESTITUTION,
)

TILE_SIZE = 1.0

TILE_START_ASSET_NAME = "start"
TILE_STRAIGHT_ASSET_NAME = "straight"
TILE_HOLE_ROUND_ASSET_NAME = "hole-round"

COURSE_NODE = "course"
HOLE_NODE = "hole"
TILE_BODY = "tile"


class Course:
    """The playing surface: a run of tiles with mesh colliders, ending in a hole.

    Builds itself under render on construction and exposes two nodes the rest of
    the game needs: `root` (the course subtree) and `hole` (the cup, used as an
    aim target). Construct it with the running ShowBase:

        self.course = Course(self)
    """

    def __init__(self, base: ShowBase) -> None:
        self.base: ShowBase = base
        self.root: NodePath = base.render.attachNewNode(COURSE_NODE)

        hole_tile = self._lay_tiles()
        self.hole: NodePath = self._place_hole(hole_tile)

    def _lay_tiles(self) -> NodePath:
        """Tee off, run down a short fairway. Returns the hole tile (the last one)."""
        self._load_tile(TILE_START_ASSET_NAME, x=0, y=0)
        self._load_tile(TILE_STRAIGHT_ASSET_NAME, x=0, y=1)
        self._load_tile(TILE_STRAIGHT_ASSET_NAME, x=0, y=2)
        self._load_tile(TILE_STRAIGHT_ASSET_NAME, x=0, y=3)

        return self._load_tile(TILE_HOLE_ROUND_ASSET_NAME, x=0, y=4, heading=180)

    def _load_tile(self, name: str, x: int, y: int, heading: float = 0) -> NodePath:
        """Load a tile by name, place it on the grid at (x, y), and collider it."""
        tile = self.base.loader.loadModel(f"{ASSET_DIRECTORY}/{name}{ASSET_EXTENSION}")
        tile.reparentTo(self.root)
        tile.setPos(x * TILE_SIZE, y * TILE_SIZE, 0)
        tile.setH(heading)
        self._make_tile_collider(tile)
        return tile

    def _make_tile_collider(self, model: NodePath) -> NodePath:
        """Build a static collider that traces a tile's mesh."""
        mesh = BulletTriangleMesh()
        for geom_nodepath in model.findAllMatches("**/+GeomNode"):
            geom_node = geom_nodepath.node()
            # Keep each piece's placement relative to the tile root.
            transform = geom_nodepath.getTransform(model)
            for i in range(geom_node.getNumGeoms()):
                mesh.addGeom(geom_node.getGeom(i), True, transform)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        tile_body = BulletRigidBodyNode(TILE_BODY)
        tile_body.addShape(shape)
        tile_body.setFriction(SURFACE_FRICTION)
        tile_body.setRestitution(SURFACE_RESTITUTION)

        collider_nodepath = model.attachNewNode(tile_body)
        self.base.physics_world.attachRigidBody(tile_body)
        return collider_nodepath

    def _place_hole(self, parent: NodePath) -> NodePath:
        """Mark the cup so we can aim shots and the camera at it later."""
        hole = parent.attachNewNode(HOLE_NODE)

        # Cup sits at the center of the hole tile, on the green surface
        hole.setPos(0, 0, GREEN_SURFACE_Z)
        return hole
