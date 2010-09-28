import sys
sys.stdout = sys.stderr

import atexit
import threading
import cherrypy
from rsthtml import Rst2Html

cherrypy.config.update({'environment': 'embedded'})

if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)

application = cherrypy.Application(Rst2Html(), script_name=None, config=None)