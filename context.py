import urlparse

import xbmc
import xbmcaddon
import xbmcgui

# Adds all librarys to our path (see lib/__init__.py)
import resources.libs

import mapper
from gmusic import GMusic

import utils

_addon = xbmcaddon.Addon()

_addon_path = 'plugin://plugin.audio.linuxwhatelse.gmusic'

def run(track_id):
    dialog = xbmcgui.Dialog()

    data = [
        utils.translate(30037, _addon),  # Add to my Library
        utils.translate(30038, _addon),  # Add to Playlist
        utils.translate(30034, _addon),  # Go to Artist
        utils.translate(30035, _addon),  # Go to Album
        utils.translate(30041, _addon),  # Rate song
    ]

    selection = dialog.select(utils.translate(30060, _addon), data, 0)
    if selection == -1:
        return

    if selection == 0:  # Add to my Library
        xbmc.executebuiltin('RunPlugin(%s)' % mapper.build_url(_addon_path, ['my-library', 'add'], {'track_id': track_id}))

    elif selection == 1:  # Add to Playlist
        xbmc.executebuiltin('RunPlugin(%s)' % mapper.build_url(_addon_path, ['my-library', 'playlist', 'add'], {'track_id': track_id}))

    elif selection == 2:  # Go to Artist
        gmusic = GMusic(debug_logging=True, validate=True, verify_ssl=True)
        gmusic.login()
        track = gmusic.get_track_info(track_id)

        if 'artistId' in track and len(track['artistId']) > 0:
            xbmc.executebuiltin('ActivateWindow(music, %s, return)' % mapper.build_url(_addon_path, ['browse', 'artist'], {'artist_id': track['artistId'][0]}))

    elif selection == 3:  # Go to Album
        gmusic = GMusic(debug_logging=True, validate=True, verify_ssl=True)
        gmusic.login()
        track = gmusic.get_track_info(track_id)

        if 'albumId' in track:
            xbmc.executebuiltin('ActivateWindow(music, %s, return)' % mapper.build_url(_addon_path, ['browse', 'album'], {'album_id': track['albumId']}))

    elif selection == 4:  # Rate song
        xbmc.executebuiltin('RunPlugin(%s)' % mapper.build_url(_addon_path, ['rate'], {'track_id': track_id}))


if __name__ == '__main__':
    query = urlparse.parse_qsl(urlparse.urlparse(xbmc.getInfoLabel('ListItem.FileNameAndPath')).query)
    track_id = dict(query)['track_id']

    run(track_id)
