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


@mpr.url('^/browse/top-charts/$')
def top_charts():
    items = [
        ( utils.build_url(url, ['songs']),  xbmcgui.ListItem(label=utils.translate(30024), iconImage=thumbs.IMG_TRACK, thumbnailImage=thumbs.IMG_TRACK), True ),
        ( utils.build_url(url, ['albums']), xbmcgui.ListItem(label=utils.translate(30023), iconImage=thumbs.IMG_ALBUM, thumbnailImage=thumbs.IMG_ALBUM), True ),
    ]
    for item in items:
        item[1].addContextMenuItems([],True)

    listing.list_items(items)

@mpr.url('^/browse/top-charts/songs/$')
def top_charts_songs():
    items = listing.build_song_listitems(gmusic.get_top_chart()['tracks'])
    listing.list_songs(items)

@mpr.url('^/browse/top-charts/albums/$')
def top_charts_albums():
    items = listing.build_album_listitems(gmusic.get_top_chart()['albums'])
    listing.list_albums(items)
