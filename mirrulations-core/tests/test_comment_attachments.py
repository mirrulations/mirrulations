from mirrcore.comment_attachments import (
    comment_attachment_file_format_count,
    file_formats_usable,
    iter_comment_attachment_file_formats,
)


def test_file_formats_usable():
    assert file_formats_usable([{}]) is True
    assert file_formats_usable(None) is False
    assert file_formats_usable('null') is False


def test_iter_and_count_single_attachment():
    link = (
        'https://downloads.regulations.gov/FDA-2017-D-2335-1566/attachment_1.pdf'
    )
    comment_json = {
        'data': {
            'id': 'FDA-2017-D-2335-1566',
            'type': 'comments',
            'attributes': {
                'agencyId': 'FDA',
                'docketId': 'FDA-2017-D-2335',
            },
        },
        'included': [{
            'attributes': {
                'fileFormats': [{'fileUrl': link}],
            },
        }],
    }
    formats = list(iter_comment_attachment_file_formats(comment_json))
    assert len(formats) == 1
    assert formats[0]['fileUrl'] == link
    assert comment_attachment_file_format_count(comment_json) == 1


def test_iter_skips_null_file_formats_and_formats_without_url():
    comment_json = {
        'data': {
            'id': 'FDA-2017-D-2335-1566',
            'type': 'comments',
            'attributes': {
                'agencyId': 'FDA',
                'docketId': 'FDA-2017-D-2335',
            },
        },
        'included': [{
            'attributes': {
                'fileFormats': None,
            },
        }],
    }
    assert not list(iter_comment_attachment_file_formats(comment_json))
    assert comment_attachment_file_format_count(comment_json) == 0


def test_two_file_formats_one_included_yields_two():
    comment_json = {
        'data': {
            'id': 'agencyID-001-0002',
            'type': 'comments',
            'attributes': {
                'agencyId': 'agencyID',
                'docketId': 'agencyID-001',
            },
        },
        'included': [{
            'attributes': {
                'fileFormats': [
                    {'fileUrl': 'https://downloads.regulations.gov/.pdf'},
                    {'fileUrl': 'https://downloads.regulations.gov/.doc'},
                ],
            },
        }],
    }
    assert comment_attachment_file_format_count(comment_json) == 2
    urls = [f['fileUrl'] for f in iter_comment_attachment_file_formats(
        comment_json)]
    assert urls[0].endswith('.pdf')
    assert urls[1].endswith('.doc')
