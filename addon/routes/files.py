from addon import utils

from addon import mpr
from addon import url


@mpr.url('^/track/$')
@mpr.url('^/track/(?P<title>.*)/$')
def track(title=None, track_id=None):
    mpr.call(utils.build_url(url=url, paths=['play', 'track'], r_path=True))

@mpr.url('^/artist/$')
def album(album_id):
    mpr.call(utils.build_url(url=url, paths=['browse', 'artist'],
        queries={'allow_view_overwrite': False}, r_path=True))

@mpr.url('^/album/$')
def album(album_id):
    mpr.call(utils.build_url(url=url, paths=['browse', 'album'],
        queries={'allow_view_overwrite': False}, r_path=True))

@mpr.url('^/playlist/$')
def playlist(playlist_id=None, playlist_token=None):
    if playlist_id:
        mpr.call(utils.build_url(url=url, paths=['browse', 'my-library', 'playlist'],
            queries={'allow_view_overwrite': False}, r_path=True))

    elif playlist_token:
        mpr.call(utils.build_url(url=url, paths=['browse', 'shared-playlist'],
            queries={'allow_view_overwrite': False}, r_path=True))

@mpr.url('^/station/$')
def station(station_id=None, station_name=None, artist_id=None, album_id=None,
        genre_id=None, track_id=None, curated_station_id=None, playlist_token=None):
    mpr.call(utils.build_url(url=url, paths=['browse', 'station'],
        queries={'allow_view_overwrite': False}, r_path=True))
