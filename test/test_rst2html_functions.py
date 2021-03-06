"""unit tests for functions in rst2html_functions.py
"""
# for now only test what we've modified (which is almost everything anyway)
import os
import sys
## import subprocess as sp
import pprint
## import yaml
import pathlib
HERE = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from app_settings import DML, WEBROOT, BASIC_CSS
import rst2html_functions as rhfn
from test_dml import list_site_contents, clear_site_contents

confdata = {'hig': 32, 'css': ['http://www.example.com/test.css'],
            'wid': 100, 'url': 'http://www.example.com', 'lang': 'en'}
confdata_text_init = '\n'.join(('css:',
                                '- http://www.example.com/test.css',
                                'hig: 32',
                                'lang: en',
                                'url: http://www.example.com',
                                'wid: 100\n'))
confdata_text = '\n'.join(('css:',
                           '- url + test.css',
                           'hig: 32',
                           'lang: en',
                           'url: http://www.example.com',
                           'wid: 100\n'))
confdata_text_2 = '\n'.join(('hig: 32',
                             'lang: en',
                             'url: /rst2html-data/test',
                             'wid: 100\n',
                             'css:',
                             '- http://www.example.com/test.css'))
confdata_extra = {x: y for x, y in confdata.items()}
confdata_extra.update(
    {'starthead': '<!-- starthead -->', 'endhead': '<!-- endhead -->'})
other_confdata = {'lang': 'en', 'hig': 32, 'wid': 100, 'css': [], 'url': ''}
other_confdata_text = '\n'.join((
    'css:' + ''.join(['\n- url + {}'.format(x) for x in BASIC_CSS]),
    'hig: 32',
    'lang: en',
    "url: ''",
    'wid: 100\n'))
newconfdata = {'lang': 'en', 'css': [], 'hig': 32, 'url': '', 'wid': 100}
newconfdata_text = '\n'.join(('css: []',
                              'hig: 32',
                              'lang: en',
                              "url: ''",
                              'wid: 100\n'))
expected_overview = [('/', 'cleese', 0),
                     ('/', 'horrorscenario', 0),
                     ('/', 'jansen', 2),
                     ('/', 'pietersen', 1),
                     ('/', 'reflist', 2),
                     ('/', 'renamed', 2),
                     ('/', 'tilanus', 2),
                     ('guichelheil', 'de groot', 2),
                     ('guichelheil', 'hendriksen', 2)]
jansen_txt = """bah humbug
.. refkey:: ref1: here1
.. refkey:: ref2: here2
end"""
csslink = '<link rel="stylesheet" href="{}" type="text/css" />'
converted_css = '\n'.join([csslink.format('url + ' + x) for x in BASIC_CSS])
converted_txt = """\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="generator" content="Docutils 0.14: http://docutils.sourceforge.net/" />
<title>&lt;string&gt;</title>
{}
</head>
<body>
<div class="document">


<p>hallo vriendjes</p>
</div>
</body>
</html>
""".format(converted_css)
pietersen_txt = 'hallo vriendjes'


def sorted_items(input_dict):
    """sort data for easier comparison"""
    return [(x, y) for x, y in sorted(input_dict.items())]


def assert_equal(left, right):
    """compare terms and display if not equal
    """
    try:
        assert left == right
    except AssertionError:
        print()
        print(left)
        print('   is ongelijk aan')
        print(right)
        raise


def test_new_site(sitename):
    """creating new site and doing some failure tests on updating"""
    print(test_new_site.__doc__ + '...', end=' ')
    mld = rhfn.new_conf(sitename)
    assert_equal(mld, '')
    mld, sett = rhfn.read_conf(sitename)
    assert_equal(mld, '')
    assert_equal(sett, {})
    mld = rhfn.new_conf('test')
    assert_equal(mld, 'site_name_taken')
    sett = {x: y for x, y in rhfn.DFLT_CONF.items()}
    mld = rhfn.save_conf(sitename, rhfn.conf2text(sett))
    mld, sett = rhfn.read_conf(sitename)

    sett['hig'] = 'Too high'
    mld = rhfn.save_conf(sitename, rhfn.conf2text(sett))
    assert_equal(mld, 'Config: invalid value for hig')
    sett['hig'] = 32
    sett['lang'] = 'xx'
    mld = rhfn.save_conf(sitename, rhfn.conf2text(sett))
    assert_equal(mld, 'Config: invalid value for lang')
    sett['lang'] = 'en'
    sett['url'] = 'http://www.example.com'
    mld = rhfn.save_conf(sitename, rhfn.conf2text(sett))
    assert_equal(mld, '')
    rhfn.init_css(sitename)
    mld, conf = rhfn.read_conf(sitename)
    for item in BASIC_CSS:
        test = WEBROOT / sitename / item
        assert 'url + ' + item in conf['css']
        assert test.exists()
    print('ok')


