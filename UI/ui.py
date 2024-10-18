import _thread
import matplotlib.pyplot as plt
import numpy as np
import pickle
import socket
import sys
import threading
import time

from socket import SHUT_RDWR

Fs_g = 1000000 # [Hz], the sampling frequency of the data.
Fs_senddata_g = 20 # [Hz], how frequent we send data.

########## Communication with the server
server_ip_g = "localhost"
# server_ip_g = "192.168.0.110"
server_port_g = 5000

N_bytesarr_buff_g = 0
bytesarr_buff_g = None

def communicateWithServer():
	global server_ip_g, server_port_g, N_bytesarr_buff_g

	# Create a TCP/IP socket
	sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	server_address_l = (server_ip_g, server_port_g)
	print("connecting to " + str(server_address_l))
	sock_l.connect(server_address_l)

	try:
		next_block_l = None

		while True:
			tic_l = time.time()*1000
			
			if next_block_l is None:
				idx_bytesarr_buff_l = 0
			else:
				idx_bytesarr_buff_l = len(next_block_l)
				bytesarr_buff_g[0:len(next_block_l)] = next_block_l

			while True:
				block_l = sock_l.recv(1000)

				N_block_l = len(block_l)

				if idx_bytesarr_buff_l + N_block_l <= N_bytesarr_buff_g:
					idx_end_l = idx_bytesarr_buff_l + N_block_l

					valid_block_l 	= block_l
					next_block_l 	= None
				else:
					idx_end_l = N_bytesarr_buff_g

					valid_block_l	= block_l[0:(N_bytesarr_buff_g - idx_bytesarr_buff_l)]
					next_block_l	= block_l[(N_bytesarr_buff_g - idx_bytesarr_buff_l):]

				bytesarr_buff_g[idx_bytesarr_buff_l:idx_end_l] = valid_block_l

				idx_bytesarr_buff_l = idx_end_l

				if idx_end_l == N_bytesarr_buff_g:
					break

			print("Assemble " + str(len(bytesarr_buff_g)) + " bytes for " + str(time.time()*1000 - tic_l - 1000/Fs_senddata_g) + " ms.")

		# uint16arr_buff_l = np.frombuffer(bytesarr_buff_g, dtype=np.uint16)

	
		# plt.plot(uint16arr_buff_l)
		# plt.show()

		# Send data
		# message_l = 'This is the message.  It will be repeated.'
	
		# print("sending " + message_l)

		# sock_l.sendall(message_l.encode())

		# # Look for the response
		# amount_received_l = 0
		# amount_expected_l = len(message_l)

		# while amount_received_l < amount_expected_l:
		# 	data_l = sock_l.recv(16)
		# 	amount_received_l += len(data_l)
		# 	# print("received " + data)

		# print(str(amount_received_l) + "/" + str(amount_expected_l))
	finally:
		print("closing socket")
		# sock_l.shutdown(SHUT_RDWR)
		sock_l.close()	

def init():
	global bytesarr_buff_g, N_bytesarr_buff_g

	N_bytesarr_buff_g = int((2*Fs_g)/Fs_senddata_g)
	bytesarr_buff_g = bytearray(N_bytesarr_buff_g)

	print(N_bytesarr_buff_g)


if __name__ == '__main__':
    ##### Initialize variables
    init()

    ##### Start MUSE OSC server thread
    # com_thread_l = threading.Thread(target=communicateWithServer)
    # com_thread_l.start()

    communicateWithServer()
