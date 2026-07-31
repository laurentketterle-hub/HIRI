//go:build tls

// Package tlsmqtt provides optional TLS support for MQTT connections.
// It is only compiled when the "tls" build tag is specified.
//
// Usage:
//
//	go build -tags tls ./...
//	go test -tags tls ./...
//
// This package is designed to be used by the HIRI firmware bridge
// to establish secure MQTT connections in production environments.
package tlsmqtt

import (
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net"
	"os"
	"time"
)

// Config holds the TLS configuration for MQTT connections.
type Config struct {
	// CAFile is the path to the CA certificate file (PEM format).
	// If empty, the system's root CA pool is used.
	CAFile string

	// CertFile is the path to the client certificate file (PEM format).
	// Required for mutual TLS (mTLS). Leave empty for server-only auth.
	CertFile string

	// KeyFile is the path to the client private key file (PEM format).
	// Required when CertFile is set.
	KeyFile string

	// ServerName overrides the server name used for TLS verification.
	// Defaults to the hostname from the MQTT broker address.
	ServerName string

	// InsecureSkipVerify disables TLS certificate verification.
	// Only use for testing — never in production.
	InsecureSkipVerify bool

	// MinVersion sets the minimum TLS version (default: TLS 1.2).
	MinVersion uint16
}

// NewTLSConfig builds a *tls.Config from the package Config.
// Returns an error if certificate files cannot be loaded.
func NewTLSConfig(cfg Config) (*tls.Config, error) {
	tlsCfg := &tls.Config{
		InsecureSkipVerify: cfg.InsecureSkipVerify, //nolint:gosec
		ServerName:         cfg.ServerName,
	}

	// Minimum TLS version
	if cfg.MinVersion == 0 {
		tlsCfg.MinVersion = tls.VersionTLS12
	} else {
		tlsCfg.MinVersion = cfg.MinVersion
	}

	// Root CA
	if cfg.CAFile != "" {
		caCert, err := os.ReadFile(cfg.CAFile)
		if err != nil {
			return nil, fmt.Errorf("tlsmqtt: read CA file %s: %w", cfg.CAFile, err)
		}
		caCertPool := x509.NewCertPool()
		if !caCertPool.AppendCertsFromPEM(caCert) {
			return nil, fmt.Errorf("tlsmqtt: failed to parse CA certificate from %s", cfg.CAFile)
		}
		tlsCfg.RootCAs = caCertPool
	}

	// Client certificate (mTLS)
	if cfg.CertFile != "" || cfg.KeyFile != "" {
		if cfg.CertFile == "" || cfg.KeyFile == "" {
			return nil, fmt.Errorf("tlsmqtt: both CertFile and KeyFile must be set for mTLS")
		}
		cert, err := tls.LoadX509KeyPair(cfg.CertFile, cfg.KeyFile)
		if err != nil {
			return nil, fmt.Errorf("tlsmqtt: load client cert/key: %w", err)
		}
		tlsCfg.Certificates = []tls.Certificate{cert}
	}

	return tlsCfg, nil
}

// Dial opens a TLS connection to the given address using the provided Config.
// The address should be in "host:port" format (e.g., "mqtt.example.com:8883").
func Dial(address string, cfg Config) (net.Conn, error) {
	tlsCfg, err := NewTLSConfig(cfg)
	if err != nil {
		return nil, err
	}

	if tlsCfg.ServerName == "" {
		host, _, err := net.SplitHostPort(address)
		if err != nil {
			return nil, fmt.Errorf("tlsmqtt: invalid address %s: %w", address, err)
		}
		tlsCfg.ServerName = host
	}

	dialer := &net.Dialer{Timeout: 10 * time.Second}
	return tls.DialWithDialer(dialer, "tcp", address, tlsCfg)
}

// MustTLSConfig is like NewTLSConfig but panics on error.
// Useful for static configurations in main packages.
func MustTLSConfig(cfg Config) *tls.Config {
	tlsCfg, err := NewTLSConfig(cfg)
	if err != nil {
		panic(fmt.Sprintf("tlsmqtt: %v", err))
	}
	return tlsCfg
}
