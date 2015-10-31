# -*- coding: utf-8 -*-

"""
These tests all run against an actual Google Music account.

Destructive modifications are not made, but if things go terrible wrong,
an extra test playlist or song may result.
"""

from collections import namedtuple
from hashlib import md5
import itertools
import os
import re
import types
import warnings

from decorator import decorator
from proboscis.asserts import (
    assert_true, assert_equal, assert_is_not_none,
    assert_raises, Check
)
from proboscis import test, before_class, after_class, SkipTest
import requests
from requests.exceptions import SSLError

from gmusicapi import Webclient, Musicmanager, Mobileclient
# from gmusicapi.protocol import mobileclient
from gmusicapi.protocol.shared import authtypes
from gmusicapi.utils.utils import retry, id_or_nid
import gmusicapi.test.utils as test_utils

TEST_PLAYLIST_NAME = 'gmusicapi_test_playlist'
TEST_PLAYLIST_DESCRIPTION = 'gmusicapi test playlist'
TEST_STATION_NAME = 'gmusicapi_test_station'

TEST_AA_GENRE_ID = 'METAL'

# that dumb little intro track on Conspiracy of One,
# picked since it's only a few seconds long
TEST_AA_SONG_ID = 'Tqqufr34tuqojlvkolsrwdwx7pe'

# used for testing streaming.
# differences between clients are presumably from stream quality.
TEST_AA_SONG_WC_HASH = 'c3302fe6bd54ce9b310f92da1904f3b9'
TEST_AA_SONG_MC_HASH = '815c49d3e49eea675d198a2e00aa4c40'

# Amorphis
TEST_AA_ARTIST_ID = 'Apoecs6off3y6k4h5nvqqos4b5e'

# Holographic Universe
TEST_AA_ALBUM_ID = 'B4cao5ms5jjn36notfgnhjtguwa'

# this is owned by my test account, so it shouldn't disappear
TEST_PLAYLIST_SHARETOKEN = ('AMaBXymHAkflgs5lvFAUyyQLYelqqMZNAB4v7Y_-'
                            'v9vmrctLOeW64GScAScoFHEnrLgOP5DSRpl9FYIH'
                            'b84HRBvyIMsxc7Zlrg==')

# this is a little data class for the songs we upload
TestSong = namedtuple('TestSong', 'sid title artist album full_data')


def sids(test_songs):
    """Given [TestSong], return ['sid']."""
    return [s.sid for s in test_songs]


def test_all_access_features():
    return 'GM_A' in os.environ


@decorator
def all_access(f, *args, **kwargs):
    """Declare a test to only be run if All Access testing is enabled."""
    if test_all_access_features():
        return f(*args, **kwargs)
    else:
        raise SkipTest('All Access testing disabled')


@test(groups=['server-other'])
class SslVerificationTests(object):
    # found on https://onlinessl.netlock.hu/en/test-center/invalid-ssl-certificate.html
    test_url = 'https://tv.eurosport.com/'

    @test
    def site_has_invalid_cert(self):
        assert_raises(SSLError, requests.head, self.test_url)

    def request_invalid_site(self, client):
        req_kwargs = {'url': self.test_url,
                      'method': 'HEAD'}
        no_auth = authtypes()

        client.session.send(req_kwargs, no_auth)

    @test
    def clients_verify_by_default(self):
        for client_cls in (Webclient, Mobileclient, Musicmanager):
            assert_raises(SSLError, self.request_invalid_site, client_cls())

    @test
    def disable_client_verify(self):
        for client_cls in (Webclient, Mobileclient, Musicmanager):
            self.request_invalid_site(client_cls(verify_ssl=False))  # should not raise SSLError


