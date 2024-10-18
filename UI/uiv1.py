import _thread
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import pyqtgraph as pg
import socket
import sys
import threading
import time


from PIL import Image
from pyqtgraph import PlotWidget
from pyqtgraph.opengl import GLViewWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5CUMatDesComps import *
from socket import SHUT_RDWR


ROOTPATH_g = (os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")).split("/Data")[0]

sys.path.append(ROOTPATH_g + "/Data/Work/UtilSrcCode/python-DeviceInterface")
from AV_DeviceInterface import EEGClientThread

_fromUtf8 = lambda s: s

class UI(CUMatDesQMainWindow):

    # def __init__(self, eegclientThread_p, refreshRate_p, main_p=None):
    def __init__(self, refreshRate_p, main_p=None):

        super(UI, self).__init__()

        # self.resize(660, 562)

        self.__main = main_p

        # self.showMaximized()
        # QMainWindow requires these two lines, otherwise we cannot set its layout.
        wid = QtGui.QWidget(self)
        self.setCentralWidget(wid)


        # pg.setConfigOption('background', (230, 233, 237))
        # pg.setConfigOption('background', (255, 255, 255))
        # pg.setConfigOption('background', None)
        # pg.setConfigOption('foreground', 'k')        

        ##### Set layouts
        main_layout = QtWidgets.QHBoxLayout()

        left_main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(left_main_layout)

        right_main_layout = QtWidgets.QVBoxLayout()        
        main_layout.addLayout(right_main_layout)

        top_left_main_layout = QtWidgets.QHBoxLayout()
        left_main_layout.addLayout(top_left_main_layout)

        bottom_left_main_layout = QtWidgets.QVBoxLayout()
        left_main_layout.addLayout(bottom_left_main_layout)

        left_top_left_main_layout = QtWidgets.QVBoxLayout()
        top_left_main_layout.addLayout(left_top_left_main_layout)

        ##### Create items
        self.__buttonCalibrate = CUMatDesQPushButton("Calibrate", self)
        self.__buttonCalibrate.clicked.connect(self.handleCalibrate)

        self.__buttonStart = CUMatDesQPushButton("Start", self)
        self.__buttonStart.clicked.connect(self.handleStart)

        self.__buttonPause = CUMatDesQPushButton("Pause", self)
        self.__buttonPause.clicked.connect(self.handlePause)

        self.__buttonStop = CUMatDesQPushButton("Stop", self)
        self.__buttonStop.clicked.connect(self.handleStop)

        self.__buttonSignOut = CUMatDesQPushButton("Sign out", self)
        self.__buttonSignOut.clicked.connect(self.handleSignOut)

        self.__linePlot0 = PlotWidget(self)
        self.__linePlot0.setObjectName("linePlot0")

        self.__linePlot0_TP9_PlotCurveItem = pg.PlotCurveItem()
        self.__linePlot0_AF7_PlotCurveItem = pg.PlotCurveItem()
        self.__linePlot0_AF8_PlotCurveItem = pg.PlotCurveItem()
        self.__linePlot0_TP10_PlotCurveItem = pg.PlotCurveItem()
        self.__linePlot0_VLine_PlotCurveItem = pg.PlotCurveItem()

        self.__linePlot0.addItem(self.__linePlot0_TP9_PlotCurveItem)
        self.__linePlot0.addItem(self.__linePlot0_AF7_PlotCurveItem)
        self.__linePlot0.addItem(self.__linePlot0_AF8_PlotCurveItem)
        self.__linePlot0.addItem(self.__linePlot0_TP10_PlotCurveItem)
        self.__linePlot0.addItem(self.__linePlot0_VLine_PlotCurveItem)        

        self.__imgPlot0 = QtWidgets.QLabel(self)        
        myPixmap_l = QtGui.QPixmap(_fromUtf8("./pic/meditation.jpg"))
        pix_ratio_l = 1.0
        self.__imgPlot0.resize(myPixmap_l.size().width()*pix_ratio_l, myPixmap_l.size().height()*pix_ratio_l)
        # myScaledPixmap_l = myPixmap_l.scaled(self.__imgPlot0.size(), Qt.KeepAspectRatio)
        myScaledPixmap_l = myPixmap_l.scaled(self.__imgPlot0.size())
        self.__imgPlot0.setPixmap(myScaledPixmap_l)
        self.__imgPlot0.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.__labelStat0 = CUMatDesQLabel("Stat0: 0", self)
        self.__labelStat1 = CUMatDesQLabel("Stat1: 0", self)
        self.__labelStat2 = CUMatDesQLabel("Stat2: 0", self)
        self.__labelStat3 = CUMatDesQLabel("Stat3: 0", self)


        right_main_layout.addWidget(self.__buttonCalibrate)
        right_main_layout.addWidget(self.__buttonStart)
        right_main_layout.addWidget(self.__buttonPause)
        right_main_layout.addWidget(self.__buttonStop)
        right_main_layout.addWidget(self.__buttonSignOut)

        bottom_left_main_layout.addWidget(self.__linePlot0)
        top_left_main_layout.addWidget(self.__imgPlot0)

        left_top_left_main_layout.addWidget(self.__labelStat0)
        left_top_left_main_layout.addWidget(self.__labelStat1)
        left_top_left_main_layout.addWidget(self.__labelStat2)
        left_top_left_main_layout.addWidget(self.__labelStat3)

        wid.setLayout(main_layout)        

        ##### Set timer to update the plots.
        self.__refreshRatetimer = QtCore.QTimer(self)
        self.__refreshRatetimer.timeout.connect(self._plot)
        # self.__refreshRatetimer.start(1000/refreshRate_p) # in milliseconds
        self.__refreshRatetimer.setInterval(1000/refreshRate_p) # in milliseconds
        # self.__refreshRatetimer.stop()

        # self.__eegclientThread = eegclientThread_p
        self.__eegclientThread = None

        self.init()

    def init(self):
        pass

    def handleSignOut(self):
        pass

    def handleStop(self):
        pass

    def handlePause(self):
        pass

    def handleStart(self):
        pass

    def handleCalibrate(self):
        pass

    # def closeEvent(self, event):

    #     self.__eegclientThread.terminate()
    #     event.accept() # let the window close

    def closeEvent(self, event):
        
        self.stop()

        if self.__main is not None:
            event.ignore() # let the window close

            self.__main.hideMainUI()
            self.__main.showLogin()
        else:
            event.accept()

    def run(self):

        iaware_l = EEGClientThread(N_channels_p=1, samples_duration_p=2)
        iaware_l.createTCPClient(buff_socket_size_p=1000, server_ip_p="192.168.4.1", server_port_p=5000, Fs_senddata_p=10, Fs_p=500, Name_p="iAwareClient")
        iaware_l.start()

        self.__eegclientThread = iaware_l
        self.__refreshRatetimer.start()

        self.showMaximized()

    def stop(self):

        if self.__eegclientThread is not None:
            self.__eegclientThread.terminate()

        self.__refreshRatetimer.stop()

    def exit(self):

        if self.__eegclientThread is not None:
            self.__eegclientThread.terminate()

        self.__refreshRatetimer.stop()            

        self.close()

    ##### Refresh
    def _plot(self):
        try:

            freq_positive_l, fft_pw_ch1_l = self.__eegclientThread.getFFTPower()
            # idx_samples_l, samples_l = self.__eegclientThread.getRawData()

            # self.__linePlot0_PlotCurveItems[i_channels_g].setData(x=time_downsampled_EEG_data_linePlot0_g, y=filtered_l)            

            # # print(np.shape(samples_l))

            # y_min_linePlot0_g = np.min(samples_l[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g])
            # y_min_linePlot0_g = y_min_linePlot0_g - 0.1*y_min_linePlot0_g
            # y_max_linePlot0_g = np.max(samples_l[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g])
            # y_max_linePlot0_g = y_max_linePlot0_g + 0.1*y_max_linePlot0_g
            # self.__linePlot0_PlotCurveItems[-1].setData(x=[(i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g, (i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g], y=[y_min_linePlot0_g, y_max_linePlot0_g])

            #  # self.__linePlot0_TP9_PlotCurveItem.setData(x=time_downsampled_EEG_data_linePlot0_g, y=filtered_l)            
            self.__linePlot0_TP9_PlotCurveItem.setData(x=freq_positive_l, y=fft_pw_ch1_l)            

        except Exception as e:
            pass

# def run(main_p):

#     iaware_l = EEGClientThread(N_channels_p=1, samples_duration_p=2)
#     iaware_l.createTCPClient(buff_socket_size_p=1000, server_ip_p="192.168.4.1", server_port_p=5000, Fs_senddata_p=10, Fs_p=500, Name_p="iAwareClient")
#     iaware_l.start()

#     window_l = UI(eegclientThread_p=iaware_l, refreshRate_p=20, main_p=main_p)        

#     return window_l                

if __name__ == '__main__':
    app_l = QtWidgets.QApplication(sys.argv)

    # iaware_l = EEGClientThread(N_channels_p=4, samples_duration_p=2)
    # iaware_l.createMuseMonitorClient(server_ip_p="192.168.0.101", server_port_p=5000, Name_p="MuseMonitor")

    # iaware_l = EEGClientThread(N_channels_p=1, samples_duration_p=2)
    # iaware_l.createTCPClient(buff_socket_size_p=1000, server_ip_p="192.168.4.1", server_port_p=5000, Fs_senddata_p=10, Fs_p=500, Name_p="iAwareClient")
    # iaware_l.start()

    window_l = UI(refreshRate_p=20)
    window_l.run()
    window_l.show()

    sys.exit(app_l.exec_())

