#include "mqtt_client.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>

static void test_init_config(void) {
    mqtt_config_t config;
    mqtt_init_config(&config);
    assert(strcmp(config.host, CONFIG_DEFAULT_MQTT_HOST) == 0);
    assert(config.port == CONFIG_DEFAULT_MQTT_PORT);
    assert(config.keepalive == 60);
#if ENABLE_MQTT_TLS
    assert(config.use_tls == true);
#else
    assert(config.use_tls == false);
#endif
    printf("PASS: test_init_config\n");
}

static void test_init_config_null(void) {
    mqtt_init_config(NULL); // Must not crash
    printf("PASS: test_init_config_null\n");
}

static void test_client_init(void) {
    mqtt_config_t config;
    mqtt_init_config(&config);
    mqtt_client_t client;
    mqtt_error_t err = mqtt_client_init(&client, &config);
    assert(err == MQTT_OK);
    assert(client.is_connected == false);
    mqtt_client_free(&client);
    printf("PASS: test_client_init\n");
}

static void test_client_init_null(void) {
    mqtt_error_t err = mqtt_client_init(NULL, NULL);
    assert(err == MQTT_ERR_PARAM);
    printf("PASS: test_client_init_null\n");
}

static void test_error_strings(void) {
    assert(strcmp(mqtt_error_string(MQTT_OK), "Success") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_SOCKET), "Socket error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_TLS), "TLS error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_CONNECT), "Connection error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_PUBLISH), "Publish error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_SUBSCRIBE), "Subscribe error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_MEMORY), "Memory allocation error") == 0);
    assert(strcmp(mqtt_error_string(MQTT_ERR_PARAM), "Invalid parameter") == 0);
    assert(strcmp(mqtt_error_string((mqtt_error_t)999), "Unknown error") == 0);
    printf("PASS: test_error_strings\n");
}

static void test_load_ca_cert_file_null(void) {
    assert(mqtt_load_ca_cert_from_file(NULL, "test.pem") == false);
    mqtt_config_t config;
    assert(mqtt_load_ca_cert_from_file(&config, NULL) == false);
    printf("PASS: test_load_ca_cert_file_null\n");
}

static void test_load_ca_cert_file_missing(void) {
    mqtt_config_t config;
    assert(mqtt_load_ca_cert_from_file(&config, "/nonexistent/ca.pem") == false);
    printf("PASS: test_load_ca_cert_file_missing\n");
}

static void test_publish_not_connected(void) {
    mqtt_client_t client;
    mqtt_config_t config;
    mqtt_init_config(&config);
    mqtt_client_init(&client, &config);
    mqtt_error_t err = mqtt_publish(&client, "test/topic", (const uint8_t *)"hello", 5, false);
    assert(err == MQTT_ERR_PARAM);
    mqtt_client_free(&client);
    printf("PASS: test_publish_not_connected\n");
}

static void test_callback_set(void) {
    mqtt_client_t client;
    memset(&client, 0, sizeof(client));
    mqtt_set_message_callback(&client, NULL, NULL);
    assert(client.on_message == NULL);
    assert(client.user_data == NULL);
    printf("PASS: test_callback_set\n");
}

static void test_custom_config(void) {
    mqtt_config_t config;
    memset(&config, 0, sizeof(config));
    snprintf(config.host, sizeof(config.host), "broker.example.com");
    config.port = 1883;
    config.keepalive = 120;
    config.client_id = "test-device";
    config.username = "user";
    config.password = "pass";

    assert(strcmp(config.host, "broker.example.com") == 0);
    assert(config.port == 1883);
    assert(config.keepalive == 120);
    assert(strcmp(config.client_id, "test-device") == 0);
    printf("PASS: test_custom_config\n");
}

int main(void) {
    printf("Running MQTT client unit tests...\n\n");
    test_init_config();
    test_init_config_null();
    test_client_init();
    test_client_init_null();
    test_error_strings();
    test_load_ca_cert_file_null();
    test_load_ca_cert_file_missing();
    test_publish_not_connected();
    test_callback_set();
    test_custom_config();
    printf("\nAll tests passed!\n");
    return 0;
}
