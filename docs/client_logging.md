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

**Operational goal:** From **ERROR** lines (transport, persistence failures) and enough **INFO** context (artifacts, tombstones, unparseable bodies), you must be able to **identify which artifact** did not complete—or what non-success artifact was recorded—so you can re-download or fix the pipeline. If a failure is recurring, fix the systemic issue; if rare, **manually download** the data and place it on disk/S3.

**Identifying artifacts in messages (no internal `job_id`):**

- **Docket, document, comment (main JSON):** use the **regulations.gov entity id** as it appears in the API path (from the job URL, query stripped)—e.g. the final path segment of `/v4/dockets/…`, `/v4/documents/…`, `/v4/comments/…`.
- **Attachments:** use **comment entity id** plus **attachment number** (1-based index in the order the client processes attachments for that comment). Filename may appear as a convenience but the id + index is the stable handle.

---

## How Redis is used (client + `JobQueue`)

The client receives the **same Redis connection** used as `JobQueue`’s Redis `database` (plus a separate **RabbitMQ** connection inside `JobQueue` for the actual FIFO job list).

1. **Per-type “waiting” counters** — Keys like `num_jobs_dockets_waiting` / `documents` / `comments` are **decremented in Redis** when a job of that type is **dequeued** (`decrement_count`), so the dashboard can show backlog by type. This happens **before** the job is fully downloaded; if the process dies mid-job, the counter already dropped.

2. **“Done” statistics (`JobStatistics`)** — Keys like `num_dockets_done`, `num_documents_done`, `num_comments_done`, `num_attachments_done` (and PDF attachment count) are **incremented** when `increase_jobs_done` runs. For the **main JSON** of a docket/document/comment, that increment runs **after** the job’s persistence for that branch finishes: on the success path, **after** `save_json` **and** any follow-up downloads (comment attachments, document HTM/HTML when applicable); on **non-OK** primary responses, after the **tombstone** is written; on **unparseable** primary bodies (HTTP success, invalid JSON), after **`save_binary`** at the canonical `.json` path. For **attachments** and **document HTM/HTML** sub-fetches, increments run **after** each attachment/body branch completes (`save_binary` or tombstone). If the process dies **after** `increase_jobs_done` but before the fact is durable elsewhere, the dashboard can briefly look **ahead** of external reality; if it dies **before** the increment after a successful save, the dashboard can look **behind**. Wrong counts are **annoying for the dashboard** but **do not replace** disk/S3 as the source of truth for persistence.

3. **Connectivity check** — `_can_connect_to_database()` **pings** Redis before dequeue. If the ping fails, the client raises **`RedisPingFailedError`** (distinct from an empty queue). The main loop logs **WARNING** once per outage (see **Goals**).

RabbitMQ unavailability is separate: **no jobs can be consumed** even if Redis is up.

---

## Goals

**Operational clarity.** Production logs should make it obvious what was saved per artifact, when work stopped, and why—without burying signal in noise.

**Normal is not an error.** An empty job queue is expected: workers rotate keys and poll until work appears. That must **not** be logged as a failure at INFO or ERROR.

**RabbitMQ down (can’t fetch jobs).** This means **work is not flowing**, not that a specific docket/document/comment job failed. Use **WARNING** (the only deliberate use of that level today): message should state that **RabbitMQ is unreachable**, that **jobs cannot be fetched**, and that the **client will resume automatically when the broker is back**. **Log once on the transition** to unhealthy (e.g. `AMQPConnectionError`), then **suppress repeats** while the condition persists (**`rabbit_is_healthy`** or equivalent in the main loop). **Log recovery** at DEBUG or INFO if useful; do not spam every poll iteration.

**Redis dequeue ping.** **WARNING** once when ping fails before dequeue (suppressed repeats; recovery when dequeue succeeds again). Mid-job **`ConnectionError`** on Redis counters remains separate if it still arises.

**Persistence failures (`SaveError`).** Disk and S3 **`save_*`** methods raise **`SaveError`** with an operator-readable message (underlying cause chained). **`SaveError`** is not logged inside savers; the **main loop** logs **ERROR** from the exception string (include cause when present).

**HTTP status vs transport.** Distinguish:

- **Primary Regulations.gov JSON URL** (`job`’s API URL): if the response is **not OK** (`requests.Response.ok` is false), the client writes a **tombstone** (see [structure.md](structure.md)), logs **INFO** (`wrote tombstone` with `http_status=…`), increments **done** counters for that job type, and **does not** treat this as a **`job_operation`** ERROR. If the response **is OK** but **`response.json()`** fails, the client writes **raw bytes** at the canonical `.json` path, logs **INFO** (`wrote unparseable api body …`), increments **done** counters, and again **does not** raise for that outcome.
- **Attachment and document-body URLs**: non-OK responses similarly produce **tombstones** and **INFO** lines (with `http_status`), with counters updated per attachment/body rules.
- **Transport failures** (timeouts, connection errors, and other **`requests.RequestException`** subclasses that prevent a normal response handling path): these still surface as structured **ERROR** logs from **`_handle_job_api_and_storage`** / the main loop as implemented, and **propagate** so the job does not appear “cleanly finished” the same way.

**Failure propagation.** **Transport** errors fail the **`job_operation`** path (raise after logging). **Handled HTTP outcomes** (primary non-OK, unparseable success body, attachment/body non-OK with tombstone) **complete** that branch without raising—**INFO** lines record what was written. If a **later** step raises (for example **`SaveError`** during a follow-up save), earlier INFO lines for artifacts already written remain valid; **ERROR** should identify what was in progress.

**Saver modules.** **`DiskSaver`** / **`S3Saver`** emit **DEBUG** only (paths, keys). **`INFO`** outcome lines come from **`Client`**, immediately **`after`** each successful `self.saver.save_json` / `save_binary`, and after **`save_tombstone`** for the tombstone paths above.

**Duplicate JSON (`DiskSaver`).** When payload matches existing on-disk JSON and no new file is written, **`DiskSaver`** logs **DEBUG** only (skipped write). Duplicate detection does **not** raise **`SaveError`**.

**Extracted text.** Downstream ETL handles extraction. The client uses **`save_json`** and **`save_binary`** only; **`save_text`** remains on savers for tests / symmetry and is **not** called from `Client`.

---

## Levels

### INFO

- **One line per persisted outcome** for the main job and follow-ups: normal JSON (`wrote artifact …`), binary body (`wrote artifact` after **`save_binary`**), **tombstone** (`wrote tombstone … http_status=…`), or **unparseable primary body** (`wrote unparseable api body …`)—each emitted after the corresponding **`Saver`** call returns from fan-out to disk and/or S3.
- **`Client`** emits the line immediately after **`self.saver.save_json`**, **`save_binary`**, or **`save_tombstone`** for those branches.
- **Purpose:** Confirm what landed (or that a deliberate tombstone/raw capture was written). Human-readable prose is fine.

### WARNING

- **Use only for RabbitMQ / dequeue unavailable** and **Redis ping before dequeue**, as described in **Goals**.

### ERROR

- **`job_operation` / API phase (transport):** API **read timeout** (`APITimeoutException`), and other **`requests.RequestException`** cases that escape the normal per-response handling (see **`mirrclient.client`**). Primary HTTP status failures are **not** logged here as ERROR when they are handled as tombstones.
- **Main loop:** **`SaveError`** (disk/S3 **`put_object`** / **`open`** / permission / etc.)—message text carries context. **`__main__`** may log an unexpected **`HTTPError`** at **DEBUG** if one surfaces outside the normal pipeline.
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
| **`Client`** | After **`save_json`** / **`save_binary`** / **`save_tombstone`** for handled outcomes | — | Flow / job lifecycle | API timeout / **`RequestException`** (transport) |
| **`__main__`** | — | Rabbit / Redis ping | Recovery (optional) | **`SaveError`**, Redis **`ConnectionError`** during loop |

Print statements for **enqueue** / **producer** Rabbit paths in **`mirrcore`** (shared with work generator) are **intentionally unchanged** until that package migrates separately.

---

## Examples (illustrative)

Timestamps omitted; formatter uses UTC ISO-like `asctime`.

**INFO — one JSON artifact:**

```text
2026-05-09T14:22:01Z INFO wrote artifact kind=docket type=json entity=DOE-HQ-2026-0001 file=DOE-HQ-2026-0001.json key_id=key4
```

**INFO — primary JSON tombstone (non-OK HTTP):**

```text
2026-05-09T14:25:00Z INFO wrote tombstone kind=document type=json entity=USTR-2015-0010-0015 file=USTR-2015-0010-0015_UNAVAILABLE key_id=key2 http_status=502
```

**INFO — HTTP 200 but body not JSON (raw bytes at canonical `.json` path):**

```text
2026-05-09T14:26:10Z INFO wrote unparseable api body kind=docket type=json entity=USTR-2015-0010 file=USTR-2015-0010.json key_id=key4
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
- Data layout and tombstones: [structure.md](structure.md)
- Environment variables: [env_files.md](env_files.md)
