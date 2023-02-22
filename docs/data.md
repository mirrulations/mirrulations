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
* At the root level, an agency such as "USTR" will exist
	* At the next level, an agencies docket will exist such as "USTR-2015-0010', which contains the agency, year, and docket number for the year
		* Under the docketId level such as "USTR-2015-0010", there are two subfolders, which seperate out binary data and text data
		* These folders are called "binary-{docketId}" and "text-{docketId}", which in this example, is "binary-USTR-2015-0010" and "text-USTR-2015-0010"
		* "binary-USTR-2015-0010" would contain two subdirectories, representing "comments_attachments", and "document_attachments"
			* Inside of "comments_attachments" a comment id will be contained, followed by the attachment number of that comment, such as "USTR-2015-0010-0002_attachment_1.pdf"
			* Inside of "documents_attachments" a document id will be contained, followed by the attachment number of that document, which are marked by the key word of "content". Contents can be of a variety of file types, such as "USTR-2015-0010-0001_content.pdf" and "USTR-2015-0010-0016_content.doc"
		* "text-USTR-2015-0010" would contain five subdirectories: docket, documents, comments, comments_extracted_text, documents_extracted_text
			* Inside of "comments", the json for a comment is contained such as "USTR-2015-0010-0002.json"
			* Inside of "comments_extracted_text", multiple directories would exist which would represent which text extraction tool was used for the attachments for a comment. In this example, these tools would include "pypdf" and "pdfplumber"
				* In a tool extraction directory such as "pydf", the text file of an attachment of a comment would exist, such as "USTR-2015-0010-0002_attachment_1_extracted.txt", which is the docketId + commentId, the attachment number, and "extracted", followed by the txt file extension
			* Inside of "docket" only the json of the docket would exist, and in this case, would be "USTR-2015-0010.json"
			* Inside of "documents", there exists the jsons for each document, along with the htm file for the fist document of a docket
				* An example of a document json is "USTR-2015-0010-0001.json"
				* This htm text file only exists for the first document of a docket, and contains the transcript of that document. An example of this is "USTR-2015-0010-0001_content.htm"
			* Inside of "documents_extracted_text", there would be multiple subdirectories, which indicate which text extraction tool was used. In this case, the two tools are "pypdf", and "pdfplumber"
				* In a text extraction tool directory such as "pypdf", the text file for an attachment of a document would exist such as "USTR-2015-0010-0001_content_extracted.txt", which is the docketId + documentId, the "content" marking, and "extracted", followed by the txt file descriptor.