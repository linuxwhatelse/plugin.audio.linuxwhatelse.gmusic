import mapper

from addon.gmusic_wrapper import GMusic

from addon import listing


mpr = mapper.Mapper.get()
gmusic = GMusic.get(debug_logging=False)


@mpr.s_url('/browse/new-releases/')
def new_releases():
    releases = gmusic.get_new_releases()
    if releases:
        items = listing.build_album_listitems(releases)
        listing.list_albums(items)

    else:
        listing.list_items([])
