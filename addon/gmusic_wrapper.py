import os
import uuid
import json
import time
import locale
import traceback
from operator import itemgetter

import xbmc

from gmusicapi import Mobileclient

from addon import mobileclient
from addon import utils
from addon import thumbs

from addon import addon


class GMusic(Mobileclient):
    _is_logged_in = False

    def _make_call(self, protocol, *args, **kwargs):
        try:
            return super(GMusic, self)._make_call(protocol, *args, **kwargs)

        except:
            utils.notify(utils.translate(30050), utils.translate(30051))
            utils.log(traceback.format_exc(), xbmc.LOGERROR)
            return None

    def _should_test_login(self):
        try:
            last_login_check = int(addon.getSetting('last_login_check'))

        except:
            last_login_check = 0

        if last_login_check == 0:
            return True

        # We check every 3 hours
        elif (last_login_check + 10800) < time.time():
            return True

        else:
            return False

    def login(self, validate=False):
        # Set Kodis locale to super class
        locale_code = xbmc.getLanguage(xbmc.ISO_639_1)
        locale_code = locale.normalize(locale_code).split('.')[0]
        if not locale_code:
            locale_code = 'en_US'

        self.locale = locale_code

        if self._is_logged_in and not validate:
            return True

        username  = addon.getSetting('username')
        password  = addon.getSetting('password')
        device_id = addon.getSetting('device_id')
        authtoken = addon.getSetting('authtoken')

        if authtoken:
            self.android_id               = device_id
            self.session._authtoken       = authtoken
            self.session.is_authenticated = True

            if not self._should_test_login():
                self._is_logged_in = True
                return True

            else:
                addon.setSetting('last_login_check', str(int(time.time())))
                try:
                    # Send a test request to ensure our authtoken
                    # is still valide and working
                    self.get_registered_devices()
                    self._is_logged_in = True
                    return True
                except:
                    # Faild with the test-request so we set
                    # "is_authenticated=False" and go through the login-process
                    # again to get a new "authtoken"
                    self.session.is_authenticated = False

        if device_id:
            success = super(GMusic, self).login(username, password,
                                                device_id, self.locale)

            if success:
                addon.setSetting('authtoken', self.session._authtoken)
                self._is_logged_in = True
                return True

        utils.notify(utils.translate(30048), '')
        addon.setSetting('is_setup', 'false')

        # Prevent further addon execution in case we failed with the login-process
        raise SystemExit

    ##
    ## Overloaded to add some stuff
    ##
    def get_listen_now_situations(self, from_cache=True):
        _cache = os.path.join(utils.get_cache_dir(), 'situations.json')

        resp = None
        if os.path.exists(_cache) and from_cache:
            with open(_cache, 'r') as f:
                try:
                    resp = json.loads(f.read())

                except:
                    pass

        if not resp:
            resp = self._make_call(mobileclient.ListListenNowSituations)

            with open(_cache, 'w+') as f:
                f.write(json.dumps(resp))

        if resp:
            return (resp['primaryHeader'], resp['situations'])

        else:
            return (None, None)

    def get_station_tracks(self, station_id, num_tracks=25,
                           recently_played_ids=None):
        _cache = utils.get_cache_dir(['station-ids'])
        station_ids_cache = os.path.join(_cache, '%s.json' % station_id)

        if not recently_played_ids:
            if os.path.exists(station_ids_cache):
                with open(station_ids_cache, 'r') as f:
                    try:
                        recently_played_ids = json.loads(f.read())

                    except ValueError:
                        pass

        tracks = super(GMusic, self).get_station_tracks(station_id, num_tracks,
                                                        recently_played_ids)

        track_ids = []
        with open(station_ids_cache, 'w+') as f:
            for track in tracks:
                if 'trackId' in track:
                    track_ids.append(track['trackId'])

                elif 'storeId' in track:
                    track_ids.append(track['storeId'])

            f.write(json.dumps(track_ids))

        return tracks

    def delete_album(self, album_id):
        songs = self.get_my_library_songs(from_cache=True)

        if not songs:
            return

        song_ids = []
        for song in songs:
            if song['albumId'] == album_id:
                song_ids.append(song['id'])

        if song_ids:
            self.delete_songs(song_ids)

    def search(self, query=None, cached=False, max_results=50):
        """Queries Google Music for content.

        Args:
            query (str): A query to search for
            cached (bool): If set, the query will be ignored and
                the result of the last search will be returned.

        Returns:
            Search results matching the query, from the cache or
            None if cache was requested but none existent
        """
        _cache = os.path.join(utils.get_cache_dir(), 'search_results.json')

        if query and not cached:
            return super(GMusic, self).search(query, max_results)

        if cached and os.path.exists(_cache):
            with open(_cache, 'r') as f:
                return json.loads(f.read())

        return None

    def get_album_info(self, album_id, include_tracks=True):
        # If a user uploaded a song where google can't match a album,
        # an albumId doesn NOT exist.
        # Therefore we generate our own id.
        # A call to googles backend will obviously return nothing
        # so we handle this case beforehand
        #
        # Note: Google albumIds always start with a capital B
        if album_id.startswith('B'):
            album_info = super(GMusic, self).get_album_info(album_id,
                                                            include_tracks)
            if include_tracks and 'tracks' in album_info:
                tracks = sorted(album_info['tracks'],
                                key=itemgetter('trackNumber'))
                album_info['tracks'] = tracks

            return album_info

        else:
            return []

    def get_artist_info(self, artist_id, include_albums=True, max_top_tracks=5,
                        max_rel_artist=5, from_cache=False):
        # If a user uploaded a song where google can't match a artist,
        # an artistId does NOT exist.
        # Therefore we generate our own id in `get_my_library_songs`.
        # A call to googles backend will obviously return nothing
        # so we handle this case beforehand
        #
        # Note: Google artistIds always start with a capital A
        if not artist_id.startswith('A'):
            return []

        artist        = None
        artists_cache = os.path.join(utils.get_cache_dir(['artists']), artist_id)

        if os.path.exists(artists_cache) and from_cache:
            with open(artists_cache, 'r') as f:
                try:
                    artist = json.loads(f.read())

                except:
                    pass

        if not artist:
            artist = super(GMusic, self).get_artist_info(artist_id,
                                                         include_albums,
                                                         max_top_tracks,
                                                         max_rel_artist)

        return artist

    ##
    ## Methods not yet in API
    ##
    def get_new_releases(self, num_items=25, genre=None):
        res = self._make_call(mobileclient.GetNewReleases, num_items, genre)
        utils.log(json.dumps(res, indent=2), xbmc.LOGERROR)
        for tabs in res['tabs']:
            if tabs['tab_type'] == 'NEW_RELEASES':
                return tabs['groups'][0]['entities']

    def get_top_chart(self):
        res = self._make_call(mobileclient.GetTopChart)
        return res['chart']

    def get_top_chart_genres(self):
        return self._make_call(mobileclient.GetTopChartGenres)

    def get_top_chart_for_genre(self, genre):
        return self._make_call(mobileclient.GetTopChartForGenre, genre)

    def get_station_categories(self, from_cache=True):
        _cache = os.path.join(utils.get_cache_dir(), 'station_categories.json')

        resp = None
        if os.path.exists(_cache) and from_cache:
            with open(_cache, 'r') as f:
                resp = json.loads(f.read())
        else:
            resp = self._make_call(mobileclient.GetStationCategories)

            with open(_cache, 'w+') as f:
                f.write(json.dumps(resp))

        return resp['root']['subcategories']

    def get_stations(self, station_subcategory_id):
        res = self._make_call(mobileclient.GetStations,
                              station_subcategory_id, self.locale)

        return res['stations']


    ##
    ## Helper/Wrapper functions
    ##
    def _uniquify(self, dict_list, key):
        new = []
        seen = set()
        for elem in dict_list:
            if key not in elem:
                continue

            if elem[key] not in seen and not seen.add(elem[key]):
                new.append(elem)

        return new

    def get_my_library_songs(self, from_cache=True):
        _cache = os.path.join(utils.get_cache_dir(['library']), 'songs.json')
        _song_cache_path = utils.get_cache_dir(['library', 'songs'])

        songs = None
        if os.path.exists(_cache) and from_cache:
            with open(_cache, 'r') as f:
                songs = json.loads(f.read())

        else:
            generator = self.get_all_songs(incremental=True, include_deleted=False)

            tmp = []
            for songs in generator:
                tmp += songs

            songs = tmp

            # Generate artistId and albumId in case they are
            # missing (applies to user uploaded songs without
            # a matching entry in googles database)
            for i, song in enumerate(songs):
                if 'artistId' not in song:
                    songs[i]['artistId'] = [str(uuid.uuid4())]

                if 'albumId' not in song:
                    songs[i]['albumId'] = str(uuid.uuid4())

                if 'album' not in song:
                    song[i]['album'] = ''


            with open(_cache, 'w+') as f:
                f.write(json.dumps(songs))


            # Save each song as separate file
            # for easier and quicker access
            for song in songs:
                # Main id file
                _target = os.path.join(_song_cache_path, song['id'])
                with open(os.path.join(_target), 'w+') as f:
                    f.write(json.dumps(song))

                # Other available ids which we create symlinks for
                for _id in ['trackId', 'storeId']:
                    if _id not in song:
                        continue

                    _link = os.path.join(_song_cache_path, song[_id])
                    if os.path.exists(_link) and os.path.islink(_link):
                        continue

                    try:
                        # On unix systems we simply create a symlink
                        os.symlink(_target, _link)

                    except:
                        # On other systems (*cough* windows *cough*) we just
                        # write another version of the file
                        with open(os.path.join(_link), 'w+') as f:
                            f.write(json.dumps(song))

        return songs

    def get_my_library_song_details(self, track_id):
        _cache = os.path.join(utils.get_cache_dir(['library', 'songs']), track_id)

        track = None
        if os.path.exists(_cache):
            with open(_cache, 'r') as f:
                track = json.loads(f.read())

        return track

    def get_my_library_artists(self, from_cache=True):
        _cache = os.path.join(utils.get_cache_dir(['library']), 'artists.json')

        artists = []
        if os.path.exists(_cache) and from_cache:
            with open(_cache, 'r') as f:
                artists = json.loads(f.read())
        else:
            songs = self.get_my_library_songs()
            songs = self._uniquify(songs, 'albumArtist')

            for song in songs:
                if 'artistId' not in song:
                    continue

                _art = thumbs.IMG_ARTIST
                if 'artistArtRef' in song and len(song['artistArtRef']) > 0:
                    _art = song['artistArtRef'][0]['url']

                artist ={
                    'artistId':     song['artistId'][0],
                    'name':         song['albumArtist'],
                    'artistArtRef': _art
                }

                artists.append(artist)

            artists = sorted(artists, key=itemgetter('name'))
            with open(_cache, 'w+') as f:
                f.write(json.dumps(artists))

        return artists

    def get_my_library_albums(self, from_cache=True):
        _cache = os.path.join(utils.get_cache_dir(['library']), 'albums.json')

        albums = []
        if os.path.exists(_cache) and from_cache:
            with open(_cache, 'r') as f:
                albums = json.loads(f.read())
        else:
            songs = self.get_my_library_songs()

            songs = self._uniquify(songs, 'albumId')

            for song in songs:
                if 'albumId' not in song:
                    continue

                if 'artistId' not in song:
                    continue

                _art = thumbs.IMG_ALBUM
                if 'albumArtRef' in song and len(song['albumArtRef']) > 0:
                    _art = song['albumArtRef'][0]['url']

                album = {
                    'albumId'    : song['albumId'],
                    'artistId'   : song['artistId'],
                    'name'       : song['album']       if 'album'       in song else '',
                    'artist'     : song['artist']      if 'artist'      in song else '',
                    'albumArtist': song['albumArtist'] if 'albumArtist' in song else '',
                    'year'       : song['year']        if 'year'        in song else '',
                    'genre'      : song['genre']       if 'genre'       in song else '',
                    'albumArtRef': _art
                }

                albums.append(album)

            albums = sorted(albums, key=itemgetter('name'))
            with open(_cache, 'w+') as f:
                f.write(json.dumps(albums))

        return albums

    def get_my_library_genres(self):
        songs = self.get_my_library_songs()
        songs = self._uniquify(songs, 'genre')

        genres = []
        for song in songs:
            if 'genre' not in song:
                continue

            if song['genre'] == '':
                continue

            genres.append(song['genre'])

        return sorted(genres)

    def get_user_artist_albums(self, artist_id):
        artist_albums = []
        for album in self.get_my_library_albums():
            if artist_id in album['artistId']:
                artist_albums.append(album)

        return artist_albums

    def get_user_album_songs(self, album_id):
        album_songs = []
        for song in self.get_my_library_songs():

            if 'albumId' in song and album_id == song['albumId']:
                album_songs.append(song)

        return sorted(album_songs, key=itemgetter('trackNumber'))

    def get_user_genre_albums(self, genre):
        genre_albums = []
        for album in self.get_my_library_albums():
            if 'genre' in album and genre == album['genre']:
                genre_albums.append(album)

        return sorted(genre_albums, key=itemgetter('name'))

    def get_user_playlists(self):
        playlists = self.get_all_playlists()
        playlists = sorted(playlists, key=itemgetter('name'))

        return playlists

    def get_user_playlist(self, playlist_id):
        playlist_content = self.get_all_user_playlist_contents()

        for playlist in playlist_content:
            if (playlist['id'] != playlist_id
                    and playlist['shareToken'] != playlist_id):
                continue

            return playlist

    def get_user_lastadded(self, limit=200):
        songs = self.get_my_library_songs()
        # ToDo:
        # Google also sorts by tracknumber specific to the album
        # Can we do that as well somehow?
        songs = sorted(songs, key=itemgetter('recentTimestamp'), reverse=True)

        return songs[:limit]
