# Problem: None Directories
 
 There is a bug in the system that is creating `None` directories instead of Docket/Document/Comment directories which is resulting in downloaded items not being stored in an appropriate place

 - Through our initial investigation this problem is arising from the the client.  

 - We found in  `client.py` that if a certain key (such as commentOnDocumentID, docketID) is found with a value of `null` the client will create a `None` directory.

Below represents a few cases of this where the current directory is `/data/data `

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


- In investigating this bug we found a few different reasons why this is occuring.  Likely due to rare json value occurences. Where `null` values are found.

## 1. No  `commentOnDocumentID` field creates `None` Directory for a comment
This case is where a comment is made directly on a docket

In the returned JSON using the regulations.gov `/comments` api endoint a comment has a `null` value for the `commentOnDocumentId` field 

However there is a docket associated with the comment


```
"commentOnDocumentID" : null
"docketId" : "NHTSA-2002-13986"
```



JSON for this comment was found at this file path
 
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

- Using `www.regulations.gov` search tool I searched for the comment [NHTSA-2002-13986-0001](https://www.regulations.gov/comment/NHTSA-2002-13986-0001) and found that this comment was made directly on a docket.


- The ability to comment directly on a docket is something we have not accounted for other than by assigning directory names as `None`

### Possible Fixes:
- Have client check for the commentOnDocumentID key and if that value is `null` then check for a docketID key and add the comment to the docketID directory directly, rather than the extra None dir in between.

---

## 2. No `DocketID` associated with Document Creates `None` Directory
In the returned JSON using the regulations.gov `/documents` api endoint the following document has a `null` value for the `docketID` field

For this case, the Document has no `docketID` value as it is `null` so there is an extra `None` folder created

```
"docketId": null
```

*JSON for this example was found at this file path*
```
/data/data/TRADE/None/TRADE-2015-0001-0001/TRADE-2015-0001-0001.json
```


Here is the link to the document on regulations.gov
 https://www.regulations.gov/document/TRADE-2015-0001-0001



*Below is the returned json from the regulations api*

```
{
  "data" : {
    "id" : "TRADE-2015-0001-0001",
    "type" : "documents",
    "links" : {
      "self" : "https://api.regulations.gov/v4/documents/TRADE-2015-0001-0001"
    },
    "attributes" : {
      "additionalRins" : null,
      "allowLateComments" : false,
      "authorDate" : null,
      "authors" : null,
      "cfrPart" : null,
      "commentEndDate" : "2015-07-03T03:59:59Z",
      "commentStartDate" : "2015-06-02T04:00:00Z",
      "effectiveDate" : null,
      "exhibitLocation" : null,
      "exhibitType" : null,
      "frDocNum" : "2015-13166",
      "frVolNum" : null,
      "implementationDate" : null,
      "media" : null,
      "ombApproval" : null,
      "paperLength" : 0,
      "paperWidth" : 0,
      "regWriterInstruction" : null,
      "sourceCitation" : null,
      "startEndPage" : null,
      "subject" : null,
      "topics" : [ "Privacy" ],
      "address1" : null,
      "address2" : null,
      "agencyId" : "TRADE",
      "city" : null,
      "category" : null,
      "comment" : null,
      "country" : null,
      "displayProperties" : null,
      "docAbstract" : null,
      "docketId" : null,

    },
    "relationships" : {
      "attachments" : {
        "links" : {
          "self" : "https://api.regulations.gov/v4/documents/TRADE-2015-0001-0001/relationships/attachments",
          "related" : "https://api.regulations.gov/v4/documents/TRADE-2015-0001-0001/attachments"
        }
      }
    }
  }
}
```






