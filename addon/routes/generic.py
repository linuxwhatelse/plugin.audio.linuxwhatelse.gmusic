from operator import itemgetter

import xbmcgui

import mapper

from addon.gmusic_wrapper import GMusic
from addon import utils
from addon import listing
from addon import thumbs

from addon import URL


MPR = mapper.Mapper.get()
GMUSIC = GMusic.get(debug_logging=False)


@MPR.s_url('/browse/artist/<artist_id>/')
def artist(artist_id):
    top_songs = xbmcgui.ListItem(utils.translate(30066))
    top_songs.setArt({
        'thumb': thumbs.IMG_STAR,
        'poster': thumbs.IMG_STAR
    })

    related_artists = xbmcgui.ListItem(utils.translate(30067))
    related_artists.setArt({
        'thumb': thumbs.IMG_ARTIST,
        'poster': thumbs.IMG_ARTIST
    })

    items = [
        (
            utils.build_url(
                url=URL,
                paths=['browse', 'artist', artist_id, 'top-songs'],
                r_path=True
            ),
            top_songs,
            True
        ),
        (
            utils.build_url(
                url=URL,
                paths=['browse', 'artist', artist_id, 'related-artists'],
                r_path=True
            ),
            related_artists,
            True
        )
    ]

    info = GMUSIC.get_artist_info(artist_id=artist_id, include_albums=True,
                                  max_top_tracks=0, max_rel_artist=0)

    if 'albums' in info:
        albums = info['albums']
        albums.sort(key=itemgetter('name'))
        albums.sort(key=itemgetter('year'), reverse=True)

        items += listing.build_album_listitems(albums)
        listing.list_albums(items)

    else:
        listing.list_items([])


@MPR.s_url('/browse/artist/<artist_id>/top-songs/')
def artist_top_tracks(artist_id):
    artist = GMUSIC.get_artist_info(artist_id=artist_id, include_albums=False,
                                    max_top_tracks=100, max_rel_artist=0)

    if artist and 'topTracks' in artist:
        items = listing.build_song_listitems(artist['topTracks'])
        listing.list_songs(items)

    else:
        listing.list_items([])


@MPR.s_url('/browse/artist/<artist_id>/related-artists/')
def artist_related_artists(artist_id):
    artist = GMUSIC.get_artist_info(artist_id=artist_id, include_albums=False,
                                    max_top_tracks=0, max_rel_artist=100)

    if artist and 'related_artists' in artist:
        items = listing.build_artist_listitems(artist['related_artists'])
        listing.list_artists(items)

    else:
        listing.list_items([])


@MPR.s_url('/browse/album/<album_id>/')
def album(album_id):
    album_info = GMUSIC.get_album_info(album_id=album_id)

    if album_info and 'tracks' in album_info:
        items = listing.build_song_listitems(album_info['tracks'])
        listing.list_songs(items)

    else:
        listing.list_items([])


@MPR.s_url('/browse/shared-playlist/<playlist_token>/')
def listen_now_shared_playlist(playlist_token):
    playlist_content = GMUSIC.get_shared_playlist_contents(
        share_token=playlist_token)

    tracks = []
    for item in playlist_content:
        tracks.append(item['track'])

    items = listing.build_song_listitems(tracks)
    listing.list_songs(items)


@MPR.s_url('/browse/station/')
def station(station_id=None, station_name=None, artist_id=None, album_id=None,
            track_id=None, genre_id=None, curated_station_id=None,
            playlist_token=None):

    if not station_id:
        station_id = GMUSIC.create_station(
            name=station_name, artist_id=artist_id, album_id=album_id,
            track_id=track_id, genre_id=genre_id,
            curated_station_id=curated_station_id,
            playlist_token=playlist_token
        )

        if not station_id:
            utils.notify(utils.translate(30050), utils.translate(30051))
            return

    tracks = GMUSIC.get_station_tracks(station_id=station_id, num_tracks=25)

    items = listing.build_song_listitems(tracks=tracks, station_id=station_id)
    listing.list_songs(items)
