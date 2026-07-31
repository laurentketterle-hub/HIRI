//go:build tls

package tlsmqtt

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"math/big"
	"net"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// generateTestCert creates a self-signed certificate and key for testing.
// Returns paths to cert PEM and key PEM files.
func generateTestCert(t *testing.T, dir string) (certPath, keyPath string) {
	t.Helper()

	priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatalf("generate key: %v", err)
	}

	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			CommonName: "test.mqtt.local",
		},
		NotBefore:             time.Now().Add(-1 * time.Hour),
		NotAfter:              time.Now().Add(1 * time.Hour),
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth, x509.ExtKeyUsageClientAuth},
		BasicConstraintsValid: true,
		IPAddresses:           []net.IP{net.ParseIP("127.0.0.1")},
		DNSNames:              []string{"localhost", "test.mqtt.local"},
	}

	certDER, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &priv.PublicKey, priv)
	if err != nil {
		t.Fatalf("create cert: %v", err)
	}

	certPath = filepath.Join(dir, "test.pem")
	keyPath = filepath.Join(dir, "test-key.pem")

	certFile, err := os.Create(certPath)
	if err != nil {
		t.Fatalf("create cert file: %v", err)
	}
	defer certFile.Close()
	pem.Encode(certFile, &pem.Block{Type: "CERTIFICATE", Bytes: certDER})

	keyFile, err := os.Create(keyPath)
	if err != nil {
		t.Fatalf("create key file: %v", err)
	}
	defer keyFile.Close()
	privDER, _ := x509.MarshalECPrivateKey(priv)
	pem.Encode(keyFile, &pem.Block{Type: "EC PRIVATE KEY", Bytes: privDER})

	return certPath, keyPath
}

// startTLSServer starts a TLS echo server on a random port.
// Returns the address ("host:port") and a cleanup function.
func startTLSServer(t *testing.T, certPath, keyPath string) (string, func()) {
	t.Helper()

	cert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		t.Fatalf("load server cert: %v", err)
	}

	tlsCfg := &tls.Config{
		Certificates: []tls.Certificate{cert},
		MinVersion:   tls.VersionTLS12,
	}

	listener, err := tls.Listen("tcp", "127.0.0.1:0", tlsCfg)
	if err != nil {
		t.Fatalf("listen TLS: %v", err)
	}

	go func() {
		for {
			conn, err := listener.Accept()
			if err != nil {
				return
			}
			buf := make([]byte, 1024)
			n, _ := conn.Read(buf)
			conn.Write(buf[:n])
			conn.Close()
		}
	}()

	return listener.Addr().String(), func() { listener.Close() }
}

func TestNewTLSConfig_Minimal(t *testing.T) {
	cfg, err := NewTLSConfig(Config{})
	if err != nil {
		t.Fatalf("NewTLSConfig() error: %v", err)
	}
	if cfg.MinVersion != tls.VersionTLS12 {
		t.Errorf("default MinVersion = %d, want %d", cfg.MinVersion, tls.VersionTLS12)
	}
	if cfg.InsecureSkipVerify {
		t.Error("InsecureSkipVerify should be false by default")
	}
}

func TestNewTLSConfig_CustomMinVersion(t *testing.T) {
	cfg, err := NewTLSConfig(Config{MinVersion: tls.VersionTLS13})
	if err != nil {
		t.Fatalf("NewTLSConfig() error: %v", err)
	}
	if cfg.MinVersion != tls.VersionTLS13 {
		t.Errorf("MinVersion = %d, want %d", cfg.MinVersion, tls.VersionTLS13)
	}
}

func TestNewTLSConfig_MTLS_MissingKey(t *testing.T) {
	_, err := NewTLSConfig(Config{
		CertFile: "/tmp/cert.pem",
	})
	if err == nil {
		t.Error("expected error when KeyFile is missing")
	}
}

func TestNewTLSConfig_MissingCertFile(t *testing.T) {
	_, err := NewTLSConfig(Config{
		CAFile: "/nonexistent/ca.pem",
	})
	if err == nil {
		t.Error("expected error for nonexistent CA file")
	}
}

