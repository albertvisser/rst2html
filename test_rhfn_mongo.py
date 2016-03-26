# tests for rst2html_functions
# only test what we've modified
# TODO: build test code for R2hState methods
import os
import subprocess as sp
import pprint
import yaml
import rst2html_functions_mongo as rhfn
from docs2mongo import clear_db as init_db
from test_mongodml import list_database_contents

def test_functions():

    # clear out test data
    testsite = 'test'
    init_db(testsite)
    mirror = os.path.join('/home', 'albert', 'www', 'cherrypy', 'rst2html',
        'rst2html-data', testsite)
    sp.call(['rm', '-R', '{}'.format(mirror)])

    print('creating new site and doing some failure tests on updating...', end=' ')
    new_site = 'test'
    mld = rhfn.new_conf(new_site)
    assert mld == ''
    sett = rhfn.read_conf(new_site)
    assert sett == {'url': '/rst2html-data/test', 'hig': 32, 'lang': 'en',
        'css': [], 'wid': 100}
    mld = rhfn.new_conf('test')
    assert mld == 'Site already exists'
    sett['url'] = 'something else'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == 'Please do not modify the url value'
    sett['url'] = '/rst2html-data/test'
    sett.pop('css')
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == "Config: invalid value for css -  does not exist"
    sett['css'] = []
    sett['hig'] = 'Too high'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == 'Config: invalid value for hig'
    sett['hig'] = 32
    sett['lang'] = 'xx'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == 'Config: invalid value for lang'
    print('ok')

    print('reading and writing conf...', end=' ')
    expected = '<option>-- new --</option><option>test</option>'
    assert rhfn.list_confs() == expected
    expected = '<option>-- new --</option><option selected="selected">test</option>'
    assert rhfn.list_confs('test') == expected

    sitename = rhfn.default_site()
    assert sitename == 'test'
    conf = rhfn.read_conf('not_test')
    assert conf == None
    conf = rhfn.read_conf(sitename)
    expected = {'lang': 'en', 'css': [], 'url': '/rst2html-data/test',
        'wid': 100, 'hig': 32}
    assert conf == expected

    text = rhfn.conf2text(conf)
    expected = "\n".join((
        "css: []",
        "hig: 32",
        "lang: en",
        "url: /rst2html-data/test",
        "wid: 100\n"))
    assert text == expected
    text = text.replace('[]', "['http://www.example.com/test.css']")
    msg = rhfn.save_conf(sitename, text)
    assert msg == ''
    expected = {'hig': 32, 'wid': 100, 'url': '/rst2html-data/test',
        'css': ['http://www.example.com/test.css'], 'lang': 'en'}
    conf = rhfn.read_conf(sitename)
    assert conf == expected
    print('ok')

    print('listing dirs and files...', end=' ')
    naam = 'jansen'
    msg = rhfn.save_src_data(sitename, '', naam,
        'now creating {}'.format(naam), True)
    assert msg == ''
    naam = 'hendriksen'
    msg = rhfn.save_src_data(sitename, 'guichelheil', naam,
        'now creating {}'.format(naam), True)
    assert msg == ''
    naam = 'jansen'
    msg = rhfn.save_html_data(sitename, '', naam,
        '<p>now creating {}</p>'.format(naam))
    assert msg == ''
    naam = 'hendriksen'
    msg = rhfn.save_html_data(sitename, 'guichelheil', naam,
        '<p>now creating {}</p>'.format(naam))
    assert msg == ''
    expected = ['guichelheil/']
    assert rhfn.list_subdirs(sitename) == expected
    assert rhfn.list_subdirs(sitename, 'src') == expected
    assert rhfn.list_subdirs(sitename, 'dest') == expected
    assert rhfn.list_subdirs(sitename, 'other') == expected

    expected_0 = '<option>-- new --</option><option>guichelheil/</option>'
    expected_1 = expected_0 + '<option>jansen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">jansen.rst</option>'
    assert rhfn.list_files(sitename) == expected_1
    naam = ''
    assert rhfn.list_files(sitename, naam=naam) == expected_1
    naam = 'nonexist'
    assert rhfn.list_files(sitename, naam=naam) == expected_0
    naam = 'jansen.rst'
    assert rhfn.list_files(sitename, naam=naam) == expected_2
    current = ''
    assert rhfn.list_files(sitename, current) == expected_1
    current = 'guichelheil'
    expected_0 = '<option>-- new --</option><option>..</option>'
    expected_1 = expected_0 + '<option>hendriksen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">hendriksen.rst</option>'
    expected_3 = expected_0 + '<option selected="selected">hendriksen.html</option>'
    assert rhfn.list_files(sitename, current) == expected_1
    naam = ''
    assert rhfn.list_files(sitename, current, naam) == expected_1
    naam = 'jansen'
    assert rhfn.list_files(sitename, current, naam) == expected_0
    naam = 'hendriksen.rst'
    assert rhfn.list_files(sitename, current, naam) == expected_2
    naam = 'hendriksen.html'
    assert rhfn.list_files(sitename, current, naam) == expected_3
    print('ok')

    print('reading and writing documents...', end = ' ')
    namen = ('', 'jansen', 'jansen.rst', 'jansen.html')
    expected_msg_1 = ('src_name_missing', '', '', 'Not a valid source file name')
    expected_data_1 = ('', 'now creating jansen', 'now creating jansen', '')
    expected_msg_2 = ('html_name_missing', '', 'Not a valid target file name', '')
    expected_data_2 = ('', '<p>now creating jansen</p>', '',
        '<p>now creating jansen</p>')
    expected_msg_3 = ('html_name_missing', '', 'Not a valid html file name', '')
    for ix, naam in enumerate(namen):
        msg, data = rhfn.read_src_data(sitename, '', naam)
        assert msg == expected_msg_1[ix]
        assert data == expected_data_1[ix]
        msg, data = rhfn.read_html_data(sitename, '', naam)
        assert msg == expected_msg_2[ix]
        assert data == expected_data_2[ix]
        msg = rhfn.save_to_mirror(sitename, '', naam)
        ## print(naam, msg)
        assert msg == expected_msg_3[ix]
    namen = ('', 'hendriksen', 'hendriksen.rst', 'hendriksen.html')
    expected_data_1 = ('', 'now creating hendriksen', 'now creating hendriksen', '')
    expected_data_2 = ('', '<p>now creating hendriksen</p>', '',
        '<p>now creating hendriksen</p>')
    for ix, naam in enumerate(namen):
        msg, data = rhfn.read_src_data(sitename, current, naam)
        assert msg == expected_msg_1[ix]
        assert data == expected_data_1[ix]
        msg, data = rhfn.read_html_data(sitename, current, naam)
        assert msg == expected_msg_2[ix]
        assert data == expected_data_2[ix]
        msg = rhfn.save_to_mirror(sitename, current, naam)
        assert msg == expected_msg_3[ix]

    naam = 'tilanus'
    msg = rhfn.save_src_data(sitename, '', naam,
        'now creating {}'.format(naam), True)
    assert msg == ''
    namen = ('', 'tilanus', 'tilanus.rst', 'tilanus.html')
    for ix, naam in enumerate(namen):
        msg = rhfn.save_src_data(sitename, '', naam,
            'now writing {}'.format(naam), False)
        assert msg == expected_msg_1[ix]
        msg = rhfn.save_html_data(sitename, '', naam,
            'now writing <p>{}</p>'.format(naam))
        assert msg == expected_msg_2[ix]
    naam = 'de groot'
    msg = rhfn.save_src_data(sitename, current, naam,
            'now creating {}'.format(naam), True)
    assert msg == ''
    namen = ('', 'de groot', 'de groot.rst', 'de groot.html')
    for ix, naam in enumerate(namen):
        msg = rhfn.save_src_data(sitename, current, naam,
                'now writing {}'.format(naam), False)
        assert msg == expected_msg_1[ix]
        msg = rhfn.save_html_data(sitename, current, naam,
                'now writing <p>{}</p>'.format(naam))
        assert msg == expected_msg_2[ix]
    print('ok')

    print("check_if_rst in various situations...", end=" ")
    msg1 = "supply_text"
    msg2 = "rst_invalid"
    msg3 = "src_name_missing"
    assert rhfn.check_if_rst("", "") == msg1
    assert rhfn.check_if_rst("some text", "") == msg2
    assert rhfn.check_if_rst("some text", "anything") == msg2
    assert rhfn.check_if_rst("some text", rhfn.RST) == ''
    assert rhfn.check_if_rst("<p>some text<p>", rhfn.RST) == ''
    assert rhfn.check_if_rst("some text", rhfn.RST, filename="") == msg3
    assert rhfn.check_if_rst("some text", rhfn.RST, filename="random") == ''
    assert rhfn.check_if_rst("some text", rhfn.RST, filename="random/") == msg3
    assert rhfn.check_if_rst("some text", rhfn.RST, filename="..") == msg3
    assert rhfn.check_if_rst("some text", rhfn.RST, filename="-- new --") == msg3
    print('ok')
    print("check_if_html in various situations:", end=" ")
    msg2 = "load_html"
    msg3 = "html_name_missing"
    assert rhfn.check_if_html("", "") == msg1
    assert rhfn.check_if_html("some text", "") == msg2
    assert rhfn.check_if_html("some text", "anything") == msg2
    assert rhfn.check_if_html("some text", rhfn.HTML) == ''
    assert rhfn.check_if_html("<p>some text<p>", rhfn.HTML) == ''
    assert rhfn.check_if_html("some text", rhfn.HTML, filename="") == msg3
    assert rhfn.check_if_html("some text", rhfn.HTML, filename="random") == ''
    assert rhfn.check_if_html("some text", rhfn.HTML, filename="random/") == msg3
    assert rhfn.check_if_html("some text", rhfn.HTML, filename="..") == msg3
    assert rhfn.check_if_html("some text", rhfn.HTML, filename="-- new --") == msg3
    print('ok')

    print('building progress list and updating all documents...', end=' ')
    # hard to assert-test because it uses actual date-time stamps
    # maybe I should create a separate demo site for this
    # but then the update-all would still be untestable this way
    # so here we just pprint an htmlview the lot
    olddata = rhfn.build_progress_list(sitename)
    ## pprint.pprint(olddata)

    errors = rhfn.update_all(sitename, conf)
    assert errors == [('tilanus', 'mirror_missing'),
        ('de groot', 'mirror_missing')]
    newdata = rhfn.build_progress_list(sitename)
    ## pprint.pprint(newdata)
    # compare newdata with olddata and check for expected differences
    # force creating missing html and mirror documents:
    errors = rhfn.update_all(sitename, conf, missing=True)
    assert errors == []
    print('ok')

    print('building reference document...', end=' ')
    # 1. add references to "jansen", save html and promote to mirror
    naam = 'jansen'
    rhfn.save_src_data(sitename, '', naam, 'bah humbug\n'
        '.. refkey:: ref1: here1\n'
        '.. refkey:: ref2: here2\n'
        'end')
    rhfn.save_html_data(sitename, '', naam, 'updated')
    rhfn.save_to_mirror(sitename, '', naam)
    # 2. add reference s to"tilanus" and save html
    naam = 'tilanus'
    rhfn.save_src_data(sitename, '', naam, 'it`s me Modine\n'
        '.. refkey:: ref3: here3\n')
    rhfn.save_html_data(sitename, '', naam, 'updated')
    # 3. add new document with references
    naam = 'horrorscenario'
    rhfn.save_src_data(sitename, '', naam, '.. refkey:: ref3: here3\n', new=True)
    refs, errs = rhfn.get_reflinks_in_dir(sitename)
    assert refs == {'Ref2': ['jansen.html#here2'], 'Ref1': ['jansen.html#here1']}
    assert errs == []
    # 4. add references to "guichelheil/hendriksen", save html and promote to mirror
    dirnaam = 'guichelheil'
    naam = 'hendriksen'
    rhfn.save_src_data(sitename, dirnaam, naam, 'later krokodil\n'
        '.. refkey:: ref4: here1\n'
        'end')
    rhfn.save_html_data(sitename, dirnaam, naam, 'updated')
    rhfn.save_to_mirror(sitename, dirnaam, naam)
    result = rhfn.build_trefwoordenlijst(sitename)
    assert result == '\n'.join(['Index', '=====', '', '`R`_ ', '', 'R', '-', '',
        '+   Ref1 `#`__ ', '+   Ref2 `#`__ ', ' ',
        '..  _R1: jansen.html#here1', '..  _R2: jansen.html#here2', ' ',
        '__ R1_', '__ R2_', ' '])
    print('ok')

