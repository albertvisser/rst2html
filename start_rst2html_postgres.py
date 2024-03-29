#! /usr/bin/env python3
"""Startup script for Rst2HTML webapp PostgreSQL version
"""
import os
import pathlib
import shutil
import cherrypy

ROOT = pathlib.Path(__file__).parent.resolve()  # '/home/albert/rst2html'
os.chdir(str(ROOT))
shutil.copyfile('app_settings_postgres.py', 'app_settings.py')
from app.rst2html import Rst2Html

application = cherrypy.tree.mount(Rst2Html())
cherrypy.config.update({'environment': 'embedded'})
cherrypy.config.update({'engine.autoreload_on': False})
