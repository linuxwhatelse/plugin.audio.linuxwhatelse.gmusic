import time

import xbmc

from addon.gmusic_wrapper import GMusic

from addon import ADDON


GMUSIC = GMusic.get(debug_logging=False)


def _get_update_interval():
    try:
        update_interval = int(ADDON.getSetting('update_interval'))
    except Exception:
        update_interval = 0

    return update_interval * 60 * 60  # We need seconds


def _get_library_last_updated():
    try:
        library_last_updated = int(ADDON.getSetting('library_last_updated'))
    except Exception:
        library_last_updated = 0

    return library_last_updated


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(30):
            # Abort was requested while waiting. We should exit
            break

        update_interval = _get_update_interval()
        library_last_updated = _get_library_last_updated()

        if update_interval == 0:
            continue

        if time.time() >= library_last_updated + update_interval:
            ADDON.setSetting('library_last_updated', str(int(time.time())))

            try:
                if GMUSIC.login():
                    GMUSIC.get_my_library_songs(from_cache=False)
                    GMUSIC.get_my_library_artists(from_cache=False)
                    GMUSIC.get_my_library_albums(from_cache=False)

            except Exception:
                continue