def test_readwrite_conf(sitename):
    """reading and writing conf"""
    print(test_readwrite_conf.__doc__ + '...', end=' ')
    expected = '<option>test</option>'
    assert expected in rhfn.list_confs()
    expected = '<option selected="selected">test</option>'
    assert expected in rhfn.list_confs('test')
    ## sitename = rhfn.default_site()
    ## assert sitename == 'test'
    mld, conf = rhfn.read_conf('not_test')
    assert_equal(mld, 'no_such_sett')
    assert conf is None
    mld, conf = rhfn.read_conf(sitename)
    assert_equal(mld, '')
    expected = {'url': 'http://www.example.com', 'wid': 100, 'hig': 32,
                'lang': 'en', 'css': ['url + {}'.format(x) for x in BASIC_CSS]}
    assert_equal(sorted_items(conf), sorted_items(expected))

    text = rhfn.conf2text(conf)
    css = ''.join(['\n- url + {}'.format(x) for x in BASIC_CSS])
    expected = "\n".join(("css:{}".format(css),
                          "hig: 32",
                          "lang: en",
                          "url: http://www.example.com",
                          "wid: 100\n"))
    assert_equal(text, expected)
    mld = rhfn.save_conf(sitename, confdata_text)
    assert_equal(mld, '')
    print('ok')
    return conf


def test_list_files(sitename):
    """listing dirs and files"""
    print(test_list_files.__doc__ + '...', end=' ')
    naam = 'jansen'
    msg = rhfn.save_src_data(sitename, '', naam,
                             'now creating {}'.format(naam), True)
    assert_equal(msg, '')
    naam = 'hendriksen'
    msg = rhfn.save_src_data(sitename, 'guichelheil', naam,
                             'now creating {}'.format(naam), True)
    assert_equal(msg, '')

    naam = 'jansen'
    msg = rhfn.save_html_data(sitename, '', naam,
                              '<p>now creating {}</p>'.format(naam))
    assert_equal(msg, '')
    naam = 'hendriksen'
    msg = rhfn.save_html_data(sitename, 'guichelheil', naam,
                              '<p>now creating {}</p>'.format(naam))
    assert_equal(msg, '')
    expected = ['guichelheil/']
    assert_equal(rhfn.list_subdirs(sitename), expected)
    assert_equal(rhfn.list_subdirs(sitename, 'src'), expected)
    assert_equal(rhfn.list_subdirs(sitename, 'dest'), expected)
    assert_equal(rhfn.list_subdirs(sitename, 'other'), expected)

    # nonexistent site
    data = rhfn.list_subdirs('oink')
    assert_equal(data, [])
    # nonexistent subdir
    data = rhfn.list_files(sitename, 'blub', '', '', 'en')
    assert_equal(data, '<option>..</option>')  # 'Directory `blub` not found'

    expected_0 = '<option>guichelheil/</option>'
    expected_1 = expected_0 + '<option>jansen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">jansen.rst</option>'
    expected_3 = expected_0 + '<option>jansen.html</option>'
    expected_4 = expected_0 + '<option selected="selected">jansen.html</option>'
    assert_equal(rhfn.list_files(sitename), expected_1)
    assert_equal(rhfn.list_files(sitename, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, ext='src', deleted=True), [])
    assert_equal(rhfn.list_files(sitename, ext='dest'), expected_3)
    assert_equal(rhfn.list_files(sitename, ext='dest', deleted=True), [])
    naam = ''
    assert_equal(rhfn.list_files(sitename, naam=naam), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='dest'), expected_3)
    naam = 'nonexist'
    assert_equal(rhfn.list_files(sitename, naam=naam), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='dest'), expected_3)
    naam = 'jansen.rst'
    assert_equal(rhfn.list_files(sitename, naam=naam), expected_2)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='src'), expected_2)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='dest'), expected_3)
    naam = 'jansen.html'
    assert_equal(rhfn.list_files(sitename, naam=naam), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, naam=naam, ext='dest'), expected_4)
    current = ''
    assert_equal(rhfn.list_files(sitename, current), expected_1)
    assert_equal(rhfn.list_files(sitename, current, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, current, ext='dest'), expected_3)
    current = 'guichelheil'
    expected_0 = '<option>..</option>'
    expected_1 = expected_0 + '<option>hendriksen.rst</option>'
    expected_2 = expected_0 + '<option selected="selected">hendriksen.rst</option>'
    expected_3 = expected_0 + '<option>hendriksen.html</option>'
    expected_4 = expected_0 + '<option selected="selected">hendriksen.html</option>'
    assert_equal(rhfn.list_files(sitename, current), expected_1)
    assert_equal(rhfn.list_files(sitename, current, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, current, ext='src', deleted=True), [])
    assert_equal(rhfn.list_files(sitename, current, ext='dest'), expected_3)
    assert_equal(rhfn.list_files(sitename, current, ext='dest', deleted=True), [])
    naam = ''
    assert_equal(rhfn.list_files(sitename, current, naam), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, ext='dest'), expected_3)
    naam = 'jansen'
    assert_equal(rhfn.list_files(sitename, current, naam), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, ext='src'), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, ext='dest'), expected_3)
    naam = 'hendriksen.rst'
    assert_equal(rhfn.list_files(sitename, current, naam), expected_2)
    assert_equal(rhfn.list_files(sitename, current, naam, 'src'), expected_2)
    assert_equal(rhfn.list_files(sitename, current, naam, 'dest'), expected_3)
    naam = 'hendriksen.html'
    assert_equal(rhfn.list_files(sitename, current, naam), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, 'src'), expected_1)
    assert_equal(rhfn.list_files(sitename, current, naam, 'dest'), expected_4)

    msg = rhfn.make_new_dir(sitename, 'moerasspiraea')
    assert_equal(msg, '')
    msg = rhfn.make_new_dir(sitename, 'moerasspiraea')
    assert_equal(msg, 'dir_name_taken')
    print('ok')
    return current


