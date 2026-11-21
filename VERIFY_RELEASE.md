# Verify the RRH package

The release bundle has two complementary checks:

1. `SHA256SUMS` **inside** the ZIP lists the checksums of the packaged source, guides, translations, tests and documents.
2. The **separate** `.sha256` file records the entire ZIP checksum. Its detached Ed25519 signature is verified with the public key distributed beside the package.

## Check archive checksum and detached signature

Place these four files in the same directory:

- `round-robin-hood-0.9.3.zip`
- `round-robin-hood-0.9.3.sha256`
- `round-robin-hood-0.9.3.sha256.sig`
- `round-robin-hood-0.9.3-public.pem`

Run:

```sh
sha256sum -c round-robin-hood-0.9.3.sha256
openssl pkeyutl -verify -pubin -inkey round-robin-hood-0.9.3-public.pem -sigfile round-robin-hood-0.9.3.sha256.sig -rawin -in round-robin-hood-0.9.3.sha256
```

To verify each file as well:

```sh
unzip -q round-robin-hood-0.9.3.zip -d rrh-check
cd rrh-check
sha256sum -c SHA256SUMS
```

**Trust limitation:** A signature only proves the content was signed with the corresponding private key. The publisher must publish the public-key fingerprint independently through a trusted project channel; a key supplied solely alongside a potentially tampered archive does **not** by itself authenticate its origin.

The private signing key and the private phrase-to-marker map are **not** present in the distributable ZIP or repository.
