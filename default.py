from os import chdir

from addon import addon
from addon import mpr
from addon import routes
from addon import utils

from addon import url

if __name__ == '__main__':
    # The initial login to google will be logged, therefor we make sure the logfile
    # will be written into our cache dir
    # On Windows the default directory would be Kodis installation dir where we can
    # NOT assume to have write rights
    chdir(utils.get_cache_dir())

    if addon.getSetting('is_setup') != 'true':
        mpr.call(utils.build_url(url=url, paths=['setup'],
            r_path=True, r_query=True))

    mpr.call(url)