def test_readwrite_docs(sitename, current):
    """reading and writing documents"""
    print(test_readwrite_docs.__doc__ + '...', end=' ')
    expected_msg_1 = ('src_name_missing', '', '', 'rst_filename_error')
    expected_data_1 = ('', 'now creating jansen', 'now creating jansen', '')
    expected_msg_2 = ('html_name_missing', '', 'html_filename_error', '')
    expected_data_2 = ('', '<p>now creating jansen</p>', '',
                       '<p>now creating jansen</p>')
    expected_msg_3 = ('html_name_missing', '', 'Not a valid html file name', '')
    namen = ('', 'jansen', 'jansen.rst', 'jansen.html')
    for ix, naam in enumerate(namen):
        msg, data = rhfn.read_src_data(sitename, '', naam)
        assert_equal(msg, expected_msg_1[ix])
        assert_equal(data, expected_data_1[ix])
        msg, data = rhfn.read_html_data(sitename, '', naam)
        assert_equal(msg, expected_msg_2[ix])
        assert_equal(data, expected_data_2[ix])
        msg = rhfn.save_to_mirror(sitename, '', naam, confdata_extra)
        ## print(naam, msg)
        assert_equal(msg, expected_msg_3[ix])
    namen = ('', 'hendriksen', 'hendriksen.rst', 'hendriksen.html')
    expected_data_1 = ('', 'now creating hendriksen', 'now creating hendriksen', '')
    expected_data_2 = ('', '<p>now creating hendriksen</p>', '',
                       '<p>now creating hendriksen</p>')
    for ix, naam in enumerate(namen):
        msg, data = rhfn.read_src_data(sitename, current, naam)
        assert_equal(msg, expected_msg_1[ix])
        assert_equal(data, expected_data_1[ix])
        msg, data = rhfn.read_html_data(sitename, current, naam)
        assert_equal(msg, expected_msg_2[ix])
        assert_equal(data, expected_data_2[ix])
        msg = rhfn.save_to_mirror(sitename, current, naam, confdata_extra)
        assert_equal(msg, expected_msg_3[ix])

    naam = 'tilanus'
    msg = rhfn.save_src_data(sitename, '', naam,
                             'now creating {}'.format(naam), True)
    assert_equal(msg, '')
    namen = ('', 'tilanus', 'tilanus.rst', 'tilanus.html')
    for ix, naam in enumerate(namen):
        msg = rhfn.save_src_data(sitename, '', naam,
                                 'now writing {}'.format(naam), False)
        assert_equal(msg, expected_msg_1[ix])
        msg = rhfn.save_html_data(sitename, '', naam,
                                  '<p>now writing {}</p>'.format(naam))
        assert_equal(msg, expected_msg_2[ix])
    naam = 'de groot'
    msg = rhfn.save_src_data(sitename, current, naam,
                             'now creating {}'.format(naam), True)
    assert_equal(msg, '')
    namen = ('', 'de groot', 'de groot.rst', 'de groot.html')
    for ix, naam in enumerate(namen):
        msg = rhfn.save_src_data(sitename, current, naam,
                                 'now writing {}'.format(naam), False)
        assert_equal(msg, expected_msg_1[ix])
        msg = rhfn.save_html_data(sitename, current, naam,
                                  '<p>now writing {}</p>'.format(naam))
        assert_equal(msg, expected_msg_2[ix])
    print('ok')


