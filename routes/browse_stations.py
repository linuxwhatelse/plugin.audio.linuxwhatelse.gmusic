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
                xbmcgui.ListItem(label=category['display_name'], iconImage=thumbs.IMG_STATION, thumbnailImage=thumbs.IMG_STATION), True )
        )

    for item in items:
        item[1].addContextMenuItems([], True)

    listing.list_items(items)

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
                        xbmcgui.ListItem(label=sub['display_name'], iconImage=thumbs.IMG_STATION, thumbnailImage=thumbs.IMG_STATION), True )
                )

        for item in items:
            item[1].addContextMenuItems([], True)

    listing.list_items(items)

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

    items = listing.build_station_listitems(new_stations)
    #ToDo: double-check the list_items here. Shouldn't we use list_stations?
    listing.list_items(items)

@mapper.url('^/browse/browse-stations/station/$')
def browse_stations_subcategories(station_name, curated_station_id):
    if station_name:
        gmusic.login()
        station_id = gmusic.create_station(name=station_name, curated_station_id=curated_station_id)

        if not station_id:
            utils.notify(utils.translate(30050, _addon), utils.translate(30051, _addon))
            return

        items = listing.build_song_listitems(gmusic.get_station_tracks(station_id=station_id, num_tracks=25))
        listing.list_songs(items)
