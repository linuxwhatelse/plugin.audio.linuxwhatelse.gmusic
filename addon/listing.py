import os
import json

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from addon import utils
from addon import thumbs

from addon import addon
from addon import url
from addon import addon_handle


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
        artist_art  = artist['artistArtRef'] if 'artistArtRef' in artist else thumbs.IMG_ARTIST_FLAT

        item = xbmcgui.ListItem(
            label           = artist_name,
            iconImage       = artist_art,
            thumbnailImage  = artist_art,
        )

        item.setInfo('music', {
            'artist': artist_name
        })

        item.addContextMenuItems(
            items=[
                (utils.translate(30036), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['play', 'station'], \
                    queries={'station_name': artist_name.encode('utf-8'), 'artist_id': artist_id}, r_path=True, r_query=True)),
            ],
            replaceItems=True
        )

        # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
        if my_library:
            items.append(
                (utils.build_url(url=url, paths=['browse', 'my-library', 'artist'], queries={'artist_id': artist_id}, \
                    r_path=True, r_query=True), item, True)
            )
        else:
            items.append(
                (utils.build_url(url=url, paths=['browse', 'artist'], queries={'artist_id': artist_id}, \
                    r_path=True, r_query=True), item, True)
            )

    return items
def list_artists(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'artists')

    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_ARTIST,
    ]

    list_items(listitems, allow_view_overwrite, int(addon.getSetting('view_id_artists')), sort_methods)

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
        album_art  = album['albumArtRef'] if 'albumArtRef' in album else thumbs.IMG_ALBUM

        item = xbmcgui.ListItem(
            label           = album_name,
            iconImage       = album_art,
            thumbnailImage  = album_art,
        )

        item.setInfo('music', {
            'album'   : album_name,
            'artist'  : album['albumArtist']  if 'albumArtist' in album else '',
            'genre'   : album['genre']        if 'genre'       in album else '',
            'year'    : album['year']         if 'year'        in album else '',
        })

        menu_items=[
            (utils.translate(30033), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['play', 'album'], \
                queries={'album_id': album_id}, r_path=True, r_query=True)),

            (utils.translate(30039), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['queue', 'album'], \
                queries={'album_id': album_id}, r_path=True, r_query=True)),

            (utils.translate(30040), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['queue', 'album'], \
                queries={'album_id': album_id, 'play_next': True}, r_path=True, r_query=True)),
        ]

        if my_library:
            menu_items.append(
                (utils.translate(30061), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'remove'], \
                    queries={'album_id': album_id}, r_path=True, r_query=True)),
            )

        else:
            menu_items.append(
                (utils.translate(30037), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'add'], \
                    queries={'album_id': album_id}, r_path=True, r_query=True)),
            )

        menu_items += [
            (utils.translate(30038), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'playlist', 'add'], \
                queries={'album_id': album_id}, r_path=True, r_query=True)),

            (utils.translate(30036), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['play', 'station'], \
                queries={'station_name': album_name.encode('utf-8'), 'album_id': album_id}, r_path=True, r_query=True)),
        ]

        if 'artistId' in album:
            menu_items.append(
                (utils.translate(30034), 'Container.Update(%s)' % utils.build_url(url=url, paths=['browse', 'artist'], \
                queries={'artist_id': album['artistId'][0]}, r_path=True, r_query=True))
            )

        item.addContextMenuItems(items=menu_items, replaceItems=True)

        # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
        if my_library:
            items.append(
                (utils.build_url(url=url, paths=['browse', 'my-library', 'album'], \
                    queries={'album_id': album_id}, r_path=True, r_query=True), item, True)
            )
        else:
            items.append(
                (utils.build_url(url=url, paths=['browse', 'album'], \
                    queries={'album_id': album_id}, r_path=True, r_query=True), item, True)
            )

    return items
def list_albums(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')

    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_ALBUM,
        xbmcplugin.SORT_METHOD_ARTIST,
        xbmcplugin.SORT_METHOD_GENRE,
    ]

    list_items(listitems, allow_view_overwrite, int(addon.getSetting('view_id_albums')), sort_methods)

