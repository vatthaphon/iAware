#ifndef IAWARE_PACKET_H
#define IAWARE_PACKET_H

#include <stdint.h>

// A packet sent between the client and the server have the format |unsigned 8-bit header|unsigned 32-bit specified the number of data in byte|byte1byte2byte3...byteN.
// PACKET_HEADER_COMMAND, etc. are initialized in iaware_packet.c
extern uint8_t PACKET_HEADER_COMMAND;

// A command packet from a client to ESP32.
#define MAX_PACKET_SIZE_SENTTO_ESP32 10				// In bytes

extern uint8_t CMD_START_STREAM;					// |2 (4bytes)|PACKET_HEADER_COMMAND|CMD_START_STREAM
extern uint8_t CMD_STOP_STREAM;						// |2 (4bytes)|PACKET_HEADER_COMMAND|CMD_STOP_STREAM
extern uint8_t CMD_SET_SAMPLING_FREQUENCY;			// |6 (4bytes)|PACKET_HEADER_COMMAND|CMD_SET_SAMPLING_FREQUENCY	|uint32_t new_sampling_frequency
extern uint8_t CMD_SET_SEND_DATA_FREQUENCY;			// |3 (4bytes)|PACKET_HEADER_COMMAND|CMD_SET_SEND_DATA_FREQUENCY|uint8_t new_send_data_sampling_frequency. The actual send data sampling frequency is new_send_data_sampling_frequency*0.1 Hz.

#define PACKET_HEADER_GROUP1_META_SIZE	(1 + 4)		// It is the size in bytes of the meta information between the 4-bytes header and the actual sampled signal, i.e. |(4bytes)|PACKET_HEADER_GROUP1_META_SIZE|buff_data
extern uint8_t PACKET_HEADER_GROUP1;

extern uint8_t PACKET_HEADER_GROUP2;


extern uint8_t CMD_SET_FIRMWARE_UPLOAD;				// |x (4bytes)|PACKET_HEADER_COMMAND|CMD_SET_FIRMWARE_UPLOAD	|FIRMWARE.


#endif