def test_class():
    print('Initializing state... ', end = '')
    state = rhfn.R2hState()
    assert state.sitename == 'test'
    print('ok')

    print('testing currentify... ', end='')
    state.current = ''
    fname = 'blub.rst'
    assert state.currentify(fname) == fname
    dirname = 'fish_goes'
    state.current = dirname
    assert state.currentify(fname) == '/'.join((dirname, fname))
    print('ok')

    print('testing read_conf... ', end='')
    confdata = {'lang': 'en', 'css': ['http://www.example.com/test.css'],
        'url': '/rst2html-data/test', 'wid': 100, 'hig': 32}
    state.subdirs = None
    mld = state.read_conf('test')
    assert mld == ''
    assert state.loaded == 'yaml'
    assert state.conf == confdata
    assert state.subdirs == ['guichelheil/']
    assert state.current == ''
    print('ok')

    print('testing index... ', end='')
    data = state.index()
    confdata = {'hig': 32, 'css': ['http://www.example.com/test.css'],
        'wid': 100, 'url': '/rst2html-data/test', 'lang': 'en'}
    confdata_text = '\n'.join((
        'css:',
        '- http://www.example.com/test.css',
        'hig: 32',
        'lang: en',
        'url: /rst2html-data/test',
        'wid: 100\n'))
    assert data == ('', '', '', 'Settings file is test', confdata_text, 'test')
    assert state.conf == confdata
    assert state.subdirs == ['guichelheil/']
    assert state.current == ''
    assert state.loaded == 'yaml'
    print('ok')

    print('testing loadconf... ', end='')
    data = state.loadconf('test', '', '')                   # ok
    assert data == ('Settings loaded from test', confdata_text, 'test', '')
    assert state.conf == confdata
    assert state.subdirs == ['guichelheil/']
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    data = state.loadconf('test', 'blub', ' to be unchanged') # other conf - fail
    assert data == ('blub does not exist', ' to be unchanged', 'blub', '')
    confdata_2 = {'lang': 'en', 'hig': 32, 'wid': 100,
        'css': ['http://www.example.com/test.css'], 'url': '/rst2html-data/test'}
    assert state.conf == confdata_2
    assert state.subdirs == ['guichelheil/']
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    data = state.loadconf('blub', 'test', 'xx')                   # other conf - ok
    assert data == ('Settings loaded from test', confdata_text, 'test', '')
    confdata_3 = {'css': ['http://www.example.com/test.css'], 'lang': 'en',
        'url': '/rst2html-data/test', 'wid': 100, 'hig': 32}
    assert state.conf == confdata_3
    assert state.subdirs == ['guichelheil/']
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    print('ok')

    print('testing saveconf... ', end='')
    data = state.saveconf('test', '', '')
    assert data == ('Please provide content for text area', 'test', '')
    state.loaded = rhfn.RST
    data = state.saveconf('test', '', 'config text')
    assert data == ("Not executed: text area doesn't contain settings data",
        'test', '')
    state.loaded = rhfn.CONF
    data = state.saveconf('test', '', 'config text')
    assert 'Config: invalid value for' in data[0]
    assert data[1:] == ('test', '')
    data = state.saveconf('test', '', confdata_text)
    confdata_4 = {'wid': 100, 'css': ['http://www.example.com/test.css'],
        'lang': 'en', 'hig': 32, 'url': '/rst2html-data/test'}
    assert data == (confdata_4, 'test', '')
    data = state.saveconf('blub', '', confdata_text)
    assert data == ('blub does not exist', 'blub', '')
    data = state.saveconf('test', 'blub', confdata_text)
    confdata_5 = {'hig': 32, 'lang': 'en', 'url': '/rst2html-data/blub', 'wid': 100,
        'css': []}
    assert data == (confdata_5, 'blub', '')
    print('ok')
    return

    print('testing loadrst... ', end='')
    data = state.loadrst()
    print('ok')

    print('testing saverst... ', end='')
    data = state.saverst()
    print('ok')

    print('testing convert... ', end='')
    data = state.convert()
    print('ok')

    print('testing saveall... ', end='')
    data = state.saveall()
    print('ok')

    print('testing loadhtml... ', end='')
    data = state.loadhtml()
    print('ok')

    print('testing showhtml... ', end='')
    data = state.showhtml()
    print('ok')

    print('testing savehtml... ', end='')
    data = state.savehtml()
    print('ok')

    print('testing copytoroot... ', end='')
    data = state.copytoroot()
    print('ok')

    print('testing makerefdoc... ', end='')
    data = state.makerefdoc()
    print('ok')

    print('testing convert_all... ', end='')
    data = state.convert_all()
    print('ok')

    print('testing overview... ', end='')
    data = state.overview()
    print('ok')

# no need to test these as they are deactivated in the page
    print('testing loadxtra... ', end='')
    data = state.loadxtra()
    print('ok')

    print('testing savextra... ', end='')
    data = state.savextra()
    print('ok')


if __name__ == '__main__':
    test_functions()
    test_class()
    ## list_database_contents()
