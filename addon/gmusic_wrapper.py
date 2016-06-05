import os
import json
import time
import locale

import xbmc
import xbmcaddon

from gmusicapi import Mobileclient, Webclient

from addon import mobileclient
from addon import utils

from addon import addon

_cache_dir = utils.get_cache_dir()

class GMusic(Mobileclient):
    _is_logged_in = False

    def _make_call(self, protocol, *args, **kwargs):
        try:
            return super(GMusic, self)._make_call(protocol, *args, **kwargs)
        except:
            utils.notify(utils.translate(30050), utils.translate(30051))
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
        # Set Kodis locale super class
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
                    # Send a test request to ensure our authtoken is still valide and working
                    self.get_registered_devices()
                    self._is_logged_in = True
                    return True
                except:
                    # Faild with the test-request so we set "is_authenticated=False"
                    # and go through the login-process again to get a new "authtoken"
                    self.session.is_authenticated = False

        if device_id:
            if super(GMusic, self).login(username, password, device_id, self.locale):
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
    def get_listen_now_situations(self):
        resp = self._make_call(mobileclient.ListListenNowSituations)
        return (resp['primaryHeader'], resp['situations'])

    def create_station(self, name, track_id=None, artist_id=None,
        album_id=None, genre_id=None, curated_station_id=None, playlist_token=None):
        """Creates an All Access radio station and returns its id.

        :param name: the name of the station to create
        :param \*_id: the id of an item to seed the station from.
          Exactly one of these params must be provided, or ValueError
          will be raised.
        """
        # TODO could expose include_tracks

        seed = {}
        if track_id is not None:
            if track_id[0] == 'T':
                seed['trackId'] = track_id
                seed['seedType'] = 2
            else:
                seed['trackLockerId'] = track_id
                seed['seedType'] = 1

        if artist_id is not None:
            seed['artistId'] = artist_id
            seed['seedType'] = 3
        if album_id is not None:
            seed['albumId'] = album_id
            seed['seedType'] = 4
        if genre_id is not None:
            seed['genreId'] = genre_id
            seed['seedType'] = 5
        if playlist_token is not None:
            seed['playlistShareToken'] = playlist_token
            seed['seedType'] = 8
        if curated_station_id is not None:
            seed['curatedStationId'] = curated_station_id
            seed['seedType'] = 9

        if len(seed) > 2:
            raise ValueError('exactly one {track,artist,album,genre}_id must be provided')

        mutate_call = mobileclient.BatchMutateStations
        add_mutation = mutate_call.build_add(name, seed, include_tracks=False, num_tracks=0)
        res = self._make_call(mutate_call, [add_mutation])

        return res['mutate_response'][0]['id']

    def get_station_tracks(self, station_id, num_tracks=25, recently_played_ids=None):
        stations_cache = utils.get_cache_dir(['station-ids'])
        station_ids_cache = os.path.join(stations_cache, '%s.json' % station_id)

        if not recently_played_ids:
            if os.path.exists(station_ids_cache):
                with open(station_ids_cache, 'r') as f:
                    try:
                        recently_played_ids = json.loads(f.read())
                    except ValueError:
                        pass


        tracks = super(GMusic, self).get_station_tracks(station_id=station_id, num_tracks=num_tracks, recently_played_ids=recently_played_ids)

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
        songs_cache  = os.path.join(_cache_dir, 'songs.json')
        songs        = self.get_my_library_songs(from_cache=True)

        if songs:
            song_ids = []
            for song in songs:
                if song['albumId'] == album_id:
                    song_ids.append(song['id'])

            self.delete_songs(song_ids)


    ##
    ## Methodes not yet in API
    ##
    def get_new_releases(self, num_items=25, genre=None):
        res = self._make_call(mobileclient.GetNewReleases, num_items, genre)
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

    def get_station_categories(self):
        res = self._make_call(mobileclient.GetStationCategories)
        return res['root']['subcategories']

    def get_stations(self, station_subcategory_id, location_code):
        res = self._make_call(mobileclient.GetStations, station_subcategory_id, location_code)
        return res['stations']



    ##
    ## Helper/Wrapper functions
    ##
    def get_my_library_songs(self, from_cache=True):
        songs_cache = os.path.join(_cache_dir, 'songs.json')

        songs = None
        if os.path.exists(songs_cache) and from_cache:
            with open(songs_cache, 'r') as f:
                songs = json.loads(f.read())
        else:
            generator = self.get_all_songs(incremental=True, include_deleted=False)
            tmp = []
            for songs in generator:
                for song in songs:
                    # If we miss required id's we ignore those entries!

                    if 'artistId' not in song:
                        continue

                    if 'albumId' not in song:
                        continue

                    if 'storeId' not in song:
                        if 'nid' not in song:
                            continue
                        else:
                            song['storeId'] = song['nid']

                    tmp.append(song)
            songs = tmp

            with open(songs_cache, 'w+') as f:
                f.write(json.dumps(songs))

        return songs

    def get_my_library_artists(self, from_cache=True):
        artists_cache = os.path.join(_cache_dir, 'artists.json')

        artists = []
        if os.path.exists(artists_cache) and from_cache:
            with open(artists_cache, 'r') as f:
                artists = json.loads(f.read())
        else:
            songs = self.get_my_library_songs()

            # Uniquify all songs by artistId
            seen = set()
            seen_add = seen.add
            songs = [x for x in songs if x['albumArtist'] not in seen and not seen_add(x['albumArtist'])]

            for song in songs:
                artists.append({
                    'artistId':     song['artistId'][0],
                    'name':         song['albumArtist'],
                    'artistArtRef': song['artistArtRef'][0]['url'] if 'artistArtRef' in song and len(song['artistArtRef']) > 0 else ''
                })

            artists = sorted(artists, key=lambda k: k['name'].lower())
            with open(artists_cache, 'w+') as f:
                f.write(json.dumps(artists))

        return artists

    def get_my_library_albums(self, from_cache=True):
        albums_cache = os.path.join(_cache_dir, 'albums.json')

        albums = []
        if os.path.exists(albums_cache) and from_cache:
            with open(albums_cache, 'r') as f:
                albums = json.loads(f.read())
        else:
            songs = self.get_my_library_songs()

            # Uniquify all songs by albumId
            seen = set()
            seen_add = seen.add
            songs = [x for x in songs if x['albumId'] not in seen and not seen_add(x['albumId'])]

            for song in songs:
                album = {
                    'albumId':     song['albumId'],
                    'artistId':    song['artistId'],
                    'name':        song['album']       if 'album'       in song else '',
                    'artist':      song['artist']      if 'artist'      in song else '',
                    'albumArtist': song['albumArtist'] if 'albumArtist' in song else '',
                    'year':        song['year']        if 'year'        in song else '',
                    'genre':       song['genre']       if 'genre'       in song else '',
                    'albumArtRef': song['albumArtRef'][0]['url'] if 'albumArtRef' in song and len(song['albumArtRef']) > 0 else '',
                }

                albums.append(album)

            albums = sorted(albums, key=lambda k: k['name'].lower())
            with open(albums_cache, 'w+') as f:
                f.write(json.dumps(albums))

        return albums

    def get_my_library_genres(self):
        songs = self.get_my_library_songs()

        # Uniquify all songs by genre
        seen = set()
        seen_add = seen.add
        songs = [x for x in songs if x['genre'] not in seen and not seen_add(x['genre'])]

        genres = []
        for song in songs:
            genres.append({
                'name':  song['genre'],
                'image': song['albumArtRef'][0]['url'] if 'albumArtRef' in song and len(song['albumArtRef']) > 0 else None
            })


        return sorted(genres, key=lambda k: k['name'])

    def get_user_artist_albums(self, artist_id):
        artist_albums = []
        for album in self.get_my_library_albums():
            if artist_id in album['artistId']:
                artist_albums.append(album)

        return artist_albums

    def get_user_album_songs(self, album_id):
        album_songs = []
        for song in self.get_my_library_songs():
            if album_id == song['albumId']:
                album_songs.append(song)

        return sorted(album_songs, key=lambda k: k['trackNumber'])

    def get_user_genre_albums(self, genre):
        genre_albums = []
        for album in self.get_my_library_albums():
            if genre == album['genre']:
                genre_albums.append(album)

        return sorted(genre_albums, key=lambda k: k['name'])

    def get_user_playlists(self):
        playlists = self.get_all_playlists()
        playlists = sorted(playlists, key=lambda k: k['name'])

        return playlists

    def get_user_playlist(self, playlist_id):
        playlist_content = self.get_all_user_playlist_contents()
        for playlist in playlist_content:
            if playlist['id'] != playlist_id:
                continue

            return playlist

    def get_user_lastadded(self, limit=200):
        songs = self.get_my_library_songs()
        # Google also sorts by tracknumber specific to the album
        # Can we do that as well somehow?
        songs = sorted(songs, key=lambda k: -long(k['recentTimestamp']))

        return songs[:limit]
