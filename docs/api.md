## ***API Documentation***

### **What a Job is**

A job is: {`job_id`, `call_url`}

`job_id` is an integer, mostly for the work server to use to manage jobs.

`call_url` is a URL for the client to call. This will generally be in the format of:
`https://api.regulations.gov/v4/END_POINT/ITEM_ID`

Where `END_POINT` would be either "dockets", "documents", or "comments", specifying which endpoint to retrieve an item from.
`ITEM_ID` is the specific thing to retrieve, whether a docket, document, or comment, and generally looks like this: `FMCSA-1997-2350-2476`.

Within the code we can represent this with a python dictionary. We can easily convert said dictionary into a string with the JSON library for transferring between parts of our implementation.
	
### **How to receive all data**

To iterate through the first 5,000 items, we first iterate through a maximum of 250 items per page, for a total of 20 pages per grouping which gives us a total of 5,000 items.
We then note the last item’s last modified date down to the second.
Then iterate through the next 5,000 items starting with the last item previously mentioned as the parameter to filter items after the parameter noted. Repeat. We are sorting by the last modified date.

The syntax for a single call to actually do this is as follows:
```
https://api.regulations.gov/v4/END_POINT?page[size]=250&page[number]=PAGE_NUMBER&sort=lastModifiedDate,documentId&api_key=API_KEY ,
```
where `END_POINT`, `PAGE_NUMBER`, and `API_KEY` are variables you put in. The max value for the page number is 20. Since each page only holds 250 items, you would only be able to get 5000 items with this format.

Once you hit those 5000 items, you'll need to add the last modified date filter, using the oldest (last) date in the set of 5000:
`filter[lastModifiedDate][ge]=2020-08-10 11:58:52 `

To basically cut off the first 5000 items you got and then continue the same way from there.

```
Added onto the first example URL/call:
https://api.regulations.gov/v4/END_POINT?filter[lastModifiedDate][ge]=2020-08-10 11:58:52&page[size]=250&page[number]=PAGE_NUMBER&sort=lastModifiedDate,documentId&api_key=API_KEY
```

### **What the client should do**
While the above section describes how to generate all jobs, the client will do the actual work for each job. 

The client will get a job from regulations.gov, process the job URL, and finally downloads the job.

Additionally, if a document/comment is being retrieved, the client will get their respective attachments alongside the document/comment. These can be identified in the JSON given under data/attributes/fileFormats.

### **Job Generator Endpoints**
***Three job generating endpoints***

Dockets - Parent of Documents

Documents - Parent of Comments

Comments - Child of Documents

### **Check data overlaps between endpoints**
*Comments* - Missing fields in detailed view for comments `lastModifiedDate` and `highlightedContent`

*Documents* - Missing fields in detailed view for Documents `lastModifiedDate` and `highlightedContent`

*Dockets* - Missing fields in detailed view for Dockets `lastModifiedDate` and `highlightedContent`

***Additional Notes***
`lastModifiedDate` and `modifyDate` have the same values. Non-detailed view for all types have `modifyDate` instead of `lastModifiedDate`
