import os
import json
import locale

import xbmc
import xbmcgui
import xbmcplugin
from xbmcaddon import Addon

import mapper

import utils
import resources
from gmusic import GMusic

# Variables will be set from "default.py"
url          = None
addon_handle = None

_addon       = Addon()
_cache_dir   = utils.get_cache_dir()
_locale_code = locale.getdefaultlocale()[0]
gmusic       = GMusic(debug_logging=False, validate=True, verify_ssl=True)


#######################
## FOLDER: MAIN MENU ##
#######################
@mapper.url('^/browse/$')
def main_menu():
    items = [
        # URL , ListItem, isFolder
        ( mapper.build_url(url, ['listen-now']),       xbmcgui.ListItem(label=utils.translate(30014, _addon), iconImage=resources.IMG_HEADPHONES, thumbnailImage=resources.IMG_HEADPHONES), True ),
        ( mapper.build_url(url, ['top-charts']),       xbmcgui.ListItem(label=utils.translate(30015, _addon), iconImage=resources.IMG_STAR,       thumbnailImage=resources.IMG_STAR),       True ),
        ( mapper.build_url(url, ['new-releases']),     xbmcgui.ListItem(label=utils.translate(30016, _addon), iconImage=resources.IMG_RELEASES,   thumbnailImage=resources.IMG_RELEASES),   True ),
        ( mapper.build_url(url, ['my-library']),       xbmcgui.ListItem(label=utils.translate(30017, _addon), iconImage=resources.IMG_LIBRARY,    thumbnailImage=resources.IMG_LIBRARY),    True ),
        ( mapper.build_url(url, ['browse-stations']),  xbmcgui.ListItem(label=utils.translate(30018, _addon), iconImage=resources.IMG_STATION,    thumbnailImage=resources.IMG_STATION),    True ),
        ( mapper.build_url(url, ['search'], {}, True), xbmcgui.ListItem(label=utils.translate(30019, _addon), iconImage=resources.IMG_SEARCH,     thumbnailImage=resources.IMG_SEARCH),     True ),
    ]

    addon_settings = (utils.translate(30049, _addon), 'Addon.OpenSettings(%s)' % _addon.getAddonInfo('id'))

    items[0][1].addContextMenuItems([addon_settings],True)
    items[1][1].addContextMenuItems([addon_settings],True)
    items[2][1].addContextMenuItems([addon_settings],True)
    items[3][1].addContextMenuItems([(utils.translate(30030, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'update'], overwrite_path=True)), addon_settings],True)
    items[4][1].addContextMenuItems([addon_settings],True)
    items[5][1].addContextMenuItems([addon_settings],True)

    list_items(items)


########################
## FOLDER: LISTEN NOW ##
########################
@mapper.url('^/browse/listen-now/$')
def listen_now():
    gmusic.login()

    items = [
        # URL , ListItem, isFolder
        ( mapper.build_url(url=url, paths=['play', 'station'], queries={'station_id': 'IFL'}, overwrite_path=True, \
            overwrite_query=True),              xbmcgui.ListItem(label=utils.translate(30045, _addon), iconImage=resources.IMG_IFL,      thumbnailImage=resources.IMG_IFL),      True ),
        ( mapper.build_url(url, ['albums']),    xbmcgui.ListItem(label=utils.translate(30023, _addon), iconImage=resources.IMG_ALBUM,    thumbnailImage=resources.IMG_ALBUM),    True ),
        ( mapper.build_url(url, ['stations']),  xbmcgui.ListItem(label=utils.translate(30021, _addon), iconImage=resources.IMG_STATION,  thumbnailImage=resources.IMG_STATION),  True ),
        ( mapper.build_url(url, ['playlists']), xbmcgui.ListItem(label=utils.translate(30020, _addon), iconImage=resources.IMG_PLAYLIST, thumbnailImage=resources.IMG_PLAYLIST), True ),

    ]

    # Get current situation and add it to the list
    situations = gmusic.get_situations(_locale_code)

    # We save the current response so we don't have to fetch it again when the users selects it
    with open(os.path.join(_cache_dir, 'situations.json'), 'w+') as f:
        f.write(json.dumps(situations, indent=2))

    items.insert(1, ( mapper.build_url(url, ['situations']), xbmcgui.ListItem(label=situations['primaryHeader'], iconImage=resources.IMG_ALBUM, thumbnailImage=resources.IMG_ALBUM),    True ))

    for item in items:
        item[1].addContextMenuItems([],True)

    # Add "Play All" to I'm feeling lucky context menu
    items[0][1].addContextMenuItems(
        [(utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['play', 'station'], queries={'station_id': 'IFL'}, overwrite_path=True, overwrite_query=True))], True
    )

    list_items(items)

