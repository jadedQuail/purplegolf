from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletPlaneShape,
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
)
from panda3d.core import Geom, GeomVertexReader, Mat4, NodePath, Vec3

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
GROUND_BODY = "ground"

WALL_MIN_Z = GREEN_SURFACE_Z + 0.01


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

        self._make_ground()
        hole_tile = self._lay_tiles()
        self.hole: NodePath = self._place_hole(hole_tile)

    def _make_ground(self) -> None:
        """A single flat plane the ball rolls on, so the green is perfectly level."""
        shape = BulletPlaneShape(Vec3(0, 0, 1), GREEN_SURFACE_Z)
        body = BulletRigidBodyNode(GROUND_BODY)
        body.addShape(shape)
        body.setFriction(SURFACE_FRICTION)
        body.setRestitution(SURFACE_RESTITUTION)

        self.root.attachNewNode(body)
        self.base.physics_world.attachRigidBody(body)

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
        """Build a static collider tracing only a tile's raised walls.

        The flat green is handled by the shared ground plane, so the ball never
        rolls over the tile mesh's faceted, slightly-uneven surface triangles.
        """
        mesh = BulletTriangleMesh()
        for geom_nodepath in model.findAllMatches("**/+GeomNode"):
            geom_node = geom_nodepath.node()
            to_tile = geom_nodepath.getTransform(model).getMat()
            for i in range(geom_node.getNumGeoms()):
                self._add_wall_triangles(mesh, geom_node.getGeom(i), to_tile)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        tile_body = BulletRigidBodyNode(TILE_BODY)
        tile_body.addShape(shape)
        tile_body.setFriction(SURFACE_FRICTION)
        tile_body.setRestitution(SURFACE_RESTITUTION)

        collider_nodepath = model.attachNewNode(tile_body)
        self.base.physics_world.attachRigidBody(tile_body)
        return collider_nodepath

    def _add_wall_triangles(self, mesh: BulletTriangleMesh, geom: Geom, to_tile: Mat4) -> None:
        """Add a geom's triangles to mesh, skipping any that lie at or below the green."""
        vertex = GeomVertexReader(geom.getVertexData(), "vertex")
        for primitive in geom.getPrimitives():
            triangles = primitive.decompose()
            for t in range(triangles.getNumPrimitives()):
                start = triangles.getPrimitiveStart(t)
                end = triangles.getPrimitiveEnd(t)
                corners = []
                for index in range(start, end):
                    vertex.setRow(triangles.getVertex(index))
                    corners.append(to_tile.xformPoint(vertex.getData3()))
                if max(corner.z for corner in corners) > WALL_MIN_Z:
                    mesh.addTriangle(corners[0], corners[1], corners[2])

    def _place_hole(self, parent: NodePath) -> NodePath:
        """Mark the cup so we can aim shots and the camera at it later."""
        hole = parent.attachNewNode(HOLE_NODE)

        # Cup sits at the center of the hole tile, on the green surface
        hole.setPos(0, 0, GREEN_SURFACE_Z)
        return hole
