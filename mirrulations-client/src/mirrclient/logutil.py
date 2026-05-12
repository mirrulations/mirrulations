"""Logging configuration and URL helpers for the Mirrulations client."""

from __future__ import annotations

import logging
import os
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


class _UTCFormatter(logging.Formatter):
    converter = time.gmtime


def configure_client_logging() -> None:
    """Configure root logging once with ISO-UTC timestamps."""
    root = logging.getLogger()
    if root.handlers:
        return
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(_UTCFormatter(
        '%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ',
    ))
    root.addHandler(handler)
    root.setLevel(level)


def redact_url(url: str) -> str:
    """Strip ``api_key`` (and variants) from a URL query string."""
    if not url:
        return ''
    if '?' not in url:
        return url
    parts = urlsplit(url)
    qs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
          if k.lower() not in ('api_key', 'apikey')]
    new_query = urlencode(qs)
    return urlunsplit((
        parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def entity_from_job_url(url: str) -> str:
    """Return the Regulations.gov-style id segment from an API-style job URL."""
    if not url:
        return ''
    path = url.split('?', 1)[0].rstrip('/')
    return path.rsplit('/', 1)[-1] if path else ''


def kind_singular(job_type: str) -> str:
    """Map queue plural ``job_type`` to singular log vocabulary."""
    mapping = {'dockets': 'docket', 'documents': 'document', 'comments': 'comment'}
    return mapping.get(job_type, job_type or 'other')
