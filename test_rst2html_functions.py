# tests for rst2html_functions
# for now only test what we've modified (which is almost everything anyway)
import os
import subprocess as sp
import pprint
import yaml
from app_settings import DML, WEBROOT, SETTFILE
import rst2html_functions_all as rhfn
from test_dml import list_site_contents, clear_site_contents

def sorted_items(input_dict):
    return [(x, y) for x, y in sorted(input_dict.items())]

confdata = {'hig': 32, 'css': ['http://www.example.com/test.css'],
    'wid': 100, 'url': 'http:///rst2html-data/test', 'lang': 'en'}
confdata_text = '\n'.join((
    'css:',
    '- http://www.example.com/test.css',
    'hig: 32',
    'lang: en',
    'url: http:///rst2html-data/test',
    'wid: 100\n'
    ))
confdata_text_2 = '\n'.join((
    'hig: 32',
    'lang: en',
    'url: http:///rst2html-data/test',
    'wid: 100\n',
    'css:',
    '- http://www.example.com/test.css'
    ))
other_confdata = {'lang': 'en', 'hig': 32, 'wid': 100,'css': [],
    'url': 'http:///rst2html-data/blub'}
other_confdata_text = '\n'.join((
    'css: []',
    'hig: 32',
    'lang: en',
    'url: http:///rst2html-data/blub',
    'wid: 100\n'
    ))
newconfdata = {'lang': 'en', 'css': [], 'hig': 32, 'url': '', 'wid': 100}
newconfdata_text = '\n'.join((
    'css: []',
    'hig: 32',
    'lang: en',
    "url: ''",
    'wid: 100\n'
    ))
expected_overview = [
    ('/', 'horrorscenario', 0),
    ('/', 'jansen', 2),
    ('/', 'pietersen', 1),
    ('/', 'python', 0),
    ('/', 'reflist', 2),
    ('/', 'tilanus', 2),
    ('guichelheil', 'de groot', 2),
    ('guichelheil', 'hendriksen', 2)
    ]
jansen_txt = """bah humbug
.. refkey:: ref1: here1
.. refkey:: ref2: here2
end"""
converted_txt = """\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="generator" content="Docutils 0.11: http://docutils.sourceforge.net/" />
<title></title>

</head>
<body>
<div class="document">


<p>hallo vriendjes</p>
</div>
</body>
</html>
"""
pietersen_txt = 'hallo vriendjes'

def test_new_site(sitename):
    print('creating new site and doing some failure tests on updating...', end=' ')
    new_site = sitename
    mld = rhfn.new_conf(sitename)
    assert mld == ''
    mld, sett = rhfn.read_conf(sitename)
    assert mld == ''
    assert sett == {}
    mld = rhfn.new_conf('test')
    assert mld == 'Site already exists'
    sett = {x:y for x, y in rhfn.DFLT_CONF.items()}
    ## sett['url'] = 'something else'
    ## mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    ## assert mld == 'Please do not modify the url value'
    sett['url'] = '/rst2html-data/test'
    ## sett.pop('css')
    ## mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    ## assert mld == "Config: invalid value for css -  does not exist"
    ## sett['css'] = []
    sett['hig'] = 'Too high'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == 'Config: invalid value for hig'
    sett['hig'] = 32
    sett['lang'] = 'xx'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == 'Config: invalid value for lang'
    sett['lang'] = 'en'
    mld = rhfn.save_conf(new_site, rhfn.conf2text(sett))
    assert mld == ''
    print('ok')

def test_readwrite_conf(sitename):
    print('reading and writing conf...', end=' ')
    expected = '<option>test</option>'
    assert expected in rhfn.list_confs()
    expected = '<option selected="selected">test</option>'
    assert expected in rhfn.list_confs('test')
    ## sitename = rhfn.default_site()
    ## assert sitename == 'test'
    mld, conf = rhfn.read_conf('not_test')
    assert mld == 'no_such_sett'
    assert conf == None
    mld, conf = rhfn.read_conf(sitename)
    assert mld == ''
    expected = {'url': 'http:///rst2html-data/test',
        'wid': 100, 'css': [], 'hig': 32, 'lang': 'en'}
    assert sorted_items(conf) == sorted_items(expected)

    text = rhfn.conf2text(conf)
    expected = "\n".join((
        "css: []",
        "hig: 32",
        "lang: en",
        "url: http:///rst2html-data/test",
        "wid: 100\n"))
    assert text == expected
    text = text.replace('[]', "['http://www.example.com/test.css']")
    msg = rhfn.save_conf(sitename, text)
    assert msg == ''
    expected = {'hig': 32, 'wid': 100, 'url': 'http:///rst2html-data/test',
        'css': ['http://www.example.com/test.css'], 'lang': 'en'}
    mld, conf = rhfn.read_conf(sitename)
    assert mld == ''
    assert sorted_items(conf) == sorted_items(expected)
    print('ok')
    return conf