def test_rename_delete_docs(sitename, current):
    """renaming and deleting documents"""
    print(test_rename_delete_docs.__doc__ + '...', end=' ')
    # create new source document and add contents
    naam_o, naam_r = 'to_rename', 'renamed'
    data_r = 'now creating {}'.format(naam_o)
    data_rh = '<p>{}</p>'.format(data_r)
    msg = rhfn.save_src_data(sitename, '', naam_o, data_r, True)
    assert_equal(msg, '')
    assert naam_o in rhfn.list_files(sitename, '', ext='src')
    # rename by marking old name as deleted and saving contents under new name
    msg = rhfn.save_src_data(sitename, '', naam_r, data_r, True)
    assert_equal(msg, '')
    msg = rhfn.mark_deleted(sitename, '', naam_o)
    assert_equal(msg, '')
    assert naam_o not in rhfn.list_files(sitename, '', ext='src')
    assert naam_o in rhfn.list_files(sitename, '', ext='src', deleted=True)
    assert naam_r in rhfn.list_files(sitename, '', ext='src')
    # create and delete document
    naam_d = 'to_delete'
    data_d = 'now creating {}'.format(naam_d)
    data_dh = '<p>{}</p>'.format(data_d)
    msg = rhfn.save_src_data(sitename, '', naam_d, data_d, True)
    assert_equal(msg, '')
    assert naam_d in rhfn.list_files(sitename, '', ext='src')
    msg = rhfn.mark_deleted(sitename, '', naam_d)
    assert_equal(msg, '')
    assert naam_d not in rhfn.list_files(sitename, '', ext='src')
    assert naam_d in rhfn.list_files(sitename, '', ext='src', deleted=True)
    # move rename/delete to target and check
    assert naam_o not in rhfn.list_files(sitename, '', ext='dest')
    assert naam_r not in rhfn.list_files(sitename, '', ext='dest')
    assert naam_d not in rhfn.list_files(sitename, '', ext='dest')
    msg = rhfn.save_html_data(sitename, '', naam_r, data_rh)
    assert_equal(msg, '')
    assert naam_o not in rhfn.list_files(sitename, '', ext='dest')
    assert naam_o in rhfn.list_files(sitename, '', ext='dest', deleted=True)
    assert naam_o not in rhfn.list_files(sitename, '', ext='src', deleted=True)
    assert naam_r in rhfn.list_files(sitename, '', ext='dest')
    assert naam_d not in rhfn.list_files(sitename, '', ext='dest')
    assert naam_d in rhfn.list_files(sitename, '', ext='dest', deleted=True)
    assert naam_d not in rhfn.list_files(sitename, '', ext='src', deleted=True)
    # move rename/delete to mirror and check
    assert naam_o not in rhfn.list_files(sitename, '', ext='mirror')
    assert naam_r not in rhfn.list_files(sitename, '', ext='mirror')
    assert naam_d not in rhfn.list_files(sitename, '', ext='mirror')
    msg = rhfn.save_to_mirror(sitename, '', naam_r, confdata_extra)
    assert_equal(msg, '')
    assert naam_o not in rhfn.list_files(sitename, '', ext='mirror')
    assert naam_r in rhfn.list_files(sitename, '', ext='mirror')
    assert naam_r not in rhfn.list_files(sitename, '', ext='dest', deleted=True)
    assert naam_d not in rhfn.list_files(sitename, '', ext='mirror')
    assert naam_d not in rhfn.list_files(sitename, '', ext='dest', deleted=True)
    print('ok')


def test_check_formats(sitename, current):
    """check_if_rst in various situations"""
    print(test_check_formats.__doc__ + '...', end=' ')
    msg1 = "supply_text"
    msg2 = "rst_invalid"
    msg3 = "src_name_missing"
    assert_equal(rhfn.check_if_rst("", ""), msg1)
    assert_equal(rhfn.check_if_rst("some text", ""), msg2)
    assert_equal(rhfn.check_if_rst("some text", "anything"), msg2)
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST), '')
    assert_equal(rhfn.check_if_rst("<p>some text<p>", rhfn.RST), '')
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST, filename=""), msg3)
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST, filename="random"), '')
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST, filename="random/"), msg3)
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST, filename=".."), msg3)
    assert_equal(rhfn.check_if_rst("some text", rhfn.RST, filename="-- new --"), msg3)
    print('ok')
    print("check_if_html in various situations:", end=" ")
    msg2 = "load_html"
    msg3 = "html_name_missing"
    assert_equal(rhfn.check_if_html("", ""), msg1)
    assert_equal(rhfn.check_if_html("some text", ""), msg2)
    assert_equal(rhfn.check_if_html("some text", "anything"), msg2)
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML), '')
    assert_equal(rhfn.check_if_html("<p>some text<p>", rhfn.HTML), '')
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML, filename=""), msg3)
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML, filename="random"), '')
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML, filename="random/"), msg3)
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML, filename=".."), msg3)
    assert_equal(rhfn.check_if_html("some text", rhfn.HTML, filename="-- new --"), msg3)
    print('ok')


