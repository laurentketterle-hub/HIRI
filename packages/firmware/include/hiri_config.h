#pragma once

// Override via build flags or local secrets (do not commit real WiFi passwords).
#ifndef HIRI_WIFI_SSID
#define HIRI_WIFI_SSID "YOUR_WIFI"
#endif
#ifndef HIRI_WIFI_PASS
#define HIRI_WIFI_PASS "YOUR_PASSWORD"
#endif
#ifndef HIRI_MQTT_HOST
#define HIRI_MQTT_HOST "homeassistant.local"
#endif
#ifndef HIRI_MQTT_PORT
#define HIRI_MQTT_PORT 1883
#endif
#ifndef HIRI_MQTT_USER
#define HIRI_MQTT_USER ""
#endif
#ifndef HIRI_MQTT_PASS
#define HIRI_MQTT_PASS ""
#endif
#ifndef HIRI_DEVICE_ID
#define HIRI_DEVICE_ID "hiri_node_01"
#endif

// TLS MQTT (optional) — set HIRI_MQTT_TLS=1 via build_flags for secure MQTT
#ifndef HIRI_MQTT_TLS
#define HIRI_MQTT_TLS 0
#endif
#ifndef HIRI_MQTT_TLS_PORT
#define HIRI_MQTT_TLS_PORT 8883
#endif
#ifndef HIRI_MQTT_TLS_CA_CERT
#define HIRI_MQTT_TLS_CA_CERT ""
#endif
#ifndef HIRI_MQTT_TLS_CLIENT_CERT
#define HIRI_MQTT_TLS_CLIENT_CERT ""
#endif
#ifndef HIRI_MQTT_TLS_CLIENT_KEY
#define HIRI_MQTT_TLS_CLIENT_KEY ""
#endif

// Deep sleep (optional) — power-saving for battery-operated farm nodes
#ifndef HIRI_DEEP_SLEEP_ENABLED
#define HIRI_DEEP_SLEEP_ENABLED 0
#endif
#ifndef HIRI_DEEP_SLEEP_SECONDS
#define HIRI_DEEP_SLEEP_SECONDS 300  // 5 minutes
#endif
#ifndef HIRI_DEEP_SLEEP_WAKE_PIN
#define HIRI_DEEP_SLEEP_WAKE_PIN GPIO_NUM_0
#endif

// Battery reporting (optional) — ADC pin for battery voltage monitoring
#ifndef HIRI_BATTERY_ENABLED
#define HIRI_BATTERY_ENABLED 0
#endif
#ifndef HIRI_BATTERY_ADC_PIN
#define HIRI_BATTERY_ADC_PIN 35
#endif
#ifndef HIRI_BATTERY_VOLTAGE_DIVIDER
#define HIRI_BATTERY_VOLTAGE_DIVIDER 2.0f  // voltage divider ratio
#endif
#ifndef HIRI_BATTERY_TOPIC
#define HIRI_BATTERY_TOPIC "hiri/state/hiri_node_01/battery"
#endif

// Sensor hardware is opt-in so existing simulated telemetry still works without
// attached DHT22/soil probes. Override these from build_flags or this file.
#ifndef HIRI_DHT_ENABLED
#define HIRI_DHT_ENABLED 0
#endif
#ifndef HIRI_DHT_PIN
#define HIRI_DHT_PIN 4
#endif
#ifndef HIRI_DHT_TYPE
#define HIRI_DHT_TYPE DHT22
#endif

#ifndef HIRI_SOIL_ADC_ENABLED
#define HIRI_SOIL_ADC_ENABLED 0
#endif
#ifndef HIRI_SOIL_ADC_PIN
#if defined(HIRI_BOARD_ESP8266) || defined(ESP8266)
#define HIRI_SOIL_ADC_PIN A0
#else
#define HIRI_SOIL_ADC_PIN 34
#endif
#endif
#ifndef HIRI_SOIL_ADC_DRY
#if defined(HIRI_BOARD_ESP8266) || defined(ESP8266)
#define HIRI_SOIL_ADC_DRY 1023
#else
#define HIRI_SOIL_ADC_DRY 3200
#endif
#endif
#ifndef HIRI_SOIL_ADC_WET
#if defined(HIRI_BOARD_ESP8266) || defined(ESP8266)
#define HIRI_SOIL_ADC_WET 300
#else
#define HIRI_SOIL_ADC_WET 1200
#endif
#endif
