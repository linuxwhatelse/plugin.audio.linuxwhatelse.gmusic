import os
import site
from sys import platform as _platform

# Define all available lib directories
lib_root_dir   = os.path.dirname(os.path.abspath(__file__))
lib_dir        = os.path.join(lib_root_dir, 'lib')         # Default cross plattform libraries
lib_sys_dir    = os.path.join(lib_root_dir, 'lib-sys')     # Libraries normally included with python but missing on some plattforms

# Add all cross plattform dependencies to the python path
site.addsitedir( lib_dir )

# "future" comes with a lot of root-level modules which would clutter the
# "lib" direcotry.
# That's why it gets special treatment and will be placed in its own folder
lib_future_dir = os.path.join(lib_root_dir, 'lib-future')
site.addsitedir( lib_future_dir )

# Special case libraries that usually exist on most systems but don't on
# some others
try:
    import lib2to3
except ImportError:
    site.addsitedir( os.path.join(lib_sys_dir, 'lib2to3') )
