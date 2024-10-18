#include <errno.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "esp_event.h"
#include "esp_event_loop.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/event_groups.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"
#include "nvs_flash.h"

#include "iaware_gpio.h"
#include "iaware_helper.h"
#include "iaware_packet.h"
#include "iaware_sampling_data.h"
#include "iaware_tcp_com.h"
#include "main.h"

static void close_all(const char *TAG, int socket, int accept);

// com_tcp_recv_task
static const char *TAG_TCP_RECV = "com_tcp_recv_task";
static const uint8_t COM_TCP_RECV_WAITFOR_DATALENGTH = 0;
static const uint8_t COM_TCP_RECV_FETCH_MSG = 1;
static const uint8_t COM_TCP_RECV_PROCESS_MSG = 2;
static uint8_t com_tcp_recv_task_err(void);
static void set_new_sampling_frequency(uint32_t new_fs);
static int cs_recv_ext = -1;

// com_tcp_send_task
static const char *TAG_TCP_SEND = "com_tcp_send_task";
static int cs_send_ext = -1;
static int send_all(int socket, uint8_t *buffer, size_t length);
static uint8_t com_tcp_send_task_err(void);

uint8_t tcp_send_frequency = TCP_SEND_FREQUENCY;
uint8_t is_start_stream = iawFalse;
// uint8_t is_start_stream = iawTrue;

