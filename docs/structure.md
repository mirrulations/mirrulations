# Proposed S3 Version 

## Raw Data Structure Overview 

- raw-data
  └── <agency>
      └── <docket id>
          ├── binary-<docket id>
          │   ├── comments_attachments
          │   │   ├── <comment id>_attachment_<counter>.<extension>
          │   │   └── ...
          │   ├── documents_attachments
          │   │   ├── <document id>_attachment_<counter>.<extension>
          │   │   └── ...
          └── text-<docket id>
              ├── comments
              │   ├── <comment id>.json
              │   └── ...
              ├── docket
              │   ├── <docket id>.json
              │   └── ...
              ├── documents
              │   ├── <document id>.json
              │   ├── <document id>_content.htm
              │   └── ...


## Overall S3 Structure Overview


-       Mirrulations
            ├── derived-data
            │   └── agency
            │       └── docketID
            │           ├── MoravianResearch
            │           │   └── projectName
            │           │       ├── comment
            │           │       ├── docket
            │           │       └── document
            │           ├── mirrulations
            │           │   ├── ai_summary
            │           │   │   ├── comment
            │           │   │   ├── comment_attachments
            │           │   │   └── document
            │           │   ├── entities
            │           │   │   ├── comment
            │           │   │   ├── comment_attachment
            │           │   │   └── document
            │           │   └── extracted_txt
            │           │       └── comment_attachment
            │           │           └── commentID_attachment.txt
            │           └── trotterf
            │               └── projectName
            │                   └── fileType
            │                       └── fileID.txt
            └── raw-data
                └── old_structure_minus_extracted_txt


## Explanation of Raw Data Structure

### **Level 1: `raw-data`**
- **Description**: The top-level directory that contains all raw data files.
- **Purpose**: Serves as the root directory for organizing data by agency and docket.

---

### **Level 2: `<agency>`**
- **Description**: Subdirectories under `raw-data` represent the government agency responsible for the data.
- **Example**: `EPA`, `FDA`, `USTR`.

---

### **Level 3: `<docket id>`**
- **Description**: Each agency directory contains subdirectories named after the docket IDs. A docket ID uniquely identifies a docket and its associated data.
- **Example**: `EPA-HQ-OPP-2011-0939`, `FDA-2017-D-2335`.

---

### **Level 4: `binary-<docket id>`**
- **Description**: This directory contains binary files (e.g., attachments) associated with the docket.
- **Subdirectories**:
  - **`comments_attachments`**:
    - Contains attachments related to comments.
    - **File Naming Convention**: `<comment id>_attachment_<counter>.<extension>`.
    - **Example**: `FDA-2017-D-2335-1566_attachment_1.pdf`.
  - **`documents_attachments`**:
    - Contains attachments related to documents.
    - **File Naming Convention**: `<document id>_attachment_<counter>.<extension>`.
    - **Example**: `FDA-2017-D-2335-0001_attachment_2.docx`.

---

### **Level 4: `text-<docket id>`**
- **Description**: This directory contains text-based files (e.g., JSON files) associated with the docket.
- **Subdirectories**:
  - **`comments`**:
    - Contains JSON files representing individual comments.
    - **File Naming Convention**: `<comment id>.json`.
    - **Example**: `FDA-2017-D-2335-1566.json`.
  - **`docket`**:
    - Contains JSON files representing the docket itself.
    - **File Naming Convention**: `<docket id>.json`.
    - **Example**: `FDA-2017-D-2335.json`.
  - **`documents`**:
    - Contains JSON files representing individual documents and their content.
    - **File Naming Convention**:
      - `<document id>.json`: Metadata for the document.
      - `<document id>_content.htm`: HTML content of the document.
    - **Examples**:
      - `FDA-2017-D-2335-0001.json`.
      - `FDA-2017-D-2335-0001_content.htm`.

---

## **Summary of Raw Data Structure**

### **Key Points**:
1. **Agency-Level Organization**:
   - Data is grouped by the agency responsible for the docket.
2. **Docket-Level Organization**:
   - Each docket has its own directory, ensuring that all related files are stored together.
3. **Binary and Text Separation**:
   - Binary files (e.g., attachments) are stored in the `binary-<docket id>` directory.
   - Text-based files (e.g., JSON and HTML) are stored in the `text-<docket id>` directory.
4. **File Naming Conventions**:
   - Files are named systematically to ensure uniqueness and easy identification.


## Explanation of Derived Data Structure

### **Level 1: `derived-data`**
- **Description**: The top-level directory that contains all derived data files.
- **Purpose**: Serves as the root directory for organizing data by agency and docket.

### **Level 2: `<agency>`**
- **Description**: Subdirectories under `derived-data` represent the government agency responsible for the data.
- **Purpose**: `EPA`, `FDA`, `USTR`.

### **Level 3: `<docket id>`**
- **Description**: Each agency directory contains subdirectories named after the docket IDs. A docket ID uniquely identifies a docket and its associated data.
- **Purpose**: `EPA-HQ-OPP-2011-0939`, `FDA-2017-D-2335`.

### **Level 4: `<organization>`**
- **Description**: Each docket-id directory contains subdirectories named after certain organizations. A organization uniquely identifies the associated data with that organization.
- **Purpose**: `mirrulations`, `MoravianResearch`.

### **Level 5: `<organization data>`**
- **Description**: Each docket-id directory contains subdirectories named after certain organizations. A organization uniquely identifies the associated derived data with that organization.
- **Purpose**: `ai_summary`, `entities`.