def test_progress_list(sitename, current, conf):
    """building progress list and updating all documents"""
    print(test_progress_list.__doc__ + '...', end=' ')
    ## list_site_contents(sitename)
    # hard to assert-test because it uses actual date-time stamps
    # maybe I should create a separate demo site for this
    # but then the update-all would still be untestable this way
    # so here we just pprint an htmlview the lot
    # print(list((WEBROOT / sitename).iterdir()))
    olddata = rhfn.build_progress_list(sitename)
    ## pprint.pprint(olddata)

    errors = rhfn.update_all(sitename, conf)
    assert_equal(errors, [('tilanus', 'mirror_missing'),
                          ('guichelheil/de groot', 'mirror_missing')])
    newdata = rhfn.build_progress_list(sitename)
    ## pprint.pprint(newdata)
    # compare newdata with olddata and check for expected differences
    # force creating missing html and mirror documents:
    errors = rhfn.update_all(sitename, conf, missing_ok=True)
    assert_equal(errors, [])
    print('ok')


def test_reference_list(sitename, current):
    """building reference document"""
    print(test_reference_list.__doc__ + '...', end=' ')
    # 1. add references to "jansen", save html and promote to mirror
    naam = 'jansen'
    rhfn.save_src_data(sitename, '', naam, 'bah humbug\n'
                       '.. refkey:: ref1: here1\n'
                       '.. refkey:: ref2: here2\n'
                       'end')
    rhfn.save_html_data(sitename, '', naam, 'updated')
    rhfn.save_to_mirror(sitename, '', naam, confdata_extra)
    # 2. add reference s to"tilanus" and save html
    naam = 'tilanus'
    rhfn.save_src_data(sitename, '', naam, 'it`s me Modine\n'
                       '.. refkey:: ref3: here3\n')
    rhfn.save_html_data(sitename, '', naam, 'updated')
    # 3. add new document with references
    naam = 'horrorscenario'
    rhfn.save_src_data(sitename, '', naam, '.. refkey:: ref3: here3\n', new=True)
    refs, errs = rhfn.get_reflinks_in_dir(sitename)
    assert_equal(refs, {'Ref2': ['jansen.html#here2'], 'Ref1': ['jansen.html#here1']})
    assert_equal(errs, [])
    # 4. add references to "guichelheil/hendriksen", save html and promote to mirror
    dirnaam = 'guichelheil'
    naam = 'hendriksen'
    rhfn.save_src_data(sitename, dirnaam, naam, 'later krokodil\n'
                       '.. refkey:: ref4: here1\n'
                       'end')
    rhfn.save_html_data(sitename, dirnaam, naam, 'updated')
    rhfn.save_to_mirror(sitename, dirnaam, naam, confdata_extra)
    result = rhfn.build_trefwoordenlijst(sitename)
    assert_equal(result, '\n'.join(['Index', '=====', '', '`R`_ ', '', 'R', '-', '',
                                    '+   Ref1 `#`__ ', '+   Ref2 `#`__ ', ' ',
                                    '..  _R1: jansen.html#here1',
                                    '..  _R2: jansen.html#here2', ' ',
                                    '__ R1_', '__ R2_', ' ']))
    print('ok')


def test_state_class():
    """Testing state class"""
    print(test_state_class.__doc__ + ":")
    state = rhfn.R2hState()
    ## assert state.sitename == 'test'

    print('testing currentify... ', end='')
    state.current = ''
    fname = 'blub.rst'
    assert_equal(state.currentify(fname), fname)
    dirname = 'fish_goes'
    state.current = dirname
    assert_equal(state.currentify(fname), '/'.join((dirname, fname)))
    print('ok')

    print('testing get_conf... ', end='')
    state.subdirs = None
    mld = state.get_conf('test')
    assert_equal(mld, '')
    assert_equal(state.loaded, 'yaml')
    assert_equal(sorted_items(state.conf), sorted_items(confdata))
    assert_equal(sorted(state.subdirs), sorted(['guichelheil/', 'moerasspiraea/']))
    assert_equal(state.current, '')
    print('ok')

    return state


def test_index(state):
    """testing index"""
    print(test_index.__doc__ + '...', end=' ')

    initial_site = state.sitename
    data = state.index()
    # skip this check for now as we haven't converted bitbucket to postgres yet
    if DML not in ('mongo', 'postgres'):
        assert_equal(data[:4], ('', '', '', 'Settings file is {}'.format(initial_site)))
    assert_equal(data[-1], initial_site)
    ## assert sorted_items(state.conf) == sorted_items(confdata)
    ## assert sorted(state.subdirs) == sorted(['guichelheil/', 'moerasspiraea/'])
    assert_equal(state.current, '')
    assert_equal(state.loaded, 'yaml')

    print('ok')
    return state


