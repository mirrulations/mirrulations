# Example

```
data
├── comments
│   └── USTR
│       └── USTR-2015-0010
│           ├── USTR-2015-0010-0002
│           │   ├── USTR-2015-0010-0002.json
│           │   ├── USTR-2015-0010-0002_attachment_1.pdf
│           │   ├── USTR-2015-0010-0002_attchment_1_pdfplumber_extracted.txt
│           │   └── USTR-2015-0010-0002_attchment_1_pypdf_extracted.txt
│           ├── USTR-2015-0010-0003
│           │   ├── USTR-2015-0010-0003.json
│           │   ├── USTR-2015-0010-0003_attachment_1.pdf
│           │   ├── USTR-2015-0010-0003_attchment_1_pdfplumber_extracted.txt
│           │   └── USTR-2015-0010-0003_attchment_1_pypdf_extracted.txt
│           ├── USTR-2015-0010-0004
│           │   ├── USTR-2015-0010-0004.json
│           │   ├── USTR-2015-0010-0004_attachment_1.pdf
│           │   ├── USTR-2015-0010-0004_attchment_1_pdfplumber_extracted.txt
│           │   └── USTR-2015-0010-0004_attchment_1_pypdf_extracted.txt
│           └── USTR-2015-0010-0005
│               ├── USTR-2015-0010-0005.json
│               ├── USTR-2015-0010-0005_attachment_1.pdf
│               ├── USTR-2015-0010-0005_attchment_1_pdfplumber_extracted.txt
│               └── USTR-2015-0010-0005_attchment_1_pypdf_extracted.txt
├── dockets
│   └── USTR
│       └── USTR-2015-0010
│           └── USTR-2015-0010.json
└── documents
    └── USTR
        └── USTR-2015-0010
            ├── USTR-2015-0010-0001
            │   ├── USTR-2015-0010-0001.json
            │   ├── USTR-2015-0010-0001_content.htm
            │   ├── USTR-2015-0010-0001_content.pdf
            │   ├── USTR-2015-0010-0001_content_pdfplumber_extracted.txt
            │   └── USTR-2015-0010-0001_content_pypdf_extracted.txt
            ├── USTR-2015-0010-0015
            │   └── USTR-2015-0010-0015.json
            ├── USTR-2015-0010-0016
            │   ├── USTR-2015-0010-0016.json
            │   ├── USTR-2015-0010-0016_content.doc
            │   ├── USTR-2015-0010-0016_content.pdf
            │   ├── USTR-2015-0010-0016_content_pdfplumber_extracted.txt
            │   └── USTR-2015-0010-0016_content_pypdf_extracted.txt
            └── USTR-2015-0010-0017
                ├── USTR-2015-0010-0017.json
                ├── USTR-2015-0010-0017_content.doc
                ├── USTR-2015-0010-0017_content.pdf
                ├── USTR-2015-0010-0017_content_pdfplumber_extracted.txt
                └── USTR-2015-0010-0017_content_pypdf_extracted.txt
```
# Explanation

 * This structure conforms to solve the issue with the "None" directories that currently appear in the local data
 * A "None" folder can be in place of a Docket, and can contain documents
 * A "None" folder can also be in place of a Document, which can contain comments
 * If a "None" folder exists at a docket level, we can extract all documents inside of it and place it in the documents directory, and extract the docketId from the document path, and create a docket with the extractedID in the dockets directory.
 	* A documentId could be "USTR-2015-0010-0001", and we can assume from that path that the docketID would be "USTR-2015-0010", which removes the document idenifier of "0001"
 * "Data" would be the root folder that contains the data
 	* There will be 3 main directories, which are "dockets", "documents", and "comments"
 		* An agency will follow, and in this example, is represented by "USTR"
 		* A docketId follows after an agency such as "USTR-2015-0010", which indicates the docket a docket.json/document.json/comment/json is linked to
 		* Inside of a dockets directory, a path such as "USTR-2015-0010" exists, which contains each dockets json
 		* Inside of a documents directory, a path such as "USTR-2015-0010-0001" represents a document of docket "USTR-2015-0010"
 			* Inside of "USTR-2015-0010-0001", all of the information of that document is included, such as the json of that document, the transcript of the document, and extracted text of that document's transcript
			* Inside of the documents json, there is a pointer inside such as "docketId": "USTR-2015-0010", which points to the docket-ID that the document is linked to, which is contained under the "dockets" directory.
		* Inside of a comments directory, a path such as "USTR-2015-0010-0002" represents a comment of docket "USTR-2015-0010"
		* inside of "USTR-2015-0010-0002", all of the correlated files to a comment is contained, such as the comments json, the various attachments a comment has, and the extracted text of the attachments
		* Inside of the comments json, a pointer is included to the document that the comment originates from, such as "commentOnDocumentId": "USTR-2015-0010-0001", which would point to the documents directory and link to the document with the id "USTR-2015-0010-0001"
			* A pointer to the docket that a comment is linked to is included inside of the comments json as well, such as "docketId": "USTR-2015-0010", which points to that docketId inside of the dockets directory

