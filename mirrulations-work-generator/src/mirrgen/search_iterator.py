import datetime
import pytz
from requests import HTTPError


class SearchIterator:
    """
    Iterate over all date older than a specified date.

    Note:  The regulations.gov expects dates to be *passed*
    as US/Eastern (i.e. U.S Eastern timezone WITH DST), but
    it *returns* dates in UTC.  This class takes UTC time as
    its parameter and handles the conversions internally.
    """

    def __init__(self, api, endpoint, datetime_str_utc):

        self.est = pytz.timezone('US/Eastern')
        self.utc = pytz.utc
        query_datetime = datetime.datetime.fromisoformat(datetime_str_utc)\
            .replace(tzinfo=self.utc)
        query_datetime_str = query_datetime.astimezone(self.est)\
            .strftime('%Y-%m-%d %H:%M:%S')
        self.api = api
        self.url = f'https://api.regulations.gov/v4/{endpoint}'
        self.next_page = 1
        self.params = {
            'sort': 'lastModifiedDate',
            'page[size]': 250,
            'filter[lastModifiedDate][ge]': query_datetime_str
        }
        self.iteration_done = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.iteration_done:
            raise StopIteration

        # If the download results in an error, don't
        # iterate next_page.  This will cause the download
        # to be re-tried next iteration.  This could cause an
        # infinite loop, but it handles a period 500-error, which
        # we were seeing.
        try:
            self.params['page[number]'] = self.next_page
            result = self.api.download(self.url, self.params)
            self.next_page += 1
        except HTTPError as error:
            print(f'FAILED: {self.url}\n{error}')
            return {}

        self.iteration_done = self.check_if_done(result)

        return result

    def check_if_done(self, result):
        if result['meta']['pageNumber'] != result['meta']['totalPages']:
            return False

        if result['meta']['totalElements'] <= 5000:
            self.iteration_done = True
            return True

        # Reset for the next search
        self.next_page = 1
        # Dates in data have T between date and time and Z at end
        # Dates in query have a space between and nothing at the end
        last_date = result['data'][-1]['attributes']['lastModifiedDate']\
            .replace('T', ' ').replace('Z', '')
        # Dates in the data are UTC, but dates in query are EST
        # Covert the date to the proper form.
        last_utc = datetime.datetime.fromisoformat(last_date).replace(
            tzinfo=self.utc)
        next_date = last_utc.astimezone(self.est).strftime('%Y-%m-%d %H:%M:%S')
        self.params['filter[lastModifiedDate][ge]'] = next_date

        return False
