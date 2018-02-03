import mapper

from addon.routes import my_library
from addon.routes import actions
from addon.routes import generic


mpr = mapper.Mapper.get()


@mpr.s_url('/track/<track_id>/')
@mpr.s_url('/track/<track_id>/<title>/')
def track(track_id, title=''):
    actions.play_track(track_id, track_title=title)


@mpr.s_url('/artist/<artist_id>/')
def artist(artist_id):
    generic.artist_top_tracks(artist_id)


@mpr.s_url('/album/<album_id>/')
def album(album_id):
    generic.album(album_id)


@mpr.s_url('/playlist/')
def playlist(playlist_id=None, playlist_token=None):
    if playlist_id:
        my_library.my_library_playlist(playlist_id)

    elif playlist_token:
        generic.listen_now_shared_playlist(playlist_token)


@mpr.s_url('/station/')
def station(station_id=None, station_name=None, artist_id=None, album_id=None,
            genre_id=None, track_id=None, curated_station_id=None,
            playlist_token=None):

    generic.station(station_id, station_name, artist_id, album_id,
                    track_id, genre_id, curated_station_id, playlist_token)
