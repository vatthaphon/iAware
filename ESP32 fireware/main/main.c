// Choose idf.py menuconfig->Component config->Wi-FI->WiFi Task Core ID->Core 1
// Choose idf.py menuconfig->Component config->LWIP->TCP/IP task affinity ->CPU1
// Choose idf.py menuconfig->Component config->ESP32-specific->disable Watch CPU0 Idel Task
// Choose idf.py menuconfig->Component config->ESP32-specific->disable Watch CPU1 Idel Task

// Choose idf.py menuconfig->Component config->enable Bluetooth
// Choose idf.py menuconfig->Component config->Bluetooth controller->The cpu core which bluetooth controller run -> Core 1
// Choose idf.py menuconfig->Component config->Bluedroid Enable->The cpu core which Bluedroid run->Core 1
// Choose idf.py menuconfig->Component config->Bluedroid Enable->Enable Include GATT server module
// Choose idf.py menuconfig->Component config->Bluedroid Enable->Enable Include GATT client module

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "driver/adc.h"
#include "driver/gpio.h"
#include "esp_bt.h"            // ESP32 BLE
#include "esp_bt_device.h"     // ESP32 BLE
#include "esp_bt_main.h"       // ESP32 BLE
#include "esp_gap_ble_api.h"   // ESP32 BLE
#include "esp_gatts_api.h"     // ESP32 BLE
#include "esp_gattc_api.h"     // ESP32 BLE
#include "esp_gatt_common_api.h"// ESP32 BLE
#include "esp_event.h"
#include "esp_event_loop.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/event_groups.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"
#include "nvs.h"
#include "nvs_flash.h"

#include "iaware_ble_clt_com.h"
#include "iaware_ble_svr_com.h"
#include "iaware_gpio.h"
#include "iaware_helper.h"
#include "iaware_packet.h"
#include "iaware_sampling_data.h"
#include "iaware_tcp_com.h"
#include "main.h"



// General
static esp_err_t event_handler(void *ctx, system_event_t *event);
static void iaware_init(void);

// Communication
static void init_wifi_in_ap(void);
static void start_dhcp_server(void);

EventGroupHandle_t event_group  = NULL;

int32_t AP_IS_START_BIT         = BIT0;
int32_t AP_IS_STACONNECTED_BIT  = BIT1;

int32_t AP_STAIPASSIGNED_BIT    = BIT2;
int32_t AP_PROBEREQRECVED_BIT   = BIT3;

char *com_tcp_inet_addr = "192.168.IP4_ADDR_2NUM.IP4_ADDR_3NUM";    

// Buffer for sampled input.
struct buff_node *head_buff_node_ptr = NULL;
struct buff_node *run_buff_node_ptr = NULL;
struct buff_node *tail_buff_node_ptr = NULL;

struct buff_node *run_tcp_send_buff_node_ptr = NULL;


// Logging
char *IAWARE_EVENT      = "iaware_event";
char *IAWARE_NETWORK    = "iaware_network";
char *IAWARE_CORE       = "iaware_core";
char *IAWARE_GPIO       = "iaware_gpio";
char *IAWARE_BLE        = "iaware_ble";

void app_main()
{   

    // Set the log levels.
    esp_log_level_set("*", ESP_LOG_ERROR);        // set all components to ERROR level
    // esp_log_level_set("wifi", ESP_LOG_LEVEL_WIFI);
    // esp_log_level_set("boot", ESP_LOG_LEVEL_BOOT);
    // esp_log_level_set("cpu_start", ESP_LOG_LEVEL_CPU_START);
    // esp_log_level_set("esp_image", ESP_LOG_LEVEL_ESP_IMAGE);
    // esp_log_level_set("heap_init", ESP_LOG_LEVEL_HEAP_INIT);
    // esp_log_level_set("system_api", ESP_LOG_LEVEL_SYSTEM_API);
    // esp_log_level_set("phy", ESP_LOG_LEVEL_PHY);
    // esp_log_level_set("tcpip_adapter", ESP_LOG_LEVEL_TCPIP_ADAPTER);

    esp_log_level_set(IAWARE_EVENT, ESP_LOG_LEVEL_IAWARE_EVENT);
    esp_log_level_set(IAWARE_NETWORK, ESP_LOG_LEVEL_IAWARE_NETWORK);
    esp_log_level_set(IAWARE_CORE, ESP_LOG_LEVEL_IAWARE_CORE);
    esp_log_level_set(IAWARE_GPIO, ESP_LOG_LEVEL_IAWARE_GPIO);
    esp_log_level_set(IAWARE_BLE, ESP_LOG_LEVEL_IAWARE_BLE);


    // Initializes a non-volatile memory in flash memory, so it can be used by concurrent tasks
    esp_err_t err = nvs_flash_init();
    if ( (err == ESP_ERR_NVS_NO_FREE_PAGES) || (err == ESP_ERR_NVS_NEW_VERSION_FOUND) ) 
    {
        // NVS partition was truncated and needs to be erased
        // Retry nvs_flash_init

        ESP_ERROR_CHECK(nvs_flash_erase());
        
        if (nvs_flash_init() != ESP_OK)
        {
            ESP_LOGE(IAWARE_CORE, "Fail to nvs_flash_init().");

            deep_restart();
        }        
    }

    iaware_init();

    ESP_ERROR_CHECK(esp_event_loop_init(event_handler, NULL));
    
    start_dhcp_server();

    init_wifi_in_ap();    

    init_ble_server();
    // init_ble_client();
     
    // This task is not intended for OTA upload.
    xTaskCreatePinnedToCore(
        com_tcp_recv_task, // Function to implement the task
        "com_tcp_recv_task", // Name of the task
        2048, // Stack size in words (32 bits in esp32)
        (void *) event_group, // Task input parameter
        (configMAX_PRIORITIES - 1), // Priority of the task
        NULL, // Task handle.
        1); // Core where the task should run

    // The task of sending the samples uses the software timer provided by FreeRTOS. However, the callback of the timer runs on Core 0. I could not 
    // find a way to change to Core 1. Therefore, I will use vTaskDelay instead.
    // When esp32 starts, sampled input transfered via wifi is disabled. We need to explicitly send CMD_START_STREAM in com_tcp_recv_task() to 
    // enable the wifi transfer.
    xTaskCreatePinnedToCore(
        com_tcp_send_task, // Function to implement the task
        "com_tcp_send_task", // Name of the task
        2048, // Stack size in words (32 bits in esp32)
        (void *) event_group, // Task input parameter
        XTASK_LOW_PRIORITY, // Priority of the task
        NULL, // Task handle.
        1); // Core where the task should run

    // The task of sampling input data uses the hardware timer. Therefore, the callback of the hardware timer always runs in Core 0.
    init_sampling_data_task();
}