def test_list_files(sitename):
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

    # nonexistent site
    data = rhfn.list_subdirs('oink')
    assert data == []
    # nonexistent subdir
    data = rhfn.list_files(sitename, 'blub', '', '', 'en')
    assert data == 'Directory `blub` not found'

    expected_0 = '<option>guichelheil/</option>'
    expected_1 = expected_0 + '<option>jansen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">jansen.rst</option>'
    expected_3 = expected_0 + '<option>jansen.html</option>'
    expected_4 = expected_0 + '<option selected="selected">jansen.html</option>'
    assert rhfn.list_files(sitename) == expected_1
    assert rhfn.list_files(sitename, ext='src') == expected_1
    assert rhfn.list_files(sitename, ext='dest') == expected_3
    naam = ''
    assert rhfn.list_files(sitename, naam=naam) == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='src') == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='dest') == expected_3
    naam = 'nonexist'
    assert rhfn.list_files(sitename, naam=naam) == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='src') == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='dest') == expected_3
    naam = 'jansen.rst'
    assert rhfn.list_files(sitename, naam=naam) == expected_2
    assert rhfn.list_files(sitename, naam=naam, ext='src') == expected_2
    assert rhfn.list_files(sitename, naam=naam, ext='dest') == expected_3
    naam = 'jansen.html'
    assert rhfn.list_files(sitename, naam=naam) == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='src') == expected_1
    assert rhfn.list_files(sitename, naam=naam, ext='dest') == expected_4
    current = ''
    assert rhfn.list_files(sitename, current) == expected_1
    assert rhfn.list_files(sitename, current, ext='src') == expected_1
    assert rhfn.list_files(sitename, current, ext='dest') == expected_3
    current = 'guichelheil'
    expected_0 = '<option>..</option>'
    expected_1 = expected_0 + '<option>hendriksen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">hendriksen.rst</option>'
    expected_3 = expected_0 + '<option>hendriksen.html</option>'
    expected_4 = expected_0 + '<option selected="selected">hendriksen.html</option>'
    assert rhfn.list_files(sitename, current) == expected_1
    assert rhfn.list_files(sitename, current, ext='src') == expected_1
    assert rhfn.list_files(sitename, current, ext='dest') == expected_3
    naam = ''
    assert rhfn.list_files(sitename, current, naam) == expected_1
    assert rhfn.list_files(sitename, current, naam, ext='src' ) == expected_1
    assert rhfn.list_files(sitename, current, naam, ext='dest') == expected_3
    naam = 'jansen'
    assert rhfn.list_files(sitename, current, naam) == expected_1
    assert rhfn.list_files(sitename, current, naam, ext='src' ) == expected_1
    assert rhfn.list_files(sitename, current, naam, ext='dest') == expected_3
    naam = 'hendriksen.rst'
    assert rhfn.list_files(sitename, current, naam) == expected_2
    assert rhfn.list_files(sitename, current, naam, 'src') == expected_2
    assert rhfn.list_files(sitename, current, naam, 'dest') == expected_3
    naam = 'hendriksen.html'
    assert rhfn.list_files(sitename, current, naam) == expected_1
    assert rhfn.list_files(sitename, current, naam, 'src') == expected_1
    assert rhfn.list_files(sitename, current, naam, 'dest') == expected_4

    msg = rhfn.make_new_dir(sitename, 'moerasspiraea')
    assert msg == ''
    msg = rhfn.make_new_dir(sitename, 'moerasspiraea')
    assert msg == 'dir_name_taken'
    print('ok')
    return current