func TestNewTLSConfig_CAFile(t *testing.T) {
	dir := t.TempDir()
	certPath, _ := generateTestCert(t, dir)

	cfg, err := NewTLSConfig(Config{CAFile: certPath})
	if err != nil {
		t.Fatalf("NewTLSConfig() error: %v", err)
	}
	if cfg.RootCAs == nil {
		t.Error("RootCAs should be set when CAFile is provided")
	}
}

func TestNewTLSConfig_MTLS(t *testing.T) {
	dir := t.TempDir()
	certPath, keyPath := generateTestCert(t, dir)

	cfg, err := NewTLSConfig(Config{
		CertFile: certPath,
		KeyFile:  keyPath,
	})
	if err != nil {
		t.Fatalf("NewTLSConfig() error: %v", err)
	}
	if len(cfg.Certificates) != 1 {
		t.Errorf("expected 1 certificate, got %d", len(cfg.Certificates))
	}
}

func TestNewTLSConfig_InvalidCA(t *testing.T) {
	dir := t.TempDir()
	badPath := filepath.Join(dir, "not-a-cert.pem")
	os.WriteFile(badPath, []byte("not a certificate"), 0644)

	_, err := NewTLSConfig(Config{CAFile: badPath})
	if err == nil {
		t.Error("expected error for invalid CA file")
	}
}

func TestDial_Success(t *testing.T) {
	dir := t.TempDir()
	certPath, keyPath := generateTestCert(t, dir)

	addr, cleanup := startTLSServer(t, certPath, keyPath)
	defer cleanup()

	conn, err := Dial(addr, Config{
		CAFile:             certPath,
		ServerName:         "test.mqtt.local",
	})
	if err != nil {
		t.Fatalf("Dial() error: %v", err)
	}
	defer conn.Close()

	// Write and read
	msg := []byte("MQTT CONNECT")
	if _, err := conn.Write(msg); err != nil {
		t.Fatalf("write: %v", err)
	}

	buf := make([]byte, 1024)
	n, err := conn.Read(buf)
	if err != nil {
		t.Fatalf("read: %v", err)
	}
	if string(buf[:n]) != string(msg) {
		t.Errorf("echo = %q, want %q", buf[:n], msg)
	}
}

func TestDial_MTLS(t *testing.T) {
	dir := t.TempDir()
	certPath, keyPath := generateTestCert(t, dir)

	addr, cleanup := startTLSServer(t, certPath, keyPath)
	defer cleanup()

	// For mTLS, we need the server to accept our client cert.
	// The server doesn't do client auth, so this tests that
	// we can present a client cert without error.
	conn, err := Dial(addr, Config{
		CAFile:             certPath,
		CertFile:           certPath,
		KeyFile:            keyPath,
		ServerName:         "test.mqtt.local",
	})
	if err != nil {
		t.Fatalf("Dial() with mTLS error: %v", err)
	}
	defer conn.Close()

	msg := []byte("hello mTLS")
	conn.Write(msg)
	buf := make([]byte, 1024)
	n, _ := conn.Read(buf)
	if string(buf[:n]) != string(msg) {
		t.Errorf("echo = %q, want %q", buf[:n], msg)
	}
}

func TestDial_InvalidAddress(t *testing.T) {
	_, err := Dial("not-an-address", Config{})
	if err == nil {
		t.Error("expected error for invalid address")
	}
}

func TestDial_ConnectionRefused(t *testing.T) {
	// Use a port likely not in use
	_, err := Dial("127.0.0.1:19999", Config{
		InsecureSkipVerify: true,
	})
	if err == nil {
		t.Error("expected connection error")
	}
}

func TestMustTLSConfig_Success(t *testing.T) {
	tlsCfg := MustTLSConfig(Config{})
	if tlsCfg == nil {
		t.Error("MustTLSConfig returned nil")
	}
}

func TestMustTLSConfig_Panic(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("MustTLSConfig should panic on invalid config")
		}
	}()
	MustTLSConfig(Config{CAFile: "/nonexistent/file.pem"})
}

func TestConfig_DefaultValues(t *testing.T) {
	cfg := Config{}
	if cfg.CAFile != "" {
		t.Errorf("CAFile default = %q, want empty", cfg.CAFile)
	}
	if cfg.InsecureSkipVerify {
		t.Error("InsecureSkipVerify should default to false")
	}
	if cfg.MinVersion != 0 {
		t.Errorf("MinVersion default = %d, want 0", cfg.MinVersion)
	}
}
