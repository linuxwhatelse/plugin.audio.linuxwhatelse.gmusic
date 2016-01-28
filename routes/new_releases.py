import mapper

from gmusic import GMusic

# Variables will be set from "default.py"
url          = None
addon_handle = None
listing      = None

gmusic       = GMusic(debug_logging=False, validate=True, verify_ssl=True)


@mapper.url('^/browse/new-releases/$')
def new_releases():
    gmusic.login()

    items = listing.build_album_listitems(gmusic.get_new_releases())
    listing.list_albums(items)
