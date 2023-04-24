# Regulations Storage on Disk

## General Description
  The format of the Regulations API is split up into `agencies`, `dockets`, `documents`, `comments`

* **Agency**
    * **Dockets**
        * Docket Description 
            * Stored as JSON
        * **Documents**
            * Attachments
                * PDF
                * HTM
            * **Comments**
                * Attachments

* **Agency**

There is a finite number of agencies within the Regulations.gov api. Within a single agency there is a number of dockets, then within a docket there is a number of documents. Some of these documents will then have comments.

 * **Dockets**  

Within each single docket there exists a description for the specific docket that is stored as a JSON. EAch docket has its specific set of attributes that varies based on the specific Agency posting the docket.

* **Documents**

Within a single Docket there exist a finite number of documents. A single document is defined by one of the following: Proposed Rule, Rule, Supporting and Related, or Other. One can choose to include attachments using include parameter. These attachments could be PDF's or HTM. Attachments are not included by default. 

* **Comments**

Comments are found within a single document and there are a few ways one can query comments endpoints so that one can retrieve detailed information for a comment. Comments can be attachments for the specific documents. One could get comment details without attachments or with attachments and this relies on the end point one uses.
