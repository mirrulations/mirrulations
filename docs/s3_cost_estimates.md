## DATA UPLOAD

* 1000 objects returned per LIST request
* 20,000,000 objects (~ size of s3://mirrulations)
* $.005 per 1,000 PUT/COPY/POST/LIST requests

20,000,000 objects / 1,000 obj per list = 20,000 PUT requests * .005 = __$100__

* Estimated 10,000,000 attachment files : 10,000 requests * .005 = __$50__

This cost would not be affected by doing this from within AWS (from Lambda for example) because a PUT request always has this cost attached to it, regardless of where it is being performed from. Transfer-in costs are free no matter the size of the data.



## DATA STORAGE

* $.02 per GB stored per Month
* $.02 * 1024 GB = $23.55 per TB per Month

*Assuming ~10,000,000 attachments*

* Approximate 5 - 8 TB of storage:
* $117.75 - $188.40 per month


## DATA DOWNLOAD

$.0004 per 1,000 GET / SELECT requests
20,000,000 objects * $0.0004 = $8.00

($.05 - $.09 per GB) 48 GB (current size of s3://mirrulations) = $4.32 + $8.00 = $12.32

Transfer-out costs $.09 per GB for the first 10 TB per month

* With 1 TB of data and 20 million objects, the cost would be $100.16. 

* With 8 TB of data and 30 million objects, the cost would be $772.83. 

## Text Only Download

Assuming text docs are ~%12 in size compared to their pdfs

* We can assume there will be 1TB of text files
* This costs about $90 to download *not compressed*

Compression should reduce this size by about by ~ 2/3.

* 350 GB * $.09 = $31.50

We would need to do the compression inside AWS and would cost us 