#ifndef IAWARE_WIFI_H
#define IAWARE_WIFI_H

#include <stdint.h>

#include "esp_log.h"
#include "esp_system.h"
#include "FreeRTOSConfig.h"
#include "freertos/event_groups.h"

// Core
#define SLEEP_TIME_MICROSEC 1000000 // [microsec]

// FreeRTOS
#define XTASK_MID_PRIORITY  3
#define XTASK_LOW_PRIORITY  1

// Logging
#define ESP_LOG_LEVEL_WIFI			ESP_LOG_ERROR
#define ESP_LOG_LEVEL_BOOT			ESP_LOG_ERROR
#define ESP_LOG_LEVEL_CPU_START     ESP_LOG_ERROR
#define ESP_LOG_LEVEL_ESP_IMAGE     ESP_LOG_ERROR
#define ESP_LOG_LEVEL_HEAP_INIT     ESP_LOG_ERROR
#define ESP_LOG_LEVEL_SYSTEM_API    ESP_LOG_ERROR
#define ESP_LOG_LEVEL_PHY           ESP_LOG_ERROR
#define ESP_LOG_LEVEL_TCPIP_ADAPTER ESP_LOG_ERROR

#define iawTrue     1
#define iawFalse    0

extern char *IAWARE_EVENT;
#define ESP_LOG_LEVEL_IAWARE_EVENT 	ESP_LOG_WARN
// #define ESP_LOG_LEVEL_IAWARE_EVENT  ESP_LOG_INFO

extern char *IAWARE_NETWORK;
#define ESP_LOG_LEVEL_IAWARE_NETWORK  ESP_LOG_WARN
// #define ESP_LOG_LEVEL_IAWARE_NETWORK  ESP_LOG_INFO

extern char *IAWARE_CORE;
// #define ESP_LOG_LEVEL_IAWARE_CORE  ESP_LOG_WARN
#define ESP_LOG_LEVEL_IAWARE_CORE  ESP_LOG_INFO

extern char *IAWARE_GPIO;
// #define ESP_LOG_LEVEL_IAWARE_GPIO  ESP_LOG_WARN
#define ESP_LOG_LEVEL_IAWARE_GPIO  ESP_LOG_INFO

extern char *IAWARE_BLE;
// #define ESP_LOG_LEVEL_IAWARE_BLE  ESP_LOG_WARN
#define ESP_LOG_LEVEL_IAWARE_BLE  ESP_LOG_INFO

#define IP4_ADDR_2NUM   4   // 192.168.IP4_ADDR_2NUM.IP4_ADDR_3NUM
#define IP4_ADDR_3NUM   1   // 192.168.IP4_ADDR_2NUM.IP4_ADDR_3NUM
// #define IP4_ADDR        192.168.IP4_ADDR_2NUM.IP4_ADDR_3NUM

extern EventGroupHandle_t event_group;

extern int32_t AP_IS_START_BIT;			// Set bit when AP starts.
extern int32_t AP_IS_STACONNECTED_BIT;	// Set bit when a client is connected.

extern int32_t AP_STAIPASSIGNED_BIT;
extern int32_t AP_PROBEREQRECVED_BIT;

extern char *com_tcp_inet_addr;

extern struct buff_node *head_buff_node_ptr;
extern struct buff_node *run_buff_node_ptr;
extern struct buff_node *tail_buff_node_ptr;

extern struct buff_node *run_tcp_send_buff_node_ptr;

// Reboot ESP32.
void deep_restart(void);

// The non-volatile storage
void nvs_read_sampling_data_fs(void);
int nvs_write_sampling_data_fs(uint32_t fs);

#endif