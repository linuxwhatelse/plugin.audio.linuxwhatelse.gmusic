from os import pardir
from os.path import dirname, abspath, join
from site import addsitedir
from sys import platform as _platform

lib_dir       = dirname(abspath(__file__))
lib_win32_dir = join(lib_dir, pardir, 'lib-win32')
lib_unix_dir  = join(lib_dir, pardir, 'lib-unix')

if _platform == 'win32':
    addsitedir( lib_win32_dir )
else:
    addsitedir( lib_unix_dir )

addsitedir( lib_dir )
