# Client Documentation

## Summary

The **client** service downloads data from Regulations.gov. Unless stopped it repeats:

1. Rotate to the next API key from `client_keys.json` (see `KeyManager`).
2. Get work from the job queue (RabbitMQ).
3. Call the Regulations.gov API using that key, then save results (disk and S3).

Internally it uses Redis for job statistics and RabbitMQ for jobs. Keys and pacing come from **`mirrclient.key_manager.KeyManager`**. Each loop iteration calls **`get_next()`** then, after work, **`seconds_to_sleep()`**, which returns any remaining time needed to stay under the configured per-key hourly rate (default **999** calls/hour per key, overridable via **`calls_per_hour_per_key`** in `client_keys.json`). Elapsed job time reduces the sleep so pacing tracks wall clock.

## Details

Download jobs include fields such as `job_id`, `url`, and `job_type`. Logs identify which API key was used via each credential’s **`id`** in `client_keys.json`.

### Logging

Target behavior for production vs debug logging, field conventions, and examples: **[client_logging.md](client_logging.md)**.

### Getting work

A client pulls a job from the queue when work is available.

### Data download

After receiving a job, the client **GET**s the Regulations.gov **`url`** from the job with the current API key. Comments may trigger **attachment** downloads and documents may trigger **HTM/HTML body** downloads (those follow-up URLs typically **do not** include an API key).

The client branches on **`requests.Response.ok`**:

| Outcome | Primary JSON (docket / document / comment) |
|--------|---------------------------------------------|
| **Not OK** | Writes a **tombstone** next to the canonical JSON location; path comes from **`job_type`** and **`url`** (no parsed API body required). See [structure.md](structure.md) § Tombstone files. |
| **OK**, valid JSON | **`save_json`** at the path implied by the payload, then any follow-ups (attachments / document body) per job type. |
| **OK**, body not JSON | **`save_binary`** at the **canonical** `.json` path derived from the job (rare; see [structure.md](structure.md) § Unparseable API responses). |

Attachment and document-body fetches use the same **`response.ok`** idea: success **`save_binary`**, non-success **tombstone** on the corresponding path.

**Redis `JobStatistics`:** “done” counters for the main job type are incremented **after** that job’s persistence branch completes (including follow-ups on the happy path, or after tombstone / unparseable handling). Transport failures still prevent a clean finish and are logged at **ERROR**; see **[client_logging.md](client_logging.md)**.

If an unrecoverable error occurs in the main loop (for example **`SaveError`**), the client logs it and continues the polling loop.

### Saving data

Results are saved under **`/data`** (and in Docker, the mounted **`raw-data`** tree) and to the **`mirrulations`** S3 bucket when **`S3_BUCKET`** is set; see **[env_files.md](env_files.md)**. On-disk layout and tombstone naming match **[structure.md](structure.md)**.

### Scaling

Run a **single** client replica per shared `client_keys.json`, or split keys across processes; multiple replicas using the same key file will overshoot API rate limits.

## Related

- [structure.md](structure.md) — `raw-data/` layout, tombstones, unparseable primary bodies  
- [client_logging.md](client_logging.md) — log levels, Redis counters, ERROR vs INFO  
- [env_files.md](env_files.md) — `S3_BUCKET`, `LOG_LEVEL`, keys paths
