import numpy as np
import os
import pickle
import socket
import sys
import time

ROOTPATH_g = (os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")).split("/Data")[0]    

sys.path.append(ROOTPATH_g + "/Data/Work/UtilSrcCode/python-DeviceInterface")
from AV_DeviceInterface import EEGClientThread

PACKET_HEADER_COMMAND=0
PACKET_HEADER_GROUP1=1
PACKET_HEADER_GROUP2=2

CMD_START_STREAM=0
CMD_STOP_STREAM=1
CMD_SET_SAMPLING_FREQUENCY=2
CMD_SET_SEND_DATA_FREQUENCY=3

def stream_start(sock_p):
    bytesarr_buff_l = bytearray(6)   

    i_l = 0     
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 2; i_l = i_l + 1;

    bytesarr_buff_l[i_l] = PACKET_HEADER_COMMAND; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = CMD_START_STREAM; i_l = i_l + 1;

    sock_l.sendall(bytesarr_buff_l)

def stream_stop(sock_p):
    bytesarr_buff_l = bytearray(6)        

    i_l = 0     
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 2; i_l = i_l + 1;

    bytesarr_buff_l[i_l] = PACKET_HEADER_COMMAND; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = CMD_STOP_STREAM; i_l = i_l + 1;    

    sock_l.sendall(bytesarr_buff_l)

def stream_set_sampling_freq(sock_p, fs_p):
    fs_uint32_l = np.uint32(fs_p)

    bytesarr_buff_l = bytearray(10)        

    i_l = 0
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 6; i_l = i_l + 1;    

    bytesarr_buff_l[i_l] = PACKET_HEADER_COMMAND; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = CMD_SET_SAMPLING_FREQUENCY; i_l = i_l + 1;    

    bytesarr_buff_l[i_l] = (fs_uint32_l>>24) & 0xFF; i_l = i_l + 1;    
    bytesarr_buff_l[i_l] = (fs_uint32_l>>16) & 0xFF; i_l = i_l + 1;    
    bytesarr_buff_l[i_l] = (fs_uint32_l>>8) & 0xFF; i_l = i_l + 1;    
    bytesarr_buff_l[i_l] = fs_uint32_l & 0xFF; i_l = i_l + 1;    

    sock_l.sendall(bytesarr_buff_l)

def stream_set_send_data_sampling_freq(sock_p, fs_p):  
    bytesarr_buff_l = bytearray(7)        
    # bytesarr_buff_l = bytearray(30 + 4)        

    i_l = 0
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 0; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = 3; i_l = i_l + 1;   
    # bytesarr_buff_l[i_l] = 30; i_l = i_l + 1;   

    bytesarr_buff_l[i_l] = PACKET_HEADER_COMMAND; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = CMD_SET_SEND_DATA_FREQUENCY; i_l = i_l + 1;
    bytesarr_buff_l[i_l] = np.uint8(fs_p*10); i_l = i_l + 1;

    sock_l.sendall(bytesarr_buff_l)  

if __name__ == "__main__":

    sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    # server_address_l = ("192.168.4.1", 5000)
    server_address_l = ("192.168.4.1", 5001)
    print(": Connecting to " + str(server_address_l))
    sock_l.connect(server_address_l)
    
    print(": Connected")

    # block_l = sock_l.recv(1000)    

    # print(block_l)

    # arr2 = bytearray(b"01000")
    # sock_l.sendall(arr2)

    i = 0

    while (i < 1):
        # stream_stop(sock_p=sock_l)
        stream_start(sock_p=sock_l)
        # stream_set_sampling_freq(sock_p=sock_l, fs_p=1000)
        # stream_set_send_data_sampling_freq(sock_p=sock_l, fs_p=20)

        # time.sleep(0.001)
        time.sleep(1)
        # time.sleep(10)
        i = i + 1

    sock_l.shutdown(socket.SHUT_RDWR)
    sock_l.close()

