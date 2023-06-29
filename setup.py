from numpy.distutils.core import Extension, setup
import configparser
import numpy
import os
import pathlib
import platform
import sys

VERSION = '1.0.0'

libdirs = []
incdirs = []
libraries = ['sp_4','ip_4']

# ----------------------------------------------------------------------------------------
# find_library.
# ----------------------------------------------------------------------------------------
def find_library(name):
    out = []
    sysinfo = (os.name, sys.platform)
    if sysinfo == ('posix', 'darwin'):
        libext = '.dylib'
    elif sysinfo == ('posix', 'linux'):
        libext = '.so'
    DIRS_TO_SEARCH = ['/usr/local', '/sw', '/opt', '/opt/local', '/opt/homebrew', '/usr']
    for d in DIRS_TO_SEARCH:
        libs = pathlib.Path(d).rglob('lib*'+name+libext)
        for l in libs: out.append(l.as_posix())
    return list(set(out))[0]

# ---------------------------------------------------------------------------------------- 
# Read setup.cfg
# ----------------------------------------------------------------------------------------
setup_cfg = 'setup.cfg'
config = configparser.ConfigParser()
config.read(setup_cfg)

# ---------------------------------------------------------------------------------------- 
# Get NCEPLIBS-sp library info.  NOTE: NCEPLIBS-sp does not have include files.
# ---------------------------------------------------------------------------------------- 
if os.environ.get('SP_DIR'):
    sp_dir = os.environ.get('SP_DIR')
    if os.path.exists(os.path.join(sp_dir,'lib')):
        sp_libdir = os.path.join(sp_dir,'lib')
    elif os.path.exists(os.path.join(sp_dir,'lib64')):
        sp_libdir = os.path.join(sp_dir,'lib64')
else:
    sp_dir = config.get('directories','sp_dir',fallback=None)
    if sp_dir is None:
       sp_libdir = os.path.dirname(find_library('sp_4'))
libdirs.append(sp_libdir)

# ---------------------------------------------------------------------------------------- 
# Get NCEPLIBS-ip library info.
# ---------------------------------------------------------------------------------------- 
if os.environ.get('IP_DIR'):
    ip_dir = os.environ.get('IP_DIR')
    if os.path.exists(os.path.join(ip_dir,'lib')):
        ip_libdir = os.path.join(ip_dir,'lib')
    elif os.path.exists(os.path.join(ip_dir,'lib64')):
        ip_libdir = os.path.join(ip_dir,'lib64')
else:
    ip_dir = config.get('directories','ip_dir',fallback=None)
    if ip_dir is None:
       ip_libdir = os.path.dirname(find_library('ip_4'))
       ip_incdir = os.path.join(os.path.dirname(ip_libdir),'include_4')
libdirs.append(ip_libdir)
incdirs.append(ip_incdir)

libdirs = list(set(libdirs))
incdirs = list(set(incdirs))

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
