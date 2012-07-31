import requests
import json

from .api import TwitterError
from .auth import NoAuth

class TwitterAPI(object):

    def __init__(self, host='api.twitter.com', api_ver='1', auth=NoAuth()):
        self.host = host
        self.api_ver = api_ver
        self.auth = auth


    def get(self, path, **kwargs):
        url, remaining_params = make_url(self.host, self.api_ver, path, kwargs)
        data = self.auth.encode_params(url, 'GET', remaining_params)
        res = requests.get(url + '?' + data)
        assert res.status_code == 200
        result = json.loads(res.text)
        return result


_default_api = TwitterAPI()

get = _default_api.get


_search_api = TwitterAPI(host="search.twitter.com", api_ver=None)

def search(q, **kwargs):
    return _search_api.get("search", q=q, **kwargs)


def make_url(host, api_ver, path, params):
    remaining_params = dict(params)
    real_params = []
    for param in path.split('/'):
        if param.startswith(':'):
            if param[1:] not in params:
                raise TwitterError("Missing parameter for ':{}'".format(param))
            param = str(params.pop(param[1:]))
        real_params.append(param)
    real_path = '/'.join(real_params)
    api_ver_str = '{}/'.format(str(api_ver)) if api_ver is not None else ""
    url = 'http://{}/{}{}.json'.format(host, str(api_ver_str), real_path)
    return url, remaining_params