def build_playlist_listitems(playlists):
    items=[]
    for playlist in playlists:
        # Applies to e.g. search results
        if 'playlist' in playlist:
            playlist = playlist['playlist']

        if 'name' not in playlist:
            continue

        playlist_token  = None
        playlist_id     = None
        playlist_name   = playlist['name']
        playlist_art    = None

        # Find a thumbnail to be displayed
        if 'images' in playlist and len(playlist['images']) > 0:
            playlist_art = playlist['images'][0]['url']

        elif 'albumArtRef' in playlist and len(playlist['albumArtRef']) > 0:
            playlist_art = playlist['albumArtRef'][0]['url']

        else:
            playlist_art = thumbs.IMG_PLAYLIST

        # Get the shareToken if available
        if 'shareToken' in playlist:
            playlist_token = playlist['shareToken']

        elif 'id' in playlist and 'shareToken' in playlist['id']:
            playlist_token = playlist['id']['shareToken']

        # Get the id if available (Would mean it's a user playlist)
        if 'id' in playlist and type(playlist['id']) == str:
            playlist_id   = playlist['id']

        item = xbmcgui.ListItem(
            label           = playlist_name,
            iconImage       = playlist_art,
            thumbnailImage  = playlist_art,
        )

        item.setInfo('music', {
            'album': playlist['name'],
        })

        paths = []
        query = {}

        if playlist_id:
            paths = ['browse', 'my-library', 'playlist']
            query['playlist_id'] = playlist_id

        elif playlist_token:
            paths = ['browse', 'shared-playlist']
            query['playlist_token'] = playlist_token

        menu_items = [
            (utils.translate(30033), 'XBMC.RunPlugin(%s)' % \
                utils.build_url(
                    url     = url,
                    paths   = ['play', 'playlist'],
                    queries = query,
                    r_path  = True,
                    r_query = True
                )
            )
        ]

        if playlist_token:
            menu_items.append(
                (utils.translate(30036), 'XBMC.RunPlugin(%s)' % \
                    utils.build_url(
                        url     = url,
                        paths   = ['play', 'station'],
                        queries = {'playlist_token': playlist_token},
                        r_path  = True,
                        r_query = True
                    )
                )
            )

        # Only user playlists have a playlist_id
        if playlist_id:
            menu_items.append(
                (utils.translate(30068), 'XBMC.RunPlugin(%s)' % \
                    utils.build_url(
                        url     = url,
                        paths   = ['my-library', 'playlist', 'delete'],
                        queries = query,
                        r_path  = True,
                        r_query = True
                    )
                )
            )

        item.addContextMenuItems(items=menu_items, replaceItems=True)

        items.append(
            (
                utils.build_url(
                    url     = url,
                    paths   = paths,
                    queries = query,
                    r_path  = True,
                    r_query = True
                ),
                item,
                True
            )
        )

    return items
