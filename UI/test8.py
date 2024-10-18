from PyQt5.QtWidgets import *
import vispy.app
import sys

canvas = vispy.app.Canvas()
w = QMainWindow()
widget = QWidget()
w.setCentralWidget(widget)
widget.setLayout(QVBoxLayout())
widget.layout().addWidget(canvas.native)
widget.layout().addWidget(QPushButton())
w.show()
vispy.app.run()