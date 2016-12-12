import os
import json
import urllib
import urlparse

import xbmc
import xbmcaddon

addon = xbmcaddon.Addon()

def log(*args, **kwargs):
    if not kwargs or 'lvl' not in kwargs:
        lvl = xbmc.LOGNOTICE

    else:
        lvl = kwargs['lvl']

    msg = '[%s] ' % addon.getAddonInfo('name')
    msg += ' '.join(str(x) for x in args)

    xbmc.log(msg, level=lvl)

def notify(title, message, icon=None, display_time=5000):
    if not icon:
        icon = addon.getAddonInfo('icon')

    xbmc.executebuiltin('Notification(%s, %s, %s, %s)' % (title, message, display_time, icon))

def translate(id):
    return addon.getLocalizedString(id)

def get_cache_dir(sub_dir=None):
    if not sub_dir:
        sub_dir = []

    cache_dir = xbmc.translatePath(
        os.path.join(addon.getAddonInfo('profile'), '.cache', *sub_dir))

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir

def get_current_track_id(key_name='track_id'):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

    if len(playlist) <= 0:
        return None

    playlist_item = playlist[playlist.getposition()]
    path = playlist_item.getfilename()

    track_id = path.rstrip('/').rsplit('/', 1)[1]

    if track_id and track_id.startswith('T'):
        return track_id

    else:
        return None


def execute_jsonrpc(method, params=None):
    data = {}
    data['id']         = 1
    data['jsonrpc']    = '2.0'
    data['method']     = method
    if params:
        data['params'] = params

    data = json.dumps(data)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return response
    except KeyError:
        return None

def build_url(url, paths=None, queries=None, r_path=False, r_query=False):
    """Build new urls by adding/overwriting path-fragments and/or queries
    Args:
        url (str): Existing url where new path-fragments and/or queries need to be appended
            or existing ones overwritten
        paths (Optional[list]): list of path-fragments to append to the url
        queries (Optional[dict]): dict which will be used as query for the url
        r_path (Optional[bool]): If the existing path of ``url``
            should be replaced with the ``paths``
        r_query (Optional[bool]): If the existing query of ``url``
            should be replaced with the new ``queries``
    """
    if not paths:
        paths = []

    if not queries:
        queries = {}

    scheme, netloc, path, query_string, fragment = urlparse.urlsplit(url)

    # Build new path
    # We'r using os.path.join instead of urlparse.urlparse.urljoin because it doesn't
    # require use to have segemnts start/end with '/' making everything much
    # easier
    if not path or r_path:
        path = '/'

    path = os.path.join(path, *paths)

    # e.g. on windows we have to swap escaped '\' with a single '/' due to us
    # using os.path.join
    path = path.replace('\\', '/')

    # Make sure we end with a '/' for now
    path = path.rstrip('/') + '/'

    # Build new query
    query_params = {}
    if r_query:
        for param_name, param_value in queries.items():
            query_params[param_name] = [param_value]

    else:
        query_params = urlparse.parse_qs(query_string)
        for param_name, param_value in queries.items():
            query_params[param_name] = [param_value]

    new_query_string = urllib.urlencode(query_params, doseq=True)

    # If a query exists, get rid of the paths trailing '/'
    if new_query_string:
        path = path.rstrip('/')

    return urlparse.urlunsplit((scheme, netloc, path, new_query_string, fragment))
