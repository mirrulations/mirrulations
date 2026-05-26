# Attachments

> **Note:** This page mixes historical notes with older path and storage ideas. For the **current** on-disk and S3 layout (including **comment attachments** and **`_UNAVAILABLE` tombstones** when a download is non-OK), use **[structure.md](structure.md)** and the download **client** docs (**[client.md](client.md)**).

## Downloading Attachments

1. Attachments are found in a single comments json data
    -  comment["data"]["relationships"]["attachments"]["links"]["related"]
2. In order to visit this link we have to use another api call to access the download links for the attachments
3. From this related link we then must iterate over the list of files attached to the comment

Example Link: 

    https://api.regulations.gov/v4/comments/CMS-2022-0012-0001/attachments?api_key=<API_KEY>

4. The work generator will then push the link found through this process as an attachment job. Jobs are then pushed to the job_waiting_queue in Redis.

5. Our clients will then download each file to disk, as well as create an entry for the attachment in mongodb


---

## Attachments Storage
- Attachments are being stored on disk under their respective Agency Name Abbreviation and by commentID. These files are encoded in `b64encoding` in order for us to pass the file through our work servers http message.


*Breakdown of attachment path* in the data directory:

    <AgencyID>/<CommentID>/<job_id>.<file_type>


Example attachment path: 

    OSHA/OSHA-H371-2006-0932-0879/22899605_0.pdf



---
## Attachments by File Type
Current Attachment Count: 207.9k

The following summary of file types is based on the current sample of attachments we have in mongo 


The script to generate this table can be found in the **cs334s23** organization: [attachment_types.py](https://github.com/cs334s23mirrulations_attachments_exploration/blob/main/src/attachment_types.py)


File Types include: 

    bmp, docx, gif, jpg, jpeg, pdf, png, pptx, rtf, sgml, tif, tiff, txt, wpd, xlsx, xml

**As the table below indicates ~95% of the attachments are `.pdf` or `.docx`**

| File Type     | Count |
| ----------- | ----------- |
| .pdf      | 176672       |
| .docx   | 18676       |
| .jpg      | 5803      |
| .png   | 2705        |
| .xlsx  | 819       |
| .txt     | 559       |
| .tif   | 467        |
| .doc   | 262        |
| .rtf      | 214      |
| .pptx   | 80       |
| .wpd      |37       |
| .gif   | 28       |
| .bmp   | 10       |
| .htm, .wav, .zip , .ppt  | <10   |

