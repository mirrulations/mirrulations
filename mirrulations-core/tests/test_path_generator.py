from mirrcore.path_generator import PathGenerator
from pytest import fixture
import pytest
import json

@fixture(name='generator')
def path_generator():
    return PathGenerator()
    

def get_test_docket():
    return {
        "data":{
        "id": "USTR-2015-0010",
        "type": "dockets", 
        "attributes": {
                    "agencyId":"USTR",
                    "docketId":"USTR-2015-0010"
                }
        }}

def get_test_document():
    return {
        "data":{
        "id": "USTR-2015-0010-0015",
        "type": "documents", 
        "attributes": {
                    "agencyId":"USTR",
                    "docketId":"USTR-2015-0010"
                }
        }}

def get_test_comment():
    return {
        "data":{
        "id": "USTR-2015-0010-0002",
        "type": "comments", 
        "attributes": {
                    "agencyId":"USTR",
                    "docketId":"USTR-2015-0010"
                }
        }}

def generate_json(id=str, type=str, agencyId=str, docketId=None) -> dict:
    # returns a json in the form that regulations.gov api stores data
    return {
        "data":{
        "id": id,
        "type": type, 
        "attributes": {
                    "agencyId": agencyId,
                    "docketId": docketId
                }
        }}


def test_get_comment_attributes(generator):
    agencyId, docket_id, item_id = generator.get_attributes(get_test_comment())
    assert "USTR-2015-0010-0002" == item_id
    assert "USTR-2015-0010" == docket_id
    assert "USTR" == agencyId


def test_get_document_attributes(generator):
    agencyId, docket_id, item_id = generator.get_attributes(get_test_document())
    assert "USTR-2015-0010-0015" == item_id
    assert "USTR-2015-0010" == docket_id
    assert "USTR" == agencyId

def test_get_docket_attributes(generator):
    agencyId, docket_id, item_id = generator.get_attributes(get_test_docket())
    assert "USTR-2015-0010" == item_id
    assert "USTR-2015-0010" == docket_id
    assert "USTR" == agencyId



## Docket Tests

def test_get_docket_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/docket/USTR-2015-0010.json"
    assert expected_path == generator.get_docket_json_path(get_test_docket())

def test_get_path_returns_valid_corpus_type_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/docket/USTR-2015-0010.json"
    assert expected_path == generator.get_path(get_test_docket())

def test_get_docket_path_with_numbers_in_agencyId(generator):
    json = generate_json(id = "EPA-R08-OAR-2005-UT-0003", type="dockets", agencyId="EPA", docketId="EPA-R08-OAR-2005-UT-0003")
    expected_path = "/data/data/EPA/EPA-R08-OAR-2005-UT-0003/text-EPA-R08-OAR-2005-UT-0003/docket/EPA-R08-OAR-2005-UT-0003.json"
    assert expected_path == generator.get_docket_json_path(json)

def test_get_docket_path_EPA_with_unconventional_agencyId(generator):
    json = generate_json(id = "EPA-HQ-OPP-2011-0939", type="dockets", agencyId="EPA")
    expected_path = "/data/data/EPA/EPA-HQ-OPP-2011-0939/text-EPA-HQ-OPP-2011-0939/docket/EPA-HQ-OPP-2011-0939.json"
    assert expected_path == generator.get_docket_json_path(json)

def test_get_docket_path_from_FRDOC_docket(generator):
    json = generate_json(id="VETS_FRDOC_0001", type="dockets", agencyId = "VETS", docketId="VETS_FRDOC_0001")
    expected_path = "/data/data/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/docket/VETS_FRDOC_0001.json"
    assert expected_path == generator.get_docket_json_path(json)

def test_get_docket_path_with_missing_id_key_but_has_agency_id_key(generator):
    json = {"data":{
        "type":"dockets",
        "attributes": {
            "agencyId":"VETS",
        }
    }}
    expected_path = "/data/data/VETS/unknown/text-unknown/docket/unknown.json"
    assert expected_path == generator.get_docket_json_path(json)

def test_get_docket_path_with_missing_agency_id_and_missing_id_keys(generator):
    json = {"data":{
        "type":"dockets",
        "attributes": {
        }
    }}
    expected_path = "/data/data/unknown/unknown/text-unknown/docket/unknown.json"
    assert expected_path == generator.get_docket_json_path(json)



## Documents 

def test_get_document_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/USTR-2015-0010-0015.json"
    assert expected_path == generator.get_document_json_path(get_test_document())

def test_get_path_on_document_returns_valid_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/USTR-2015-0010-0015.json"
    assert expected_path == generator.get_path(get_test_document())

