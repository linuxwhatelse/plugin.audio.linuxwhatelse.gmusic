import xbmcgui

import mapper

from addon.gmusic_wrapper import GMusic
from addon import utils
from addon import thumbs

from addon import url
from addon import listing


mpr = mapper.Mapper.get()
gmusic = GMusic.get(debug_logging=False)
_cache_dir   = utils.get_cache_dir()


@mpr.s_url('/browse/browse-stations/')
def browse_stations():
    categories = gmusic.get_station_categories(False)

    items = []
    for category in categories:
        item = xbmcgui.ListItem(category['display_name'])
        item.setArt({
            'thumb'  : thumbs.IMG_STATION,
            'poster' : thumbs.IMG_STATION
        })

        items.append((
            utils.build_url(
                url     = url,
                paths   = ['browse', 'browse-stations', 'categories', category['id']],
                r_path  = True,
                r_query = True
            ),
            item,
            True
        ))

    listing.list_items(items)


@mpr.s_url('/browse/browse-stations/categories/<category_id>/')
def browse_stations_categories(category_id):
    categories = gmusic.get_station_categories(True)

    if categories:
        items = []
        for category in categories:
            if category['id'] != category_id:
                continue

            subcategories = category['subcategories']
            for sub in subcategories:
                item = xbmcgui.ListItem(sub['display_name'])
                item.setArt({
                    'thumb'  : thumbs.IMG_STATION,
                    'poster' : thumbs.IMG_STATION
                })

                items.append((
                    utils.build_url(
                        url     = url,
                        paths   = ['browse', 'browse-stations', 'subcategories', sub['id']],
                        r_path  = True,
                        r_query = True
                    ),
                    item,
                    True
                ))

    listing.list_items(items)


@mpr.s_url('/browse/browse-stations/subcategories/<subcategory_id>/')
def browse_stations_subcategories(subcategory_id):
    stations = gmusic.get_stations(subcategory_id)

    new_stations = []
    for station in stations:

        for artref in station['compositeArtRefs']:
            if artref['aspectRatio'] == '1':
                break

        new_stations.append({
            'name'      : station['name'],
            'imageUrls' : [{
                'url': artref['url']
            }],
            'curatedStationId': station['seed']['curatedStationId']
        })

    items = listing.build_station_listitems(new_stations)
    listing.list_stations(items)


@mpr.s_url('/browse/browse-stations/station/')
def browse_stations_station(station_name, curated_station_id):
    station_id = gmusic.create_station(name=station_name, curated_station_id=curated_station_id)

    if not station_id:
        utils.notify(utils.translate(30050), utils.translate(30051))
        return

    items = listing.build_song_listitems(gmusic.get_station_tracks(station_id=station_id, num_tracks=25))
    listing.list_songs(items)
