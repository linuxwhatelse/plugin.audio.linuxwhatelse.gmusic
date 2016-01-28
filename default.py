from os import chdir
from urlparse import urlparse

from xbmcaddon import Addon

import mapper

import listing
import utils

# Adds all librarys to our path (see lib/__init__.py)
import resources.libs

addon_handle = int(sys.argv[1])
url          = sys.argv[0] + sys.argv[2]

if urlparse(url).path == '/':
    url = mapper.build_url(url, ['browse'])

_listing     = listing.Listing(url, addon_handle)

# Includes some more routs for the mapper
from routes import home
home.url          = url
home.addon_handle = addon_handle
home.listing      = _listing

from routes import listen_now
listen_now.url          = url
listen_now.addon_handle = addon_handle
listen_now.listing      = _listing

from routes import top_charts
top_charts.url          = url
top_charts.addon_handle = addon_handle
top_charts.listing      = _listing

from routes import new_releases
new_releases.url          = url
new_releases.addon_handle = addon_handle
new_releases.listing      = _listing

from routes import my_library
my_library.url          = url
my_library.addon_handle = addon_handle
my_library.listing      = _listing

from routes import browse_stations
browse_stations.url          = url
browse_stations.addon_handle = addon_handle
browse_stations.listing      = _listing

from routes import others
others.url          = url
others.addon_handle = addon_handle
others.listing       = _listing

from routes import actions
actions.url          = url
actions.addon_handle = addon_handle
actions.listing      = _listing

from routes import files
files.url          = url
files.addon_handle = addon_handle
files.listing      = _listing


if __name__ == '__main__':
    # The initial login to google will be logged, therefor we make sure the logfile
    # will be written into our cache dir
    # On Windows the default directory would be Kodis installation dir where we can
    # NOT assume to have write rights
    chdir(utils.get_cache_dir())

    is_setup = mapper.call(mapper.build_url(url=url, paths=['setup'], overwrite_path=True, overwrite_query=True))
    if is_setup:
        mapper.call(url)
