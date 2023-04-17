# Structure Overview

This structure organizes data by agency and docket id.  Within each docket, the binary data (attachments) are stored separately from the text data so that users can easily download only the text data.

The structure also allows us to store the results from multiple text extraction tools.  Further, the attachments on comments and documents are stored separately.

```
data
└── <agency>
    └── <docket id>
        ├── binary-<docket id>
        │   ├── comments_attachments
        │   │   ├── <comment id>_attachement_<counter>.<extension>
        │   │   └── ...
        │   ├── documents_attachments
        │   │   ├── <document id>_attachement_<counter>.<extension>
        │   │   └── ...
        └── text-<docket id>
            ├── comments
            │   ├── <comment id>.json
            │   └── ...
            ├── comments_extracted_text
            │   ├── <tool name>
            │   |   ├── <comment id>_attachment_<counter>_extracted.txt
            │   |   └── ...
            |   └─ ... <other tools>
            ├── docket
            │   ├── <docket id>.json
            |   └── ...
            ├── documents
            │   ├── <document id>.json
            │   ├── <document id>_content.htm
            │   └── ...
            └── documents_extracted_text
                ├── <tool name>
                |   ├── <document id>_content_extracted.txt
                |   └── ...
                └─ ... <other tools>
```                    

# Example

The USTR contains a docket id `USTR-2015-0010` that holds 1 docket, 4 documents, and 4 comments.  Each of the comments has an attachment, and each of the documents have one or more attachments.  The tool `pikepdf` was used to extract text from these attachments.


This data would be stored in the structure as follows:

```
data
└── USTR
    └── USTR-2015-0010
        ├── binary-USTR-2015-0010
        │   ├── comments_attachments
        │   │   ├── USTR-2015-0010-0002_attachment_1.pdf
        │   │   ├── USTR-2015-0010-0003_attachment_1.pdf
        │   │   ├── USTR-2015-0010-0004_attachment_1.pdf
        │   │   └── USTR-2015-0010-0005_attachment_1.pdf
        │   └── documents_attachments
        │       ├── USTR-2015-0010-0001_content.pdf
        │       ├── USTR-2015-0010-0015_content.pdf
        │       ├── USTR-2015-0010-0016_content.doc
        │       ├── USTR-2015-0010-0016_content.pdf
        │       ├── USTR-2015-0010-0017_content.doc
        │       └── USTR-2015-0010-0017_content.pdf
        └── text-USTR-2015-0010
            ├── comments
            │   ├── USTR-2015-0010-0002.json
            │   ├── USTR-2015-0010-0003.json
            │   ├── USTR-2015-0010-0004.json
            │   └── USTR-2015-0010-0005.json
            ├── comments_extracted_text
            │   ├── pikepdf
            │       ├── USTR-2015-0010-0002_attachment_1_extracted.txt
            │       ├── USTR-2015-0010-0003_attachment_1_extracted.txt
            │       ├── USTR-2015-0010-0004_attachment_1_extracted.txt
            │       └── USTR-2015-0010-0005_attachment_1_extracted.txt
            ├── docket
            │   └── USTR-2015-0010.json
            ├── documents
            │   ├── USTR-2015-0010-0001.json
            │   ├── USTR-2015-0010-0001_content.htm
            │   ├── USTR-2015-0010-0015.json
            │   ├── USTR-2015-0010-0016.json
            │   └── USTR-2015-0010-0017.json
            └── documents_extracted_text
                ├── pikepdf
                    ├── USTR-2015-0010-0015_content_extracted.txt
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
			* Inside of "comments_extracted_text", multiple directories would exist which would represent which text extraction tool was used for the attachments for a comment. In this example, only the tool 'pikepdf' was used
				* In a tool extraction directory such as 'pikepdf', the text file of an attachment of a comment would exist, such as "USTR-2015-0010-0002_attachment_1_extracted.txt", which is the docketId + commentId, the attachment number, and "extracted", followed by the txt file extension
			* Inside of "docket" only the json of the docket would exist, and in this case, would be "USTR-2015-0010.json"
			* Inside of "documents", there exists the jsons for each document, along with the htm file if one exists
				* An example of a document json is "USTR-2015-0010-0001.json"
				* An example of an htm document is "USTR-2015-0010-0001_content.htm"
			* Inside of "documents_extracted_text", there would be multiple subdirectories, which indicate which text extraction tool was used. In this case, the tool used was 'pikepdf'
				* In a text extraction tool directory such as 'pikepdf', the text file for an attachment of a document would exist such as "USTR-2015-0010-0001_content_extracted.txt", which is the docketId + documentId, the "content" marking, and "extracted", followed by the txt file descriptor.