def test_load_conf(state):
    """testing loadconf"""
    print(test_load_conf.__doc__ + '...', end=' ')
    data = state.loadconf('-- new --', '')
    assert_equal(data, ("New site will be created on save - don't forget to provide "
                        "a name for it", newconfdata_text, '-- new --', ''))
    assert_equal(sorted_items(state.conf), sorted_items(newconfdata))
    assert_equal(state.subdirs, [])
    assert_equal(state.current, '')
    assert_equal(state.loaded, 'yaml')
    assert_equal(state.sitename, '-- new --')
    assert state.newconf is True
    data = state.loadconf('test', '')
    assert_equal(data, ('Settings loaded from test', confdata_text, 'test', ''))
    assert_equal(sorted_items(state.conf), sorted_items(confdata))
    assert_equal(sorted(state.subdirs), sorted(['guichelheil/', 'moerasspiraea/']))
    assert_equal(state.current, '')
    assert_equal(state.loaded, 'yaml')
    assert_equal(state.sitename, 'test')
    assert state.newconf is False
    data = state.loadconf('test', 'blub')                   # other conf - fail
    assert_equal(data, ('blub does not exist', confdata_text, 'test', ''))
    assert_equal(sorted_items(state.conf), sorted_items(confdata))
    assert_equal(sorted(state.subdirs), sorted(['guichelheil/', 'moerasspiraea/']))
    assert_equal(state.current, '')
    assert_equal(state.loaded, 'yaml')
    assert_equal(state.sitename, 'test')
    assert state.newconf is False
    data = state.loadconf('blub', 'test')                   # other conf - ok
    assert_equal(data, ('Settings loaded from test', confdata_text, 'test', ''))
    assert_equal(sorted_items(state.conf), sorted_items(confdata))
    assert_equal(sorted(state.subdirs), sorted(['guichelheil/', 'moerasspiraea/']))
    assert_equal(state.current, '')
    assert_equal(state.loaded, 'yaml')
    assert_equal(state.sitename, 'test')
    assert state.newconf is False
    print('ok')
    return state


def test_save_conf(state):
    """testing saveconf"""
    print(test_save_conf.__doc__ + '...', end=' ')
    last_sett = state.sitename
    data = state.saveconf('test', '', '')
    assert_equal(data, ('Please provide content for text area', '', last_sett, ''))
    state.loaded = rhfn.RST
    data = state.saveconf('test', '', 'config text')
    assert_equal(data, ("Not executed: text area doesn't contain settings data",
                        'config text', last_sett, ''))
    state.loaded = rhfn.CONF
    data = state.saveconf('test', '', 'config text')
    assert 'Config: invalid value for' in data[0]
    assert_equal(data[1:], ('config text', 'test', ''))
    data = state.saveconf('test', '', confdata_text)
    assert_equal(data, ('Settings opgeslagen als test', confdata_text, 'test', ''))
    data = state.saveconf('blub', '', confdata_text)
    assert_equal(data, ('blub does not exist', confdata_text, 'test', ''))
    state.newconf = True
    data = state.saveconf('test', 'blub', newconfdata_text)
    assert_equal(data, ("Settings opgeslagen als blub; note that previews won't work "
                        "with empty url setting", other_confdata_text, 'blub', ''))
    print('ok')
    return state


