#include <stdint.h>
#include <stdio.h>

#include "esp_err.h"
#include "esp_event.h"
#include "esp_event_loop.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "nvs_flash.h"

#include "iaware_helper.h"
#include "iaware_packet.h"
#include "main.h"


const char* err_to_str(esp_err_t err)
{
    switch (err) 
    {
        case ESP_OK:
            return "ESP_OK";
        case ESP_FAIL:
            return "ESP_FAIL";
        case ESP_ERR_NO_MEM:
            return "ESP_ERR_NO_MEM";
        case ESP_ERR_INVALID_ARG:
            return "ESP_ERR_INVALID_ARG";
        case ESP_ERR_INVALID_SIZE:
            return "ESP_ERR_INVALID_SIZE";
        case ESP_ERR_INVALID_STATE:
            return "ESP_ERR_INVALID_STATE";
        case ESP_ERR_NOT_FOUND:
            return "ESP_ERR_NOT_FOUND";
        case ESP_ERR_NOT_SUPPORTED:
            return "ESP_ERR_NOT_SUPPORTED";
        case ESP_ERR_TIMEOUT:
            return "ESP_ERR_TIMEOUT";
        case ESP_ERR_NVS_NOT_INITIALIZED:
            return "ESP_ERR_NVS_NOT_INITIALIZED";
        case ESP_ERR_NVS_NOT_FOUND:
            return "ESP_ERR_NVS_NOT_FOUND";
        case ESP_ERR_NVS_TYPE_MISMATCH:
            return "ESP_ERR_NVS_TYPE_MISMATCH";
        case ESP_ERR_NVS_READ_ONLY:
            return "ESP_ERR_NVS_READ_ONLY";
        case ESP_ERR_NVS_NOT_ENOUGH_SPACE:
            return "ESP_ERR_NVS_NOT_ENOUGH_SPACE";
        case ESP_ERR_NVS_INVALID_NAME:
            return "ESP_ERR_NVS_INVALID_NAME";
        case ESP_ERR_NVS_INVALID_HANDLE:
            return "ESP_ERR_NVS_INVALID_HANDLE";
        case ESP_ERR_NVS_REMOVE_FAILED:
            return "ESP_ERR_NVS_REMOVE_FAILED";
        case ESP_ERR_NVS_KEY_TOO_LONG:
            return "ESP_ERR_NVS_KEY_TOO_LONG";
        case ESP_ERR_NVS_PAGE_FULL:
            return "ESP_ERR_NVS_PAGE_FULL";
        case ESP_ERR_NVS_INVALID_STATE:
            return "ESP_ERR_NVS_INVALID_STATE";
        case ESP_ERR_NVS_INVALID_LENGTH:
            return "ESP_ERR_NVS_INVALID_LENGTH";
        case ESP_ERR_WIFI_NOT_INIT:
            return "ESP_ERR_WIFI_NOT_INIT";
        //case ESP_ERR_WIFI_NOT_START:
        //  return "ESP_ERR_WIFI_NOT_START";
        case ESP_ERR_WIFI_IF:
            return "ESP_ERR_WIFI_IF";
        case ESP_ERR_WIFI_MODE:
            return "ESP_ERR_WIFI_MODE";
        case ESP_ERR_WIFI_STATE:
            return "ESP_ERR_WIFI_STATE";
        case ESP_ERR_WIFI_CONN:
            return "ESP_ERR_WIFI_CONN";
        case ESP_ERR_WIFI_NVS:
            return "ESP_ERR_WIFI_NVS";
        case ESP_ERR_WIFI_MAC:
            return "ESP_ERR_WIFI_MAC";
        case ESP_ERR_WIFI_SSID:
            return "ESP_ERR_WIFI_SSID";
        case ESP_ERR_WIFI_PASSWORD:
            return "ESP_ERR_WIFI_PASSWORD";
        case ESP_ERR_WIFI_TIMEOUT:
            return "ESP_ERR_WIFI_TIMEOUT";
        case ESP_ERR_WIFI_WAKE_FAIL:
            return "ESP_ERR_WIFI_WAKE_FAIL";
        default:
            return "Unknown ESP_ERR error";
    }
}

void pop_buff_node_group1(void) 
// The function frees tail_buff_node_ptr. If it is the last element, it will empty the list.
{
    struct buff_node *tmp_ptr = tail_buff_node_ptr;

    if (head_buff_node_ptr != NULL)
    {
        if (tail_buff_node_ptr == head_buff_node_ptr)
        {
            head_buff_node_ptr  = NULL;
            run_buff_node_ptr   = NULL;
            tail_buff_node_ptr  = NULL;              
        }
        else
        {
            tail_buff_node_ptr->prev->next = NULL;

            tail_buff_node_ptr = tail_buff_node_ptr->prev;
        }
    
        free_buff_node_group1(&tmp_ptr);
    }
}

int append_buff_node_group1(uint32_t elt_count) 
{
    struct buff_node *tmp_ptr = buff_node_group1_alloc(elt_count);

    if (tmp_ptr != NULL)
    {
        if (head_buff_node_ptr == NULL)
        {
            head_buff_node_ptr = tmp_ptr;
            run_buff_node_ptr = tmp_ptr;
            tail_buff_node_ptr = tmp_ptr;
        }
        else
        {
            tmp_ptr->prev = tail_buff_node_ptr;
            tail_buff_node_ptr->next = tmp_ptr;

            tail_buff_node_ptr = tmp_ptr;
        }

        return iawTrue;
    }
    else
    {
        return iawFalse;
    }
}

