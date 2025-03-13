import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QFont
import multiprocessing

class EegInterface(QWidget):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue  # Queue to receive scores from ScanProcessing
        self.file_path = None  # Store the selected file path
        self.selected_channels = None  # Store the selected EEG channels
        self.available_channels = [
            'EEG Fp1-LE', 'EEG F3-LE', 'EEG C3-LE', 'EEG P3-LE', 'EEG O1-LE', 
            'EEG F7-LE', 'EEG T3-LE', 'EEG T5-LE', 'EEG Fz-LE', 'EEG Fp2-LE', 
            'EEG F4-LE', 'EEG C4-LE', 'EEG P4-LE', 'EEG O2-LE', 'EEG F8-LE', 
            'EEG T4-LE', 'EEG T6-LE', 'EEG Cz-LE', 'EEG Pz-LE', 'EEG A2-A1', 
            'EEG 23A-23R', 'EEG 24A-24R'
        ]
        self.init_ui()

    def init_ui(self):
        """Initializes the GUI layout."""
        self.setWindowTitle("EEG Asymmetry Score")
        self.setGeometry(100, 100, 400, 400)
        
        self.layout = QVBoxLayout()
        
        # File selection button
        self.file_button = QPushButton("Select EEG File", self)
        self.file_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.file_button)

        # Channel selection dropdowns
        self.channel1_dropdown = QComboBox(self)
        self.channel1_dropdown.addItems(self.available_channels)
        self.layout.addWidget(self.channel1_dropdown)

        self.channel2_dropdown = QComboBox(self)
        self.channel2_dropdown.addItems(self.available_channels)
        self.layout.addWidget(self.channel2_dropdown)

        # Run scenario button (disabled until a file is selected)
        self.run_button = QPushButton("Run Scenario", self)
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.start_scenario)
        self.layout.addWidget(self.run_button)

        # Score label with larger font
        self.label = QLabel("Waiting for data...")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 14, QFont.Bold))
        self.layout.addWidget(self.label)

        # Add an emoji display for mood representation
        self.emoji_label = QLabel(self)
        self.emoji_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.emoji_label)

        self.setLayout(self.layout)

        # Load emoji images dynamically
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.happy_face = self.load_image(os.path.join(base_path, "/home/jarred/git/Brainground/BCI/img/happy.png"))
        self.neutral_face = self.load_image(os.path.join(base_path, "/home/jarred/git/Brainground/BCI/img/neutral.jpeg"))
        self.sad_face = self.load_image(os.path.join(base_path, "/home/jarred/git/Brainground/BCI/img/sad.png"))
        
        self.emoji_label.setPixmap(self.neutral_face.scaled(80, 80, Qt.KeepAspectRatio))

        # Timer to poll the queue for score updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_for_updates)
        self.timer.start(100)  # Check every 100 ms

    def load_image(self, path):
        """Safely loads an image, handling missing files."""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"⚠️ Warning: Missing image file - {path}")
        return pixmap

    def select_file(self):
        """Opens a file dialog to select an EEG file."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select EEG File", "", "EDF Files (*.edf);;All Files (*)", options=options)
        if file_path:
            self.file_path = file_path
            self.label.setText(f"Selected File: {os.path.basename(file_path)}")
            self.run_button.setEnabled(True)  # Enable run button

    def start_scenario(self):
        """Starts the EEG scenario by sending the file path and channels."""
        if self.file_path:
            print("📤 Sending start command to main process...")
            self.run_button.setEnabled(False)  # Prevent multiple clicks
            self.selected_channels = (
                self.available_channels.index(self.channel1_dropdown.currentText()),
                self.available_channels.index(self.channel2_dropdown.currentText())
            )
            self.queue.put({"command": "start", "file_path": self.file_path, "asymmetry_channels": self.selected_channels})
            print(f"✅ Start command sent with file: {self.file_path} and channels: {self.selected_channels}")

    def check_for_updates(self):
        """Periodically checks for score updates from the queue."""
        while not self.queue.empty():
            message = self.queue.get()
            print(f"📥 Received from queue in GUI: {message}")  # Debugging

            if isinstance(message, dict) and "score" in message:
                self.update_score(message["score"])

    def update_score(self, score):
        """Updates the GUI with the latest asymmetry score."""
        try:
            score_value = float(score)
            self.label.setText(f"Asymmetry Score: {score_value:.2f}")
            self.update_emoji(score_value)
        except ValueError:
            print(f"⚠️ Invalid score received: {score}")

    def update_emoji(self, score):
        """Updates the emoji based on the asymmetry score."""
        if score > 80:
            self.emoji_label.setPixmap(self.happy_face.scaled(80, 80, Qt.KeepAspectRatio))
        elif score >= 50:
            self.emoji_label.setPixmap(self.neutral_face.scaled(80, 80, Qt.KeepAspectRatio))
        else:
            self.emoji_label.setPixmap(self.sad_face.scaled(80, 80, Qt.KeepAspectRatio))

    def run(self):
        """Starts the GUI in the main thread."""
        self.show()