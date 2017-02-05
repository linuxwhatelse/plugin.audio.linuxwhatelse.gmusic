import os
import json
import time

import xbmc
import xbmcgui
import xbmcplugin

from addon import utils
from addon import thumbs

from addon import addon
from addon import url
from addon import addon_handle
from addon import gmusic


def build_artist_listitems(artists, my_library=False):
    items = []
    for artist in artists:
        # Applies to e.g. search results
        if 'artist' in artist:
            artist = artist['artist']

        if 'artistId' not in artist or 'name' not in artist:
            continue

        artist_id   = artist['artistId']
        artist_name = artist['name']
        artist_art  = thumbs.IMG_ARTIST_FLAT
        if 'artistArtRef' in artist:
            artist_art = artist['artistArtRef']

        item = xbmcgui.ListItem(artist_name)

        item.setArt({
            'thumb'  : artist_art,
            'poster' : artist_art,
            #'fanart' : artist_art + '=s1920'
        })

        item.setInfo('music', {
            'mediatype' : 'artist',
            'artist'    : artist_name,
        })

        item.addContextMenuItems(
            items=[(
                utils.translate(30036),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['play', 'station'],
                    queries = {'station_name': artist_name.encode('utf-8'), 'artist_id': artist_id},
                    r_path  = True,
                    r_query = True
                )
            )]
        )

        # My Library entries differ from normal AllAcces ones as users are able
        # to add only parts of the item to there library
        if my_library:
            items.append((
                utils.build_url(
                    url     = url,
                    paths   = ['browse', 'my-library', 'artist', artist_id],
                    r_path  = True,
                    r_query = True
                ),
                item,
                True
            ))

        else:
            items.append((
                utils.build_url(
                    url     = url,
                    paths   = ['browse', 'artist', artist_id],
                    r_path  = True,
                    r_query = True
                ),
                item,
                True
            ))

    return items


def list_artists(listitems):
    xbmcplugin.setContent(addon_handle, 'artists')

    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_ARTIST,
    ]

    list_items(listitems, sort_methods)


def build_album_listitems(albums, my_library=False):
    items = []
    for album in albums:
        # Applies to e.g. search results
        if 'album' in album:
            album = album['album']

        if 'albumId' not in album or 'name' not in album:
            continue

        album_id   = album['albumId']
        album_name = album['name']
        album_art  = thumbs.IMG_ALBUM
        fanart     = None

        if 'albumArtRef' in album:
            album_art = album['albumArtRef']

        if album_art and album_art != thumbs.IMG_ALBUM:
            fanart = album_art + "=w1280-w1280"

        item = xbmcgui.ListItem(album_name)

        item.setArt({
            'thumb'  : album_art,
            'poster' : album_art,
            #'fanart' : fanart
        })

        item.setInfo('music', {
            'mediatype': 'album',
            'album'    : album_name,
            'artist'   : album['albumArtist']  if 'albumArtist' in album else '',
            'genre'    : album['genre']        if 'genre'       in album else '',
            'year'     : album['year']         if 'year'        in album else '',
        })

        menu_items = []

        if not my_library:
            menu_items.append((
                utils.translate(30037),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'add', 'album', album_id],
                    r_path  = True,
                    r_query = True
                )
            ))

        menu_items += [
            (
                utils.translate(30038),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'playlist', 'add'],
                    queries = {'album_id': album_id},
                    r_path  = True,
                    r_query = True
                )
            ),
            (
                utils.translate(30036),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['play', 'station'],
                    queries = {'station_name': album_name.encode('utf-8'), 'album_id': album_id},
                    r_path  = True,
                    r_query = True
                )
            )
        ]

        if 'artistId' in album:
            menu_items.append((
                utils.translate(30034),
                'Container.Update(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['browse', 'artist', album['artistId'][0]],
                    r_path  = True,
                    r_query = True
                )
            ))

        if my_library:
            menu_items.append((
                utils.translate(30061),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'remove', 'album', album_id],
                    r_path  = True,
                    r_query = True
                )
            ))


        item.addContextMenuItems(items=menu_items)

        # My Library entries differ from normal AllAcces ones as users are able
        # to add only parts of the item to there library
        if my_library:
            items.append((
                utils.build_url(
                    url     = url,
                    paths   = ['browse', 'my-library', 'album', album_id],
                    r_path  = True,
                    r_query = True
                ),
                item,
                True
            ))

        else:
            items.append((
                utils.build_url(
                    url     = url,
                    paths   = ['browse', 'album', album_id],
                    r_path  = True,
                    r_query = True
                ),
                item,
                True
            ))

    return items