def list_playlists(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')

    list_items(listitems, allow_view_overwrite, int(addon.getSetting('view_id_playlists')))

def build_station_listitems(stations):
    items=[]
    for station in stations:
        # Applies to e.g. search results
        if 'station' in station:
            station = station['station']

        if 'name' not in station:
            continue

        station_name = station['name']
        station_art  = station['imageUrls'][0]['url'] if 'imageUrls' in station and len(station['imageUrls']) > 0 else thumbs.IMG_STATION

        item = xbmcgui.ListItem(
            label           = station_name,
            iconImage       = station_art,
            thumbnailImage  = station_art,
        )

        item.setInfo('music', {
            'album': station_name,
            # This might look a little bit wrong, but as long as no one complains about it,
            # we'll leave that in so we have that nice description at least somewhere
            'artist': station['description'] if 'description' in station else '',
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
            items=[
                (utils.translate(30033), 'XBMC.RunPlugin(%s)' % \
                    utils.build_url(
                        url     = url,
                        paths   = ['play', 'station'],
                        queries = query,
                        r_path  = True,
                        r_query = True
                    )
                )
            ],
            replaceItems=True
        )

        items.append(
            (utils.build_url(
                url     = url,
                paths   = ['play', 'station'],
                queries = query,
                r_path  = True,
                r_query = True
            ), item, True)
        )

    return items
def list_stations(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')
    list_items(listitems, allow_view_overwrite, int(addon.getSetting('view_id_stations')), None, False)

def build_situation_listitems(situations):
    items = []
    for situation in situations:
        situation_id    = situation['id']
        situation_title = situation['title']
        situation_art   = situation['imageUrl'] if 'imageUrl' in situation else thumbs.IMG_ALBUM

        item = xbmcgui.ListItem(
            label           = situation_title,
            iconImage       = situation_art,
            thumbnailImage  = situation_art,
        )

        item.setInfo('music', {
            'album'   : situation_title,
            # This might look a little bit wrong, but as long as no one complains about it,
            # we'll leave that in so we have that nice description at least somewhere
            'artist'  : situation['description']  if 'description' in situation else '',
        })

        item.addContextMenuItems(items=[], replaceItems=True)

        items.append(
            (utils.build_url(url=url, paths=['browse', 'listen-now', 'situation'], \
                queries={'situation_id': situation_id}, r_path=True, r_query=True), item, True)
            )

    return items
def list_situations(listitems, allow_view_overwrite=True):
    list_albums(listitems, allow_view_overwrite)

def build_song_listitems(tracks, station_id=None, my_library=False, my_library_playlist=False):
    items = []
    for elem in tracks:
        # Applies to e.g. search results
        if 'track' in elem:
            track = elem['track']
        else:
            track = elem

        if ('trackId' not in track and 'storeId' not in track) or 'title' not in track:
            continue

        track_id    = track['trackId'] if 'trackId' in track else track['storeId']
        track_title = track['title']
        album_art   = track['albumArtRef'][0]['url'] if 'albumArtRef' in track and len(track['albumArtRef']) > 0 else thumbs.IMG_TRACK

        item = xbmcgui.ListItem(
            label           = track_title,
            iconImage       = album_art,
            thumbnailImage  = album_art,
        )
        item.setInfo('music', {
            'title'        :  track_title,
            'tracknumber'  :  track['trackNumber']  if 'trackNumber' in track else '',
            'year'         :  track['year']         if 'year'        in track else '',
            'genre'        :  track['genre']        if 'genre'       in track else '',
            'album'        :  track['album']        if 'album'       in track else '',
            'artist'       :  track['artist']       if 'artist'      in track else '',
            'rating'       :  track['rating']       if 'rating'      in track else '',
            'playcount'    :  track['playCount']    if 'playCount'   in track else '',
        })

        menu_items = [
            (utils.translate(30039), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['queue', 'track'], \
                queries={'track_id': track_id}, r_path=True, r_query=True)),

            (utils.translate(30040), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['queue', 'track'], \
                queries={'track_id': track_id, 'play_next': True}, r_path=True, r_query=True)),
        ]


        if my_library:
            if 'id' in track:
                menu_items.append(
                    (utils.translate(30061), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'remove'], \
                        queries={'library_song_id': track['id']}, r_path=True, r_query=True)),
                )

        else:
            menu_items.append(
                (utils.translate(30037), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'add'], \
                    queries={'track_id': track_id}, r_path=True, r_query=True)),
            )

        menu_items.append(
            (utils.translate(30038), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'playlist', 'add'], \
                queries={'track_id': track_id}, r_path=True, r_query=True)),
        )

        if my_library_playlist:
            if 'id' in elem:
                menu_items.append(
                    (utils.translate(30062), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['my-library', 'playlist', 'remove'], \
                        queries={'entry_id': elem['id']}, r_path=True, r_query=True)),
                )


        menu_items.append(
            (utils.translate(30036), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['play', 'station'], \
                queries={'track_id': track_id, 'station_name': track_title.encode('utf-8')}, r_path=True, r_query=True)),
        )

        if 'artistId' in track and len(track['artistId']) > 0:
            menu_items.append(
                (utils.translate(30034), 'Container.Update(%s)' % utils.build_url(url=url, paths=['browse', 'artist'], \
                    queries={'artist_id': track['artistId'][0]}, r_path=True, r_query=True))
            )

        if 'albumId' in track:
            menu_items.append(
                (utils.translate(30035), 'Container.Update(%s)' % utils.build_url(url=url, paths=['browse', 'album'], \
                    queries={'album_id': track['albumId']}, r_path=True, r_query=True))
            )

        menu_items.append(
            (utils.translate(30041), 'XBMC.RunPlugin(%s)' % utils.build_url(url=url, paths=['rate'], \
                queries={'track_id': track_id}, r_path=True, r_query=True)),
        )

        item.addContextMenuItems(items=menu_items, replaceItems=True)

        item.setProperty('IsPlayable','true')
        item.setProperty('Music', 'true')
        item.setProperty('mimetype', 'audio/mpeg')


        queries = {'track_id':track_id}
        if station_id:
            queries['station_id'] = station_id


        # We cache everything so :play_track: doesn't have to fetch those informations again
        tracks_cache = utils.get_cache_dir(['tracks'])
        with open(os.path.join(tracks_cache, track_id), 'w+') as f:
            f.write(json.dumps(track))

        items.append(
            (utils.build_url(url=url, paths=['play', 'track'], queries=queries, r_path=True, r_query=True), item, False)
        )

    return items
def list_songs(listitems, allow_view_overwrite=True):
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

    list_items(listitems, allow_view_overwrite, int(addon.getSetting('view_id_songs')), sort_methods)


def list_items(listitems, allow_view_overwrite=True, view_mode_id=None, sort_methods=None, cacheToDisc=True):
    cacheToDisc=False
    if not view_mode_id:
        view_mode_id = int(addon.getSetting('view_id_list'))

    if not sort_methods:
        sort_methods = []

    xbmcplugin.addDirectoryItems(
        handle=addon_handle,
        items=listitems,
        totalItems=len(listitems)
    )

    for sort_method in sort_methods:
        xbmcplugin.addSortMethod(addon_handle, sort_method)

    if allow_view_overwrite and addon.getSetting('overwrite_views') == 'true':
        xbmc.executebuiltin('Container.SetViewMode(%d)' % view_mode_id)

    xbmcplugin.endOfDirectory(handle=addon_handle, cacheToDisc=cacheToDisc)