@mapper.url('^/browse/listen-now/situations/$')
def listen_now_situations():
    situations = None
    with open(os.path.join(_cache_dir, 'situations.json'), 'r') as f:
        situations = json.loads(f.read())

    if situations:
        items = build_situation_listitems(situations['situations'])
        list_situations(items)

@mapper.url('^/browse/listen-now/situation/$')
def listen_now_situation(situation_id):
    situations = None
    with open(os.path.join(_cache_dir, 'situations.json'), 'r') as f:
        situations = json.loads(f.read())

    if not situations:
        list_items([])

    for situation in situations['situations']:
        if situation_id != situation['id']:
            # In some cases, a situation can have situations as childs (not stations),
            # therefore we have to check if one of the sub-situations matches our id
            if 'situations' in situation:
                for situation in situation['situations']:
                    if situation_id != situation['id']:
                        continue
            else:
                continue

        if 'situations' in situation:
            list_situations(build_situation_listitems(situation['situations']))

        elif 'stations' in situation:
            stations = situation['stations']
            new_stations = []
            for station in stations:
                art = ''
                for img_urls in station['compositeArtRefs']:
                    if int(img_urls['aspectRatio']) == 1:
                        art = img_urls['url']
                        break

                tmp_station = {
                    'name': station['name'],
                    'imageUrls': [
                        {'url': art}
                    ],
                    'curatedStationId': station['seed']['curatedStationId'],
                    'description': station['description']
                }

                new_stations.append(tmp_station)
            list_stations(build_station_listitems(new_stations))

@mapper.url('^/browse/listen-now/albums/$')
def listen_now_albums():
    gmusic.login()

    listen_now = gmusic.get_listen_now()

    albums   = []
    for item in listen_now:
        # 1 = album
        # 2 = playlist
        # 3 = radio
        if item['type'] != '1':
            continue

        album = item['album']
        if not 'id' in album and not 'metajamCompactKey' in album['id']:
            continue

        albums.append({
            'albumId'     : album['id']['metajamCompactKey'],
            'name'        : album['title']            if 'title'       in album else '',
            'albumArtist' : album['artist_name']      if 'artist_name' in album else '',
            'albumArtRef' :  item['images'][0]['url'] if 'images'      in item and len(item['images']) > 0 else '',
        })

    items = build_album_listitems(albums)
    list_albums(items)

@mapper.url('^/browse/listen-now/stations/$')
def listen_now_stations():
    gmusic.login()

    listen_now = gmusic.get_listen_now()

    new_stations=[]
    for item in listen_now:
        # 1 = album
        # 2 = playlist
        # 3 = radio
        if item['type'] != '3':
            continue
        
        art = None
        if 'compositeArtRefs' in item:
            for artref in item['compositeArtRefs']:
                if artref['aspectRatio'] == '1':
                    art = artref['url']
                    break


        station = item['radio_station']

        tmp_station = {
                'name': station['title'],
                'imageUrls': [
                    {'url': art}
                ],
            }

        seed = station['id']['seeds'][0]
        if 'trackId' in seed:
            tmp_station['trackId'] = seed['trackId']

        elif 'artistId' in seed:
            tmp_station['artistId'] = seed['artistId']

        elif 'albumId' in seed:
            tmp_station['albumId'] = seed['albumId']

        elif 'genreId' in seed:
            tmp_station['genreId'] = seed['genreId']

        new_stations.append(tmp_station)

    items = build_station_listitems(new_stations)
    list_albums(items)

