# -*- coding: utf-8 -*-
"""
Simple example of loading UI template created with Qt Designer.

The application uses uic.loadUiType to parse and load the ui at runtime. It is also
possible to pre-compile the .ui file using pyuic (see VideoSpeedTest and 
ScatterPlotSpeedTest examples; these .ui files have been compiled with the
tools/rebuildUi.py script).
"""

# Add path to library (just for examples; you do not need this)
import initExample

import _thread
import argparse
import datetime
import math
import numpy as np
import os
import pickle
import pyaudio
import pylab
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import sys
import socket
import threading
import time

from pylab import *
from pyqtgraph.Qt import QtCore, QtGui
from scipy import fftpack, signal
from socket import SHUT_RDWR
from time import localtime, strftime


########## MUSE OSC
# server_ip_g = "localhost"
# server_ip_g = "localhost"
server_ip_g = "192.168.4.1"
server_port_g = 5000
# server_port_g = 10900

# Sampling frequency of the emitting-data device.
# Fs_g = 20_000 # [Hz], the sampling frequency of the data.
Fs_g = 500 # [Hz], the sampling frequency of the data.
# Fs_senddata_g = 10 # [Hz], how frequent we send data.
Fs_senddata_g = 10 # [Hz], how frequent we send data.


uint16Tovoltage_g   = 3.3/65535
max_voltage_g       = 3.3 # [-]. Because the emitting-data device sampled with 16bits.
mean_voltage_g      = max_voltage_g/2 # [-]. The mean voltage of each channel.


########## Raw Data buffered and record the buffer when the arrays are filled.
N_channels_g = 1

buffDurations_g = 60 # sec.

N_records_g = Fs_g*buffDurations_g
i_records_g = 0

EEG_data_g = np.zeros((1, N_records_g, N_channels_g), float)

########## DSP
isShutdownDSPThread = False
isShutdownComThread = False

########## UI
refreshRate_g               = 20 # [Hz]
pg.mkQApp()
win_g = None
idx_downsampled_EEG_data_g  = None

# line plot
N_maxdatapoints_linePlot0_g             = 100_000 # The maximum number of the data points shown in linePlot0.
T_x_ranges_linePlot0_g                  = 5 # [sec.]. The duration of the x axis in linePlot0.
# T_x_ranges_linePlot0_g                  = 0.1 # [sec.]. The duration of the x axis in linePlot0.
i_EEG_data_linePlot0_g                  = 0
N_EEG_data_linePlot0_g                  = int(Fs_g*T_x_ranges_linePlot0_g)
idx_EEG_data_linePlot0_g                = np.arange(0, N_EEG_data_linePlot0_g)
EEG_data_linePlot0_g                    = None
y_min_linePlot0_g                       = 0.0 - 0.05
y_max_linePlot0_g                       = N_channels_g + 0.05

N_downsampled_EEG_data_linePlot0_g      = 0
idx_downsampled_EEG_data_linePlot0_g    = None
time_downsampled_EEG_data_linePlot0_g   = None
y_range_linePlot0_g                     = max_voltage_g # [The same unit as the emitted data]. With the muse monitor, data for each channel is between 0 and 1682 microV and fluctuates around 850 microV.

# line plot filters
# isNotch50Hz = True
isNotch50Hz = False

# image plot
uint16arr_buff_g        = None
i_EEG_data_fft_g        = None
T_EEG_data_fft_g        = 0.2 # [sec.]. The duration of the signal that we will use as a base for calculating FFT.
N_EEG_data_fft_g        = None
N_Desired_freq_step_padding_g = None
idx_EEG_data_fft_g      = None
EEG_data_fft_g          = None
taper_EEG_data_fft_g    = None
is_Padded_g             = None


# The variables for the FFT image.
img_good_freq_positive_lin_g = None
img_N_good_freq_positive_g  = None
img_good_freq_positive_g= None
img_Desired_freq_step_g = 0.5 # [Hz]. If T_EEG_data_fft_g yields lower value of the frequency step, we use T_EEG_data_fft_g otherwise we use Desired_freq_step_g.
img_time_EEG_data_fft_g = None
img_min_freq_positive_g = 1 # [Hz], the minimum frequency shown in the FFT plot.
img_max_freq_positive_g = 200 # [Hz], the max frequency shown in the FFT plot.
img_freq_positive_g     = None
img_N_EEG_data_fft_g    = None
img_EEG_data_fft_g      = None
# img_Fs_fft_g            = int(refreshRate_g/2) # Set the sampling frequency of calculating FFT much lower than the refresh rate will create the smooth feeling.
img_Fs_fft_g            = 20 # [Hz], Set the sampling frequency of calculating FFT much lower than the refresh rate will create the smooth feeling.
img_T_x_ranges_EEG_data_fft_g = 10 # [sec.]
img_N_T_x_ranges_EEG_data_fft_g = img_T_x_ranges_EEG_data_fft_g*img_Fs_fft_g

# The variables for the FFT 3D.
threeD_plot_type_g                      = 0 # 0 for the line plot, 1 for the surface plot, 2 for the scatter plot.
threeD_good_freq_positive_lin_g         = None
threeD_good_freq_positive_lin_scale_g   = 50 # The frequency resolution is reduced to (threeD_img_good_freq_positive_lin_scale_g/100)*len(threeD_img_good_freq_positive_lin_g)
threeD_N_good_freq_positive_lin_g       = None
threeD_time_EEG_data_fft_lin_g          = None
threeD_time_EEG_data_fft_lin_scale_g    = 50 # The frequency resolution is reduced to (threeD_img_time_EEG_data_fft_scale_g/100)*len(threeD_img_time_EEG_data_fft_g)
# threeD_time_EEG_data_fft_lin_scale_g    = 10 # The frequency resolution is reduced to (threeD_img_time_EEG_data_fft_scale_g/100)*len(threeD_img_time_EEG_data_fft_g)
threeD_N_time_EEG_data_fft_lin_g        = None
cmap_g                                  = None

threeD_zscale_g = 7

# Define main window class from template
path_g = os.path.dirname(os.path.abspath(__file__))

# ui_name_g = "mainUI.ui"
ui_name_g = "mainUIV2.ui"

