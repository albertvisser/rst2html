# tests for rst2html_functions
# only test what we've modified
import os
import subprocess as sp
import pprint
import yaml
import rst2html_functions_mongo as rhfn
from docs2mongo import clear_db as init_db
from test_mongodml import list_database_contents

def main():

    # clear out test data
    testsite = 'test'
    init_db(testsite)
    mirror = os.path.join('/home', 'albert', 'www', 'cherrypy', 'rst2html',
        'rst2html-data', testsite)
    sp.call(['rm', '-R', '{}'.format(mirror)])

    print('creating new site and doing some failure tests on updating...', end=' ')
    new_site = 'test'
    mld = rhfn.new_conf(new_site)
    assert mld == None
    mld, sett = rhfn.read_conf(new_site)
    assert mld == ''
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
    msg, conf = rhfn.read_conf(sitename)
    expected = {'lang': 'en', 'css': [], 'url': '/rst2html-data/test',
        'wid': 100, 'hig': 32}
    assert msg == ''
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
    assert msg == None
    expected = {'hig': 32, 'wid': 100, 'url': '/rst2html-data/test',
        'css': ['http://www.example.com/test.css'], 'lang': 'en'}
    msg, conf = rhfn.read_conf(sitename)
    assert msg == ''
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
    mld, data = rhfn.determine_most_recently_updated(sitename)
    assert mld == ''
    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(data)
    ## sp.Popen(['/home/albert/bin/viewhtml', '/tmp/test.html'])

    errors = rhfn.update_all(sitename, conf)
    assert errors == [('tilanus', 'mirror_missing'),
        ('de groot', 'mirror_missing')]
    newdata = rhfn.build_progress_list(sitename)
    ## pprint.pprint(newdata)
    mld, data = rhfn.determine_most_recently_updated(sitename)
    assert mld == ''
    with open('test2.html', 'w', encoding='utf-8') as f:
        f.write(data)
    ## sp.Popen(['/home/albert/bin/viewhtml', '/tmp/test2.html'])
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
    assert result == []
    msg, data = rhfn.read_src_data(sitename, '', 'reflist')
    assert msg == ""
    assert data == '\n'.join(['Index', '=====', '', '`R`_ ', '', 'R', '-', '',
        '+   Ref1 `#`__ ', '+   Ref2 `#`__ ', ' ',
        '..  _R1: jansen.html#here1', '..  _R2: jansen.html#here2', ' ',
        '__ R1_', '__ R2_', ' '])
    ## with open('/tmp/reflist.rst', 'w', encoding='utf-8') as f:
        ## f.write(data)
    ## sp.Popen(['python3', 'htmlfromrst.py', '/tmp/reflist.rst'])
    print('ok')

if __name__ == '__main__':
    ## main()
    list_database_contents()