def test_readwrite_docs(sitename, current):
    print('reading and writing documents...', end = ' ')
    namen = ('', 'jansen', 'jansen.rst', 'jansen.html')
    expected_msg_1 = ('src_name_missing', '', '', 'rst_filename_error')
    expected_data_1 = ('', 'now creating jansen', 'now creating jansen', '')
    expected_msg_2 = ('html_name_missing', '', 'html_filename_error', '')
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

def test_check_formats(sitename, current):
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

def test_progress_list(sitename, current, conf):
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

def test_reference_list(sitename, current):
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


def test_state_class():
    print('Testing state class:')
    state = rhfn.R2hState()
    ## assert state.sitename == 'test'

    print('testing currentify... ', end='')
    state.current = ''
    fname = 'blub.rst'
    assert state.currentify(fname) == fname
    dirname = 'fish_goes'
    state.current = dirname
    assert state.currentify(fname) == '/'.join((dirname, fname))
    print('ok')

    print('testing read_conf... ', end='')
    state.subdirs = None
    mld = state.read_conf('test')
    assert mld == ''
    assert state.loaded == 'yaml'
    assert sorted_items(state.conf) == sorted_items(confdata)
    assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert state.current == ''
    print('ok')

    return state

def test_index(state):
    print('testing index... ', end='')

    initial_site = state.sitename
    data = state.index()
    assert data[:4] == ('', '', '', 'Settings file is {}'.format(initial_site))
    assert data[-1] == initial_site
    ## assert sorted_items(state.conf) == sorted_items(confdata)
    ## assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert state.current == ''
    assert state.loaded == 'yaml'

    print('ok')
    return state

def test_load_conf(state):
    print('testing loadconf... ', end='')

    data = state.loadconf('-- new --', '')
    assert data == ('New site will be created on save', newconfdata_text,
        '-- new --', '')
    assert sorted_items(state.conf) == sorted_items(newconfdata)
    assert state.subdirs == []
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == '-- new --'
    assert state.newconf is True

    data = state.loadconf('test', '')
    assert data == ('Settings loaded from test', confdata_text, 'test', '')
    assert sorted_items(state.conf) == sorted_items(confdata)
    assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    assert state.newconf is False

    data = state.loadconf('test', 'blub') # other conf - fail
    assert data == ('blub does not exist', confdata_text, 'test', '')
    assert sorted_items(state.conf) == sorted_items(confdata)
    assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    assert state.newconf is False

    data = state.loadconf('blub', 'test')                   # other conf - ok
    assert data == ('Settings loaded from test', confdata_text, 'test', '')
    assert sorted_items(state.conf) == sorted_items(confdata)
    assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert state.current == ''
    assert state.loaded == 'yaml'
    assert state.sitename == 'test'
    assert state.newconf is False

    print('ok')
    return state

def test_save_conf(state):
    print('testing saveconf... ', end='')
    last_sett = state.sitename

    data = state.saveconf('test', '', '')
    assert data == ('Please provide content for text area', '', last_sett, '')

    state.loaded = rhfn.RST
    data = state.saveconf('test', '', 'config text')
    assert data == ("Not executed: text area doesn't contain settings data",
        'config text', last_sett, '')

    state.loaded = rhfn.CONF
    data = state.saveconf('test', '', 'config text')
    assert 'Config: invalid value for' in data[0]
    assert data[1:] == ('config text', 'test', '')

    data = state.saveconf('test', '', confdata_text)
    assert data == ('Settings opgeslagen als test', confdata_text, 'test', '')

    data = state.saveconf('blub', '', confdata_text)
    assert data == ('blub does not exist', confdata_text, 'test', '')

    state.newconf = True
    data = state.saveconf('test', 'blub', newconfdata_text)
    assert data == ('Settings opgeslagen als blub', other_confdata_text, 'blub', '')

    print('ok')
    return state