uiFile_g = os.path.join(path_g, ui_name_g)
WindowTemplate_g, TemplateBaseClass_g = pg.Qt.loadUiType(uiFile_g)

tmp = 0 
class MainWindow(TemplateBaseClass_g):  
    def __init__(self, refreshRate_p):
    # Params:
    #   refreshRate_p:  the frequency in Hz that the plots will be updated.
        global N_EEG_data_linePlot0_g, y_min_linePlot0_g, y_max_linePlot0_g
        global img_T_x_ranges_EEG_data_fft_g, img_N_T_x_ranges_EEG_data_fft_g
        global img_min_freq_positive_g, img_max_freq_positive_g, N_channels_g, T_x_ranges_linePlot0_g
        global img_EEG_data_fft_g, img_N_good_freq_positive_g, ui_name_g, img_good_freq_positive_g
        global img_good_freq_positive_lin_g, threeD_zscale_g
        global threeD_img_good_freq_positive_lin_g, threeD_img_time_EEG_data_fft_g
        global threeD_N_time_EEG_data_fft_lin_g
        global cmap_g, threeD_plot_type_g

        TemplateBaseClass_g.__init__(self)
        self.setWindowTitle('pyqtgraph example: Qt Designer')
        
        ##### Create the main window
        self.__ui = WindowTemplate_g()
        self.__ui.setupUi(self)
        
        ##### Set timer to update the plots.
        self.__refreshRatetimer = QtCore.QTimer(self)
        self.__refreshRatetimer.timeout.connect(self.plot)

        ##### Initialize the empty plot
        self.__linePlot0_PlotDataItem = self.__ui.linePlot0.plot(antialias=False, clipToView=True)

        ##### 1D plot
        self.__linePlot0_PlotCurveItems = []

        for i_PlotCurveItem in range(N_channels_g):
            self.__linePlot0_PlotCurveItems.append(pg.PlotCurveItem())

        # The last PlotCurveItem is for the moving vertical line
        self.__linePlot0_PlotCurveItems.append(pg.PlotCurveItem())

        ##### Add PlotCurveItems to the plot
        for i_PlotCurveItem in range(N_channels_g + 1):
            self.__ui.linePlot0.addItem(self.__linePlot0_PlotCurveItems[i_PlotCurveItem])
                
        # self.__ui.linePlot0.enableAutoRange('xy', False)
        # self.__ui.linePlot0.enableAutoRange('y', False)
        # Set the range of X
        self.__ui.linePlot0.setXRange(0, T_x_ranges_linePlot0_g, padding=0)
        # self.__ui.linePlot0.setXRange(0, 1001, padding=0)
        
        # Set the range of Y
        # self.__ui.linePlot0.setYRange(y_min_linePlot0_g, y_max_linePlot0_g, padding=0)

        ##### 2D plot
        self.__img = pg.ImageItem(labels={'bottom':('time [sec.]',''),'left':('frequency [Hz]','')})
        self.__ui.imgPlot0.addItem(self.__img)
        # self.__ui.imgPlot0.setXRange(0, N_T_x_ranges_EEG_data_fft_g, padding=0)        
        # self.__ui.imgPlot0.setYRange(min_freq_positive_g, max_freq_positive_g, padding=0)        

        self.__img.setImage(img_EEG_data_fft_g)

        # Set tick labels of the x axis of the image
        N__ui_imgPlot0_xticks_l  = 5
        __ui_imgPlot0_xticks_l  = np.linspace(0, img_N_T_x_ranges_EEG_data_fft_g, N__ui_imgPlot0_xticks_l)
        __ui_imgPlot0_xlabels_l = np.linspace(0, img_T_x_ranges_EEG_data_fft_g, N__ui_imgPlot0_xticks_l)

        __ui_imgPlot0_xtick = list()
        for tmp_i_l in range(N__ui_imgPlot0_xticks_l):
            __ui_imgPlot0_xtick.append( ( int(__ui_imgPlot0_xticks_l[tmp_i_l]), str(__ui_imgPlot0_xlabels_l[tmp_i_l]) ) )  

        __ui_imgPlot0_xaxis = self.__ui.imgPlot0.getAxis("bottom")
        __ui_imgPlot0_xaxis.setTicks([__ui_imgPlot0_xtick])        
        

        # Set tick labels of the y axis of the image
        N__ui_imgPlot0_yticks_l  = 5
        __ui_imgPlot0_yticks_l  = np.linspace(0, img_N_good_freq_positive_g, N__ui_imgPlot0_yticks_l)
        __ui_imgPlot0_ylabels_l = np.linspace(img_min_freq_positive_g, img_max_freq_positive_g, N__ui_imgPlot0_yticks_l)

        __ui_imgPlot0_ytick = list()
        for tmp_i_l in range(N__ui_imgPlot0_yticks_l):
            __ui_imgPlot0_ytick.append( ( int(__ui_imgPlot0_yticks_l[tmp_i_l]), str(__ui_imgPlot0_ylabels_l[tmp_i_l]) ) )  

        __ui_imgPlot0_yaxis = self.__ui.imgPlot0.getAxis("left")
        __ui_imgPlot0_yaxis.setTicks([__ui_imgPlot0_ytick])        

        self.__img.setLevels([0 - 0.05,0.8 + 0.05]) # 0 for black and 1 for bright.

        ##### 3D plot

        if ui_name_g == "mainUIV2.ui":

            self.__ui.threeDplots.opts['distance'] = 40
            self.__ui.threeDplots.setGeometry(0, 110, 1920, 1080)
            # self.__ui.threeDplots.show()
      
            if threeD_plot_type_g == 1:
            ##### Do 3D plot. The surface plot version.
                gx_l = gl.GLGridItem()
                gx_l.rotate(90, 0, 1, 0)
                gx_l.translate(-10, 0, 9)
                self.__ui.threeDplots.addItem(gx_l)

                gy_l = gl.GLGridItem()
                gy_l.rotate(90, 1, 0, 0)
                gy_l.translate(0, -10, 9)
                self.__ui.threeDplots.addItem(gy_l)

                cmap_l  = plt.get_cmap("jet")
                # minZ_l  = 0
                # maxZ_l  = threeD_zscale_g

                tmp_l       = img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g, :]
                tmp_data_l  = threeD_zscale_g*tmp_l[:, mask_threeD_img_good_freq_positive_lin_g]

                colors = cmap_g(tmp_data_l.transpose()/threeD_zscale_g)

                self.__surf_l = gl.GLSurfacePlotItem(y=threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g], \
                    x=threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], \
                    z=tmp_data_l.transpose(), \
                    shader='shaded', colors=colors.reshape(len(mask_threeD_N_time_EEG_data_fft_lin_g)*len(mask_threeD_img_good_freq_positive_lin_g),4))

                self.__ui.threeDplots.addItem(self.__surf_l)

            elif threeD_plot_type_g == 0:
            ##### Do 3D plot. The line plot version.
                gx_l = gl.GLGridItem()
                gx_l.rotate(90, 0, 1, 0)
                gx_l.translate(-10, 0, 9)
                self.__ui.threeDplots.addItem(gx_l)

                gy_l = gl.GLGridItem()
                gy_l.rotate(90, 1, 0, 0)
                gy_l.translate(0, -10, 9)
                self.__ui.threeDplots.addItem(gy_l)

                # gz_l = gl.GLGridItem()
                # gz_l.translate(0, 0, -10)
                # self.__ui.threeDplots.addItem(gz_l)

                self.__traces = dict()

                
                # Plot each trances.
                for i_time_l in range(threeD_N_time_EEG_data_fft_lin_g):

                    yi      = np.array([threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l]]] * threeD_N_good_freq_positive_lin_g)

                    pts_l   = np.vstack([threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], yi, threeD_zscale_g*img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l], mask_threeD_img_good_freq_positive_lin_g]]).transpose()

                    self.__traces[i_time_l] = gl.GLLinePlotItem(pos=pts_l, color=pg.glColor( (i_time_l, threeD_N_time_EEG_data_fft_lin_g*1.3) ), antialias=True)

                    self.__ui.threeDplots.addItem(self.__traces[i_time_l])
            elif threeD_plot_type_g == 2:
            ##### Do 3D plot. The scatter plot version.
                gx_l = gl.GLGridItem()
                gx_l.rotate(90, 0, 1, 0)
                gx_l.translate(-10, 0, 9)
                self.__ui.threeDplots.addItem(gx_l)

                gy_l = gl.GLGridItem()
                gy_l.rotate(90, 1, 0, 0)
                gy_l.translate(0, -10, 9)
                self.__ui.threeDplots.addItem(gy_l)

                self.__traces = dict()

                # plt.setGLOptions('opaque')

                # Plot each trances.
                for i_time_l in range(threeD_N_time_EEG_data_fft_lin_g):

                    yi      = np.array([threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l]]] * threeD_N_good_freq_positive_lin_g)

                    pts_l   = np.vstack([threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], yi, threeD_zscale_g*img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l], mask_threeD_img_good_freq_positive_lin_g]]).transpose()

                    self.__traces[i_time_l] = gl.GLScatterPlotItem(pos=pts_l, size=1)

                    self.__ui.threeDplots.addItem(self.__traces[i_time_l])            

        self.__refreshRatetimer.start(1000/refreshRate_p) # in milliseconds
        self.show()
        
    def plot(self):
    # It is guaranteed that this method will be called every 1000/refreshRate_g millisecs.

        global EEG_data_linePlot0_g, idx_downsampled_EEG_data_linePlot0_g, N_downsampled_EEG_data_linePlot0_g
        global running_downsampled_EEG_data_linePlot0_g, time_downsampled_EEG_data_linePlot0_g
        global Fs_g, i_EEG_data_linePlot0_g, idx_EEG_data_linePlot0_g
        global img_EEG_data_fft_g, N_channels_g, T_x_ranges_linePlot0_g, y_min_linePlot0_g, y_max_linePlot0_g
        global img_N_T_x_ranges_EEG_data_fft_g, threeD_img_time_EEG_data_fft_g, img_N_good_freq_positive_g
        global threeD_img_good_freq_positive_lin_g, threeD_zscale_g
        global cmap_g

        ##### Do 1D plot.
        # if isNotch50Hz:

        #     # running_i_EEG_data_linePlot0_g  = i_EEG_data_linePlot0_g + idx_EEG_data_linePlot0_g
        #     # modulo_i_EEG_data_linePlot0_g   = np.take(a=idx_EEG_data_linePlot0_g, indices=running_i_EEG_data_linePlot0_g, mode='wrap')

        #     # tmp_TP9_l   = np.take(a=EEG_data_linePlot0_g[0, :, 0], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_AF7_l   = np.take(a=EEG_data_linePlot0_g[0, :, 1], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_AF8_l   = np.take(a=EEG_data_linePlot0_g[0, :, 2], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_TP10_l  = np.take(a=EEG_data_linePlot0_g[0, :, 3], indices=running_i_EEG_data_linePlot0_g, mode='wrap')

        #     # # tmp_TP9_l   = EEG_data_linePlot0_g[0, modulo_i_EEG_data_linePlot0_g, 0]
        #     # # tmp_AF7_l   = EEG_data_linePlot0_g[0, modulo_i_EEG_data_linePlot0_g, 1]
        #     # # tmp_AF8_l   = EEG_data_linePlot0_g[0, modulo_i_EEG_data_linePlot0_g, 2]
        #     # # tmp_TP10_l  = EEG_data_linePlot0_g[0, modulo_i_EEG_data_linePlot0_g, 3]

        #     # tmp_TP9_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=tmp_TP9_l, isShowLog_p=False)
        #     # tmp_AF7_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=tmp_AF7_l, isShowLog_p=False)
        #     # tmp_AF8_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=tmp_AF8_l, isShowLog_p=False)
        #     # tmp_TP10_l  = AV_remove_line_noise(fs_p=Fs_g, signal_p=tmp_TP10_l, isShowLog_p=False)

        #     # tmp_TP9_l[modulo_i_EEG_data_linePlot0_g]    = tmp_TP9_l
        #     # tmp_AF7_l[modulo_i_EEG_data_linePlot0_g]    = tmp_AF7_l
        #     # tmp_AF8_l[modulo_i_EEG_data_linePlot0_g]    = tmp_AF8_l
        #     # tmp_TP10_l[modulo_i_EEG_data_linePlot0_g]   = tmp_TP10_l

        #     # running_i_EEG_data_linePlot0_g  = i_EEG_data_linePlot0_g + idx_EEG_data_linePlot0_g
        #     # modulo_i_EEG_data_linePlot0_g   = np.take(a=idx_EEG_data_linePlot0_g, indices=running_i_EEG_data_linePlot0_g, mode='wrap')

        #     # tmp_TP9_l   = np.take(a=EEG_data_linePlot0_g[0, :, 0], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_AF7_l   = np.take(a=EEG_data_linePlot0_g[0, :, 1], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_AF8_l   = np.take(a=EEG_data_linePlot0_g[0, :, 2], indices=running_i_EEG_data_linePlot0_g, mode='wrap')
        #     # tmp_TP10_l  = np.take(a=EEG_data_linePlot0_g[0, :, 3], indices=running_i_EEG_data_linePlot0_g, mode='wrap')


        #     tmp_TP9_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=EEG_data_linePlot0_g[0, :, 0], isShowLog_p=False)
        #     tmp_AF7_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=EEG_data_linePlot0_g[0, :, 1], isShowLog_p=False)
        #     tmp_AF8_l   = AV_remove_line_noise(fs_p=Fs_g, signal_p=EEG_data_linePlot0_g[0, :, 2], isShowLog_p=False)
        #     tmp_TP10_l  = AV_remove_line_noise(fs_p=Fs_g, signal_p=EEG_data_linePlot0_g[0, :, 3], isShowLog_p=False)

        # else:
        #     tmp_TP9_l   = EEG_data_linePlot0_g[0, :, 0]
        #     tmp_AF7_l   = EEG_data_linePlot0_g[0, :, 1]
        #     tmp_AF8_l   = EEG_data_linePlot0_g[0, :, 2]
        #     tmp_TP10_l  = EEG_data_linePlot0_g[0, :, 3]


        if isNotch50Hz:
            for i_channels_g in range(N_channels_g):
                filtered_l = EEG_data_linePlot0_g[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g]

                filtered_l = AV_remove_line_noise(fs_p=Fs_g, signal_p=filtered_l, isShowLog_p=False)

                self.__linePlot0_PlotCurveItems[i_channels_g].setData(x=time_downsampled_EEG_data_linePlot0_g, y=filtered_l)            
        else:
            for i_channels_g in range(N_channels_g):
                self.__linePlot0_PlotCurveItems[i_channels_g].setData(x=time_downsampled_EEG_data_linePlot0_g, y=EEG_data_linePlot0_g[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g])

        ##### Plot a moving vertical line
        # self.__linePlot0_PlotCurveItems[-1].setData(x=[(i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g, (i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g], y=[y_min_linePlot0_g, y_max_linePlot0_g])

        y_min_linePlot0_g = np.min(EEG_data_linePlot0_g[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g])
        y_min_linePlot0_g = y_min_linePlot0_g - 0.1*y_min_linePlot0_g
        y_max_linePlot0_g = np.max(EEG_data_linePlot0_g[0, idx_downsampled_EEG_data_linePlot0_g, i_channels_g])
        y_max_linePlot0_g = y_max_linePlot0_g + 0.1*y_max_linePlot0_g
        self.__linePlot0_PlotCurveItems[-1].setData(x=[(i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g, (i_EEG_data_linePlot0_g*T_x_ranges_linePlot0_g)/N_EEG_data_linePlot0_g], y=[y_min_linePlot0_g, y_max_linePlot0_g])
        

        ##### Do 2D plot.
        self.__img.setImage(img_EEG_data_fft_g, autoLevels=False)

        if threeD_plot_type_g == 1:
        ##### Do 3D plot. The surface plot version.
            tmp_l = img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g, :]
            tmp_data_l = threeD_zscale_g*tmp_l[:, mask_threeD_img_good_freq_positive_lin_g]

            colors = cmap_g(tmp_data_l.transpose()/threeD_zscale_g)

            self.__surf_l.setData(y=threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g], \
                x=threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], \
                z=tmp_data_l.transpose(), \
                colors=colors.reshape(len(mask_threeD_N_time_EEG_data_fft_lin_g)*len(mask_threeD_img_good_freq_positive_lin_g),4))
        
        elif threeD_plot_type_g == 0:
        ##### Do 3D plot. The line plot version.
            for i_time_l in range(threeD_N_time_EEG_data_fft_lin_g):

                yi      = np.array([threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l]]] * threeD_N_good_freq_positive_lin_g)

                pts_l   = np.vstack([threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], yi, threeD_zscale_g*img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l], mask_threeD_img_good_freq_positive_lin_g]]).transpose()

                self.__traces[i_time_l].setData(pos=pts_l, color=pg.glColor( (i_time_l, threeD_N_time_EEG_data_fft_lin_g*1.3) ), mode="line_strip")

        elif threeD_plot_type_g == 2:
        ##### Do 3D plot. The scatter plot version.
            for i_time_l in range(threeD_N_time_EEG_data_fft_lin_g):

                yi      = np.array([threeD_time_EEG_data_fft_lin_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l]]] * threeD_N_good_freq_positive_lin_g)

                pts_l   = np.vstack([threeD_good_freq_positive_lin_g[mask_threeD_img_good_freq_positive_lin_g], yi, threeD_zscale_g*img_EEG_data_fft_g[mask_threeD_N_time_EEG_data_fft_lin_g[i_time_l], mask_threeD_img_good_freq_positive_lin_g]]).transpose()

                self.__traces[i_time_l].setData(pos=pts_l, size=1)


    # Clean up before exiting.
    def closeEvent(self, event):
        global isShutdownDSPThread, isShutdownComThread

        print("Window is closing.")

        isShutdownComThread = True
        isShutdownDSPThread = True

        event.accept() # let the window close


