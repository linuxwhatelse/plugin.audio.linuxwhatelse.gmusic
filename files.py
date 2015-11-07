import xbmcplugin
from xbmcaddon import Addon

import mapper

from gmusic import GMusic

# Variables will be set from "default.py"
url          = None
addon_handle = None

_addon    = Addon()
gmusic    = GMusic(debug_logging=False, validate=True, verify_ssl=True)


@mapper.url('^/track/$')
@mapper.url('^/track/(?P<title>.*)/$')
def track(title, track_id):
    mapper.call(mapper.build_url(url=url, paths=['play', 'track'], overwrite_path=True))

@mapper.url('^/artist/$')
def album(album_id):
    mapper.call(mapper.build_url(url=url, paths=['browse', 'artist'], queries={'allow_view_overwrite': False}, overwrite_path=True))

@mapper.url('^/album/$')
def album(album_id):
    mapper.call(mapper.build_url(url=url, paths=['browse', 'album'], queries={'allow_view_overwrite': False}, overwrite_path=True))

@mapper.url('^/playlist/$')
def playlist(playlist_id, shared_token):
    if playlist_id:
        mapper.call(mapper.build_url(url=url, paths=['browse', 'my-library', 'playlist'], queries={'allow_view_overwrite': False}, overwrite_path=True))

    elif shared_token:
        mapper.call(mapper.build_url(url=url, paths=['browse', 'shared-playlist'], queries={'allow_view_overwrite': False}, overwrite_path=True))

@mapper.url('^/station/$')
def station(station_id, station_name, artist_id, album_id, genre_id, track_id, curated_station_id):
    mapper.call(mapper.build_url(url=url, paths=['browse', 'station'], queries={'allow_view_overwrite': False}, overwrite_path=True))