def test_loadrst(state):
    """testing loadrst"""
    print(test_loadrst.__doc__ + '...', end=' ')
    state.sitename = 'test'
    data = state.loadrst('')
    assert_equal(data, ('Oops! Page was probably open on closing the browser',
                        other_confdata_text, '', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.CONF)
    assert_equal(state.oldtext, other_confdata_text)
    data = state.loadrst('-- new --')
    assert_equal(data, ("Don't forget to supply a new filename on saving", '', '', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, '')
    data = state.loadrst('guichelheil/')
    assert_equal(data, ('switching to directory guichelheil', '', '', ''))
    assert_equal(state.current, 'guichelheil')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, '')
    data = state.loadrst('..')
    assert_equal(data, ('switching to parent directory', '', '', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, '')
    data = state.loadrst('jansen.rst')
    assert_equal(data, ('Source file jansen.rst loaded', jansen_txt, 'jansen.html', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, jansen_txt)
    data = state.loadrst('jansen')
    assert_equal(data, ('Source file jansen loaded', jansen_txt, 'jansen.html', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, jansen_txt)
    data = state.loadrst('jansen.html')
    assert_equal(data, ('Not executed: not a valid source file name', jansen_txt,
                        'jansen.html', ''))
    assert_equal(state.current, '')
    assert_equal(state.loaded, rhfn.RST)
    assert_equal(state.oldtext, jansen_txt)
    print('ok')
    return state


def test_saverst(state):
    """testing saverst"""
    print(test_saverst.__doc__ + '...', end=' ')
    data = state.saverst('jansen.rst', '', '', 'hallo vriendjes')
    assert_equal(data, ('Rst source saved as jansen.rst',
                        'jansen.rst', 'jansen.html', '', False))
    data = state.saverst('jansen', '', '', 'hallo vriendjes')
    assert_equal(data, ('Rst source saved as jansen.rst',
                        'jansen.rst', 'jansen.html', '', False))
    data = state.saverst('jansen.rst', 'monty/', '', 'my hovercraft is full of eels')
    assert_equal(data, ('New subdirectory monty created', 'monty/', 'jansen.html', '', False))
    state.rstfile = 'jansen.rst'
    data = state.saverst('monty/', '', '', 'my hovercraft is full of eels')
    assert_equal(data, ('Subdirectory monty already exists',
                        'jansen.rst', 'jansen.html', '', False))
    # save as
    data = state.saverst('jansen.rst', 'python.rst', '', 'my hovercraft is full of eels')
    assert_equal(data, ('Rst source saved as python.rst', 'python.rst', 'python.html',
                        '', False))
    # rename
    data = state.saverst('python.rst', '', 'rename', '')
    assert_equal(data, ('Please enter a (.rst) name to rename this file to',
                        'python.rst', 'python.html', '', False))
    data = state.saverst('python.rst', 'jansen.rst', 'rename', '')
    assert_equal(data, ('New name for file already in use', 'python.rst', 'python.html',
                        '', False))
    data = state.saverst('python.rst', 'cleese.rst', 'rename', '')
    assert_equal(data, ('python.rst renamed to cleese.rst', 'python.rst', 'python.html',
                        '', False))
    # delete
    data = state.saverst('', 'tobedeleted.rst', '', 'hallo vriendjes')
    assert data[0].startswith('Rst source saved as')
    data = state.saverst('tobedeleted.rst', '', 'delete', '')
    assert_equal(data, ('tobedeleted.rst deleted', 'tobedeleted.rst', 'tobedeleted.html', '', True))

    state.loaded = rhfn.CONF
    data = state.saverst('jansen.rst', '', '', 'hallo vriendjes')
    assert_equal(data[0], "Not executed: text area doesn't contain restructured text")
    print('ok')
    return state


def test_convert(state):
    """testing convert"""
    print(test_convert.__doc__ + '...', end=' ')
    state.oldtext = 'hallo vriendjes'
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data, ("Not executed: text area doesn't contain restructured text", '', ''))
    state.loaded = rhfn.RST
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data, ('', converted_txt, 'jansen.rst'))
    data = state.convert('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert_equal(data, ('', converted_txt, 'pietersen.rst'))
    state.oldtext = 'something else'
    data = state.convert('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data, ('', converted_txt, 'jansen.rst'))
    data = state.convert('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert_equal(data, ('Source file does not exist', '', ''))
    print('ok')
    return state


def test_saveall(state):
    """testing saveall"""
    print(test_saveall.__doc__ + '...', end=' ')
    state.oldtext = 'hallo vriendjes'
    state.loaded = rhfn.HTML
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data[0], "Not executed: text area doesn't contain restructured text")
    state.loaded = rhfn.RST
    # first-time only: check if deletions have been propagated
    for name in ('tobedeleted', 'python'):
        assert name in rhfn.list_files(state.sitename, state.current, ext='src', deleted=True)
        assert name not in rhfn.list_files(state.sitename, state.current, ext='dest', deleted=True)
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data, ('Rst converted to html and saved as jansen.html',
                        'jansen.rst', 'jansen.html', ''))
    for name in ('tobedeleted', 'python'):
        assert name not in rhfn.list_files(state.sitename, state.current, ext='src', deleted=True)
        assert name in rhfn.list_files(state.sitename, state.current, ext='dest', deleted=True)
    data = state.saveall('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert_equal(data, ('Rst converted to html and saved as pietersen.html',
                        'pietersen.rst', 'pietersen.html', ''))
    state.oldtext = 'something else'
    data = state.saveall('jansen.rst', '', 'hallo vriendjes')
    assert_equal(data, ('Rst converted to html and saved as jansen.html',
                        'jansen.rst', 'jansen.html', ''))
    data = state.saveall('jansen.rst', 'pietersen.rst', 'hallo vriendjes')
    assert_equal(data, ('Source file already exists', 'pietersen.rst',
                        'pietersen.html', ''))
    print('ok')
    return state


def test_loadhtml(state):
    """testing loadhtml"""
    print(test_loadhtml.__doc__ + '...', end=' ')
    data = state.loadhtml('')
    assert_equal(data, ('Please enter or select a target (.html) filename',
                        pietersen_txt, 'pietersen.rst', 'pietersen.html'))
    data = state.loadhtml('..')
    assert_equal(data, ('Please enter or select a target (.html) filename',
                        pietersen_txt, 'pietersen.rst', 'pietersen.html'))
    data = state.loadhtml('guichelheil/')
    assert_equal(data, ('Please enter or select a target (.html) filename',
                        pietersen_txt, 'pietersen.rst', 'pietersen.html'))
    data = state.loadhtml('-- new --')
    assert_equal(data, ('Please enter or select a target (.html) filename',
                        pietersen_txt, 'pietersen.rst', 'pietersen.html'))
    data = state.loadhtml('jansen')
    assert_equal(data, ('Target html jansen.html loaded', converted_txt, 'jansen.rst',
                        'jansen.html'))
    data = state.loadhtml('jansen.html')
    assert_equal(data, ('Target html jansen.html loaded', converted_txt, 'jansen.rst',
                        'jansen.html'))
    data = state.loadhtml('jansen.rst')
    assert_equal(data, ('Not executed: not a valid target file name', converted_txt,
                        'jansen.rst', 'jansen.html'))
    print('ok')
    return state


def test_showhtml(state):
    """testing showhtml"""
    print(test_showhtml.__doc__ + '...', end=' ')
    state.htmlfile = 'jansen.html'
    state.loaded = rhfn.RST
    data = state.showhtml(converted_txt)
    assert_equal(data, ('Please load HTML first', '', ''))
    state.loaded = rhfn.HTML
    data = state.showhtml(converted_txt)
    assert_equal(data, ('', converted_txt, 'jansen.html'))
    print('ok')
    return state


def test_savehtml(state):
    """testing savehtml"""
    print(test_savehtml.__doc__ + '...', end=' ')
    state.loaded = rhfn.RST
    data = state.savehtml('jansen.html', '', converted_txt)
    assert_equal(data, ('Please load HTML first', converted_txt, ''))
    state.loaded = rhfn.HTML
    data = state.savehtml('jansen.html', '', converted_txt)
    assert_equal(data, ('Modified HTML saved as jansen.html', converted_txt, ''))
    data = state.savehtml('jansen.html', 'jansens.html', converted_txt)
    assert_equal(data, ('Not executed: can only save HTML under the same name',
                        converted_txt, ''))
    print('ok')
    return state


def test_copytoroot(state):
    """testing copytoroot"""
    print(test_copytoroot.__doc__ + '...', end=' ')
    state.loaded = rhfn.RST
    data = state.copytoroot('jansen.html', converted_txt)
    assert_equal(data, 'Please load HTML first')
    state.loaded = rhfn.HTML
    # also check if deletions have been propagated
    for name in ('tobedeleted', 'python'):
        assert name in rhfn.list_files(state.sitename, state.current, ext='dest', deleted=True)
    data = state.copytoroot('jansen.html', converted_txt)
    assert_equal(data, 'Copied to siteroot/jansen.html')
    for name in ('tobedeleted', 'python'):
        assert name not in rhfn.list_files(state.sitename, state.current, ext='dest', deleted=True)
        assert name not in rhfn.list_files(state.sitename, state.current, ext='src')
        assert name not in rhfn.list_files(state.sitename, state.current, ext='dest')
        # also check existence in mirror directory
        assert name not in rhfn.list_files(state.sitename, state.current, ext='mirror')
    print('ok')
    return state


def test_makerefdoc(state):
    """testing makerefdoc"""
    print(test_makerefdoc.__doc__ + '...', end=' ')
    data = state.makerefdoc()
    assert_equal(data, ('Index created as reflist.html', 'Index\n=====\n\n'))
    # ja zo kan ik het ook - nog een keer met refkeys aanwezig graag
    print('ok')
    return state


def test_convert_all(state):
    """testing convert_all"""
    print(test_convert_all.__doc__ + '...', end=' ')
    mld, data = state.convert_all()
    assert_equal(mld, 'Site documents regenerated, messages below')
    test = data.split('\n')
    assert_equal(sorted(test),
                 sorted(('pietersen not present at mirror',
                         # target_missing message vervangen door html_file_missing
                         # 'cleese skipped: not in target directory',
                         # 'horrorscenario skipped: not in target directory')))
                         'cleese: Target file does not exist',
                         'horrorscenario: Target file does not exist')))
    print('ok')
    return state


def test_overview(state):
    """testing overview"""
    print(test_overview.__doc__ + '...', end=' ')
    # not much more than receiving the results of the earlier tested build_progress_list
    data = state.overview()
    # this yields time-dependent data so we can't do a simple assert on it:
    ## print(data)
    assert_equal(sorted([item[:3] for item in data]), sorted(expected_overview))
    print('ok')
    return state


def test_loadxtra(state):
    """loading site directives"""
    print(test_loadxtra.__doc__ + '...', end=' ')
    data = state.loadxtra()
    assert data is not None  # for now
    print('ok (not implemented yet)')
    return state


def test_savextra(state):
    """saving site directives"""
    print(test_savextra.__doc__ + '...', end=' ')
    data = state.savextra()
    assert data is not None  # for now
    print('ok (not implemented yet)')


def main():
    """run tests"""
    sitename = 'test'
    clear_site_contents(sitename)
    clear_site_contents('blub')

    ## test_functions_setup(sitename)
    test_new_site(sitename)
    conf = test_readwrite_conf(sitename)
    current = test_list_files(sitename)
    test_readwrite_docs(sitename, current)
    test_check_formats(sitename, current)
    test_rename_delete_docs(sitename, current)
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
