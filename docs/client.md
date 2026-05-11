# Client Documentation

## Summary

The **client** service downloads data from Regulations.gov. Unless stopped it repeats:

1. Rotate to the next API key from `client_keys.json` (see `KeyManager`).
2. Get work from the job queue (RabbitMQ).
3. Call the Regulations.gov API using that key, then save results (disk and S3).

Internally it uses Redis for job statistics and RabbitMQ for jobs. Keys and pacing come from **`mirrclient.key_manager.KeyManager`**; sleep duration between iterations is **`seconds_between_api_calls()`** (shared 1000/hour budget across keys).

## Details

Download jobs include fields such as `job_id`, `url`, and `job_type`. Logs identify which API key was used via each credential’s **`id`** in `client_keys.json`.

### Logging

Target behavior for production vs debug logging, field conventions, and examples: **[client_logging.md](client_logging.md)**.

### Getting work

A client pulls a job from the queue when work is available.

### Data download

After receiving a job, the client requests the API URL with the current key. Comments may trigger attachment downloads (no API key on those HTTP requests). Completed work increments Redis counters via `JobStatistics`.

If an unrecoverable error occurs, the client prints the failing job id and URL, then continues the loop.

### Saving data

Results are saved under `/data` and to the `mirrulations` S3 bucket when configured.

### Scaling

Run a **single** client replica per shared `client_keys.json`, or split keys across processes; multiple replicas using the same key file will overshoot API rate limits.