def list_albums(listitems):
    xbmcplugin.setContent(addon_handle, 'albums')

    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_ALBUM,
        xbmcplugin.SORT_METHOD_ARTIST,
        xbmcplugin.SORT_METHOD_GENRE,
    ]

    list_items(listitems, sort_methods)


def build_playlist_listitems(playlists):
    items = []
    for playlist in playlists:
        # Applies to e.g. search results
        if 'playlist' in playlist:
            playlist = playlist['playlist']

        if 'name' not in playlist:
            continue

        playlist_id     = None
        playlist_token  = None
        playlist_name   = playlist['name']
        playlist_art    = thumbs.IMG_PLAYLIST
        fanart          = None

        # Find a thumbnail to be displayed
        if 'images' in playlist and len(playlist['images']) > 0:
            playlist_art = playlist['images'][0]['url']

        elif 'albumArtRef' in playlist and len(playlist['albumArtRef']) > 0:
            playlist_art = playlist['albumArtRef'][0]['url']

        if playlist_art and playlist_art != thumbs.IMG_PLAYLIST:
            fanart = playlist_art + "=w1280-w1280"

        # Get the id if available (Would mean it's a user playlist)
        if 'id' in playlist and type(playlist['id']) == unicode:
            playlist_id   = playlist['id']

        # Get the shareToken if available
        if 'shareToken' in playlist:
            playlist_token = playlist['shareToken']

        elif 'id' in playlist and 'shareToken' in playlist['id']:
            playlist_token = playlist['id']['shareToken']

        item = xbmcgui.ListItem(playlist_name)

        item.setArt({
            'thumb'  : playlist_art,
            'poster' : playlist_art,
            #'fanart' : fanart
        })


        item.setInfo('music', {
            'mediatype' : 'album',
            'album'     : playlist['name'],
        })

        paths = []
        query = {}

        if playlist_id:
            paths = ['browse', 'my-library', 'playlist', playlist_id]

        elif playlist_token:
            paths = ['browse', 'shared-playlist', playlist_token]
            query['playlist_token'] = playlist_token

        else:
            continue

        menu_items = [(
            utils.translate(30033),
            'XBMC.RunPlugin(%s)' % utils.build_url(
                url     = url,
                paths   = ['play', 'playlist'],
                queries = query,
                r_path  = True,
                r_query = True
            ),
        )]

        if playlist_token:
            menu_items.append((
                utils.translate(30036),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['play', 'station'],
                    queries = {'playlist_token': playlist_token},
                    r_path  = True,
                    r_query = True
                )
            ))

        # Add "Delete playlist" to user playlist (Only
        # user playlists have a playlist id)
        if playlist_id:
            menu_items.append((
                utils.translate(30068),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'playlist', 'delete'],
                    queries = query,
                    r_path  = True,
                    r_query = True
                )
            ))

        item.addContextMenuItems(items=menu_items)

        items.append((
            utils.build_url(
                url     = url,
                paths   = paths,
                queries = query,
                r_path  = True,
                r_query = True
            ),
            item,
            True
        ))

    return items


def list_playlists(listitems):
    xbmcplugin.setContent(addon_handle, 'albums')

    list_items(listitems)


def build_station_listitems(stations):
    items = []
    for station in stations:
        # Applies to e.g. search results
        if 'station' in station:
            station = station['station']

        if 'name' not in station:
            continue

        description = ''
        if 'description' in station:
            description = station['description']

        station_name = station['name']
        station_art  = thumbs.IMG_STATION
        fanart       = None

        if 'imageUrls' in station and len(station['imageUrls']) > 0:
            station_art = station['imageUrls'][0]['url']

        if station_art and station_art != thumbs.IMG_STATION:
            fanart = station_art + "=w1280-w1280"

        item = xbmcgui.ListItem(station_name)

        item.setArt({
            'thumb'  : station_art,
            'poster' : station_art,
            #'fanart' : fanart
        })

        item.setInfo('music', {
            'mediatype' : 'album',
            'album': station_name,
            'comment': description,
        })

        query = {}
        if 'id' in station:
            query['station_id'] = station['id']

        else:
            seed = station
            if 'seed' in station:
                seed = station['seed']

            query['station_name'] = station_name.encode('utf-8')
            if 'trackId' in seed:
                query['track_id'] = seed['trackId']

            elif 'artistId' in seed:
                query['artist_id'] = seed['artistId']

            elif 'albumId' in seed:
                query['album_id'] = seed['albumId']

            elif 'genreId' in seed:
                query['genre_id'] = seed['genreId']

            elif 'curatedStationId' in seed:
                query['curated_station_id'] = seed['curatedStationId']

            else:
                continue

        item.addContextMenuItems(
            items=[(
                utils.translate(30033),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['play', 'station'],
                    queries = query,
                    r_path  = True,
                    r_query = True
                )
            )]
        )

        items.append((
            utils.build_url(
                url     = url,
                paths   = ['play', 'station'],
                queries = query,
                r_path  = True,
                r_query = True
            ),
            item,
            False
        ))

    return items


