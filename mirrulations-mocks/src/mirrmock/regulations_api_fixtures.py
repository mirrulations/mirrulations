"""Minimal regulations.gov-style API JSON blobs shared across test modules."""


def get_test_docket():
    return {
        "data": {
            "id": "USTR-2015-0010",
            "type": "dockets",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010",
            },
        },
    }


def get_test_document():
    return {
        "data": {
            "id": "USTR-2015-0010-0015",
            "type": "documents",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010",
            },
        },
    }


def get_test_comment():
    return {
        "data": {
            "id": "USTR-2015-0010-0002",
            "type": "comments",
            "attributes": {
                "agencyId": "USTR",
                "docketId": "USTR-2015-0010",
            },
        },
    }
