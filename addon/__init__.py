import sys

if len(sys.argv) > 1:
    addon_handle = int(sys.argv[1])
    url          = sys.argv[0] + sys.argv[2]

    if url == 'plugin://plugin.audio.linuxwhatelse.gmusic/':
        from addon import utils
        url = utils.build_url(url, ['browse'])
else:
    addon_handle = None
    url          = None

import xbmcaddon
addon = xbmcaddon.Addon()

import mapper
mpr = mapper.Mapper()

# Adds all libraries to our path
# see "resources/libs/lib/__init__.py"
import resources.libs


# The initial login to google will be logged, therefor we make sure the logfile
# will be written into our cache dir
# On Windows the default directory would be Kodis installation dir where we can
# NOT assume to have write rights
import os
import utils
os.chdir(utils.get_cache_dir())

from gmusic_wrapper import GMusic
gmusic = GMusic(debug_logging=False, validate=True, verify_ssl=True)
