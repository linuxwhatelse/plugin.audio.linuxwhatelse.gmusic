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

    is_setup = mapper.call(mapper.build_url(url=url, paths=['setup'], overwrite_path=True, overwrite_query=True))
    if is_setup:
        mapper.call(url)
