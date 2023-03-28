import time
import requests


MIN_DELAY_BETWEEN_CALLS = 3600 / 1000


class RegulationsAPI:
    """
    Wrapper for making calls to the regulations.gov API.

    The class handles attaching the API key to the parameters
    and it adds a delay between calls to ensure less than 1000
    calls per hour.
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def download(self, url, params=None):
        time.sleep(MIN_DELAY_BETWEEN_CALLS)
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        result = requests.get(url, params=params, timeout=10)
        result.raise_for_status()
        return result.json()
