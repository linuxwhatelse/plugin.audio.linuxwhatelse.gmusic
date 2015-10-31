from os.path import join, exists
from os import makedirs
from json import dumps, loads

import xbmc
from xbmcaddon import Addon

def log(message, level=xbmc.LOGDEBUG):
    xbmc.log('%s: %s' % (Addon().getAddonInfo('name'), message), level)

def notify(title, message, icon=None):
    if not icon:
        icon = join(Addon().getAddonInfo('path'), 'icon.png')

    xbmc.executebuiltin('Notification(%s, %s, 5000, %s)' % (title, message, icon))

def translate(id, addon=None):
    if not addon:
        addon = Addon()
    return addon.getLocalizedString(id)

def get_cache_dir(addon=None):
    if not addon:
        addon = Addon()
    
    cache_dir = xbmc.translatePath(join(addon.getAddonInfo('profile'), '.cache'))

    if not exists(cache_dir):
        makedirs(cache_dir)

    return cache_dir

def execute_jsonrpc(method, params=None):
    data = {}
    data['id']         = 1
    data['jsonrpc']    = '2.0'
    data['method']     = method
    if params:
        data['params'] = params

    data = dumps(data)
    request = xbmc.executeJSONRPC(data)

    try:
        response = loads(request)
    except UnicodeDecodeError:
        response = loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return response
    except KeyError:
        return None
