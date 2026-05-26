# Mirrulations data layout

This page describes **where files live** for one **docket** in the public mirror. Paths below are shown the way they appear under the bucket root (for example on Amazon S3, keys start with `raw-data/...`). The same folder names apply when data is written to a local disk mount.

**Raw data** is exactly what was fetched from the Regulations.gov API (plus downloaded attachment files and document HTML bodies). **Derived data** is anything produced later by separate processing pipelines; layout under `derived-data/` is left to each project, but it is intended to stay traceable back to raw paths and names.

---

## One docket in one place

Every docket is stored under:

```text
raw-data/<agency>/<docket id>/
```

- **`<agency>`** — Agency abbreviation from Regulations.gov (same idea as `agencyId` in the API), for example `EPA` or `FDA`.
- **`<docket id>`** — Full docket identifier, for example `EPA-HQ-OPP-2011-0939`.

Under that folder there are two parallel trees:

| Branch | Purpose |
|--------|--------|
| **`text-<docket id>/`** | JSON metadata for the docket, its documents, and its comments; document body text as `.htm` / `.html` where available. |
| **`binary-<docket id>/`** | Non-JSON files for **comment** attachments (PDFs, images, etc.). |

Example (placeholders only):

```text
raw-data/
  └── EPA/
      └── EPA-HQ-OPP-2011-0939/
          ├── text-EPA-HQ-OPP-2011-0939/
          │   ├── docket/
          │   │   └── EPA-HQ-OPP-2011-0939.json
          │   ├── documents/
          │   │   ├── EPA-HQ-OPP-2011-0939-0001.json
          │   │   ├── EPA-HQ-OPP-2011-0939-0001_content.htm
          │   │   └── …
          │   └── comments/
          │       ├── EPA-HQ-OPP-2011-0939-0042.json
          │       └── …
          └── binary-EPA-HQ-OPP-2011-0939/
              └── comments_attachments/
                  ├── EPA-HQ-OPP-2011-0939-0042_<tail-from-download-url>.pdf
                  └── …
```

### What each file is

| Location | File | Contents |
|----------|------|----------|
| `text-…/docket/` | `<docket id>.json` | Docket record from the API. |
| `text-…/documents/` | `<document id>.json` | Document metadata. |
| `text-…/documents/` | `<document id>_content.htm` or `_content.html` | Downloaded document body when the mirror fetched HTML for that document. |
| `text-…/comments/` | `<comment id>.json` | Comment record (often including `include=attachments` so attachment metadata is present). |
| `binary-…/comments_attachments/` | `<comment id>_<tail>` | One file per attachment; **`<tail>`** is the last segment of the download URL (usually a filename with extension). |

Regulations.gov IDs appear in full in paths, so a comment id encodes its docket (same prefix as the parent folder).

---

## Multiple JSON snapshots: `(1)`, `(2)`, …

Regulations.gov can return a **new** JSON payload for the same docket, document, or comment later (for example after an edit). The mirror keeps a **canonical** filename first, then adds numbered sibling files when another distinct snapshot needs to be stored.

**Canonical file** — the path the mirror aims for first, for example:

```text
text-<docket id>/comments/<comment id>.json
```

**Additional snapshots** — same base name with a numeric suffix **in parentheses** before `.json`:

```text
<comment id>(1).json
<comment id>(2).json
…
```

So you might see `ABC-Docket-0001.json` alongside `ABC-Docket-0001(1).json`. Each file is a complete JSON document for that moment in time.

How a new snapshot is chosen depends on storage backend:

- **Disk** — If the canonical file is missing, it is created. If it already exists and the new payload is **identical JSON** to the file on disk, no extra file is written. If it exists and differs, the mirror writes the next free `(n).json` slot (skipping slots that already hold an identical payload).
- **S3** — If the canonical key is missing, it is created. If the key already exists, the next free `(n).json` key is used based on **object presence only** (no comparison of file bodies in the bucket).

