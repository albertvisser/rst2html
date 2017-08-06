"""sample application-wide settings for Rst2HTML
"""
import pathlib
import collections

# specify which data backend to use
## DML = 'fs'        # file system
DML = 'mongo'     # NoSQL
## DML = 'postgres'  # SQL
# database connection parameters (needed for postgresql)
user = '<username>'
password = '<password>'
# default site to start the application with
DFLT = '<sitename>'
# physical path for mirror root
# note: home works from Python 3.5 onwards. If your Python is older, simply use the full path
FS_WEBROOT = pathlib.Path('<webroot>')  # as configured in web server
DB_WEBROOT = pathlib.Path(__file__).parent / 'rst2html-data'    # database versions
# css files that are always needed, will be copied to every new site
BASIC_CSS = ['reset.css', 'html4css1.css', '960.css']

#
# the following settings are not meant to be modified for a user-installation
# as they are actually constants  (and a class) for the application
#
WEBROOT = FS_WEBROOT if DML == 'fs' else DB_WEBROOT
# convert locations/doctypes to extensions v.v.
EXTS, LOCS = ['.rst', '.html', '.html'], ['src', 'dest', 'to_mirror']
EXT2LOC = dict(zip(EXTS, LOCS))
LOC2EXT = dict(zip(LOCS, EXTS))
Stats = collections.namedtuple('Stats', LOCS)
