"""
Load and rotate regulations.gov API keys from a JSON file.

The file must be a non-empty JSON array of objects with exactly two string
fields: ``id`` and ``api_key``.  The ``id`` field must be ASCII letters,
digits, and underscores only, and the first character must not be a digit.
The ``api_key`` field must be non-empty and alphanumeric ASCII only.

The KeyManager class validates the file and rejects duplicate ``id`` values or
duplicate ``api_key`` values.  It provides methods to get the next credential
in rotation and to calculate the seconds between API calls.
"""

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


# TypeAdapter is a Pydantic utility that provides a parser (validator) for a
# top-level list of KeyCredential objects. We use it in the KeyManager
# constructor to validate the structure and values of the JSON file.
_CREDENTIAL_LIST_ADAPTER = TypeAdapter(list[KeyCredential])


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


def _parse_text(text: str) -> list[KeyCredential]:
    """Convert JSON text into a list of ``KeyCredential``.

    Raises:
        KeyManagerJsonError: Invalid JSON or layout, or empty array.
    """
    try:
        parsed = _CREDENTIAL_LIST_ADAPTER.validate_json(text)
    except ValidationError as exc:
        raise KeyManagerJsonError(
            'Invalid JSON or credential layout') from exc
    if not parsed:
        raise KeyManagerJsonError('Credential list is empty')
    return parsed


class KeyManager:
    """
    Stateful rotation over credentials loaded from disk at construction.

    The file is read and validated once in ``__init__``. ``get_next`` returns
    entries in order and cycles through keys. For pacing many keys
    against a shared hourly limit, ``seconds_between_api_calls``
    divides that budget evenly across ``key_count``.
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
        self._entries = _parse_text(_read_text(Path(path)))
        _check_for_duplicates(self._entries)

    @property
    def key_count(self) -> int:
        """Number of loaded credentials."""

        return len(self._entries)

    def get_next(self) -> KeyCredential:
        """Return the next credential in rotation; advances internal index."""

        row = self._entries[self._next_index]
        next_index = self._next_index + 1
        self._next_index = next_index % len(self._entries)
        return row

    def seconds_between_api_calls(self) -> float:
        """Seconds between API calls."""

        api_rate_limit = 1000
        seconds_per_hour = 3600
        return seconds_per_hour / api_rate_limit / len(self._entries)
