# Client logging (design)

The download **client** uses Python’s **`logging`** module (stderr), with **`LOG_LEVEL`** defaulting to **`INFO`** (see [env_files.md](env_files.md)). Example lines below omit logger name in the message text; Docker may add a prefix.

---

## Jobs, parts, and completeness

**One job** is a single unit from the queue: a **docket**, **document**, or **comment** (use these **singular** names in log messages, even when internal fields use plurals like `job_type: "comments"`).

Jobs can have **multiple saved parts**:

| Job kind | Typical parts |
|----------|----------------|
| **docket** | Main JSON |
| **document** | Main JSON, plus HTM/HTML body when present |
| **comment** | Main JSON, plus each **attachment** |

The system is supposed to **download and persist everything** for that job. The client **does not** re-queue failed jobs. If a job does not fully complete, **logs are the only place** operators can see that; there is no separate “incomplete job” record to query.

**Operational goal:** From ERROR (and enough context on INFO when useful), you must be able to **identify which artifact** did not complete so you can re-download or fix the pipeline. If a failure is recurring, fix the systemic issue; if rare, **manually download** the data and place it on disk/S3.

**Identifying artifacts in messages (no internal `job_id`):**

- **Docket, document, comment (main JSON):** use the **regulations.gov entity id** as it appears in the API path (from the job URL, query stripped)—e.g. the final path segment of `/v4/dockets/…`, `/v4/documents/…`, `/v4/comments/…`.
- **Attachments:** use **comment entity id** plus **attachment number** (1-based index in the order the client processes attachments for that comment). Filename may appear as a convenience but the id + index is the stable handle.

---

## How Redis is used (client + `JobQueue`)

The client receives the **same Redis connection** used as `JobQueue`’s Redis `database` (plus a separate **RabbitMQ** connection inside `JobQueue` for the actual FIFO job list).

1. **Per-type “waiting” counters** — Keys like `num_jobs_dockets_waiting` / `documents` / `comments` are **decremented in Redis** when a job of that type is **dequeued** (`decrement_count`), so the dashboard can show backlog by type. This happens **before** the job is fully downloaded; if the process dies mid-job, the counter already dropped.

2. **“Done” statistics (`JobStatistics`)** — Keys like `num_dockets_done`, `num_documents_done`, `num_comments_done`, `num_attachments_done` (and PDF attachment count) are **incremented** when `increase_jobs_done` runs. Today, for the **main JSON** of a docket/document/comment, that increment runs **immediately before** `save_json` in `_download_job`—so the counter can be **ahead of disk/S3** if the save then fails. For **attachments** and **document HTM/HTML**, increments run **after** the corresponding `save_binary` path completes. Wrong counts are **annoying for the dashboard** but **do not mean data was written**; the filesystem and bucket are the source of truth for persistence.

3. **Connectivity check** — `_can_connect_to_database()` **pings** Redis before dequeue. If the ping fails, the client raises **`RedisPingFailedError`** (distinct from an empty queue). The main loop logs **WARNING** once per outage (see **Goals**).

RabbitMQ unavailability is separate: **no jobs can be consumed** even if Redis is up.

---

## Goals

**Operational clarity.** Production logs should make it obvious what was saved per artifact, when work stopped, and why—without burying signal in noise.

**Normal is not an error.** An empty job queue is expected: workers rotate keys and poll until work appears. That must **not** be logged as a failure at INFO or ERROR.

**RabbitMQ down (can’t fetch jobs).** This means **work is not flowing**, not that a specific docket/document/comment job failed. Use **WARNING** (the only deliberate use of that level today): message should state that **RabbitMQ is unreachable**, that **jobs cannot be fetched**, and that the **client will resume automatically when the broker is back**. **Log once on the transition** to unhealthy (e.g. `AMQPConnectionError`), then **suppress repeats** while the condition persists (**`rabbit_is_healthy`** or equivalent in the main loop). **Log recovery** at DEBUG or INFO if useful; do not spam every poll iteration.

**Redis dequeue ping.** **WARNING** once when ping fails before dequeue (suppressed repeats; recovery when dequeue succeeds again). Mid-job **`ConnectionError`** on Redis counters remains separate if it still arises.

**Persistence failures (`SaveError`).** Disk and S3 **`save_*`** methods raise **`SaveError`** with an operator-readable message (underlying cause chained). **`SaveError`** is not logged inside savers; the **main loop** logs **ERROR** from the exception string (include cause when present).