void com_tcp_recv_task(void *event_group)
{
    struct sockaddr_in tcpServerAddr, remote_addr;

    uint32_t socklen = sizeof(remote_addr);
    uint32_t data_len = 0, i_data_len;

    uint8_t recv_buf[MAX_PACKET_SIZE_SENTTO_ESP32], tmp_len[4], recv_state;
    uint8_t data_len_bytes[4], i_data_len_bytes;

    int s, cs, mytrue = 1;

    ssize_t r;

    uint8_t *msg = NULL;

    tcpServerAddr.sin_addr.s_addr   = htonl(INADDR_ANY);
    tcpServerAddr.sin_family        = AF_INET;
    tcpServerAddr.sin_port          = htons(TCP_RECV_PORT);

    WAIT_AP_START: while (1)    // Level 0
    {
        free_null((void **) (&msg));

        // Wait for the Wifi AP to start.Because INCLUDE_vTaskSuspend in FreeRTOSConfig.h is set to 1, xEventGroupWaitBits will wait forever.
        xEventGroupWaitBits((EventGroupHandle_t) event_group, AP_IS_START_BIT, pdFALSE, pdTRUE, portMAX_DELAY);

        RECREATE_SOCKET: while (1)  // Level 1
        {
            free_null((void **) (&msg));

            ESP_LOGI(IAWARE_NETWORK, "Recv. conns: Try to create a socket.");

            // Create an IP4 socket.
            if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0)                
            {
                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Failed to allocate socket (%s, %d).", strerror(errno), errno);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }        

            // Set socket's option.
            if (setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &mytrue, sizeof(int)) < 0)
            {
                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Failed to socket's option (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_RECV, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            } 

            // Bind the IP4 socket to an IP address and a port.
            if (bind(s, (struct sockaddr *) (&tcpServerAddr), sizeof(tcpServerAddr)) < 0) 
            {
                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Failed to bind socket (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_RECV, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }     

            // Listen the IP4 socket.
            if (listen (s, TCP_RECV_LISTENQ) < 0) 
            {
                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Failed to listen (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_RECV, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }        

            WAIT_FOR_A_CLIENT: while (1)    // Level 2
            {
                free_null((void **) (&msg));

                ESP_LOGI(IAWARE_NETWORK, "Recv. conns: Wait for a client.");

                recv_state = COM_TCP_RECV_WAITFOR_DATALENGTH; // Here, we implicitly assume that new accept causes fresh recv().
                i_data_len_bytes = 0;

                // Wait for a new client to connect. This corresponds to socket.socket.connect.
                if ((cs = accept(s, (struct sockaddr *) (&remote_addr), &socklen)) < 0)
                {
                    ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Failed to accept (%s, %d).", strerror(errno), errno);

                    close_all(TAG_TCP_RECV, s, -1);

                    vTaskDelay(1000 / portTICK_PERIOD_MS);

                    goto RECREATE_SOCKET;
                }
                cs_recv_ext = cs;

                // x_printf("Recv. conns: New connection request.\n");

                WAIT_TO_RECV: while (1) // Level 3
                {
                    // x_printf("Recv. conns: Wait for data.\n");

                    r = recv(cs, recv_buf, sizeof(recv_buf), 0);

                    // Error.
                    if (r < 0)
                    {
                        ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Read data fail caused by %s (%d)", strerror(errno), errno);

                        vTaskDelay(1000 / portTICK_PERIOD_MS);

                        switch (com_tcp_recv_task_err())
                        {
                            case 0:
                                close_all(TAG_TCP_RECV, s, cs);

                                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Wait for AP to start.");

                                goto WAIT_AP_START;
                            case 1:
                                close_all(TAG_TCP_RECV, s, cs);

                                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Recreate a socket.");

                                goto RECREATE_SOCKET;
                            case 2:
                                close_all(TAG_TCP_RECV, s, cs);                            

                                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Wait for a new client.");

                                goto WAIT_FOR_A_CLIENT;
                            case 3:

                                ESP_LOGW(IAWARE_NETWORK, "Recv. conns: Wait for a new recv().");

                                goto WAIT_TO_RECV;
                        }
         
                    }
                    // No msg in the stream left.
                    else if (r == 0)
                    {
                        ESP_LOGI(IAWARE_NETWORK, "Recv. conns: zero return.");   

                        close_all(TAG_TCP_RECV, -1, cs);

                        goto WAIT_FOR_A_CLIENT;                        
                    }
                    else
                    {
                        ssize_t remain_r = r;
                        int i_r = 0;

                        // We process it till nothing left in the buffer. 
                        while (remain_r > 0)
                        {
                            // This state is for getting the first four bytes that are for identifying the length of the data in bytes.
                            if (recv_state == COM_TCP_RECV_WAITFOR_DATALENGTH)
                            {                                
                                // Fetch recv() till either 4-bytes data length is filled or the buffer is empty.
                                while ((i_data_len_bytes < 4) && (i_r < r))
                                {
                                    data_len_bytes[i_data_len_bytes] = recv_buf[i_r];

                                    i_data_len_bytes = i_data_len_bytes + 1;
                                    i_r = i_r + 1;

                                    remain_r = remain_r - 1;
                                }

                                // If the 4-bytes data length is completely filled, we go to the next state. 
                                // It might be possible that there is some data left in the recv() buffer.
                                if (i_data_len_bytes == 4)
                                {
                                    data_len = bytes_to_uint32(data_len_bytes);
                                    i_data_len = 0;

                                    if ((msg = (uint8_t *)calloc(data_len, sizeof(uint8_t))) == NULL)
                                    {
                                        ESP_LOGE(IAWARE_CORE, "Recv. conns: calloc() fails.");

                                        close_all(TAG_TCP_RECV, -1, cs);

                                        goto WAIT_FOR_A_CLIENT;
                                    }

                                    recv_state = COM_TCP_RECV_FETCH_MSG;
                                }
                            }

                            // When we already knew the lenght of the msg in bytes, we collect all those bytes. When it completes, we pass to the next state that is processing the msg.
                            if (recv_state == COM_TCP_RECV_FETCH_MSG)
                            {
                                while ((i_data_len < data_len) && (i_r < r))
                                {
                                    msg[i_data_len] = recv_buf[i_r];

                                    i_data_len = i_data_len + 1;
                                    i_r = i_r + 1;

                                    remain_r = remain_r - 1;
                                }

                                // We have a complete message.
                                if (i_data_len == data_len)
                                {
                                    recv_state = COM_TCP_RECV_PROCESS_MSG;
                                }
                            }

                            // When we finish process the msg, we return the state back to getting next msg.
                            if (recv_state == COM_TCP_RECV_PROCESS_MSG)
                            {
                                ESP_LOGI(IAWARE_NETWORK, "Recv. conns: Get %d bytes.", data_len);

                                uint32_t i_msg = 0;

                                if (msg[i_msg] == PACKET_HEADER_COMMAND)
                                {            
                                    i_msg = i_msg + 1;

                                    if (msg[i_msg] == CMD_START_STREAM)
                                    {
                                        ESP_LOGI(IAWARE_CORE, "Recv. conns: CMD_START_STREAM");

                                        is_start_stream = iawTrue;
                                    }
                                    else if (msg[i_msg] == CMD_STOP_STREAM)
                                    {
                                        ESP_LOGI(IAWARE_CORE, "Recv. conns: CMD_STOP_STREAM");

                                        is_start_stream = iawFalse;
                                    }
                                    else if (msg[i_msg] == CMD_SET_SAMPLING_FREQUENCY)
                                    {
                                        ESP_LOGI(IAWARE_CORE, "Recv. conns: CMD_SET_SAMPLING_FREQUENCY");
                                        
                                        i_msg = i_msg + 1;
                                        tmp_len[0] = msg[i_msg];        

                                        i_msg = i_msg + 1;
                                        tmp_len[1] = msg[i_msg];

                                        i_msg = i_msg + 1;
                                        tmp_len[2] = msg[i_msg];

                                        i_msg = i_msg + 1;
                                        tmp_len[3] = msg[i_msg];

                                        uint32_t new_sampling_frequency = bytes_to_uint32(tmp_len);

                                        set_new_sampling_frequency(new_sampling_frequency);                                                                                
                                        
                                    }
                                    else if (msg[i_msg] == CMD_SET_SEND_DATA_FREQUENCY)
                                    {
                                        ESP_LOGI(IAWARE_CORE, "Recv. conns: CMD_SET_SEND_DATA_FREQUENCY");

                                        i_msg = i_msg + 1;
                                        printf("Recv. conns: Set new send-data sampling frequency to %f Hz.", msg[i_msg]*0.1);
                                    }
                                }
                                else
                                    ESP_LOGI(IAWARE_CORE, "Recv. conns: header %d does not support.", msg[i_msg]);

                                free_null((void **) (&msg));

                                recv_state = COM_TCP_RECV_WAITFOR_DATALENGTH;
                                i_data_len_bytes = 0;
                            }      
                        }                  
                    }
                }
            }
        }
    }
}


void close_cs(void)
{
    if (cs_recv_ext >= 0)
        close(cs_recv_ext);   

    if (cs_send_ext >= 0)
        close(cs_send_ext);  
}


void com_tcp_send_task(void *event_group)
{
    struct sockaddr_in tcpServerAddr, remote_addr;

    uint32_t socklen = sizeof(remote_addr);

    int s, cs, mytrue = 1;

    tcpServerAddr.sin_addr.s_addr   = htonl(INADDR_ANY);
    tcpServerAddr.sin_family        = AF_INET;
    tcpServerAddr.sin_port          = htons(TCP_SEND_PORT);

    WAIT_AP_START: while (1)    // Level 0
    {
        // Wait for the Wifi AP to start.Because INCLUDE_vTaskSuspend in FreeRTOSConfig.h is set to 1, xEventGroupWaitBits will wait forever.
        xEventGroupWaitBits((EventGroupHandle_t) event_group, AP_IS_START_BIT, pdFALSE, pdTRUE, portMAX_DELAY);

        RECREATE_SOCKET: while (1)  // Level 1
        {
            // Create an IP4 socket.
            if ((s = socket(AF_INET, SOCK_STREAM, 0)) < 0)                
            {
                ESP_LOGW(IAWARE_NETWORK, "Send conns: Failed to allocate socket (%s, %d).", strerror(errno), errno);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }        

            // Set socket's option.
            if (setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &mytrue, sizeof(int)) < 0)
            {
                ESP_LOGW(IAWARE_NETWORK, "Send conns: Failed to socket's option (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_SEND, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            } 

            // Bind the IP4 socket to an IP address and a port.
            if (bind(s, (struct sockaddr *)&tcpServerAddr, sizeof(tcpServerAddr)) < 0) 
            {
                ESP_LOGW(IAWARE_NETWORK, "Send conns: Failed to bind socket (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_SEND, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }     

            // Listen the IP4 socket.
            if (listen (s, TCP_RECV_LISTENQ) < 0) 
            {
                ESP_LOGW(IAWARE_NETWORK, "Send conns: Failed to listen (%s, %d).", strerror(errno), errno);

                close_all(TAG_TCP_SEND, s, -1);

                vTaskDelay(1000 / portTICK_PERIOD_MS);

                goto RECREATE_SOCKET;
            }        

            WAIT_FOR_A_CLIENT: while (1)    // Level 2
            {
                ESP_LOGI(IAWARE_NETWORK, "Send conns: Wait for a client.");

                // Wait for a new client to connect. This corresponds to socket.socket.connect.
                if ((cs = accept(s, (struct sockaddr *)&remote_addr, &socklen)) < 0)
                {
                    close_all(TAG_TCP_SEND, s, -1);

                    vTaskDelay(1000 / portTICK_PERIOD_MS);

                    goto RECREATE_SOCKET;
                }
                cs_send_ext = cs;
                run_tcp_send_buff_node_ptr = run_buff_node_ptr;

                WAIT_TO_SEND: while (1) // Level 3
                {
                    if (run_tcp_send_buff_node_ptr->is_sent == iawFalse)
                    {
                        run_tcp_send_buff_node_ptr->is_sent = iawTrue;

                        int64_t pre_time = esp_timer_get_time(); // [microsec.]

                        int r = 0;

                        if (is_start_stream == iawTrue)
                        {
                            led_onboard_send_data_to_client();
                            r = send_all(cs, run_tcp_send_buff_node_ptr->samples_buff, run_tcp_send_buff_node_ptr->n_samples + 4 + PACKET_HEADER_GROUP1_META_SIZE);    
                        }

                        if (r < 0)
                        {
                            ESP_LOGW(IAWARE_NETWORK, "Send conns: Send data fail caused by %s (%d)", strerror(errno), errno);

                            vTaskDelay(1000 / portTICK_PERIOD_MS);

                            switch (com_tcp_send_task_err())
                            {
                                case 0:
                                    close_all(TAG_TCP_RECV, s, cs);

                                    ESP_LOGW(IAWARE_NETWORK, "Send conns: Wait for AP to start.");

                                    goto WAIT_AP_START;
                                case 1:
                                    close_all(TAG_TCP_RECV, s, cs);

                                    ESP_LOGW(IAWARE_NETWORK, "Send conns: Recreate a socket.");

                                    goto RECREATE_SOCKET;
                                case 2:
                                    close_all(TAG_TCP_RECV, s, cs);                            

                                    ESP_LOGW(IAWARE_NETWORK, "Send conns: Wait for a new client.");

                                    goto WAIT_FOR_A_CLIENT;
                                case 3:

                                    ESP_LOGW(IAWARE_NETWORK, "Send conns: Wait for a new recv().");

                                    goto WAIT_TO_SEND;
                            }                                                
                        }

                        int64_t cur_time = esp_timer_get_time();

                        if ((cur_time - pre_time) > (int64_t) (1000000/tcp_send_frequency))
                            ESP_LOGW(IAWARE_NETWORK, "Send conns: Too high latency by %" PRId64 " microsec.", (cur_time - pre_time) - (int64_t) (1000000/sampling_data_fs));                    

                        // if ( (cur_time - pre_time) > ((int64_t) (TCP_MAX_LATENCY*1000)) )
                        //     ESP_LOGW( IAWARE_NETWORK, "Send conns: Latency is longer than expected by %" PRId64 " microsec.", (cur_time - pre_time) - ( (int64_t) (TCP_MAX_LATENCY*1000) ) );                    

                        if (run_tcp_send_buff_node_ptr->next != NULL)
                        {
                            run_tcp_send_buff_node_ptr = run_tcp_send_buff_node_ptr->next;
                        }
                        else
                        {
                            run_tcp_send_buff_node_ptr = head_buff_node_ptr;
                        }
                    }

                    vTaskDelay(1 / portTICK_PERIOD_MS);   
                }
            }
        }
    }
}


//////////////////// Private ////////////////////
static void set_new_sampling_frequency(uint32_t new_fs)
{
    ESP_LOGI(IAWARE_CORE, "Recv. conns: Setting new sampling frequency to %d Hz ...", new_fs);    

    ESP_LOGI(IAWARE_CORE, "Recv. conns: Waiting for all accesses of buff nodes to finish ...");

    if (nvs_write_sampling_data_fs(new_fs) == iawTrue)
    {
        ESP_LOGI(IAWARE_CORE, "Recv. conns: Changed to new sampling frequency to %d Hz SUCCESS", new_fs);    
    }
    else
    {
        ESP_LOGE(IAWARE_CORE, "Recv. conns: Changed to new sampling frequency to %d Hz FAIL", new_fs);    
    }

    close_cs();    

    deep_restart();    

    // sampling_data_stopTimer();

    // vTaskDelay(1000 / portTICK_PERIOD_MS);

    // ESP_LOGI(IAWARE_CORE, "Recv. conns: Setting new sampling frequency to %d Hz ...", new_fs);    

    // ESP_LOGI(IAWARE_CORE, "Recv. conns: Waiting for all accesses of buff nodes to finish ...");

    // is_set_new_sampling_frequency = iawTrue;
    // while ( (is_set_new_sampling_frequency_sampling_data_allow == iawFalse) || (is_set_new_sampling_frequency_tcp_send_allow == iawFalse) )
    // {
    //     vTaskDelay(100 / portTICK_PERIOD_MS);        
    // }
    // is_set_new_sampling_frequency = iawFalse;

    // ESP_LOGI(IAWARE_CORE, "Recv. conns: Freeing buff nodes ...");
    // free_all_buff_node_group1();

    // ESP_LOGI(IAWARE_CORE, "Recv. conns: Initializing buff nodes ...");
    // init_buff_nodes();

    // if (nvs_write_sampling_data_fs(new_fs) == iawTrue)
    // {
    //     ESP_LOGI(IAWARE_CORE, "Recv. conns: Changed to new sampling frequency to %d Hz SUCCESS", new_fs);    

    //     sampling_data_startTimer((int64_t) (1000000/new_fs));
    // }
    // else
    // {
    //     ESP_LOGE(IAWARE_CORE, "Recv. conns: Changed to new sampling frequency to %d Hz FAIL", new_fs);    

    //     sampling_data_startTimer((int64_t) (1000000/sampling_data_fs));
    // }    
}

static int send_all(int cs, uint8_t *buffer, size_t length)
{
    uint8_t *ptr = buffer;

    while (length > 0)
    {
        int i = send(cs, ptr, length, 0);

        if (i < 1) 
            return -1;

        ptr += i;
        length -= i;
    }

    return 0;
}

static uint8_t com_tcp_recv_task_err(void)
{
    switch (errno)
    {
        case EBADF :
            return 1;

        case ENOTCONN : // The socket is not connected (POSIX.1)
            return 2;

        default :
            return 1;
    }    
}

static uint8_t com_tcp_send_task_err(void)
{
    switch (errno)
    {
        case EBADF :
            return 1;

        case ENOTCONN : // The socket is not connected (POSIX.1)
            return 2;

        default :
            return 1;
    }    
}

static void close_all(const char *TAG, int socket, int accept)
{
    if (socket >= 0)
    {
        if (close(socket) < 0)
        {
            // x_printf("close(s) fail.\n");                            
            // ESP_LOGE(TAG, "close(s) fail.\n");                          
        }                                
    }

    if (accept >= 0)
    {
        if (close(accept) < 0)
        {
            // x_printf("close(cs) fail.\n");                            
            // ESP_LOGE(TAG, "close(cs) fail.\n");                          
        }        
    }
}