########## Do digital signal processing on the shown data.
def doDSP():
    global isShutdownDSPThread
    global Fs_g, idx_EEG_data_fft_g, i_EEG_data_fft_g
    global img_Fs_fft_g, taper_EEG_data_fft_g, N_T_x_ranges_EEG_data_fft_g, EEG_data_fft_g, img_EEG_data_fft_g, img_min_freq_positive_g, img_max_freq_positive_g
    global uint16arr_buff_g, is_Padded_g, N_EEG_data_fft_g

    last_i_EEG_data_fft_l = -1
    i_img_EEG_data_fft_l = 0

    while not isShutdownDSPThread:
        
        time.sleep(1.0/img_Fs_fft_g)

        if True:
        # if not (last_i_EEG_data_fft_l == i_EEG_data_fft_g):
        # If there is no new data points, we do not do the calculation.

            last_i_EEG_data_fft_l = i_EEG_data_fft_g

            running_i_EEG_data_fft_l  = i_EEG_data_fft_g + idx_EEG_data_fft_g
            modulo_i_EEG_data_fft_g   = np.take(a=idx_EEG_data_fft_g, indices=running_i_EEG_data_fft_l, mode='wrap')

            if is_Padded_g:

                N_begin_padd_l  = int(np.floor((img_N_EEG_data_fft_g - N_EEG_data_fft_g)/2.0))
                N_end_padd_l    = int(np.ceil((img_N_EEG_data_fft_g - N_EEG_data_fft_g)/2.0))
                
                # [3, 2, 1, 2, 3, 4, 5, 4, 3, 2]
                ch1_l = np.pad(EEG_data_fft_g[0, modulo_i_EEG_data_fft_g, 0], (N_begin_padd_l, N_end_padd_l), 'reflect')


                # ch1_l = np.pad(EEG_data_fft_g[0, modulo_i_EEG_data_fft_g, 0], (N_begin_padd_l, N_end_padd_l), 'constant', constant_values=(0, 0))
                
            else:
                ch1_l = EEG_data_fft_g[0, modulo_i_EEG_data_fft_g, 0]

            freq_positive_l, _, _, fft_pw_ch1_l, _, _, _    = AV_ShortFFT(fs_p=Fs_g, signal_p=ch1_l - np.mean(ch1_l), typeTaper_p="hann", taper_p=taper_EEG_data_fft_g)

            mask_good_freq_positive_l   = (img_min_freq_positive_g < freq_positive_l) & (freq_positive_l < img_max_freq_positive_g)
            good_freq_positive_l        = freq_positive_l[mask_good_freq_positive_l]
            good_fft_pw_ch1_l           = fft_pw_ch1_l[mask_good_freq_positive_l]

            with np.errstate(divide='ignore',invalid='ignore'):
                avg_pw_l = good_fft_pw_ch1_l/np.nanmax(good_fft_pw_ch1_l) 

            # Store FFT data
            if i_img_EEG_data_fft_l < img_N_T_x_ranges_EEG_data_fft_g:

                img_EEG_data_fft_g[i_img_EEG_data_fft_l, :] = avg_pw_l

                i_img_EEG_data_fft_l = i_img_EEG_data_fft_l + 1
            else:
                i_img_EEG_data_fft_l = 0

                img_EEG_data_fft_g[i_img_EEG_data_fft_l, :] = avg_pw_l

    print("DSP thread is shutting down.")

