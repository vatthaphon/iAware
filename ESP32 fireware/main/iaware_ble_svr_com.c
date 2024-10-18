/*
    GAP (Generic Access Profile), https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gap
    GATT (Generic Attribute Profile), https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gatt
    
    How bluetooth works?
    1. A device will set a specific advertising interval, and every time this interval passes, it will retransmit it's main advertising packet.
    2. If a listening (central) device is interested in the scan response payload (and it is available on the device) 
        it can optionally request the scan response payload, and the device will respond with the scan response data one time after the scan response
        payload request afterwhich the device sends the Advertising Data payload as usual.
    3. We can see that if we just want to send out a small amout of data (less than 31 bytes) to many central devices. We can just use the "Advertising data" payload
        or the scan response payload as a mean to publich those data. This is known as Broadcasting in Bluetooth Low Energy. This is one-way communication.
    4. Once a connection between the device and the central is established. The device will stop advertising and two-way communications via GATT will
        take place.
    5. When establishing a connection, the device will suggest a 'Connection Interval' to the central device, and the central device will try to 
        reconnect every connection interval to see if any new data is available, etc. With these roles, the device behaves as GATT server and 
        the central behaves as GATT client. It's important to keep in mind that this connection interval is really just a suggestion, though! 
        Your central device may not be able to honour the request because it's busy talking to another device or the required system resources just aren't available.
    6. GATT transactions are based on objects called Profiles, of which each contains Services, of which each contains Characteristics. For example,
        An Heart Rate Profile contains the Heart Rate Service and the Device Information Service. Official Profiles are published in https://www.bluetooth.com/specifications/gatt/
        Services are used to break data up into logic entities. Each service will have an UUID that can be either 16-bit (for officially adopted BLE 
        Services https://www.bluetooth.com/specifications/gatt/services/) or 128-bit (for custom services). Characteristics encapsulates a single data point
        (though it may contain an array of related data, such as X/Y/Z values from a 3-axis accelerometer, etc.).
        Each Characteristic distinguishes itself via a pre-defined 16-bit (https://www.bluetooth.com/specifications/gatt/characteristics/) or 128-bit UUID.
        Each characteristic is composed of Attributes.
    7. A BLE packet equals |1 byte of Preamble|4 bytes of Access Address|2 bytes of LL Header|0-255 bytes of Data|3 bytes of CRC|. The size of Data
        depends on the Bluetooth specification, e.g. in Bluetooth v4.0 and 4.1, the maximum size of the Data is 27 bytes. In the Data field,
        it equals |4 bytes of L2CAP Header|0-251 bytes of ATT Data|. Because we have 4 bytes of L2CAP Header, we can trasfer ATT Data with the length
        up to 2^32 - 1. The length of the ATT Data in one BLE packet is called ATT MTU (maximum transfer unit), which has a unit of bytes. The 
        ATT Data is composed of |1 byte for op-code|0 - (ATT MTU - 1) for Actual Data|. The 1-byte op-code represents Write Command, Notification, Read Response, etc. 
        For each command, additional bytes may be required and they will be stored in the Actual Data. For different standards, the ATT Data can be
        1500 bytes for Ethernet IEEE 802.3/802.2, 1492 bytes for X.25, 576 bytes for BLE, 23 bytes for BLE4.0/4.1, and 251 bytes for BLE4.2.

*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_bt.h"

#include "esp_gap_ble_api.h"
#include "esp_gatts_api.h"
#include "esp_bt_defs.h"
#include "esp_bt_main.h"
#include "esp_gatt_common_api.h"

#include "iaware_ble_svr_com.h"
#include "iaware_helper.h"
#include "main.h"

static uint8_t char1_str[] = {0x11,0x22,0x44};
static esp_gatt_char_prop_t a_property = 0;
static esp_gatt_perm_t a_permission = 0;

static esp_gatt_char_prop_t TX_a_property = 0;
static esp_gatt_perm_t TX_a_permission = 0;

static esp_gatt_char_prop_t RX_a_property = 0;
static esp_gatt_perm_t RX_a_permission = 0;


static esp_gatts_cb_event_t notify_event;
static esp_gatt_if_t notify_gatts_if;
static esp_ble_gatts_cb_param_t *notify_param;
static xTimerHandle notify_timerHandle;

static esp_attr_value_t gatts_demo_char1_val =
{
    .attr_max_len = GATTS_DEMO_CHAR_VAL_LEN_MAX,
    .attr_len     = sizeof(char1_str),
    .attr_value   = char1_str,
};

static uint8_t adv_config_done = 0;

#ifdef CONFIG_SET_RAW_ADV_DATA
    static uint8_t raw_adv_data[] = {
            0x02, 0x01, 0x06,
            0x02, 0x0a, 0xeb, 0x03, 0x03, 0xab, 0xcd
    };
    static uint8_t raw_scan_rsp_data[] = {
            0x0f, 0x09, 0x45, 0x53, 0x50, 0x5f, 0x47, 0x41, 0x54, 0x54, 0x53, 0x5f, 0x44,
            0x45, 0x4d, 0x4f
    };
#else
    static uint8_t adv_service_uuid128[32] = {
        /* LSB <--------------------------------------------------------------------------------> MSB */
        //first uuid, 16bit, [12],[13] is the value
        0xfb, 0x34, 0x9b, 0x5f, 0x80, 0x00, 0x00, 0x80, 0x00, 0x10, 0x00, 0x00, 0xEE, 0x00, 0x00, 0x00,
        //second uuid, 32bit, [12], [13], [14], [15] is the value
        0xfb, 0x34, 0x9b, 0x5f, 0x80, 0x00, 0x00, 0x80, 0x00, 0x10, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    };

    // The length of adv data must be less than 31 bytes
    //static uint8_t test_manufacturer[TEST_MANUFACTURER_DATA_LEN] =  {0x12, 0x23, 0x45, 0x56};
    //adv data
    static esp_ble_adv_data_t adv_data = {
        .set_scan_rsp = false,
        .include_name = true,
        .include_txpower = true,
        .min_interval = 0x0006, //slave connection min interval, Time = min_interval * 1.25 msec
        .max_interval = 0x0010, //slave connection max interval, Time = max_interval * 1.25 msec
        .appearance = 0x00,
        .manufacturer_len = 0, //TEST_MANUFACTURER_DATA_LEN,
        .p_manufacturer_data =  NULL, //&test_manufacturer[0],
        .service_data_len = 0,
        .p_service_data = NULL,
        .service_uuid_len = sizeof(adv_service_uuid128),
        .p_service_uuid = adv_service_uuid128,
        .flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT),
    };
    // scan response data
    static esp_ble_adv_data_t scan_rsp_data = {
        .set_scan_rsp = true,
        .include_name = true,
        .include_txpower = true,
        .min_interval = 0x0006,
        .max_interval = 0x0010,
        .appearance = 0x00,
        .manufacturer_len = 0, //TEST_MANUFACTURER_DATA_LEN,
        .p_manufacturer_data =  NULL, //&test_manufacturer[0],
        .service_data_len = 0,
        .p_service_data = NULL,
        .service_uuid_len = sizeof(adv_service_uuid128),
        .p_service_uuid = adv_service_uuid128,
        .flag = (ESP_BLE_ADV_FLAG_GEN_DISC | ESP_BLE_ADV_FLAG_BREDR_NOT_SPT),
    };
