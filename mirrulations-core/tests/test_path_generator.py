from mirrcore.path_generator import PathGenerator
from pytest import fixture


@fixture(name='generator')
def path_generator():
    return PathGenerator()


def get_test_docket():
    return {
        "data": {
            "id": "USTR-2015-0010",
            "type": "dockets",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }}


def get_test_document():
    return {
        "data": {
            "id": "USTR-2015-0010-0015",
            "type": "documents",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }}


def get_test_document_htm():
    return {
        "data": {
            "id": "USTR-2015-0010-0001",
            "type": "documents",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010",
                "fileFormats": [
                    {
                        "fileUrl": "https://downloads.regulations.gov/" +
                                   "USTR-2015-0010-0001/content.pdf",
                        "format": "pdf",
                        "size": 182010
                    },
                    {
                        "fileUrl": "https://downloads.regulations.gov/" +
                                   "USTR-2015-0010-0001/content.htm",
                        "format": "htm",
                        "size": 9709
                    }
                ]
            }
        }
        }


def get_test_comment():
    return {
        "data": {
            "id": "USTR-2015-0010-0002",
            "type": "comments",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010"
            }
        }}


def get_attachment_and_comment():
    link = "https://downloads.regulations.gov/FDA-2017-D-2335-1566/" + \
            "attachment_1.pdf"
    return {
        "data": {
            "id": "FDA-2017-D-2335-1566",
            "type": "comments",
            "attributes": {
                "agencyId": "FDA",
                "docketId": "FDA-2017-D-2335"
            }
        },
        "included": [{
            "attributes": {
                "fileFormats": [{
                    "fileUrl": link
                }]
            }
        }]}


def generate_json(i_d=str, doc_type=str, agency_i_d=str, docket_i_d=None):
    # returns a json in the form that regulations.gov api stores data
    return {
        "data": {
            "id": i_d,
            "type": doc_type,
            "attributes": {
                "agencyId": agency_i_d,
                "docketId": docket_i_d
            }
        }}


def test_get_comment_attributes(generator):
    agency_i_d, docket_i_d, item_i_d = generator \
                                        .get_attributes(get_test_comment())
    assert "USTR-2015-0010-0002" == item_i_d
    assert "USTR-2015-0010" == docket_i_d
    assert "USTR" == agency_i_d


def test_get_document_attributes(generator):
    agency_i_d, docket_i_d, item_i_d = generator \
                                    .get_attributes(get_test_document())
    assert "USTR-2015-0010-0015" == item_i_d
    assert "USTR-2015-0010" == docket_i_d
    assert "USTR" == agency_i_d


def test_get_docket_attributes(generator):
    agency_i_d, docket_i_d, item_i_d = generator \
                                        .get_attributes(get_test_docket())
    assert "USTR-2015-0010" == item_i_d
    assert "USTR-2015-0010" == docket_i_d
    assert "USTR" == agency_i_d


# Docket Tests
def test_get_docket_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "docket/USTR-2015-0010.json"
    assert expected_path == generator.get_docket_json_path(get_test_docket())


def test_get_path_returns_valid_corpus_type_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "docket/USTR-2015-0010.json"
    assert expected_path == generator.get_path(get_test_docket())


def test_get_docket_path_with_numbers_in_agency_i_d(generator):
    json = generate_json(i_d="EPA-R08-OAR-2005-UT-0003",
                         doc_type="dockets",
                         agency_i_d="EPA",
                         docket_i_d="EPA-R08-OAR-2005-UT-0003")
    expected_path = "/EPA/EPA-R08-OAR-2005-UT-0003/" + \
                    "text-EPA-R08-OAR-2005-UT-0003/" + \
                    "docket/EPA-R08-OAR-2005-UT-0003.json"
    assert expected_path == generator.get_docket_json_path(json)


def test_get_docket_path_epa_with_unconventional_agency_i_d(generator):
    json = generate_json(i_d="EPA-HQ-OPP-2011-0939",
                         doc_type="dockets",
                         agency_i_d="EPA")
    expected_path = "/EPA/EPA-HQ-OPP-2011-0939/text-EPA-HQ-OPP-2011-0939/" + \
                    "docket/EPA-HQ-OPP-2011-0939.json"
    assert expected_path == generator.get_docket_json_path(json)


