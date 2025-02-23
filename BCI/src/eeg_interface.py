import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from multiprocessing import Queue

class EegInterface(QWidget):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue  # Queue to receive scores from ScanProcessing
        self.init_ui()

    def init_ui(self):
        """Initializes the GUI layout."""
        self.setWindowTitle("EEG Asymmetry Score")
        self.setGeometry(100, 100, 300, 150)
        
        self.layout = QVBoxLayout()
        self.label = QLabel("Waiting for data...")
        self.layout.addWidget(self.label)
        
        self.setLayout(self.layout)
        
        # Timer to update the score periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_score)
        self.timer.start(500)  # Update every 500 ms

    def update_score(self):
        """Updates the GUI with the latest asymmetry score."""
        while not self.queue.empty():
            try:
                score = self.queue.get_nowait()  # Non-blocking queue retrieval
                if isinstance(score, (int, float)):  # Ensure valid numerical score
                    self.label.setText(f"Asymmetry Score: {score:.2f}")
                else:
                    print(f"⚠️ Invalid data received in GUI queue: {score}")  # Debugging
            except Exception as e:
                print(f"❌ Error retrieving score from queue: {e}")

    @staticmethod
    def run(queue):
        """Starts the PyQt application in a separate process."""
        app = QApplication(sys.argv)
        interface = EegInterface(queue)
        interface.show()
        sys.exit(app.exec_())