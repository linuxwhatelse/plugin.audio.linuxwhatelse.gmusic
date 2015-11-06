#from sys import exit

from os import makedirs
from os.path import join, exists
from json import dumps, loads

from xbmc import translatePath, LOGERROR
from xbmcaddon import Addon
from xbmcgui import Dialog

import utils

from lib.gmusicapi import Mobileclient, Webclient
import mobileclient

_addon     = Addon()
_cache_dir = utils.get_cache_dir(_addon)
_username  = _addon.getSetting('username')
_password  = _addon.getSetting('password')

class GMusic(Mobileclient):

    def _get_android_id(self):
        android_id = _addon.getSetting('android_id')

        if android_id:
            return android_id

        # We use the webclient so we don't have to spoof a androidid and ensure
        # we don't create new devices in google play music or elsewhere
        web = Webclient()
        if not web.login(_username, _password):
            return None

        devices = web.get_registered_devices()
        if not devices:
            return None

        # Display a dialog to the use to choose one of his android-devices for future requests
        action_dialog = Dialog()
        dev_list = []
        for dev in devices:
            if 'id' in dev and dev['id']:
                dev_list.append('%s %s (%s)' % (dev['carrier'], dev['model'], dev['name']))

        selection = action_dialog.select(utils.translate(30042, _addon), dev_list, 0)

        if selection >= 0:
            android_id = devices[selection]['id'].lstrip('0x')
            _addon.setSetting('android_id', android_id)
            return android_id

        return None

    def login(self):
        android_id = self._get_android_id()
        authtoken  = _addon.getSetting('authtoken')

        if authtoken:
            self.android_id               = android_id
            self.session._authtoken       = authtoken
            self.session.is_authenticated = True

            try:
                # Send a test request to ensure our authtoken is still valide and working
                self.get_registered_devices()
                return True
            except:
                # Faild with the test-request so we set "is_authenticated=False"
                # and go through the login-process again to get a new "authtoken"
                self.session.is_authenticated = False

        if android_id:
            if super(GMusic, self).login(_username, _password, android_id):
                _addon.setSetting('authtoken', self.session._authtoken)
                return True

        utils.notify(utils.translate(30048, _addon), '')

        # Prevent further addon execution in case we failed with the login-process
        raise SystemExit

    ##
    ## Overloaded to add some stuff
    ##
    def create_station(self, name, track_id=None, artist_id=None, album_id=None, genre_id=None, curated_station_id=None):
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
        stations_cache = join(_cache_dir, 'stations')
        station_ids_cache = join(stations_cache, '%s.json' % station_id)

        if not exists(stations_cache):
            makedirs(stations_cache)

        if not recently_played_ids:
            if exists(station_ids_cache):
                with open(station_ids_cache, 'r') as f:
                    try:
                        recently_played_ids = loads(f.read())
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

            f.write(dumps(track_ids, indent=2))

        return tracks

    def delete_album(self, album_id):
        songs_cache  = join(_cache_dir, 'songs.json')
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
    def get_listen_now(self):
        res = self._make_call(mobileclient.GetListenNow)
        return res['listennow_items']

    def get_situations(self, locale_code):
        return self._make_call(mobileclient.GetSituations, locale_code)

    def get_new_releases(self, num_items=25, genre=None):
        res = self._make_call(mobileclient.GetNewReleases, num_items, genre)
        for tabs in res['tabs']:
            if tabs['tab_type'] == "NEW_RELEASES":
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

    def get_stations(self, station_subcategory_id, location_id):
        res = self._make_call(mobileclient.GetStations, station_subcategory_id, location_id)
        return res['stations']



    ##
    ## Helper/Wrapper functions
    ##
    def get_my_library_songs(self, from_cache=True):
        songs_cache = join(_cache_dir, 'songs.json')

        songs = None
        if exists(songs_cache) and from_cache:
            with open(songs_cache, 'r') as f:
                songs = loads(f.read())
        else:
            songs = self.get_all_songs(incremental=True, include_deleted=False)
            tmp = []
            for song in songs:
                tmp += song
            songs = tmp

            with open(songs_cache, 'w+') as f:
                f.write(dumps(songs, indent=2))

        return songs

    def get_my_library_artists(self, from_cache=True):
        artists_cache = join(_cache_dir, 'artists.json')

        artists = []
        if exists(artists_cache) and from_cache:
            with open(artists_cache, 'r') as f:
                artists = loads(f.read())
        else:
            songs = self.get_my_library_songs()

            # Uniquify all songs by artistId
            seen = set()
            seen_add = seen.add
            songs = [x for x in songs if x['artistId'][0] not in seen and not seen_add(x['artistId'][0])]

            for song in songs:
                try:
                    artists.append(self.get_artist_info(artist_id=song['artistId'][0], include_albums=False, max_top_tracks=0, max_rel_artist=0))
                except:
                    utils.log('Faild loading artists "%s" with id: "%s"' % (song['artist'], song['artistId'][0]), LOGERROR)

            artists = sorted(artists, key=lambda k: k['name'].lower())
            with open(artists_cache, 'w+') as f:
                f.write(dumps(artists, indent=2))

        return artists

    def get_my_library_albums(self, from_cache=True):
        albums_cache = join(_cache_dir, 'albums.json')

        albums = []
        if exists(albums_cache) and from_cache:
            with open(albums_cache, 'r') as f:
                albums = loads(f.read())
        else:
            songs = self.get_my_library_songs()

            # Uniquify all songs by albumId
            seen = set()
            seen_add = seen.add
            songs = [x for x in songs if x['albumId'] not in seen and not seen_add(x['albumId'])]
            for song in songs:
                if not 'albumId' in song:
                    continue

                album = {
                    'name':        song['album']  if 'album'  in song else '',
                    'artist':      song['artist'] if 'artist' in song else '',
                    'albumArtist': song['albumArtist'] if 'albumArtist' in song else '',
                    'albumArtRef': song['albumArtRef'][0]['url'] if len(song['albumArtRef']) > 0 else '',
                    'albumId':     song['albumId'],
                    'year':        song['year']     if 'year'     in song else '',
                    'genre':       song['genre']    if 'genre'    in song else '',
                    'artistId':    song['artistId'] if 'artistId' in song else '',
                }

                albums.append(album)

            albums = sorted(albums, key=lambda k: k['name'].lower())
            with open(albums_cache, 'w+') as f:
                f.write(dumps(albums, indent=2))

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
