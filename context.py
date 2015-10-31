from urlparse import urlparse, parse_qsl

from xbmc      import executebuiltin, getInfoLabel
from xbmcaddon import Addon
from xbmcgui   import Dialog

from mapper import build_url

from gmusic import GMusic
from utils import translate

_addon = Addon()

_addon_path = 'plugin://plugin.audio.linuxwhatelse.gmusic'

def run(track_id):
    dialog = Dialog()

    data = [
        translate(30037, _addon),  # Add to my Library
        translate(30038, _addon),  # Add to Playlist
        translate(30034, _addon),  # Go to Artist
        translate(30035, _addon),  # Go to Album
        translate(30041, _addon),  # Rate song
    ]

    selection = dialog.select(translate(30060, _addon), data, 0)

    if selection == -1:
        return

    if selection == 0:  # Add to my Library
        executebuiltin('RunPlugin(%s)' % build_url(_addon_path, ['my-library', 'add'], {'track_id': track_id}))

    elif selection == 1:  # Add to Playlist
        executebuiltin('RunPlugin(%s)' % build_url(_addon_path, ['my-library', 'playlist', 'add'], {'track_id': track_id}))

    elif selection == 2:  # Go to Artist
        gmusic = GMusic(debug_logging=True, validate=True, verify_ssl=True)
        gmusic.login()
        track = gmusic.get_track_info(track_id)

        if 'artistId' in track and len(track['artistId']) > 0:
            executebuiltin('Container.Update(%s)' % build_url(_addon_path, ['browse', 'artist'], {'artist_id': track['artistId'][0]}))

    elif selection == 3:  # Go to Album
        gmusic = GMusic(debug_logging=True, validate=True, verify_ssl=True)
        gmusic.login()
        track = gmusic.get_track_info(track_id)

        if 'albumId' in track:
            executebuiltin('Container.Update(%s)' % build_url(_addon_path, ['browse', 'album'], {'album_id': track['albumId']}))

    elif selection == 4:  # Rate song
        executebuiltin('RunPlugin(%s)' % build_url(_addon_path, ['rate'], {'track_id': track_id}))


if __name__ == '__main__':
    query = parse_qsl(urlparse(getInfoLabel('ListItem.FileNameAndPath')).query)
    track_id = dict(query)['track_id']

    run(track_id)