# pylint: disable=too-many-public-methods

from pathlib import Path
from urllib.parse import urlparse


class PathGenerator:
    """
    Maps a concrete Regulations.gov payload (docket, document, comment JSON,
    attachments, document body) to a storage path segment.
    """

    def _get_nested_keys_in_json(self, json_data, nested_keys, default_value):
        '''
        Gets a value from traversing a series of nested keys in a JSON object.
        default_value is the value that should be returned if any of the nested
        keys are missing from the JSON.
        '''
        json_subset = json_data

        for key in nested_keys:
            if key not in json_subset:
                return default_value
            json_subset = json_subset[key]
        return json_subset

    def _parse_docket_id(self, item_i_d):
        if item_i_d is None:
            return "unknown"

        segments = item_i_d.split('-')  # list of segments separated by '-'
        segments_excluding_end = segments[:-1]  # drops the last segment
        parsed_docket_id = '-'.join(segments_excluding_end)
        return parsed_docket_id

    def _check_for_none_values(self, docket_id, agency_id, ):
        if docket_id is None:
            docket_id = 'unknown'
        if agency_id is None:
            agency_id = 'unknown'
        return docket_id, agency_id

    def _get_attributes(self, json_data, is_docket=False):
        '''
        Returns the agency, docket id, and item id from a loaded json object.
        '''
        item_i_d = self._get_nested_keys_in_json(
            json_data, ['data', 'id'], None)
        agency_id = self._get_nested_keys_in_json(
            json_data, ['data', 'attributes', 'agencyId'], None)

        if is_docket:
            docket_id = item_i_d
            item_i_d = None
        else:
            docket_id = self._get_nested_keys_in_json(
                json_data, ['data', 'attributes', 'docketId'], None)

            if docket_id is None:
                docket_id = self._parse_docket_id(item_i_d)
        if not is_docket and item_i_d is None:
            item_i_d = 'unknown'
        docket_id, agency_id = self._check_for_none_values(docket_id,
                                                           agency_id)

        return agency_id, docket_id, item_i_d

    def get_docket_json_path(self, json):
        agency_i_d, docket_i_d, _ = self._get_attributes(json,
                                                         is_docket=True)
        return (
            f'/raw-data/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/docket/'
            f'{docket_i_d}.json')

    def get_document_json_path(self, json):
        agency_i_d, docket_i_d, item_i_d = self._get_attributes(json)

        return (
            f'/raw-data/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/documents'
            f'/{item_i_d}.json')

    def get_document_htm_path(self, json):
        agency_id, docket_id, item_id = self._get_attributes(json)

        return f'/raw-data/{agency_id}/{docket_id}/text-{docket_id}/' + \
               f'documents/{item_id}_content.htm'

    def get_document_html_path(self, json):
        agency_id, docket_id, item_id = self._get_attributes(json)

        return f'/raw-data/{agency_id}/{docket_id}/text-{docket_id}/' + \
               f'documents/{item_id}_content.html'

    def get_comment_json_path(self, json):
        agency_i_d, docket_i_d, item_i_d = self._get_attributes(json)

        return (
            f'/raw-data/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/comments/'
            f'{item_i_d}.json')

    def get_comment_attachment_path(self, json_data, file_format):
        """
        Storage path for one comment attachment.

        ``file_format`` must be a ``fileFormats`` element that includes
        ``fileUrl`` (typically taken from ``iter_comment_attachment_file_formats``
        in ``mirrcore.comment_attachments``).
        """
        if 'fileUrl' not in file_format:
            raise ValueError('file_format must contain fileUrl')
        agency_i_d, docket_i_d, item_i_d = self._get_attributes(json_data)
        tail = file_format['fileUrl'].split('/')[-1]
        return (
            f'/raw-data/{agency_i_d}/{docket_i_d}/binary-{docket_i_d}/comments_'
            f'attachments/{item_i_d}_{tail}'
        )

    def get_comment_json_tombstone_path(self, job):
        comment_id = urlparse(job['url']).path.rstrip('/').split('/')[-1]
        agency = comment_id.split('-')[0]
        docket_id = comment_id.rsplit('-', 1)[0]
        return (
            f'/raw-data/{agency}/{docket_id}/text-{docket_id}/comments/'
            f'{comment_id}_UNAVAILABLE')

    def get_docket_json_tombstone_path(self, job):
        docket_id = urlparse(job['url']).path.rstrip('/').split('/')[-1]
        agency = docket_id.split('-')[0]
        return (
            f'/raw-data/{agency}/{docket_id}/text-{docket_id}/docket/'
            f'{docket_id}_UNAVAILABLE')

    def get_document_json_tombstone_path(self, job):
        document_id = urlparse(job['url']).path.rstrip('/').split('/')[-1]
        agency = document_id.split('-')[0]
        docket_id = document_id.rsplit('-', 1)[0]
        return (
            f'/raw-data/{agency}/{docket_id}/text-{docket_id}/documents/'
            f'{document_id}_UNAVAILABLE')

    def _tombstone_path_from_success_path(self, success_path):
        p = Path(success_path)
        return str(p.with_name(f'{p.stem}_UNAVAILABLE'))

    def get_comment_attachment_tombstone_path(self, json_data, file_format):
        return self._tombstone_path_from_success_path(
            self.get_comment_attachment_path(json_data, file_format))

    def get_document_htm_tombstone_path(self, json_data):
        return self._tombstone_path_from_success_path(
            self.get_document_htm_path(json_data))

    def get_document_html_tombstone_path(self, json_data):
        return self._tombstone_path_from_success_path(
            self.get_document_html_path(json_data))
