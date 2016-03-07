import time

import xbmc
import xbmcaddon

import utils

# Adds all librarys to our path (see lib/__init__.py)
import resources.libs

from gmusic import GMusic

def _get_update_interval():
    try:
        update_interval = int(addon.getSetting('update_interval'))
    except:
        update_interval = 0

    return update_interval * 60 * 60  # We need seconds

def _get_library_last_updated():
    try:
        library_last_updated = int(addon.getSetting('library_last_updated'))
    except:
        library_last_updated = 0

    return library_last_updated

if __name__ == '__main__':
    addon  = xbmcaddon.Addon()
    gmusic = GMusic(debug_logging=False, validate=True, verify_ssl=True)

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(30):
            # Abort was requested while waiting. We should exit
            break

        update_interval      = _get_update_interval()
        library_last_updated = _get_library_last_updated()

        if update_interval == 0:
            continue

        if time.time() >= library_last_updated + update_interval:
            gmusic.login()

            gmusic.get_my_library_songs(from_cache=False)
            gmusic.get_my_library_artists(from_cache=False)
            gmusic.get_my_library_albums(from_cache=False)

            addon.setSetting('library_last_updated', str(int(time.time())))
