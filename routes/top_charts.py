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

@mapper.url('^/browse/top-charts/$')
def top_charts():
    items = [
        ( mapper.build_url(url, ['songs']),  xbmcgui.ListItem(label=utils.translate(30024, _addon), iconImage=thumbs.IMG_TRACK, thumbnailImage=thumbs.IMG_TRACK), True ),
        ( mapper.build_url(url, ['albums']), xbmcgui.ListItem(label=utils.translate(30023, _addon), iconImage=thumbs.IMG_ALBUM, thumbnailImage=thumbs.IMG_ALBUM), True ),
    ]
    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)

@mapper.url('^/browse/top-charts/songs/$')
def top_charts_songs():
    gmusic.login()

    items = listing.build_song_listitems(gmusic.get_top_chart()['tracks'])
    listing.list_songs(items)

@mapper.url('^/browse/top-charts/albums/$')
def top_charts_albums():
    gmusic.login()

    items = listing.build_album_listitems(gmusic.get_top_chart()['albums'])
    listing.list_albums(items)
