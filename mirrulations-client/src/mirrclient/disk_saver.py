import logging
import os
from json import dumps, load

from mirrclient.exceptions import SaveError

_log = logging.getLogger(__name__)


class DiskSaver():

    def make_path(self, _dir):
        try:
            os.makedirs(_dir)
        except FileExistsError:
            pass

    def save_to_disk(self, path, data):
        """Write JSON payload to ``path`` (exclusive create)."""
        try:
            with open(path, 'x', encoding='utf8') as file:
                file.write(dumps(data))
                _log.debug('Disk wrote json path=%s', path)
        except Exception as exc:
            raise SaveError(
                f'Disk save_to_disk failed path={path}: {exc}') from exc

    def _prepare_parent_dir_for_path(self, path):
        parent = path.rsplit('/', 1)[0]
        self.make_path(parent)

    def _write_json_if_canonical_missing(self, path, payload):
        """Create canonical JSON file when absent; return True if written."""
        if not os.path.exists(path):
            self.save_to_disk(path, payload)
            return True
        return False

    def _try_save_payload_at_alternate_slot(self, candidate, payload, counter):
        """Write at ``candidate`` or skip if duplicate; True when finished."""
        if not os.path.exists(candidate):
            _log.debug(
                'Disk json alternate path counter=%s path=%s',
                counter,
                candidate,
            )
            self.save_to_disk(candidate, payload)
            return True
        if self.is_duplicate(
                self.open_json_file(candidate),
                payload,
                candidate):
            return True
        return False

    def _write_payload_to_next_alternate_json_path(self, canonical_path, payload):
        """Pick ``file(1).json``, ``file(2).json``, … after canonical exists."""
        stem = canonical_path.removesuffix('.json')
        counter = 1
        while True:
            candidate = f'{stem}({counter}).json'
            if self._try_save_payload_at_alternate_slot(
                    candidate, payload, counter):
                return
            counter += 1

    def save_json(self, path, data):
        """
        writes the results to disk. used by docket document and comment jobs
        Parameters
        ----------
        data : dict
            the results data for the writer
        """
        try:
            self._prepare_parent_dir_for_path(path)
            payload = data['results']
            if self._write_json_if_canonical_missing(path, payload):
                return
            if self.is_duplicate(self.open_json_file(path), payload, path):
                return
            self._write_payload_to_next_alternate_json_path(path, payload)
        except SaveError:
            raise
        except Exception as exc:
            raise SaveError(
                f'Disk save_json failed path={path}: {exc}') from exc

    def save_binary(self, path, data):
        try:
            _dir = path.rsplit('/', 1)[0]
            self.make_path(_dir)
            with open(path, "wb") as file:
                file.write(data)
            _log.debug('Disk wrote binary path=%s', path)
        except Exception as exc:
            raise SaveError(
                f'Disk save_binary failed path={path}: {exc}') from exc

    def save_text(self, path, data):
        try:
            _dir = path.rsplit('/', 1)[0]
            self.make_path(_dir)
            with open(path, "w", encoding="utf-8") as file:
                file.write(data)
            _log.debug('Disk wrote text path=%s', path)
        except Exception as exc:
            raise SaveError(
                f'Disk save_text failed path={path}: {exc}') from exc

    def open_json_file(self, path):
        with open(path, encoding='utf8') as file:
            saved_data = load(file)
        return saved_data

    def is_duplicate(self, existing, new, path_hint=''):
        if existing == new:
            _log.debug(
                'Disk json unchanged skip write path=%s',
                path_hint or '(canonical)',
            )
            return True
        return False
