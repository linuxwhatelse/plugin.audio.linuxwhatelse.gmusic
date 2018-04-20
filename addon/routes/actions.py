import os
import json
import shutil
import urlparse
import re
import uuid
import codecs

import xbmc
import xbmcgui
import xbmcplugin

import mapper
import gmusicapi

from addon.gmusic_wrapper import GMusic
from addon import utils
from addon import listing
from addon import thumbs

from addon import ADDON
from addon import URL
from addon import ADDON_HANDLE


MPR = mapper.Mapper.get()
GMUSIC = GMusic.get(debug_logging=False)
_CACHE_DIR = utils.get_cache_dir()


@MPR.s_url('/setup/', type_cast={'force': bool})
def setup(force=False):
    is_setup = True if ADDON.getSetting('is_setup') == 'true' else False

    if is_setup and not force:
        return True

    dialog = xbmcgui.Dialog()

    username = dialog.input(utils.translate(30075),
                            type=xbmcgui.INPUT_ALPHANUM)
    if not username:
        return False

    # If 2-Factor Authentication is used
    is_two_factor = dialog.yesno(
        utils.translate(30071), utils.translate(30072))
    if is_two_factor:
        if not dialog.ok(utils.translate(30071),
                         utils.translate(30073), utils.translate(30074)):
            return False

    password = dialog.input(utils.translate(30076),
                            type=xbmcgui.INPUT_ALPHANUM,
                            option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if not password:
        return False

    device_id = None
    if is_two_factor:
        # If Android Device available
        if dialog.yesno(utils.translate(30077), utils.translate(30078)):
            if not dialog.ok(utils.translate(30079), utils.translate(30081)):
                return False

            device_id = dialog.input(utils.translate(30084),
                                     type=xbmcgui.INPUT_ALPHANUM)
            if not device_id:
                return False
        else:
            # If using MAC-Address
            if dialog.yesno(utils.translate(30082), utils.translate(30083)):
                device_id = gmusicapi.Mobileclient.FROM_MAC_ADDRESS
            else:
                return False
    else:
        web = gmusicapi.Webclient()
        if not web.login(username, password):
            # If re-run setup due to login failed
            if dialog.yesno(utils.translate(30048), utils.translate(30085)):
                return setup(force=True)
            else:
                return False

        try:
            devices = web.get_registered_devices()
            if not devices:
                raise

            dev_list = []
            for dev in devices:
                # Not an Android Device so we skip as streaming would not work
                if dev['deviceType'] != 2:
                    continue

                if 'id' in dev and dev['id']:
                    dev_list.append('%s - %s' % (
                        dev.get('carrier', '').strip(' '),
                        dev.get('model', '').strip(' '),
                    ))
                    dev_list = sorted(dev_list)

            if len(dev_list) <= 0:
                raise

            elif len(dev_list) == 1:
                device_id = devices[0]['id'].lstrip('0x')

            else:
                selection = dialog.select(utils.translate(30042), dev_list, 0)

                if selection >= 0:
                    device_id = devices[selection]['id'].lstrip('0x')

                else:
                    return False

        except Exception:
            # If use MAC-Address instead due to no devices found
            if not dialog.yesno(utils.translate(30079), utils.translate(30097)):
                return False

            device_id = gmusicapi.Mobileclient.FROM_MAC_ADDRESS

    # Test login
    mobile = gmusicapi.Mobileclient()
    if mobile.login(username, password, device_id):

        # Test if this is an all-access account
        if not mobile.get_all_stations():
            dialog.ok(utils.translate(30091), utils.translate(30092))
            return False

        ADDON.setSetting('username',  username)
        ADDON.setSetting('password',  password)
        ADDON.setSetting('authtoken', mobile.session._authtoken)

        if device_id == gmusicapi.Mobileclient.FROM_MAC_ADDRESS:
            mac_address = ''.join(re.findall('..', '%012x' % uuid.getnode()))
            ADDON.setSetting('device_id', mac_address)
        else:
            ADDON.setSetting('device_id', device_id)

        ADDON.setSetting('is_setup', 'true')

        utils.notify(utils.translate(30086), utils.translate(30087))

        return True

    else:
        # If re-run setup
        if dialog.yesno(utils.translate(30048), utils.translate(30085)):
            return setup(force=True)

        return False


##############
## PLAYBACK ##
##############
def _get_track_details(track_id, store_id=None):
    cache = os.path.join(utils.get_cache_dir(['tracks']), track_id)

    if os.path.exists(cache):
        with open(cache, 'r') as f:
            track = json.loads(f.read())

    elif store_id:
        try:
            track = GMUSIC.get_track_info(store_track_id=track_id)

        except Exception:
            pass

    else:
        track = None

    return track


@MPR.s_url('/play/track/<track_id>/')
def play_track(track_id, store_id=None, track_title='', station_id=None):
    track = _get_track_details(track_id, store_id)

    item = None
    if track:
        item = listing.build_song_listitems([track])[0][1]

    else:
        item = xbmcgui.ListItem(track_title)
        item.setArt({
            'thumb': thumbs.IMG_ALBUM,
            'poster': thumbs.IMG_ALBUM
        })

    item.setPath(
        GMUSIC.get_stream_url(
            song_id=track_id,
            quality=ADDON.getSetting('stream_quality')
        )
    )

    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, item)

    GMUSIC.increment_song_playcount(track_id)

    # If the current track is from a station and within the last five (5)
    # playlist tracks, we get a new set of tracks for this station and
    # add it to the playlist.
    if station_id:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        if playlist.getposition() >= (len(playlist) - 5):
            queue_station(station_id)


