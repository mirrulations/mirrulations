# S3 Structure

The `regulations.gov` API allows users to download multiple types of files.  We define this data as the **raw data**:

* **Docket metadata**: JSON files that contain high-level details about the docket
* **Document metadata**: JSON files that contain high-level details about the document
* **Document HTML**: HTML version of the Federal Register document
* **Comment metadata**: JSON files that contain high-level details about a comment (includes comment text entered on the [`regulations.gov`](https://www.regulations.gov/) website)
* **Attachments**: Files attached to a comment; arbitrary formats allowed; in practice mostly `.pdf` and `.docx`

The bucket allows for storage of **derived data**, defined as any data that is generated from one or more **raw data** files. In practice,
most derived data files correspond to a single raw data file, for example the text extracted from an attachment.

The structure of the S3 bucket aims to achieve the following goals:

* Keep all the data of a docket together
* Separate raw-data from derived data
* Document the source of derived data and support future expansion
* Keep all versions of files
* Document when files are missing
* Ensure that file linkage is maintained (e.g. attachments are linked to their corresponding metadata file)


```
s3://mirrulations/
     ├── raw-data/
     │   └── <agency>/
     │       └── <docket id>/
     │           ├── text-<docket id>/
     │           │   ├── comments
     │           │   │   ├── <comment id>.json
     │           │   │   ├── <comment id>_UNAVAILABLE
     │           │   │   └── ...
     │           │   ├── docket/
     │           │   │   ├── <docket id>.json
     │           │   │   ├── <docket id>(1).json
     │           │   │   └── ...
     │           │   └── documents/
     │           │       ├── <document id>.json
     │           │       ├── <document id>_content.html
     │           │       └── ...
     │           └── binary-<docket id>/
     │               └── comments_attachments
     │                   ├── <comment id>_attachment_<counter>.<extension>
     │                   ├── <comment id>_attachment_<counter>_UNAVAILABLE
     │                   └── ...
     └── derived-data/
         └── <agency>/
             └── <docket id>/
                 └── <organization>/
                     └── <project name>/
                         └── <file type>/
                             └── <data file>
```


### Raw Data Structure

* The directory structure indicates the agency, docket ID, and file type.
* For metadata files (JSON), the filename contains the ID contained in the file.
* When a new version of a file is downloaded, revision numbers (e.g. `(1)`, `(2)`, etc.) are appended to the filename.
* For HTML files, the filename contains the corresponding document ID
* For attachments, the filename contains the corresponding comment ID
* If a file could not be downloaded, the file extension is removed, and the filename is appended with `_UNAVAILABLE`.  The contents of this file will be the HTTP status code (non-200) that occurred when mirrulations attempted the download.

### Derived Data Structure

* The directory structure starts with the same agency and docket ID
* For each docket, the directory structure documents the organization that did the work and their project name.  Within this folder organizations have some flexibility on how they store data.


## Example Docket

This example is based on a real docket, `HUD-2026-0529`. For completeness of the example, some filenames were adjusted.

* This was the 529th docket created by HUD in 2026.  
* The docket contained one document with multiple versions.
* The docket received 4.48K comments.
* Some of the comments were unavailable when the mirrulations system attempted the download
* Many comments contained binary attachments
* Some of the attachments were unavailable when the mirrulations system attempted the download
* PDF attachments were processed by the mirrulations system to extract text using `pypdf`

The files are stored in the S3 bucket in the following structure:

```text
s3://mirrulations/
  ├── raw-data/
  │   └── HUD/
  │       └── HUD-2026-0529/
  │           ├── text-HUD-2026-0529/
  │           │   ├── docket/
  │           │   │   ├── HUD-2026-0529.json
  │           │   │   ├── HUD-2026-0529(1).json
  │           │   │   └── …
  │           │   ├── documents/
  │           │   │   ├── HUD-2026-0529-0001.json
  │           │   │   ├── HUD-2026-0529-0001_content.html
  │           │   │   └── …
  │           │   └── comments/
  │           │       ├── HUD-2026-0529-0002.json
  │           │       ├── HUD-2026-0529-0011.json
  │           │       ├── HUD-2026-0529-0099_UNAVAILABLE
  │           │       └── …
  │           └── binary-HUD-2026-0529/
  │               └── comments_attachments/
  │                   ├── HUD-2026-0529-0011_attachment_1.pdf
  │                   ├── HUD-2026-0529-0404_attachment_1_UNAVAILABLE
  │                   └── …
  └── derived-data/
      └── HUD/
          └── HUD-2026-0529/
              └── mirrulations/
                  └── extracted_txt/
                      └── comments_extracted_text/
                          └── pypdf/
                              ├── HUD-2026-0529-0011_attachment_1_extracted.txt
                              └── …
```

### File Descriptions

- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/docket/HUD-2026-0529.json` - The metadata for the original form of the docket
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/docket/HUD-2026-0529(1).json` - The metadata for the first revision of the docket
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/documents/HUD-2026-0529-0001.json` - Metadata for the document
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/documents/HUD-2026-0529-0001_content.html` - The text of the document
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/comments/HUD-2026-0529-0002.json` - Metadata for a comment
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/comments/HUD-2026-0529-0011.json` - Metadata for a second comment
- `raw-data/HUD/HUD-2026-0529/text-HUD-2026-0529/comments/HUD-2026-0529-0099_UNAVAILABLE` - A tombstone file indicating that the comment metadata was not available.  The file contains the HTTP status code returned by the regulations.gov API
- `raw-data/HUD/HUD-2026-0529/binary-HUD-2026-0529/comments_attachments/HUD-2026-0529-0011_attachment_1.pdf` - An attachment for the second comment (`HUD-2026-0529-0011`)
- `raw-data/HUD/HUD-2026-0529/binary-HUD-2026-0529/comments_attachments/HUD-2026-0529-0404_attachment_1_UNAVAILABLE` - A tombstone file indicating that the comment attachment was not available.  The file contains the HTTP status code returned by the regulations.gov API
- `derived-data/HUD/HUD-2026-0529/mirrulations/extracted_txt/comments_extracted_text/pypdf/HUD-2026-0529-0011_attachment_1_extracted.txt` - The text extracted from `HUD-2026-0529-0011_attachment_1.pdf` by `pypdf`


