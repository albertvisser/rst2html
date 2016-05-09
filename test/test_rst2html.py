# -*- coding: utf-8 -*-
import os
import sys
import pathlib
import datetime
## import cherrypy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import rst2html_all as r2h
from app_settings import DML
if DML == 'fs':
    print('using file system dml')
    from docs2fs import Stats
elif DML == 'mongo':
    print('using mongodb dml')
    from docs2mongo import Stats
elif DML == 'postgres':
    print('using postgresql dml')
    from docs2pg import Stats

## from cptestcase import BaseCherryPyTestCase

def test_unexposed():
    """just testing the two presentation functions should be enough as there's
    hardly any logic in the webapp class, just passing data from the processing
    functions to the server.
    """
    sitename = 'test'
    state = r2h.rhfn.R2hState()
    state.sitename = sitename
    state.conf = {'lang': 'en', 'wid': 200, 'hig': 40}

    print('testing format_output...', end='')
    state.loaded = r2h.rhfn.RST
    with open('/tmp/test_empty.html', 'w') as _out:
        _out.write(r2h.format_output('', '', '', '', '', '', state))
    with open('/tmp/test_jansen.html', 'w') as _out:
        _out.write(r2h.format_output('jansen.rst', 'jansen.html', 'newjansen.rst',
        'this is a message', 'this is data!', 'test', state))
    print('ok')

    print('testing format_overview... ', end ='')
    data = r2h.format_progress_list([
        ('/', 'horrorscenario', 0, Stats(
            src=datetime.datetime(2016, 3, 28, 16, 0, 52, 96000),
            dest=datetime.datetime(1, 1, 1, 0, 0),
            to_mirror=datetime.datetime(1, 1, 1, 0, 0))),
        ('/', 'jansen', 2, Stats(
            src=datetime.datetime(2016, 3, 28, 16, 0, 52, 248000),
            dest=datetime.datetime(2016, 3, 28, 16, 0, 52, 326000),
            to_mirror=datetime.datetime(2016, 3, 28, 16, 0, 52, 329000))),
        ('guichelheil', 'pietersen', 2, Stats(
            src=datetime.datetime(2016, 3, 28, 16, 0, 52, 248000),
            dest=datetime.datetime(2016, 3, 28, 16, 0, 52, 326000),
            to_mirror=datetime.datetime(2016, 3, 28, 16, 0, 52, 329000))),
        ])
    with open('/tmp/progress_list.html', 'w') as _out:
        _out.write(data.format(sitename))
    ## sp.Popen(['/home/albert/bin/viewhtml', '/tmp/test2.html'])
    print('ok')

    print('testing resolve_images... ', end='')
    testdata = ''.join(('begin',
        '<img />',
        '<img src="here.img"/>'
        '<img src="/here.img"/>'
        '<img src="somewhere/here.img"/>'
        '<img src="/somewhere/here.img"/>'
        '<img src="http://somewhere.com/here.img"/>'
        'einde'))
    testoutput_1 = ''.join(('begin<img />',
        '<img src="http://www.example.com/here.img"/>',
        '<img src="http://www.example.com/here.img"/>',
        '<img src="http://www.example.com/somewhere/here.img"/>',
        '<img src="http://www.example.com/somewhere/here.img"/>',
        '<img src="http://somewhere.com/here.img"/>',
        'einde'))
    testoutput_2 = ''.join(('begin<img />',
        '<img src="http://www.example.com/hell/here.img"/>',
        '<img src="http://www.example.com/hell/here.img"/>',
        '<img src="http://www.example.com/hell/somewhere/here.img"/>',
        '<img src="http://www.example.com/hell/somewhere/here.img"/>',
        '<img src="http://somewhere.com/here.img"/>',
        'einde'))
    output = r2h.resolve_images(testdata, 'http://www.example.com', '')
    assert output == testoutput_1
    output = r2h.resolve_images(testdata, 'http://www.example.com/', '')
    assert output == testoutput_1
    output = r2h.resolve_images(testdata, 'http://www.example.com/', 'hell')
    assert output == testoutput_2
    output = r2h.resolve_images(testdata, 'http://www.example.com', 'hell/')
    assert output == testoutput_2
    print('ok')

    # TODO: test  format_previewdata


## def setUpModule():
    ## # also init test database
    ## cherrypy.tree.mount(Rst2Html(), '/')
    ## cherrypy.engine.start()
## setup_module = setUpModule

## def tearDownModule():
    ## cherrypy.engine.exit()
## teardown_module = tearDownModule

## class TestCherryPyApp(BaseCherryPyTestCase):

    ## def test_index(self):
        ## response = self.request('/')
        ## self.assertEqual(response.output_status, '200 OK')
        ## # response body is wrapped into a list internally by CherryPy
        ## self.assertEqual(response.body, ['hello world'])


if __name__ == '__main__':
    ## import unittest
    ## unittest.main()
    test_unexposed()