@MPR.s_url('/play/album/<album_id>/')
def play_album(album_id):
    # _play uses the previous url and matches it to one of `files.py`
    _play(path=['album', album_id])


@MPR.s_url('/play/playlist/')
def play_playlist(playlist_id=None, playlist_token=None):
    # _play uses the previous url and matches it to one of `files.py`
    _play(['playlist'])


@MPR.s_url('/play/station/')
def play_station(station_id=None, station_name=None, artist_id=None,
                 album_id=None, genre_id=None, track_id=None,
                 curated_station_id=None, playlist_token=None):
    # Shuffle and Repeat make no sense what so ever when starting a station
    utils.execute_jsonrpc('Player.SetShuffle',
                          {'playerid': xbmc.PLAYLIST_MUSIC, 'shuffle': False})

    utils.execute_jsonrpc('Player.SetRepeat',
                          {'playerid': xbmc.PLAYLIST_MUSIC, 'repeat': 'off'})

    # _play uses the previous url and matches it to one of `files.py`
    _play(['station'])


def _play(path):
    utils.execute_jsonrpc(method='Playlist.Clear',
                          params={'playlistid': xbmc.PLAYLIST_MUSIC})

    utils.execute_jsonrpc(
        method='Playlist.Add',
        params={
            'playlistid': xbmc.PLAYLIST_MUSIC,
            'item': {
                'directory': utils.build_url(url=URL, paths=path, r_path=True)
            }
        }
    )

    utils.execute_jsonrpc(
        method='Player.Open',
        params={'item': {'playlistid': xbmc.PLAYLIST_MUSIC, 'position': 0}}
    )

    if ADDON.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen': True})


#############
## QUEUING ##
#############
@MPR.s_url('/queue/track/<track_id>/')
def queue_track(track_id, track_title='', play_next=False):
    track = _get_track_details(track_id)

    path = None
    item = None
    if track:
        listitem = listing.build_song_listitems([track])[0]
        path = listitem[0]
        item = listitem[1]

    else:
        item = xbmcgui.ListItem(track_title)
        item.setArt({
            'thumb': thumbs.IMG_ALBUM,
            'poster': thumbs.IMG_ALBUM
        })

        path = utils.build_url(
            url=URL,
            paths=['play', 'track', track_id],
            queries={'track_title': track_title},
            r_path=True,
            r_query=True
        )

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1
    if play_next:
        position = playlist.getposition() + 1

    playlist.add(URL=path, listitem=item, index=position)


