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


@MPR.s_url('/browse/my-library/')
def my_library():
    playlists = xbmcgui.ListItem(utils.translate(30020))
    playlists.setArt({
        'thumb': thumbs.IMG_PLAYLIST,
        'poster': thumbs.IMG_PLAYLIST
    })

    stations = xbmcgui.ListItem(utils.translate(30021))
    stations.setArt({
        'thumb': thumbs.IMG_STATION,
        'poster': thumbs.IMG_STATION
    })

    artists = xbmcgui.ListItem(utils.translate(30022))
    artists.setArt({
        'thumb': thumbs.IMG_ARTIST,
        'poster': thumbs.IMG_ARTIST
    })

    albums = xbmcgui.ListItem(utils.translate(30023))
    albums.setArt({
        'thumb': thumbs.IMG_ALBUM,
        'poster': thumbs.IMG_ALBUM
    })

    songs = xbmcgui.ListItem(utils.translate(30024))
    songs.setArt({
        'thumb': thumbs.IMG_TRACK,
        'poster': thumbs.IMG_TRACK
    })
    genres = xbmcgui.ListItem(utils.translate(30025))
    genres.setArt({
        'thumb': thumbs.IMG_GENRE,
        'poster': thumbs.IMG_GENRE
    })

    items = [
        (
            utils.build_url(URL, ['playlists']),
            playlists,
            True
        ),
        (
            utils.build_url(URL, ['stations']),
            stations,
            True
        ),
        (
            utils.build_url(URL, ['artists']),
            artists,
            True
        ),
        (
            utils.build_url(URL, ['albums']),
            albums,
            True
        ),
        (
            utils.build_url(URL, ['songs']),
            songs,
            True
        ),
        (
            utils.build_url(URL, ['genres']),
            genres,
            True
        ),
    ]

    listing.list_items(items)


@MPR.s_url('/browse/my-library/playlists/')
def my_library_playlists():
    # Auto playlists - "Thumbs up" and "Last added"

    thumbs_up = xbmcgui.ListItem(utils.translate(30027))
    thumbs_up.setArt({
        'thumb': thumbs.IMG_THUMB_UP,
        'poster': thumbs.IMG_THUMB_UP
    })

    last_added = xbmcgui.ListItem(utils.translate(30026))
    last_added.setArt({
        'thumb': thumbs.IMG_CLOCK,
        'poster': thumbs.IMG_CLOCK
    })

    items = [
        (
            utils.build_url(
                url=URL,
                paths=['browse', 'my-library', 'playlist', 'thumbsup'],
                r_path=True,
                r_query=True
            ),
            thumbs_up,
            True
        ),
        (
            utils.build_url(
                url=URL,
                paths=['browse', 'my-library', 'playlist', 'lastadded'],
                r_path=True,
                r_query=True
            ),
            last_added,
            True
        ),
    ]

    # User playlists
    items += listing.build_playlist_listitems(GMUSIC.get_user_playlists())
    listing.list_playlists(items)


@MPR.s_url('/browse/my-library/playlist/<playlist_id>/')
def my_library_playlist(playlist_id):
    my_library = False
    my_library_playlist = False

    items = []
    if playlist_id == 'thumbsup':
        items = GMUSIC.get_promoted_songs()

    elif playlist_id == 'lastadded':
        items = GMUSIC.get_user_lastadded()
        my_library = True

    else:
        playlist = GMUSIC.get_user_playlist(playlist_id)

        if playlist and 'tracks' in playlist:
            items = playlist['tracks']

        my_library_playlist = True

    items = listing.build_song_listitems(
        tracks=items,
        my_library=my_library,
        my_library_playlist=my_library_playlist
    )

    listing.list_songs(items)


@MPR.s_url('/browse/my-library/stations/')
def my_library_stations():
    stations = GMUSIC.get_all_stations()
    stations = sorted(stations, key=itemgetter('lastModifiedTimestamp'),
                      reverse=True)

    items = listing.build_station_listitems(stations)
    listing.list_stations(items)


@MPR.s_url('/browse/my-library/artists/')
def my_library_artists():
    artists = GMUSIC.get_my_library_artists()
    items = listing.build_artist_listitems(artists, True)
    listing.list_artists(items)


@MPR.s_url('/browse/my-library/artist/<artist_id>/')
def my_library_artist(artist_id):
    if artist_id:
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

        all_albums = xbmcgui.ListItem(utils.translate(30098))
        all_albums.setArt({
            'thumb': thumbs.IMG_ALBUM,
            'poster': thumbs.IMG_ALBUM
        })

        items = [
            (
                utils.build_url(
                    url=URL,
                    paths=['browse', 'artist', artist_id, 'top-songs'],
                    r_path=True,
                    r_query=True,
                ),
                top_songs,
                True
            ),
            (
                utils.build_url(
                    url=URL,
                    paths=['browse', 'artist', artist_id, 'related-artists'],
                    r_path=True,
                    r_query=True,
                ),
                related_artists,
                True
            ),
            (
                utils.build_url(
                    url=URL,
                    paths=['browse', 'artist', artist_id],
                    r_path=True,
                    r_query=True,
                ),
                all_albums,
                True
            ),
        ]

        albums = GMUSIC.get_user_artist_albums(artist_id=artist_id)
        albums.sort(key=itemgetter('name'))
        albums.sort(key=itemgetter('year'), reverse=True)

        items += listing.build_album_listitems(albums, True)

        listing.list_albums(items)


@MPR.s_url('/browse/my-library/albums/')
def my_library_albums():
    albums = GMUSIC.get_my_library_albums()
    items = listing.build_album_listitems(albums, True)

    listing.list_albums(items)


@MPR.s_url('/browse/my-library/album/<album_id>/')
def my_library_album(album_id):
    songs = GMUSIC.get_user_album_songs(album_id=album_id)
    items = listing.build_song_listitems(songs, my_library=True)

    listing.list_songs(items)


@MPR.s_url('/browse/my-library/songs/')
def my_library_songs():
    items = listing.build_song_listitems(
        tracks=GMUSIC.get_my_library_songs(),
        my_library=True
    )

    listing.list_songs(items)


@MPR.s_url('/browse/my-library/genres/')
def my_library_genres():
    genres = GMUSIC.get_my_library_genres()

    items = []
    for genre in genres:
        item = xbmcgui.ListItem(genre)
        item.setArt({
            'thumb': thumbs.IMG_GENRE,
            'poster': thumbs.IMG_GENRE
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['browse', 'my-library', 'genre', genre],
                r_path=True
            ),
            item,
            True
        ))

    listing.list_items(items)


@MPR.s_url('/browse/my-library/genre/<genre>/')
def my_library_genre(genre):
    albums = GMUSIC.get_user_genre_albums(genre=genre)
    items = listing.build_album_listitems(albums, True)

    listing.list_albums(items)
