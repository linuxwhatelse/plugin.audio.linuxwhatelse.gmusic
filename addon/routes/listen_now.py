import time

import xbmcgui

from addon import utils
from addon import thumbs

from addon import addon
from addon import mpr
from addon import url
from addon import listing
from addon import gmusic

_cache_dir = utils.get_cache_dir()


@mpr.s_url('/browse/listen-now/')
def listen_now():
    ifl = xbmcgui.ListItem(utils.translate(30045))
    ifl.setArt({
        'thumb'  : thumbs.IMG_IFL,
        'poster' : thumbs.IMG_IFL
    })

    albums = xbmcgui.ListItem(utils.translate(30023))
    albums.setArt({
        'thumb'  : thumbs.IMG_ALBUM,
        'poster' : thumbs.IMG_ALBUM
    })

    stations = xbmcgui.ListItem(utils.translate(30021))
    stations.setArt({
        'thumb'  : thumbs.IMG_STATION,
        'poster' : thumbs.IMG_STATION
    })

    playlists = xbmcgui.ListItem(utils.translate(30020))
    playlists.setArt({
        'thumb'  : thumbs.IMG_PLAYLIST,
        'poster' : thumbs.IMG_PLAYLIST
    })

    items = [
        (
            utils.build_url(
                url     = url,
                paths   = ['play', 'station'],
                queries = {'station_id': 'IFL'},
                r_path  = True,
                r_query = True
            ),
            ifl,
            True
        ),
        (
            utils.build_url(url, ['albums']),
            albums,
            True
        ),
        (
            utils.build_url(url, ['stations']),
            stations,
            True
        ),
        (
            utils.build_url(url, ['playlists']),
            playlists,
            True
        ),

    ]

    # Only fetch new information if one full hour has passed
    # to keep things speedy on slow devices
    try:
        last_check = addon.getSetting('listen_now_last_update')

    except:
        last_check = -1

    from_cache = True
    if last_check != time.strftime('%Y%m%d%H'):
        from_cache = False
        addon.setSetting('listen_now_last_update', time.strftime('%Y%m%d%H'))

    primary_header, situations = gmusic.get_listen_now_situations(from_cache)

    if primary_header and situations:
        situations = xbmcgui.ListItem(primary_header)
        situations.setArt({
            'thumb'  : thumbs.IMG_ALBUM,
            'poster' : thumbs.IMG_ALBUM
        })

        # Add Situations after IFL
        items.insert(1, (
            utils.build_url(url, ['situations']),
            situations,
            True
        ))

    # Remove all default context menu items (like "Play all", "Queue", etc.)
    for item in items:
        item[1].addContextMenuItems([], True)

    listing.list_items(items)


@mpr.s_url('/browse/listen-now/situations/')
def listen_now_situations():
    primary_header, situations = gmusic.get_listen_now_situations(
        from_cache=True)

    if situations:
        items = listing.build_situation_listitems(situations)
        listing.list_situations(items)


@mpr.s_url('/browse/listen-now/situation/<situation_id>/')
def listen_now_situation(situation_id):
    def _find_situation(situation_id, situations, parent=None):
        """ Helper to find the right situation as
        situations can have situations as child (instead of stations)
        """
        match  = None
        for situation in situations:
            parent = situation

            if 'id' in situation and situation['id'] == situation_id:
                match = situation

            elif 'situations' in situation:
                parent, match = _find_situation(situation_id,
                                                situation['situations'],
                                                parent)

            if match:
                return parent, match

        return None, None

    primary_header, situations = gmusic.get_listen_now_situations(
        from_cache=True)

    if not situations:
        listing.list_items([])
        return

    parent, situation = _find_situation(situation_id, situations)

    if not situation:
        listing.list_items([])
        return

    items = []
    if 'situations' in situation:
        sub_situations = situation['situations']
        for i, sit in enumerate(sub_situations):
            sub_situations[i]['imageUrl'] = parent['imageUrl']

        items = listing.build_situation_listitems(sub_situations)

    elif 'stations' in situation:
        stations = []
        for station in situation['stations']:
            art = ''
            for img_urls in station['compositeArtRefs']:
                if int(img_urls['aspectRatio']) == 1:
                    art = img_urls['url']
                    break

            stations.append({
                'name'      : station['name'],
                'imageUrls' : [{
                    'url' : art
                }],
                'curatedStationId' : station['seed']['curatedStationId'],
                'description'      : station['description']
            })

        items = listing.build_station_listitems(stations)

    listing.list_stations(items)


@mpr.s_url('/browse/listen-now/albums/')
def listen_now_albums():
    listen_now = gmusic.get_listen_now_items()

    albums   = []
    for item in listen_now:
        # 1 = album
        # 2 = playlist
        # 3 = radio
        if item['type'] != '1':
            continue

        album = item['album']
        if 'id' not in album and 'metajamCompactKey' not in album['id']:
            continue

        album_title = ''
        if 'title' in album:
            album_title = album['title']

        album_artist = None
        if 'artist_name' in album:
            album_artist = album['artist_name']

        album_art = thumbs.IMG_ALBUM
        if 'images' in item and len(item['images']) > 0:
            album_art = item['images'][0]['url']

        albums.append({
            'albumId'     : album['id']['metajamCompactKey'],
            'name'        : album_title,
            'albumArtist' : album_artist,
            'albumArtRef' : album_art
        })

    items = listing.build_album_listitems(albums)
    listing.list_albums(items)


@mpr.s_url('/browse/listen-now/stations/')
def listen_now_stations():
    listen_now = gmusic.get_listen_now_items()

    new_stations = []
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
            'name'      : station['title'],
            'imageUrls' : [{
                'url' : art
            }],
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

    items = listing.build_station_listitems(new_stations)
    listing.list_stations(items)


@mpr.s_url('/browse/listen-now/playlists/')
def listen_now_playlists():
    listen_now = gmusic.get_listen_now_items()

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

        playlists.append({
            'id'     : playlist['id'],
            'name'   : playlist['title'],
            'images' : item['images'],
        })

    items = listing.build_playlist_listitems(playlists)
    listing.list_playlists(items)