def test_loadrst(state):
    print('testing loadrst... ', end='')

    state.sitename = 'test'
    data = state.loadrst('')
    assert data == ('Oops! Page was probably open on closing the browser',
        other_confdata_text, '', '')
    assert state.current == ''
    assert state.loaded == rhfn.CONF
    assert state.oldtext == other_confdata_text

    data = state.loadrst('-- new --')
    assert data == ("Don't forget to supply a new filename on saving", '', '', '')
    assert state.current == ''
    assert state.loaded == rhfn.RST
    assert state.oldtext == ''

    data = state.loadrst('guichelheil/')
    assert data == ('switching to directory guichelheil', '', '', '')
    assert state.current == 'guichelheil'
    assert state.loaded == rhfn.RST
    assert state.oldtext == ''

    data = state.loadrst('..')
    assert data == ('switching to parent directory', '', '', '')
    assert state.current == ''
    assert state.loaded == rhfn.RST
    assert state.oldtext == ''

    data = state.loadrst('jansen.rst')
    assert data == ('Source file jansen.rst loaded', jansen_txt, 'jansen.html', '')
    assert state.current == ''
    assert state.loaded == rhfn.RST
    assert state.oldtext == jansen_txt

    data = state.loadrst('jansen')
    assert data == ('Source file jansen loaded', jansen_txt, 'jansen.html', '')
    assert state.current == ''
    assert state.loaded == rhfn.RST
    assert state.oldtext == jansen_txt

    data = state.loadrst('jansen.html')
    assert data == ('Not executed: not a valid source file name', jansen_txt,
        'jansen.html', '')
    assert state.current == ''
    assert state.loaded == rhfn.RST
    assert state.oldtext == jansen_txt

    print('ok')
    return state

def test_saverst(state):
    print('testing saverst... ', end='')

    data = state.saverst('jansen.rst', '', 'hallo vriendjes')
    assert data == ('Rst source saved as jansen.rst',
        'jansen.rst', 'jansen.html', '')

    data = state.saverst('jansen', '', 'hallo vriendjes')
    assert data == ('Rst source saved as jansen.rst',
        'jansen.rst', 'jansen.html', '')

    data = state.saverst('jansen.rst', 'monty/', 'my hovercraft is full of eels')
    assert data == ('New subdirectory monty created', 'monty/', 'jansen.html', '')

    state.rstfile = 'jansen.rst'
    data = state.saverst('monty/', '', 'my hovercraft is full of eels')
    assert data == ('Subdirectory monty already exists',
        'jansen.rst', 'jansen.html', '')

    data = state.saverst('jansen.rst', 'python', 'my hovercraft is full of eels')
    assert data == ('Rst source saved as python.rst', 'python.rst', 'python.html',
        '')

    state.loaded = rhfn.CONF
    data = state.saverst('jansen.rst', '', 'hallo vriendjes')
    assert data == ("Not executed: text area doesn't contain restructured text",
        'python.rst', 'python.html', '')

    print('ok')
    return state

