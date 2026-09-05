# Emulator TLS certificate

No private key is shipped with badfish. On first start, the emulator generates a
fresh self-signed localhost certificate (`emulator.crt` / `emulator.key`) in a
per-user writable directory, so every install has its own keypair and none ever
sits in SCM or in built artifacts (wheel/RPM).

Default location (see `_default_cert_dir` in `src/badfish/emulator.py`):

```
$XDG_CACHE_HOME/badfish/emulator/   (default: ~/.cache/badfish/emulator/)
```

Override with the `BADFISH_EMULATOR_CERTS` env var, pointing at a directory that
already contains `emulator.crt` and `emulator.key`, or an empty directory where
they should be created. Requires `openssl` on PATH to generate the keypair.

The generated certificate is self-signed (CN=localhost, SAN localhost +
127.0.0.1, valid 1 year) for local/test use only, not production. badfish clients
that talk to the emulator should pass `--insecure` to skip verification of this
self-signed certificate.

The equivalent manual command, for reference:

```
openssl req -x509 -newkey rsa:2048 \
  -keyout emulator.key -out emulator.crt -days 365 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 600 emulator.key
```
