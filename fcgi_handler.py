#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
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

application = cherrypy.tree.mount(Rst2Html(), config=None)
cherrypy.config.update({'engine.autoreload_on': False,
				# 'server.socket_host': 'rst2html.linuxmoby.nl',
				# 'server.socket_port': 80,
				})
## try:
WSGIServer(application).run()
## finally:
	## cherrypy.engine.stop()