Only **`.json`** objects follow this numbering rule. Other object types (HTML bodies, attachments, tombstones) use the single path described for them in this document unless noted otherwise.

The canonical **`.json`** path for a docket, document, or comment normally holds a **JSON** document. In the rare case where the API returns **HTTP success** but the body is **not valid JSON**, the client may instead store **raw response bytes** at that same canonical `.json` path (see **Unparseable API responses** below). Downstream tools should not assume every `*.json` object is parseable JSON.

---

## Tombstone files

When a download gets a **non-success HTTP response** (in client terms: `requests.Response.ok` is false—typically **4xx** or **5xx**, plus any other status the library treats as failure), the mirror writes a **tombstone** instead of the artifact: a small plain-text file at the predictable path reserved for that artifact. The body is a single line of the form `HTTP <status code>` (for example `HTTP 404`). Tombstones exist so automated scans can tell “we tried here” instead of seeing a missing file with no explanation.

There is **no separate retry loop** in the client for these writes: one non-OK response for that fetch produces one tombstone. **Unparseable** primary bodies on HTTP success are handled separately (see below). Broader retry or re-queue behavior is a pipeline concern outside this document.

**Primary job JSON** (docket / document / comment from the queue): tombstone paths are derived from the **job** (`job_type` and `url`), so the client does not need a parsed Regulations.gov JSON body to choose where the tombstone goes.

**Follow-up downloads** inside a job (comment attachments, document `.htm` / `.html` bodies): tombstones use the same layout rules as the success paths, based on the JSON already retrieved for that job.

Tombstones are written **next to** where the successful file would have lived, with a predictable name:

| Artifact | Tombstone path (same directory as the success case) |
|----------|------------------------------------------------------|
| Docket JSON | `text-…/docket/<docket id>_UNAVAILABLE` (no `.json` suffix on the tombstone name). |
| Document JSON | `text-…/documents/<document id>_UNAVAILABLE` |
| Comment JSON | `text-…/comments/<comment id>_UNAVAILABLE` |
| Comment attachment | Same directory and basename as the attachment, with `_UNAVAILABLE` inserted **before** the file extension — e.g. `…/comments_attachments/<comment id>_report.pdf` → `…/<comment id>_report_UNAVAILABLE.pdf`. |
| Document body `.htm` / `.html` | Same pattern: `…_content.htm` → `…_content_UNAVAILABLE.htm` (and similarly for `.html`). |

Treat any path ending in the `_UNAVAILABLE` marker (or containing `_UNAVAILABLE` immediately before the extension for binaries) as **not** a Regulations.gov payload: it is only the mirror’s note that the download did not succeed.

---

## Unparseable API responses (HTTP success)

If the **primary** Regulations.gov JSON request returns **HTTP success** (`Response.ok` true) but the response body **cannot be parsed as JSON**, the client does **not** write a tombstone for that case. It stores **`save_binary`** at the **canonical** `.json` path that would have been used for a normal save (derived from the job URL and `job_type`), so operators still see an object at the expected key. Logs record this outcome at **INFO**; the bytes may be HTML, an error page, or other non-JSON content.

---

## Derived data (`derived-data/`)

Derived products live under:

```text
derived-data/<agency>/<docket id>/<organization>/<project>/<file type>/…
```

- **`<organization>`** — Who produced the dataset (for example a research group name).
- **`<project>`** / **`<file type>`** — Project-specific layout; files here should remain mappable back to the corresponding paths under `raw-data/` for the same agency and docket.

---

## Reading this alongside the API

IDs in paths (`<docket id>`, `<document id>`, `<comment id>`) match Regulations.gov **entity ids** used in API URLs. If you have a comment URL from the API, the comment id is the last path segment; the docket id is the same value with the final `-<number>` segment removed for typical id patterns used in this mirror. For how the download **client** maps HTTP outcomes to files and logs, see **[client.md](client.md)** and **[client_logging.md](client_logging.md)**.

For questions about environment variables (alternate bucket names, disabling S3, etc.), see **[env_files.md](env_files.md)**.
