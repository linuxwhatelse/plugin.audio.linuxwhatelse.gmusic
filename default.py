import mapper

from addon import addon
from addon import routes
from addon import utils
from addon import gmusic

from addon import url

from addon.routes import actions


mpr = mapper.Mapper.get()


if __name__ == '__main__':

    if addon.getSetting('is_setup') != 'true':
        actions.setup()

    gmusic.login()
    mpr.call(url)
