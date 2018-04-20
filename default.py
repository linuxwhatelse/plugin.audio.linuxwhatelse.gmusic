import mapper

# Get all routes added to the mappers data store
from addon import routes  # noqa
from addon.gmusic_wrapper import GMusic

from addon import ADDON
from addon import URL

from addon.routes import actions


MPR = mapper.Mapper.get()
GMUSIC = GMusic.get(debug_logging=False)


if __name__ == '__main__':
    if ADDON.getSetting('is_setup') != 'true':
        actions.setup()

    GMUSIC.login()
    MPR.call(URL)