def test_convert(state):
    print('testing convert... ', end='')
    state.oldtext = 'hallo vriendjes'
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert data == ("Not executed: text area doesn't contain restructured text",
        '', '')
    state.loaded = rhfn.RST
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert data == ('', converted_txt, 'jansen.rst')
    data = state.convert('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert data == ('', converted_txt, 'pietersen.rst')
    state.oldtext = 'something else'
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert data == ('', converted_txt, 'jansen.rst')
    data = state.convert('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert data == ('Source file does not exist', '', '')
    print('ok')
    return state

def test_saveall(state):
    print('testing saveall... ', end='')
    state.oldtext = 'hallo vriendjes'
    state.loaded = rhfn.HTML
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert data == ("Not executed: text area doesn't contain restructured text",
        'python.rst', 'python.html', '')
    state.loaded = rhfn.RST
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert data == ('Rst converted to html and saved as jansen.html',
        'jansen.rst', 'jansen.html', '')
    data = state.saveall('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert data == ('Rst converted to html and saved as pietersen.html',
        'pietersen.rst', 'pietersen.html', '')
    state.oldtext = 'something else'
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert data == ('Rst converted to html and saved as jansen.html',
        'jansen.rst', 'jansen.html', '')
    data = state.saveall('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert data == ('Source file already exists', 'pietersen.rst',
        'pietersen.html', '')   # is this ok? It is meant to be a safeguard against using an
        # existing name in a "save as" operation
    print('ok')
    return state

def test_loadhtml(state):
    print('testing loadhtml... ', end='')
    data = state.loadhtml('')
    assert data == ('Please enter or select a target (.html) filename',
        pietersen_txt, 'pietersen.rst', 'pietersen.html')
    data = state.loadhtml('..')
    assert data == ('Please enter or select a target (.html) filename',
        pietersen_txt, 'pietersen.rst', 'pietersen.html')
    data = state.loadhtml('guichelheil/')
    assert data == ('Please enter or select a target (.html) filename',
        pietersen_txt, 'pietersen.rst', 'pietersen.html')
    data = state.loadhtml('-- new --')
    assert data == ('Please enter or select a target (.html) filename',
        pietersen_txt, 'pietersen.rst', 'pietersen.html')
    data = state.loadhtml('jansen')
    assert data == ('Target html jansen.html loaded', converted_txt, 'jansen.rst',
        'jansen.html')
    data = state.loadhtml('jansen.html')
    assert data == ('Target html jansen.html loaded', converted_txt, 'jansen.rst',
        'jansen.html')
    data = state.loadhtml('jansen.rst')
    assert data == ('Not executed: not a valid target file name', converted_txt,
        'jansen.rst', 'jansen.html')
    print('ok')
    return state

def test_showhtml(state):
    print('testing showhtml... ', end='')
    state.htmlfile = 'jansen.html'
    state.loaded = rhfn.RST
    data = state.showhtml(converted_txt)
    assert data == ('Please load HTML first', '', '')
    state.loaded = rhfn.HTML
    data = state.showhtml(converted_txt)
    assert data == ('', converted_txt, 'jansen.html')
    print('ok')
    return state

def test_savehtml(state):
    print('testing savehtml... ', end='')
    state.loaded = rhfn.RST
    data = state.savehtml('jansen.html', converted_txt)
    assert data == ('Please load HTML first', converted_txt, '')
    state.loaded = rhfn.HTML
    data = state.savehtml('jansen.html', converted_txt)
    assert data == ('Modified HTML saved as jansen.html', converted_txt, '')
    print('ok')
    return state

def test_copytoroot(state):
    print('testing copytoroot... ', end='')
    state.loaded = rhfn.RST
    data = state.copytoroot('jansen.html', converted_txt)
    assert data == 'Please load HTML first'
    state.loaded = rhfn.HTML
    data = state.copytoroot('jansen.html', converted_txt)
    assert data == 'Copied to siteroot/jansen.html'
    print('ok')
    return state

def test_makerefdoc(state):
    print('testing makerefdoc... ', end='')
    data = state.makerefdoc()
    assert data == ('Index created as reflist.html', 'Index\n=====\n\n')
    print('ok')
    return state

def test_convert_all(state):
    # not much more than receiving the results of the earlier tested update_all
    print('testing convert_all... ', end='')
    mld, data = state.convert_all()
    assert mld == 'Site documents regenerated, messages below'
    test = data.split('\n')
    assert sorted(test) == sorted(('pietersen not present at mirror',
        'python skipped: not in target directory',
        'horrorscenario skipped: not in target directory'))
    print('ok')
    return state

def test_overview(state):
    print('testing overview... ', end='')
    # not much more than receiving the results of the earlier tested build_progress_list
    data = state.overview()
    # this yields time-dependent data so we can't do a simple assert on it:
    ## print(data)
    assert sorted([item[:3] for item in data]) == sorted(expected_overview)
    print('ok')
    return state

def test_loadxtra(state):
    print('testing loadxtra... ', end='')
    data = state.loadxtra()
    print('ok')
    return state

def test_savextra(state):
    print('testing savextra... ', end='')
    data = state.savextra()
    print('ok')


def main():
    sitename = 'test'
    clear_site_contents(sitename)
    clear_site_contents('blub')

    ## test_functions_setup(sitename)
    test_new_site(sitename)
    conf = test_readwrite_conf(sitename)
    current = test_list_files(sitename)
    test_readwrite_docs(sitename, current)
    test_check_formats(sitename, current)
    test_progress_list(sitename, current, conf)
    test_reference_list(sitename, current)

    state = test_state_class()
    state = test_index(state)
    state = test_load_conf(state)
    state = test_save_conf(state)
    state = test_loadrst(state)
    state = test_saverst(state)
    state = test_convert(state)
    state = test_saveall(state)
    state = test_loadhtml(state)
    state = test_showhtml(state)
    state = test_savehtml(state)
    state = test_copytoroot(state)
    state = test_makerefdoc(state)
    state = test_convert_all(state)
    state = test_overview(state)
    # no need to test these as they are deactivated in the page
    ## state = test_loadxtra(state)
    ## state = test_savextra(state)

    ## list_site_contents(sitename)
    clear_site_contents(sitename)
    clear_site_contents('blub')


if __name__ == '__main__':
    main()