def test_get_document_path_EPA_with_unconventional_agencyId(generator):
    json = generate_json(id = "EPA-HQ-OPP-2011-0939-0001", type="documents", agencyId="EPA", docketId="EPA-HQ-OPP-2011-0939")
    expected_path = "/data/data/EPA/EPA-HQ-OPP-2011-0939/text-EPA-HQ-OPP-2011-0939/documents/EPA-HQ-OPP-2011-0939-0001.json"
    assert expected_path == generator.get_document_json_path(json)

def test_get_document_path_without_docket_id_key(generator):
    json = generate_json(id = "USTR-2015-0001-0001", type="documents", agencyId="USTR")
    expected_path = "/data/data/USTR/USTR-2015-0001/text-USTR-2015-0001/documents/USTR-2015-0001-0001.json"
    assert expected_path == generator.get_document_json_path(json)

def test_get_document_path_full_json(generator):
    json_file = '{"data": {"attributes": {"additionalRins": null, "address1": null, "address2": null, "agencyId": "USTR", "allowLateComments": false, "authorDate": null, "authors": null, "category": null, "cfrPart": null, "city": null, "comment": null, "commentEndDate": null, "commentStartDate": null, "country": null, "displayProperties": null, "docAbstract": null, "docketId": "USTR-2015-0010", "documentType": "Supporting & Related Material", "effectiveDate": null, "email": null, "exhibitLocation": null, "exhibitType": null, "fax": null, "field1": null, "field2": null, "fileFormats": null, "firstName": null, "frDocNum": null, "frVolNum": null, "govAgency": null, "govAgencyType": null, "implementationDate": null, "lastName": null, "legacyId": null, "media": null, "modifyDate": "2015-10-09T15:59:17Z", "objectId": "0900006481cb1d8f", "ombApproval": null, "openForComment": false, "organization": null, "originalDocumentId": null, "pageCount": 0, "paperLength": 0, "paperWidth": 0, "phone": null, "postedDate": "2015-10-05T00:00:00Z", "postmarkDate": null, "reasonWithdrawn": "Upddate to agenda", "receiveDate": null, "regWriterInstruction": null, "restrictReason": null, "restrictReasonType": null, "sourceCitation": null, "startEndPage": null, "stateProvinceRegion": null, "subject": null, "submitterRep": null, "submitterRepAddress": null, "submitterRepCityState": null, "subtype": null, "title": "China Public Hearing Agenda", "topics": null, "trackingNbr": null, "withdrawn": true, "zip": null}, "id": "USTR-2015-0010-0015", "links": {"self": "https://api.regulations.gov/v4/documents/USTR-2015-0010-0015"}, "relationships": {"attachments": {"links": {"related": "https://api.regulations.gov/v4/documents/USTR-2015-0010-0015/attachments", "self": "https://api.regulations.gov/v4/documents/USTR-2015-0010-0015/relationships/attachments"}}}, "type": "documents"}}'
    json_file = json.loads(json_file)
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/documents/USTR-2015-0010-0015.json"
    assert expected_path == generator.get_document_json_path(json_file)

def test_get_document_path_from_FRDOC_document(generator):
    json = generate_json(id="VETS_FRDOC_0001-0001", type="documents", agencyId = "VETS", docketId="VETS_FRDOC_0001")
    expected_path = "/data/data/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/documents/VETS_FRDOC_0001-0001.json"
    assert expected_path == generator.get_document_json_path(json)

def test_get_FRDOC_document_path_without_docket_id_key(generator):
    json = generate_json(id = "VETS_FRDOC_0001-0021", type="documents", agencyId="VETS")
    expected_path = "/data/data/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/documents/VETS_FRDOC_0001-0021.json"
    assert expected_path == generator.get_document_json_path(json)

def test_get_document_path_with_missing_id_key_but_has_agencyID(generator):
    json = {"data":{
        "type":"documents",
        "attributes": {
                    "agencyId":"VETS",
                }
        }}
    expected_path = "/data/data/VETS/unknown/text-unknown/documents/unknown.json"
    assert expected_path == generator.get_document_json_path(json)
    
def test_get_document_path_with_missing_docketId_key(generator):
    json = {"data":{
        "id": "VETS-2010-0001-0011",
        "type":"document",
        "attributes": {
                    "agencyId":"VETS",
                }
        }}
    # Here we must parse the id
    expected_path = "/data/data/VETS/VETS-2010-0001/text-VETS-2010-0001/documents/VETS-2010-0001-0011.json"
    assert expected_path == generator.get_document_json_path(json)