void free_all_buff_node_group1(void)
{
    while (tail_buff_node_ptr != NULL)
    {
        struct buff_node *prev_ptr = tail_buff_node_ptr->prev;

        free_buff_node_group1(&tail_buff_node_ptr);

        tail_buff_node_ptr = prev_ptr;
    }    

    head_buff_node_ptr  = NULL;
    run_buff_node_ptr   = NULL;
    tail_buff_node_ptr  = NULL;  
}

void free_buff_node_group1(struct buff_node **curr_ptr)
{
    if ((*curr_ptr) != NULL)
    {
        struct buff_node *prev_ptr = (*curr_ptr)->prev;
        struct buff_node *next_ptr = (*curr_ptr)->next;

        // Isolate the current buff node.
        if (prev_ptr != NULL)
        {
            prev_ptr->next = next_ptr;    
        }

        if (next_ptr != NULL)
        {
            next_ptr->prev = prev_ptr;
        }

        free((*curr_ptr)->samples_buff);
        free(*curr_ptr);

        *curr_ptr = NULL;
    }
}

struct buff_node *buff_node_group1_alloc(uint32_t elt_count) 
{
    uint8_t *samples_buff = NULL;
    if ((samples_buff = (uint8_t *)calloc(4 + PACKET_HEADER_GROUP1_META_SIZE + 2*elt_count, sizeof(uint8_t))) == NULL) // 4 bytes for the length + 1 byte for PACKET_HEADER_GROUPx + 8 bytes to represent the duration in microsec that we use to contruct that data. We multiply with 2 because each sample is represented by two bytes.
        return NULL;

    uint8_t a[4];
    uint32_to_bytes(PACKET_HEADER_GROUP1_META_SIZE + 2*elt_count, a); // 1 byte for PACKET_HEADER_GROUPx, 8 bytes for the duration in microsec.
    samples_buff[0] = a[0];
    samples_buff[1] = a[1];
    samples_buff[2] = a[2];
    samples_buff[3] = a[3];

    samples_buff[4] = PACKET_HEADER_GROUP1;

    struct buff_node *retVal = malloc(sizeof(struct buff_node));
    if (retVal == NULL)
    {
        free(samples_buff);
        return NULL;    
    }
    
    retVal->prev = NULL;

    retVal->is_sent = iawTrue;

    retVal->packet_header_group_id = PACKET_HEADER_GROUP1;

    retVal->t_begin = 0;

    retVal->samples_buff            = samples_buff;

    retVal->n_samples               = 2*elt_count;
    retVal->i_samples               = 0;

    retVal->next = NULL;

    return retVal;    
}


void free_null(void **ptr)
{
    if ((*ptr) != NULL)
    {
        free(*ptr);

        *ptr = NULL;
    }
}

void uint32_to_bytes(uint32_t num, uint8_t a[])
// a[0] contains the leading bits.
{
    a[0] = (num>>24) & 0xFF;
    a[1] = (num>>16) & 0xFF;
    a[2] = (num>>8) & 0xFF;
    a[3] = num & 0xFF;
}

void uint64_to_bytes(uint64_t num, uint8_t a[])
// a[0] contains the leading bits.
{
    a[0] = (num>>56) & 0xFFFF;
    a[1] = (num>>48) & 0xFFFF;
    a[2] = (num>>40) & 0xFFFF;
    a[3] = (num>>32) & 0xFFFF;
    a[4] = (num>>24) & 0xFFFF;
    a[5] = (num>>16) & 0xFFFF;
    a[6] = (num>>8) & 0xFFFF;
    a[7] = num & 0xFFFF;
}

uint32_t bytes_to_uint32(uint8_t a[])
// a[0] contains the leading bits.
{
    return (a[0] << 24) | (a[1] << 16) | (a[2] << 8) | a[3];    
}

uint64_t bytes_to_uint64(uint8_t a[])
// a[0] contains the leading bits.
{
    return (a[0] << 56) | (a[1] << 48) | (a[2] << 40) | (a[3] << 32) | (a[4] << 24) | (a[5] << 16) | (a[6] << 8) | a[7];    
}


int getSSID(uint8_t *mac, char *ssid)
// Params
//     ssid : an array of 15 char (14 characters, plus NULL terminator).
{
    sprintf(ssid, "i-Aware-%02x%02x%02x", (unsigned char)(mac[3]), (unsigned char)(mac[4]), (unsigned char)(mac[5]));

    return 0;
}


static SemaphoreHandle_t xSem_printf = NULL;

int x_printf_int(char *msg)
// Mutual exclusive printf. return 0 when success.
{
    extern SemaphoreHandle_t xSem_printf;

    vSemaphoreCreateBinary(xSem_printf);    

    if(xSem_printf != NULL)
    {
        printf("Semaphore Creation: Success\n");
        return 0;
    } 
    else
    {
        printf("Semaphore Creation: Fail\n");
        return 1;
    }            
}

int x_printf(char *msg)
// Mutual exclusive printf. return 0 when success.
{
    // extern SemaphoreHandle_t xSem_printf;

    // /*check and waits for semaphore to be released for 100 ticks. 
    // If the semaphore is available it is taken / blocked */    
    // if(xSemaphoreTake(xSem_printf, (TickType_t) 100) == pdTRUE )
    // {
    //     printf(msg);
    //     vTaskDelay(100 / portTICK_RATE_MS);
    //     xSemaphoreGive(xSem_printf);

        return 0;
    // }
    // else
    // {
    //     //Does something else in case the semaphore is not available
        // return 1;
    // } 
}


static union u_type
{
  uint16_t  IntVar;
  uint8_t   Bytes[2];
} temp;            

uint8_t highbyte(uint16_t num)
{
    temp.IntVar = num;

    return temp.Bytes[1];
}

uint8_t lowbyte(uint16_t num)
{
    temp.IntVar = num;

    return temp.Bytes[0];
}
