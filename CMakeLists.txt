cmake_minimum_required(VERSION 3.16)
project(hiri_firmware C CXX)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Feature Flags
option(ENABLE_MQTT_TLS "Enable TLS/SSL encryption for MQTT connections (production HA)" OFF)

if(ENABLE_MQTT_TLS)
    add_compile_definitions(ENABLE_MQTT_TLS=1)
    message(STATUS "MQTT TLS encryption: ENABLED")
else()
    add_compile_definitions(ENABLE_MQTT_TLS=0)
    message(STATUS "MQTT TLS encryption: DISABLED (Standard TCP)")
endif()

# Enable testing
option(BUILD_TESTS "Build unit tests" ON)

# Core Firmware Library
add_library(hiri_mqtt STATIC
    src/mqtt_client.cpp
)
target_include_directories(hiri_mqtt PUBLIC include)

if(ENABLE_MQTT_TLS)
    find_package(MbedTLS REQUIRED)
    target_link_libraries(hiri_mqtt PUBLIC MbedTLS::mbedtls MbedTLS::mbedcrypto MbedTLS::mbedx509)
endif()

# Main executable
add_executable(hiri_firmware
    src/main.cpp
)
target_link_libraries(hiri_firmware PRIVATE hiri_mqtt)

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_executable(test_mqtt_client
        tests/test_mqtt_client.cpp
    )
    target_link_libraries(test_mqtt_client PRIVATE hiri_mqtt)
    add_test(NAME mqtt_client COMMAND test_mqtt_client)
endif()