**HTTP status.** **4xx and 5xx** are treated the same for logging: a failed request logs **ERROR** (include status in the message for triage).

**Failure propagation (initial scope).** **One failed step fails the whole job**: raise to the **main client loop**. INFO lines for artifacts already written **before** the failure remain valid; later parts are missing—ERROR must identify **which artifact** was in progress (entity id from URL, or comment id + attachment index).

**Saver modules.** **`DiskSaver`** / **`S3Saver`** emit **DEBUG** only (paths, keys). **`INFO`** artifact lines come from **`Client`**, immediately **`after`** each successful `self.saver.save_json` / `save_binary`.

**Duplicate JSON (`DiskSaver`).** When payload matches existing on-disk JSON and no new file is written, **`DiskSaver`** logs **DEBUG** only (skipped write). Duplicate detection does **not** raise **`SaveError`**.

**Extracted text.** Downstream ETL handles extraction. The client uses **`save_json`** and **`save_binary`** only; **`save_text`** remains on savers for tests / symmetry and is **not** called from `Client`.

---

## Levels

### INFO

- **One line per artifact** successfully persisted (after **`Saver`** returns from fan-out to disk and/or S3).
- **`Client`** emits the line immediately after **`self.saver.save_json`** / **`self.saver.save_binary`** succeed.
- **Purpose:** Confirm what landed. Human-readable prose is fine.

### WARNING

- **Use only for RabbitMQ / dequeue unavailable** and **Redis ping before dequeue**, as described in **Goals**.

### ERROR

- **job_operation** failures: API timeout, **`HTTPError`**, and similar (see code).
- **Main loop:** **`SaveError`** (disk/S3 **`put_object`** / **`open`** / permission / etc.)—message text carries context.
- **Identity:** **Artifact** identity as in the table above where applicable. Include **redacted URL**, **`key_id`** when a credential was in use.

### DEBUG

- Dequeued job, download steps, attachment progress, document HTM save path, “job finished” summary; **Saver** internals (paths, S3 keys); optional Rabbit/Redis recovery.

### FATAL / **CRITICAL** (startup)

- Python **`logging`** has no **FATAL**; use **`CRITICAL`** for “cannot run the process” (**`CLIENT_KEYS_PATH`**, invalid keys file, Redis unavailable at bootstrap). **`sys.exit(1)`** follows.

### Generic **CRITICAL** (runtime)

- Reserved for optional future pager-level use.

---

## Where logging happens

| Area | INFO | WARNING | DEBUG | ERROR |
|------|------|---------|-------|-------|
| **`Saver`** | — | — | — | Raises only |
| **`DiskSaver` / `S3Saver`** | — | — | Paths / keys / duplicate skip | Raise **`SaveError`** (no logging) |
| **`Client`** | After each **`save_*`** success | — | Flow / job lifecycle | API timeout / **`HTTPError`** |
| **`__main__`** | — | Rabbit / Redis ping | Recovery (optional) | **`SaveError`**, Redis **`ConnectionError`** during loop |

Print statements for **enqueue** / **producer** Rabbit paths in **`mirrcore`** (shared with work generator) are **intentionally unchanged** until that package migrates separately.

---

## Examples (illustrative)

Timestamps omitted; formatter uses UTC ISO-like `asctime`.

**INFO — one JSON artifact:**

```text
2026-05-09T14:22:01Z INFO wrote artifact kind=docket type=json entity=DOE-HQ-2026-0001 file=DOE-HQ-2026-0001.json key_id=key4
```

**DEBUG — unchanged JSON on disk:**

```text
2026-05-09T14:30:00Z DEBUG Disk json unchanged skip write path=/data/.../doc.json
```

**ERROR — `SaveError` from main:**

```text
2026-05-09T15:03:40Z ERROR Disk save_binary failed path=/data/.../x.pdf: [Errno 13] Permission denied
```

**Idle worker:** no INFO lines when the queue is empty.

**WARNING — RabbitMQ unreachable (once per outage):**

```text
2026-05-09T14:00:05Z WARNING RabbitMQ unreachable; cannot fetch jobs. Client will resume when the broker is available again.
```

---

## Implementation notes

- **Default log level INFO** via **`LOG_LEVEL`** ([env_files.md](env_files.md)). **WARNING** remains visible when **`INFO`** is the floor.
- **UTC** timestamps on **`basicConfig`**-style formatter in **`mirrclient.logutil.configure_client_logging`**.

---

## Related

- Client overview: [client.md](client.md)
- Environment variables: [env_files.md](env_files.md)
