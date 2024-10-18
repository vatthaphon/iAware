#ifndef IAWARE_BLE_SVR_COM_H
#define IAWARE_BLE_SVR_COM_H

// #define IAWARE_BLE_SERVICE_UUID                     "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" // UART service UUID
// #define IAWARE_BLE_CHARACTERISTIC_UUID_RX           "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
// #define IAWARE_BLE_CHARACTERISTIC_UUID_TX           "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" // Normal Read

#define IAWARE_BLE_SERVICE_UUID                     "D0611E78-BBB4-4591-A5F8-487910AE4366" // UART service UUID
#define IAWARE_BLE_CHARACTERISTIC_UUID_RX           "D0611E79-BBB4-4591-A5F8-487910AE4366"
#define IAWARE_BLE_CHARACTERISTIC_UUID_TX           "D0611E7A-BBB4-4591-A5F8-487910AE4366" // Normal Read


#define SVR_PROFILE_NUM 1
#define PROFILE_A_APP_ID 0

#define GATTS_SERVICE_UUID_TEST_A   0x00FF
#define GATTS_CHAR_UUID_TEST_A      0xFF01
#define GATTS_DESCR_UUID_TEST_A     0x3333
#define GATTS_NUM_HANDLE_TEST_A     20 // The maximum number of handles associated with the service.

#define IAWARE_DEVICE_NAME            "i-Aware"
#define TEST_MANUFACTURER_DATA_LEN  17

#define GATTS_DEMO_CHAR_VAL_LEN_MAX 0x40

#define PREPARE_BUF_MAX_SIZE 1024

#define adv_config_flag      (1 << 0)
#define scan_rsp_config_flag (1 << 1)

#define BLE_NOTIFY_INTERVAL 1000 // [ms]

struct gatts_profile_inst {
    esp_gatts_cb_t          gatts_cb;
    uint16_t                gatts_if;
    uint16_t                app_id;
    uint16_t                conn_id;
    uint16_t                service_handle;
    esp_gatt_srvc_id_t      service_id;
    uint16_t                char_handle;
    esp_gatt_perm_t         perm;
    esp_gatt_char_prop_t    property;
    uint16_t                descr_handle;

    esp_bt_uuid_t           char_uuid;    
    esp_bt_uuid_t           descr_uuid;

    esp_bt_uuid_t           RX_char_uuid;
    esp_bt_uuid_t           RX_descr_uuid;

    esp_bt_uuid_t           TX_char_uuid;
    esp_bt_uuid_t           TX_descr_uuid;

};

struct prepare_type_env {
    uint8_t                 *prepare_buf;
    int                     prepare_len;
};

int init_ble_server(void);

#endif