void deep_restart(void)
{
    esp_sleep_enable_timer_wakeup(SLEEP_TIME_MICROSEC);
    esp_deep_sleep_start();
}

void nvs_read_sampling_data_fs(void)
{
    ESP_LOGI(IAWARE_CORE, "Opening Non-Volatile Storage (NVS) handle for reading sampling_data_fs ...");

    nvs_handle my_handle;

    esp_err_t err = nvs_open("storage", NVS_READONLY, &my_handle);
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_CORE, "Error (%s) opening NVS handle!", esp_err_to_name(err));
    } 
    else 
    {
        ESP_LOGI(IAWARE_CORE, "Reading sampling_data_fs from the non-volatile storage ...");

        sampling_data_fs = SAMPLING_DATA_FS; // value will default to 0, if not set yet in NVS

        err = nvs_get_u32(my_handle, "fs", &sampling_data_fs);
        switch (err) 
        {
            case ESP_OK:
                ESP_LOGI(IAWARE_CORE, "Reading sampling_data_fs from the non-volatile storage SUCCESS and sampling_data_fs = %d Hz", sampling_data_fs);

                break;
            case ESP_ERR_NVS_NOT_FOUND:
                ESP_LOGW(IAWARE_CORE, "Not found sampling_data_fs in the non-volatile storage sampling_data_fs is set to %d Hz", sampling_data_fs);

                break;
            default :
                ESP_LOGE(IAWARE_CORE, "Reading sampling_data_fs from the non-volatile storage FAIL with Error (%s) and sampling_data_fs is set to %d Hz", esp_err_to_name(err), sampling_data_fs);

                break;
        }    

        // Close & free memory.
        nvs_close(my_handle);        
    }
}


int nvs_write_sampling_data_fs(uint32_t fs)
{
    int ret = iawTrue;

    ESP_LOGI(IAWARE_CORE, "Opening Non-Volatile Storage (NVS) handle for writing sampling_data_fs ...");

    nvs_handle my_handle;

    esp_err_t err = nvs_open("storage", NVS_READWRITE, &my_handle);
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_CORE, "Error (%s) opening NVS handle!", esp_err_to_name(err));

        ret = iawFalse;
    } 
    else 
    {
        ESP_LOGI(IAWARE_CORE, "Writting sampling_data_fs in the non-volatile storage to be %d Hz ...", fs);

        err = nvs_set_u32(my_handle, "fs", fs);
        switch (err) 
        {
            case ESP_OK:
                ESP_LOGI(IAWARE_CORE, "Writting sampling_data_fs in the non-volatile storage to be %d Hz SUCCESS.", fs);

                break;
            default :
                ESP_LOGE(IAWARE_CORE, "Writting sampling_data_fs in the non-volatile storage to be %d Hz FAIL with Error (%s).", fs, esp_err_to_name(err));

                ret = iawFalse;

                break;
        }    

        // Commit written value.
        // After setting any values, nvs_commit() must be called to ensure changes are written
        // to flash storage. Implementations may write to storage at other times,
        // but this is not guaranteed.
        ESP_LOGI(IAWARE_CORE, "Committing sampling_data_fs in the non-volatile storage to be %d Hz.", fs);        

        err = nvs_commit(my_handle);
        switch (err) 
        {
            case ESP_OK:
                ESP_LOGI(IAWARE_CORE, "Committing sampling_data_fs in the non-volatile storage to be %d Hz SUCCESS.", fs);

                break;
            default :
                ESP_LOGE(IAWARE_CORE, "Committing sampling_data_fs in the non-volatile storage to be %d Hz FAIL with Error (%s).", fs, esp_err_to_name(err));

                ret = iawFalse;

                break;
        }   

        // Close
        nvs_close(my_handle);        
    }

    return ret;
}


