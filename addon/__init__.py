import sys

import xbmcaddon

# Adds all libraries to our path
# see "resources/libs/lib/__init__.py"
import resources.libs  # noqa


ADDON = xbmcaddon.Addon()

ADDON_HANDLE = None
URL = None


if len(sys.argv) > 1:
    ADDON_HANDLE = int(sys.argv[1])
    URL = sys.argv[0] + sys.argv[2]

    if URL == 'plugin://plugin.audio.linuxwhatelse.gmusic/':
        from addon import utils
        URL = utils.build_url(URL, ['browse'])
