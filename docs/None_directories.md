# Problem: None Directories
 
 There is a bug in the system that is creating `None` directories instead of Docket/Document/Comment directories which is resulting in downloaded items not being stored in an appropriate place

 - Through our initial investigation this problem is arising from the work server.  

 - We found in  `client.py` that if a certain key is not found it returns a creates `None` directories in an `agencyID` directory or in an `docketID` directory

Below represents a few cases where the current directory is `/data/data `

We found minimally 130 other cases similiar to below.
 ```
./TRADE/None
./BBG/None
./RISC/None
./LSC/None
./NEC/None
./ARCTIC/None
./NCPC/None
./NPREC/None
./CCJJDP/None
./MISS/None
./GAO/None
./DIA/None
./PRC/None
./ACFR/None
./NHTSA/NHTSA-2002-13986/None
 ```


- In investigating this bug we found a few different reasons why this is occuring.  Likely due to malformed json responses. Where `null` values are found

## 1. No  `commentOnDocumentID` field creates None Directory
In the returned JSON using the regulations.gov `/comments` api endoint a comment does not have a value for the `commentOnDocumentId` field 

JSON was found at this directory 
 
```
/data/data/NHTSA/NHTSA-2002-13986/None/NHTSA-2002-13986-0001
```
 Example from `NHTSA-2002-13986-0001.json` from a None directory: 



```
{
  "data" : {
    "id" : "NHTSA-2002-13986-0001",
    "type" : "comments",
    "links" : {
      "self" : "https://api.regulations.gov/v4/comments/NHTSA-2002-13986-0001"
    },
    "attributes" : {
      "commentOn" : null,
      "commentOnDocumentId" : null,
      "duplicateComments" : 0,
      "address1" : "Office of Vehicle Safety Compliance",
      "address2" : null,
      "agencyId" : "NHTSA",
      "city" : null,
      "category" : null,
      "comment" : "This document announces decisions by NHTSA",
      "country" : null,
      "displayProperties" : [ {
        "name" : "postmarkDate",
        "label" : "Answer Date",
        "tooltip" : "Date the document was postmarked"
      } ],
      "docAbstract" : null,
      "docketId" : "NHTSA-2002-13986",
```

- I visited this commentID using regulations.gov website and found that this comment was made directly on a docket.  
- Notice that this comment does not have a value for commentOnDocumentID but it does have a docketID value

- The ability to comment directly on a docket is something we have not accounted for in our code

### Possible Fixes:
- Have work_server check for the documentID and if that does not exist/ is None then add the comment to the Docket Folder

---

## 2. No `DocketID` associated with Document Creates `None` Directory
In the returned JSON using the regulations.gov `/documents` api endoint the following document does not have a value for the `docketID` field

For this case, the document has no Docket associated with it, so there is an extra `None` folder created

Here is the link to the document on regulations.gov
 https://www.regulations.gov/document/TRADE-2015-0001-0001

```
/data/data/TRADE/None/TRADE-2015-0001-0001/TRADE-2015-0001-0001.json
```

