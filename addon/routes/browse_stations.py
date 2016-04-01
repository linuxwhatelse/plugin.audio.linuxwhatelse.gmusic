import os
import json
import locale

import xbmcgui
import xbmcaddon

from addon import utils
from addon import thumbs

from addon import addon
from addon import mpr
from addon import url
from addon import addon_handle
from addon import listing
from addon import gmusic


_cache_dir   = utils.get_cache_dir()
_locale_code = locale.getdefaultlocale()[0]


@mpr.url('^/browse/browse-stations/$')
def browse_stations():
    categories = gmusic.get_station_categories()
    with open(os.path.join(_cache_dir,'categories.json'), 'w+') as f:
        f.write(json.dumps(categories))

    items = []
    for category in categories:
        items.append(
            ( utils.build_url(url=url, paths=['browse', 'browse-stations', 'categories'], \
                queries={'category_id': category['id']}, r_path=True, r_query=True), \
                xbmcgui.ListItem(label=category['display_name'], iconImage=thumbs.IMG_STATION, thumbnailImage=thumbs.IMG_STATION), True )
        )

    for item in items:
        item[1].addContextMenuItems([], True)

    listing.list_items(items)

@mpr.url('^/browse/browse-stations/categories/$')
def browse_stations_categories(category_id):
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
                    ( utils.build_url(url=url, paths=['browse', 'browse-stations', 'subcategories'], \
                        queries={'subcategory_id': sub['id']}, r_path=True, r_query=True), \
                        xbmcgui.ListItem(label=sub['display_name'], iconImage=thumbs.IMG_STATION, thumbnailImage=thumbs.IMG_STATION), True )
                )

        for item in items:
            item[1].addContextMenuItems([], True)

    listing.list_items(items)

@mpr.url('^/browse/browse-stations/subcategories/$')
def browse_stations_subcategories(subcategory_id):
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

@mpr.url('^/browse/browse-stations/station/$')
def browse_stations_subcategories(station_name, curated_station_id):
    if station_name:
        station_id = gmusic.create_station(name=station_name, curated_station_id=curated_station_id)

        if not station_id:
            utils.notify(utils.translate(30050), utils.translate(30051))
            return

        items = listing.build_song_listitems(gmusic.get_station_tracks(station_id=station_id, num_tracks=25))
        listing.list_songs(items)
