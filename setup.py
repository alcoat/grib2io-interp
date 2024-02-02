from ctypes.util import find_library as ctypes_find_library
from numpy.distutils.core import Extension, setup
from pathlib import Path
import configparser
import numpy
import os
import platform
import sys

with open("VERSION","rt") as f:
    VERSION = f.readline().strip()

libdirs = []
incdirs = []
libraries = ['ip_4']

# ----------------------------------------------------------------------------------------
# find_library.
# ----------------------------------------------------------------------------------------
def find_library(name, dirs=None):
    _libext_by_platform = {"linux": ".so", "darwin": ".dylib"}
    out = []

    # According to the ctypes documentation Mac and Windows ctypes_find_library
    # returns the full path.
    #
    # IMPORTANT: The following does not work at this time (Jan. 2024) for macOS on
    # Apple Silicon.
    if (os.name, sys.platform) != ("posix", "linux"):
        if (sys.platform, platform.machine()) == ("darwin", "arm64"):
            pass
        else:
            out.append(ctypes_find_library(name))

    # For Linux and macOS (Apple Silicon), we have to search ourselves.
    libext = _libext_by_platform[sys.platform]
    if dirs is None:
        if os.environ.get("CONDA_PREFIX"):
            dirs = [os.environ["CONDA_PREFIX"]]
        else:
            dirs = ["/usr/local", "/sw", "/opt", "/opt/local", "/opt/homebrew", "/usr"]
    if os.environ.get("LD_LIBRARY_PATH"):
        dirs = dirs + os.environ.get("LD_LIBRARY_PATH").split(":")

    out = []
    for d in dirs:
        libs = Path(d).rglob(f"lib*{name}{libext}")
        out.extend(libs)
    if not out:
        raise ValueError(f"""

The library "lib{name}{libext}" could not be found in any of the following
directories:
{dirs}

""")
    return out[0].absolute().resolve().as_posix()

# ---------------------------------------------------------------------------------------- 
# Read setup.cfg
# ----------------------------------------------------------------------------------------
setup_cfg = 'setup.cfg'
config = configparser.ConfigParser()
config.read(setup_cfg)

# ---------------------------------------------------------------------------------------- 
# Get NCEPLIBS-ip library info.
# ---------------------------------------------------------------------------------------- 
if os.environ.get('IP_DIR'):
    ip_dir = os.environ.get('IP_DIR')
    ip_libdir = os.path.dirname(find_library('ip_4', dirs=[ip_dir]))
    ip_incdir = os.path.join(ip_dir,'include_4')
else:
    ip_dir = config.get('directories','ip_dir',fallback=None)
    if ip_dir is None:
        ip_libdir = os.path.dirname(find_library('ip_4'))
        ip_incdir = os.path.join(os.path.dirname(ip_libdir),'include_4')
    else:
        ip_libdir = os.path.dirname(find_library('ip_4', dirs=[ip_dir]))
        ip_incdir = os.path.join(os.path.dirname(ip_libdir),'include_4')
libdirs.append(ip_libdir)
incdirs.append(ip_incdir)

libdirs = list(set(libdirs))
incdirs = list(set(incdirs))
incdirs.append(numpy.get_include())

# ---------------------------------------------------------------------------------------- 
# Define interpolation NumPy extension module.
# ---------------------------------------------------------------------------------------- 
interpext = Extension(name = 'grib2io_interp.interpolate',
                      sources = ['src/interpolate/interpolate.pyf','src/interpolate/interpolate.f90'],
                      extra_f77_compile_args = ['-O3','-fopenmp'],
                      extra_f90_compile_args = ['-O3','-fopenmp'],
                      include_dirs = incdirs,
                      library_dirs = libdirs,
                      runtime_library_dirs = libdirs,
                      libraries = libraries)

# ----------------------------------------------------------------------------------------
# Create __config__.py
# ----------------------------------------------------------------------------------------
cnt = \
"""# This file is generated by grib2io-interps's setup.py
# It contains configuration information when building this package.
grib2io_interp_version = '%(grib2io_interp_version)s'
"""
a = open('src/grib2io_interp/__config__.py','w')
cfgdict = {}
cfgdict['grib2io_interp_version'] = VERSION
try:
    a.write(cnt % cfgdict)
finally:
    a.close()

# ----------------------------------------------------------------------------------------
# Import README.md as PyPi long_description
# ----------------------------------------------------------------------------------------
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# ----------------------------------------------------------------------------------------
# Run setup
# ----------------------------------------------------------------------------------------
setup(ext_modules       = [interpext],
      long_description  = long_description,
      long_description_content_type = 'text/markdown')
