#ifndef MQTT_CLIENT_H
#define MQTT_CLIENT_H

#ifndef ENABLE_MQTT_TLS
#define ENABLE_MQTT_TLS 0
#endif

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#if ENABLE_MQTT_TLS
#include "mbedtls/net_sockets.h"
#include "mbedtls/ssl.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/error.h"
#include "mbedtls/certs.h"
#endif

#ifndef CONFIG_DEFAULT_MQTT_HOST
#define CONFIG_DEFAULT_MQTT_HOST "mqtt-ha-broker.local"
#endif

#ifndef CONFIG_DEFAULT_MQTT_PORT
#if ENABLE_MQTT_TLS
#define CONFIG_DEFAULT_MQTT_PORT 8883
#else
#define CONFIG_DEFAULT_MQTT_PORT 1883
#endif
#endif

#define MQTT_MAX_TOPIC_LENGTH 256
#define MQTT_MAX_PAYLOAD_SIZE 4096

typedef enum {
    MQTT_OK = 0,
    MQTT_ERR_SOCKET = -1,
    MQTT_ERR_TLS = -2,
    MQTT_ERR_CONNECT = -3,
    MQTT_ERR_PUBLISH = -4,
    MQTT_ERR_SUBSCRIBE = -5,
    MQTT_ERR_MEMORY = -6,
    MQTT_ERR_PARAM = -7,
} mqtt_error_t;

typedef struct {
    char host[256];
    uint16_t port;
    uint16_t keepalive;
    bool use_tls;
    
    const char *ca_cert_pem;
    size_t ca_cert_len;
    
    const char *client_cert_pem;
    size_t client_cert_len;
    const char *client_key_pem;
    size_t client_key_len;

    const char *username;
    const char *password;
    const char *client_id;
} mqtt_config_t;

typedef void (*mqtt_message_callback_t)(const char *topic, const uint8_t *payload, size_t payload_len, void *user_data);

typedef struct {
    mqtt_config_t config;
    bool is_connected;
    int socket_fd;
    mqtt_message_callback_t on_message;
    void *user_data;
#if ENABLE_MQTT_TLS
    mbedtls_net_context net_ctx;
    mbedtls_ssl_context ssl_ctx;
    mbedtls_ssl_config ssl_conf;
    mbedtls_x509_crt ca_cert;
    mbedtls_x509_crt client_cert;
    mbedtls_pk_context client_key;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
#endif
} mqtt_client_t;

#ifdef __cplusplus
extern "C" {
#endif

void mqtt_init_config(mqtt_config_t *config);
mqtt_error_t mqtt_client_init(mqtt_client_t *client, const mqtt_config_t *config);
mqtt_error_t mqtt_connect(mqtt_client_t *client);
mqtt_error_t mqtt_publish(mqtt_client_t *client, const char *topic, const uint8_t *payload, size_t payload_len, bool retain);
mqtt_error_t mqtt_subscribe(mqtt_client_t *client, const char *topic);
mqtt_error_t mqtt_unsubscribe(mqtt_client_t *client, const char *topic);
mqtt_error_t mqtt_disconnect(mqtt_client_t *client);
void mqtt_client_free(mqtt_client_t *client);
bool mqtt_load_ca_cert_from_file(mqtt_config_t *config, const char *filepath);
void mqtt_set_message_callback(mqtt_client_t *client, mqtt_message_callback_t callback, void *user_data);
const char *mqtt_error_string(mqtt_error_t error);

#ifdef __cplusplus
}
#endif

#endif // MQTT_CLIENT_H