def test_get_docket_path_from_frdoc_docket(generator):
    json = generate_json(i_d="VETS_FRDOC_0001",
                         doc_type="dockets",
                         agency_i_d="VETS",
                         docket_i_d="VETS_FRDOC_0001")
    expected_path = "/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/" + \
                    "docket/VETS_FRDOC_0001.json"
    assert expected_path == generator.get_docket_json_path(json)


def test_get_docket_path_with_missing_id_key_but_has_agency_id_key(generator):
    json = {"data": {
        "type": "dockets",
        "attributes": {
            "agencyId": "VETS",
        }
    }}
    expected_path = "/VETS/unknown/text-unknown/docket/unknown.json"
    assert expected_path == generator.get_docket_json_path(json)


def test_get_docket_path_with_missing_agency_id_and_missing_id_keys(generator):
    json = {"data": {
        "type": "dockets",
        "attributes": {
        }
    }}
    expected_path = "/unknown/unknown/text-unknown/docket/unknown.json"
    assert expected_path == generator.get_docket_json_path(json)


# Documents
def test_get_document_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "documents/USTR-2015-0010-0015.json"
    test_document = get_test_document
    assert expected_path == generator.get_document_json_path(test_document())


def test_get_path_on_document_returns_valid_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "documents/USTR-2015-0010-0015.json"
    assert expected_path == generator.get_path(get_test_document())


def test_get_document_path_epa_with_unconventional_agency_i_d(generator):
    json = generate_json(i_d="EPA-HQ-OPP-2011-0939-0001",
                         doc_type="documents",
                         agency_i_d="EPA",
                         docket_i_d="EPA-HQ-OPP-2011-0939")
    expected_path = "/EPA/EPA-HQ-OPP-2011-0939/text-EPA-HQ-OPP-2011-0939/" + \
                    "documents/EPA-HQ-OPP-2011-0939-0001.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_without_docket_i_d_key(generator):
    json = generate_json(i_d="USTR-2015-0001-0001",
                         doc_type="documents",
                         agency_i_d="USTR")
    expected_path = "/USTR/USTR-2015-0001/text-USTR-2015-0001/" + \
                    "documents/USTR-2015-0001-0001.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_full_json(generator):
    json_file = {
        "data": {
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010",
            },
            "id": "USTR-2015-0010-0015",
            "type": "documents"
        }
    }
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "documents/USTR-2015-0010-0015.json"
    assert expected_path == generator.get_document_json_path(json_file)


def test_get_document_path_from_frdoc_document(generator):
    json = generate_json(i_d="VETS_FRDOC_0001-0001",
                         doc_type="documents",
                         agency_i_d="VETS",
                         docket_i_d="VETS_FRDOC_0001")
    expected_path = "/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/" + \
                    "documents/VETS_FRDOC_0001-0001.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_frdoc_document_path_without_docket_i_d_key(generator):
    json = generate_json(i_d="VETS_FRDOC_0001-0021",
                         doc_type="documents",
                         agency_i_d="VETS")
    expected_path = "/VETS/VETS_FRDOC_0001/text-VETS_FRDOC_0001/" + \
                    "documents/VETS_FRDOC_0001-0021.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_with_missing_id_key_but_has_agency_i_d(generator):
    json = {
        "data": {
            "type": "documents",
            "attributes": {
                "agencyId": "VETS",
            }
        }}
    expected_path = "/VETS/unknown/text-unknown/documents/unknown.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_with_missing_docket_i_d_key(generator):
    json = {
        "data": {
            "id": "VETS-2010-0001-0011",
            "type": "document",
            "attributes": {
                "agencyId": "VETS",
            }
        }}
    # Here we must parse the id
    expected_path = "/VETS/VETS-2010-0001/text-VETS-2010-0001/documents/" + \
                    "VETS-2010-0001-0011.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_with_missing_agency_i_d_key(generator):
    json = {
        "data": {
            "id": "VETS-2010-0001-0010",
            "type": "comments",
            "attributes": {
            }
        }}
    expected_path = "/unknown/VETS-2010-0001/text-VETS-2010-0001/" + \
                    "documents/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_document_json_path(json)


