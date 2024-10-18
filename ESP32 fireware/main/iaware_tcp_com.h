#ifndef IAWARE_TCP_COM_H
#define IAWARE_TCP_COM_H

#define TCP_MAX_LATENCY	2000 // [ms]. The maximum latency that could be possible in the transmission.

#define TCP_RECV_PORT   5001
#define TCP_SEND_PORT   5000
#define TCP_RECV_LISTENQ    2  // The backlog argument defines the maximum length to which the queue of pending connections for sockfd may grow.  If a connection request arrives when the queue is full, the client may receive an error with an indication of ECONNREFUSED or, if the underlying protocol supports retransmission, the request may be ignored so that a later reattempt at connection succeeds.
#define TCP_RECV_MESSAGE    "Hello TCP Client!!"
#define TCP_SEND_MESSAGE    "Hello TCP Client!!"
#define TCP_SEND_FREQUENCY	20	// [Hz]

extern uint8_t tcp_send_frequency;

extern uint8_t is_start_stream;

void com_tcp_recv_task(void *event_group);
void com_tcp_send_task(void *event_group);

void close_cs(void);

#endif