########## Else
def normalizeEEG_data(data_p):
    """
    This function will normalize the EEG data by max_voltage_g to the value between -0.5 and 0.5.
    """
    global max_voltage_g

    return data_p/max_voltage_g - 0.5

def magnifyEEG_data(data_p):
    """
    Params:
        data_p: data after normalizeEEG_data
    """

    global y_range_linePlot0_g, max_voltage_g

    return data_p*max_voltage_g/y_range_linePlot0_g

def stackEEG_data(data_p, channel_p):
    """
    Assume that data is centered at 0.0.
    """
    
    if channel_p == "CH1":
        return data_p + 0.5

def chopChunk(chuck_p, idx_storage_p, N_storage_p):
    N_chuck_p = len(chuck_p)

    if idx_storage_p + N_chuck_p <= N_storage_p:
        idx_end_l = idx_storage_p + N_chuck_p

        valid_block_l   = chuck_p
        next_block_l    = None
    else:
        idx_end_l = N_storage_p

        valid_block_l   = chuck_p[0:(N_storage_p - idx_storage_p)]
        next_block_l    = chuck_p[(N_storage_p - idx_storage_p):]

    return idx_end_l, valid_block_l, next_block_l

def combineHighByteLowByte(bytesarr_buff_p):
    global N_bytesarr_buff_g

    uint16arr_buff_l = np.zeros((int(N_bytesarr_buff_g/2),), dtype=np.uint16)

    i_l = 0
    j_l = 0
    while i_l < N_bytesarr_buff_g:
        
        uint16arr_buff_l[j_l] = (uint16((bytesarr_buff_p[i_l]  << 8 | bytesarr_buff_p[i_l + 1])))
        j_l = j_l + 1
        i_l = i_l  + 2

    return uint16arr_buff_l

