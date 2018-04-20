import mapper

from addon.gmusic_wrapper import GMusic

from addon import listing


MPR = mapper.Mapper.get()
GMUSIC = GMusic.get(debug_logging=False)


@MPR.s_url('/browse/new-releases/')
def new_releases():
    releases = GMUSIC.get_new_releases()
    if releases:
        items = listing.build_album_listitems(releases)
        listing.list_albums(items)

    else:
        listing.list_items([])
