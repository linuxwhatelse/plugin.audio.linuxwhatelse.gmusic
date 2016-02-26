import os
import json
import urlparse

import xbmc
from xbmcaddon import Addon

def log(message, level=xbmc.LOGDEBUG):
    xbmc.log('%s: %s' % (Addon().getAddonInfo('name'), message), level)

def notify(title, message, icon=None, display_time=5000):
    if not icon:
        icon = os.path.join(Addon().getAddonInfo('path'), 'icon.png')

    xbmc.executebuiltin('Notification(%s, %s, %s, %s)' % (title, message, display_time, icon))

def translate(id, addon=None):
    if not addon:
        addon = Addon()
    return addon.getLocalizedString(id)

def get_cache_dir(addon=None, sub_dir=None):
    if not sub_dir:
        sub_dir = []

    if not addon:
        addon = Addon()

    cache_dir = xbmc.translatePath(os.path.join(addon.getAddonInfo('profile'), '.cache', *sub_dir))

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    return cache_dir

def get_current_track_id(key_name='track_id'):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist_item = playlist[playlist.getposition()]

    path = playlist_item.getfilename()

    query = urlparse.parse_qs(urlparse.urlparse(path).query)

    if not query:
        return None

    if key_name in query:
        return query[key_name][0]

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
