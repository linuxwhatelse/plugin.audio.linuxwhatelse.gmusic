import os
import json
import locale

import xbmc
import xbmcgui
import xbmcaddon

from addon import utils
from addon import thumbs

from addon import mpr
from addon import url
from addon import listing
from addon import gmusic


_cache_dir   = utils.get_cache_dir()

@mpr.url('^/browse/listen-now/$')
def listen_now():
    items = [
        (
            utils.build_url(
                url=url,
                paths=['play', 'station'],
                queries={'station_id': 'IFL'},
                r_path=True,
                r_query=True
            ),
            xbmcgui.ListItem(
                label          = utils.translate(30045),
                iconImage      = thumbs.IMG_IFL,
                thumbnailImage = thumbs.IMG_IFL
            ),
            True
        ),
        (
            utils.build_url(
                url   = url,
                paths = ['albums']
            ),
            xbmcgui.ListItem(
                label          = utils.translate(30023),
                iconImage      = thumbs.IMG_ALBUM,
                thumbnailImage = thumbs.IMG_ALBUM),
            True
        ),
        (
            utils.build_url(
                url   = url,
                paths = ['stations']
            ),
            xbmcgui.ListItem(
                label          = utils.translate(30021),
                iconImage      = thumbs.IMG_STATION,
                thumbnailImage = thumbs.IMG_STATION),
            True
        ),
        (
            utils.build_url(
                url   = url,
                paths = ['playlists']
            ),
            xbmcgui.ListItem(
                label          = utils.translate(30020),
                iconImage      = thumbs.IMG_PLAYLIST,
                thumbnailImage = thumbs.IMG_PLAYLIST),
            True
        ),

    ]

    locale_code = xbmc.getLanguage(xbmc.ISO_639_1)
    locale_code = locale.normalize(locale_code).split('.')[0]

    if not locale_code or locale_code == xbmc.getLanguage(xbmc.ISO_639_1):
        locale_code = 'en_US'
        utils.log('Could not retrieve your locale. Using "%s" instead' % locale_code, xbmc.LOGERROR)

    situations = gmusic.get_situations(locale_code)

    if situations and 'primaryHeader' in situations:
        # We save the current response so we don't have to fetch it again when the users selects it
        with open(os.path.join(_cache_dir, 'situations.json'), 'w+') as f:
            f.write(json.dumps(situations))

        items.insert(1, (
            utils.build_url(
                url   = url,
                paths = ['situations']
            ),
            xbmcgui.ListItem(
                label          = situations['primaryHeader'],
                iconImage      = thumbs.IMG_ALBUM,
                thumbnailImage = thumbs.IMG_ALBUM),
            True
        ))

    else:
        utils.log('Failed retrieving situations. Locale is %s' % locale_code, xbmc.LOGERROR)

    for item in items:
        item[1].addContextMenuItems([],True)

    # Add "Play All" to I'm feeling lucky context menu
    items[0][1].addContextMenuItems(
        [(
            utils.translate(30033),
            'XBMC.RunPlugin(%s)' % utils.build_url(
                url=url,
                paths=['play', 'station'],
                queries={'station_id': 'IFL'},
                r_path=True,
                r_query=True
            )
        )],
        True
    )

    listing.list_items(items)

@mpr.url('^/browse/listen-now/situations/$')
def listen_now_situations():
    situations = None
    with open(os.path.join(_cache_dir, 'situations.json'), 'r') as f:
        situations = json.loads(f.read())

    if situations:
        items = listing.build_situation_listitems(situations['situations'])
        listing.list_situations(items)

@mpr.url('^/browse/listen-now/situation/$')
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

@mpr.url('^/browse/listen-now/albums/$')
def listen_now_albums():
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

@mpr.url('^/browse/listen-now/stations/$')
def listen_now_stations():
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

@mpr.url('^/browse/listen-now/playlists/$')
def listen_now_playlists():
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
