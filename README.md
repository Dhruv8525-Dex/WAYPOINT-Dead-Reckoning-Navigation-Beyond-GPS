# Waypoint

Waypoint is a local research workspace for smartphone IMU dead reckoning during GNSS outages. It keeps raw recordings, preprocessing decisions, model artifacts, experiments, and reports together so each result can be repeated and inspected.

## Run locally

Requirements: Node.js 20+, Python 3.12, and a Java 17+ JDK for the Android companion.

```powershell
npm install
.\scripts\setup.ps1
npm run dev
```

Open `http://127.0.0.1:5173`. The development launcher starts the Vite interface and the local FastAPI service. `npm run build` creates the production frontend, and `npm start` serves it with the API.

The default workspace is `data/workspace`. Set `WAYPOINT_DATA` to place the SQLite database and generated artifacts elsewhere. No account or hosted service is required.

Copy `.env.example` to `.env` only when overriding local defaults. The checked-in example contains no API key or credential. Install Python packages from `backend/requirements-lock.txt`; regenerate it with `pip-compile` after editing `backend/requirements.txt`. The local API accepts workspace requests only from loopback addresses; paired Android devices use token-authenticated endpoints. For a future hosted setup, `WAYPOINT_PUBLIC=1` requires a long `WAYPOINT_ADMIN_PASSWORD` and an explicit comma-separated `WAYPOINT_ALLOWED_ORIGINS` list. Do not expose the local workspace API publicly without configuring those settings and HTTPS.

Security and quality checks run on GitHub pushes and pull requests: TypeScript checking, Python tests, dependency audit, production build, a browser smoke flow, secret scanning, and CodeQL. Dependabot checks npm, Python, Gradle, and Actions dependencies weekly. These workflows do not deploy the app. SQLite has no user roles, so API read paths use a separate database connection opened in read-only mode; write paths retain the writable connection. HTTP security headers are configured in FastAPI (this is a Python app, so Node's `helmet` package does not apply).

## Product flow

1. Import an IO-VNBD CSV or pair the Android recorder.
2. Review detected columns, units, timestamp gaps, GPS coverage, and the selected continuous segment.
3. Optionally create a stationary calibration interval.
4. Train a causal ridge or CNN-GRU velocity model using disjoint dataset splits.
5. Configure a GPS outage and run raw inertial integration, the error-state filter, or learned velocity plus EKF.
6. Inspect trajectories and error metrics, then export CSV, JSON, or an HTML report.

The API validates uploaded data before it is persisted, stores immutable experiment configuration, and recovers interrupted jobs on restart. Backups are consistent SQLite snapshots with a SHA-256 manifest; restore only targets a newly empty workspace.

## Android companion

Build the recorder with `npm run android:build`. The APK is written to `artifacts/waypoint-recorder.apk`. It records accelerometer, gyroscope, optional gravity, and GPS samples to local JSONL, uploads complete batches over a pinned HTTPS/WebSocket connection, persists acknowledgements, and retries safely after interruption. Pairing is an expiring local code; the device token can be revoked from the workspace.

The companion was validated on a physical Galaxy S22: pairing, live transfer, acknowledgement persistence, retry/deduplication, local save, and workspace import all completed successfully. Benchmark recordings remain in the local workspace and are excluded from the public Git repository; import your own IO-VNBD files or a phone recording to exercise the desktop software.

## Scientific limits

This is a research instrument, not a certified navigation system. GPS is withheld only inside the configured outage, and reference GPS is used afterward for evaluation. Reports state whether metrics cover the outage or full route, preserve the estimator version, and label covariance as uncalibrated. Phone mounting, timestamp quality, sensor bias, GPS accuracy, and vehicle dynamics materially affect results.

Map tiles are loaded from OpenStreetMap in the browser and need network access. Computation, database state, recordings, and model artifacts stay local.