def communicateWithServer():
    global server_ip_g, server_port_g, N_bytesarr_buff_g, bytesarr_buff_g
    global EEG_data_g, i_records_g, N_EEG_data_fft_g, i_EEG_data_fft_g
    global i_EEG_data_linePlot0_g, EEG_data_linePlot0_g, N_EEG_data_linePlot0_g, EEG_data_fft_g
    global isShutdownComThread, uint16arr_buff_g


    # Create a TCP/IP socket
    sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address_l = (server_ip_g, server_port_g)
    print("connecting to " + str(server_address_l))
    sock_l.connect(server_address_l)

    try:
        next_block_l = None

        while not isShutdownComThread:
            tic_l = time.time()*1000
            
            if next_block_l is None:
                idx_bytesarr_buff_l = 0
            else:
                idx_bytesarr_buff_l = len(next_block_l)
                bytesarr_buff_g[0:len(next_block_l)] = next_block_l

            while True:
                block_l = sock_l.recv(1000)

                idx_end_l, valid_block_l, next_block_l = \
                chopChunk(chuck_p=block_l, idx_storage_p=idx_bytesarr_buff_l, N_storage_p=N_bytesarr_buff_g)                

                bytesarr_buff_g[idx_bytesarr_buff_l:idx_end_l] = valid_block_l

                idx_bytesarr_buff_l = idx_end_l

                if idx_bytesarr_buff_l == N_bytesarr_buff_g:
                    idx_bytesarr_buff_l = 0
                    break

            # print(len(bytesarr_buff_g))

            # Convert from an array of bytes to an array of 2-byte unsigned interger.
            uint16arr_buff_l = combineHighByteLowByte(bytesarr_buff_g)
            N_uint16arr_buff_l = int(N_bytesarr_buff_g/2)

            ##### Fill complete data
            idx_end_EEG_data_l, valid_block_EEG_data_l, next_block_EEG_data_l = \
            chopChunk(chuck_p=uint16arr_buff_l, idx_storage_p=i_records_g, N_storage_p=N_records_g)

            EEG_data_g[0, i_records_g:idx_end_EEG_data_l, 0]    = uint16Tovoltage_g*valid_block_EEG_data_l

            if next_block_EEG_data_l is not None:
                i_records_g = len(next_block_EEG_data_l)
                EEG_data_g[0, 0:len(next_block_EEG_data_l), 0]  = uint16Tovoltage_g*next_block_EEG_data_l
            else:
                i_records_g = idx_end_EEG_data_l 

            if i_records_g == N_records_g:
                i_records_g = 0


            ##### Fill data for display
            idx_end_EEG_data_linePlot0_l, valid_block_EEG_data_linePlot0_l, next_block_EEG_data_linePlot0_l = \
            chopChunk(chuck_p=uint16arr_buff_l, idx_storage_p=i_EEG_data_linePlot0_g, N_storage_p=N_EEG_data_linePlot0_g)

            EEG_data_linePlot0_g[0, i_EEG_data_linePlot0_g:idx_end_EEG_data_linePlot0_l, 0] = stackEEG_data(magnifyEEG_data(normalizeEEG_data(uint16Tovoltage_g*valid_block_EEG_data_linePlot0_l)), "CH1")

            if next_block_EEG_data_linePlot0_l is not None:
                i_EEG_data_linePlot0_g = len(next_block_EEG_data_linePlot0_l)
                EEG_data_linePlot0_g[0, 0:len(next_block_EEG_data_linePlot0_l), 0]          = stackEEG_data(magnifyEEG_data(normalizeEEG_data(uint16Tovoltage_g*next_block_EEG_data_linePlot0_l)), "CH1")
            else:
                i_EEG_data_linePlot0_g = idx_end_EEG_data_linePlot0_l 

            if i_EEG_data_linePlot0_g == N_EEG_data_linePlot0_g:
                i_EEG_data_linePlot0_g = 0

            ##### Fill data for calculating FFT
            idx_end_EEG_data_fft_l, valid_block_EEG_data_fft_l, next_block_EEG_data_fft_l = \
            chopChunk(chuck_p=uint16arr_buff_l, idx_storage_p=i_EEG_data_fft_g, N_storage_p=N_EEG_data_fft_g)

            EEG_data_fft_g[0, i_EEG_data_fft_g:idx_end_EEG_data_fft_l, 0]   = uint16Tovoltage_g*valid_block_EEG_data_fft_l

            if next_block_EEG_data_fft_l is not None:
                i_EEG_data_fft_g = len(next_block_EEG_data_fft_l)
                EEG_data_fft_g[0, 0:len(next_block_EEG_data_fft_l), 0]      = uint16Tovoltage_g*next_block_EEG_data_fft_l
            else:
                i_EEG_data_fft_g = idx_end_EEG_data_fft_l 

            if i_EEG_data_fft_g == N_EEG_data_fft_g:
                i_EEG_data_fft_g = 0

            # print("Store " + str(len(bytesarr_buff_g)) + " bytes for " + str(time.time()*1000 - tic_l - 1000/Fs_senddata_g) + " ms.")

    finally:
        print("closing socket")
        sock_l.shutdown(SHUT_RDWR)
        sock_l.close()          


