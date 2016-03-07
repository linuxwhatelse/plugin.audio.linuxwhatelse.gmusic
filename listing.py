import os
import json

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import mapper

import utils
import thumbs


class Listing:
    url          = None
    addon_handle = None

    _addon       = None

    def __init__(self, url, addon_handle):
        self.url          = url
        self.addon_handle = addon_handle

        self._addon       = xbmcaddon.Addon()


    def build_artist_listitems(self, artists, my_library=False):
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
                    (utils.translate(30036, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['play', 'station'], \
                        queries={'station_name': artist_name.encode('utf-8'), 'artist_id': artist_id}, overwrite_path=True, overwrite_query=True)),
                ],
                replaceItems=True
            )

            # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
            if my_library:
                items.append(
                    (mapper.build_url(url=self.url, paths=['browse', 'my-library', 'artist'], queries={'artist_id': artist_id}, \
                        overwrite_path=True, overwrite_query=True), item, True)
                )
            else:
                items.append(
                    (mapper.build_url(url=self.url, paths=['browse', 'artist'], queries={'artist_id': artist_id}, \
                        overwrite_path=True, overwrite_query=True), item, True)
                )

        return items
    def list_artists(self, listitems, allow_view_overwrite=True):
        xbmcplugin.setContent(self.addon_handle, 'artists')

        sort_methods = [
            xbmcplugin.SORT_METHOD_UNSORTED,
            xbmcplugin.SORT_METHOD_ARTIST,
        ]

        self.list_items(listitems, allow_view_overwrite, int(self._addon.getSetting('view_id_artists')), sort_methods)

    def build_album_listitems(self, albums, my_library=False):
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
                (utils.translate(30033, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['play', 'album'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

                (utils.translate(30039, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['queue', 'album'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

                (utils.translate(30040, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['queue', 'album'], \
                    queries={'album_id': album_id, 'play_next': True}, overwrite_path=True, overwrite_query=True)),
            ]

            if my_library:
                menu_items.append(
                    (utils.translate(30061, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'remove'], \
                        queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
                )

            else:
                menu_items.append(
                    (utils.translate(30037, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'add'], \
                        queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
                )

            menu_items += [
                (utils.translate(30038, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'playlist', 'add'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

                (utils.translate(30036, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['play', 'station'], \
                    queries={'station_name': album_name.encode('utf-8'), 'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
            ]

            if 'artistId' in album:
                menu_items.append(
                    (utils.translate(30034, self._addon), 'Container.Update(%s)' % mapper.build_url(url=self.url, paths=['browse', 'artist'], \
                    queries={'artist_id': album['artistId'][0]}, overwrite_path=True, overwrite_query=True))
                )

            item.addContextMenuItems(items=menu_items, replaceItems=True)

            # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
            if my_library:
                items.append(
                    (mapper.build_url(url=self.url, paths=['browse', 'my-library', 'album'], \
                        queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True), item, True)
                )
            else:
                items.append(
                    (mapper.build_url(url=self.url, paths=['browse', 'album'], \
                        queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True), item, True)
                )

        return items
    def list_albums(self, listitems, allow_view_overwrite=True):
        xbmcplugin.setContent(self.addon_handle, 'albums')

        sort_methods = [
            xbmcplugin.SORT_METHOD_UNSORTED,
            xbmcplugin.SORT_METHOD_ALBUM,
            xbmcplugin.SORT_METHOD_ARTIST,
            xbmcplugin.SORT_METHOD_GENRE,
        ]

        self.list_items(listitems, allow_view_overwrite, int(self._addon.getSetting('view_id_albums')), sort_methods)

    def build_playlist_listitems(self, playlists):
        items=[]
        for playlist in playlists:
            # Applies to e.g. search results
            if 'playlist' in playlist:
                playlist = playlist['playlist']

            if 'id' not in playlist or 'name' not in playlist:
                continue

            playlist_token  = None
            playlist_id   = None
            playlist_name = playlist['name']
            playlist_art  = playlist['images'][0]['url'] if 'images' in playlist and len(playlist['images']) > 0 else thumbs.IMG_PLAYLIST

            if 'shareToken' in playlist:
                playlist_token = playlist['shareToken']
            elif 'shareToken' in playlist['id']:
                playlist_token = playlist['id']['shareToken']
            elif 'sharedToken' in playlist:
                playlist_token = playlist['sharedToken']
            elif 'sharedToken' in playlist['id']:
                playlist_token = playlist['id']['sharedToken']
            else:
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
                (utils.translate(30033, self._addon), 'XBMC.RunPlugin(%s)' % \
                    mapper.build_url(url=self.url, paths=['play', 'playlist'], queries=query, overwrite_path=True, overwrite_query=True))
            ]

            if playlist_token:
                menu_items.append(
                    (utils.translate(30036, self._addon), 'XBMC.RunPlugin(%s)' % \
                        mapper.build_url(url=self.url, paths=['play', 'station'], queries={'playlist_token': playlist_token}, overwrite_path=True, overwrite_query=True))
                )

            if playlist_id:  # Only user playlists have a playlist_id
                menu_items.append(
                    (utils.translate(30068, self._addon), 'XBMC.RunPlugin(%s)' % \
                        mapper.build_url(url=self.url, paths=['my-library', 'playlist', 'delete'], queries=query, overwrite_path=True, overwrite_query=True))
                )

            item.addContextMenuItems(items=menu_items, replaceItems= True)

            items.append(
                (mapper.build_url(url=self.url, paths=paths, queries=query, overwrite_path=True, overwrite_query=True), item, True)
            )

        return items
    def list_playlists(self, listitems, allow_view_overwrite=True):
        xbmcplugin.setContent(self.addon_handle, 'albums')

        self.list_items(listitems, allow_view_overwrite, int(self._addon.getSetting('view_id_playlists')))

    def build_station_listitems(self, stations):
        items=[]
        for station in stations:
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
                query['station_name'] = station_name.encode('utf-8')
                if 'trackId' in station:
                    query['track_id'] = station['trackId']

                elif 'artistId' in station:
                    query['artist_id'] = station['artistId']

                elif 'albumId' in station:
                    query['album_id'] = station['albumId']

                elif 'genreId' in station:
                    query['genre_id'] = station['genreId']

                elif 'curatedStationId' in station:
                    query['curated_station_id'] = station['curatedStationId']

                else:
                    continue

            item.addContextMenuItems(
                items=[
                    (utils.translate(30033, self._addon), 'XBMC.RunPlugin(%s)' % \
                        mapper.build_url(url=self.url, paths=['play', 'station'], queries=query, overwrite_path=True, overwrite_query=True))
                ],
                replaceItems=True
            )


            items.append(
                (mapper.build_url(url=self.url, paths=['play', 'station'], queries=query, overwrite_path=True, overwrite_query=True), item, True)
            )

        return items
    def list_stations(self, listitems, allow_view_overwrite=True):
        xbmcplugin.setContent(self.addon_handle, 'albums')
        self.list_items(listitems, allow_view_overwrite, int(self._addon.getSetting('view_id_stations')), None, False)

    def build_situation_listitems(self, situations):
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
                (mapper.build_url(url=self.url, paths=['browse', 'listen-now', 'situation'], \
                    queries={'situation_id': situation_id}, overwrite_path=True, overwrite_query=True), item, True)
                )

        return items
    def list_situations(self, listitems, allow_view_overwrite=True):
        list_albums(listitems, allow_view_overwrite)

    def build_song_listitems(self, tracks, station_id=None, my_library=False, my_library_playlist=False):
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
                (utils.translate(30039, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['queue', 'track'], \
                    queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),

                (utils.translate(30040, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['queue', 'track'], \
                    queries={'track_id': track_id, 'play_next': True}, overwrite_path=True, overwrite_query=True)),
            ]


            if my_library:
                if 'id' in track:
                    menu_items.append(
                        (utils.translate(30061, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'remove'], \
                            queries={'library_song_id': track['id']}, overwrite_path=True, overwrite_query=True)),
                    )

            else:
                menu_items.append(
                    (utils.translate(30037, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'add'], \
                        queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
                )

            menu_items.append(
                (utils.translate(30038, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'playlist', 'add'], \
                    queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
            )

            if my_library_playlist:
                if 'id' in elem:
                    menu_items.append(
                        (utils.translate(30062, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['my-library', 'playlist', 'remove'], \
                            queries={'entry_id': elem['id']}, overwrite_path=True, overwrite_query=True)),
                    )


            menu_items.append(
                (utils.translate(30036, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['play', 'station'], \
                    queries={'track_id': track_id, 'station_name': track_title.encode('utf-8')}, overwrite_path=True, overwrite_query=True)),
            )

            if 'artistId' in track and len(track['artistId']) > 0:
                menu_items.append(
                    (utils.translate(30034, self._addon), 'Container.Update(%s)' % mapper.build_url(url=self.url, paths=['browse', 'artist'], \
                        queries={'artist_id': track['artistId'][0]}, overwrite_path=True, overwrite_query=True))
                )

            if 'albumId' in track:
                menu_items.append(
                    (utils.translate(30035, self._addon), 'Container.Update(%s)' % mapper.build_url(url=self.url, paths=['browse', 'album'], \
                        queries={'album_id': track['albumId']}, overwrite_path=True, overwrite_query=True))
                )

            menu_items.append(
                (utils.translate(30041, self._addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=self.url, paths=['rate'], \
                    queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
            )

            item.addContextMenuItems(items=menu_items, replaceItems=True)

            item.setProperty('IsPlayable','true')
            item.setProperty('Music', 'true')
            item.setProperty('mimetype', 'audio/mpeg')


            queries = {'track_id':track_id}
            if station_id:
                queries['station_id'] = station_id


            # We cache everything so :play_track: doesn't have to featch those informations again
            tracks_cache = utils.get_cache_dir(sub_dir=['tracks'])
            with open(os.path.join(tracks_cache, track_id), 'w+') as f:
                f.write(json.dumps(track, indent=2))

            items.append(
                (mapper.build_url(url=self.url, paths=['play', 'track'], queries=queries, overwrite_path=True, overwrite_query=True), item, False)
            )

        return items
    def list_songs(self, listitems, allow_view_overwrite=True):
        xbmcplugin.setContent(self.addon_handle, 'songs')

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

        self.list_items(listitems, allow_view_overwrite, int(self._addon.getSetting('view_id_songs')), sort_methods)


    def list_items(self, listitems, allow_view_overwrite=True, view_mode_id=None, sort_methods=None, cacheToDisc=True):
        cacheToDisc=False
        if not view_mode_id:
            view_mode_id = int(self._addon.getSetting('view_id_list'))

        if not sort_methods:
            sort_methods = []

        xbmcplugin.addDirectoryItems(
            handle=self.addon_handle,
            items=listitems,
            totalItems=len(listitems)
        )

        for sort_method in sort_methods:
            xbmcplugin.addSortMethod(self.addon_handle, sort_method)

        if allow_view_overwrite and self._addon.getSetting('overwrite_views') == 'true':
            xbmc.executebuiltin('Container.SetViewMode(%d)' % view_mode_id)

        xbmcplugin.endOfDirectory(handle=self.addon_handle, cacheToDisc=cacheToDisc)