//////////////////// Private ////////////////////

static esp_err_t event_handler(void *ctx, system_event_t *event)
{
    switch(event->event_id) 
    {
        case SYSTEM_EVENT_AP_START:
            led_onboard_ap_start();

            ESP_LOGI(IAWARE_EVENT, "ESP32 started in AP mode.");

            xEventGroupSetBits(event_group, AP_IS_START_BIT);            
            
            break;

        case SYSTEM_EVENT_AP_STOP:
            led_onboard_ap_stop();
            
            ESP_LOGI(IAWARE_EVENT, "ESP32 stopped acting AP mode.");

            xEventGroupClearBits(event_group, AP_IS_START_BIT);            

            break;
            
        case SYSTEM_EVENT_AP_STACONNECTED:
            led_onboard_client_connected();
            
            ESP_LOGI(IAWARE_EVENT, "A client is connected.");

            xEventGroupSetBits(event_group, AP_IS_STACONNECTED_BIT);            

            break;

        case SYSTEM_EVENT_AP_STADISCONNECTED:
            // This happens when for example we disable wifi of the client.

            led_onboard_client_disconnected();

            ESP_LOGI(IAWARE_EVENT, "A client is disconnected.");

            close_cs();

            xEventGroupClearBits(event_group, AP_IS_STACONNECTED_BIT);

            break;      

        case SYSTEM_EVENT_AP_STAIPASSIGNED:

            ESP_LOGI(IAWARE_EVENT, "A client is assigned an IP address.");

            xEventGroupSetBits(event_group, AP_STAIPASSIGNED_BIT);

            break;  

        case SYSTEM_EVENT_AP_PROBEREQRECVED:

            ESP_LOGI(IAWARE_EVENT, "Recive a probe request from a client.");

            xEventGroupSetBits(event_group, AP_PROBEREQRECVED_BIT);

            break;              
            
        default:
            break;
    }

    return ESP_OK;
}

static void init_wifi_in_ap(void)
{
    wifi_init_config_t wifi_cfg = WIFI_INIT_CONFIG_DEFAULT();
 
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_cfg));
 
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
 
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));

    uint8_t mac[6];
    ESP_ERROR_CHECK(esp_read_mac(mac, ESP_MAC_WIFI_SOFTAP));    // Read Wifi's mac address that is not a constant depending on which wireless interfaces are enabled (Wifi, BLE, Ethernet).

    char ssid[32];
    getSSID(&(mac[0]), &(ssid[0])); // Get the SSID generated for our device.

    ESP_LOGI(IAWARE_NETWORK, "Name of AP is %s.", ssid);    

    wifi_config_t ap_config = {
          .ap = {
            .channel = 0,
            .authmode = WIFI_AUTH_OPEN,
            .ssid_hidden = 0,
            .max_connection = 1,
            .beacon_interval = 100
          }
        };

    strcpy((char *)ap_config.ap.ssid, (char *)ssid);

    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_config));

    ESP_ERROR_CHECK(esp_wifi_start());
}

static void start_dhcp_server(void)
{    
        // initialize the tcp stack
        tcpip_adapter_init();

        // stop DHCP server
        ESP_ERROR_CHECK(tcpip_adapter_dhcps_stop(TCPIP_ADAPTER_IF_AP));

        // assign a static IP to the network interface
        tcpip_adapter_ip_info_t info;
        memset(&info, 0, sizeof(info));
        IP4_ADDR(&info.ip, 192, 168, IP4_ADDR_2NUM, IP4_ADDR_3NUM);
        IP4_ADDR(&info.gw, 192, 168, IP4_ADDR_2NUM, IP4_ADDR_3NUM);//ESP acts as router, so gw addr will be its own addr
        IP4_ADDR(&info.netmask, 255, 255, 255, 0);
        ESP_ERROR_CHECK(tcpip_adapter_set_ip_info(TCPIP_ADAPTER_IF_AP, &info));

        // start the DHCP server   
        ESP_ERROR_CHECK(tcpip_adapter_dhcps_start(TCPIP_ADAPTER_IF_AP));

        ESP_LOGI(IAWARE_NETWORK, "DHCP server started.");
}

static void iaware_init(void)
{
    event_group = xEventGroupCreate(); 

    // NVS accessing.
    nvs_read_sampling_data_fs();
    nvs_write_sampling_data_fs(sampling_data_fs);

    // Initialize GPIOs.
    iaware_init_gpio();

    ESP_LOGI(IAWARE_CORE, "Done initializing.");
}