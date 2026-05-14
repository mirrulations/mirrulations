import logging
import time
import os
import sys
from typing import NamedTuple

import requests
import redis
from dotenv import load_dotenv
from mirrclient.saver import Saver
from mirrclient.disk_saver import DiskSaver
from mirrclient.s3_saver import S3Saver
from mirrclient.exceptions import (
    APITimeoutException,
    RedisPingFailedError,
    SaveError,
)
from mirrclient.logutil import (
    configure_client_logging,
    entity_from_job_url,
    kind_singular,
    redact_url,
)
from mirrclient.key_manager import (
    KeyCredential,
    KeyManager,
    KeyManagerFileError,
    KeyManagerJsonError,
)
from mirrcore.redis_check import load_redis
from mirrcore.path_generator import PathGenerator
from mirrcore.comment_attachments import (
    comment_attachment_file_format_count,
    iter_comment_attachment_file_formats,
)
from mirrcore.job_queue import JobQueue
from mirrcore.jobs_statistics import JobStatistics
from mirrcore.job_queue_exceptions import JobQueueException
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)

BROWSER_DOWNLOAD_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,*/*;q=0.8'
    ),
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.regulations.gov/',
}


class _CommentAttachmentSlot(NamedTuple):
    """One attachment URL/path pair during comment downloads."""

    url: str
    attach_path: str
    attachment_entity: str
    key_id: str
    attachment_index: int
    file_format: dict


class _DocumentBodyFetch(NamedTuple):
    """Resolved URL and destination path for an HTM/HTML document body."""

    download_url: str | None
    storage_path: str
    file_format: str
    entity_id: str


class _JobFailureLog(NamedTuple):
    """Precomputed values for job failure log lines (no ``job_id`` in messages)."""

    kind: str
    redacted_job_url: str
    key_id: str


_RABBITMQ_DOWN_MSG = (
    'RabbitMQ unreachable; cannot fetch jobs. '
    'Client will resume when the broker is available again.'
)
_REDIS_DOWN_MSG = (
    'Redis unreachable (ping failed before dequeue); '
    'client will retry when Redis is reachable again.'
)


def _build_savers():
    """
    Disk is always enabled.

    S3 is controlled by ``S3_BUCKET``:

    * unset — use bucket name ``mirrulations`` (backward compatible default)
    * empty or whitespace-only — disable S3 (disk only)
    * any other value — use that string as the bucket name

    Returns
    -------
    list
        ``DiskSaver`` and optionally ``S3Saver``.
    """
    raw = os.getenv('S3_BUCKET')
    if raw is not None and not raw.strip():
        return [DiskSaver()]
    bucket = (raw.strip() if raw else None) or 'mirrulations'
    return [DiskSaver(), S3Saver(bucket_name=bucket)]


def is_client_keys_path_configured():
    """
    Return True if CLIENT_KEYS_PATH is set.

    File validity is checked when KeyManager loads.

    Returns
    -------
    Boolean
    """
    path = os.getenv('CLIENT_KEYS_PATH')
    return path is not None and path != ''


class Client:
    """
    The Client class gets a job directly from the job queue.
    It receives a job, performs it depending on the job type.
    A job is performed by calling an api endpoint to request
    a json object. The client saves the result of the job and any included
    attachments using the Saver class.

    Attributes
    ----------
    path_generator : PathGenerator
        Returns a path for the result of a job to be saved to.
    saver : Saver
        Handles the making of directories and the saving of files either
        to disk or Amazon s3.
    redis : redis_server
        Allows for a direct connection to the Redis server, incrementing the
        jobs completed.
    job_queue : JobQueue
        Queue of all of the jobs that need to be completed. The client will
        directly pull jobs from this queue.
    key_manager : KeyManager
        Loads API keys and pacing between calls.
    """
    def __init__(self, redis_server, job_queue, manager):
        self.path_generator = PathGenerator()
        self.saver = Saver(savers=_build_savers())
        self.redis = redis_server
        self.job_queue = job_queue
        self.cache = JobStatistics(redis_server)
        self.key_manager = manager

    @staticmethod
    def _log_artifact_info(  # pylint: disable=too-many-arguments,too-many-locals
            *,
            kind,
            entity,
            key_id,
            artifact,
            filename,
            attachment_index=None,
            http_status=None):
        verb = 'wrote tombstone' if http_status is not None else 'wrote artifact'
        msg = (
            f"{verb} kind={kind} type={artifact} entity={entity} "
            f"file={filename} key_id={key_id}"
        )
        if http_status is not None:
            msg += f" http_status={http_status}"
        if attachment_index is not None:
            msg += f" attachment={attachment_index}"
        logger.info('%s', msg)

    def _can_connect_to_database(self):
        try:
            self.redis.ping()
        except redis.exceptions.ConnectionError:
            return False
        return True

    def _get_job_from_job_queue(self):
        if not self._can_connect_to_database():
            raise RedisPingFailedError

        return self.job_queue.get_job()

    def _set_default_key(self, job, key, default_value):
        if key not in job:
            job[key] = default_value

    def _set_missing_job_key_defaults(self, job):
        self._set_default_key(job, 'job_type', 'other')
        self._set_default_key(job, 'reg_id', 'other_reg_id')
        self._set_default_key(job, 'agency', 'other_agency')
        return job

    def _remove_plural_from_job_type(self, job):
        split_url = str(job['url']).split('/')
        job_type = split_url[-2][:-1]  # Removes plural from job type
        type_id = split_url[-1]
        return f'{job_type}/{type_id}'

    def _get_job(self, key_id: str):
        """
        Get a job from the JobQueue.

        Returns the job dict, or ``None`` if no job is available.
        """
        job = self._get_job_from_job_queue()

        if job is None:
            return None

        job = self._set_missing_job_key_defaults(job)

        # update count for dashboard
        self.job_queue.decrement_count(job['job_type'])

        logger.debug(
            'Dequeued job type=%s key_id=%s url=%s',
            job['job_type'],
            key_id,
            redact_url(job['url']),
        )

        return job

    def _primary_json_corpus_path(self, job_result):
        """
        Full corpus path for the primary API JSON object (``/raw-data`` prefix).

        Mirrors the former ``PathGenerator.get_path`` contract: missing or empty
        ``data``, or ``data['type'] == -1``, map to ``/unknown/unknown.json``;
        unknown ``type`` yields ``/raw-data/unknown/unknown.json``.
        """
        if 'data' not in job_result or job_result['data'] == []:
            return '/unknown/unknown.json'
        payload = job_result['data']
        if payload.get('type') == -1:
            return '/unknown/unknown.json'
        pg = self.path_generator
        handler = {
            'comments': pg.get_comment_json_path,
            'dockets': pg.get_docket_json_path,
            'documents': pg.get_document_json_path,
        }.get(payload.get('type'))
        if handler is not None:
            return handler(job_result)
        return '/raw-data/unknown/unknown.json'

    def _primary_json_corpus_path_from_job(self, job):
        """Canonical primary ``.json`` path from ``job`` when the body is not parsed."""
        pg = self.path_generator
        handler = {
            'comments': pg.get_comment_json_path_from_job,
            'dockets': pg.get_docket_json_path_from_job,
            'documents': pg.get_document_json_path_from_job,
        }.get(job.get('job_type'))
        if handler is not None:
            return handler(job)
        return '/raw-data/unknown/unknown.json'

    def _primary_json_tombstone_path_for_job(self, job):
        """Primary API JSON tombstone path from ``job`` (HTTP error responses)."""
        pg = self.path_generator
        if job.get('job_type') == 'comments':
            return pg.get_comment_json_tombstone_path(job)
        if job.get('job_type') == 'dockets':
            return pg.get_docket_json_tombstone_path(job)
        if job.get('job_type') == 'documents':
            return pg.get_document_json_tombstone_path(job)
        return '/raw-data/unknown/unknown_UNAVAILABLE'

    def _persist_primary_api_tombstone(self, job, response, key_id):
        """Write primary JSON tombstone for non-OK API response; log and count."""
        path = self._primary_json_tombstone_path_for_job(job)
        self.saver.save_tombstone(path, response.status_code)
        _, fname = path.rsplit('/', 1)
        self._log_artifact_info(
            kind=kind_singular(job['job_type']),
            entity=entity_from_job_url(job['url']),
            key_id=key_id,
            artifact='json',
            filename=fname,
            http_status=response.status_code,
        )
        self.cache.increase_jobs_done(job['job_type'])

    def _persist_primary_api_unparseable_body(self, job, response, key_id):
        """Save raw response bytes at canonical ``.json`` path when JSON parse fails."""
        path = self._primary_json_corpus_path_from_job(job)
        self.saver.save_binary(path, response.content)
        _, fname = path.rsplit('/', 1)
        logger.info(
            'wrote unparseable api body kind=%s type=json entity=%s file=%s '
            'key_id=%s',
            kind_singular(job['job_type']),
            entity_from_job_url(job['url']),
            fname,
            key_id,
        )
        self.cache.increase_jobs_done(job['job_type'])

    def _download_job(self, job, job_result, key_id):
        """
        Downloads the current job and saves the data using the Saver.

        Parameters
        ----------
        job : dict
            information about the job being completed
        job_result : dict
            results from a performed job
        key_id : str
            Credential id used for API calls during this job.
        """
        data = {
            'job_type': job['job_type'],
            'job_id': job['job_id'],
            'results': job_result,
            'reg_id': job['reg_id'],
            'agency': job['agency']
        }
        logger.debug(
            'Download start job id=%s type=%s key_id=%s',
            job['job_id'],
            job['job_type'],
            key_id,
        )
        data['directory'] = self._primary_json_corpus_path(job_result)

        self._save_primary_json_and_log(job, data, key_id)
        self._maybe_download_followups(job_result, data['job_type'], key_id)
        self.cache.increase_jobs_done(data['job_type'])

    def _save_primary_json_and_log(self, job, data, key_id):
        """Persist API JSON for this job and emit the artifact INFO line."""
        self._put_results(data)
        _, filename = data['directory'].rsplit('/', 1)
        self._log_artifact_info(
            kind=kind_singular(data['job_type']),
            entity=entity_from_job_url(job['url']),
            key_id=key_id,
            artifact='json',
            filename=filename,
        )

    def _maybe_download_followups(self, job_result, job_type, key_id):
        """Pull comment attachments or document body when the payload calls for it."""
        if job_type == 'comments' and self._does_comment_have_attachment(
                job_result):
            self._download_all_attachments_from_comment(job_result, key_id)
        if job_type == 'documents' and self._document_has_file_formats(
                job_result):
            if self._get_document_htm(job_result) is not None:
                self._download_htm(job_result, key_id)

    def _put_results(self, data):
        """
        Ensures data format matches expected format
        If results are valid, writes them to disk / S3
        """
        self.saver.save_json(data['directory'], data)

    def _perform_job(self, job_url: str, api_cred: KeyCredential):
        """
        Performs job via get_request function by giving it the job_url combined
        with the api_key for validation.

        Parameters
        ----------
        job_url : str
            url from a job
        api_cred : KeyCredential
            Regulations.gov API credential for this request

        Returns
        -------
        requests.Response
        """
        try:
            delimiter = '&' if '?' in job_url else '?'
            url = f'{job_url}{delimiter}api_key={api_cred.api_key}'

            return requests.get(url, timeout=10)
        except requests.exceptions.ReadTimeout as exc:
            raise APITimeoutException from exc

    def _iter_comment_attachment_slots(self, comment_json, key_id):
        """Yield each attachment URL/path pair during comment downloads."""
        attachment_entity = comment_json['data']['id']
        for idx, file_format in enumerate(
                iter_comment_attachment_file_formats(comment_json)):
            attach_path = self.path_generator.get_comment_attachment_path(
                comment_json, file_format)
            yield _CommentAttachmentSlot(
                file_format['fileUrl'],
                attach_path,
                attachment_entity,
                key_id,
                idx + 1,
                file_format,
            )

    def _persist_comment_attachment_and_record_stats(
            self, comment_json, slot):
        """Fetch one attachment; on success save bytes, else tombstone; log."""
        response = self._download_single_attachment(slot.url)
        _, fname = slot.attach_path.rsplit('/', 1)
        if response.ok:
            self.saver.save_binary(slot.attach_path, response.content)
            self._log_artifact_info(
                kind='attachment',
                entity=slot.attachment_entity,
                key_id=slot.key_id,
                artifact='attachment',
                filename=fname,
                attachment_index=slot.attachment_index,
            )
        else:
            tomb_path = (
                self.path_generator.get_comment_attachment_tombstone_path(
                    comment_json, slot.file_format))
            self.saver.save_tombstone(tomb_path, response.status_code)
            _, tfname = tomb_path.rsplit('/', 1)
            self._log_artifact_info(
                kind='attachment',
                entity=slot.attachment_entity,
                key_id=slot.key_id,
                artifact='attachment',
                filename=tfname,
                attachment_index=slot.attachment_index,
                http_status=response.status_code,
            )
        self.cache.increase_jobs_done(
            'attachment', slot.url.endswith('.pdf'))

    def _download_all_attachments_from_comment(self, comment_json, key_id):
        '''
        Downloads all attachments for a comment.

        Parameters
        ----------
        comment_json : dict
            The json of the comment

        key_id : str
            API credential id.
        '''
        count = comment_attachment_file_format_count(comment_json)
        attachment_entity = comment_json['data']['id']
        logger.debug(
            'Comment attachments scheduled count=%s entity=%s',
            count,
            attachment_entity,
        )
        for slot in self._iter_comment_attachment_slots(
                comment_json, key_id):
            self._persist_comment_attachment_and_record_stats(
                comment_json, slot)

    def _download_single_attachment(self, url):
        """GET attachment bytes; caller branches on ``response.ok``."""
        return requests.get(
            url, headers=BROWSER_DOWNLOAD_HEADERS, timeout=10)

    def _does_comment_have_attachment(self, comment_json):
        """
        Validates whether a json for a comment has any
        attachments to be downloaded.
        """
        if "included" in comment_json and len(comment_json["included"]) > 0:
            return True
        return False

    def _resolve_document_body_fetch(self, json_data):
        """Resolve HTM/HTML URL and saver-relative path from document JSON."""
        url = self._get_document_htm(json_data)
        file_format = self._get_format(json_data)
        if file_format == 'html':
            storage_path = self.path_generator.get_document_html_path(json_data)
        else:
            storage_path = self.path_generator.get_document_htm_path(json_data)
        return _DocumentBodyFetch(
            url,
            storage_path,
            file_format,
            json_data['data']['id'],
        )

    def _persist_downloaded_document_body(  # pylint: disable=too-many-arguments
            self, response, key_id, fetch, json_data):
        """Save HTM/HTML body or tombstone from ``response``; log and stats."""
        _, filename = fetch.storage_path.rsplit('/', 1)
        if response.ok:
            self.saver.save_binary(fetch.storage_path, response.content)
            self._log_artifact_info(
                kind='document',
                entity=fetch.entity_id,
                key_id=key_id,
                artifact=fetch.file_format,
                filename=filename,
            )
        else:
            if fetch.file_format == 'html':
                tomb_path = (
                    self.path_generator.get_document_html_tombstone_path(
                        json_data))
            else:
                tomb_path = self.path_generator.get_document_htm_tombstone_path(
                    json_data)
            self.saver.save_tombstone(tomb_path, response.status_code)
            _, tfname = tomb_path.rsplit('/', 1)
            self._log_artifact_info(
                kind='document',
                entity=fetch.entity_id,
                key_id=key_id,
                artifact=fetch.file_format,
                filename=tfname,
                http_status=response.status_code,
            )
        self.cache.increase_jobs_done('attachment')

    def _download_htm(self, json_data, key_id):
        fetch = self._resolve_document_body_fetch(json_data)
        if fetch.download_url is None:
            return
        response = requests.get(
            fetch.download_url, headers=BROWSER_DOWNLOAD_HEADERS, timeout=10)
        self._persist_downloaded_document_body(
            response, key_id, fetch, json_data)

    def _get_format(self, json_data):
        file_formats = json_data["data"]["attributes"]["fileFormats"]
        for file_format in file_formats:
            if file_format.get("format") in ("htm", "html"):
                return file_format.get("format")
        return "htm"

    def _get_document_htm(self, json_data):
        """
        Gets the download link for a documents HTM if one exists
        """
        file_formats = json_data["data"]["attributes"]["fileFormats"]
        for file_format in file_formats:
            if file_format.get("format") in ("htm", "html"):
                file_url = file_format.get("fileUrl")
                if file_url is not None:
                    return file_url
        return None

    def _document_has_file_formats(self, json_data):
        """
        Checks to see if the necessary attribute of fileFormats exists
        """
        if "data" not in json_data or "attributes" not in \
            json_data["data"] or "fileFormats" not in \
                json_data["data"]["attributes"]:
            return False
        if json_data["data"]["attributes"]["fileFormats"] is None:
            return False
        return True

    def _run_fetched_job_pipeline(self, job, api_cred):
        """HTTP GET job URL; persist primary JSON, tombstone, or raw body."""
        response = self._perform_job(job['url'], api_cred)
        key_id = api_cred.id
        if not response.ok:
            self._persist_primary_api_tombstone(job, response, key_id)
            return
        try:
            result = response.json()
        except ValueError:
            self._persist_primary_api_unparseable_body(job, response, key_id)
            return
        self._download_job(job, result, key_id)

    @staticmethod
    def _log_job_failed_timeout(kind, redacted_job_url, key_id):
        logger.error(
            'job failed kind=%s phase=api url=%s key_id=%s reason=timeout',
            kind,
            redacted_job_url,
            key_id,
        )

    @staticmethod
    def _log_job_failed_http(kind, redacted_job_url, key_id, err):
        response = err.response
        status = response.status_code if response is not None else ''
        retry_after = ''
        body_preview = ''
        if response is not None:
            retry_after = response.headers.get('Retry-After', '')
            body_preview = response.text[:500]
        logger.error(
            'job failed kind=%s phase=api url=%s key_id=%s status=%s '
            'error=%s retry_after=%s response_body=%r',
            kind,
            redacted_job_url,
            key_id,
            status,
            err,
            retry_after,
            body_preview,
        )

    @staticmethod
    def _log_job_failed_request(kind, redacted_job_url, key_id, err):
        logger.error(
            'job failed kind=%s phase=api url=%s key_id=%s reason=%s',
            kind,
            redacted_job_url,
            key_id,
            err,
        )

    def _handle_job_api_and_storage(self, job, api_cred, failure_log):
        """Run HTTP fetch + persist; map failures to structured ERROR logs."""
        try:
            self._run_fetched_job_pipeline(job, api_cred)
        except APITimeoutException:
            self._log_job_failed_timeout(
                failure_log.kind,
                failure_log.redacted_job_url,
                failure_log.key_id,
            )
            raise
        except requests.exceptions.RequestException as err:
            self._log_job_failed_request(
                failure_log.kind,
                failure_log.redacted_job_url,
                failure_log.key_id,
                err,
            )
            raise

    def job_operation(self, api_cred: KeyCredential):
        """
        Pull a job if one is available, then download and persist it.

        If the queue is empty, returns immediately.
        """
        job = self._get_job(api_cred.id)

        if job is None:
            return

        failure_log = _JobFailureLog(
            kind_singular(job['job_type']),
            redact_url(job['url']),
            api_cred.id,
        )
        self._handle_job_api_and_storage(job, api_cred, failure_log)

        logger.debug(
            'Job finished kind=%s url=%s key_id=%s',
            failure_log.kind,
            failure_log.redacted_job_url,
            failure_log.key_id,
        )


if __name__ == '__main__':
    load_dotenv()
    configure_client_logging()

    if not is_client_keys_path_configured():
        logger.critical('CLIENT_KEYS_PATH is not set; exiting.')
        sys.exit(1)

    keys_path = os.environ['CLIENT_KEYS_PATH']
    try:
        key_manager = KeyManager(keys_path)
    except (KeyManagerFileError, KeyManagerJsonError) as exc:
        logger.critical('Could not load API keys file: %s', exc)
        sys.exit(1)

    try:
        redis_client = load_redis()
    except redis.exceptions.ConnectionError:
        logger.critical('Cannot connect to Redis at startup; exiting.')
        sys.exit(1)

    logger.info(
        'Waiting for RabbitMQ message broker to accept connections before '
        'dequeuing jobs.'
    )
    mirr_job_queue = JobQueue(redis_client)
    mirr_job_queue.wait_for_ready()
    client = Client(redis_client, mirr_job_queue, key_manager)

    rabbit_is_healthy = True
    redis_is_healthy = True

    while True:
        try:
            cred = key_manager.get_next()
            client.job_operation(cred)
            rabbit_is_healthy = True
            redis_is_healthy = True
        except redis.exceptions.ConnectionError:
            logger.error('Redis connection lost during operation.')
        except RedisPingFailedError:
            if redis_is_healthy:
                logger.warning(_REDIS_DOWN_MSG)
                redis_is_healthy = False
        except APITimeoutException:
            pass
        except requests.exceptions.HTTPError as exc:
            logger.debug('Unexpected HTTPError after job: %s', exc)
        except (JobQueueException, AMQPConnectionError):
            if rabbit_is_healthy:
                logger.warning(_RABBITMQ_DOWN_MSG)
                rabbit_is_healthy = False
        except SaveError as exc:
            logger.error('%s', exc)
            if exc.__cause__ is not None:
                logger.error('Cause: %r', exc.__cause__)

        time.sleep(key_manager.seconds_between_api_calls())
