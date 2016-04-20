from addon import addon
from addon import mpr
from addon import routes
from addon import utils
from addon import gmusic

from addon import url

if __name__ == '__main__':
    if addon.getSetting('is_setup') != 'true':
        mpr.call(utils.build_url(url=url, paths=['setup'],
            r_path=True, r_query=True))

    gmusic.login()
    mpr.call(url)
