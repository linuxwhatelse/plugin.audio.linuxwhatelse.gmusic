import xbmcgui
import xbmcaddon

from addon import utils
from addon import thumbs

from addon import addon
from addon import mpr
from addon import url
from addon import addon_handle
from addon import listing
from addon import gmusic


@mpr.url('^/browse/artist/$', type_cast={'allow_view_overwrite': bool})
def artist(artist_id, allow_view_overwrite=True):
    if artist_id:
        items = [
            ( utils.build_url(url=url, paths=['browse', 'artist', 'top-songs'],       r_path=True), xbmcgui.ListItem(label=utils.translate(30066, addon), iconImage=thumbs.IMG_STAR,   thumbnailImage=thumbs.IMG_STAR), True ),
            ( utils.build_url(url=url, paths=['browse', 'artist', 'related-artists'], r_path=True), xbmcgui.ListItem(label=utils.translate(30067, addon), iconImage=thumbs.IMG_ARTIST, thumbnailImage=thumbs.IMG_ARTIST),     True ),
        ]

        items += listing.build_album_listitems(gmusic.get_artist_info(artist_id=artist_id, include_albums=True, max_top_tracks=0, max_rel_artist=0)['albums'])
        listing.list_albums(items, allow_view_overwrite)

@mpr.url('^/browse/artist/top-songs/$')
def artist_top_tracks(artist_id):
    if artist_id:
        artist = gmusic.get_artist_info(artist_id=artist_id, include_albums=False, max_top_tracks=100, max_rel_artist=0)
        if 'topTracks' in artist:
            items = listing.build_song_listitems(artist['topTracks'])
            listing.list_songs(items)

@mpr.url('^/browse/artist/related-artists/$')
def artist_related_artists(artist_id):
    if artist_id:
        artist = gmusic.get_artist_info(artist_id=artist_id, include_albums=False, max_top_tracks=0, max_rel_artist=100)
        if 'related_artists' in artist:
            items = listing.build_artist_listitems(artist['related_artists'])
            listing.list_artists(items)

@mpr.url('^/browse/album/$', type_cast={'allow_view_overwrite': bool})
def album(album_id, allow_view_overwrite=True):
    if album_id:
        items = listing.build_song_listitems(gmusic.get_album_info(album_id=album_id)['tracks'])
        listing.list_songs(items, allow_view_overwrite)

@mpr.url('^/browse/shared-playlist/$')
def listen_now_shared_playlist(playlist_token):
    playlist_content = gmusic.get_shared_playlist_contents(share_token=playlist_token)

    tracks=[]
    for item in playlist_content:
        tracks.append(item['track'])

    items = listing.build_song_listitems(tracks)
    listing.list_songs(items)

@mpr.url('^/browse/station/$')
def station(station_id=None, station_name=None, artist_id=None, album_id=None,
        track_id=None, genre_id=None, curated_station_id=None,
        playlist_token=None, allow_view_overwrite=True):
    allow_view_overwrite = False if allow_view_overwrite == 'False' else True

    if not station_id:
        station_id = gmusic.create_station(name=station_name, artist_id=artist_id,
            album_id=album_id, track_id=track_id, genre_id=genre_id,
            curated_station_id=curated_station_id, playlist_token=playlist_token)

        if not station_id:
            utils.notify(utils.translate(30050, addon), utils.translate(30051, addon))
            return


    tracks = gmusic.get_station_tracks(station_id=station_id, num_tracks=25)

    items = listing.build_song_listitems(tracks=tracks, station_id=station_id)
    listing.list_songs(items, allow_view_overwrite)
