import xbmcgui

import mapper

from addon import utils
from addon import listing
from addon import thumbs

from addon import URL


MPR = mapper.Mapper.get()


@MPR.s_url('/browse/')
def main_menu():
    listen_now = xbmcgui.ListItem(utils.translate(30014))
    listen_now.setArt({
        'thumb': thumbs.IMG_HEADPHONES,
        'poster': thumbs.IMG_HEADPHONES
    })

    top_charts = xbmcgui.ListItem(utils.translate(30015))
    top_charts.setArt({
        'thumb': thumbs.IMG_STAR,
        'poster': thumbs.IMG_STAR
    })

    new_releases = xbmcgui.ListItem(utils.translate(30016))
    new_releases.setArt({
        'thumb': thumbs.IMG_RELEASES,
        'poster': thumbs.IMG_RELEASES
    })

    my_library = xbmcgui.ListItem(utils.translate(30017))
    my_library.setArt({
        'thumb': thumbs.IMG_LIBRARY,
        'poster': thumbs.IMG_LIBRARY
    })

    browse_stations = xbmcgui.ListItem(utils.translate(30018))
    browse_stations.setArt({
        'thumb': thumbs.IMG_STATION,
        'poster': thumbs.IMG_STATION
    })

    search = xbmcgui.ListItem(utils.translate(30019))
    search.setArt({
        'thumb': thumbs.IMG_SEARCH,
        'poster': thumbs.IMG_SEARCH
    })

    items = [
        (
            utils.build_url(URL, ['listen-now']),
            listen_now,
            True
        ),
        (
            utils.build_url(URL, ['top-charts']),
            top_charts,
            True
        ),
        (
            utils.build_url(URL, ['new-releases']),
            new_releases,
            True
        ),
        (
            utils.build_url(URL, ['my-library']),
            my_library,
            True
        ),
        (
            utils.build_url(URL, ['browse-stations']),
            browse_stations,
            True
        ),
        (
            utils.build_url(URL, ['search', 'history'], r_path=True),
            search,
            True
        ),
    ]

    # Add "Update Library" context menu to "My Library" entry
    items[3][1].addContextMenuItems([(
        utils.translate(30030),
        'XBMC.RunPlugin(%s)' % utils.build_url(
            url=URL,
            paths=['my-library', 'update'],
            r_path=True
        )
    )])

    # Add "Clear search history" context menu to "Search" entry
    items[5][1].addContextMenuItems([(
        utils.translate(30012),
        'XBMC.RunPlugin(%s)' % utils.build_url(
            url=URL,
            paths=['clear', 'search-history'],
            r_path=True
        )
    )])

    listing.list_items(items)
