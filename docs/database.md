# Redis and job queue

Mirrulations uses **RabbitMQ** for the FIFO job list and **Redis** for numeric counters, Regulations.gov crawl checkpoints, and aggregate totals. The dashboard and work generator read both through `JobQueue` and `JobStatistics` in `mirrcore`.

## RabbitMQ: download jobs

Jobs are published to a durable queue named **`jobs_waiting_queue`**. Each message body is JSON with at least:

- **`job_id`** — integer, unique per assignment (`last_job_id` in Redis is incremented to produce the next id).
- **`url`** — Regulations.gov API URL for the client to request.
- **`job_type`** — from the Regulations.gov payload (`dockets`, `documents`, or `comments` for work the generator enqueues). Attachment files are downloaded inside a comment job, not as separate queued jobs.
- **`reg_id`**, **`agency`** — optional metadata carried with the job.

The work generator enqueues jobs; clients consume them with `basic_get`, acknowledge after read, and deserialize the JSON into a dict.

## Redis: keys in use

All of the following are string values in Redis unless noted. Application code treats counts as integers when reading.

### Job id sequence

| Key | Role |
|-----|------|
| **`last_job_id`** | Monotonic counter (`INCR`) used when assigning **`job_id`** to newly created jobs. |

### Per-type “waiting” counters (dashboard backlog)

These track how many jobs of each type were **added** to the pipeline versus **dequeued** for work. The work generator **`INCR`**s the matching key when it enqueues a job with that `job_type`. The client **`DECR`**s the matching key when it takes a job of that type from RabbitMQ (before the download finishes).

| Key |
|-----|
| **`num_jobs_dockets_waiting`** |
| **`num_jobs_documents_waiting`** |
| **`num_jobs_comments_waiting`** |

`JobQueue.get_job_stats()` exposes RabbitMQ depth as **`num_jobs_waiting`** (message count on `jobs_waiting_queue`) together with these three Redis integers as **`num_jobs_dockets_queued`**, **`num_jobs_documents_queued`**, and **`num_jobs_comments_queued`**.

### Completed work (`JobStatistics`)

| Key | Meaning |
|-----|---------|
| **`num_dockets_done`** | Count of completed docket jobs. |
| **`num_documents_done`** | Count of completed document jobs. |
| **`num_comments_done`** | Count of completed comment jobs. |
| **`num_attachments_done`** | Count of completed attachment downloads. |
| **`num_pdf_attachments_done`** | Subset of attachments that were PDFs. |

### Regulations.gov totals (snapshot from the API)

| Key | Meaning |
|-----|---------|
| **`regulations_total_dockets`** | Total dockets reported by Regulations.gov when the work generator last refreshed counts. |
| **`regulations_total_documents`** | Total documents. |
| **`regulations_total_comments`** | Total comments. |

### S3 mirror size

| Key | Meaning |
|-----|---------|
| **`mirrulations_bucket_size`** | Approximate S3 bucket size in **binary gigabytes** (1024³ bytes), updated by the work generator from CloudWatch metrics. |

### Work generator crawl checkpoints

The work generator stores the last processed **`lastModifiedDate`** boundary per endpoint so incremental runs can resume. Keys are built as `{endpoint}_last_timestamp` with **`endpoint`** in `dockets`, `documents`, or `comments`:

| Key |
|-----|
| **`dockets_last_timestamp`** |
| **`documents_last_timestamp`** |
| **`comments_last_timestamp`** |

Values are stored without the `T` / `Z` ISO-8601 suffixes (normalized to a space-separated form in `JobQueue.set_last_timestamp_string`). If a key is missing, readers use a default epoch string for “start from the beginning” behavior.

## Operational notes

- **Authoritative persistence** for downloaded payloads is disk and S3, not Redis. Counters are updated **after** each completed persistence branch for a job (see **[client_logging.md](client_logging.md)**); a crash can still leave Redis briefly out of sync with storage.
- **Redis connectivity** is checked before the client dequeues work; **RabbitMQ** availability is separate and determines whether jobs can be fetched at all.
