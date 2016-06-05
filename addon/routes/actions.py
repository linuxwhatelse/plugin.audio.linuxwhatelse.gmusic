import os
import json
import shutil
import time
import urlparse
import re
import uuid
import threading

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import gmusicapi

from addon import utils
from addon import thumbs

from addon import addon
from addon import mpr
from addon import url
from addon import addon_handle
from addon import listing
from addon import gmusic


_cache_dir = utils.get_cache_dir()


@mpr.url('^/setup/$', type_cast={'force' : bool})
def setup(force=False):
    is_setup = True if addon.getSetting('is_setup') == 'true' else False

    if is_setup and not force:
        return True

    dialog = xbmcgui.Dialog()

    username = dialog.input(utils.translate(30075), type=xbmcgui.INPUT_ALPHANUM)
    if not username:
        return False

    # If 2-Factor Authentication is used
    is_two_factor = dialog.yesno(utils.translate(30071), utils.translate(30072))
    if is_two_factor:
        if not dialog.ok(utils.translate(30071), utils.translate(30073), utils.translate(30074)):
            return False

    password = dialog.input(utils.translate(30076), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if not password:
        return False


    device_id = None
    if is_two_factor:
        # If Android Device available
        if dialog.yesno(utils.translate(30077), utils.translate(30078)):
            if not dialog.ok(utils.translate(30079), utils.translate(30081)):
                return False

            device_id = dialog.input(utils.translate(30084), type=xbmcgui.INPUT_ALPHANUM)
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
                        dev['carrier'].strip(' ') if 'carrier' in dev else '',
                        dev['model'].strip(' ')   if 'model'   in dev else '',
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
        except:
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

        addon.setSetting('username',  username)
        addon.setSetting('password',  password)
        addon.setSetting('authtoken', mobile.session._authtoken)

        if device_id == gmusicapi.Mobileclient.FROM_MAC_ADDRESS:
            mac_address = ''.join(re.findall('..', '%012x' % uuid.getnode()))
            addon.setSetting('device_id', mac_address)
        else:
            addon.setSetting('device_id', device_id)

        addon.setSetting('is_setup', 'true')

        utils.notify(utils.translate(30086), utils.translate(30087))

        return True
    else:
        # If re-run setup
        if dialog.yesno(utils.translate(30048), utils.translate(30085)):
            return setup(force=True)
        else:
            return False


##############
## PLAYBACK ##
##############
@mpr.url('^/play/track/$')
def play_track(track_id, station_id=None):
    cache = os.path.join(utils.get_cache_dir(['tracks']), track_id)
    if os.path.exists(cache):
        with open(cache, 'r') as f:
            track = json.loads(f.read())

    else:
        track = gmusic.get_track_info(store_track_id=track_id)

    item = listing.build_song_listitems([track])[0]
    item[1].setPath(gmusic.get_stream_url(song_id=track_id, quality=addon.getSetting('stream_quality')))

    xbmcplugin.setResolvedUrl(addon_handle, True, item[1])

    def _increment_playcount(track):
        try:
            wait_seconds = int(track['durationMillis']) / 3 / 1000
        except:
            # Just in case
            wait_seconds = 30

        wait_unitl   = time.time() + wait_seconds

        monitor = xbmc.Monitor()
        player  = xbmc.Player()

        while not monitor.abortRequested():
            if monitor.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

            # Check wheter or not the same track is still playing.
            # If not the user either stoped or skipped to the next/previous
            # on meaning we can exit
            if player.isPlayingAudio():
                if track_id != utils.get_current_track_id():
                    return

            if time.time() >= wait_unitl:
                break

        if not monitor.abortRequested():
            gmusic.increment_song_playcount(track_id)

    threading.Thread(target=_increment_playcount, args=(track,)).start()

    # If the current track is from a station and within the last five (5)
    # playlist tracks, we get a new set of tracks for this station and
    # add it to the playlist.
    if station_id:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        if playlist.getposition() >= (len(playlist) - 5):
            mpr.call(utils.build_url(url=url, paths=['queue', 'station'], queries={'station_id': station_id}, r_path=True, r_query=True))

@mpr.url('^/play/album/$')
def play_album(album_id):
    _play(['album'])
    if addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

@mpr.url('^/play/playlist/$')
def play_playlist(playlist_id=None, playlist_token=None):
    _play(['playlist'])
    if addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

@mpr.url('^/play/station/$')
def play_station(station_id=None, station_name=None, artist_id=None,
        album_id=None, genre_id=None, track_id=None, curated_station_id=None,
        playlist_token=None):
    # Shuffle and Repeat make no sense what so ever when starting a station
    utils.execute_jsonrpc('Player.SetShuffle',
        {'playerid': xbmc.PLAYLIST_MUSIC, 'shuffle' : False})
    utils.execute_jsonrpc('Player.SetRepeat',
        {'playerid': xbmc.PLAYLIST_MUSIC, 'repeat' : 'off'})

    _play(['station'])
    if addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

def _play(path):
    utils.execute_jsonrpc(
        method='Playlist.Clear',
        params={'playlistid': xbmc.PLAYLIST_MUSIC}
    )

    utils.execute_jsonrpc(
        method='Playlist.Add',
        params={'playlistid': xbmc.PLAYLIST_MUSIC,
            'item': {'directory': utils.build_url(url=url, paths=path, r_path=True)}}
    )

    utils.execute_jsonrpc(
        method='Player.Open',
        params={'item': {'playlistid': xbmc.PLAYLIST_MUSIC, 'position': 0}}
    )


#############
## QUEUING ##
#############
@mpr.url('^/queue/track/$')
def queue_track(track_id, play_next=False):
    listitem = listing.build_song_listitems([gmusic.get_track_info(track_id)])[0]


    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1
    if play_next:
        position = playlist.getposition() + 1

    playlist.add(url=listitem[0], listitem=listitem[1], index=position)

@mpr.url('^/queue/album/$')
def queue_album(album_id, play_next=False):
    _queue(['album'])

@mpr.url('^/queue/playlist/$')
def queue_playlist(playlist_id, play_next=False):
    _queue(['playlist'])

@mpr.url('^/queue/station/$')
def queue_station(station_id=None, station_name=None, artist_id=None,
        album_id=None, genre_id=None, track_id=None,
        curated_station_id=None, play_next=False):
    _queue(['station'])

def _queue(path, play_next=False):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1
    if play_next:
        position = playlist.getposition() + 1

    query = dict(urlparse.parse_qsl(urlparse.urlparse(url).query))
    if 'play_next' in query:
        del query['play_next']
        position = playlist.getposition() + 1

    utils.execute_jsonrpc(
        method='Playlist.Insert',
        params={'playlistid': xbmc.PLAYLIST_MUSIC, 'position': position, 'item': {'directory': utils.build_url(url=url, paths=path, queries=query, r_path=True, r_query=True)}}
    )


############
## SEARCH ##
############
@mpr.url('^/search/history/$')
def search_history():
    history = _get_search_history()

    if not history:
        search()

    # Add "New Search" to the list
    items = [(
        utils.build_url(url, ['search'], r_path=True, r_query=True),
        xbmcgui.ListItem(
            label=utils.translate(30053),
            iconImage=thumbs.IMG_SEARCH,
            thumbnailImage=thumbs.IMG_SEARCH
        ),
        True
    )]

    for hist in history:
        items.append((
            utils.build_url(url, ['search'], {'query': hist}, r_path=True, r_query=True),
            xbmcgui.ListItem(
                label=hist,
                iconImage=thumbs.IMG_SEARCH,
                thumbnailImage=thumbs.IMG_SEARCH
            ),
            True
        ))

    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)

