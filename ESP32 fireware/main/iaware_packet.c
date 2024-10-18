#include "iaware_packet.h"

uint8_t PACKET_HEADER_COMMAND   = 0;
uint8_t PACKET_HEADER_GROUP1    = 1;
uint8_t PACKET_HEADER_GROUP2    = 2;

uint8_t CMD_START_STREAM            = 0;
uint8_t CMD_STOP_STREAM             = 1;
uint8_t CMD_SET_SAMPLING_FREQUENCY  = 2;
uint8_t CMD_SET_SEND_DATA_FREQUENCY = 3;

uint8_t CMD_SET_FIRMWARE_UPLOAD     = 100;