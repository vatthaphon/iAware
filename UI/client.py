import matplotlib.pyplot as plt
import numpy as np
import pickle
import socket
import sys
import time

from socket import SHUT_RDWR

if __name__ == '__main__':
	# Create a TCP/IP socket
	sock_l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	server_address_l = ('localhost', 5000)
	print("connecting to " + str(server_address_l))
	sock_l.connect(server_address_l)

	try:
		tic_l = time.time()*1000
		data = b''
		i = 0
		while True:
			block = sock_l.recv(10000)

			print(i)
			i = i + 1			
			if not block: 
				break

			data += block	

		print("assemble " + str(len(data)) + " bytes for " + str(time.time()*1000 - tic_l) + " ms.")

		data_arr = np.frombuffer(data, dtype=np.uint16)

	
		plt.plot(data_arr)
		plt.show()

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