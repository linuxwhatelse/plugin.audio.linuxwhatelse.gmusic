import os
import json
import shutil
import time
import urlparse

import xbmc
import xbmcgui
import xbmcplugin
from xbmcaddon import Addon

import mapper

import utils
import browse
import resources
from gmusic import GMusic

# Variables will be set from "default.py"
url          = None
addon_handle = None

_addon     = Addon()
_cache_dir = utils.get_cache_dir()
gmusic     = GMusic(debug_logging=False, validate=True, verify_ssl=True)

##############
## PLAYBACK ##
##############
@mapper.url('^/play/track/$')
def play_track(track_id, station_id):
    gmusic.login()

    cache = os.path.join(utils.get_cache_dir(sub_dir=['tracks']), track_id)
    if os.path.exists(cache):
        with open(cache, 'r') as f:
            track = json.loads(f.read())

    else:
        track = gmusic.get_track_info(store_track_id=track_id)

    item = browse.build_song_listitems([track])[0]
    item[1].setPath(gmusic.get_stream_url(song_id=track_id, quality=_addon.getSetting('stream_quality')))

    xbmcplugin.setResolvedUrl(addon_handle, True, item[1])
    
    gmusic.increment_song_playcount(track_id)

    # If the current track is from a station and within the last five (5)
    # playlist tracks, we get a new set of tracks for this station and
    # add it to the playlist.
    if station_id:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        if playlist.getposition() >= (len(playlist) - 5):
            mapper.call(mapper.build_url(url=url, paths=['queue', 'station'], queries={'station_id': station_id}, overwrite_path=True, overwrite_query=True))

@mapper.url('^/play/album/$')
def play_album(album_id):
    _play(['album'])
    if _addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

@mapper.url('^/play/playlist/$')
def play_playlist(playlist_id, shared_token):
    _play(['playlist'])
    if _addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

@mapper.url('^/play/station/$')
def play_station(station_id, station_name, artist_id, album_id, genre_id, track_id, curated_station_id):
    _play(['station'])
    if _addon.getSetting('auto_fullscreen') == 'true':
        utils.execute_jsonrpc('GUI.SetFullscreen', {'fullscreen':True})

def _play(path):
    utils.execute_jsonrpc(
        method='Playlist.Clear',
        params={'playlistid': xbmc.PLAYLIST_MUSIC}
    )

    utils.execute_jsonrpc(
        method='Playlist.Add',
        params={'playlistid': xbmc.PLAYLIST_MUSIC, 'item': {'directory': mapper.build_url(url=url, paths=path, overwrite_path=True)}}
    )

    utils.execute_jsonrpc(
        method='Player.Open',
        params={'item': {'playlistid': xbmc.PLAYLIST_MUSIC, 'position': 0}}
    )


#############
## QUEUING ##
#############
@mapper.url('^/queue/track/$')
def queue_track(track_id, play_next=False):
    gmusic.login()

    listitem = browse.build_song_listitems([gmusic.get_track_info(track_id)])[0]


    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1
    if play_next:
        position = playlist.getposition() + 1

    playlist.add(url=listitem[0], listitem=listitem[1], index=position)

@mapper.url('^/queue/album/$')
def queue_album(album_id, play_next=False):
    _queue(['album'])
    
@mapper.url('^/queue/playlist/$')
def queue_playlist(playlist_id, play_next=False):
    _queue(['playlist'])

@mapper.url('^/queue/station/$')
def queue_station(station_id, station_name, artist_id, album_id, genre_id, track_id, curated_station_id, play_next=False):
    _queue(['station'])

def _queue(path, play_next=False):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    position = len(playlist) + 1
    if play_next:
        position = playlist.getposition() + 1

    query = dict(urlparse.parse_qsl(urlparse.urlparse(url).query))
    if 'play_next' in query:
        del query['play_next']
        position = playlist.getposition()+1

    utils.execute_jsonrpc(
        method='Playlist.Insert',
        params={'playlistid': xbmc.PLAYLIST_MUSIC, 'position': position, 'item': {'directory': mapper.build_url(url=url, paths=path, queries=query, overwrite_path=True, overwrite_query=True)}}
    )


