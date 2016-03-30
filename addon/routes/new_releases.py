from addon import mpr
from addon import url
from addon import addon_handle
from addon import listing
from addon import gmusic


@mpr.url('^/browse/new-releases/$')
def new_releases():
    items = listing.build_album_listitems(gmusic.get_new_releases())
    listing.list_albums(items)
