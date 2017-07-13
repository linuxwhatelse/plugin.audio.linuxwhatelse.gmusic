import xbmcgui

import mapper

from addon import utils
from addon import thumbs

from addon import url
from addon import listing
from addon import gmusic


mpr = mapper.Mapper.get()


@mpr.s_url('/browse/top-charts/')
def top_charts():
    songs = xbmcgui.ListItem(utils.translate(30024))
    songs.setArt({
        'thumb'  : thumbs.IMG_TRACK,
        'poster' : thumbs.IMG_TRACK
    })

    albums = xbmcgui.ListItem(utils.translate(30023))
    albums.setArt({
        'thumb'  : thumbs.IMG_ALBUM,
        'poster' : thumbs.IMG_ALBUM
    })

    items = [
        (
            utils.build_url(url, ['songs']),
            songs,
            True
        ),
        (
            utils.build_url(url, ['albums']),
            albums,
            True
        )
    ]

    listing.list_items(items)


@mpr.s_url('/browse/top-charts/songs/')
def top_charts_songs():
    top_charts = gmusic.get_top_chart()

    if top_charts and 'tracks' in top_charts:
        items = listing.build_song_listitems(top_charts['tracks'])
        listing.list_songs(items)

    else:
        listing.list_items([])


@mpr.s_url('/browse/top-charts/albums/')
def top_charts_albums():
    top_charts = gmusic.get_top_chart()

    if top_charts and 'albums' in top_charts:
        items = listing.build_album_listitems(top_charts['albums'])
        listing.list_albums(items)

    else:
        listing.list_items([])
