# Edit following two lines to set component requirements (see docs)
set(COMPONENT_REQUIRES )
set(COMPONENT_PRIV_REQUIRES )

set(COMPONENT_SRCS "main.c" "iaware_helper.c" "iaware_tcp_com.c" "iaware_sampling_data.c" "iaware_packet.c" "iaware_gpio.c" "iaware_ble_svr_com.c" "iaware_ble_clt_com.c")
set(COMPONENT_ADD_INCLUDEDIRS ".")

register_component()
