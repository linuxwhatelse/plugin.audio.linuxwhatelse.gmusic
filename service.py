import time

import xbmc
import xbmcaddon

import utils

# Adds all librarys to our path (see lib/__init__.py)
import resources.libs

from gmusic import GMusic

if __name__ == '__main__':
    addon  = xbmcaddon.Addon()
    gmusic = GMusic(debug_logging=False, validate=True, verify_ssl=True)

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        time.sleep(1)

        try:
            update_interval = int(addon.getSetting('update_interval'))
        except:
            update_interval = 0

        try:
            library_last_updated = int(addon.getSetting('library_last_updated'))
        except:
            library_last_updated = 0

        if update_interval == 0:
            continue

        if time.time() >= library_last_updated + update_interval:
            gmusic.login()

            gmusic.get_my_library_songs(from_cache=False)
            gmusic.get_my_library_artists(from_cache=False)
            gmusic.get_my_library_albums(from_cache=False)

            addon.setSetting('library_last_updated', str(int(time.time())))
