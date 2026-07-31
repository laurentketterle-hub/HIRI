# tlsmqtt — Optional TLS MQTT for HIRI Firmware Bridge

Go package providing optional TLS support for MQTT connections in the HIRI firmware bridge.

## Features

- **Build-gated**: only compiled with `-tags tls` — zero overhead when disabled
- **CA certificates**: custom CA pool or system roots
- **mTLS**: mutual TLS with client certificates
- **Configurable**: minimum TLS version, server name override, skip verify (testing only)

## Quick Start

```go
import "github.com/mergeos-bounties/HIRI/packages/bridge/tlsmqtt"

cfg := tlsmqtt.Config{
    CAFile:   "/etc/hiri/ca.pem",
    CertFile: "/etc/hiri/client.pem",
    KeyFile:  "/etc/hiri/client-key.pem",
}

conn, err := tlsmqtt.Dial("mqtt.example.com:8883", cfg)
if err != nil {
    log.Fatal(err)
}
defer conn.Close()
```

## Build

```bash
# Compile with TLS support
go build -tags tls ./...

# Run tests
go test -tags tls -v ./...
```

## Configuration Reference

| Field | Type | Description |
|-------|------|-------------|
| `CAFile` | `string` | Path to CA certificate PEM file |
| `CertFile` | `string` | Path to client certificate PEM file (mTLS) |
| `KeyFile` | `string` | Path to client key PEM file (mTLS) |
| `ServerName` | `string` | Override TLS server name |
| `InsecureSkipVerify` | `bool` | Skip cert verification (testing only!) |
| `MinVersion` | `uint16` | Minimum TLS version (default: TLS 1.2) |

## License

Part of the HIRI project. See repository root for license.