@MPR.s_url('/queue/album/<album_id>/')
def queue_album(album_id, play_next=False):
    _queue(['album', album_id], play_next)


@MPR.s_url('/queue/playlist/<playlist_id>/')
def queue_playlist(playlist_id, play_next=False):
    _queue(['playlist', playlist_id], play_next)


@MPR.url('^/queue/station/$')
def queue_station(station_id=None, station_name=None, artist_id=None,
                  album_id=None, genre_id=None, track_id=None,
                  curated_station_id=None, play_next=False):
    _queue(['station'])


def _queue(path, play_next=False):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1

    if play_next:
        position = playlist.getposition() + 1

    query = dict(urlparse.parse_qsl(urlparse.urlparse(URL).query))
    if 'play_next' in query:
        del query['play_next']
        position = playlist.getposition() + 1

    utils.execute_jsonrpc(
        method='Playlist.Insert',
        params={
            'playlistid': xbmc.PLAYLIST_MUSIC,
            'position': position,
            'item': {
                'directory': utils.build_url(
                    url=URL,
                    paths=path,
                    queries=query,
                    r_path=True,
                    r_query=True
                )
            }
        }
    )


############
## SEARCH ##
############
@MPR.s_url('/search/history/')
def search_history():
    history = _get_search_history()

    # Add "New Search" to the list
    item = xbmcgui.ListItem(utils.translate(30053))
    item.setArt({
        'thumb': thumbs.IMG_SEARCH,
        'poster': thumbs.IMG_SEARCH
    })

    items = [(
        utils.build_url(
            url=URL,
            paths=['search', 'new'],
            r_path=True,
            r_query=True
        ),
        item,
        True
    )]

    for hist in history:
        item = xbmcgui.ListItem(hist)
        item.setArt({
            'thumb': thumbs.IMG_SEARCH,
            'poster': thumbs.IMG_SEARCH
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', hist],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    listing.list_items(items)


@MPR.s_url('/search/new/')
def search_new():
    keyboard = xbmc.Keyboard()
    keyboard.doModal()

    if keyboard.isConfirmed() and keyboard.getText():
        query = keyboard.getText()

    else:
        # User canceled or used a empty search-string
        return

    search(query)


@MPR.s_url('/search/<query>/')
def search(query):
    history_file = os.path.join(_CACHE_DIR, 'search_history.json')
    history = _get_search_history()

    # It was a new search so we add it to the history
    if query.decode('utf-8').lower() not in (hist.lower() for hist in history):
        history.insert(0, query)
        with codecs.open(history_file, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(history[:20], indent=2))

    result = GMUSIC.search(query)

    if not result:
        listing.list_items([])
        return

    items = []
    if 'artist_hits' in result and len(result['artist_hits']) > 0:
        item = xbmcgui.ListItem('%s (%s)' % (utils.translate(30022),
                                             len(result['artist_hits'])))
        item.setArt({
            'thumb': thumbs.IMG_ARTIST,
            'poster': thumbs.IMG_ARTIST
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', 'artists', query],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    if 'album_hits' in result and len(result['album_hits']) > 0:
        item = xbmcgui.ListItem('%s (%s)' % (utils.translate(30023),
                                             len(result['album_hits'])))
        item.setArt({
            'thumb': thumbs.IMG_ALBUM,
            'poster': thumbs.IMG_ALBUM
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', 'albums', query],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    if 'playlist_hits' in result and len(result['playlist_hits']) > 0:
        item = xbmcgui.ListItem('%s (%s)' % (utils.translate(30020),
                                             len(result['playlist_hits'])))
        item.setArt({
            'thumb': thumbs.IMG_PLAYLIST,
            'poster': thumbs.IMG_PLAYLIST
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', 'playlists', query],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    if 'station_hits' in result and len(result['station_hits']) > 0:
        item = xbmcgui.ListItem('%s (%s)' % (utils.translate(30021),
                                             len(result['station_hits'])))
        item.setArt({
            'thumb': thumbs.IMG_STATION,
            'poster': thumbs.IMG_STATION
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', 'stations', query],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    if 'song_hits' in result and len(result['song_hits']) > 0:
        item = xbmcgui.ListItem('%s (%s)' % (utils.translate(30024),
                                             len(result['song_hits'])))
        item.setArt({
            'thumb': thumbs.IMG_TRACK,
            'poster': thumbs.IMG_TRACK
        })

        items.append((
            utils.build_url(
                url=URL,
                paths=['search', 'songs', query],
                r_path=True,
                r_query=True
            ),
            item,
            True
        ))

    listing.list_items(items)


@MPR.s_url('/search/artists/<query>/')
def search_artists(query):
    if query:
        result = GMUSIC.search(query)
    else:
        result = GMUSIC.search(cached=True)

    if result:
        items = listing.build_artist_listitems(result['artist_hits'])
        listing.list_artists(items)


@MPR.s_url('/search/albums/<query>/')
def search_albums(query):
    if query:
        result = GMUSIC.search(query)
    else:
        result = GMUSIC.search(cached=True)

    if result:
        items = listing.build_album_listitems(result['album_hits'])
        listing.list_albums(items)


@MPR.s_url('/search/playlists/<query>/')
def search_playlists(query):
    if query:
        result = GMUSIC.search(query)
    else:
        result = GMUSIC.search(cached=True)

    if result:
        items = listing.build_playlist_listitems(result['playlist_hits'])
        listing.list_playlists(items)


@MPR.s_url('/search/stations/<query>/')
def search_stations(query):
    if query:
        result = GMUSIC.search(query)
    else:
        result = GMUSIC.search(cached=True)

    if result:
        items = listing.build_station_listitems(result['station_hits'])
        listing.list_stations(items)


@MPR.s_url('/search/songs/<query>/')
def search_songs(query):
    if query:
        result = GMUSIC.search(query)
    else:
        result = GMUSIC.search(cached=True)

    if result:
        items = listing.build_song_listitems(result['song_hits'])
        listing.list_songs(items)


def _get_search_history():
    history_file = os.path.join(_CACHE_DIR, 'search_history.json')

    history = []
    if os.path.exists(history_file):
        with codecs.open(history_file, 'r', encoding='utf-8') as f:
            try:
                history = json.loads(f.read())
            except ValueError:
                pass

    return history


###################
## MISCELLANEOUS ##
###################
@MPR.s_url('/my-library/update/')
def my_library_update():
    utils.notify(utils.translate(30030), utils.translate(30043))

    GMUSIC.get_my_library_songs(from_cache=False)
    GMUSIC.get_my_library_artists(from_cache=False)
    GMUSIC.get_my_library_albums(from_cache=False)

    utils.notify(utils.translate(30030), utils.translate(30044))

    xbmc.executebuiltin('Container.Refresh')


@MPR.s_url('/my-library/add/track/<track_id>/')
@MPR.s_url('/my-library/add/album/<album_id>/')
def my_library_add(album_id=None, track_id=None):
    if track_id:
        GMUSIC.add_store_track(track_id)

    elif album_id:
        album = GMUSIC.get_album_info(album_id=album_id, include_tracks=True)
        for track in album['tracks']:
            if 'storeId' in track:
                GMUSIC.add_store_track(track['storeId'])

    if xbmcgui.Dialog().yesno(heading=utils.translate(30030),
                              line1=utils.translate(30065)):
        my_library_update()


@MPR.s_url('/my-library/remove/track/<track_id>/')
@MPR.s_url('/my-library/remove/album/<album_id>/')
def my_library_remove(album_id=None, track_id=None):
    if not album_id and not track_id:
        return

    if not xbmcgui.Dialog().yesno(heading=utils.translate(30061),
                                  line1=utils.translate(30063)):
        return

    if album_id:
        GMUSIC.delete_album(album_id)

    elif track_id:
        GMUSIC.delete_songs([track_id])

    if xbmcgui.Dialog().yesno(heading=utils.translate(30030),
                              line1=utils.translate(30065)):
        my_library_update()


@MPR.s_url('/my-library/playlist/add/')
def my_library_playlist_add(playlist_id=None, album_id=None, track_id=None):
    # In case no playlist_id is specified we guide the user through
    # the process of selecting one.
    # He will also have the ability to create a new one
    if not playlist_id:
        action_dialog = xbmcgui.Dialog()
        playlists = GMUSIC.get_user_playlists()

        playlist_names = []
        playlist_ids = []
        for playlist in playlists:
            if playlist['type'] != 'USER_GENERATED':
                continue

            playlist_names.append(playlist['name'])
            playlist_ids.append(playlist['id'])

        playlist_names.insert(0, utils.translate(30052))
        selection = action_dialog.select(utils.translate(30020),
                                         playlist_names, 0)
        if selection == -1:
            return

        if selection == 0:
            keyboard = xbmc.Keyboard()
            keyboard.doModal()

            if keyboard.isConfirmed() and keyboard.getText():
                playlist_id = GMUSIC.create_playlist(name=keyboard.getText())
        else:
            playlist_id = playlist_ids[selection-1]

    if playlist_id:
        if track_id:
            GMUSIC.add_songs_to_playlist(playlist_id=playlist_id,
                                         song_ids=track_id)

        elif album_id:
            album = GMUSIC.get_album_info(
                album_id=album_id, include_tracks=True)

            track_ids = []
            for track in album['tracks']:
                if 'storeId' in track:
                    track_ids.append(track['storeId'])

            GMUSIC.add_songs_to_playlist(playlist_id=playlist_id,
                                         song_ids=track_ids)


@MPR.s_url('/my-library/playlist/remove/')
def my_library_playlist_remove(entry_id):
    if xbmcgui.Dialog().yesno(heading=utils.translate(30062),
                              line1=utils.translate(30064)):
        GMUSIC.remove_entries_from_playlist([entry_id])

        xbmc.executebuiltin('Container.Refresh')


@MPR.s_url('/my-library/playlist/delete/')
def my_library_playlist_delete(playlist_id):
    if xbmcgui.Dialog().yesno(heading=utils.translate(30068),
                              line1=utils.translate(30069)):
        GMUSIC.delete_playlist(playlist_id)

        xbmc.executebuiltin('Container.Refresh')


@MPR.s_url('/rate/')
def rate(track_id):
    rating = [
        utils.translate(30027),  # Thumbs up
        utils.translate(30028),  # No Thumbs
        utils.translate(30029),  # Thumbs down
    ]

    dialog = xbmcgui.Dialog()
    selection = dialog.select(utils.translate(30041), rating, 0)

    if selection == -1:
        return

    song = GMUSIC.get_track_info(track_id)

    if not song:
        return

    if selection == 0:
        GMUSIC.rate_songs(song, 5)

    elif selection == 1:
        GMUSIC.rate_songs(song, 0)

    elif selection == 2:
        GMUSIC.rate_songs(song, 1)

    utils.notify(utils.translate(30099), "")


@MPR.s_url('/clear/cache/')
def clear_cache():
    if os.path.exists(_CACHE_DIR):
        shutil.rmtree(_CACHE_DIR)

    utils.notify(utils.translate(30094), '', display_time=1000)


@MPR.s_url('/clear/search-history/')
def clear_search_history():
    history_file = os.path.join(_CACHE_DIR, 'search_history.json')
    if os.path.exists(history_file):
        os.remove(history_file)

    utils.notify(utils.translate(30095), '', display_time=1000)
