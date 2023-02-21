# Example Structure

```
data
└── USTR
    └── USTR-2015-0010
        ├── binary-USTR-2015-0010
        │   ├── comments_attachments
        │   │   ├── USTR-2015-0010-0002_attachment_1.pdf
        │   │   ├── USTR-2015-0010-0003_attachment_1.pdf
        │   │   ├── USTR-2015-0010-0004_attachment_1.pdf
        │   │   └── USTR-2015-0010-0005_attachment_1.pdf
        │   └── documents_attachments
        │       ├── USTR-2015-0010-0001_content.pdf
        │       ├── USTR-2015-0010-0016_content.doc
        │       ├── USTR-2015-0010-0016_content.pdf
        │       ├── USTR-2015-0010-0017_content.doc
        │       └── USTR-2015-0010-0017_content.pdf
        └── text-USTR-2015-0010
            ├── comments
            │   ├── USTR-2015-0010-0002.json
            │   ├── USTR-2015-0010-0003.json
            │   ├── USTR-2015-0010-0004.json
            │   └── USTR-2015-0010-0005.json
            ├── comments_extracted_text
            │   ├── pdfplumber
            │   │   ├── USTR-2015-0010-0002_attachment_1_extracted.txt
            │   │   ├── USTR-2015-0010-0003_attachment_1_extracted.txt
            │   │   ├── USTR-2015-0010-0004_attachment_1_extracted.txt
            │   │   └── USTR-2015-0010-0005_attachment_1_extracted.txt
            │   └── pypdf
            │       ├── USTR-2015-0010-0002_attachment_1_extracted.txt
            │       ├── USTR-2015-0010-0003_attachment_1_extracted.txt
            │       ├── USTR-2015-0010-0004_attachment_1_extracted.txt
            │       └── USTR-2015-0010-0005_attachment_1_extracted.txt
            ├── docket
            │   └── USTR-2015-0010.json
            ├── documents
            │   ├── USTR-2015-0010-0001.json
            │   ├── USTR-2015-0010-0001_content.htm
            │   ├── USTR-2015-0010-0015.json
            │   ├── USTR-2015-0010-0016.json
            │   └── USTR-2015-0010-0017.json
            └── documents_extracted_text
                ├── pdfplumber
                │   ├── USTR-2015-0010-0001_content_extracted.txt
                │   ├── USTR-2015-0010-0016_content_extracted.txt
                │   └── USTR-2015-0010-0017_content_extracted.txt
                └── pypdf
                    ├── USTR-2015-0010-0001_content_extracted.txt
                    ├── USTR-2015-0010-0016_content_extracted.txt
                    └── USTR-2015-0010-0017_content_extracted.txt
```

# Explanation
* 