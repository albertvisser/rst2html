import os
import pathlib
import collections

# specify which data backend to use
## DML = 'fs'        # file system
DML = 'mongo'     # NoSQL
## DML = 'postgres'  # SQL
# default site to start the application with
DFLT ='bitbucket'
# css files that are always needed, will be copied to every new site
BASIC_CSS = ['reset.css', 'html4css1.css', '960.css']

#
# the following settings are not meant to be modified for a user-installation
# as they are actually constants  (and a class) for the application
#
# physical path for mirror root
FS_WEBROOT = pathlib.Path('/home/albert') / 'www'  # as configured in web server
DB_WEBROOT = pathlib.Path(__file__).parent / 'rst2html-data'    # database versions
WEBROOT = FS_WEBROOT if DML == 'fs' else DB_WEBROOT
# convert locations/doctypes to extensions v.v.
EXTS, LOCS = ['.rst', '.html', '.html'], ['src', 'dest', 'to_mirror']
EXT2LOC = dict(zip(EXTS, LOCS))
LOC2EXT = dict(zip(LOCS, EXTS))
Stats = collections.namedtuple('Stats', LOCS)
