from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
import openvr
import os

class VRBeachWorld(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Try initializing OpenVR
        try:
            self.vr_system = openvr.init(openvr.VRApplication_Scene)
            print("OpenVR initialized successfully.")
        except openvr.error_code.InitError as e:
            print(f"OpenVR not available: {e}. Running in non-VR mode.")
            self.vr_system = None  # Continue without VR

        # Force Panda3D to recognize the models directory
        getModelPath().appendDirectory(Filename.fromOsSpecific("/home/jarred/git/Brainground/BCI/models/"))

        # Load the skybox
        self.skybox = loader.loadModel("skybox.egg")  # Load skybox model
        if self.skybox:
            print("Skybox loaded successfully!")
            self.skybox.setScale(500)  # Make it large
            self.skybox.reparentTo(render)
        else:
            print("Error: Skybox model failed to load!")

        # Weather settings
        self.weather = "Sunny"
        self.accept("w", self.toggle_weather)

        # Lighting (default: Sunny)
        self.setup_lighting("Sunny")

    def setup_lighting(self, condition):
        render.clearLight()
        if condition == "Sunny":
            sunlight = DirectionalLight("sunlight")
            sunlight.setColor((1, 1, 0.8, 1))  # Warm sunlight
            sun = render.attachNewNode(sunlight)
            sun.setHpr(45, -60, 0)
            render.setLight(sun)
        elif condition == "Cloudy":
            ambient = AmbientLight("cloudy")
            ambient.setColor((0.5, 0.5, 0.6, 1))  # Dimmer lighting
            render.setLight(render.attachNewNode(ambient))
        elif condition == "Rainy":
            ambient = AmbientLight("rainy")
            ambient.setColor((0.3, 0.3, 0.5, 1))  # Dark blueish lighting
            render.setLight(render.attachNewNode(ambient))
            
    def toggle_weather(self):
        if self.weather == "Sunny":
            self.weather = "Cloudy"
        elif self.weather == "Cloudy":
            self.weather = "Rainy"
        else:
            self.weather = "Sunny"
        self.setup_lighting(self.weather)
        print(f"Weather changed to: {self.weather}")

    def cleanup(self):
        openvr.shutdown()

app = VRBeachWorld()
app.run()
