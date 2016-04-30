
import os
import pathlib

# specify which data backend to use
DML = 'fs'        # file system
## DML = 'mongo'     # NoSQL
## DML = 'postgres'  # SQL

# basepath for file system version
WEBROOT = pathlib.Path(os.environ['HOME']) / 'www'

# settings file name pattern for file system version
SETTFILE = 'settings_{}.yml'
