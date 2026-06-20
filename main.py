from direct.showbase.ShowBase import ShowBase

# Kenney tiles sit on a 1x1 grid, so stepping position by 1.0 snaps them
# edge-to-edge.
TILE_SIZE = 1.0
ASSET_DIR = "kenney_minigolf-kit/GLB format"


class MinigolfApp(ShowBase):
    def __init__(self):
        super().__init__()

        # No camera dragging
        self.disableMouse()

        self.course = self.render.attachNewNode("course")

        self.build_course(self.course)
        self.frame_camera(self.course)

    def load_tile(self, parent, name, x, y, heading=0):
        """Load a tile by name and place it on the grid at (x, y)."""
        tile = self.loader.loadModel(f"{ASSET_DIR}/{name}.glb")
        tile.reparentTo(parent)
        tile.setPos(x * TILE_SIZE, y * TILE_SIZE, 0)
        tile.setH(heading)
        return tile

    def build_course(self, parent):
        """Tee off, run down a short fairway, into the hole."""
        self.load_tile(parent, "start", 0, 0)
        self.load_tile(parent, "straight", 0, 1)
        self.load_tile(parent, "straight", 0, 2)
        self.load_tile(parent, "straight", 0, 3)
        self.load_tile(parent, "hole-round", 0, 4)

    def frame_camera(self, node):
        """Point the camera at a node so its whole extent is visible."""
        min_pt, max_pt = node.getTightBounds()
        center = (min_pt + max_pt) / 2
        size = (max_pt - min_pt).length()

        self.camera.setPos(center.x, min_pt.y - size * 0.8, center.z + size * 0.8)
        self.camera.lookAt(center)


if __name__ == "__main__":
    app = MinigolfApp()
    app.run()
