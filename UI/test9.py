import cv2
import numpy as np
import sys

from os import path
from PyQt5 import QtCore, QtWidgets, QtGui

# class RecordVideo:
#     def __init__(self, camera_port=0):
#         self.camera = cv2.VideoCapture(camera_port)
#         self.running = False

#     def run(self):
#         self.running = True
#         while self.running:
#             read, image = self.camera.read()
#             # TODO: detect faces now

# class FaceDetection:
#     def __init__(self, haar_cascade_filepath):
#         self.classifier = cv2.CascadeClassifier(haar_cascade_filepath)
#         self._min_size = (30, 30)

#     def detect_faces(self, image):
#         # haarclassifiers work better in black and white
#         gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#         gray_image = cv2.equalizeHist(grey_image)

#         faces = self.classifier.detectMultiScale(grey_image, scaleFactor=1.3, minNeighbors=4, flags=cv2.CASCADE_SCALE_IMAGE, min_size=self._min_size)

#         # TODO: Paint on a surface and add the faces.

class RecordVideo(QtCore.QObject):
    image_data = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, camera_port=0, parent=None):
        super().__init__(parent)
        self.camera = cv2.VideoCapture(camera_port)
        self.timer = QtCore.QBasicTimer()

    def start_recording(self):
        self.timer.start(0, self)

    def timerEvent(self, event):
        if (event.timerId() != self.timer.timerId()):
            return

        read, image = self.camera.read()
        if read:
            self.image_data.emit(image)

class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, haar_cascade_filepath, parent=None):
        super().__init__(parent)
        self.classifier = cv2.CascadeClassifier(haar_cascade_filepath)
        self.image = QtGui.QImage()
        self._red = (0, 0, 255)
        self._width = 2
        self._min_size = (30, 30)

    def detect_faces(self, image: np.ndarray):
        # haarclassifiers work better in black and white
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_image = cv2.equalizeHist(gray_image)

        faces = self.classifier.detectMultiScale(gray_image, scaleFactor=1.3, minNeighbors=4, flags=cv2.CASCADE_SCALE_IMAGE, minSize=self._min_size)

        return faces

    def image_data_slot(self, image_data):
        faces = self.detect_faces(image_data)
        for (x, y, w, h) in faces:
            cv2.rectangle(image_data, (x, y), (x+w, y+h), self._red, self._width)

        self.image = self.get_qimage(image_data)
        if self.image.size() != self.size():
            self.setFixedSize(self.image.size())

        self.update()

    def get_qimage(self, image: np.ndarray):
        height, width, colors = image.shape
        bytesPerLine = 3 * width
        QImage = QtGui.QImage

        image = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888)

        image = image.rgbSwapped()

        return image

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.image)
        self.image = QtGui.QImage()

class MainWidget(QtWidgets.QWidget):
    def __init__(self, haarcascade_filepath, parent=None):
        super().__init__(parent)
        fp = haarcascade_filepath
        self.face_detection_widget = FaceDetectionWidget(fp)

        # TODO: set video port
        self.record_video = RecordVideo()
        self.run_button = QtWidgets.QPushButton('Start')

        # Connect the image data signal and slot together
        image_data_slot = self.face_detection_widget.image_data_slot
        self.record_video.image_data.connect(image_data_slot)
        # connect the run button to the start recording slot
        self.run_button.clicked.connect(self.record_video.start_recording)

        # Create and set the layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.face_detection_widget)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

def main(haar_cascade_filepath):
    app = QtWidgets.QApplication(sys.argv)

    main_window = QtWidgets.QMainWindow()
    main_widget = MainWidget(haar_cascade_filepath)
    main_window.setCentralWidget(main_widget)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    script_dir = path.dirname(path.realpath(__file__))
    cascade_filepath = path.join(script_dir, '..', 'data', 'haarcascade_frontalface_default.xml')

    cascade_filepath = path.abspath(cascade_filepath)
    main(cascade_filepath)