@mapper.url('^/browse/listen-now/playlists/$')
def listen_now_playlists():
    gmusic.login()

    listen_now = gmusic.get_listen_now()

    playlists   = []
    for item in listen_now:
        # 1 = album
        # 2 = playlist
        # 3 = radio
        if item['type'] != '2':
            continue

        if 'playlist' not in item:
            continue

        playlist = item['playlist']

        playlists.append (
            {
                'name':   playlist['title'],
                'images': item['images'],
                'id':     playlist['id'],
            }
        )
    
    items = build_playlist_listitems(playlists)
    list_playlists(items)


########################
## FOLDER: TOP CHARTS ##
########################
@mapper.url('^/browse/top-charts/$')
def top_charts():
    items = [
        ( mapper.build_url(url, ['songs']),  xbmcgui.ListItem(label=utils.translate(30024, _addon), iconImage=resources.IMG_TRACK, thumbnailImage=resources.IMG_TRACK), True ),
        ( mapper.build_url(url, ['albums']), xbmcgui.ListItem(label=utils.translate(30023, _addon), iconImage=resources.IMG_ALBUM, thumbnailImage=resources.IMG_ALBUM), True ),
    ]
    for item in items:
        item[1].addContextMenuItems([],True)

    list_items(items)

@mapper.url('^/browse/top-charts/songs/$')
def top_charts_songs():
    gmusic.login()

    items = build_song_listitems(gmusic.get_top_chart()['tracks'])
    list_songs(items)

@mapper.url('^/browse/top-charts/albums/$')
def top_charts_albums():
    gmusic.login()

    items = build_album_listitems(gmusic.get_top_chart()['albums'])
    list_albums(items)


##########################
## FOLDER: NEW RELEASES ##
##########################
@mapper.url('^/browse/new-releases/$')
def new_releases():
    gmusic.login()

    items = build_album_listitems(gmusic.get_new_releases())
    list_albums(items)


########################
## FOLDER: MY LIBRARY ##
########################
@mapper.url('^/browse/my-library/$')
def my_library():
    items = [
        # URL , ListItem, isFolder
        ( mapper.build_url(url, ['playlists']), xbmcgui.ListItem(label=utils.translate(30020, _addon), iconImage=resources.IMG_PLAYLIST, thumbnailImage=resources.IMG_PLAYLIST), True ),
        ( mapper.build_url(url, ['stations']),  xbmcgui.ListItem(label=utils.translate(30021, _addon), iconImage=resources.IMG_STATION,  thumbnailImage=resources.IMG_STATION),  True ),
        ( mapper.build_url(url, ['artists']),   xbmcgui.ListItem(label=utils.translate(30022, _addon), iconImage=resources.IMG_ARTIST,   thumbnailImage=resources.IMG_ARTIST),   True ),
        ( mapper.build_url(url, ['albums']),    xbmcgui.ListItem(label=utils.translate(30023, _addon), iconImage=resources.IMG_ALBUM,    thumbnailImage=resources.IMG_ALBUM),    True ),
        ( mapper.build_url(url, ['songs']),     xbmcgui.ListItem(label=utils.translate(30024, _addon), iconImage=resources.IMG_TRACK,    thumbnailImage=resources.IMG_TRACK),    True ),
        ( mapper.build_url(url, ['genres']),    xbmcgui.ListItem(label=utils.translate(30025, _addon), iconImage=resources.IMG_GENRE,    thumbnailImage=resources.IMG_GENRE),    True ),
    ]

    for item in items:
        item[1].addContextMenuItems([],True)

    list_items(items)

