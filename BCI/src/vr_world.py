from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
import simplepbr
from panda3d.core import AmbientLight, DirectionalLight
import math

## \class VRWorld
#  \brief Creates a 3D VR environment using Panda3D with a dynamic skybox and lighting system.
#
#  The VRWorld class sets up a Panda3D scene with a skybox model, ambient and directional lighting,
#  and real-time lighting control based on an external score file (e.g., from EEG analysis).
#  It continuously rotates the skybox for visual immersion and adjusts lighting dynamically.
class VRWorld(ShowBase):
    ## \brief Constructor that initializes the 3D world, lighting, and skybox.
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

        # Listen for lighting score updates from file
        self.taskMgr.add(self.listen_for_lighting, "LightingFileListener")

    ## \brief Continuously rotates the skybox to simulate motion.
    #  \param task Panda3D task object.
    #  \return task.cont to continue scheduling the task.
    def rotate_skybox(self, task):
        self.skybox.setH(self.skybox.getH() + 0.02)
        return task.cont

    ## \brief Monitors an external file for lighting control values and updates the scene lighting.
    #
    #  This function reads a score (0–100) from a text file and adjusts ambient and directional
    #  lighting brightness accordingly. Called repeatedly as a Panda3D task.
    #
    #  \param task Panda3D task object.
    #  \return task.cont to keep the listener active.
    def listen_for_lighting(self, task):
        try:
            # with open("/tmp/lighting_value.txt", "r") as f: # Slider Score
            with open("/home/jarred/git/Brainground/BCI/score_output.txt", "r") as f: # Actual Score
                brightness = float(f.read().strip()) / 100.0
                brightness = max(0.0, min(1.0, brightness))
                self.alight.setColor((brightness, brightness, brightness, 1))
                self.dlight.setColor((brightness, brightness, brightness, 1))
        except:
            pass  # File might not exist yet
        return task.cont

## \brief Entry point for running the VR simulation.
if __name__ == "__main__":
    app = VRWorld()
    app.run()