import cv2
import numpy as np
import glob
import os
import logging

IMAGES_PATH = './images'  # put your reference images in here
CAMERA_DEVICE_ID = 0
MAX_DISTANCE = 0.6  # increase to make recognition less strict, decrease to make more strict

# open a connection to the camera
video_capture = cv2.VideoCapture(CAMERA_DEVICE_ID)

# read from the camera in a loop, frame by frame
while video_capture.isOpened():
    # Grab a single frame of video
    ok, frame = video_capture.read()
    
    #    
    # do face recognition stuff here using this frame...
    #
    
    # Display the image
    cv2.imshow('my_window_name', frame)

    # Hit 'q' on the keyboard to stop the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
# release handle to the webcam
video_capture.release()

# close the window (buggy on a Mac btw)
cv2.destroyAllWindows()

if __name__ == '__main__':
    