#include "mqtt_client.h"
#include <stdio.h>

int main(int argc, char **argv) {
    printf("Starting HIRI Firmware...\n");

    mqtt_config_t config;
    mqtt_init_config(&config);

    if (argc > 1) {
        snprintf(config.host, sizeof(config.host), "%s", argv[1]);
    }
    if (argc > 2) {
        config.client_id = argv[2];
    }

#if ENABLE_MQTT_TLS
    if (argc > 3) {
        if (!mqtt_load_ca_cert_from_file(&config, argv[3])) {
            printf("[WARNING] Could not load CA cert from: %s\n", argv[3]);
        }
    } else {
        printf("[WARNING] TLS enabled but no CA certificate file path provided.\n");
    }
#endif

    mqtt_client_t client;
    mqtt_error_t err = mqtt_client_init(&client, &config);
    if (err != MQTT_OK) {
        printf("Failed to initialize MQTT client: %s\n", mqtt_error_string(err));
        return 1;
    }

    printf("Connecting to %s:%u...\n", config.host, config.port);
    err = mqtt_connect(&client);
    if (err == MQTT_OK) {
        printf("MQTT Session active.\n");
        const char *msg = "{\"status\":\"online\",\"device\":\"hiri-firmware\"}";
        mqtt_publish(&client, "hiri/status", (const uint8_t *)msg, strlen(msg), false);
        mqtt_disconnect(&client);
    } else {
        printf("MQTT Connection failed: %s\n", mqtt_error_string(err));
        mqtt_client_free(&client);
        return 1;
    }

    mqtt_client_free(&client);
    return 0;
}
