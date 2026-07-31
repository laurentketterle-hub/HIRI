#include "mqtt_client.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>

#ifdef _WIN32
#include <winsock2.h>
#define close closesocket
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#endif

// ── MQTT packet helpers ────────────────────────────────────────────────

static uint8_t mqtt_encode_remaining_length(uint32_t length, uint8_t *buf) {
    uint8_t encoded = 0;
    do {
        uint8_t byte = length % 128;
        length /= 128;
        if (length > 0) byte |= 0x80;
        buf[encoded++] = byte;
    } while (length > 0);
    return encoded;
}

static int mqtt_send_connect(mqtt_client_t *client) {
    const char *client_id = client->config.client_id ? client->config.client_id : "hiri-client";
    uint8_t id_len = (uint8_t)strlen(client_id);
    
    uint8_t var_header[10];
    var_header[0] = 0x00; var_header[1] = 0x04; // Protocol name length
    var_header[2] = 'M'; var_header[3] = 'Q';
    var_header[4] = 'T'; var_header[5] = 'T';
    var_header[6] = 0x04; // Protocol level (MQTT 3.1.1)
    uint8_t flags = 0x02; // Clean session
    if (client->config.username) flags |= 0x80;
    if (client->config.password) flags |= 0x40;
    var_header[7] = flags;
    var_header[8] = (uint8_t)(client->config.keepalive >> 8);
    var_header[9] = (uint8_t)(client->config.keepalive & 0xFF);

    uint32_t payload_len = 2 + id_len;
    uint8_t username_len = client->config.username ? (uint8_t)strlen(client->config.username) : 0;
    uint8_t password_len = (client->config.password && client->config.username) ? (uint8_t)strlen(client->config.password) : 0;
    if (username_len) payload_len += 2 + username_len;
    if (password_len) payload_len += 2 + password_len;

    uint32_t remaining = 10 + payload_len;
    uint8_t rl_buf[4];
    uint8_t rl_len = mqtt_encode_remaining_length(remaining, rl_buf);

    uint8_t *packet = (uint8_t *)malloc(1 + rl_len + remaining);
    if (!packet) return -1;
    uint8_t *p = packet;
    *p++ = 0x10; // CONNECT
    memcpy(p, rl_buf, rl_len); p += rl_len;
    memcpy(p, var_header, 10); p += 10;
    *p++ = 0x00; *p++ = id_len;
    memcpy(p, client_id, id_len); p += id_len;
    if (username_len) {
        *p++ = 0x00; *p++ = username_len;
        memcpy(p, client->config.username, username_len); p += username_len;
    }
    if (password_len) {
        *p++ = 0x00; *p++ = password_len;
        memcpy(p, client->config.password, password_len); p += password_len;
    }

    int total = (int)(1 + rl_len + remaining);
    int sent = 0;
#if ENABLE_MQTT_TLS
    if (client->config.use_tls) {
        while (sent < total) {
            int n = mbedtls_ssl_write(&client->ssl_ctx, packet + sent, total - sent);
            if (n <= 0) { free(packet); return -1; }
            sent += n;
        }
    } else
#endif
    {
        while (sent < total) {
            int n = (int)send(client->socket_fd, (const char *)(packet + sent), total - sent, 0);
            if (n <= 0) { free(packet); return -1; }
            sent += n;
        }
    }
    free(packet);
    return 0;
}

// ── Public API ─────────────────────────────────────────────────────────

void mqtt_init_config(mqtt_config_t *config) {
    if (!config) return;
    memset(config, 0, sizeof(mqtt_config_t));
    snprintf(config->host, sizeof(config->host), "%s", CONFIG_DEFAULT_MQTT_HOST);
    config->port = CONFIG_DEFAULT_MQTT_PORT;
    config->keepalive = 60;
#if ENABLE_MQTT_TLS
    config->use_tls = true;
#endif
}