#endif

// adv_params is for the "Advertising Data" and "Scan Response" payload.
static esp_ble_adv_params_t adv_params = {
    .adv_int_min        = 0x0020, // [uint16_t], 0xffff, Minimum advertising interval for undirected and low duty cycle directed advertising. Range: 0x0020 to 0x4000 Default: N = 0x0800 (1.28 second) Time = N * 0.625 msec Time Range: 20 ms to 10.24 sec 
    .adv_int_max        = 0x0040, // [uint16_t], 0xffff, Maximum advertising interval for undirected and low duty cycle directed advertising. Range: 0x0020 to 0x4000 Default: N = 0x0800 (1.28 second) Time = N * 0.625 msec Time Range: 20 ms to 10.24 sec Advertising max interval 
    .adv_type           = ADV_TYPE_IND, // Advertising type
    .own_addr_type      = BLE_ADDR_TYPE_PUBLIC, // Owner bluetooth device address type.
    //.peer_addr            = // Peer device bluetooth device address.
    //.peer_addr_type       = // Peer device bluetooth device address type, only support public address type and random address type.
    .channel_map        = ADV_CHNL_ALL, // Advertising channel map.
    .adv_filter_policy  = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY, // Advertising filter policy. ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY = Allow both scan and connection requests from anyone.
};

typedef struct prepare_type_env prepare_type_env_t;

static prepare_type_env_t a_prepare_write_env;

static void vTimerCallbackNotifyExpired(xTimerHandle pxTimer);
static void exec_write_event_env(prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param);
static void write_event_env(esp_gatt_if_t gatts_if, prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param);
static void gatts_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param);
static void gap_event_handler(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param);
static void gatts_profile_a_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param);