def init():
    global Fs_g, N_channels_g
    global T_x_ranges_linePlot0_g, N_maxdatapoints_linePlot0_g
    global idx_downsampled_EEG_data_g, idx_downsampled_EEG_data_linePlot0_g
    global N_downsampled_EEG_data_linePlot0_g, time_downsampled_EEG_data_linePlot0_g
    global EEG_data_linePlot0_g, N_EEG_data_linePlot0_g, N_EEG_data_fft_g, i_EEG_data_fft_g
    global taper_EEG_data_fft_g, img_EEG_data_fft_g, img_freq_positive_g
    global EEG_data_fft_g, img_N_T_x_ranges_EEG_data_fft_g, idx_EEG_data_fft_g
    global img_T_x_ranges_EEG_data_fft_g
    global bytesarr_buff_g, N_bytesarr_buff_g, Fs_senddata_g
    global img_min_freq_positive_g, img_max_freq_positive_g
    global img_N_good_freq_positive_g, T_EEG_data_fft_g, img_Desired_freq_step_g, N_Desired_freq_step_padding_g
    global img_time_EEG_data_fft_g, img_N_EEG_data_fft_g
    global is_Padded_g, img_good_freq_positive_g, img_good_freq_positive_lin_g
    global threeD_good_freq_positive_lin_g, threeD_time_EEG_data_fft_lin_g
    global threeD_N_good_freq_positive_lin_g, threeD_good_freq_positive_lin_scale_g
    global mask_threeD_img_good_freq_positive_lin_g, threeD_time_EEG_data_fft_lin_scale_g
    global threeD_N_time_EEG_data_fft_lin_g, mask_threeD_N_time_EEG_data_fft_lin_g
    global cmap_g


    ##### Initialize for TCP/IP communication wtih the emitting-data device.
    N_bytesarr_buff_g = int((2*Fs_g)/Fs_senddata_g)
    bytesarr_buff_g = bytearray(N_bytesarr_buff_g)

    print("One chunk sent by the emitting-device data: " + str(N_bytesarr_buff_g) + " bytes")
    print("Meaningfull frequency in one chunk: " + str(3*Fs_senddata_g) + " Hz")

    ##### Set the number of data points in linePlot0.
    if int(Fs_g*T_x_ranges_linePlot0_g) < N_maxdatapoints_linePlot0_g:
    # We use all data points when the plot is capable of drawing. Therefore, we have N_maxdatapoints_linePlot0_g during T_x_ranges_linePlot0_g sec.
        N_maxdatapoints_linePlot0_g = int(Fs_g*T_x_ranges_linePlot0_g)

    tmp_dt_l = T_x_ranges_linePlot0_g/N_maxdatapoints_linePlot0_g # [sec.]. What is the time step in the downsampled signale?
    N_tmp_dt_l = np.ceil(tmp_dt_l*Fs_g) # The number of samples in that downsampled time.

    idx_downsampled_EEG_data_linePlot0_g    = np.arange(0, int(Fs_g*T_x_ranges_linePlot0_g), N_tmp_dt_l, dtype=np.uint64) # indices of the downsampled sample.
    N_downsampled_EEG_data_linePlot0_g      = len(idx_downsampled_EEG_data_linePlot0_g)
    time_downsampled_EEG_data_linePlot0_g   = np.linspace(0, T_x_ranges_linePlot0_g, N_downsampled_EEG_data_linePlot0_g)

    ##### Create a non-downsampled EEG data.
    EEG_data_linePlot0_g = np.zeros((1, int(Fs_g*T_x_ranges_linePlot0_g), N_channels_g), float)

    # Normalize the values sent by the server to 0.0 and 1.0 and stack each plots on top of each others when there are more than one types.
    for i_channels_l in range(N_channels_g):
        EEG_data_linePlot0_g[0, :, i_channels_l] = stackEEG_data(magnifyEEG_data(normalizeEEG_data(uint16Tovoltage_g*EEG_data_linePlot0_g[0, :, i_channels_l])), "CH" + str(i_channels_l))

    ##### Initialize fft variables
    print("Meaningful at-least frequency in one duration for calculation FFT: " + str(3/T_EEG_data_fft_g) + " Hz")

    i_EEG_data_fft_g = 0

    N_EEG_data_fft_g = int(Fs_g*T_EEG_data_fft_g)

    idx_EEG_data_fft_g  = np.arange(0, N_EEG_data_fft_g)
    EEG_data_fft_g      = np.zeros((1, N_EEG_data_fft_g, N_channels_g), float)

    if img_Desired_freq_step_g < (1/T_EEG_data_fft_g):
        is_Padded_g = True
        img_N_EEG_data_fft_g = AV_next_power_of_2(int(Fs_g*(1/img_Desired_freq_step_g)))

        img_Desired_freq_step_g = Fs_g/img_N_EEG_data_fft_g
        print("The frequency resolution in FFT image is changed from " + str(1/T_EEG_data_fft_g) + " Hz to " + str(img_Desired_freq_step_g) + " Hz (follow the power of 2 FFT speed improvement)")        
    else:
        is_Padded_g = False
        img_N_EEG_data_fft_g = int(Fs_g*T_EEG_data_fft_g)

        print("The frequency resolution in FFT image is " + str(1/T_EEG_data_fft_g) + " Hz")

    _, taper_EEG_data_fft_g = AV_taper_signal(signal_p=np.zeros(img_N_EEG_data_fft_g), typeTaper_p="hann")

    img_freq_positive_g     = AV_fft_getfreq(fs_p=Fs_g, signal_p=np.zeros(img_N_EEG_data_fft_g))

    # Set up the image part of FFT.
    img_time_EEG_data_fft_g     = np.linspace(0, img_T_x_ranges_EEG_data_fft_g, img_N_T_x_ranges_EEG_data_fft_g)
    img_good_freq_positive_g    = (img_min_freq_positive_g < img_freq_positive_g) & (img_freq_positive_g < img_max_freq_positive_g)
    img_good_freq_positive_lin_g= img_freq_positive_g[img_good_freq_positive_g]
    img_N_good_freq_positive_g  = len(img_good_freq_positive_lin_g)
    img_EEG_data_fft_g          = np.zeros((img_N_T_x_ranges_EEG_data_fft_g, img_N_good_freq_positive_g), float)

    ##### Set up for the 3D of FFT.
    threeD_good_freq_positive_lin_g = 20*img_good_freq_positive_lin_g/np.max(img_good_freq_positive_lin_g) - 10 # 0 Hz is mapped to -10 and np.max(img_good_freq_positive_lin_g) mapped to 10.
    threeD_time_EEG_data_fft_lin_g  = 20*img_time_EEG_data_fft_g/np.max(img_time_EEG_data_fft_g) - 10 # 0 sec. is mapped to -10 and np.max(img_time_EEG_data_fft_g) mapped to 10.

    threeD_N_good_freq_positive_lin_g               = 100/threeD_good_freq_positive_lin_scale_g
    mask_threeD_img_good_freq_positive_lin_g        = np.arange(0, img_N_good_freq_positive_g, int(threeD_N_good_freq_positive_lin_g))
    mask_threeD_img_good_freq_positive_lin_g[-1]    = img_N_good_freq_positive_g - 1
    threeD_N_good_freq_positive_lin_g               = len(mask_threeD_img_good_freq_positive_lin_g)

    print("The frequency resolution in 3D plot is reduced from " + str(img_N_good_freq_positive_g) + " to " + str(threeD_N_good_freq_positive_lin_g))

    threeD_N_time_EEG_data_fft_lin_g                = 100/threeD_time_EEG_data_fft_lin_scale_g
    mask_threeD_N_time_EEG_data_fft_lin_g           = np.arange(0, img_N_T_x_ranges_EEG_data_fft_g, int(threeD_N_time_EEG_data_fft_lin_g))
    mask_threeD_N_time_EEG_data_fft_lin_g[-1]       = img_N_T_x_ranges_EEG_data_fft_g - 1
    threeD_N_time_EEG_data_fft_lin_g                = len(mask_threeD_N_time_EEG_data_fft_lin_g)

    print("The time resolution in 3D plot is reduced from " + str(img_N_T_x_ranges_EEG_data_fft_g) + " to " + str(threeD_N_time_EEG_data_fft_lin_g))

    cmap_g  = plt.get_cmap("rainbow")

