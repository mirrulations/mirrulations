# JSON Example
Example of how data is saved for the following: Dockets, Documents, and Comments.

## Dockets
This collection contains the dockets filed by the court. This collection is nested with multiple dictionaries. Below is an example of a docket: 

```
{
    _id: ObjectId("610d93fe346bee7cb5e849eb"),
    data: {
      id: 'NCUA-2021-0112',
      type: 'dockets',
      attributes: {
        displayProperties: [
          {
            name: 'effectiveDate',
            label: 'Effective Date',
            tooltip: 'Date of Vote'
          },
          {
            name: 'abstract',
            label: 'Description',
            tooltip: "Describes an agency's specific regulatory action; equivalents: Abstract, Docket Subject, General Info, Related To, Summary."
          }
        ],
        keywords: null,
        modifyDate: '2021-08-06T14:57:23Z',
        dkAbstract: 'Proposed Merger of Northland Community Credit Union located in Gladstone, MO with and into CSD Credit Union located in Kansas City, MO.  If you decide to submit comments, you are attesting to NCUA that you are a current member or are part of the management team of the proposed merging credit union.  Your name will be posted with your comments.  Please do not include any personally identifiable information in your comments or attachments.  We will post only information entered in the comments section, not attachments. ',
        agencyId: 'NCUA',
        program: null,
        shortTitle: null,
        subType2: null,
        title: 'Proposed Merger of Northland Community Credit Union located in Gladstone, MO with and into CSD Credit Union located in Kansas City, MO.',
        generic: null,
        field1: null,
        docketType: 'Nonrulemaking',
        petitionNbr: null,
        rin: null,
        organization: null,
        legacyId: null,
        subType: null,
        category: null,
        field2: null,
        effectiveDate: '2021-09-22T04:00:00Z',
        objectId: '0b00006484c3224e'
      },
      links: { self: 'https://api.regulations.gov/v4/dockets/NCUA-2021-0112' }
    }
  }

```


## Documents
This JSON contains the documents associated with dockets. This collection is nested with multiple dictionaries.  
Below is an example of a document: 

```
{
    _id: ObjectId("60d34ea4980dae7064c3ff27"),
    data: {
      id: 'EPA-HQ-OA-2003-0003-0003',
      type: 'documents',
      links: {
        self: 'https://api.regulations.gov/v4/documents/EPA-HQ-OA-2003-0003-0003'
      },
      attributes: {
        additionalRins: null,
        allowLateComments: false,
        authorDate: '2003-02-24T05:00:00Z',
        authors: null,
        cfrPart: null,
        commentEndDate: null,
        commentStartDate: null,
        effectiveDate: null,
        exhibitLocation: null,
        exhibitType: null,
        frDocNum: null,
        frVolNum: null,
        implementationDate: null,
        media: 'ELECTRONIC FILE',
        ombApproval: null,
        paperLength: 0,
        paperWidth: 0,
        regWriterInstruction: null,
        sourceCitation: null,
        startEndPage: null,
        subject: null,
        topics: null,
        address1: null,
        address2: null,
        agencyId: 'EPA',
        city: null,
        category: null,
        comment: null,
        country: null,
        displayProperties: [
          {
            name: 'pageCount',
            label: 'Page Count',
            tooltip: 'Number of pages In the content file'
          }
        ],
        docAbstract: 'Supporting Statement for ICR No.  0277.08, OMB No. 2090-0014',
        docketId: 'EPA-HQ-OA-2003-0003',
        documentType: 'Supporting & Related Material',
        email: null,
        fax: null,
        field1: null,
        field2: null,
        fileFormats: [
          {
            fileUrl: 'https://downloads.regulations.gov/EPA-HQ-OA-2003-0003-0003/content.pdf',
            format: 'pdf',
            size: 38531
          },
          {
            fileUrl: 'https://downloads.regulations.gov/EPA-HQ-OA-2003-0003-0003/content.txt',
            format: 'txt',
            size: 14180
          }
        ],
        firstName: null,
        govAgency: null,
        govAgencyType: null,
        objectId: '09000064800ad408',
        lastName: null,
        legacyId: null,
        modifyDate: '2006-09-02T12:28:49Z',
        organization: null,
        originalDocumentId: '',
        pageCount: 2,
        phone: null,
        postedDate: '2003-02-24T05:00:00Z',
        postmarkDate: null,
        reasonWithdrawn: null,
        receiveDate: '2003-02-24T05:00:00Z',
        restrictReason: null,
        restrictReasonType: null,
        stateProvinceRegion: null,
        submitterRep: null,
        submitterRepAddress: null,
        submitterRepCityState: null,
        subtype: 'Other',
        title: 'Supporting Statement for ICR No. 0275.08 OMB No. 2090-0014',
        trackingNbr: '800ad408',
        withdrawn: false,
        zip: null,
        openForComment: false
      },
      relationships: {
        attachments: {
          links: {
            self: 'https://api.regulations.gov/v4/documents/EPA-HQ-OA-2003-0003-0003/relationships/attachments',
            related: 'https://api.regulations.gov/v4/documents/EPA-HQ-OA-2003-0003-0003/attachments'
          }
        }
      }
    }
  }

```

## Comments 
This JSON contains the comments made on documents. It is nested with multiple dictionaries. Below is an example of a comment: 

```
{
  _id: ObjectId(“60d56e18e0bd631edd99e668”),
  data: {
   id: ‘EPA-HQ-OECA-2004-0024-0048’,
   type: ‘comments’,
   links: {
    self: ‘https://api.regulations.gov/v4/comments/EPA-HQ-OECA-2004-0024-0048’
   },
   attributes: {
    commentOn: ‘09000064800b858d’,
    commentOnDocumentId: null,
    duplicateComments: 1,
    address1: null,
    address2: null,
    agencyId: ‘EPA’,
    city: null,
    category: null,
    comment: null,
    country: null,
    displayProperties: [
     {
      name: ‘pageCount’,
      label: ‘Page Count’,
      tooltip: ‘Number of pages In the content file’
     }
    ],
    docAbstract: null,
    docketId: ‘EPA-HQ-OECA-2004-0024’,
    documentType: ‘Public Submission’,
    email: null,
    fax: null,
    field1: null,
    field2: null,
    fileFormats: null,
    firstName: null,
    govAgency: null,
    govAgencyType: null,
    objectId: ‘09000064800b8954’,
    lastName: null,
    legacyId: null,
    modifyDate: ‘2006-09-02T12:39:21Z’,
    organization: null,
    originalDocumentId: ‘’,
    pageCount: 3,
    phone: null,
    postedDate: ‘2005-03-07T05:00:00Z’,
    postmarkDate: ‘2005-03-07T05:00:00Z’,
    reasonWithdrawn: null,
    receiveDate: ‘2005-03-07T05:00:00Z’,
    restrictReason: null,
    restrictReasonType: null,
    stateProvinceRegion: null,
    submitterRep: null,
    submitterRepAddress: null,
    submitterRepCityState: null,
    subtype: ‘Public Comment’,
    title: ‘Comment submitted by Karen M. Jayne, Environmental Attorney, Oklahoma State Department of Environmental Quality ’,
    trackingNbr: ‘800b8954’,
    withdrawn: false,
    zip: null,
    openForComment: false
   },
   relationships: {
    attachments: {
     links: {
      self: ‘https://api.regulations.gov/v4/comments/EPA-HQ-OECA-2004-0024-0048/relationships/attachments’,
      related: ‘https://api.regulations.gov/v4/comments/EPA-HQ-OECA-2004-0024-0048/attachments’
     }
    }
   }
  }
 }

```
