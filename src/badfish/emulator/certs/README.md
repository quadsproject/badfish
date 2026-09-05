# Emulator TLS certificate

`emulator.crt` and `emulator.key` are a self-signed test certificate for the
built-in Redfish emulator. They are bundled so anyone can spin up a mock iDRAC
with zero setup, not for production use. The private key is public and must
never be used anywhere real.

badfish clients that talk to the emulator should pass `--insecure` to skip
verification of this self-signed certificate.

Regenerate (1 year, SAN for localhost and loopback):

```
openssl req -x509 -newkey rsa:2048 \
  -keyout emulator.key -out emulator.crt -days 365 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 emulator.key
```