#################### Helper ####################
def AV_next_power_of_2(x_p):
    return int(1 if (x_p == 0) else 2**math.ceil(math.log2(x_p)))

def AV_remove_line_noise(fs_p, signal_p, isShowLog_p=True):
# Checked
    dt_l = 1/fs_p
    fnyq_l = fs_p/2.0

    # initialize filtered signal
    signal_l = signal_p

    frex2notch_l = [50]

    for fline_l in frex2notch_l:
        if (fline_l <= fnyq_l):
            if isShowLog_p:
                print("AV_remove_line_noise: remove line noise at %f Hz" % (fline_l))
            frange_l = [fline_l - 0.5, fline_l + 0.5]
            order_l = np.round(150*fs_p/frange_l[0])
            # order_l = np.round(500*fs_p/frange_l[0])

            if ((int(order_l) % 2) == 0):
                order_l = order_l + 1
            else:
                pass
            
            if isShowLog_p:
                print("AV_remove_line_noise: order = %d" % (order_l))

            filtkern_l = signal.firwin(numtaps=int(order_l), cutoff=frange_l, nyq=fnyq_l)            

            signal_l = AV_reflected_zerophaseshift_filter(signal_p=signal_l, filtkern_b_p=filtkern_l)

    return signal_l

def AV_reflected_zerophaseshift_filter(signal_p, filtkern_b_p=None, filtkern_a_p=None, sos_p=None):
# return fsignal_l

    if (sos_p is None):
        if (filtkern_a_p is None):
            filtkern_a_p = 1

            order_l = len(filtkern_b_p)

            relected_signal_l = np.append(np.append(np.flip(signal_p[0:order_l]), signal_p), (np.flip(signal_p))[0:order_l])

            # 1) Forward 2) Reverse 3) Flip forward
            relected_signal_l = np.flip(signal.lfilter(filtkern_b_p, filtkern_a_p, np.flip(signal.lfilter(filtkern_b_p, filtkern_a_p, relected_signal_l))))

            end_l = len(relected_signal_l)
            fsignal_l = relected_signal_l[order_l:(end_l - order_l)]
        else:
            fsignal_l = signal.filtfilt(filtkern_b_p, filtkern_a_p, signal_p)
    else:
        fsignal_l = signal.sosfiltfilt(sos_p, signal_p)
        # fsignal_l = signal.sosfilt(sos_p, signal_p)

    return fsignal_l    

