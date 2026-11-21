# Verify Round Robin Hood 0.9.3

GitHub release `v0.9.3` provides `round-robin-hood-0.9.3.zip` and `round-robin-hood-0.9.3.sha256`.

The ZIP contains `SHA256SUMS`, which lists SHA-256 checksums of every other packaged file. The separate `.sha256` file records the digest of the complete ZIP.

Download both files from [the official GitHub Releases page](https://github.com/satisfried-yt/round-robin-hood/releases).

Verify the complete archive:

```sh
sha256sum -c round-robin-hood-0.9.3.sha256
```

Verify the contents:

```sh
mkdir -p rrh-check
unzip -q round-robin-hood-0.9.3.zip -d rrh-check
cd rrh-check
sha256sum -c SHA256SUMS
```

**Security limitation:** Checksums detect corruption and support comparison against a digest obtained through a trusted channel, but a checksum hosted alongside an altered archive is not an independent authenticity proof. Version 0.9.3 **does not publish a detached signature or a trusted signing key**.

The ZIP contains the full tracked source tree. For installation in Home Assistant, copy **only** `custom_components/round_robin_hood`; preserve the existing Home Assistant `.storage` data. For updating 0.9.2 use the [backup/rollback procedure](docs/UPDATE_0.9.3.md).
