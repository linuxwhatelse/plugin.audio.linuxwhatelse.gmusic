from os import chdir
from urlparse import urlparse

from xbmcaddon import Addon

import mapper

from utils import notify, translate, get_cache_dir

# Adds all librarys to our path (see lib/__init__.py)
import lib

addon_handle = int(sys.argv[1])
url          = sys.argv[0] + sys.argv[2]

if urlparse(url).path == '/':
    url = mapper.build_url(url, ['browse'])


# Includes some more routs for the mapper
import browse
browse.url          = url
browse.addon_handle = addon_handle

import actions
actions.url          = url
actions.addon_handle = addon_handle

import files
files.url          = url
files.addon_handle = addon_handle

if __name__ == '__main__':
    # The initial login to google will be logged, therefor we make sure the logfile
    # will be written into our cache dir
    # On Windows the default directory would be Kodis installation dir where we can
    # NOT assume to have write rights
    chdir(get_cache_dir())
    addon = Addon()
    if not addon.getSetting('username') or not addon.getSetting('password'):
        notify(translate(30046, addon), translate(30047, addon))
        addon.openSettings()
    else:
       mapper.call(url)
