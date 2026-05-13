"""Walk Regulations.gov comment JSON for attachment ``fileFormats`` entries."""


def file_formats_usable(blocks):
    """True when ``fileFormats`` is a non-empty list (not API ``null`` sentinel)."""
    if blocks in ('null', None) or not blocks:
        return False
    return True


def iter_comment_attachment_file_formats(comment_json):
    """
    Yield each ``file_format`` dict under ``included`` that contains ``fileUrl``.

    Order: each ``included`` element in list order, then each ``fileFormats``
    entry in list order (only formats with ``fileUrl`` are yielded).
    """
    for block in comment_json.get('included', []):
        formats = block.get('attributes', {}).get('fileFormats')
        if not file_formats_usable(formats):
            continue
        for file_format in formats:
            if 'fileUrl' in file_format:
                yield file_format


def comment_attachment_file_format_count(comment_json):
    """Number of attachment file-format slots (same iteration as the iterator)."""
    return sum(1 for _ in iter_comment_attachment_file_formats(comment_json))