@mapper.url('^/browse/my-library/playlists/$')
def my_library_playlists():
    gmusic.login()

    # Auto playlists
    items = [
        ( mapper.build_url(url=url, paths=['browse', 'my-library', 'playlist'], queries={'playlist_id': 'thumbsup'}, overwrite_path=True, overwrite_query=True), \
            xbmcgui.ListItem(label=utils.translate(30027, _addon), iconImage=resources.IMG_THUMB_UP, thumbnailImage=resources.IMG_THUMB_UP), True ),

        ( mapper.build_url(url=url, paths=['browse', 'my-library', 'playlist'], queries={'playlist_id': 'lastadded'}, overwrite_path=True, overwrite_query=True),\
            xbmcgui.ListItem(label=utils.translate(30026, _addon), iconImage=resources.IMG_CLOCK, thumbnailImage=resources.IMG_CLOCK), True ),
    ]

    for item, playlist_id in zip(items, ['thumbsup', 'lastadded']):
        item[1].addContextMenuItems(
            items=[
                (utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url, ['play', 'playlist'], {'playlist_id': playlist_id}, True, True))
            ],
            replaceItems=True
        )


    # User playlists
    items += build_playlist_listitems(gmusic.get_user_playlists())

    list_playlists(items)

@mapper.url('^/browse/my-library/playlist/$')
def my_library_playlist(playlist_id, allow_view_overwrite=True):
    if playlist_id:
        gmusic.login()

        my_library = False
        my_library_playlist = False

        items = []
        if playlist_id == 'thumbsup':
            items = gmusic.get_promoted_songs()

        elif playlist_id == 'lastadded':
            items = gmusic.get_user_lastadded()
            my_library = True

        else:
            playlist = gmusic.get_user_playlist(playlist_id)

            if playlist and 'tracks' in playlist:
                items = playlist['tracks']

            my_library_playlist = True

        list_songs(build_song_listitems(tracks=items, my_library=my_library, my_library_playlist=my_library_playlist), allow_view_overwrite)

@mapper.url('^/browse/my-library/stations/$')
def my_library_stations():
    gmusic.login()

    stations = gmusic.get_all_stations()
    stations = sorted(stations, key=lambda k: k['lastModifiedTimestamp'], reverse=True)
    items = build_station_listitems(stations)
    list_stations(items)

@mapper.url('^/browse/my-library/artists/$')
def my_library_artists():
    gmusic.login()

    items = build_artist_listitems(gmusic.get_my_library_artists(), True)
    list_artists(items)

@mapper.url('^/browse/my-library/artist/$')
def my_library_artist(artist_id):
    if artist_id:
        gmusic.login()

        items = [
            ( mapper.build_url(url=url, paths=['browse', 'artist', 'top-songs'],       overwrite_path=True), xbmcgui.ListItem(label=utils.translate(30066, _addon), iconImage=resources.IMG_STAR,   thumbnailImage=resources.IMG_STAR), True ),
            ( mapper.build_url(url=url, paths=['browse', 'artist', 'related-artists'], overwrite_path=True), xbmcgui.ListItem(label=utils.translate(30067, _addon), iconImage=resources.IMG_ARTIST, thumbnailImage=resources.IMG_ARTIST),     True ),
        ]

        items += build_album_listitems(gmusic.get_user_artist_albums(artist_id=artist_id), True)
        list_albums(items)

@mapper.url('^/browse/my-library/albums/$')
def my_library_albums():
    gmusic.login()

    items = build_album_listitems(gmusic.get_my_library_albums(), True)
    list_albums(items)

@mapper.url('^/browse/my-library/album/$')
def my_library_album(album_id):
    if album_id:
        gmusic.login()

        items = build_song_listitems(tracks=gmusic.get_user_album_songs(album_id=album_id), my_library=True)
        list_songs(items)

@mapper.url('^/browse/my-library/songs/$')
def my_library_songs():
    gmusic.login()

    list_songs(build_song_listitems(tracks=gmusic.get_my_library_songs(), my_library=True))

