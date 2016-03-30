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


@mpr.url('^/browse/my-library/$')
def my_library():
    items = [
        # URL , ListItem, isFolder
        ( utils.build_url(url, ['playlists']), xbmcgui.ListItem(label=utils.translate(30020, addon), iconImage=thumbs.IMG_PLAYLIST, thumbnailImage=thumbs.IMG_PLAYLIST), True ),
        ( utils.build_url(url, ['stations']),  xbmcgui.ListItem(label=utils.translate(30021, addon), iconImage=thumbs.IMG_STATION,  thumbnailImage=thumbs.IMG_STATION),  True ),
        ( utils.build_url(url, ['artists']),   xbmcgui.ListItem(label=utils.translate(30022, addon), iconImage=thumbs.IMG_ARTIST,   thumbnailImage=thumbs.IMG_ARTIST),   True ),
        ( utils.build_url(url, ['albums']),    xbmcgui.ListItem(label=utils.translate(30023, addon), iconImage=thumbs.IMG_ALBUM,    thumbnailImage=thumbs.IMG_ALBUM),    True ),
        ( utils.build_url(url, ['songs']),     xbmcgui.ListItem(label=utils.translate(30024, addon), iconImage=thumbs.IMG_TRACK,    thumbnailImage=thumbs.IMG_TRACK),    True ),
        ( utils.build_url(url, ['genres']),    xbmcgui.ListItem(label=utils.translate(30025, addon), iconImage=thumbs.IMG_GENRE,    thumbnailImage=thumbs.IMG_GENRE),    True ),
    ]

    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)

@mpr.url('^/browse/my-library/playlists/$')
def my_library_playlists():
    # Auto playlists
    items = [
        ( utils.build_url(url=url, paths=['browse', 'my-library', 'playlist'], queries={'playlist_id': 'thumbsup'}, r_path=True, r_query=True), \
            xbmcgui.ListItem(label=utils.translate(30027, addon), iconImage=thumbs.IMG_THUMB_UP, thumbnailImage=thumbs.IMG_THUMB_UP), True ),

        ( utils.build_url(url=url, paths=['browse', 'my-library', 'playlist'], queries={'playlist_id': 'lastadded'}, r_path=True, r_query=True),\
            xbmcgui.ListItem(label=utils.translate(30026, addon), iconImage=thumbs.IMG_CLOCK, thumbnailImage=thumbs.IMG_CLOCK), True ),
    ]

    for item, playlist_id in zip(items, ['thumbsup', 'lastadded']):
        item[1].addContextMenuItems(
            items=[
                (utils.translate(30033, addon), 'XBMC.RunPlugin(%s)' % utils.build_url(url, ['play', 'playlist'], {'playlist_id': playlist_id}, True, True))
            ],
            replaceItems=True
        )


    # User playlists
    items += listing.build_playlist_listitems(gmusic.get_user_playlists())

    listing.list_playlists(items)

@mpr.url('^/browse/my-library/playlist/$')
def my_library_playlist(playlist_id, allow_view_overwrite=True):
    if playlist_id:
        my_library = False
        my_library_playlist = False

        items = []
        if playlist_id == 'thumbsup':
            items = gmusic.get_promoted_songs()

        elif playlist_id == 'lastadded':
            items = gmusic.get_user_lastadded()
            my_library = True

        else:
            playlist = gmusic.get_user_playlist(playlist_id)

            if playlist and 'tracks' in playlist:
                items = playlist['tracks']

            my_library_playlist = True

        items = listing.build_song_listitems(tracks=items, my_library=my_library, my_library_playlist=my_library_playlist)
        listing.list_songs(items, allow_view_overwrite)

@mpr.url('^/browse/my-library/stations/$')
def my_library_stations():
    stations = gmusic.get_all_stations()
    stations = sorted(stations, key=lambda k: k['lastModifiedTimestamp'], reverse=True)
    items = listing.build_station_listitems(stations)
    listing.list_stations(items)

@mpr.url('^/browse/my-library/artists/$')
def my_library_artists():
    items = listing.build_artist_listitems(gmusic.get_my_library_artists(), True)
    listing.list_artists(items)

@mpr.url('^/browse/my-library/artist/$')
def my_library_artist(artist_id):
    if artist_id:
        items = [
            ( utils.build_url(url=url, paths=['browse', 'artist', 'top-songs'],       r_path=True), xbmcgui.ListItem(label=utils.translate(30066, addon), iconImage=thumbs.IMG_STAR,   thumbnailImage=thumbs.IMG_STAR), True ),
            ( utils.build_url(url=url, paths=['browse', 'artist', 'related-artists'], r_path=True), xbmcgui.ListItem(label=utils.translate(30067, addon), iconImage=thumbs.IMG_ARTIST, thumbnailImage=thumbs.IMG_ARTIST),     True ),
        ]

        items += listing.build_album_listitems(gmusic.get_user_artist_albums(artist_id=artist_id), True)
        listing.list_albums(items)

@mpr.url('^/browse/my-library/albums/$')
def my_library_albums():
    items = listing.build_album_listitems(gmusic.get_my_library_albums(), True)
    listing.list_albums(items)

@mpr.url('^/browse/my-library/album/$')
def my_library_album(album_id):
    if album_id:
        items = listing.build_song_listitems(tracks=gmusic.get_user_album_songs(album_id=album_id), my_library=True)
        listing.list_songs(items)

@mpr.url('^/browse/my-library/songs/$')
def my_library_songs():
    items = listing.build_song_listitems(tracks=gmusic.get_my_library_songs(), my_library=True)
    listing.list_songs(items)

@mpr.url('^/browse/my-library/genres/$')
def my_library_genres():
    genres = gmusic.get_my_library_genres()

    items=[]
    for genre in genres:
        if 'name' not in genre:
            continue

        genre_name = genre['name']
        genre_art  = genre['image'] if 'image' in genre else ''

        items.append((
                utils.build_url(url=url, paths=['browse', 'my-library', 'genre'], \
                    queries={'genre': genre['name']}, r_path=True, r_query=True),
                xbmcgui.ListItem(
                    label           = genre_name,
                    iconImage       = genre_art,
                    thumbnailImage  = genre_art,
                ),
            True
        ))

    listing.list_items(items)

@mpr.url('^/browse/my-library/genre/$')
def my_library_genre(genre):
    if genre:
        items = listing.build_album_listitems(gmusic.get_user_genre_albums(genre=genre), True)
        listing.list_albums(items)