@mpr.url('^/search/$')
def search(query=None):
    if not query:
        keyboard = xbmc.Keyboard()
        keyboard.doModal()

        if keyboard.isConfirmed() and keyboard.getText():
            query = keyboard.getText()
        else:
            # User canceled or used a empty search-string
            return

        history_file = os.path.join(_cache_dir,'search_history.json')
        history      = _get_search_history()
        # It was a new search so we add it to the history
        if query.lower() not in (hist.lower() for hist in history):
            history.insert(0, query)
            with open(history_file, 'w+') as f:
                # TODO: Make max history size configurable?
                f.write(json.dumps(history[:10], indent=2))

    result = _perform_search(query)

    if not result:
        # TODO: Notification that nothing was found
        return

    items = []
    if 'artist_hits' in result and len(result['artist_hits']) > 0:
        items.append((
            utils.build_url(url, ['artists'], r_query=True),
            xbmcgui.ListItem(
                label='%s (%s)' % (utils.translate(30022),
                    len(result['artist_hits'])),
                iconImage=thumbs.IMG_ARTIST,
                thumbnailImage=thumbs.IMG_ARTIST
            ),
            True
        ))

    if 'album_hits' in result and len(result['album_hits']) > 0:
        items.append((
            utils.build_url(url, ['albums'], r_query=True),
            xbmcgui.ListItem(
                label='%s (%s)' % (utils.translate(30023),
                    len(result['album_hits'])),
                iconImage=thumbs.IMG_ALBUM,
                thumbnailImage=thumbs.IMG_ALBUM
            ),
            True
        ))

    if 'playlist_hits' in result and len(result['playlist_hits']) > 0:
        items.append((
            utils.build_url(url, ['playlists'], r_query=True),
                xbmcgui.ListItem(
                    label='%s (%s)' % (utils.translate(30020),
                        len(result['playlist_hits'])),
                    iconImage=thumbs.IMG_PLAYLIST,
                    thumbnailImage=thumbs.IMG_PLAYLIST
                ),
                True
            ))

    if 'station_hits' in result and len(result['station_hits']) > 0:
        items.append((
            utils.build_url(url, ['stations'], r_query=True),
                xbmcgui.ListItem(
                    label='%s (%s)' % (utils.translate(30021),
                        len(result['station_hits'])),
                    iconImage=thumbs.IMG_STATION,
                    thumbnailImage=thumbs.IMG_STATION
                ),
                True
            ))

    if 'song_hits' in result and len(result['song_hits']) > 0:
        items.append((
            utils.build_url(url, ['songs'], r_query=True),
                xbmcgui.ListItem(
                    label='%s (%s)' % (utils.translate(30024),
                        len(result['song_hits'])),
                    iconImage=thumbs.IMG_TRACK,
                    thumbnailImage=thumbs.IMG_TRACK
                ),
                True
        ))

    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)