def list_stations(listitems):
    xbmcplugin.setContent(addon_handle, 'albums')

    list_items(listitems, None, False)


def build_situation_listitems(situations):
    items = []
    for situation in situations:
        situation_id    = situation['id']
        situation_title = situation['title']
        situation_art   = thumbs.IMG_ALBUM
        fanart          = None

        description = ''
        if 'description' in situation:
            description = situation['description']

        if 'imageUrl' in situation:
            situation_art = situation['imageUrl']

        if situation_art and situation_art != thumbs.IMG_ALBUM:
            fanart = situation_art + "=w1280-w1280"

        item = xbmcgui.ListItem(situation_title)

        item.setArt({
            'thumb'  : situation_art,
            'poster' : situation_art,
            #'fanart' : fanart
        })

        item.setInfo('music', {
            'mediatype' : 'album',
            'album'     : situation_title,
            'comment'   : description,
        })

        items.append((
            utils.build_url(
                url     = url,
                paths   = ['browse', 'listen-now', 'situation', situation_id],
                r_path  = True,
                r_query = True
            ),
            item,
            True
        ))

    return items


def list_situations(listitems):
    list_albums(listitems)


def build_song_listitems(tracks, station_id=None, my_library=False, my_library_playlist=False):
    tracks_cache = utils.get_cache_dir(['tracks'])

    items = []
    for elem in tracks:
        # Applies to e.g. search results
        if 'track' in elem:
            track = elem['track']
        else:
            track = elem

        # Try to get an id, otherwise we skip
        # Important, always try to get a trackId first, than
        # storeId and than id
        if 'trackId' in track:
            track_id = track['trackId']

        elif 'storeId' in track:
            track_id = track['storeId']

        elif 'id' in track:
            track_id = track['id']

        else:
            continue

        # In case of playlists, user uploaded songs come without
        # metadata (title, album, etc.)
        # All we can do at this point is to check the library cache
        # entry and use the informations from there (if it exists)
        #
        # We only do this if the title is missing as other metadata
        # isn't as important and we don't want to do this to often
        if 'title' not in track:
            _track = gmusic.get_my_library_song_details(track_id)
            if _track:
                track = _track

        track_title = track['title'] if 'title' in track else ''
        album_art   = thumbs.IMG_TRACK
        fanart      = None

        if 'albumArtRef' in track and len(track['albumArtRef']) > 0:
            album_art = track['albumArtRef'][0]['url']

        if 'artistArtRef' in track and len(track['artistArtRef']) > 0:
            fanart = track['artistArtRef'][0]['url'] + '=s1920'

        item = xbmcgui.ListItem(track_title)

        item.setArt({
            'thumb'  : album_art,
            'poster' : album_art,
            #'fanart' : fanart
        })

        item.setInfo('music', {
            'mediatype'    : 'song',
            'title'        :  track_title,
            'tracknumber'  :  track['trackNumber']  if 'trackNumber' in track else '',
            'year'         :  track['year']         if 'year'        in track else '',
            'genre'        :  track['genre']        if 'genre'       in track else '',
            'album'        :  track['album']        if 'album'       in track else '',
            'artist'       :  track['artist']       if 'artist'      in track else '',
            'rating'       :  track['rating']       if 'rating'      in track else '',
            'playcount'    :  track['playCount']    if 'playCount'   in track else '',
        })

        menu_items = []

        if not my_library and 'id' not in track:
            # Add "Add to library" to context menu
            menu_items.append((
                utils.translate(30037),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'add', 'track', track_id],
                    r_path  = True,
                    r_query = True
                )
            ))

        # Add "Add to playlist" to context menu
        menu_items.append((
            utils.translate(30038),
            'XBMC.RunPlugin(%s)' % utils.build_url(
                url     = url,
                paths   = ['my-library', 'playlist', 'add'],
                queries = {'track_id': track_id},
                r_path  = True,
                r_query = True
            )
        ))

        if my_library_playlist:
            # Add "Remove from playlist" to context menu
            if 'id' in elem:
                menu_items.append((
                    utils.translate(30062),
                    'XBMC.RunPlugin(%s)' % utils.build_url(
                        url     = url,
                        paths   = ['my-library', 'playlist', 'remove'],
                        queries = {'entry_id': elem['id']},
                        r_path  = True,
                        r_query = True
                    )
                ))

        # Add "Start radio" to context menu
        menu_items.append((
            utils.translate(30036),
            'XBMC.RunPlugin(%s)' % utils.build_url(
                url     = url,
                paths   = ['play', 'station'],
                queries = {'track_id': track_id, 'station_name': track_title.encode('utf-8')},
                r_path  = True,
                r_query = True
            )
        ))

        # Add "Go to Artist" to context menu
        if 'artistId' in track and len(track['artistId']) > 0:
            menu_items.append((
                utils.translate(30034),
                'Container.Update(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['browse', 'artist', track['artistId'][0]],
                    r_path  = True,
                    r_query = True
                )
            ))

        # Add "Go to Album" to context menu
        if 'albumId' in track:
            menu_items.append((
                utils.translate(30035),
                'Container.Update(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['browse', 'album', track['albumId']],
                    r_path  = True,
                    r_query = True
                )
            ))

        # Add "Rate song" to context menu
        menu_items.append((
            utils.translate(30041),
            'XBMC.RunPlugin(%s)' % utils.build_url(
                url     = url,
                paths   = ['rate'],
                queries = {'track_id': track_id},
                r_path  = True,
                r_query = True
            )
        ))

        if my_library and 'id' in track:
            # Add "Remove from library" to context menu
            menu_items.append((
                utils.translate(30061),
                'XBMC.RunPlugin(%s)' % utils.build_url(
                    url     = url,
                    paths   = ['my-library', 'remove', 'track', track['id']],
                    r_path  = True,
                    r_query = True
                )
            ))

        item.addContextMenuItems(items=menu_items)

        item.setProperty('IsPlayable', 'true')
        item.setProperty('Music',      'true')
        item.setProperty('mimetype',   'audio/mpeg')

        # We cache everything so :play_track: doesn't have to fetch those informations again
        with open(os.path.join(tracks_cache, track_id), 'w+') as f:
            f.write(json.dumps(track))

        queries = {}
        if station_id:
            queries['station_id'] = station_id

        items.append((
            utils.build_url(
                url     = url,
                paths   = ['play', 'track', track_id],
                queries = queries,
                r_path  = True,
                r_query = True
            ),
            item,
            False
        ))

    # Clean up the tracks directory
    for _file in os.listdir(tracks_cache):
        _file = os.path.join(tracks_cache, _file)
        m_time = os.stat(_file).st_mtime

        # If older than 24h we remove it
        if m_time < time.time() - 86400:
            os.remove(_file)

    return items


def list_songs(listitems):
    xbmcplugin.setContent(addon_handle, 'songs')

    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_TRACKNUM,
        xbmcplugin.SORT_METHOD_TITLE,
        xbmcplugin.SORT_METHOD_ALBUM,
        xbmcplugin.SORT_METHOD_ARTIST,
        xbmcplugin.SORT_METHOD_PLAYCOUNT,
        xbmcplugin.SORT_METHOD_DURATION,
        xbmcplugin.SORT_METHOD_SONG_RATING,
        xbmcplugin.SORT_METHOD_GENRE,
    ]

    list_items(listitems, sort_methods)


def list_items(listitems, sort_methods=None, cache_to_disc=True):
    if not sort_methods:
        sort_methods = []

    xbmcplugin.addDirectoryItems(
        handle     = addon_handle,
        items      = listitems,
        totalItems = len(listitems)
    )

    for sort_method in sort_methods:
        xbmcplugin.addSortMethod(addon_handle, sort_method)

    xbmcplugin.endOfDirectory(handle=addon_handle, cacheToDisc=cache_to_disc)
