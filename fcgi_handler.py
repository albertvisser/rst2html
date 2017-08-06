#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Old starter program currently not in use and not maintained?
"""
import sys
import os
sys.stdout = sys.stderr

import atexit
import threading
import cherrypy
from rst2html import Rst2Html
from flup.server.fcgi import WSGIServer

import cgitb
cgitb.enable()

cherrypy.config.update({'environment': 'embedded'})

## if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
    ## cherrypy.engine.start(blocking=False)
    ## atexit.register(cherrypy.engine.stop)

## os.chdir(os.path.split(__file__)[0])
application = cherrypy.tree.mount(Rst2Html())
cherrypy.config.update({'engine.autoreload_on': False,
        ## "tools.sessions.on": True,
        ## "tools.sessions.timeout": 5,
        ## "log.screen": False,
        ## "log.access_file": "/tmp/cherry_access.log",
        ## "log.error_file": "/tmp/cherry_error.log",
        'server.socket_file': "/var/run/rst2html.sock",
        ## 'server.socket_host': 'rst2html.lemoncurry.nl',
        ## 'server.socket_port': 80,
        })
#try:
WSGIServer(application).run()
#finally:
	  #cherrypy.engine.stop()
