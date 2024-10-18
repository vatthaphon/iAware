#include <inttypes.h>
#include <stdio.h>

#include "esp_timer.h"
#include "esp_sleep.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "iaware_gpio.h"
#include "iaware_helper.h"
#include "iaware_packet.h"
#include "iaware_sampling_data.h"
#include "iaware_tcp_com.h"
#include "main.h"

static esp_timer_handle_t sampling_data_Timer;

static void sampling_data_callback(void* arg);
static uint16_t sampling_input(void);


uint32_t sampling_data_fs = SAMPLING_DATA_FS;

void init_sampling_data_task(void)
{
    // Initialize buffer nodes.
    init_buff_nodes();

    // Create a hardware timer.
    sampling_data_createTimer();

    // Start the hardware timer.
    sampling_data_startTimer((int64_t) (1000000/sampling_data_fs));
}

void sampling_data_createTimer(void)
{
    const esp_timer_create_args_t periodic_timer_args = {
        .callback = &sampling_data_callback,
        .name = "periodic"
    };

    ESP_ERROR_CHECK(esp_timer_create(&periodic_timer_args, &sampling_data_Timer));
}

void sampling_data_startTimer(int64_t duration)
// Params:
//     duration    : It has a unit of microsecond.
{
    ESP_LOGI(IAWARE_CORE, "Sample data: Set esp_timer to tick every %" PRId64 " microsec.", duration);

    ESP_ERROR_CHECK(esp_timer_start_periodic(sampling_data_Timer, duration)); 
}

void sampling_data_stopTimer(void)
{
    ESP_ERROR_CHECK(esp_timer_stop(sampling_data_Timer)); 
}

void init_buff_nodes(void)
{
    // Create buffer nodes for filling in the sampled inputs.
    uint32_t N_buff_node = (uint32_t) (TCP_MAX_LATENCY/(1000/tcp_send_frequency));

    uint32_t i = 0;
    while ((i < N_buff_node) & (append_buff_node_group1((uint32_t) (sampling_data_fs/tcp_send_frequency)) == iawTrue))
    {
        i = i + 1;
    }

    if (i == 0)
    {
        ESP_LOGE(IAWARE_CORE, "Sample data: Initialize buff_node (%d bytes) FAIL.", (uint32_t) (2*sampling_data_fs/tcp_send_frequency));

        deep_restart();
    }
    else
    {
        ESP_LOGI(IAWARE_CORE, "Sample data: Initialize buff_node (%d buff nodes = %d bytes).", i, (uint32_t) (i*2*sampling_data_fs/tcp_send_frequency));
    }
}

//////////////////// Private ////////////////////

static void sampling_data_callback(void* arg)
// This function should execute with using as least time as possible. Otherwise we will get this error on the console:
// E (5196) task_wdt: Task watchdog got triggered. The following tasks did not reset the watchdog in time:                                 
// E (5196) task_wdt:  - IDLE0 (CPU 0)                                                                                                     
// E (5196) task_wdt: Tasks currently running:                                                                                             
// E (5196) task_wdt: CPU 0: esp_timer                                                                                                     
// E (5196) task_wdt: CPU 1: IDLE1 
// Please read https://docs.espressif.com/projects/esp-idf/en/latest/api-reference/system/wdts.html for further informaiton.
{
    int64_t pre_time = esp_timer_get_time();

    if (run_buff_node_ptr->i_samples == 0)
    {
        run_buff_node_ptr->t_begin = (uint64_t) pre_time; // Record the time that we begin recording.
    }

    uint16_t sample = sampling_input();

    uint8_t high_sample = highbyte(sample);
    uint8_t low_sample  = lowbyte(sample);

    // Store the high byte of the sample.
    (run_buff_node_ptr->samples_buff)[4 + PACKET_HEADER_GROUP1_META_SIZE + (run_buff_node_ptr->i_samples)] = high_sample; // 4 bytes for the length of the data
    (run_buff_node_ptr->samples_buff)[4 + PACKET_HEADER_GROUP1_META_SIZE + (run_buff_node_ptr->i_samples)] = low_sample;   
    run_buff_node_ptr->i_samples = run_buff_node_ptr->i_samples + 2;

    if (run_buff_node_ptr->i_samples == run_buff_node_ptr->n_samples)
    {        
        // Calculate the effective sampling frequency.
        run_buff_node_ptr->eff_sampling_freq = (uint32_t) ( (run_buff_node_ptr->n_samples - 2)*500000 )/( ( (uint64_t) pre_time ) - (run_buff_node_ptr->t_begin) );

        // Record the effective sampling frequency into the streamed data.
        uint8_t tmp[4];
        uint32_to_bytes(run_buff_node_ptr->eff_sampling_freq, tmp);

        (run_buff_node_ptr->samples_buff)[5] = tmp[0];
        (run_buff_node_ptr->samples_buff)[6] = tmp[1];
        (run_buff_node_ptr->samples_buff)[7] = tmp[2];
        (run_buff_node_ptr->samples_buff)[8] = tmp[3];

        struct buff_node *tmp_ptr = run_buff_node_ptr; // Guarantee thread safe.        

        // Move run_buff_node_ptr to the next node.
        if (run_buff_node_ptr->next != NULL)
        {
            run_buff_node_ptr = run_buff_node_ptr->next;
        }
        else
        {
            // Reach the end of the buff nodes.
            run_buff_node_ptr = head_buff_node_ptr;
        }

        run_buff_node_ptr->i_samples = 0;     
        run_buff_node_ptr->is_sent = iawTrue;

        // Set bit to tell com_tcp_send_task() to send this buffer node.
        tmp_ptr->is_sent  = iawFalse;
    }

    int64_t cur_time = esp_timer_get_time();

    // Check if the operation is longer that the sampling frequency. If it is, we cannot guarantee the right timing.    
    if ((cur_time - pre_time) > (int64_t) (1000000/sampling_data_fs))
        ESP_LOGW(IAWARE_CORE, "Sample data: Too high sampling frequency by %" PRId64 " microsec.", (cur_time - pre_time) - (int64_t) (1000000/sampling_data_fs));   

}

static uint16_t sampling_input(void)
{
    return (uint16_t) iaware_analogRead();
}