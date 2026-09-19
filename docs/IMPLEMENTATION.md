# Implementation record

Authorized scope: complete local Waypoint website, Python backend, real navigation and ML evaluation, Android recording companion. No Git operations or deployment.

## Acceptance checklist
- [x] Persistent API, schema migration, durable jobs, recovery, backup/restore
- [x] Validated IO-VNBD import, segment selection, unit normalization, and preview
- [x] Causal inertial integration, error-state filtering, and learned velocity evaluation
- [x] Reproducible ridge and CNN-GRU training artifacts with held-out test metrics
- [x] Product landing page and complete workspace flows
- [x] Android recorder source, pairing, transfer protocol, and debug APK
- [x] Numerical, API, TypeScript, production-build, and Android JVM checks
- [x] Physical Galaxy S22 recording, pinned-TLS pairing, live transfer, retry/deduplication, and workspace import

Physical validation captured 5,291 samples over 49.57 seconds at 106.72 Hz. Eleven batches were acknowledged and the resulting dataset was imported into the IO-VNBD research project. The indoor validation recording did not contain a GPS fix, so it verifies the phone IMU and transfer path rather than position accuracy.

Raw IO-VNBD S1, S2, S4 downloaded or copied from the verified official source. Preserve these unchanged.