@mapper.url('^/browse/my-library/genres/$')
def my_library_genres():
    gmusic.login()

    genres = gmusic.get_my_library_genres()

    items=[]
    for genre in genres:
        if 'name' not in genre:
            continue

        genre_name = genre['name']
        genre_art  = genre['image'] if 'image' in genre else ''

        items.append((
                mapper.build_url(url=url, paths=['browse', 'my-library', 'genre'], \
                    queries={'genre': genre['name']}, overwrite_path=True, overwrite_query=True),
                xbmcgui.ListItem(
                    label           = genre_name,
                    iconImage       = genre_art,
                    thumbnailImage  = genre_art,
                ),
            True
        ))

    list_items(items)

@mapper.url('^/browse/my-library/genre/$')
def my_library_genre(genre):
    if genre:
        gmusic.login()

        list_albums(build_album_listitems(gmusic.get_user_genre_albums(genre=genre), True))


#############################
## FOLDER: BROWSE STATIONS ##
#############################
@mapper.url('^/browse/browse-stations/$')
def browse_stations():
    gmusic.login()

    categories = gmusic.get_station_categories()
    with open(os.path.join(_cache_dir,'categories.json'), 'w+') as f:
        f.write(json.dumps(categories, indent=4))

    items = []
    for category in categories:
        items.append(
            ( mapper.build_url(url=url, paths=['browse', 'browse-stations', 'categories'], \
                queries={'category_id': category['id']}, overwrite_path=True, overwrite_query=True), \
                xbmcgui.ListItem(label=category['display_name'], iconImage=resources.IMG_STATION, thumbnailImage=resources.IMG_STATION), True )
        )

    for item in items:
        item[1].addContextMenuItems([], True)

    list_items(items)

@mapper.url('^/browse/browse-stations/categories/$')
def browse_stations_categories(category_id):
    gmusic.login()

    categories = None

    categories_cache = os.path.join(_cache_dir,'categories.json')

    if os.path.exists(categories_cache):
        with open(categories_cache, 'r') as f:
            categories = json.loads(f.read())
    else:
        categories = gmusic.get_station_categories()

    if categories:
        items = []
        for category in categories:
            if category['id'] != category_id:
                continue

            subcategories = category['subcategories']
            for sub in subcategories:
                items.append(
                    ( mapper.build_url(url=url, paths=['browse', 'browse-stations', 'subcategories'], \
                        queries={'subcategory_id': sub['id']}, overwrite_path=True, overwrite_query=True), \
                        xbmcgui.ListItem(label=sub['display_name'], iconImage=resources.IMG_STATION, thumbnailImage=resources.IMG_STATION), True )
                )

        for item in items:
            item[1].addContextMenuItems([], True)

    list_items(items)

@mapper.url('^/browse/browse-stations/subcategories/$')
def browse_stations_subcategories(subcategory_id):
    gmusic.login()

    stations = gmusic.get_stations(station_subcategory_id=subcategory_id, location_code=_locale_code)

    new_stations=[]
    for station in stations:
        
        for artref in station['compositeArtRefs']:
            if artref['aspectRatio'] == '1':
                break

        new_stations.append(
            {
                'name': station['name'],
                'imageUrls': [
                    {'url': artref['url']}
                ],
                'curatedStationId': station['seed']['curatedStationId']
            }
        )

    items = build_station_listitems(new_stations)
    list_items(items)

@mapper.url('^/browse/browse-stations/station/$')
def browse_stations_subcategories(station_name, curated_station_id):
    if station_name:
        gmusic.login()
        station_id = gmusic.create_station(name=station_name, curated_station_id=curated_station_id)

        if not station_id:
            utils.notify(utils.translate(30050, _addon), utils.translate(30051, _addon))
            return

        items = build_song_listitems(gmusic.get_station_tracks(station_id=station_id, num_tracks=25))
        list_songs(items)


