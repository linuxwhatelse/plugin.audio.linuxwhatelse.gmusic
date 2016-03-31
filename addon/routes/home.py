import xbmcgui
import xbmcaddon

from addon import utils
from addon import thumbs

from addon import addon
from addon import mpr
from addon import url
from addon import addon_handle
from addon import listing


@mpr.url('^/browse/$')
def main_menu():
    items = [
        (utils.build_url(url, ['listen-now']),
            xbmcgui.ListItem(
                label=utils.translate(30014, addon),
                iconImage=thumbs.IMG_HEADPHONES,
                thumbnailImage=thumbs.IMG_HEADPHONES
            ),
            True
        ),

        (utils.build_url(url, ['top-charts']),
            xbmcgui.ListItem(
                label=utils.translate(30015, addon),
                iconImage=thumbs.IMG_STAR,
                thumbnailImage=thumbs.IMG_STAR
            ),
            True
        ),

        (utils.build_url(url, ['new-releases']),
            xbmcgui.ListItem(
                label=utils.translate(30016, addon),
                iconImage=thumbs.IMG_RELEASES,
                thumbnailImage=thumbs.IMG_RELEASES
            ),
            True
        ),

        (utils.build_url(url, ['my-library']),
            xbmcgui.ListItem(
                label=utils.translate(30017, addon),
                iconImage=thumbs.IMG_LIBRARY,
                thumbnailImage=thumbs.IMG_LIBRARY
            ),
            True
        ),

        (utils.build_url(url, ['browse-stations']),
            xbmcgui.ListItem(
                label=utils.translate(30018, addon),
                iconImage=thumbs.IMG_STATION,
                thumbnailImage=thumbs.IMG_STATION
            ),
            True
        ),

        (utils.build_url(url, ['search', 'history'], r_path=True),
            xbmcgui.ListItem(
                label=utils.translate(30019, addon),
                iconImage=thumbs.IMG_SEARCH,
                thumbnailImage=thumbs.IMG_SEARCH
            ),
            True
        ),
    ]

    # "My Library" entry
    items[3][1].addContextMenuItems([(
        utils.translate(30030, addon),
        'XBMC.RunPlugin(%s)' % utils.build_url(
            url=url,
            paths=['my-library', 'update'],
            r_path=True
        )
    )])

    # "Search" entry
    items[5][1].addContextMenuItems([(
        utils.translate(30012, addon),
        'XBMC.RunPlugin(%s)' % utils.build_url(
            url=url,
            paths=['clear', 'search-history'],
            r_path=True
        )
    )])

    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)