############
## SEARCH ##
############
@mapper.url('^/search/$')
def search(query):
    if not query:
        history_file = os.path.join(_cache_dir,'search_history.json')
    
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                try:
                    history = json.loads(f.read())
                except ValueError:
                    pass
    
    
        query = None
        if history:
            history.insert(0, utils.translate(30053, _addon))
            diag = xbmcgui.Dialog()
    
            selection = diag.select(utils.translate(30019, _addon), history, 0)
    
            # User canceled the operation
            if selection == -1:
                return
    
            # User selected "New Search"
            elif selection == 0:
                # Now we have to remove the "New search" entry again
                history.pop(0)
    
            # User selected a history entrie and NOT "New Search"
            elif selection > 0:
                # We still have to remove the "New search" entry
                history.pop(0)
                # This also means that :selection: = :selection: - 1
                selection -= 1        
    
                query = history[selection]

    
    
        # At this point the user didn't cancel but also didn't select
        # a actuall history entry so we know he either selected "New Search"
        # or a history didn't exist at this point
        if not query:
            keyboard = xbmc.Keyboard()
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                query = keyboard.getText()
            else:
                # User canceled or used a empty search-string
                return

            # It was a new search so we add it to the history
            if query not in history:
                history.insert(0, query)
                with open(history_file, 'w+') as f:
                    # ToDo: Make max history size configurable?
                    f.write(json.dumps(history[:10], indent=2))

        # We finally got a query and therefore call ourself with it again
        mapper.call(mapper.build_url(url=url, queries={'query': query}))

    else:
        result = _perform_search(query)

        if not result:
            return

        items = []
        if 'artist_hits' in result and len(result['artist_hits']) > 0:
            items.append(
                ( mapper.build_url(url, ['artists']), xbmcgui.ListItem(label='%s (%s)' % (utils.translate(30022, _addon), \
                    len(result['artist_hits'])), iconImage=resources.IMG_ARTIST, thumbnailImage=resources.IMG_ARTIST), True )
            )
        if 'album_hits' in result and len(result['album_hits']) > 0:
            items.append(
                ( mapper.build_url(url, ['albums']),  xbmcgui.ListItem(label='%s (%s)' % (utils.translate(30023, _addon), \
                    len(result['album_hits'])), iconImage=resources.IMG_ALBUM, thumbnailImage=resources.IMG_ALBUM), True )
            )

        if 'playlist_hits' in result and len(result['playlist_hits']) > 0:
            items.append(
                ( mapper.build_url(url, ['playlists']),   xbmcgui.ListItem(label='%s (%s)' % (utils.translate(30020, _addon), \
                    len(result['playlist_hits'])), iconImage=resources.IMG_PLAYLIST, thumbnailImage=resources.IMG_PLAYLIST), True )
            )

        if 'song_hits' in result and len(result['song_hits']) > 0:
            items.append(
                ( mapper.build_url(url, ['songs']),   xbmcgui.ListItem(label='%s (%s)' % (utils.translate(30024, _addon), \
                    len(result['song_hits'])), iconImage=resources.IMG_TRACK, thumbnailImage=resources.IMG_TRACK), True )
            )

        for item in items:
            item[1].addContextMenuItems([],True)

        browse.list_items(items)

@mapper.url('^/search/artists/$')
def search_artists(query):
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
        items = browse.build_artist_listitems(result['artist_hits'])
        browse.list_artists(items)

@mapper.url('^/search/albums/$')
def search_artists(query):
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
        items = browse.build_album_listitems(result['album_hits'])
        browse.list_albums(items)

@mapper.url('^/search/playlists/$')
def search_artists(query):
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
        items = browse.build_playlist_listitems(result['playlist_hits'])
        browse.list_playlists(items)

