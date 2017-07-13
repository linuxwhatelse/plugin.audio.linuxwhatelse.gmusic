import mapper

from addon import listing
from addon import gmusic


mpr = mapper.Mapper.get()


@mpr.s_url('/browse/new-releases/')
def new_releases():
    releases = gmusic.get_new_releases()
    if releases:
        items = listing.build_album_listitems(releases)
        listing.list_albums(items)

    else:
        listing.list_items([])
