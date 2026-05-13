# pylint: disable=too-many-public-methods


class PathGenerator:
    """
    Maps a concrete Regulations.gov payload (docket, document, comment JSON,
    attachments, document body) to a storage path segment.

    Primary API JSON corpus paths (``/raw-data`` + relative path) are assembled
    in the client, which dispatches on ``data['type']`` and calls the appropriate
    ``get_*_json_path`` method here.
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

    def parse_docket_id(self, item_i_d):
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

    def get_attributes(self, json_data, is_docket=False):
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
                docket_id = self.parse_docket_id(item_i_d)
        if not is_docket and item_i_d is None:
            item_i_d = 'unknown'
        docket_id, agency_id = self._check_for_none_values(docket_id,
                                                           agency_id)

        return agency_id, docket_id, item_i_d

    def get_docket_json_path(self, json):
        agency_i_d, docket_i_d, _ = self.get_attributes(json,
                                                        is_docket=True)
        return f'/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/docket/' + \
               f'{docket_i_d}.json'

    def get_document_json_path(self, json):
        agency_i_d, docket_i_d, item_i_d = self.get_attributes(json)

        return f'/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/documents' + \
               f'/{item_i_d}.json'

    def get_document_htm_path(self, json):
        agency_id, docket_id, item_id = self.get_attributes(json)

        return f'/raw-data/{agency_id}/{docket_id}/text-{docket_id}/' + \
               f'documents/{item_id}_content.htm'

    def get_document_html_path(self, json):
        agency_id, docket_id, item_id = self.get_attributes(json)

        return f'/raw-data/{agency_id}/{docket_id}/text-{docket_id}/' + \
               f'documents/{item_id}_content.html'

    def get_comment_json_path(self, json):
        agency_i_d, docket_i_d, item_i_d = self.get_attributes(json)

        return f'/{agency_i_d}/{docket_i_d}/text-{docket_i_d}/comments/' + \
               f'{item_i_d}.json'

    def _parse_attachment_path(self, json, file_format, attachments):
        agency_i_d, docket_i_d, item_i_d = self.get_attributes(json)
        if "fileUrl" in file_format:
            attachment_name = item_i_d + "_" + \
                file_format["fileUrl"].split("/")[-1]
            attachments.append(f'/raw-data/{agency_i_d}/{docket_i_d}/' +
                               f'binary-{docket_i_d}/comments_' +
                               f'attachments/{attachment_name}')
        return attachments

    def get_attachment_json_paths(self, json):
        '''
        Given a json, this function will return all attachment paths for
        n number attachment links
        '''

        # contains list of paths for attachments
        attachments = []
        for attachment in json["included"]:
            attributes = attachment["attributes"]
            if attributes.get("fileFormats"):
                for file_format in attributes["fileFormats"]:
                    attachments = self._parse_attachment_path(json,
                                                              file_format,
                                                              attachments)

        return attachments