bool mqtt_load_ca_cert_from_file(mqtt_config_t *config, const char *filepath) {
    if (!config || !filepath) return false;
    FILE *f = fopen(filepath, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (sz <= 0) { fclose(f); return false; }
    char *buf = (char *)malloc(sz + 1);
    if (!buf) { fclose(f); return false; }
    size_t read_bytes = fread(buf, 1, sz, f);
    fclose(f);
    buf[read_bytes] = '\0';
    config->ca_cert_pem = buf;
    config->ca_cert_len = read_bytes + 1;
    return true;
}

mqtt_error_t mqtt_client_init(mqtt_client_t *client, const mqtt_config_t *config) {
    if (!client || !config) return MQTT_ERR_PARAM;
    memset(client, 0, sizeof(mqtt_client_t));
    memcpy(&client->config, config, sizeof(mqtt_config_t));
    client->socket_fd = -1;
#if ENABLE_MQTT_TLS
    if (config->use_tls) {
        mbedtls_net_init(&client->net_ctx);
        mbedtls_ssl_init(&client->ssl_ctx);
        mbedtls_ssl_config_init(&client->ssl_conf);
        mbedtls_x509_crt_init(&client->ca_cert);
        mbedtls_x509_crt_init(&client->client_cert);
        mbedtls_pk_init(&client->client_key);
        mbedtls_entropy_init(&client->entropy);
        mbedtls_ctr_drbg_init(&client->ctr_drbg);
        if (mbedtls_ctr_drbg_seed(&client->ctr_drbg, mbedtls_entropy_func, &client->entropy, NULL, 0) != 0) {
            return MQTT_ERR_TLS;
        }
    }
#endif
    return MQTT_OK;
}

mqtt_error_t mqtt_connect(mqtt_client_t *client) {
    if (!client) return MQTT_ERR_PARAM;
    if (client->is_connected) return MQTT_OK;

#if ENABLE_MQTT_TLS
    if (client->config.use_tls) {
        char port_str[8];
        snprintf(port_str, sizeof(port_str), "%u", client->config.port);
        int ret = mbedtls_net_connect(&client->net_ctx, client->config.host, port_str, MBEDTLS_NET_PROTO_TCP);
        if (ret != 0) return MQTT_ERR_SOCKET;

        if (mbedtls_ssl_config_defaults(&client->ssl_conf,
                MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM,
                MBEDTLS_SSL_PRESET_DEFAULT) != 0) return MQTT_ERR_TLS;

        mbedtls_ssl_conf_rng(&client->ssl_conf, mbedtls_ctr_drbg_random, &client->ctr_drbg);

        if (client->config.ca_cert_pem && client->config.ca_cert_len > 0) {
            if (mbedtls_x509_crt_parse(&client->ca_cert, (const unsigned char *)client->config.ca_cert_pem, client->config.ca_cert_len) != 0)
                return MQTT_ERR_TLS;
            mbedtls_ssl_conf_ca_chain(&client->ssl_conf, &client->ca_cert, NULL);
        } else {
            mbedtls_ssl_conf_authmode(&client->ssl_conf, MBEDTLS_SSL_VERIFY_OPTIONAL);
        }

        if (mbedtls_ssl_setup(&client->ssl_ctx, &client->ssl_conf) != 0) return MQTT_ERR_TLS;
        if (mbedtls_ssl_set_hostname(&client->ssl_ctx, client->config.host) != 0) return MQTT_ERR_TLS;
        mbedtls_ssl_set_bio(&client->ssl_ctx, &client->net_ctx, mbedtls_net_send, mbedtls_net_recv, NULL);

        while ((ret = mbedtls_ssl_handshake(&client->ssl_ctx)) != 0) {
            if (ret != MBEDTLS_ERR_SSL_WANT_READ && ret != MBEDTLS_ERR_SSL_WANT_WRITE)
                return MQTT_ERR_TLS;
        }
    } else
#endif
    {
        client->socket_fd = (int)socket(AF_INET, SOCK_STREAM, 0);
        if (client->socket_fd < 0) return MQTT_ERR_SOCKET;
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(client->config.port);
        struct hostent *he = gethostbyname(client->config.host);
        if (!he) { close(client->socket_fd); return MQTT_ERR_SOCKET; }
        memcpy(&addr.sin_addr, he->h_addr_list[0], he->h_length);
        if (connect(client->socket_fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
            close(client->socket_fd);
            return MQTT_ERR_SOCKET;
        }
    }

    if (mqtt_send_connect(client) != 0) {
        mqtt_disconnect(client);
        return MQTT_ERR_CONNECT;
    }

    client->is_connected = true;
    return MQTT_OK;
}

mqtt_error_t mqtt_publish(mqtt_client_t *client, const char *topic, const uint8_t *payload, size_t payload_len, bool retain) {
    if (!client || !client->is_connected || !topic) return MQTT_ERR_PARAM;
    size_t topic_len = strlen(topic);
    if (topic_len == 0) return MQTT_ERR_PARAM;

    uint32_t remaining = 2 + (uint32_t)topic_len + (uint32_t)payload_len;
    uint8_t rl_buf[4];
    uint8_t rl_len = mqtt_encode_remaining_length(remaining, rl_buf);

    uint8_t header = 0x30;
    if (retain) header |= 0x01;

    size_t total = 1 + rl_len + remaining;
    uint8_t *packet = (uint8_t *)malloc(total);
    if (!packet) return MQTT_ERR_MEMORY;
    uint8_t *p = packet;
    *p++ = header;
    memcpy(p, rl_buf, rl_len); p += rl_len;
    *p++ = 0x00; *p++ = (uint8_t)topic_len;
    memcpy(p, topic, topic_len); p += topic_len;
    if (payload_len > 0) memcpy(p, payload, payload_len);

    int sent = 0;
#if ENABLE_MQTT_TLS
    if (client->config.use_tls) {
        while (sent < (int)total) {
            int n = mbedtls_ssl_write(&client->ssl_ctx, packet + sent, (int)(total - sent));
            if (n <= 0) { free(packet); return MQTT_ERR_PUBLISH; }
            sent += n;
        }
    } else
#endif
    {
        while (sent < (int)total) {
            int n = (int)send(client->socket_fd, (const char *)(packet + sent), (int)(total - sent), 0);
            if (n <= 0) { free(packet); return MQTT_ERR_PUBLISH; }
            sent += n;
        }
    }
    free(packet);
    return MQTT_OK;
}

mqtt_error_t mqtt_subscribe(mqtt_client_t *client, const char *topic) {
    if (!client || !client->is_connected || !topic) return MQTT_ERR_PARAM;
    size_t topic_len = strlen(topic);
    uint32_t remaining = 2 + 2 + (uint32_t)topic_len + 1;
    uint8_t rl_buf[4];
    uint8_t rl_len = mqtt_encode_remaining_length(remaining, rl_buf);
    size_t total = 1 + rl_len + remaining;
    uint8_t *packet = (uint8_t *)malloc(total);
    if (!packet) return MQTT_ERR_MEMORY;
    uint8_t *p = packet;
    *p++ = 0x82;
    memcpy(p, rl_buf, rl_len); p += rl_len;
    *p++ = 0x00; *p++ = 0x01; // packet identifier
    *p++ = 0x00; *p++ = (uint8_t)topic_len;
    memcpy(p, topic, topic_len); p += topic_len;
    *p++ = 0x00; // QoS 0
    int sent = 0;
#if ENABLE_MQTT_TLS
    if (client->config.use_tls) {
        while (sent < (int)total) { int n = mbedtls_ssl_write(&client->ssl_ctx, packet + sent, (int)(total - sent)); if (n <= 0) { free(packet); return MQTT_ERR_SUBSCRIBE; } sent += n; }
    } else
#endif
    { while (sent < (int)total) { int n = (int)send(client->socket_fd, (const char *)(packet + sent), (int)(total - sent), 0); if (n <= 0) { free(packet); return MQTT_ERR_SUBSCRIBE; } sent += n; } }
    free(packet);
    return MQTT_OK;
}

mqtt_error_t mqtt_unsubscribe(mqtt_client_t *client, const char *topic) {
    if (!client || !client->is_connected || !topic) return MQTT_ERR_PARAM;
    size_t topic_len = strlen(topic);
    uint32_t remaining = 2 + 2 + (uint32_t)topic_len;
    uint8_t rl_buf[4];
    uint8_t rl_len = mqtt_encode_remaining_length(remaining, rl_buf);
    size_t total = 1 + rl_len + remaining;
    uint8_t *packet = (uint8_t *)malloc(total);
    if (!packet) return MQTT_ERR_MEMORY;
    uint8_t *p = packet;
    *p++ = 0xA2;
    memcpy(p, rl_buf, rl_len); p += rl_len;
    *p++ = 0x00; *p++ = 0x02;
    *p++ = 0x00; *p++ = (uint8_t)topic_len;
    memcpy(p, topic, topic_len);
    int sent = 0;
#if ENABLE_MQTT_TLS
    if (client->config.use_tls) { while (sent < (int)total) { int n = mbedtls_ssl_write(&client->ssl_ctx, packet + sent, (int)(total - sent)); if (n <= 0) { free(packet); return MQTT_ERR_SUBSCRIBE; } sent += n; } }
    else
#endif
    { while (sent < (int)total) { int n = (int)send(client->socket_fd, (const char *)(packet + sent), (int)(total - sent), 0); if (n <= 0) { free(packet); return MQTT_ERR_SUBSCRIBE; } sent += n; } }
    free(packet);
    return MQTT_OK;
}

mqtt_error_t mqtt_disconnect(mqtt_client_t *client) {
    if (!client) return MQTT_ERR_PARAM;
    if (client->is_connected) {
        uint8_t disconnect[] = {0xE0, 0x00};
#if ENABLE_MQTT_TLS
        if (client->config.use_tls) mbedtls_ssl_write(&client->ssl_ctx, disconnect, 2);
        else
#endif
        send(client->socket_fd, (const char *)disconnect, 2, 0);
        client->is_connected = false;
    }
#if ENABLE_MQTT_TLS
    if (client->config.use_tls) {
        mbedtls_ssl_close_notify(&client->ssl_ctx);
        mbedtls_net_free(&client->net_ctx);
        mbedtls_ssl_free(&client->ssl_ctx);
        mbedtls_ssl_config_free(&client->ssl_conf);
        mbedtls_x509_crt_free(&client->ca_cert);
        mbedtls_x509_crt_free(&client->client_cert);
        mbedtls_pk_free(&client->client_key);
        mbedtls_entropy_free(&client->entropy);
        mbedtls_ctr_drbg_free(&client->ctr_drbg);
    } else
#endif
    { if (client->socket_fd >= 0) { close(client->socket_fd); client->socket_fd = -1; } }
    return MQTT_OK;
}

void mqtt_client_free(mqtt_client_t *client) {
    if (!client) return;
    mqtt_disconnect(client);
}

void mqtt_set_message_callback(mqtt_client_t *client, mqtt_message_callback_t callback, void *user_data) {
    if (!client) return;
    client->on_message = callback;
    client->user_data = user_data;
}

const char *mqtt_error_string(mqtt_error_t error) {
    switch (error) {
        case MQTT_OK: return "Success";
        case MQTT_ERR_SOCKET: return "Socket error";
        case MQTT_ERR_TLS: return "TLS error";
        case MQTT_ERR_CONNECT: return "Connection error";
        case MQTT_ERR_PUBLISH: return "Publish error";
        case MQTT_ERR_SUBSCRIBE: return "Subscribe error";
        case MQTT_ERR_MEMORY: return "Memory allocation error";
        case MQTT_ERR_PARAM: return "Invalid parameter";
        default: return "Unknown error";
    }
}