@mapper.url('^/search/songs/$')
def search_artists(query):
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
        items = browse.build_song_listitems(result['song_hits'])
        browse.list_songs(items)

def _perform_search(query):
    gmusic.login()

    result = gmusic.search_all_access(query)
    if not result:
        return None

    with open(os.path.join(_cache_dir, 'search_results.json'), 'w+') as f:
        f.write(json.dumps(result, indent=2))

    return result


###################
## MISCELLANEOUS ##
###################
@mapper.url('^/my-library/update/$')
def my_library_update():
    utils.notify(utils.translate(30030, _addon), utils.translate(30043, _addon))

    gmusic.login()

    gmusic.get_my_library_songs(from_cache=False)
    gmusic.get_my_library_artists(from_cache=False)
    gmusic.get_my_library_albums(from_cache=False)

    utils.notify(utils.translate(30030, _addon), utils.translate(30044, _addon))

    xbmc.executebuiltin('Container.Refresh')

@mapper.url('^/my-library/add/$')
def my_library_add(album_id, track_id):
    gmusic.login()
    if track_id:
        gmusic.add_aa_track(aa_song_id=track_id)
    elif album_id:
        album = gmusic.get_album_info(album_id=album_id, include_tracks=True)
        for track in album['tracks']:
            if 'storeId' in track:
                gmusic.add_aa_track(aa_song_id=track['storeId'])

@mapper.url('^/my-library/remove/$')
def my_library_remove(album_id, library_song_id):
    if not album_id and not library_song_id:
        return

    if not xbmcgui.Dialog().yesno(heading=utils.translate(30061), line1=utils.translate(30063)):
        return

    gmusic.login()

    if album_id:
        gmusic.delete_album(album_id)

    elif library_song_id:
        gmusic.delete_songs(library_song_id)

    if xbmcgui.Dialog().yesno(heading=utils.translate(30030), line1=utils.translate(30065)):
        mapper.call(mapper.build_url(url=url, paths=['my-library', 'update'], overwrite_path=True, overwrite_query=True))

@mapper.url('^/my-library/playlist/add/$')
def my_library_playlist_add(playlist_id, album_id, track_id):
    gmusic.login()

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

        playlist_names.insert(0, utils.translate(30052, _addon))
        selection = action_dialog.select(utils.translate(30020, _addon), playlist_names, 0)
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

@mapper.url('^/my-library/playlist/remove/$')
def my_library_playlist_remove(entry_id):
    if entry_id:
        if xbmcgui.Dialog().yesno(heading=utils.translate(30062), line1=utils.translate(30064)):
            gmusic.login()

            gmusic.remove_entries_from_playlist([entry_id])

            xbmc.executebuiltin('Container.Refresh')

@mapper.url('^/my-library/playlist/delete/$')
def my_library_playlist_delete(playlist_id):
    if playlist_id:
        if xbmcgui.Dialog().yesno(heading=utils.translate(30068), line1=utils.translate(30069)):
            gmusic.login()

            gmusic.delete_playlist(playlist_id)

            xbmc.executebuiltin('Container.Refresh')

@mapper.url('^/rate/$')
def rate(track_id):

    rating = [
        utils.translate(30027, _addon),  # Thumbs up
        utils.translate(30028, _addon),  # No Thumbs
        utils.translate(30029, _addon),  # Thumbs down
    ]

    dialog = xbmcgui.Dialog()    
    selection = dialog.select(utils.translate(30041, _addon), rating, 0)

    if selection == -1:
        return

    gmusic.login()
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

@mapper.url('^/clear/cache/$')
def clear_cache():
    if os.path.exists(_cache_dir):
        shutil.rmtree(_cache_dir)

@mapper.url('^/clear/search-history/$')
def clear_search_history():
    history_file = os.path.join(_cache_dir,'search_history.json')
    if os.path.exists(history_file):
        os.remove(history_file)