@mpr.url('^/search/artists/$')
def search_artists(query=None):
    result = None
    if query:
        result = _perform_search(query)

    else:
        with open(os.path.join(_cache_dir, 'search_results.json'), 'r') as f:
            try:
                result = json.loads(f.read())
            except ValueError:
                pass

    if result:
        items = listing.build_artist_listitems(result['artist_hits'])
        listing.list_artists(items)

@mpr.url('^/search/albums/$')
def search_albums(query=None):
    result = None
    if query:
        result = _perform_search(query)

    else:
        with open(os.path.join(_cache_dir, 'search_results.json'), 'r') as f:
            try:
                result = json.loads(f.read())
            except ValueError:
                pass

    if result:
        items = listing.build_album_listitems(result['album_hits'])
        listing.list_albums(items)

@mpr.url('^/search/playlists/$')
def search_playlists(query=None):
    result = None
    if query:
        result = _perform_search(query)

    else:
        with open(os.path.join(_cache_dir, 'search_results.json'), 'r') as f:
            try:
                result = json.loads(f.read())
            except ValueError:
                pass

    if result:
        items = listing.build_playlist_listitems(result['playlist_hits'])
        listing.list_playlists(items)

@mpr.url('^/search/stations/$')
def search_stations(query=None):
    result = None
    if query:
        result = _perform_search(query)

    else:
        with open(os.path.join(_cache_dir, 'search_results.json'), 'r') as f:
            try:
                result = json.loads(f.read())
            except ValueError:
                pass

    if result:
        items = listing.build_station_listitems(result['station_hits'])
        listing.list_stations(items)

@mpr.url('^/search/songs/$')
def search_songs(query=None):
    result = None
    if query:
        result = _perform_search(query)

    else:
        with open(os.path.join(_cache_dir, 'search_results.json'), 'r') as f:
            try:
                result = json.loads(f.read())
            except ValueError:
                pass

    if result:
        items = listing.build_song_listitems(result['song_hits'])
        listing.list_songs(items)

def _get_search_history():
    history_file = os.path.join(_cache_dir,'search_history.json')

    history = []
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try:
                history = json.loads(f.read())
            except ValueError:
                pass

    return history

def _perform_search(query):
    result = gmusic.search(query)
    if not result:
        return None

    with open(os.path.join(_cache_dir, 'search_results.json'), 'w+') as f:
        f.write(json.dumps(result))

    return result


