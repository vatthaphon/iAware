# -*- coding: utf-8 -*-
# vispy: gallery 30
# -----------------------------------------------------------------------------
# Copyright (c) 2014, Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
"""
This example demonstrates the use of the SurfacePlot visual.
"""

import sys
import numpy as np

from vispy import app, scene
from vispy.util.filter import gaussian_filter

canvas      = scene.SceneCanvas(keys='interactive')
view        = canvas.central_widget.add_view()
view.camera = scene.TurntableCamera(up='z')

N = 50
def generate(i): #this seems to be  the fastest way to create an array
    return np.fromfunction(lambda x, y: np.sin(np.sqrt((((x/N)-0.5)*i)*(((x/N)-0.5)*i) + (((y/N)-0.5)*i)*(((y/N)-0.5)*i)))/np.sqrt((((x/N)-0.5)*i)*(((x/N)-0.5)*i) + (((y/N)-0.5)*i)*(((y/N)-0.5)*i)), (N, N), dtype=np.float32)    


p1           = scene.visuals.SurfacePlot(z=generate(1.0), color=(0.9, 0.2, 0.5, 1), shading='smooth')
# p1.transform = scene.transforms.AffineTransform()
# p1.transform.scale([1/49., 1/49., 1.0])
# p1.transform.translate([-0.5, -0.5, 0])

view.add(p1)

# Add a 3D axis to keep us oriented
axis = scene.visuals.XYZAxis(parent=view.scene)
i = 1.0
def update(ev):
    global p1
    global i
    i += 1.0
    p1.set_data(z=generate(i))

timer = app.Timer()
timer.connect(update)
timer.start(0)



if __name__ == '__main__':
    canvas.show()
    if sys.flags.interactive == 0:
        app.run()