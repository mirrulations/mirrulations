"""
Load and rotate regulations.gov API keys from a JSON file.

The file must be a JSON object with a required ``keys`` field: a non-empty
array of objects with exactly two string fields: ``id`` and ``api_key``.
The ``id`` field must be ASCII letters, digits, and underscores only, and the
first character must not be a digit.  The ``api_key`` field must be non-empty
and alphanumeric ASCII only.

An optional ``calls_per_hour_per_key`` integer sets the pacing target per key
(default 999).

The KeyManager class validates the file and rejects duplicate ``id`` values or
duplicate ``api_key`` values.  It provides methods to get the next credential
in rotation and to compute how long the client should sleep before the next
iteration.
"""

import time
from pathlib import Path
from typing import ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    TypeAdapter,
    ValidationError,
)

DEFAULT_CALLS_PER_HOUR_PER_KEY = 999
CONSERVATIVE_CALLS_PER_HOUR_PER_KEY = 1000


class KeyManagerFileError(Exception):
    """Path or read error; or file is not UTF-8 decodable text."""


class KeyManagerJsonError(Exception):
    """JSON or credential validation error (dupes, empty list, etc.)."""


class KeyCredential(BaseModel):
    """
    ``id`` for a key

    ``api_key`` the api key (do not log)
    """

    model_config = ConfigDict(extra='forbid', frozen=True)

    _ID_VAR_PATTERN: ClassVar[str] = r'^[A-Za-z_][A-Za-z0-9_]*$'
    _API_KEY_ALNUM_PATTERN: ClassVar[str] = r'^[A-Za-z0-9]+$'

    id: StrictStr = Field(pattern=_ID_VAR_PATTERN)
    api_key: StrictStr = Field(pattern=_API_KEY_ALNUM_PATTERN)


class KeyManagerFile(BaseModel):
    """Top-level ``client_keys.json`` layout."""

    model_config = ConfigDict(extra='forbid', frozen=True)

    keys: list[KeyCredential]
    calls_per_hour_per_key: int = Field(
        default=DEFAULT_CALLS_PER_HOUR_PER_KEY,
        gt=0,
    )


_KEY_MANAGER_FILE_ADAPTER = TypeAdapter(KeyManagerFile)


def _read_text(path: Path) -> str:
    """Load the raw JSON file as UTF-8 text.

    Raises:
        KeyManagerFileError: If ``path`` is missing or not a file, if open or
            read fails (``OSError``), or if the bytes are not valid UTF-8.
    """
    try:
        if not path.exists():
            raise KeyManagerFileError('API keys file does not exist')
        if not path.is_file():
            raise KeyManagerFileError('Path is not a file')
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError as exc:
        raise KeyManagerFileError(
            f'File must be UTF-8 text ({exc.reason}).'
        ) from exc
    except OSError as exc:
        raise KeyManagerFileError(
            f'Could not read API keys file: {exc}') from exc


def _check_for_duplicates(entries: list[KeyCredential]) -> None:
    """Check for duplicate ``id`` or duplicate ``api_key`` values.

    Raises:
        KeyManagerJsonError: On duplicate ``id`` or duplicate ``api_key``.
            Messages name only an ``id``, never an ``api_key``.
    """
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    for cred in entries:
        if cred.id in seen_ids:
            raise KeyManagerJsonError(f'duplicate id {cred.id!r}')
        seen_ids.add(cred.id)
        if cred.api_key in seen_keys:
            raise KeyManagerJsonError(
                f'duplicate api_key id {cred.id!r}')
        seen_keys.add(cred.api_key)


def _parse_text(text: str) -> KeyManagerFile:
    """Parse JSON text into a validated ``KeyManagerFile``.

    Raises:
        KeyManagerJsonError: Invalid JSON or layout, or empty keys array.
    """
    try:
        parsed = _KEY_MANAGER_FILE_ADAPTER.validate_json(text)
    except ValidationError as exc:
        raise KeyManagerJsonError(
            'Invalid JSON or credential layout') from exc
    if not parsed.keys:
        raise KeyManagerJsonError('Credential list is empty')
    return parsed


class KeyManager:
    """
    Stateful rotation over credentials loaded from disk at construction.

    The file is read and validated once in ``__init__``. ``get_next`` returns
    entries in order and cycles through keys. Call ``get_next`` before
    ``seconds_to_sleep`` each iteration so pacing can account for wall-clock
    time spent on work; if ``seconds_to_sleep`` runs without a prior
    ``get_next``, it returns a conservative fixed interval.
    """

    def __init__(self, path: str | Path) -> None:
        """
        Parameters:
            path: Path to the JSON credentials file.

        Raises:
            KeyManagerFileError: If the file cannot be read as UTF-8 text.
            KeyManagerJsonError: If JSON is invalid, empty, violates the
                credential schema, or contains duplicate ids or api keys.
        """
        self._next_index = 0
        key_file = _parse_text(_read_text(Path(path)))
        self._entries = key_file.keys
        self._calls_per_hour_per_key = key_file.calls_per_hour_per_key
        _check_for_duplicates(self._entries)
        self._last_handout_monotonic: float | None = None

    @property
    def key_count(self) -> int:
        """Number of loaded credentials."""

        return len(self._entries)

    @property
    def calls_per_hour_per_key(self) -> int:
        """Configured API call rate target per key."""

        return self._calls_per_hour_per_key

    def _target_interval_seconds(self) -> float:
        return (
            3600
            / self._calls_per_hour_per_key
            / len(self._entries)
        )

    def _conservative_interval_seconds(self) -> float:
        return (
            3600
            / CONSERVATIVE_CALLS_PER_HOUR_PER_KEY
            / len(self._entries)
        )

    def get_next(self) -> KeyCredential:
        """Return the next credential in rotation; advances internal index."""

        self._last_handout_monotonic = time.monotonic()
        row = self._entries[self._next_index]
        next_index = self._next_index + 1
        self._next_index = next_index % len(self._entries)
        return row

    def seconds_to_sleep(self) -> float:
        """Seconds the client should sleep before the next iteration.

        After ``get_next`` has been called in the current iteration, returns
        the remaining time needed to meet the configured per-key hourly rate,
        accounting for wall-clock time since that handout. If ``get_next`` has
        not been called yet, returns a conservative interval based on 1000
        calls per hour per key.
        """

        if self._last_handout_monotonic is None:
            return self._conservative_interval_seconds()
        elapsed = time.monotonic() - self._last_handout_monotonic
        return max(0.0, self._target_interval_seconds() - elapsed)
