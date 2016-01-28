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
gmusic       = GMusic(debug_logging=False, validate=True, verify_ssl=True)


@mapper.url('^/browse/$')
def main_menu():
    items = [
        # URL , ListItem, isFolder
        ( mapper.build_url(url, ['listen-now']),       xbmcgui.ListItem(label=utils.translate(30014, _addon), iconImage=thumbs.IMG_HEADPHONES, thumbnailImage=thumbs.IMG_HEADPHONES), True ),
        ( mapper.build_url(url, ['top-charts']),       xbmcgui.ListItem(label=utils.translate(30015, _addon), iconImage=thumbs.IMG_STAR,       thumbnailImage=thumbs.IMG_STAR),       True ),
        ( mapper.build_url(url, ['new-releases']),     xbmcgui.ListItem(label=utils.translate(30016, _addon), iconImage=thumbs.IMG_RELEASES,   thumbnailImage=thumbs.IMG_RELEASES),   True ),
        ( mapper.build_url(url, ['my-library']),       xbmcgui.ListItem(label=utils.translate(30017, _addon), iconImage=thumbs.IMG_LIBRARY,    thumbnailImage=thumbs.IMG_LIBRARY),    True ),
        ( mapper.build_url(url, ['browse-stations']),  xbmcgui.ListItem(label=utils.translate(30018, _addon), iconImage=thumbs.IMG_STATION,    thumbnailImage=thumbs.IMG_STATION),    True ),
        ( mapper.build_url(url, ['search'], {}, True), xbmcgui.ListItem(label=utils.translate(30019, _addon), iconImage=thumbs.IMG_SEARCH,     thumbnailImage=thumbs.IMG_SEARCH),     True ),
    ]

    addon_settings = (utils.translate(30049, _addon), 'Addon.OpenSettings(%s)' % _addon.getAddonInfo('id'))

    items[0][1].addContextMenuItems([addon_settings],True)
    items[1][1].addContextMenuItems([addon_settings],True)
    items[2][1].addContextMenuItems([addon_settings],True)
    items[3][1].addContextMenuItems([(utils.translate(30030, _addon), 'XBMC.RunPlugin(%s)' % mapper.build_url(url=url, paths=['my-library', 'update'], overwrite_path=True)), addon_settings],True)
    items[4][1].addContextMenuItems([addon_settings],True)
    items[5][1].addContextMenuItems([addon_settings],True)

    listing.list_items(items)