@test(groups=['server'])
class ClientTests(object):
    # set on the instance in login
    wc = None  # webclient
    mm = None  # musicmanager
    mc = None  # mobileclient

    # These are set on the instance in eg create_song.

    # both are [TestSong]
    user_songs = None
    aa_songs = None

    playlist_ids = None
    plentry_ids = None
    station_ids = None

    @property
    def all_songs(self):
        return (self.user_songs or []) + (self.aa_songs or [])

    def mc_get_playlist_songs(self, plid):
        """For convenience, since mc can only get all playlists at once."""
        all_contents = self.mc.get_all_user_playlist_contents()
        found = [p for p in all_contents if p['id'] == plid]

        assert_true(len(found), 1)

        return found[0]['tracks']

    @before_class
    def login(self):
        self.wc = test_utils.new_test_client(Webclient)
        assert_true(self.wc.is_authenticated())

        self.mm = test_utils.new_test_client(Musicmanager)
        assert_true(self.mm.is_authenticated())

        self.mc = test_utils.new_test_client(Mobileclient)
        assert_true(self.mc.is_authenticated())

    @after_class(always_run=True)
    def logout(self):
        if self.wc is None:
            raise SkipTest('did not create wc')
        assert_true(self.wc.logout())

        if self.mm is None:
            raise SkipTest('did not create mm')
        assert_true(self.mm.logout())

        if self.mc is None:
            raise SkipTest('did not create mc')
        assert_true(self.mc.logout())

    # This next section is a bit odd: it orders tests that create
    # required resources.

    # The intuitition: starting from an empty library, you need to create
    #  a song before you can eg add it to a playlist.

    # The dependencies end up with an ordering that might look like:
    #
    # with song
    #   with playlist
    #     with plentry
    #   with station
    #
    #
    # Suggestions to improve any of this are welcome!

    @staticmethod
    @retry
    def assert_songs_state(method, sids, present):
        """
        Assert presence/absence of sids and return a list of
        TestSongs found.

        :param method: eg self.mc.get_all_songs
        :param sids: list of song ids
        :param present: if True verify songs are present; False the opposite
        """

        library = method()

        found = [s for s in library if s['id'] in sids]

        expected_len = len(sids)
        if not present:
            expected_len = 0

        assert_equal(len(found), expected_len)

        return [TestSong(s['id'], s['title'], s['artist'], s['album'], s)
                for s in found]

    @staticmethod
    @retry
    def assert_list_inc_equivalence(method, **kwargs):
        """
        Assert that some listing method returns the same
        contents for incremental=True/False.

        :param method: eg self.mc.get_all_songs, must support `incremental` kwarg
        :param **kwargs: passed to method
        """

        lib_chunk_gen = method(incremental=True, **kwargs)
        assert_true(isinstance(lib_chunk_gen, types.GeneratorType))

        assert_equal([e for chunk in lib_chunk_gen for e in chunk],
                     method(incremental=False, **kwargs))

    @staticmethod
    @retry
    def assert_listing_contains_deleted_items(method):
        """
        Assert that some listing method includes deleted tracks.

        :param method: eg self.mc.get_all_songs
        """
        lib = method(incremental=False, include_deleted=True)

        # how long do deleted tracks get returned for?
        # will this return tracks I've deleted since...ever?

        num_deleted = [t for t in lib if t['deleted']]
        assert_true(num_deleted > 0)

    @test
    def song_create(self):
        # This can create more than one song: one through uploading, one through
        # adding an AA track to the library.

        user_sids = []
        aa_sids = []

        fname = test_utils.small_mp3

        uploaded, matched, not_uploaded = self.mm.upload(fname)

        if len(not_uploaded) == 1 and 'ALREADY_EXISTS' in not_uploaded[fname]:
            # delete the song if it exists already because a previous test failed
            self.mc.delete_songs(re.search(r'\(.*\)', not_uploaded[fname]).group().strip('()'))

            # and retry the upload
            uploaded, matched, not_uploaded = self.mm.upload(fname)

        # Otherwise, it should have been uploaded normally.
        assert_equal(not_uploaded, {})
        assert_equal(matched, {})
        assert_equal(uploaded.keys(), [fname])

        user_sids.append(uploaded[fname])

        if test_all_access_features():
            aa_sids.append(self.mc.add_aa_track(TEST_AA_SONG_ID))

        # we test get_all_songs here so that we can assume the existance
        # of the song for future tests (the servers take time to sync an upload)

        self.user_songs = self.assert_songs_state(self.mc.get_all_songs, user_sids, present=True)
        self.aa_songs = self.assert_songs_state(self.mc.get_all_songs, aa_sids, present=True)

    @test
    def playlist_create(self):
        mc_id = self.mc.create_playlist(TEST_PLAYLIST_NAME, "", public=True)
        wc_id = self.wc.create_playlist(TEST_PLAYLIST_NAME, "", public=True)

        # like song_create, retry until the playlist appears
        @retry
        def assert_playlist_exists(plids):
            found = [p for p in self.mc.get_all_playlists()
                     if p['id'] in plids]

            assert_equal(len(found), 2)

        assert_playlist_exists([mc_id, wc_id])
        self.playlist_ids = [mc_id, wc_id]

    @test(depends_on=[playlist_create, song_create],
          runs_after_groups=['playlist.exists', 'song.exists'])
    def plentry_create(self):

        song_ids = [self.user_songs[0].sid]

        # create 3 entries total
        # 3 songs is the minimum to fully test reordering, and also includes the
        # duplicate song_id case
        double_id = self.user_songs[0].sid
        if test_all_access_features():
            double_id = TEST_AA_SONG_ID

        song_ids += [double_id] * 2

        plentry_ids = self.mc.add_songs_to_playlist(self.playlist_ids[0], song_ids)

        @retry
        def assert_plentries_exist(plid, plentry_ids):
            songs = self.mc_get_playlist_songs(plid)
            found = [e for e in songs
                     if e['id'] in plentry_ids]

            assert_equal(len(found), len(plentry_ids))

        assert_plentries_exist(self.playlist_ids[0], plentry_ids)
        self.plentry_ids = plentry_ids

    @test(groups=['plentry'], depends_on=[plentry_create],
          runs_after_groups=['plentry.exists'],
          always_run=True)
    def plentry_delete(self):
        if self.plentry_ids is None:
            raise SkipTest('did not store self.plentry_ids')

        res = self.mc.remove_entries_from_playlist(self.plentry_ids)
        assert_equal(res, self.plentry_ids)

        @retry
        def assert_plentries_removed(plid, entry_ids):
            found = [e for e in self.mc_get_playlist_songs(plid)
                     if e['id'] in entry_ids]

            assert_equal(len(found), 0)

        assert_plentries_removed(self.playlist_ids[0], self.plentry_ids)
        # self.assert_listing_contains_deleted_items(self.mc_get_playlist_songs)

    @test(groups=['playlist'], depends_on=[playlist_create],
          runs_after=[plentry_delete],
          runs_after_groups=['playlist.exists'],
          always_run=True)
    def playlist_delete(self):
        if self.playlist_ids is None:
            raise SkipTest('did not store self.playlist_ids')

        for plid in self.playlist_ids:
            res = self.mc.delete_playlist(plid)
            assert_equal(res, plid)

        @retry
        def assert_playlist_does_not_exist(plid):
            found = [p for p in self.mc.get_all_playlists(include_deleted=False)
                     if p['id'] == plid]

            assert_equal(len(found), 0)

        for plid in self.playlist_ids:
            assert_playlist_does_not_exist(plid)
            self.assert_listing_contains_deleted_items(self.mc.get_all_playlists)

    @test
    def station_create(self):
        if not test_all_access_features():
            raise SkipTest('AA testing not enabled')

        station_ids = []
        for prefix, kwargs in (('AA song', {'track_id': TEST_AA_SONG_ID}),
                               ('AA-added song', {'track_id': self.aa_songs[0].sid}),
                               ('up song', {'track_id': self.user_songs[0].sid}),
                               ('artist', {'artist_id': TEST_AA_ARTIST_ID}),
                               ('album', {'album_id': TEST_AA_ALBUM_ID}),
                               ('genre', {'genre_id': TEST_AA_GENRE_ID})):
            station_ids.append(
                self.mc.create_station(prefix + ' ' + TEST_STATION_NAME, **kwargs))

        @retry
        def assert_station_exists(station_id):
            stations = self.mc.get_all_stations()

            found = [s for s in stations
                     if s['id'] == station_id]

            assert_equal(len(found), 1)

        for station_id in station_ids:
            assert_station_exists(station_id)

        self.station_ids = station_ids

    @test(groups=['station'], depends_on=[station_create, song_create],
          runs_after_groups=['station.exists', 'song.exists'],
          always_run=True)
    def station_delete(self):
        if self.station_ids is None:
            raise SkipTest('did not store self.station_ids')

        res = self.mc.delete_stations(self.station_ids)
        assert_equal(res, self.station_ids)

        @retry
        def assert_station_deleted(station_id):
            stations = self.mc.get_all_stations()

            found = [s for s in stations
                     if s['id'] == station_id]

            assert_equal(len(found), 0)

        for station_id in self.station_ids:
            assert_station_deleted(station_id)
        self.assert_listing_contains_deleted_items(self.mc.get_all_stations)

    @test(groups=['song'], depends_on=[song_create],
          runs_after=[plentry_delete, station_delete],
          runs_after_groups=["song.exists"],
          always_run=True)
    def song_delete(self):
        # split deletion between wc and mc
        # mc is the only to run if AA testing not enabled
        with Check() as check:
            for i, testsong in enumerate(self.all_songs):
                if i % 2 == 0:
                    res = self.mc.delete_songs(testsong.sid)
                else:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        res = self.wc.delete_songs(testsong.sid)
                check.equal(res, [testsong.sid])

        self.assert_songs_state(self.mc.get_all_songs, sids(self.all_songs), present=False)
        self.assert_listing_contains_deleted_items(self.mc.get_all_songs)

    # These decorators just prevent setting groups and depends_on over and over.
    # They won't work right with additional settings; if that's needed this
    #  pattern should be factored out.

    # TODO it'd be nice to have per-client test groups
    song_test = test(groups=['song', 'song.exists'], depends_on=[song_create])
    playlist_test = test(groups=['playlist', 'playlist.exists'],
                         depends_on=[playlist_create])
    plentry_test = test(groups=['plentry', 'plentry.exists'],
                        depends_on=[plentry_create])
    station_test = test(groups=['station', 'station.exists'], depends_on=[station_create])

    # Non-wonky tests resume down here.

    # ---------
    #  MM tests
    # ---------

    @song_test
    def mm_list_new_songs(self):
        # mm only includes user-uploaded songs
        self.assert_songs_state(self.mm.get_uploaded_songs, sids(self.user_songs), present=True)
        self.assert_songs_state(self.mm.get_uploaded_songs, sids(self.aa_songs), present=False)

    @test
    def mm_list_songs_inc_equal(self):
        self.assert_list_inc_equivalence(self.mm.get_uploaded_songs)

    @song_test
    def mm_download_song(self):

        @retry
        def assert_download(sid):
            filename, audio = self.mm.download_song(sid)

            # TODO could use original filename to verify this
            # but, when manually checking, got modified title occasionally
            assert_true(filename.endswith('.mp3'))
            assert_is_not_none(audio)

        assert_download(self.user_songs[0].sid)

    # ---------
    #  WC tests
    # ---------

    @test
    def wc_get_registered_devices(self):
        # no logic; just checking schema
        self.wc.get_registered_devices()

    @test
    def wc_get_shared_playlist_info(self):
        expected = {
            u'author': u'gmusic api',
            u'description': u'description here',
            u'title': u'public title here',
            u'num_tracks': 2
        }

        assert_equal(
            self.wc.get_shared_playlist_info(TEST_PLAYLIST_SHARETOKEN),
            expected
        )

    @test
    @all_access
    def wc_get_aa_stream_urls(self):
        urls = self.wc.get_stream_urls(TEST_AA_SONG_ID)

        assert_true(len(urls) > 1)

    @test
    @all_access
    def wc_stream_aa_track_with_header(self):
        audio = self.wc.get_stream_audio(TEST_AA_SONG_ID, use_range_header=True)

        assert_equal(md5(audio).hexdigest(), TEST_AA_SONG_WC_HASH)

    @test
    @all_access
    def wc_stream_aa_track_without_header(self):
        audio = self.wc.get_stream_audio(TEST_AA_SONG_ID, use_range_header=False)

        assert_equal(md5(audio).hexdigest(), TEST_AA_SONG_WC_HASH)

    @song_test
    def wc_get_download_info(self):
        url, download_count = self.wc.get_song_download_info(self.user_songs[0].sid)

        assert_is_not_none(url)

    @song_test
    def wc_get_uploaded_stream_urls(self):
        urls = self.wc.get_stream_urls(self.user_songs[0].sid)

        assert_equal(len(urls), 1)

        url = urls[0]

        assert_is_not_none(url)
        assert_equal(url.split(':')[0], 'https')

    @song_test
    def wc_upload_album_art(self):
        url = self.wc.upload_album_art(self.user_songs[0].sid, test_utils.image_filename)
        assert_equal(url[:4], 'http')
        # TODO download the track and verify the metadata changed

    # ---------
    #  MC tests
    # ---------

    @test
    def mc_get_registered_devices(self):
        # no logic; just checking schema
        self.mc.get_registered_devices()

    @test
    def mc_list_stations_inc_equal(self):
        self.assert_list_inc_equivalence(self.mc.get_all_stations)

    @test
    def mc_list_stations_inc_equal_with_deleted(self):
        self.assert_list_inc_equivalence(self.mc.get_all_stations, include_deleted=True)

    @test
    def mc_list_shared_playlist_entries(self):
        entries = self.mc.get_shared_playlist_contents(TEST_PLAYLIST_SHARETOKEN)
        assert_true(len(entries) > 0)

    @test
    @all_access
    def mc_stream_aa_track(self):
        url = self.mc.get_stream_url(TEST_AA_SONG_ID)  # uses frozen device_id
        audio = self.mc.session._rsession.get(url).content
        assert_equal(md5(audio).hexdigest(), TEST_AA_SONG_MC_HASH)

    @song_test
    def mc_get_uploaded_track_stream_url(self):
        url = self.mc.get_stream_url(self.user_songs[0].sid)

        assert_is_not_none(url)
        assert_equal(url[:4], 'http')

    @staticmethod
    @retry
    def _assert_song_key_equal_to(method, sid, key, value):
        """
        :param method: eg self.mc.get_all_songs
        :param sid: song id
        :param key: eg 'rating'
        :param value: eg '1'
        """
        songs = method()

        if not isinstance(songs, list):
            # kind of a hack to support get_track_info as well
            songs = [songs]

        found = [s for s in songs if id_or_nid(s) == sid]

        assert_equal(len(found), 1)

        assert_equal(found[0][key], value)
        return found[0]

    # how can I get the rating key to show up for store tracks?
    # it works in Google's clients!

    # @test
    # @all_access
    # def mc_change_store_song_rating(self):
    #     song = self.mc.get_track_info(TEST_AA_SONG_ID)

    #     # increment by one but keep in rating range
    #     song['rating'] = int(song.get('rating', '0')) + 1
    #     song['rating'] = str(song['rating'] % 6)

    #     self.mc.change_song_metadata(song)

    #     self._assert_song_key_equal_to(lambda: self.mc.get_track_info(TEST_AA_SONG_ID),
    #                              id_or_nid(song),
    #                              song['rating'])

    @song_test
    def mc_change_uploaded_song_rating(self):
        song = self._assert_song_key_equal_to(
            self.mc.get_all_songs,
            self.all_songs[0].sid,
            'rating',
            '0')  # initially unrated

        song['rating'] = '1'
        self.mc.change_song_metadata(song)

        self._assert_song_key_equal_to(self.mc.get_all_songs, song['id'], 'rating', '1')

        song['rating'] = '0'
        self.mc.change_song_metadata(song)

    @song_test
    @all_access
    @retry
    def mc_get_promoted_songs(self):
        song = self.mc.get_track_info(TEST_AA_SONG_ID)

        song['rating'] = '5'
        self.mc.change_song_metadata(song)

        promoted = self.mc.get_promoted_songs()
        assert_true(len(promoted))

        song['rating'] = '0'
        self.mc.change_song_metadata(song)

    def _test_increment_playcount(self, sid):
        matching = [t for t in self.mc.get_all_songs()
                    if t['id'] == sid]
        assert_equal(len(matching), 1)

        # playCount is an optional field.
        initial_playcount = matching[0].get('playCount', 0)

        self.mc.increment_song_playcount(sid, 2)

        self._assert_song_key_equal_to(
            self.mc.get_all_songs,
            sid,
            'playCount',
            initial_playcount + 2)

    @song_test
    def mc_increment_uploaded_song_playcount(self):
        self._test_increment_playcount(self.all_songs[0].sid)

    # Fails silently. See https://github.com/simon-weber/gmusicapi/issues/349.
    # @song_test
    # @all_access
    # def mc_increment_aa_song_playcount(self):
    #     self._test_increment_playcount(self.all_songs[1].sid)

    @song_test
    def mc_change_uploaded_song_title_fails(self):
        # this used to work, but now only ratings can be changed.
        # this test is here so I can tell if this starts working again.
        song = self.assert_songs_state(self.mc.get_all_songs, [self.all_songs[0].sid],
                                       present=True)[0]

        old_title = song.title
        new_title = old_title + '_mod'
        self.mc.change_song_metadata({'id': song.sid, 'title': new_title})

        self._assert_song_key_equal_to(self.mc.get_all_songs, song.sid, 'title', old_title)

    @song_test
    def mc_list_songs_inc_equal(self):
        self.assert_list_inc_equivalence(self.mc.get_all_songs)

    @song_test
    def mc_list_songs_inc_equal_with_deleted(self):
        self.assert_list_inc_equivalence(self.mc.get_all_songs, include_deleted=True)

    @playlist_test
    def mc_list_playlists_inc_equal(self):
        self.assert_list_inc_equivalence(self.mc.get_all_playlists)

    @playlist_test
    def mc_list_playlists_inc_equal_with_deleted(self):
        self.assert_list_inc_equivalence(self.mc.get_all_playlists, include_deleted=True)

    @playlist_test
    def mc_edit_playlist_name(self):
        new_name = TEST_PLAYLIST_NAME + '_mod'
        plid = self.mc.edit_playlist(self.playlist_ids[0], new_name=new_name)
        assert_equal(self.playlist_ids[0], plid)

        @retry  # change takes time to propogate
        def assert_name_equal(plid, name):
            playlists = self.mc.get_all_playlists()

            found = [p for p in playlists if p['id'] == plid]

            assert_equal(len(found), 1)
            assert_equal(found[0]['name'], name)

        assert_name_equal(self.playlist_ids[0], new_name)

        # revert
        self.mc.edit_playlist(self.playlist_ids[0], new_name=TEST_PLAYLIST_NAME)
        assert_name_equal(self.playlist_ids[0], TEST_PLAYLIST_NAME)

    @playlist_test
    def mc_edit_playlist_description(self):
        new_description = TEST_PLAYLIST_DESCRIPTION + '_mod'
        plid = self.mc.edit_playlist(self.playlist_ids[0], new_description=new_description)
        assert_equal(self.playlist_ids[0], plid)

        @retry  # change takes time to propogate
        def assert_description_equal(plid, description):
            playlists = self.mc.get_all_playlists()

            found = [p for p in playlists if p['id'] == plid]

            assert_equal(len(found), 1)
            assert_equal(found[0]['description'], description)

        assert_description_equal(self.playlist_ids[0], new_description)

        # revert
        self.mc.edit_playlist(self.playlist_ids[0], new_description=TEST_PLAYLIST_DESCRIPTION)
        assert_description_equal(self.playlist_ids[0], TEST_PLAYLIST_DESCRIPTION)

    @playlist_test
    def mc_edit_playlist_public(self):
        new_public = False
        plid = self.mc.edit_playlist(self.playlist_ids[0], public=new_public)
        assert_equal(self.playlist_ids[0], plid)

        @retry  # change takes time to propogate
        def assert_public_equal(plid, public):
            playlists = self.mc.get_all_playlists()

            found = [p for p in playlists if p['id'] == plid]

            assert_equal(len(found), 1)
            assert_equal(found[0]['accessControlled'], public)

        assert_public_equal(self.playlist_ids[0], new_public)

        # revert
        self.mc.edit_playlist(self.playlist_ids[0], public=True)
        assert_public_equal(self.playlist_ids[0], True)

    @retry(tries=3)
    def _mc_assert_ple_position(self, entry, pos):
        """
        :param entry: entry dict
        :pos: 0-based position to assert
        """
        pl = self.mc_get_playlist_songs(entry['playlistId'])

        indices = [i for (i, e) in enumerate(pl)
                   if e['id'] == entry['id']]

        assert_equal(len(indices), 1)

        assert_equal(indices[0], pos)

    @retry
    def _mc_test_ple_reodering(self, from_pos, to_pos):
        if from_pos == to_pos:
            raise ValueError('Will not test no-op reordering.')

        pl = self.mc_get_playlist_songs(self.playlist_ids[0])

        from_e = pl[from_pos]

        e_before_new_pos, e_after_new_pos = None, None

        if from_pos < to_pos:
            adj = 0
        else:
            adj = -1

        if to_pos - 1 >= 0:
            e_before_new_pos = pl[to_pos + adj]

        if to_pos + 1 < len(self.plentry_ids):
            e_after_new_pos = pl[to_pos + adj + 1]

        self.mc.reorder_playlist_entry(from_e,
                                       to_follow_entry=e_before_new_pos,
                                       to_precede_entry=e_after_new_pos)
        self._mc_assert_ple_position(from_e, to_pos)

        if e_before_new_pos:
            self._mc_assert_ple_position(e_before_new_pos, to_pos - 1)

        if e_after_new_pos:
            self._mc_assert_ple_position(e_after_new_pos, to_pos + 1)

    @plentry_test
    def mc_reorder_ple_forwards(self):
        for from_pos, to_pos in [pair for pair in
                                 itertools.product(range(len(self.plentry_ids)), repeat=2)
                                 if pair[0] < pair[1]]:
            self._mc_test_ple_reodering(from_pos, to_pos)

    @plentry_test
    def mc_reorder_ple_backwards(self):
        playlist_len = len(self.plentry_ids)
        for from_pos, to_pos in [pair for pair in
                                 itertools.product(range(playlist_len), repeat=2)
                                 if pair[0] > pair[1]]:
            self._mc_test_ple_reodering(from_pos, to_pos)

    # This fails, unfortunately, which means n reorderings mean n
    # separate calls in the general case.
    # @plentry_test
    # def mc_reorder_ples_forwards(self):
    #    pl = self.mc_get_playlist_songs(self.playlist_ids[0])
    #    # rot2, eg 0123 -> 2301
    #    pl.append(pl.pop(0))
    #    pl.append(pl.pop(0))

    #    mutate_call = mobileclient.BatchMutatePlaylistEntries
    #    mutations = [
    #        mutate_call.build_plentry_reorder(
    #            pl[-1], pl[-2]['clientId'], None),
    #        mutate_call.build_plentry_reorder(
    #            pl[-2], pl[-3]['clientId'], pl[-1]['clientId'])
    #    ]

    #    self.mc._make_call(mutate_call, [mutations])
    #    self._mc_assert_ple_position(pl[-1], len(pl) - 1)
    #    self._mc_assert_ple_position(pl[-2], len(pl) - 2)

    @station_test
    @retry  # sometimes this comes back with no data key
    @all_access
    def mc_list_station_tracks(self):
        for station_id in self.station_ids:
            self.mc.get_station_tracks(station_id, num_tracks=1)
            # used to assert that at least 1 track came back, but
            # our dummy uploaded track won't match anything
            self.mc.get_station_tracks(station_id, num_tracks=1,
                                       recently_played_ids=[TEST_AA_SONG_ID])
            self.mc.get_station_tracks(station_id, num_tracks=1,
                                       recently_played_ids=[self.user_songs[0].sid])

    @all_access
    def mc_list_IFL_station_tracks(self):
        assert_equal(len(self.mc.get_station_tracks('IFL', num_tracks=1)),
                     1)

    @test(groups=['search'])
    @all_access
    def mc_search_aa_no_playlists(self):
        res = self.mc.search_all_access('amorphis', max_results=100)

        # TODO is there a search query that will consistently get playlist results?
        res.pop('playlist_hits')

        with Check() as check:
            for type_, hits in res.items():
                check.true(len(hits) > 0, "%s had %s hits, expected > 0" % (type_, len(hits)))

    @test
    @all_access
    def mc_artist_info(self):
        aid = 'Apoecs6off3y6k4h5nvqqos4b5e'  # amorphis
        optional_keys = set(('albums', 'topTracks', 'related_artists'))

        include_all_res = self.mc.get_artist_info(aid, include_albums=True,
                                                  max_top_tracks=1, max_rel_artist=1)

        no_albums_res = self.mc.get_artist_info(aid, include_albums=False)
        no_rel_res = self.mc.get_artist_info(aid, max_rel_artist=0)
        no_tracks_res = self.mc.get_artist_info(aid, max_top_tracks=0)

        with Check() as check:
            check.true(set(include_all_res.keys()) & optional_keys == optional_keys)

            check.true(set(no_albums_res.keys()) & optional_keys ==
                       optional_keys - set(['albums']))
            check.true(set(no_rel_res.keys()) & optional_keys ==
                       optional_keys - set(['related_artists']))
            check.true(set(no_tracks_res.keys()) & optional_keys ==
                       optional_keys - set(['topTracks']))

    @test
    @retry
    @all_access
    def mc_album_info(self):
        include_tracks = self.mc.get_album_info(TEST_AA_ALBUM_ID, include_tracks=True)
        no_tracks = self.mc.get_album_info(TEST_AA_ALBUM_ID, include_tracks=False)

        with Check() as check:
            check.true('tracks' in include_tracks)
            check.true('tracks' not in no_tracks)

            del include_tracks['tracks']
            check.equal(include_tracks, no_tracks)

    @test
    @all_access
    def mc_track_info(self):
        self.mc.get_track_info(TEST_AA_SONG_ID)  # just for the schema

    @test(groups=['genres'])
    @all_access
    def mc_all_genres(self):
        expected_genres = set([
            u'COMEDY_SPOKEN_WORD_OTHER', u'COUNTRY', u'HOLIDAY', u'R_B_SOUL', u'FOLK', u'LATIN',
            u'CHRISTIAN_GOSPEL', u'ALTERNATIVE_INDIE', u'POP', u'ROCK', u'WORLD',
            u'VOCAL_EASY_LISTENING', u'HIP_HOP_RAP', u'JAZZ', u'METAL', u'REGGAE_SKA',
            u'SOUNDTRACKS_CAST_ALBUMS', u'DANCE_ELECTRONIC', u'CLASSICAL', u'NEW_AGE', u'BLUES',
            u'CHILDREN_MUSIC'])
        res = self.mc.get_genres()
        assert_equal(set([e['id'] for e in res]), expected_genres)

    @test(groups=['genres'])
    @all_access
    def mc_specific_genre(self):
        expected_genres = set([
            u'PROGRESSIVE_METAL', u'CLASSIC_METAL', u'HAIR_METAL', u'INDUSTRIAL', u'ALT_METAL',
            u'THRASH', u'METALCORE', u'BLACK_DEATH_METAL', u'DOOM_METAL'])
        res = self.mc.get_genres('METAL')
        assert_equal(set([e['id'] for e in res]), expected_genres)

    @test(groups=['genres'])
    @all_access
    def mc_leaf_parent_genre(self):
        assert_equal(self.mc.get_genres('AFRICA'), [])

    @test(groups=['genres'])
    @all_access
    def mc_invalid_parent_genre(self):
        assert_equal(self.mc.get_genres('bogus genre'), [])
