## Data Design Example:

```json
{
  "comments": [
    {
      "id": 1,
      "text": "comment",
      "attachments": [
        {
          "id": 1,
          "url": "https://example.com/attachment1.pdf",
          "type": "pdf",
	  "extracted_text": "text extracted from attachment 1" 
        },
        {
          "id": 2,
          "url": "https://example.com/attachment2.jpeg",
          "type": "image",
	  "extracted_text": ""
        },
      ]
  ]
}
```