def AV_fft(fs_p, signal_p):
    """
    The function returns only the positive-frequency term.
    See https://docs.scipy.org/doc/scipy/reference/generated/scipy.fftpack.fft.html
    """

    try:
        print("AV_fft: Wrong signal_p dimension %d" % (int(np.shape(signal_p)[1])))
    except IndexError:    
        N_signal_l = len(signal_p)
        fft_l = fftpack.fft(signal_p)
        freq_l = np.fft.fftfreq(N_signal_l, d = (1/fs_p))

        if ((N_signal_l % 2) == 0):
            freq_positive_l = freq_l[0:((N_signal_l//2))]
            fft_l = fft_l[0:((N_signal_l//2))]
        else:
            freq_positive_l = freq_l[0:(((N_signal_l - 1)//2) + 1)]
            fft_l = fft_l[0:(((N_signal_l - 1)//2) + 1)]


        fft_amp_l = 2.0*np.abs(fft_l)/N_signal_l
        fft_pw_l = fft_amp_l**2
        fft_gain_l = np.abs(fft_l)

        # fft_amp_l has the same unit as signal_p. [fft_amp_l] = [signal_p]
        # [fft_pw_l] = [fft_amp_l]*[fft_amp_l], i.e. if the unit of the signal is microvolt, the unit of the power (fft_pw_l) is microvolt^2
        return freq_positive_l, fft_l, fft_amp_l, fft_pw_l, fft_gain_l

def AV_fft_getfreq(fs_p, signal_p):
# return freq_positive_l

    try:
        print("AV_fft_getfreq: Wrong signal_p dimension %d" % (int(np.shape(signal_p)[1])))
    except IndexError:    
        N_signal_l = len(signal_p)
        freq_l = np.fft.fftfreq(N_signal_l, d = (1/fs_p))

        if ((N_signal_l % 2) == 0):
            freq_positive_l = freq_l[0:((N_signal_l//2))]
        else:
            freq_positive_l = freq_l[0:(((N_signal_l - 1)//2) + 1)]

        return freq_positive_l

def AV_taper_signal(signal_p, typeTaper_p="hann", taper_p=None):
# This function will taper the signal mainly because we want to reduce the edge artifacts before applying FFT.

    if taper_p is None:
        pnts_l = len(signal_p)
        if (typeTaper_p == "hann"):
            # With Hann taper
            hannw_l     = 0.5 - 0.5*np.cos(2*np.pi*np.linspace(0.0, 1.0, pnts_l))
            signal_l    = np.multiply(signal_p, hannw_l)
            taper_l     = hannw_l


        if (typeTaper_p == "hamming"):
            # With Hamming taper
            hammingw_l  = .54 - .46*np.cos(2*np.pi*np.linspace(0.0, 1.0, pnts_l))
            signal_l    = np.multiply(signal_p, hammingw_l)
            taper_l     = hammingw_l

        if (typeTaper_p == "gaussian"):
            # With Gaussian taper
            gaussw_l    = np.exp(-np.square(time_l))
            signal_l    = np.multiply(signal_p, gaussw_l)
            taper_l     = gaussw_l
    else:
        signal_l    = np.multiply(signal_p, taper_p)
        taper_l     = taper_p

    return signal_l, taper_l

def AV_ShortFFT(fs_p, signal_p, typeTaper_p="hann", taper_p=None):
    tapered_signal_l, taper_l = AV_taper_signal(signal_p=signal_p, typeTaper_p=typeTaper_p, taper_p=taper_p)
    freq_positive_p, fft_p, fft_amp_p, fft_pw_p, fft_gain_p = AV_fft(fs_p=fs_p, signal_p=tapered_signal_l)

    return freq_positive_p, fft_p, fft_amp_p, fft_pw_p, fft_gain_p, tapered_signal_l, taper_l

if __name__ == '__main__':
    ##### Initialize variables
    init()

    ##### TCP thread
    # communicateWithServer()
    tcp_thread_l = threading.Thread(target=communicateWithServer)
    tcp_thread_l.start()

    ##### Start digital signal processing thread
    # doDSP()
    dsp_thread_l = threading.Thread(target=doDSP)
    dsp_thread_l.start()

    # ##### Start Qt event loop unless running in interactive mode or using pyside.     
    win_g = MainWindow(refreshRate_g)
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        # you MUST put this at the end of the entrire program.
        QtGui.QApplication.instance().exec_()


