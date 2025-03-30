from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
import simplepbr
from panda3d.core import AmbientLight, DirectionalLight
import math

class VRWorld(ShowBase):
    def __init__(self):
        super().__init__()
        simplepbr.init()

        # Load the skybox model
        self.skybox = self.loader.loadModel("/home/jarred/git/Brainground/BCI/models/skybox.bam")
        self.skybox.reparentTo(self.render)
        self.skybox.set_scale(10000)

        # Add Ambient Lighting
        self.alight = AmbientLight('alight')
        self.alight.setColor((0.75, 0.75, 0.75, 1))
        alnp = self.render.attachNewNode(self.alight)
        self.render.setLight(alnp)

        # Add Directional Lighting
        self.dlight = DirectionalLight('dlight')
        self.dlight.setColor((1.0, 1.0, 1.0, 1))
        dlnp = self.render.attachNewNode(self.dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        # Rotate the skybox slowly
        self.taskMgr.add(self.rotate_skybox, "RotateSkyboxTask")

        # Animate lighting over time (sunrise/sunset effect)
        self.taskMgr.add(self.animate_lighting, "AnimateLightingTask")

    def rotate_skybox(self, task):
        self.skybox.setH(self.skybox.getH() + 0.02)
        return task.cont

    def animate_lighting(self, task):
        brightness = 0.5 + 0.5 * math.sin(task.time * 0.2)
        warm = 0.7 + 0.3 * math.sin(task.time * 0.2)

        self.alight.setColor((brightness, brightness, brightness, 1))
        self.dlight.setColor((warm, warm * 0.9, brightness * 0.8, 1))
        return task.cont

if __name__ == "__main__":
    app = VRWorld()
    app.run()