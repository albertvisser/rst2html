#! /usr/bin/env python3
"""Startup script for Rst2HTML webapp file system version
"""
import sys
import os
import pathlib
import shutil
# import cgitb
import cherrypy
# cgitb.enable()

ROOT = pathlib.Path(__file__).parent.resolve()  # '/home/albert/rst2html'
os.chdir(str(ROOT))
# sys.path.insert(0, str(ROOT))
shutil.copyfile('app_settings_fs.py', 'app_settings.py')
from app.rst2html import Rst2Html

application = cherrypy.tree.mount(Rst2Html())
cherrypy.config.update({'environment': 'embedded'})
cherrypy.config.update({'engine.autoreload_on': False})