def test_get_document_path_with_missing_agencyId_key(generator):
    json = {"data":{
        "id": "VETS-2010-0001-0010",
        "type":"comments",
        "attributes": {
                }
        }}
    expected_path = "/data/data/unknown/VETS-2010-0001/text-VETS-2010-0001/documents/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_document_json_path(json)


## Comments

def test_get_comment_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_comment_json_path(get_test_comment())

def test_get_path_on_comment_returns_valid_comment_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_path(get_test_comment())

def test_get_comment_path_without_docket_id_key(generator):
    json = generate_json(id = "USTR-2015-0001-0002", type="comments", agencyId="USTR")
    expected_path = "/data/data/USTR/USTR-2015-0001/text-USTR-2015-0001/comments/USTR-2015-0001-0002.json"
    assert expected_path == generator.get_comment_json_path(json)

def test_get_comment_path_full_json(generator):
    json_file = '{"data": {"attributes": {"address1": null, "address2": null, "agencyId": "USTR", "category": null, "city": "Washington", "comment": "See attached. ", "commentOn": "0900006481bce624", "commentOnDocumentId": "USTR-2015-0010-0001", "country": "United States", "displayProperties": null, "docAbstract": null, "docketId": "USTR-2015-0010", "documentType": "Public Submission", "duplicateComments": 0, "email": null, "fax": null, "field1": null, "field2": null, "fileFormats": null, "firstName": "Stephanie", "govAgency": null, "govAgencyType": null, "lastName": "Henry", "legacyId": null, "modifyDate": "2015-09-30T20:57:34Z", "objectId": "0900006481c7f7ad", "openForComment": false, "organization": "US-China Business Council", "originalDocumentId": null, "pageCount": 0, "phone": null, "postedDate": "2015-09-30T04:00:00Z", "postmarkDate": null, "reasonWithdrawn": null, "receiveDate": "2015-09-18T04:00:00Z", "restrictReason": null, "restrictReasonType": null, "stateProvinceRegion": "DC", "submitterRep": null, "submitterRepAddress": null, "submitterRepCityState": null, "subtype": null, "title": "US China Business Council", "trackingNbr": "1jz-8l73-5qbv", "withdrawn": false, "zip": null}, "id": "USTR-2015-0010-0002", "links": {"self": "https://api.regulations.gov/v4/comments/USTR-2015-0010-0002"}, "relationships": {"attachments": {"links": {"related": "https://api.regulations.gov/v4/comments/USTR-2015-0010-0002/attachments", "self": "https://api.regulations.gov/v4/comments/USTR-2015-0010-0002/relationships/attachments"}}}, "type": "comments"}}'
    json_file = json.loads(json_file)
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_comment_json_path(json_file)

def test_get_FRDOC_comment_path_without_docket_id_key(generator):
    json = generate_json(id = "CPPBSD_FRDOC_0001-0076", type="comments", agencyId="CPPBSD")
    expected_path = "/data/data/CPPBSD/CPPBSD_FRDOC_0001/text-CPPBSD_FRDOC_0001/comments/CPPBSD_FRDOC_0001-0076.json"
    assert expected_path == generator.get_comment_json_path(json)

def test_get_comment_path_with_missing_id_key_but_has_agencyId_key(generator):
    json = {"data":{
        "type":"comments",
        "attributes": {
                    "agencyId":"VETS",
                }
        }}
    expected_path = "/data/data/VETS/unknown/text-unknown/comments/unknown.json"
    assert expected_path == generator.get_comment_json_path(json)

def test_get_comment_path_with_missing_docketId_key(generator):
    json = {"data":{
        "id": "VETS-2010-0001-0010",
        "type":"comments",
        "attributes": {
                    "agencyId":"VETS",
                }
        }}
    # Parsing
    expected_path = "/data/data/VETS/VETS-2010-0001/text-VETS-2010-0001/comments/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_comment_json_path(json)

def test_get_comment_path_with_missing_agencyId_key(generator):
    json = {"data":{
        "id": "VETS-2010-0001-0010",
        "type":"comments",
        "attributes": {
                }
        }}
    expected_path = "/data/data/unknown/VETS-2010-0001/text-VETS-2010-0001/comments/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_comment_json_path(json)


## Comments Attachments
def test_get_comment_path(generator):
    expected_path = "/data/data/USTR/USTR-2015-0010/binary-USTR-2015-0010/comments_attachments/USTR-2015-0010-0002_attachment_1.pdf"
    assert expected_path == generator.get_comment_attachment_path(get_test_comment(), "attachment_1.pdf")


def test_empty_json_places_json_in_unknown(generator):
    json = dict()
    expected_path = "/data/data/unknown/unknown.json"
    assert expected_path == generator.get_path(json)