def test_get_document_path_for_htm(generator):
    document = get_test_document_htm()
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "documents/USTR-2015-0010-0001_content.htm"
    assert expected_path == generator.get_document_htm_path(document)


# Comments
def test_get_comment_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_comment_json_path(get_test_comment())


def test_get_path_on_comment_returns_valid_comment_path(generator):
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_path(get_test_comment())


def test_get_comment_path_without_docket_i_d_key(generator):
    json = generate_json(i_d="USTR-2015-0001-0002",
                         doc_type="comments",
                         agency_i_d="USTR")
    expected_path = "/USTR/USTR-2015-0001/text-USTR-2015-0001/" + \
                    "comments/USTR-2015-0001-0002.json"
    assert expected_path == generator.get_comment_json_path(json)


def test_get_comment_path_full_json(generator):
    json_file = {
        "data": {
            "attributes": {
                "agencyId": "USTR",
                "commentOnDocumentId": "USTR-2015-0010-0001",
                "docketId": "USTR-2015-0010"
            },
            "id": "USTR-2015-0010-0002",
            "type": "comments"
        }
        }
    expected_path = "/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "comments/USTR-2015-0010-0002.json"
    assert expected_path == generator.get_comment_json_path(json_file)


def test_get_frdoc_comment_path_without_docket_i_d_key(generator):
    json = generate_json(i_d="CPPBSD_FRDOC_0001-0076",
                         doc_type="comments",
                         agency_i_d="CPPBSD")
    expected_path = "/CPPBSD/CPPBSD_FRDOC_0001/text-CPPBSD_FRDOC_0001/" + \
                    "comments/CPPBSD_FRDOC_0001-0076.json"
    assert expected_path == generator.get_comment_json_path(json)


def test_get_comment_path_with_missing_id_key_but_has_agency_i_d(generator):
    json = {
        "data": {
            "type": "comments",
            "attributes": {
                "agencyId": "VETS",
            }
        }}
    expected_path = "/VETS/unknown/text-unknown/comments/unknown.json"
    assert expected_path == generator.get_comment_json_path(json)


def test_get_comment_path_with_missing_docket_i_d_key(generator):
    json = {
        "data": {
            "id": "VETS-2010-0001-0010",
            "type": "comments",
            "attributes": {
                "agencyId": "VETS",
            }
        }}
    # Parsing
    expected_path = "/VETS/VETS-2010-0001/text-VETS-2010-0001/" + \
                    "comments/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_comment_json_path(json)


def test_get_comment_path_with_missing_agency_i_d_key(generator):
    json = {
        "data": {
            "id": "VETS-2010-0001-0010",
            "type": "comments",
            "attributes": {
            }
        }}
    expected_path = "/unknown/VETS-2010-0001/text-VETS-2010-0001/" + \
                    "comments/VETS-2010-0001-0010.json"
    assert expected_path == generator.get_comment_json_path(json)


# Comments Attachments
def test_empty_json_places_json_in_unknown(generator):
    json = {}
    expected_path = "/unknown/unknown.json"
    assert expected_path == generator.get_path(json)


def test_attachment_comment_paths(generator):
    json_pls = get_attachment_and_comment()
    expected_path = ["/FDA/FDA-2017-D-2335/binary-FDA-2017-D-2335/comments" +
                     "_attachments/FDA-2017-D-2335-1566_attachment_1.pdf"]
    assert expected_path == generator.get_attachment_json_paths(json_pls)


def test_extractor_save_path():
    path = "/data/data/USTR/USTR-2015-0010/" + \
           "binary-USTR-2015-0010/" + \
           "comments_attachments/USTR-2015-0010-0002_attachment_1.pdf"
    save_path = PathGenerator.make_attachment_save_path(path)
    expected_path = "/data/data/USTR/USTR-2015-0010/text-USTR-2015-0010/" + \
                    "comments_extracted_text/pdfminer/" + \
                    "USTR-2015-0010-0002_attachment_1_extracted.txt"
    assert save_path == expected_path
