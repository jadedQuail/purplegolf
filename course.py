from direct.showbase.ShowBase import ShowBase
from panda3d.bullet import (
    BulletRigidBodyNode,
    BulletTriangleMesh,
    BulletTriangleMeshShape,
)
from panda3d.core import Geom, GeomVertexReader, Mat4, NodePath, Point3, Vec3

from constants import (
    ASSET_DIRECTORY,
    ASSET_EXTENSION,
    GREEN_SURFACE_Z,
    SURFACE_FRICTION,
    SURFACE_RESTITUTION,
)

TILE_SIZE = 1.0
LAST_TILE_Y = 4

GROUND_MIN_X = -TILE_SIZE / 2
GROUND_MAX_X = TILE_SIZE / 2
GROUND_MIN_Y = -TILE_SIZE / 2
GROUND_MAX_Y = LAST_TILE_Y * TILE_SIZE + TILE_SIZE / 2

HOLE_CENTER_X = 0.0
HOLE_CENTER_Y = LAST_TILE_Y * TILE_SIZE
HOLE_GAP_HALF = 0.045
HOLE_DEPTH = 0.15

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
        """A flat floor the ball rolls on, built as a mesh we can carve later."""
        mesh = BulletTriangleMesh()
        self._add_floor_quads(mesh)
        self._add_cup(mesh)

        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        body = BulletRigidBodyNode(GROUND_BODY)
        body.addShape(shape)
        body.setFriction(SURFACE_FRICTION)
        body.setRestitution(SURFACE_RESTITUTION)

        self.root.attachNewNode(body)
        self.base.physics_world.attachRigidBody(body)

    def _add_floor_quads(self, mesh: BulletTriangleMesh) -> None:
        """Lay the green flat, leaving a square gap at the cup for the ball to drop through."""
        gap_min_x = HOLE_CENTER_X - HOLE_GAP_HALF
        gap_max_x = HOLE_CENTER_X + HOLE_GAP_HALF
        gap_min_y = HOLE_CENTER_Y - HOLE_GAP_HALF
        gap_max_y = HOLE_CENTER_Y + HOLE_GAP_HALF

        self._add_quad(mesh, GROUND_MIN_X, gap_min_x, GROUND_MIN_Y, GROUND_MAX_Y)
        self._add_quad(mesh, gap_max_x, GROUND_MAX_X, GROUND_MIN_Y, GROUND_MAX_Y)
        self._add_quad(mesh, gap_min_x, gap_max_x, GROUND_MIN_Y, gap_min_y)
        self._add_quad(mesh, gap_min_x, gap_max_x, gap_max_y, GROUND_MAX_Y)

    def _add_quad(self, mesh: BulletTriangleMesh, x0: float, x1: float, y0: float, y1: float) -> None:
        """Add one flat quad (two upward-facing triangles) at the green surface."""
        self._add_face(
            mesh,
            Point3(x0, y0, GREEN_SURFACE_Z),
            Point3(x1, y0, GREEN_SURFACE_Z),
            Point3(x1, y1, GREEN_SURFACE_Z),
            Point3(x0, y1, GREEN_SURFACE_Z),
        )

    def _add_cup(self, mesh: BulletTriangleMesh) -> None:
        """Build an open-topped box under the gap so the ball drops in and is held."""
        min_x = HOLE_CENTER_X - HOLE_GAP_HALF
        max_x = HOLE_CENTER_X + HOLE_GAP_HALF
        min_y = HOLE_CENTER_Y - HOLE_GAP_HALF
        max_y = HOLE_CENTER_Y + HOLE_GAP_HALF
        top_z = GREEN_SURFACE_Z
        bottom_z = GREEN_SURFACE_Z - HOLE_DEPTH

        bottom_sw = Point3(min_x, min_y, bottom_z)
        bottom_se = Point3(max_x, min_y, bottom_z)
        bottom_ne = Point3(max_x, max_y, bottom_z)
        bottom_nw = Point3(min_x, max_y, bottom_z)
        top_sw = Point3(min_x, min_y, top_z)
        top_se = Point3(max_x, min_y, top_z)
        top_ne = Point3(max_x, max_y, top_z)
        top_nw = Point3(min_x, max_y, top_z)

        self._add_face(mesh, bottom_sw, bottom_se, bottom_ne, bottom_nw)
        self._add_face(mesh, bottom_sw, bottom_se, top_se, top_sw)
        self._add_face(mesh, bottom_nw, bottom_ne, top_ne, top_nw)
        self._add_face(mesh, bottom_sw, bottom_nw, top_nw, top_sw)
        self._add_face(mesh, bottom_se, bottom_ne, top_ne, top_se)

    def _add_face(
        self, mesh: BulletTriangleMesh, corner_a: Point3, corner_b: Point3, corner_c: Point3, corner_d: Point3
    ) -> None:
        """Add a quad as two triangles, given its four corners in loop order."""
        mesh.addTriangle(corner_a, corner_b, corner_c)
        mesh.addTriangle(corner_a, corner_c, corner_d)

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
