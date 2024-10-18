import matplotlib.pyplot as plt
import numpy as np
import pickle
import socket
import sys
import time

from socket import SHUT_RDWR

Fs_g = 20_000 # [Hz], the sampling frequency of the data.
Fs_senddata_g = 20 # [Hz], how frequent we send data.
Fs_sine_g = 10 # [Hz], the frequency of the sine wave.

########## Communication with the server
server_ip_g = "localhost"
# server_ip_g = "192.168.0.110"
server_port_g = 5000

def getsine(t_begin_p):
	global Fs_g, Fs_senddata_g

	t_l = np.arange(t_begin_p, t_begin_p + 1/Fs_senddata_g, 1/Fs_g)

	y_l = (np.sin(2*np.pi*Fs_sine_g*t_l) + 1.0)*65535/2.0
	y_l = y_l.astype("uint16") 

	
	return y_l, t_begin_p + 1/Fs_senddata_g

if __name__ == '__main__':

	# Create a TCP/IP socket
	sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Bind the socket to the port
	server_address_l = (server_ip_g, server_port_g)
	print("Start")
	sock_l.bind(server_address_l)

	# Listen for incoming connections
	sock_l.listen(1)

	while True:
		# Wait for a connection
		print("waiting for a connection")
		connection_l, client_address_l = sock_l.accept() # If there is a client connects, we do next step.

		try:
			print("connection from " + str(client_address_l))

			t_end_l = 0.0
			while True:
				time.sleep(1/Fs_senddata_g)

				y_l, t_end_l = getsine(t_end_l)

				# print(len(y_l))
				# serialized_y_l = pickle.dumps(y_l, protocol=2)
				connection_l.sendall(y_l.tobytes())

			# plt.plot(y_l)
			# plt.show()
				# break

		finally:
			# Clean up the connection
			print("closing connection")
			connection_l.close()
			# sock_l.shutdown(SHUT_RDWR)
			# sock_l.close()

	# print("closing connection")
	# connection_l.close()
	# sock_l.shutdown(SHUT_RDWR)
	# sock_l.close()


	# 	break

	# connection_l.close()


	# # Create a TCP/IP socket
	# sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# # Bind the socket to the port
	# server_address_l = ('localhost', 5000)
	# print("Start")
	# sock_l.bind(server_address_l)

	# # Listen for incoming connections
	# sock_l.listen(1)

	# while True:
	# 	# Wait for a connection
	# 	print("waiting for a connection")
	# 	connection_l, client_address_l = sock_l.accept()	

	# 	try:
	# 		print("connection from " + str(client_address_l))

	# 		# Receive the data in small chunks and retransmit it
	# 		while True:
	# 			data_l = connection_l.recv(16)
	# 			# print("received")				

	# 			if data_l:
	# 				# print("sending data back to the client")

	# 				print(data_l)
	# 				connection_l.sendall(data_l)
	# 			else:
	# 				print("no more data from " + str(client_address_l))

	# 				break

	# 	finally:
	# 		# Clean up the connection
	# 		connection_l.close()