import os
import site
from sys import platform as _platform

lib_root_dir = os.path.dirname(os.path.abspath(__file__))

# Default cross plattform libraries
lib_dir = os.path.join(lib_root_dir, 'lib')

# Libraries normally included with python but missing on some plattforms
lib_sys_dir = os.path.join(lib_root_dir, 'lib-sys')

# Add all cross plattform dependencies to the python path
site.addsitedir(lib_dir)

# Special case libraries that usually exist on most systems but don't on
# some others
try:
    import lib2to3

except ImportError:
    site.addsitedir(os.path.join(lib_sys_dir, 'lib2to3'))