###################
## MISCELLANEOUS ##
###################
@mpr.url('^/my-library/update/$')
def my_library_update():
    utils.notify(utils.translate(30030), utils.translate(30043))

    gmusic.get_my_library_songs(from_cache=False)
    gmusic.get_my_library_artists(from_cache=False)
    gmusic.get_my_library_albums(from_cache=False)

    utils.notify(utils.translate(30030), utils.translate(30044))

    xbmc.executebuiltin('Container.Refresh')

@mpr.url('^/my-library/add/$')
def my_library_add(album_id=None, track_id=None):
    if track_id:
        gmusic.add_aa_track(aa_song_id=track_id)
    elif album_id:
        album = gmusic.get_album_info(album_id=album_id, include_tracks=True)
        for track in album['tracks']:
            if 'storeId' in track:
                gmusic.add_aa_track(aa_song_id=track['storeId'])

@mpr.url('^/my-library/remove/$')
def my_library_remove(album_id=None, library_song_id=None):
    if not album_id and not library_song_id:
        return

    if not xbmcgui.Dialog().yesno(heading=utils.translate(30061), line1=utils.translate(30063)):
        return

    if album_id:
        gmusic.delete_album(album_id)

    elif library_song_id:
        gmusic.delete_songs(library_song_id)

    if xbmcgui.Dialog().yesno(heading=utils.translate(30030), line1=utils.translate(30065)):
        mpr.call(utils.build_url(url=url, paths=['my-library', 'update'], r_path=True, r_query=True))

@mpr.url('^/my-library/playlist/add/$')
def my_library_playlist_add(playlist_id=None, album_id=None, track_id=None):
    # In case no playlist_id is specified we guide the user through
    # the process of selecting one.
    # He will also have the ability to create a new one
    if not playlist_id:
        action_dialog = xbmcgui.Dialog()
        playlists = gmusic.get_user_playlists()

        playlist_names = []
        playlist_ids   = []
        for playlist in playlists:
            if playlist['type'] != 'USER_GENERATED':
                continue

            playlist_names.append(playlist['name'])
            playlist_ids.append(playlist['id'])

        playlist_names.insert(0, utils.translate(30052))
        selection = action_dialog.select(utils.translate(30020), playlist_names, 0)
        if selection == -1:
            return

        if selection == 0:
            keyboard = xbmc.Keyboard()
            keyboard.doModal()

            if keyboard.isConfirmed() and keyboard.getText():
                playlist_id = gmusic.create_playlist(name=keyboard.getText())
        else:
            playlist_id = playlist_ids[selection-1]

    if playlist_id:
        if track_id:
            gmusic.add_songs_to_playlist(playlist_id=playlist_id, song_ids=track_id)
        elif album_id:
            album = gmusic.get_album_info(album_id=album_id, include_tracks=True)

            track_ids = []
            for track in album['tracks']:
                if 'storeId' in track:
                    track_ids.append(track['storeId'])

            gmusic.add_songs_to_playlist(playlist_id=playlist_id, song_ids=track_ids)

@mpr.url('^/my-library/playlist/remove/$')
def my_library_playlist_remove(entry_id):
    if xbmcgui.Dialog().yesno(heading=utils.translate(30062), line1=utils.translate(30064)):
        gmusic.remove_entries_from_playlist([entry_id])

        xbmc.executebuiltin('Container.Refresh')

@mpr.url('^/my-library/playlist/delete/$')
def my_library_playlist_delete(playlist_id):
    if xbmcgui.Dialog().yesno(heading=utils.translate(30068), line1=utils.translate(30069)):
        gmusic.delete_playlist(playlist_id)

        xbmc.executebuiltin('Container.Refresh')

@mpr.url('^/rate/$')
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

    song = gmusic.get_track_info(track_id)

    if song:
        if selection == 0:
            song['rating'] = '5'

        elif selection == 1:
            song['rating'] = '0'

        elif selection == 2:
            song['rating'] = '1'

        song['lastRatingChangeTimestamp'] = int(round(time.time() * 1000000))
        gmusic.change_song_metadata(song)

@mpr.url('^/clear/cache/$')
def clear_cache():
    if os.path.exists(_cache_dir):
        shutil.rmtree(_cache_dir)
    utils.notify(utils.translate(30094), '', display_time=1000)

@mpr.url('^/clear/search-history/$')
def clear_search_history():
    history_file = os.path.join(_cache_dir,'search_history.json')
    if os.path.exists(history_file):
        os.remove(history_file)
    utils.notify(utils.translate(30095), '', display_time=1000)
