import os
import json
import locale

import xbmcgui
import xbmcaddon

import mapper

import utils
import thumbs
from gmusic import GMusic

# Variables will be set from "default.py"
url          = None
addon_handle = None
listing      = None

_addon       = xbmcaddon.Addon()
_cache_dir   = utils.get_cache_dir()
_locale_code = locale.getdefaultlocale()[0]
gmusic       = GMusic(debug_logging=False, validate=True, verify_ssl=True)


@mapper.url('^/browse/listen-now/$')
def listen_now():
    gmusic.login()

    items = [
        # URL , ListItem, isFolder
        ( mapper.build_url(url=url, paths=['play', 'station'], queries={'station_id': 'IFL'}, overwrite_path=True, \
            overwrite_query=True),              xbmcgui.ListItem(label=utils.translate(30045, _addon), iconImage=thumbs.IMG_IFL,      thumbnailImage=thumbs.IMG_IFL),      True ),
        ( mapper.build_url(url, ['albums']),    xbmcgui.ListItem(label=utils.translate(30023, _addon), iconImage=thumbs.IMG_ALBUM,    thumbnailImage=thumbs.IMG_ALBUM),    True ),
        ( mapper.build_url(url, ['stations']),  xbmcgui.ListItem(label=utils.translate(30021, _addon), iconImage=thumbs.IMG_STATION,  thumbnailImage=thumbs.IMG_STATION),  True ),
        ( mapper.build_url(url, ['playlists']), xbmcgui.ListItem(label=utils.translate(30020, _addon), iconImage=thumbs.IMG_PLAYLIST, thumbnailImage=thumbs.IMG_PLAYLIST), True ),

    ]

    # Get current situation and add it to the list
    situations = gmusic.get_situations(_locale_code)

    # We save the current response so we don't have to fetch it again when the users selects it
    with open(os.path.join(_cache_dir, 'situations.json'), 'w+') as f:
        f.write(json.dumps(situations, indent=2))

    items.insert(1, ( mapper.build_url(url, ['situations']), xbmcgui.ListItem(label=situations['primaryHeader'], iconImage=thumbs.IMG_ALBUM, thumbnailImage=thumbs.IMG_ALBUM),    True ))

    for item in items:
        item[1].addContextMenuItems([],True)

    # Add "Play All" to I'm feeling lucky context menu
    items[0][1].addContextMenuItems(
        [(utils.translate(30033, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['play', 'station'], queries={'station_id': 'IFL'}, overwrite_path=True, overwrite_query=True))], True
    )

    listing.list_items(items)

@mapper.url('^/browse/listen-now/situations/$')
def listen_now_situations():
    situations = None
    with open(os.path.join(_cache_dir, 'situations.json'), 'r') as f:
        situations = json.loads(f.read())

    if situations:
        items = listing.build_situation_listitems(situations['situations'])
        listing.list_situations(items)

@mapper.url('^/browse/listen-now/situation/$')
def listen_now_situation(situation_id):
    situations = None
    with open(os.path.join(_cache_dir, 'situations.json'), 'r') as f:
        situations = json.loads(f.read())

    if not situations:
        listing.list_items([])

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
            items = listing.build_situation_listitems(situation['situations'])
            listing.list_situations(items)

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

            items = listing.build_station_listitems(new_stations)
            listing.list_stations(items)

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

    items = listing.build_album_listitems(albums)
    listing.list_albums(items)

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

    items = listing.build_station_listitems(new_stations)
    listing.list_stations(items)

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

    items = listing.build_playlist_listitems(playlists)
    listing.list_playlists(items)
