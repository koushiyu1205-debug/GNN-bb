# rcspp patch queue

The v1 native backend uses pinned upstream commit
`2f1d53ba6806844e30ce43ee9c41041a5a1b4e79` without a fork or source patch.

Exact mode sets `memory_pressure_fraction=1.0`, checks the hard memory limit before
pressure trimming, and treats any observed pressure event as a certificate blocker.
New patches must be listed in `manifest.json` with upstream blob hashes and a
standalone reproducer before they may enter the build.