/* One gatt-based profile one app_id and one gatts_if, this array will store the gatts_if returned by ESP_GATTS_REG_EVT */
static struct gatts_profile_inst gl_profile_tab[SVR_PROFILE_NUM] = {
    [PROFILE_A_APP_ID] = {
        .gatts_cb = gatts_profile_a_event_handler,
        .gatts_if = ESP_GATT_IF_NONE,       /* Not get the gatt_if, so initial is ESP_GATT_IF_NONE */
    },
};

////////// Public //////////
int init_ble_server(void)
{
    esp_err_t err;

    ESP_ERROR_CHECK(esp_bt_controller_mem_release(ESP_BT_MODE_CLASSIC_BT));

    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    err = esp_bt_controller_init(&bt_cfg);
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_BLE, "%s initialize controller failed: %s", __func__, err_to_str(err));
        return -1;
    }    

    err = esp_bt_controller_enable(ESP_BT_MODE_BLE);
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_BLE, "%s enable controller failed: %s", __func__, err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

    err = esp_bluedroid_init();
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_BLE, "%s init bluetooth failed: %s", __func__, err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

    err = esp_bluedroid_enable();
    if (err != ESP_OK) 
    {
        ESP_LOGE(IAWARE_BLE, "%s enable bluetooth failed: %s", __func__, err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

    // Controls connections and advertising in Bluetooth. 
    // GAP is what makes my device visible to the outside world, and determines how two devices can (or can't) interact with each other.
    // The process of making my device visible is called Advertising that has two ways "Advertising Data" payload and "Scan Response" payload.
    // Each payload allows to send out as many as 31 bytes of data. The "Advertising Data" payload is mandatory because it will be constantly 
    // transmitted out from the device to let central devices in range know that it exists. And stop advertising when the device connects the central device.
    // The "Scan Response" payload is an optional secondary payload that central devices can request, and allows device designers to fit 
    // a bit more information in the "Advertising Data" payload such a strings for a device name, etc. 
    err = esp_ble_gap_register_callback(gap_event_handler);
    if (err != ESP_OK)
    {
        ESP_LOGE(IAWARE_BLE, "gap register error: %s", err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }    

    // Register application callbacks with BTA GATTS module.
    err = esp_ble_gatts_register_callback(gatts_event_handler);
    if (err != ESP_OK)
    {
        ESP_LOGE(IAWARE_BLE, "gatts register error: %s", err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

    // Register application identifier.
    err = esp_ble_gatts_app_register(PROFILE_A_APP_ID);
    if (err != ESP_OK)
    {
        ESP_LOGE(IAWARE_BLE, "gatts app register error: %s", err_to_str(err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

    // Set the maximum length of an ATT packet (MTU is Maximum Transmission Unit in bytes). 251 (for BLE4.2)
    esp_err_t local_mtu_err = esp_ble_gatt_set_local_mtu(500);
    if (local_mtu_err != ESP_OK)
    {
        ESP_LOGE(IAWARE_BLE, "set local  MTU failed: %s", err_to_str(local_mtu_err));

        if (esp_bt_controller_deinit() != ESP_OK) 
            ESP_LOGE(IAWARE_BLE, "esp_bt_controller_deinit: %s", err_to_str(err));

        return -1;
    }

#ifdef CONFIG_SET_RAW_ADV_DATA
    ESP_LOGI(IAWARE_BLE, "CONFIG_SET_RAW_ADV_DATA is defined");
#else
    ESP_LOGI(IAWARE_BLE, "CONFIG_SET_RAW_ADV_DATA is NOT defined");
#endif    

    notify_timerHandle = xTimerCreate("notify_timerHandle", /* name */
                                      pdMS_TO_TICKS(BLE_NOTIFY_INTERVAL), // [ms]
                                      pdTRUE, /* auto reload */
                                      (void*)0, /* timer ID */
                                      vTimerCallbackNotifyExpired); /* callback */

    return 0;
}

////////// Private //////////
static void vTimerCallbackNotifyExpired(xTimerHandle pxTimer) 
{    
    uint8_t notify_data[15];
    for (int i = 0; i < sizeof(notify_data); ++i)
    {
        // notify_data[i] = i%0xff;
        notify_data[i] = 0x21;
    }


    //the size of notify_data[] need less than MTU size
    esp_ble_gatts_send_indicate(notify_gatts_if, notify_param->write.conn_id, gl_profile_tab[PROFILE_A_APP_ID].char_handle, sizeof(notify_data), notify_data, false);    
}

static void exec_write_event_env(prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param)
{
    if (param->exec_write.exec_write_flag == ESP_GATT_PREP_WRITE_EXEC)
    {
        esp_log_buffer_hex(IAWARE_BLE, prepare_write_env->prepare_buf, prepare_write_env->prepare_len);
    }
    else
    {
        ESP_LOGI(IAWARE_BLE,"ESP_GATT_PREP_WRITE_CANCEL");
    }

    if (prepare_write_env->prepare_buf) 
    {
        free(prepare_write_env->prepare_buf);
        prepare_write_env->prepare_buf = NULL;
    }

    prepare_write_env->prepare_len = 0;
}

static void write_event_env(esp_gatt_if_t gatts_if, prepare_type_env_t *prepare_write_env, esp_ble_gatts_cb_param_t *param)
{
    esp_gatt_status_t status = ESP_GATT_OK;

    if (param->write.need_rsp)
    {
        if (param->write.is_prep)
        {
            if (prepare_write_env->prepare_buf == NULL) 
            {
                prepare_write_env->prepare_buf = (uint8_t *)malloc(PREPARE_BUF_MAX_SIZE*sizeof(uint8_t));
                prepare_write_env->prepare_len = 0;
                if (prepare_write_env->prepare_buf == NULL) 
                {
                    ESP_LOGE(IAWARE_BLE, "Gatt_server prep no mem");

                    status = ESP_GATT_NO_RESOURCES;
                }
            } 
            else 
            {
                if(param->write.offset > PREPARE_BUF_MAX_SIZE) 
                {
                    status = ESP_GATT_INVALID_OFFSET;
                } 
                else if ((param->write.offset + param->write.len) > PREPARE_BUF_MAX_SIZE) 
                {
                    status = ESP_GATT_INVALID_ATTR_LEN;
                }
            }

            esp_gatt_rsp_t *gatt_rsp = (esp_gatt_rsp_t *)malloc(sizeof(esp_gatt_rsp_t));
            gatt_rsp->attr_value.len = param->write.len;
            gatt_rsp->attr_value.handle = param->write.handle;
            gatt_rsp->attr_value.offset = param->write.offset;
            gatt_rsp->attr_value.auth_req = ESP_GATT_AUTH_REQ_NONE;
            memcpy(gatt_rsp->attr_value.value, param->write.value, param->write.len);

            esp_err_t response_err = esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, status, gatt_rsp);
            if (response_err != ESP_OK)
            {
               ESP_LOGE(IAWARE_BLE, "Send response error");
            }

            free(gatt_rsp);
            
            if (status != ESP_GATT_OK)
            {
                return;
            }
            memcpy(prepare_write_env->prepare_buf + param->write.offset, param->write.value, param->write.len);

            prepare_write_env->prepare_len += param->write.len;

        }
        else
        {
            esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, status, NULL);
        }
    }
}

static void gap_event_handler(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param)
{
    switch (event) 
    {
#ifdef CONFIG_SET_RAW_ADV_DATA
        case ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT: // When raw advertising data set complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_ADV_DATA_RAW_SET_COMPLETE_EVT");

            adv_config_done &= (~adv_config_flag);
            if (adv_config_done == 0)
            {
                esp_ble_gap_start_advertising(&adv_params);
            }

            break;

        case ESP_GAP_BLE_SCAN_RSP_DATA_RAW_SET_COMPLETE_EVT: // When raw advertising data set complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_SCAN_RSP_DATA_RAW_SET_COMPLETE_EVT");

            adv_config_done &= (~scan_rsp_config_flag);
            if (adv_config_done == 0)
            {
                esp_ble_gap_start_advertising(&adv_params);
            }

            break;
#else
        case ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT: // When advertising data set complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_ADV_DATA_SET_COMPLETE_EVT");

            adv_config_done &= (~adv_config_flag);
            if (adv_config_done == 0)
            {
                esp_ble_gap_start_advertising(&adv_params);
            }

            break;

        case ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT: // When scan response data set complete, the event comes.                    
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_SCAN_RSP_DATA_SET_COMPLETE_EVT");

            adv_config_done &= (~scan_rsp_config_flag);
            if (adv_config_done == 0)
            {
                esp_ble_gap_start_advertising(&adv_params);
            }

            break;
#endif
        case ESP_GAP_BLE_ADV_START_COMPLETE_EVT: // When starting advertising complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_ADV_START_COMPLETE_EVT");

            //advertising start complete event to indicate advertising start successfully or failed
            if (param->adv_start_cmpl.status != ESP_BT_STATUS_SUCCESS) 
            {
                ESP_LOGE(IAWARE_BLE, "gap_event_handler: Advertising start failed");
            }

            break;

        case ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT: // When stopping adv complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_ADV_STOP_COMPLETE_EVT");

            if (param->adv_stop_cmpl.status != ESP_BT_STATUS_SUCCESS) 
            {
                ESP_LOGE(IAWARE_BLE, "Advertising stop failed");
            } 
            else 
            {
                ESP_LOGI(IAWARE_BLE, "Stop adv successfully");
            }

            break;

        case ESP_GAP_BLE_UPDATE_CONN_PARAMS_EVT: // When updating connection parameters complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: ESP_GAP_BLE_UPDATE_CONN_PARAMS_EVT");

            ESP_LOGI(IAWARE_BLE, "update connection params status = %d, min_int = %d, max_int = %d,conn_int = %d,latency = %d, timeout = %d",
                      param->update_conn_params.status,
                      param->update_conn_params.min_int,
                      param->update_conn_params.max_int,
                      param->update_conn_params.conn_int,
                      param->update_conn_params.latency,
                      param->update_conn_params.timeout);
             
            break;

        default:
            ESP_LOGI(IAWARE_BLE, "gap_event_handler: default");

            break;
    }
}

// static void str_to_uuid128(struct gatts_profile_inst *ptr, char uuid128_str[])
static void str_to_uuid128(uint8_t uuid128[], char uuid128_str[])
// Params:
//     uuid128_str  : It is a string, of which length is 36 (including '-')
{
    printf("%s\n", uuid128_str);
    int n = 0;
    for (int i = 0; i < 36;)
    {
        if (uuid128_str[i] == '-')
            i++;

        uint8_t MSB = uuid128_str[i];
        uint8_t LSB = uuid128_str[i + 1];

        if (MSB > '9') 
            MSB -= 7; 

        if (LSB > '9') 
            LSB -= 7;

        // ptr->service_id.id.uuid.uuid.uuid128[15 - n++] = ( (MSB&0x0F) << 4 ) | (LSB & 0x0F);
        uuid128[15 - n++] = ( (MSB&0x0F) << 4 ) | (LSB & 0x0F);
        i+=2;   
    }

    for (int i = 0; i < 16; i++)
    {
        printf("%d", uuid128[i]);
    }
    printf("\n");
}



static void gatts_profile_a_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param) 
// Params:
//      esp_gatts_cb_event_t    : GATT Server callback function events. 
//      esp_gatt_if_t   : Gatt interface type, different application on GATT client use different gatt_if 
//      esp_ble_gatts_cb_param_t    : Gatt server callback parameters union.
{
    switch (event) 
    {
        case ESP_GATTS_REG_EVT: // When register application id, the event comes.
            ESP_LOGI(IAWARE_BLE, "A: REGISTER_APP_EVT, status %d, app_id %d", param->reg.status, param->reg.app_id);

            gl_profile_tab[PROFILE_A_APP_ID].service_id.is_primary = true;
            gl_profile_tab[PROFILE_A_APP_ID].service_id.id.inst_id = 0x00;

            gl_profile_tab[PROFILE_A_APP_ID].service_id.id.uuid.len = ESP_UUID_LEN_128;                        
            str_to_uuid128(gl_profile_tab[PROFILE_A_APP_ID].service_id.id.uuid.uuid.uuid128, IAWARE_BLE_SERVICE_UUID);

            esp_err_t set_dev_name_ret = esp_ble_gap_set_device_name(IAWARE_DEVICE_NAME);
            if (set_dev_name_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: set device name failed, error code = %x", set_dev_name_ret);
            }

#ifdef CONFIG_SET_RAW_ADV_DATA
            esp_err_t raw_adv_ret = esp_ble_gap_config_adv_data_raw(raw_adv_data, sizeof(raw_adv_data));
            if (raw_adv_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: config raw adv data failed, error code = %x ", raw_adv_ret);
            }

            adv_config_done |= adv_config_flag;

            esp_err_t raw_scan_ret = esp_ble_gap_config_scan_rsp_data_raw(raw_scan_rsp_data, sizeof(raw_scan_rsp_data));
            if (raw_scan_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: config raw scan rsp data failed, error code = %x", raw_scan_ret);
            }

            adv_config_done |= scan_rsp_config_flag;
#else
            //config adv data
            esp_err_t ret = esp_ble_gap_config_adv_data(&adv_data);
            if (ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: config adv data failed, error code = %x", ret);
            }

            adv_config_done |= adv_config_flag;
            //config scan response data
            ret = esp_ble_gap_config_adv_data(&scan_rsp_data);
            if (ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: config scan response data failed, error code = %x", ret);
            }

            adv_config_done |= scan_rsp_config_flag;

#endif
            // Create a service. number of handle requested for this service.
            esp_ble_gatts_create_service(gatts_if, &gl_profile_tab[PROFILE_A_APP_ID].service_id, GATTS_NUM_HANDLE_TEST_A);

            break;

        case ESP_GATTS_CREATE_EVT: // When create service complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CREATE_EVT, status %d,  service_handle %d", param->create.status, param->create.service_handle);

            // When we success in creating the service, we then create characteristics.
            gl_profile_tab[PROFILE_A_APP_ID].service_handle = param->create.service_handle;

            // Add a characteristic of RX
            gl_profile_tab[PROFILE_A_APP_ID].RX_char_uuid.len = ESP_UUID_LEN_128;
            str_to_uuid128(gl_profile_tab[PROFILE_A_APP_ID].RX_char_uuid.uuid.uuid128, IAWARE_BLE_CHARACTERISTIC_UUID_RX);            

            // Add a characteristic of TX
            gl_profile_tab[PROFILE_A_APP_ID].TX_char_uuid.len = ESP_UUID_LEN_128;
            str_to_uuid128(gl_profile_tab[PROFILE_A_APP_ID].TX_char_uuid.uuid.uuid128, IAWARE_BLE_CHARACTERISTIC_UUID_TX);            
            
            // This function is called to start a service.
            esp_ble_gatts_start_service(gl_profile_tab[PROFILE_A_APP_ID].service_handle);

            esp_err_t add_char_ret;

            RX_a_property = ESP_GATT_CHAR_PROP_BIT_WRITE;
            RX_a_permission = ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE;

            add_char_ret = esp_ble_gatts_add_char(gl_profile_tab[PROFILE_A_APP_ID].service_handle, 
                                                    &gl_profile_tab[PROFILE_A_APP_ID].RX_char_uuid, 
                                                    RX_a_permission, 
                                                    RX_a_property, 
                                                    &gatts_demo_char1_val, 
                                                    NULL);
            if (add_char_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: add char failed, error code =%x",add_char_ret);
            }

            TX_a_property = ESP_GATT_CHAR_PROP_BIT_READ | ESP_GATT_CHAR_PROP_BIT_NOTIFY;
            TX_a_permission = ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE;

            add_char_ret = esp_ble_gatts_add_char(gl_profile_tab[PROFILE_A_APP_ID].service_handle, 
                                                    &gl_profile_tab[PROFILE_A_APP_ID].TX_char_uuid, 
                                                    TX_a_permission, 
                                                    TX_a_property, 
                                                    &gatts_demo_char1_val, 
                                                    NULL);
            if (add_char_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: add char failed, error code =%x",add_char_ret);
            }            


            break;

        case ESP_GATTS_ADD_CHAR_EVT: // When add characteristic complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_ADD_CHAR_EVT, status %d,  attr_handle %d, service_handle %d", param->add_char.status, param->add_char.attr_handle, param->add_char.service_handle);

            for (int i = 0; i < 16; i++)
            {
                printf("%d", param->add_char.char_uuid.uuid.uuid128[i]);
            }
            printf("\n");            

            uint16_t length = 0;
            const uint8_t *prf_char;
            
            gl_profile_tab[PROFILE_A_APP_ID].char_handle = param->add_char.attr_handle;
            gl_profile_tab[PROFILE_A_APP_ID].TX_descr_uuid.len = ESP_UUID_LEN_16;
            gl_profile_tab[PROFILE_A_APP_ID].TX_descr_uuid.uuid.uuid16 = ESP_GATT_UUID_CHAR_CLIENT_CONFIG;

            

            esp_err_t get_attr_ret = esp_ble_gatts_get_attr_value(param->add_char.attr_handle, &length, &prf_char);
            if (get_attr_ret == ESP_FAIL)
            {
                ESP_LOGE(IAWARE_BLE, "A: ILLEGAL HANDLE");
            }

            ESP_LOGI(IAWARE_BLE, "A: the gatts demo char length = %x", length);

            for(int i = 0; i < length; i++)
            {
                ESP_LOGI(IAWARE_BLE, "A: prf_char[%x] =%x",i,prf_char[i]);
            }

            esp_err_t add_descr_ret = esp_ble_gatts_add_char_descr(gl_profile_tab[PROFILE_A_APP_ID].service_handle, // service handle to which this characteristic descriptor is to be added.
                                                                    &gl_profile_tab[PROFILE_A_APP_ID].TX_descr_uuid, // descriptor UUID.
                                                                    ESP_GATT_PERM_READ | ESP_GATT_PERM_WRITE, // descriptor access permission.
                                                                    NULL, // Characteristic descriptor value 
                                                                    NULL); // attribute response control byte 


            if (add_descr_ret)
            {
                ESP_LOGE(IAWARE_BLE, "A: add char descr failed, error code =%x", add_descr_ret);
            }

            break;
        
        case ESP_GATTS_ADD_CHAR_DESCR_EVT: // When add descriptor complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_ADD_CHAR_DESCR_EVT, status %d, attr_handle %d, service_handle %d", param->add_char_descr.status, param->add_char_descr.attr_handle, param->add_char_descr.service_handle);

            break;



        case ESP_GATTS_READ_EVT: // This is where we send data back to the central server.
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_READ_EVT, conn_id %d, trans_id %d, handle %d", param->read.conn_id, param->read.trans_id, param->read.handle);

            esp_gatt_rsp_t rsp;
            memset(&rsp, 0, sizeof(esp_gatt_rsp_t));
            rsp.attr_value.handle = param->read.handle;
            rsp.attr_value.len = 4;
            rsp.attr_value.value[0] = 0xde;
            rsp.attr_value.value[1] = 0xed;
            rsp.attr_value.value[2] = 0xbe;
            rsp.attr_value.value[3] = 0xef;
            esp_ble_gatts_send_response(gatts_if, param->read.conn_id, param->read.trans_id, ESP_GATT_OK, &rsp); // This function is called to send a response to a request.

            break;
        
        case ESP_GATTS_WRITE_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_WRITE_EVT, conn_id %d, trans_id %d, handle %d", param->write.conn_id, param->write.trans_id, param->write.handle);

            if (!param->write.is_prep) //  If the write is a long write, then (param->write.is_prep) will be set, if it is a short write then (param->write.is_prep) will not be set. 
            // when short write occurs, i.e. the size of the payload is less than MTU-3, where MTU is usually 23 bytes.
            {
                ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_WRITE_EVT, value len %d", param->write.len);

                // Log a buffer of hex bytes at Info level. 
                esp_log_buffer_hex(IAWARE_BLE, param->write.value, param->write.len);

                // printf("%d\n", param->write.handle);
                // printf("%d\n", gl_profile_tab[PROFILE_A_APP_ID].descr_handle);
                // if ( (gl_profile_tab[PROFILE_A_APP_ID].descr_handle == param->write.handle) && (param->write.len == 2) )
                {
                    uint16_t descr_value = param->write.value[1]<<8 | param->write.value[0];
                    if (descr_value == 0x0001)
                    {
                        // if (a_property & ESP_GATT_CHAR_PROP_BIT_NOTIFY)
                        {
                            ESP_LOGI(IAWARE_BLE, "A: notify enable");

                            notify_event = event;
                            notify_gatts_if = gatts_if;
                            notify_param = param;

                            if (xTimerStart(notify_timerHandle, 0) != pdPASS) 
                            {
                                ESP_LOGE(IAWARE_BLE, "A: ESP_GATTS_WRITE_EVT, Fail to start notification timer");
                            }                            
                        }
                    }
                    else if (descr_value == 0x0002)
                    {
                        // if (a_property & ESP_GATT_CHAR_PROP_BIT_INDICATE)
                        {
                            ESP_LOGI(IAWARE_BLE, "A: indicate enable");

                            uint8_t indicate_data[15];
                            for (int i = 0; i < sizeof(indicate_data); ++i)
                            {
                                indicate_data[i] = i%0xff;
                            }
                            //the size of indicate_data[] need less than MTU size
                            esp_ble_gatts_send_indicate(gatts_if, param->write.conn_id, gl_profile_tab[PROFILE_A_APP_ID].char_handle, sizeof(indicate_data), indicate_data, true);
                        }
                    }                    
                    else if (descr_value == 0x0000)
                    {
                        ESP_LOGI(IAWARE_BLE, "A: notify/indicate disable ");

                        if (xTimerStop(notify_timerHandle, 0) != pdPASS) 
                        {
                            ESP_LOGE(IAWARE_BLE, "A: ESP_GATTS_WRITE_EVT, Fail to stop notification timer");
                        }                        
                    }
                    else
                    {
                        ESP_LOGE(IAWARE_BLE, "A: unknown descr value");

                        esp_log_buffer_hex(IAWARE_BLE, param->write.value, param->write.len);
                    }
                }
            }

            write_event_env(gatts_if, &a_prepare_write_env, param);

            break;
        
        case ESP_GATTS_EXEC_WRITE_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_EXEC_WRITE_EVT");

            esp_ble_gatts_send_response(gatts_if, param->write.conn_id, param->write.trans_id, ESP_GATT_OK, NULL);

            exec_write_event_env(&a_prepare_write_env, param);

            break;

        case ESP_GATTS_MTU_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_MTU_EVT, MTU %d", param->mtu.mtu);

            break;

        case ESP_GATTS_UNREG_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_UNREG_EVT not implement");            

            break;


        case ESP_GATTS_ADD_INCL_SRVC_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_ADD_INCL_SRVC_EVT not implement");            

            break;


        case ESP_GATTS_DELETE_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_DELETE_EVT not implement");            

            break;

        case ESP_GATTS_START_EVT: // When start service complete, the event comes.
            ESP_LOGI(IAWARE_BLE, "A: SERVICE_START_EVT, status %d, service_handle %d", param->start.status, param->start.service_handle);

            break;

        case ESP_GATTS_STOP_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_STOP_EVT not implement");            

            break;

        case ESP_GATTS_CONNECT_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CONNECT_EVT");

            esp_ble_conn_update_params_t conn_params = {0};
            memcpy(conn_params.bda, param->connect.remote_bda, sizeof(esp_bd_addr_t));

            /* For the IOS system, please reference the apple official documents about the ble connection parameters restrictions. */
            conn_params.latency = 0;
            conn_params.min_int = 0x10;    // min_int = 0x10*1.25ms = 20ms            
            conn_params.max_int = 0x20;    // max_int = 0x20*1.25ms = 40ms
            conn_params.timeout = 400;    // timeout = 400*10ms = 4000ms
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CONNECT_EVT, conn_id %d, remote %02x:%02x:%02x:%02x:%02x:%02x:",
                     param->connect.conn_id,
                     param->connect.remote_bda[0], param->connect.remote_bda[1], param->connect.remote_bda[2],
                     param->connect.remote_bda[3], param->connect.remote_bda[4], param->connect.remote_bda[5]);

            gl_profile_tab[PROFILE_A_APP_ID].conn_id = param->connect.conn_id;

            //start sent the update connection parameters to the peer device.
            esp_ble_gap_update_conn_params(&conn_params);

            break;
        
        case ESP_GATTS_DISCONNECT_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_DISCONNECT_EVT, disconnect reason 0x%x", param->disconnect.reason);

            esp_ble_gap_start_advertising(&adv_params);
            
            break;

        case ESP_GATTS_CONF_EVT: // When receive confirm, the event comes
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CONF_EVT, status %d attr_handle %d", param->conf.status, param->conf.handle);

            if (param->conf.status != ESP_GATT_OK)
            {
                ESP_LOGE(IAWARE_BLE, "A: param->conf.status != ESP_GATT_OK, status %d attr_handle %d", param->conf.status, param->conf.handle);

                esp_log_buffer_hex(IAWARE_BLE, param->conf.value, param->conf.len);
            }

            break;

        case ESP_GATTS_OPEN_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_OPEN_EVT not implement");

            break;

        case ESP_GATTS_CANCEL_OPEN_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CANCEL_OPEN_EVT not implement");

            break;

        case ESP_GATTS_CLOSE_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CLOSE_EVT not implement");

            break;

        case ESP_GATTS_LISTEN_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_LISTEN_EVT not implement");

            break;

        case ESP_GATTS_CONGEST_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_CONGEST_EVT not implement");

            break;

        case ESP_GATTS_RESPONSE_EVT:
            ESP_LOGI(IAWARE_BLE, "A: ESP_GATTS_RESPONSE_EVT not implement");

            break;

        default:
            ESP_LOGI(IAWARE_BLE, "A: default %d", event);

            break;
    }
}

static void gatts_event_handler(esp_gatts_cb_event_t event, esp_gatt_if_t gatts_if, esp_ble_gatts_cb_param_t *param)
{
    /* If event is register event, store the gatts_if for each profile */
    if (event == ESP_GATTS_REG_EVT) 
    {
        if (param->reg.status == ESP_GATT_OK) 
        {
            gl_profile_tab[param->reg.app_id].gatts_if = gatts_if;
        } 
        else 
        {
            ESP_LOGI(IAWARE_BLE, "Reg app failed, app_id %04x, status %d",
                    param->reg.app_id,
                    param->reg.status);
            return;
        }
    }

    /* If the gatts_if equal to profile A, call profile A cb handler,
     * so here call each profile's callback */
    do 
    {
        int idx;
        for (idx = 0; idx < SVR_PROFILE_NUM; idx++) 
        {
            if (gatts_if == ESP_GATT_IF_NONE || /* ESP_GATT_IF_NONE, not specify a certain gatt_if, need to call every profile cb function */
                    gatts_if == gl_profile_tab[idx].gatts_if) 
            {
                if (gl_profile_tab[idx].gatts_cb) 
                {
                    gl_profile_tab[idx].gatts_cb(event, gatts_if, param);
                }
            }
        }
    } while (0);
}