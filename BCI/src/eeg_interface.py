import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from multiprocessing import Queue

class EegInterface(QWidget):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue  # Queue to receive scores from ScanProcessing
        self.init_ui()

    def init_ui(self):
        """Initializes the GUI layout."""
        self.setWindowTitle("EEG Asymmetry Score")
        self.setGeometry(100, 100, 300, 250)
        
        self.layout = QVBoxLayout()
        self.label = QLabel("Waiting for data...")
        self.layout.addWidget(self.label)

        # Add an emoji display for mood representation
        self.emoji_label = QLabel(self)
        self.layout.addWidget(self.emoji_label)

        self.setLayout(self.layout)

        # Load emoji images
        self.happy_face = QPixmap("/home/jarred/git/Brainground/BCI/img/happy.png")  # High score
        self.neutral_face = QPixmap("/home/jarred/git/Brainground/BCI/img/neutral.jpeg")  # Medium score
        self.sad_face = QPixmap("/home/jarred/git/Brainground/BCI/img/sad.png")  # Low score
        
        self.emoji_label.setPixmap(self.neutral_face)

        # Timer to update the score periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_score)
        self.timer.start(100)  # Update every 500 ms

    def update_score(self):
        """Updates the GUI with the latest asymmetry score."""
        if not self.queue.empty():
            score = self.queue.get()
            self.label.setText(f"Asymmetry Score: {score:.2f}")
            self.update_emoji(score)

    def update_emoji(self, score):
        """Updates the emoji based on the asymmetry score."""
        if score > 80:
            self.emoji_label.setPixmap(self.happy_face)
        elif score >= 50:
            self.emoji_label.setPixmap(self.neutral_face)
        else:
            self.emoji_label.setPixmap(self.sad_face)

    @staticmethod
    def run(queue):
        """Starts the PyQt application in a separate process."""
        app = QApplication(sys.argv)
        interface = EegInterface(queue)
        interface.show()
        sys.exit(app.exec_())