#####################
## FOLDER: DYNAMIC ##
#####################
@mapper.url('^/browse/artist/$', {'allow_view_overwrite': bool})
def artist(artist_id, allow_view_overwrite=True):
    if artist_id:
        gmusic.login()

        items = [
            ( mapper.build_url(url=url, paths=['browse', 'artist', 'top-songs'],       overwrite_path=True), xbmcgui.ListItem(label=utils.translate(30066, _addon), iconImage=resources.IMG_STAR,   thumbnailImage=resources.IMG_STAR), True ),
            ( mapper.build_url(url=url, paths=['browse', 'artist', 'related-artists'], overwrite_path=True), xbmcgui.ListItem(label=utils.translate(30067, _addon), iconImage=resources.IMG_ARTIST, thumbnailImage=resources.IMG_ARTIST),     True ),
        ]

        items += build_album_listitems(gmusic.get_artist_info(artist_id=artist_id, include_albums=True, max_top_tracks=0, max_rel_artist=0)['albums'])

        list_albums(items, allow_view_overwrite)

@mapper.url('^/browse/artist/top-songs/$')
def artist_top_tracks(artist_id):
    if artist_id:
        gmusic.login()

        artist = gmusic.get_artist_info(artist_id=artist_id, include_albums=False, max_top_tracks=100, max_rel_artist=0)
        if 'topTracks' in artist:
            list_songs(build_song_listitems(artist['topTracks']))

@mapper.url('^/browse/artist/related-artists/$')
def artist_related_artists(artist_id):
    if artist_id:
        gmusic.login()

        artist = gmusic.get_artist_info(artist_id=artist_id, include_albums=False, max_top_tracks=0, max_rel_artist=100)
        if 'related_artists' in artist:
            list_artists(build_artist_listitems(artist['related_artists']))

@mapper.url('^/browse/album/$', {'allow_view_overwrite': bool})
def album(album_id, allow_view_overwrite=True):
    if album_id:
        gmusic.login()
        items = build_song_listitems(gmusic.get_album_info(album_id=album_id)['tracks'])
        list_songs(items, allow_view_overwrite)

@mapper.url('^/browse/shared-playlist/$')
def listen_now_shared_playlist(shared_token):
    if shared_token:
        gmusic.login()
        playlist_content = gmusic.get_shared_playlist_contents(share_token=shared_token)

        tracks=[]
        for item in playlist_content:
            tracks.append(item['track'])

        items = build_song_listitems(tracks)
        list_songs(items)

@mapper.url('^/browse/station/$')
def station(station_id, station_name, artist_id, album_id, track_id, genre_id, curated_station_id, allow_view_overwrite=True):
    allow_view_overwrite = False if allow_view_overwrite == 'False' else True

    gmusic.login()

    if not station_id and station_name:
        station_id = gmusic.create_station(name=station_name, artist_id=artist_id, album_id=album_id, track_id=track_id, genre_id=genre_id, curated_station_id=curated_station_id)

        if not station_id:
            utils.notify(utils.translate(30050, _addon), utils.translate(30051, _addon))
            return

    tracks = gmusic.get_station_tracks(station_id=station_id, num_tracks=25)

    items = build_song_listitems(tracks=tracks, station_id=station_id)
    list_songs(items, allow_view_overwrite)



####################################################
## HELPER FOR GENERATING AND DISPLAYING LISTITEMS ##
####################################################
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
        artist_art  = artist['artistArtRef'] if 'artistArtRef' in artist else resources.IMG_ARTIST_FLAT

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
                (utils.translate(30036, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url, ['play', 'station'], \
                    {'station_name': artist_name.encode('utf-8'), 'artist_id': artist_id}, True, True)),
            ],
            replaceItems=True
        )

        # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
        if my_library:
            items.append(
                (mapper.build_url(url=url, paths=['browse', 'my-library', 'artist'], queries={'artist_id': artist_id}, \
                    overwrite_path=True, overwrite_query=True), item, True)
            )
        else:
            items.append(
                (mapper.build_url(url=url, paths=['browse', 'artist'], queries={'artist_id': artist_id}, \
                    overwrite_path=True, overwrite_query=True), item, True)
            )

    return items
