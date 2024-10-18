#ifndef IAWARE_GPIO_H
#define IAWARE_GPIO_H

#include "driver/adc.h"
#include "driver/gpio.h"

#define GPIO_OUTPUT_LOW 	0
#define GPIO_OUTPUT_HIGH 	1

#define GPIO_LED_ONBOARD 	GPIO_NUM_2

int iaware_analogRead(void);
void iaware_init_gpio(void);

void turn_on_LED_ONBOARD(void);
void turn_off_LED_ONBOARD(void);

void led_onboard_ap_start(void);
void led_onboard_ap_stop(void);
void led_onboard_client_connected(void);
void led_onboard_client_disconnected(void);
void led_onboard_send_data_to_client(void);

#endif