from urllib import urlencode
import urllib2
from wham.httmock import urlmatch
from os.path import join
from os import listdir
from os.path import isfile, join
from urlparse import urlparse, parse_qs, parse_qsl


# def mock_function_builder(scheme, netloc, url_name, settings, responses_dir):
#     url_path = settings['url_path']
#     params = settings.get('params', {})
#     method = settings.get('method', 'GET')
#     @urlmatch(scheme=scheme, netloc=netloc, path=url_path, method=method, params=params)
#     def mock_function(_url, _request):
#         with open(join(responses_dir, url_name)) as f:
#             return f.read()
#     return mock_function


def build_httmock_function(scheme, netloc, url_path, response_content, method='GET', params=None):
    if params is None:
        params = {}
    @urlmatch(scheme=scheme, netloc=netloc, path=url_path, method=method, params=params)
    def mock_function(_url, _request):
        return response_content
    return mock_function


def build_httmock_functions(mock_response_dir):
    print 'building mock functions'
    functions = []
    for filename in listdir(mock_response_dir):
        filepath = join(mock_response_dir,filename)
        if isfile(filepath):
            method = None
            for _method in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
                if filename.startswith(_method):
                    filename = filename[len(_method):]
                    method = _method

            url = urllib2.unquote(filename)

            parts = urlparse(url)
            params = {}
            if parts.query:
                print parts.query
                params = dict(parse_qsl(parts.query))
                print params
            with open(filepath) as f:
                content = f.read()
                functions.append(build_httmock_function(
                    parts.scheme, parts.netloc, parts.path, content, params=params, method=method))
    return functions


def make_mock_response_file(url, content, output_dir, method='GET', extra_params=None):
    if extra_params:
        url += '?' + urlencode(extra_params)
    path = output_dir + method + urllib2.quote(url, safe='')
    print path
    with open(path, 'w') as f:
        f.write(content)