def list_artists(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'artists')
    list_items(listitems, allow_view_overwrite, int(_addon.getSetting('view_id_artists')))

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
        album_art  = album['albumArtRef'] if 'albumArtRef' in album else resources.IMG_ALBUM

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
            (utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['play', 'album'], \
                queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

            (utils.translate(30039, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['queue', 'album'], \
                queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

            (utils.translate(30040, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['queue', 'album'], \
                queries={'album_id': album_id, 'play_next': True}, overwrite_path=True, overwrite_query=True)),
        ]

        if my_library:
            menu_items.append(
                (utils.translate(30061, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'remove'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
            )

        else:
            menu_items.append(
                (utils.translate(30037, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'add'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
            )

        menu_items += [
            (utils.translate(30038, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'playlist', 'add'], \
                queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True)),

            (utils.translate(30036, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['play', 'station'], \
                queries={'station_name': album_name.encode('utf-8'), 'album_id': album_id}, overwrite_path=True, overwrite_query=True)),
        ]

        if 'artistId' in album:
            menu_items.append(
                (utils.translate(30034, _addon), 'Container.Update(%s)' % mapper.build_url(url=url, paths=['browse', 'artist'], \
                queries={'artist_id': album['artistId'][0]}, overwrite_path=True, overwrite_query=True))
            )

        item.addContextMenuItems(items=menu_items, replaceItems=True)

        # My Library entries differ from normal AllAcces ones as users are able to add only parts of the item to there library
        if my_library:
            items.append(
                (mapper.build_url(url=url, paths=['browse', 'my-library', 'album'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True), item, True)
            )
        else:
            items.append(
                (mapper.build_url(url=url, paths=['browse', 'album'], \
                    queries={'album_id': album_id}, overwrite_path=True, overwrite_query=True), item, True)
            )

    return items
def list_albums(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')
    list_items(listitems, allow_view_overwrite, int(_addon.getSetting('view_id_albums')))

def build_playlist_listitems(playlists):
    items=[]
    for playlist in playlists:
        # Applies to e.g. search results
        if 'playlist' in playlist:
            playlist = playlist['playlist']

        if 'id' not in playlist or 'name' not in playlist:
            continue

        shared_token  = None
        playlist_id   = None
        playlist_name = playlist['name']
        playlist_art  = playlist['images'][0]['url'] if 'images' in playlist and len(playlist['images']) > 0 else resources.IMG_PLAYLIST

        if 'sharedToken' in playlist['id']:
            shared_token = playlist['id']['sharedToken']
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
        elif shared_token:
            paths = ['browse', 'shared-playlist']
            query['shared_token'] = shared_token

        menu_items = [
            (utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % \
                mapper.build_url(url=url, paths=['play', 'playlist'], queries=query, overwrite_path=True, overwrite_query=True))
        ]

        if playlist_id:  # Only user playlists have a playlist_id
            menu_items.append(
                (utils.translate(30068, _addon), 'XBMC.RunPlugin(%s)' % \
                    mapper.build_url(url=url, paths=['my-library', 'playlist', 'delete'], queries=query, overwrite_path=True, overwrite_query=True))
            )

        item.addContextMenuItems(items=menu_items, replaceItems= True)

        items.append(
            (mapper.build_url(url=url, paths=paths, queries=query, overwrite_path=True, overwrite_query=True), item, True)
        )

    return items
def list_playlists(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')
    list_items(listitems, allow_view_overwrite, int(_addon.getSetting('view_id_playlists')))

def build_station_listitems(stations):
    items=[]
    for station in stations:
        if 'name' not in station:
            continue

        station_name = station['name']
        station_art  = station['imageUrls'][0]['url'] if 'imageUrls' in station and len(station['imageUrls']) > 0 else resources.IMG_STATION

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
                (utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % \
                    mapper.build_url(url=url, paths=['play', 'station'], queries=query, overwrite_path=True, overwrite_query=True))
            ],
            replaceItems=True
        )


        items.append(
            (mapper.build_url(url=url, paths=['play', 'station'], queries=query, overwrite_path=True, overwrite_query=True), item, True)
        )

    return items
def list_stations(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'albums')
    list_items(listitems, allow_view_overwrite, int(_addon.getSetting('view_id_stations')), False)

def build_situation_listitems(situations):
    items = []
    for situation in situations:
        situation_id    = situation['id']
        situation_title = situation['title']
        situation_art   = situation['imageUrl'] if 'imageUrl' in situation else resources.IMG_ALBUM

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
            (mapper.build_url(url=url, paths=['browse', 'listen-now', 'situation'], \
                queries={'situation_id': situation_id}, overwrite_path=True, overwrite_query=True), item, True)
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
        album_art   = track['albumArtRef'][0]['url'] if 'albumArtRef' in track and len(track['albumArtRef']) > 0 else resources.IMG_TRACK

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
            (utils.translate(30039, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['queue', 'track'], \
                queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),

            (utils.translate(30040, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['queue', 'track'], \
                queries={'track_id': track_id, 'play_next': True}, overwrite_path=True, overwrite_query=True)),
        ]


        if my_library:
            if 'id' in track:
                menu_items.append(
                    (utils.translate(30061, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'remove'], \
                        queries={'library_song_id': track['id']}, overwrite_path=True, overwrite_query=True)),
                )

        else:
            menu_items.append(
                (utils.translate(30037, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'add'], \
                    queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
            )

        menu_items.append(
            (utils.translate(30038, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'playlist', 'add'], \
                queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
        )

        if my_library_playlist:
            if 'id' in elem:
                menu_items.append(
                    (utils.translate(30062, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'playlist', 'remove'], \
                        queries={'entry_id': elem['id']}, overwrite_path=True, overwrite_query=True)),
                )


        menu_items.append(
            (utils.translate(30036, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['play', 'station'], \
                queries={'track_id': track_id, 'station_name': track_title.encode('utf-8')}, overwrite_path=True, overwrite_query=True)),
        )

        if 'artistId' in track and len(track['artistId']) > 0:
            menu_items.append(
                (utils.translate(30034, _addon), 'Container.Update(%s)' % mapper.build_url(url=url, paths=['browse', 'artist'], \
                    queries={'artist_id': track['artistId'][0]}, overwrite_path=True, overwrite_query=True))
            )

        if 'albumId' in track:
            menu_items.append(
                (utils.translate(30035, _addon), 'Container.Update(%s)' % mapper.build_url(url=url, paths=['browse', 'album'], \
                    queries={'album_id': track['albumId']}, overwrite_path=True, overwrite_query=True))
            )

        menu_items.append(
            (utils.translate(30041, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['rate'], \
                queries={'track_id': track_id}, overwrite_path=True, overwrite_query=True)),
        )

        item.addContextMenuItems(items=menu_items, replaceItems=True)

        item.setProperty('IsPlayable','true')


        queries = {'track_id':track_id}
        if station_id:
            queries['station_id'] = station_id


        # We cache everything so :play_track: doesn't have to featch those informations again
        tracks_cache = utils.get_cache_dir(sub_dir=['tracks'])
        with open(os.path.join(tracks_cache, track_id), 'w+') as f:
            f.write(json.dumps(track, indent=2))

        items.append(
            (mapper.build_url(url=url, paths=['play', 'track'], queries=queries, overwrite_path=True, overwrite_query=True), item, False)
        )

    return items
def list_songs(listitems, allow_view_overwrite=True):
    xbmcplugin.setContent(addon_handle, 'songs')
    list_items(listitems, allow_view_overwrite, int(_addon.getSetting('view_id_songs')))


def list_items(listitems, allow_view_overwrite=True, view_mode_id=int(_addon.getSetting('view_id_list')), cacheToDisc=True):
    xbmcplugin.addDirectoryItems(
        handle=addon_handle,
        items=listitems,
        totalItems=len(listitems)
    )

    if allow_view_overwrite and _addon.getSetting('overwrite_views') == 'true':
        xbmc.executebuiltin('Container.SetViewMode(%d)' % view_mode_id)

    xbmcplugin.endOfDirectory(handle=addon_handle, cacheToDisc=cacheToDisc)
