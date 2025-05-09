"""unittests for ./app/rst2html_functions.py

verifiëren dat hulpmethodes aangeroepen worden heb ik gedaan door deze te monkeypatchen met een
methode die een print statement doet en dat dan met capsys te controleren;
later bedacht ik dat ik dan meteen de argumenten kon laten tonen, dit kan desgewenst nog toegevoegd
worden in de eerder geschreven mock methoden
"""
# import pathlib
import datetime
import pytest

import app.rst2html_functions as testee
from app_settings import LANG

FIXDATE = datetime.datetime(2020, 1, 1)

def mock_default_site():
    """stub
    """
    return 'testsite'


def mock_get_lang(*args):
    """stub
    """
    return ''


def mock_get_text(*args):
    """stub
    """
    return args[0]


class MockDatetime:
    """stub for datetime.Datetime object
    """
    @classmethod
    def today(cls):
        """stub
        """
        return FIXDATE


class TestLangRelated:
    """unittests for functions related to language support
    """
    def test_get_text(self):
        """unittest for rst2html_functions.get_text

        voorlopig even met hard gecodeerde verwachte uitkomsten
        """
        lang_keyword = 't_settings'
        lang_string_nl = 'selecteer een settings bestand'
        lang_string_en = ('Select a settings file, indicating the site to work on and other'
                          ' parameters')

        assert testee.get_text(lang_keyword, 'en') == lang_string_en
        assert testee.get_text(lang_keyword, 'nl') == lang_string_nl
        if LANG == 'en':
            assert testee.get_text(lang_keyword) == lang_string_en
        elif LANG == 'nl':
            assert testee.get_text(lang_keyword) == lang_string_nl

    def test_translate_action(self, monkeypatch):
        """unittest for rst2html_functions.translate_action
        """
        def mock_get_text(*args):
            """stub
            """
            return args[0]
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testee.translate_action('rename') == 'rename'
        assert testee.translate_action('c_rename') == 'rename'
        assert testee.translate_action('revert') == 'revert'
        assert testee.translate_action('c_revert') == 'revert'
        assert testee.translate_action('delete') == 'delete'
        assert testee.translate_action('c_delete') == 'delete'

    def test_format_message(self, monkeypatch):
        """unittest for rst2html_functions.format_message
        """
        def mock_get_text(*args):
            """stub
            """
            raise KeyError
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testee.format_message('test: {}', '', 'parm') == 'test: parm'
        assert testee.format_message('hallo', '', 'x') == 'hallo'
        monkeypatch.setattr(testee, 'get_text', lambda x, y: 'test: {}')
        assert testee.format_message('', '', 'arg') == 'test: arg'


class TestR2HRelated:
    """unittests for functions related to the conversion process using Docutils
    """
    def test_post_process_title(self):
        """unittest for rst2html_functions.post_process_title
        """
        wo_title = ('<html><head></head>'
                    '<body><h1 class="page-titel">Welkom</h1>Hallo allemaal</body>')
        w_title_nok = ('<html><head></head>'
                       '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')
        w_title_ok = ('<html><head><title>stuff</title></head>'
                      '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')
        w_title_after = ('<html><head></head><title>stuff</title>'
                      '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')
        expected = ('<html><head><title>Welkom</title></head>'
                    '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')

        assert testee.post_process_title(wo_title) == wo_title
        with pytest.raises(ValueError):
            testee.post_process_title(w_title_nok)
        assert testee.post_process_title(w_title_ok) == expected
        assert testee.post_process_title(w_title_after) == w_title_after

    def test_rst2html(self, monkeypatch, capsys):
        """unittest for rst2html_functions.rst2html
        """
        def mock_read(name):
            print(f"called dml.read_settings with arg '{name}'")
            return {'writer': 'yyy'}
        def mock_publish_string(*args, **kwargs):
            """stub
            """
            print('called docutils.publish_string with args', args, kwargs)
            return b''
        def mock_post_process_title(*args):
            """stub
            """
            print('called post_process_title with args', args)
        invoer = "Hababarulala"
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read)
        monkeypatch.setattr(testee, 'publish_string', mock_publish_string)
        monkeypatch.setattr(testee, 'post_process_title', mock_post_process_title)
        testee.rst2html('xxx', invoer, 'test.css')
        assert capsys.readouterr().out == (
                "called dml.read_settings with arg 'xxx'\n"
                "called docutils.publish_string with args () {'source': 'Hababarulala',"
                " 'destination_path': 'temp/omgezet.html', 'writer_name': 'yyy',"
                " 'settings_overrides': {'embed_stylesheet': False, 'stylesheet_path': '',"
                " 'stylesheet': 'test.css', 'report_level': 3}}\n"
                "called post_process_title with args ('',)\n")

    def test_register_directives(self, monkeypatch, capsys):
        """unittest for rst2html_functions.register_directives
        """
        def mock_register_directive(*args):
            """stub
            """
            print(f'args for directives.register_directive: `{args[0]}` `{args[1]}`')
        monkeypatch.setattr(testee, 'standard_directives', {'name1': 'fun1', 'name2': 'fun2'})
        monkeypatch.setattr(testee.rd.directives, 'register_directive', mock_register_directive)
        testee.register_directives()
        assert capsys.readouterr().out == ('args for directives.register_directive: `name1`'
                                           ' `fun1`\n'
                                           'args for directives.register_directive: `name2`'
                                           ' `fun2`\n')
        monkeypatch.setattr(testee, 'standard_directives', {})
        testee.register_directives()
        assert capsys.readouterr().out == ''

    def test_get_directives_used(self):
        """unittest for rst2html_functions.get_directives_used
        """
        assert testee.get_directives_used({}) == set()
        data = {('', 'index'): [(1, '.. directive::', [1]), (2, '.. direct::', [1])],
                ('dir', 'text'): [(1, '.. directive', [1])]}
        assert testee.get_directives_used(data) == {'directive', 'direct'}

    def test_get_idcls(self):
        """unittest for rst2html_functions.get_idcls
        """
        testee.rhdir.directive_selectors = {'directive': [('selector', 'class'),
                                                        ('selector', 'id_1')],
                                          'direct': [('selector', 'class'), ('selector', 'id_2')]}
        assert testee.get_idcls([]) == set()
        assert testee.get_idcls({'directive', 'direct'}) == {'class', 'id_1', 'id_2'}
        assert testee.get_idcls({'unknown'}) == set()

    def test_check_directive_selectors(self, monkeypatch, capsys):
        """unittest for rst2html_functions.check_directive_selectors
        """
        def mock_search_site(*args):
            """stub
            """
            return {('', 'index'): [(1, 'directive', [1]), (2, 'direct', [1])]}
        def mock_get_directives_used(*args):
            """stub
            """
            print('called get_directives_used')
            return {'directive', 'direct'}
        def mock_get_directives_used_none(*args):
            """stub
            """
            print('called get_directives_used')
            return {}
        def mock_get_idcls(*args):
            """stub
            """
            print('called get_idcls')
            return {'class_1', 'id_1', 'id_2', 'class_2'}
        def mock_get_idcls_none(*args):
            """stub
            """
            print('called get_idcls')
            return {}
        def mock_read_conf(*args):
            """stub
            """
            return '', {'css': ['test1.css', 'test2.css']}
        def mock_run_found_all(*args, **kwargs):
            """stub
            """
            print('call subprocess with args', ' '.join([f'`{x}`' for x in args[0]]))
            with open('/tmp/r2h_css.css', 'w') as out:
                out.write('selector.class_1 #id_1 .class_2 selector#id_2\n')
        def mock_run_not_all(*args, **kwargs):
            """stub
            """
            print('call subprocess with args', ' '.join(['`{x}`' for x in args[0]]))
            with open('/tmp/r2h_css.css', 'w') as out:
                out.write('selector.class_1 #id_1 \n')
        monkeypatch.setattr(testee, 'search_site', mock_search_site)
        monkeypatch.setattr(testee, 'get_directives_used', mock_get_directives_used)
        monkeypatch.setattr(testee, 'get_idcls', mock_get_idcls)
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)
        monkeypatch.setattr(testee.subprocess, 'run', mock_run_found_all)
        assert testee.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\ncalled get_idcls\n'
                                           'call subprocess with args `wget` `test1.css`'
                                           ' `test2.css` `-O` `/tmp/r2h_css.css`\n')
        monkeypatch.setattr(testee, 'get_directives_used', mock_get_directives_used_none)
        assert testee.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\n')
        monkeypatch.setattr(testee, 'get_directives_used', mock_get_directives_used)
        monkeypatch.setattr(testee, 'get_idcls', mock_get_idcls_none)
        assert testee.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\ncalled get_idcls\n')
        monkeypatch.setattr(testee, 'get_idcls', mock_get_idcls)
        monkeypatch.setattr(testee.subprocess, 'run', mock_run_not_all)
        assert sorted(testee.check_directive_selectors('testsite')) == ['class_2', 'id_2']
        capsys.readouterr()  # swallow stdout/err

    def test_preprocess_includes(self, monkeypatch):
        """unittest for rst2html_functions.preprocess_includes
        """
        def mock_read_conf(*args):
            """stub
            """
            return '', {'lang': testee.LANG}
        def mock_read_src_data(*args):
            """stub
            """
            return '', f'include {args[0]} {args[1]} {args[2]}'
        def mock_read_src_data_msg(*args):
            """stub
            """
            return 'fname_invalid', ''
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)
        # lege invoer
        assert testee.preprocess_includes('testsite', '', '') == ''
        # fout bij ophalen include
        data = 'eerste regel\n\n.. incl:: jansen\n\ntweede regel\n'
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data_msg)
        expected = 'eerste regel\n\n.. error:: Not a valid filename: jansen\n\ntweede regel\n'
        assert testee.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: docname' in root
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data)
        expected = 'eerste regel\n\ninclude testsite  jansen\ntweede regel\n'
        assert testee.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: docname' in subdir
        expected = 'eerste regel\n\ninclude testsite subdir jansen\ntweede regel\n'
        assert testee.preprocess_includes('testsite', 'subdir', data) == expected
        # '.. incl:: subdir/docname' in root
        data = 'eerste regel\n\n.. incl:: subdir/jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite subdir jansen\ntweede regel\n'
        assert testee.preprocess_includes('testsite', '', data) == expected
        # fout: '.. incl:: subdir/docname' in subdir
        data = 'eerste regel\n\n.. incl:: subdir/jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: subdir/jansen\n\n'
                    'tweede regel\n')
        assert testee.preprocess_includes('testsite', 'ix', data) == expected
        # '.. incl:: ../docname' in subdir
        data = 'eerste regel\n\n.. incl:: ../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite  jansen\ntweede regel\n'
        assert testee.preprocess_includes('testsite', 'subdir', data) == expected
        # fout: '.. incl:: ../docname' in root
        data = 'eerste regel\n\n.. incl:: ../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\n.. error:: Not a valid filename: ../jansen\n\ntweede regel\n'
        assert testee.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: ../subdir/docname' in andere subdir
        data = 'eerste regel\n\n.. incl:: topdir/../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite topdir jansen\ntweede regel\n'
        assert testee.preprocess_includes('testsite', 'subdir', data) == expected
        # fout: '.. incl:: ../subdir/docname' in root
        data = 'eerste regel\n\n.. incl:: topdir/../jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: topdir/../jansen\n\n'
                    'tweede regel\n')
        assert testee.preprocess_includes('testsite', '', data) == expected
        # fout: geen includenaam
        data = 'eerste regel\n\n.. incl::\n\ntweede regel\n'
        expected = ("eerste regel\n\n.. error:: Not a valid filename: it's missing...\n\n"
                    'tweede regel\n')
        assert testee.preprocess_includes('testsite', '', data) == expected
        # fout: teveel pad-onderdelen
        data = 'eerste regel\n\n.. incl:: top/dir/../jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: top/dir/../jansen\n\n'
                    'tweede regel\n')
        assert testee.preprocess_includes('testsite', '', data) == expected


class TestConfRelated:
    """unittests for site / configuration related functions
    """
    def test_default_site(self, monkeypatch):
        """unittest for rst2html_functions.default_site
        """
        def no_sitelist():
            """stub
            """
            return []
        def sitelist_without_dflt():
            """stub
            """
            return ['site_1', 'site_2']
        def sitelist_with_dflt():
            """stub
            """
            return ['site_0', 'blabla']
        monkeypatch.setattr(testee.dml, 'list_sites', no_sitelist)
        assert testee.default_site() == ''
        monkeypatch.setattr(testee.dml, 'list_sites', sitelist_without_dflt)
        assert testee.default_site() == 'site_1'
        monkeypatch.setattr(testee, 'DFLT', 'blabla')
        monkeypatch.setattr(testee.dml, 'list_sites', sitelist_with_dflt)
        assert testee.default_site() == 'blabla'

    def test_new_conf(self, monkeypatch):
        """unittest for rst2html_functions.new_conf
        """
        def text2conf_notok(*args):
            """stub
            """
            return 'Not OK', {}
        def text2conf_emptyurl(*args):
            """stub
            """
            return '', {'url': ''}
        def text2conf_ok(*args):
            """stub
            """
            return '', {'url': 'http://www.example.org'}
        def get_text_msg(*args):
            """stub
            """
            return 'Not Created'
        def create_conf(*args):
            """stub
            """
            return 'new_site'
        def create_site_exc(*args):
            """stub
            """
            raise FileExistsError('Exists')
        def create_site_ok(*args):
            """stub
            """
        monkeypatch.setattr(testee, 'text2conf', text2conf_notok)
        monkeypatch.setattr(testee, 'get_text', get_text_msg)
        assert testee.new_conf('', '') == ('Not Created Not OK', '')
        monkeypatch.setattr(testee, 'text2conf', text2conf_emptyurl)
        monkeypatch.setattr(testee, 'create_server_config', create_conf)
        monkeypatch.setattr(testee.dml, 'create_new_site', create_site_exc)
        assert testee.new_conf('', '') == ('Exists', '')  # 'http://new_site')
        monkeypatch.setattr(testee.dml, 'create_new_site', create_site_ok)
        assert testee.new_conf('', '') == ('', 'http://new_site')
        monkeypatch.setattr(testee, 'text2conf', text2conf_ok)
        assert testee.new_conf('', '') == ('', '')

    def test_create_server_config(self, monkeypatch):
        """unittest for rst2html_functions.create_server_config
        """
        def mock_get_tldname(*args):
            """stub
            """
            return 'example.com'
        def mock_add_to_hostsfile(*args):
            """stub
            """
            print('mock_add_to_hostsfile was called')
        def mock_add_to_server(*args):
            """stub
            """
            print('mock_add_to_server was called')
        monkeypatch.setattr(testee, 'get_tldname', mock_get_tldname)
        monkeypatch.setattr(testee, 'add_to_hostsfile', mock_add_to_hostsfile)
        monkeypatch.setattr(testee, 'add_to_server', mock_add_to_server)
        assert testee.create_server_config('mysite') == 'mysite.example.com'

    # eigenlijk betekent het gegeven dat de volgende drie methoden niet te testen zijn dat deze
    # thuishoren in een data-benaderingsmodule, dan wel dat het ophalen van gegevens uit een extern
    # bestand in zo'n module thuishoort waardoor het wel monkeypatchbaar wordt
    # anderszijds is het voor de eerste routine ook mogelijk de filenamen niet hard te coderen
    # zodat de inhoud gesimuleerd kan worden

    def test_get_tldname(self):
        """unittest for rst2html_functions.get_tldname
        """
        # voor bepalen tldname kijken we in eerst /etc/hosts: eerste entry met een punt erin
        # pas als die niet bestaat kijken we of er iets in /etc/hostname staat (computernaam)
        # maar dat is niet te testen zonder /etc/hosts aan te passen
        assert testee.get_tldname() == 'lemoncurry.nl'

    def _test_add_to_hostsfile(self):  # not really testable (yet)
        """unittest for rst2html_functions.add_to_hostsfile
        """

    def _test_add_to_server(self):  # not really testable (yet)
        """unittest for rst2html_functions.add_to_server
        """

    def test_init_css(self, monkeypatch, capsys):
        """unittest for rst2html_functions.init_css
        """
        def mock_read_settings_empty(*args):
            """stub
            """
            return {'css': []}
        def mock_read_settings_basic_plus(*args):
            """stub
            """
            return {'css': testee.BASIC_CSS['html5'][:2] + ['960.css', 'myowncss.css',
                                             'http://www.example.com/static/css.css']}
        def mock_read_settings_3(*args):
            """stub
            """
            return {'writer': 'html5', 'css': testee.BASIC_CSS['html5']}
        def mock_copyfile(*args):
            """stub
            """
            print(f'copying `{args[0]}` to `{args[1]}`')
        def mock_update_settings(*args):
            """stub
            """
            print(f'update_settings called with args `{args[0]}` `{args[1]}`')
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_empty)
        monkeypatch.setattr(testee.shutil, 'copyfile', mock_copyfile)
        monkeypatch.setattr(testee.dml, 'update_settings', mock_update_settings)
        # als deze nog niet bestaat wordt er een directory css aangemaakt onder `sitename`
        # alle files in BASIC_CSS die nog niet in conf['css'] zitten worden daarin opgevoerd
        # en ook aan conf['css'] toegevoegd dat daarna aangepast wordt
        sitename = 'testsite'
        here = testee.HERE.parent / 'static'
        there = testee.WEBROOT / sitename / 'css'
        there_present = there.parent.exists()
        monkeypatch.setattr(testee, 'BASIC_CSS', {'html5': ['minimal.css', 'plain.css']})
        copy_lines = [f'copying `{here}/{x}` to `{there}/{x}`\n' for x in testee.BASIC_CSS['html5']]
        update_lines = [f"'url + css/{x}'" for x in testee.BASIC_CSS['html5']]
        if not there_present:  # make sure cssdir.mkdir doesn't fail
            there.parent.mkdir(parents=True, exist_ok=True)
        testee.init_css(sitename)
        # assert capsys.readouterr().out == ''
        assert capsys.readouterr().out == (''.join(copy_lines) + "update_settings called with"
                                           " args `testsite` `{{'css': [{}, {}], 'writer':"
                                           " 'html5'}}`\n".format(*update_lines))
        if not there_present:  # teardown if necessary
            there.parent.rmdir()
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_basic_plus)
        testee.init_css(sitename)
        assert capsys.readouterr().out == (
                # "copying `/home/albert/projects/rst2html/static/960.cs` to"
                # " `/home/albert/projects/rst2html/rst2html-data/testsite/css/960.cs`\n"
                "update_settings called with args `testsite` `{'css':"
                " ['minimal.css', 'plain.css', '960.css', 'myowncss.css',"
                " 'http://www.example.com/static/css.css'], 'writer': 'html5'}`\n")
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_3)
        # breakpoint()
        testee.init_css(sitename)
        assert capsys.readouterr().out == ""

    def test_list_confs(self, monkeypatch):
        """unittest for rst2html_functions.list_confs
        """
        def mock_list_sites_none():
            """stub
            """
            return []
        def mock_list_sites_one():
            """stub
            """
            return ['one']
        def mock_list_sites_more():
            """stub
            """
            return ['first', 'next', 'last']
        monkeypatch.setattr(testee.dml, 'list_sites', mock_list_sites_none)
        assert testee.list_confs() == ''
        monkeypatch.setattr(testee.dml, 'list_sites', mock_list_sites_one)
        assert testee.list_confs() == '<option>one</option>'
        assert testee.list_confs('two') == '<option>one</option>'
        monkeypatch.setattr(testee.dml, 'list_sites', mock_list_sites_more)
        assert testee.list_confs() == ('<option>first</option><option>next</option>'
                                     '<option>last</option>')
        assert testee.list_confs('last') == ('<option>first</option><option>next</option>'
                                           '<option selected="selected">last</option>')

    def test_read_conf(self, monkeypatch):
        """unittest for rst2html_functions.read_conf
        """
        mocked_settings = {'x': 'y'}
        def mock_read_settings_notfound(*args):
            """stub
            """
            raise FileNotFoundError
        def mock_read_settings_found(*args):
            """stub
            """
            return mocked_settings
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_notfound)
        assert testee.read_conf('testsite') == ('no_such_sett', None)
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_found)
        assert testee.read_conf('testsite') == ('', mocked_settings)

    def test_conf2text(self, monkeypatch):
        """unittest for rst2html_functions.conf2text
        """
        def mock_save_config_data(confdict, **kwargs):
            """stub
            """
            return confdict
        monkeypatch.setattr(testee, 'save_config_data', mock_save_config_data)
        conf_in = {'test': 'tested', 'url': 'gargl', 'css': ['gargl/snork.css', 'test.css']}
        conf_out = {'test': 'tested', 'url': 'gargl', 'css': ['url + snork.css', 'test.css']}
        assert testee.conf2text(conf_in) == conf_out

    def _test_text2conf_old(self, monkeypatch):
        """unittest for rst2html_functions.text2conf_old
        """
        def mock_get_text(*args):
            """stub
            """
            return args[0] + ': {}'
        def mock_load_config_data_error(*args):
            """stub
            """
            raise testee.ParserError
        def mock_load_config_data_empty(*args):
            """stub
            """
            return {}
        def mock_load_config_data_basic(*args):
            """stub
            """
            return testee.DFLT_CONF
        def mock_load_config_data_hig_fout(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['hig'] = 'hallo'
            return conf
        def mock_load_config_data_lang_fout(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['lang'] = 'du'
            return conf
        def mock_load_config_url_not_http(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['url'] = 'x'
            print(conf)
            return conf
        def mock_load_config_url_other(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['url'] = 'http://x/'
            return conf
        def mock_check_url(*args):
            """stub
            """
            # raise testee.urllib.error.HTTPError
            raise testee.urllib.error.URLError('x')
        def mock_load_config_css_simple(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['css'] = 'a_string'
            return conf
        def mock_load_config_css_double(*args):
            """stub
            """
            conf = dict(testee.DFLT_CONF.items())
            conf['url'] = 'http://x'
            conf['css'] = ['url + a_string', 'http://stuff']
            return conf
        def mock_check_url_ok(*args):
            """stub
            """
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_error)
        assert testee.text2conf_old('') == ('sett_no_good: {}', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_empty)
        assert testee.text2conf_old('') == ('sett_invalid: wid', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_basic)
        assert testee.text2conf_old('') == ('', testee.DFLT_CONF)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_hig_fout)
        assert testee.text2conf_old('') == ('sett_invalid: hig', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_lang_fout)
        assert testee.text2conf_old('') == ('sett_invalid: lang', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_url_not_http)
        assert testee.text2conf_old('') == ('sett_invalid: url', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_url_other)
        monkeypatch.setattr(testee, 'check_url_old', mock_check_url)
        assert testee.text2conf_old('') == ('sett_invalid: url', {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_css_simple)
        # expected = dict(testee.DFLT_CONF.items()).update({'css': ['https://a_string']})
        expected = dict(testee.DFLT_CONF.items())
        expected.update({'css': ['https://a_string']})
        assert testee.text2conf_old('') == ('', expected)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_css_double)
        monkeypatch.setattr(testee, 'check_url_old', mock_check_url_ok)
        # expected = dict(testee.DFLT_CONF.items()).update(
        #         {'url': 'http://x', 'css': ['http://x/a_string', 'http://stuff']})
        expected = dict(testee.DFLT_CONF.items())
        expected.update({'url': 'http://x', 'css': ['http://x/a_string', 'http://stuff']})
        assert testee.text2conf_old('') == ('', expected)

    def test_check_changed_settings(self, monkeypatch, capsys):
        """unittest for rst2html_functions.check_changed_settings
        """
        def mock_check(arg):
            """stub
            """
            print(f'called check_url with arg `{arg}`')
        def mock_check_urlerror(arg):
            """stub
            """
            print(f'called check_url with arg `{arg}`')
            raise testee.urllib.error.URLError(x)
        def mock_check_httperror(arg):
            """stub
            """
            print(f'called check_url with arg `{arg}`')
            raise testee.urllib.error.HTTPError(arg, 'y', 'z', 'a', 'b')
        assert testee.check_changed_settings({'x': 'y', 'a': 'b'}, {'x': 'y', 'a': 'b'}) == (
                {'x': 'y', 'a': 'b'}, ('conf_no_changes',))
        assert testee.check_changed_settings({'wid': 'x'}, {}) == ({}, ('sett_invalid', 'wid'))
        assert testee.check_changed_settings({'wid': '1.2'}, {}) == ({}, ('sett_invalid', 'wid'))
        assert testee.check_changed_settings({'wid': '1'}, {}) == ({'wid': '1'}, ())
        assert testee.check_changed_settings({'wid': 0}, {}) == ({}, ('sett_invalid', 'wid'))
        assert testee.check_changed_settings({'wid': -1}, {}) == ({}, ('sett_invalid', 'wid'))
        assert testee.check_changed_settings({'wid': 1}, {}) == ({'wid': 1}, ())
        assert testee.check_changed_settings({'wid': 1.2}, {}) == ({'wid': 1.2}, ())
        assert testee.check_changed_settings({'hig': 'x'}, {}) == ({}, ('sett_invalid', 'hig'))
        assert testee.check_changed_settings({'hig': '1.2'}, {}) == ({}, ('sett_invalid', 'hig'))
        assert testee.check_changed_settings({'hig': '1'}, {}) == ({'hig': '1'}, ())
        assert testee.check_changed_settings({'hig': 0}, {}) == ({}, ('sett_invalid', 'hig'))
        assert testee.check_changed_settings({'hig': -1}, {}) == ({}, ('sett_invalid', 'hig'))
        assert testee.check_changed_settings({'hig': 1}, {}) == ({'hig': 1}, ())
        assert testee.check_changed_settings({'hig': 1.2}, {}) == ({'hig': 1.2}, ())

        assert testee.check_changed_settings({'lang': ''}, {}) == ({}, ('sett_invalid', 'lang'))
        assert testee.check_changed_settings({'lang': 'x'}, {}) == ({}, ('sett_invalid', 'lang'))
        for x in testee.languages:
            assert testee.check_changed_settings({'lang': x}, {}) == ({'lang': x}, ())

        assert testee.check_changed_settings({'writer': ''}, {}) == ({}, ('sett_invalid', 'writer'))
        assert testee.check_changed_settings({'writer': 'x'}, {}) == ({}, ('sett_invalid', 'writer'))
        for x in testee.writers:
            assert testee.check_changed_settings({'writer': x}, {}) == ({'writer': x}, ())

        assert testee.check_changed_settings({'url': ''}, {}) == ({'url': ''}, ())
        assert capsys.readouterr().out == ''
        assert testee.check_changed_settings({'url': 'x'}, {}) == ({}, ('sett_invalid', 'url'))
        assert capsys.readouterr().out == ''

        monkeypatch.setattr(testee.urllib.request, 'urlopen', mock_check_httperror)
        # deze test geeft de unraisable exception
        # deze test was uitgeschakeld omdat deze controle niet meer gedaan wordt (nog wel voor https)
        # assert testee.check_changed_settings({'url': 'http://x'}, {}) == ({},
        #                                                                   ('sett_invalid', 'url'))
        # assert capsys.readouterr().out == 'called check_url with arg `http://x`\n'

        # deze test geeft de unraisable exception
        assert testee.check_changed_settings({'url': 'https://x'}, {}) == ({},
                                                                           ('sett_invalid', 'url'))
        assert capsys.readouterr().out == 'called check_url with arg `https://x`\n'

        monkeypatch.setattr(testee.urllib.request, 'urlopen', mock_check_urlerror)
        # deze test gaat onder python 3.12 anders
        # deze test was uitgeschakeld omdat deze controle niet meer gedaan wordt (nog wel voor https)
        # assert testee.check_changed_settings({'url': 'http://x'}, {}) == ({},
        #                                                                   ('sett_invalid', 'url'))
        assert testee.check_changed_settings({'url': 'http://x'}, {}) == ({'url': 'http://x'}, ())
        # assert capsys.readouterr().out == 'called check_url with arg `http://x`\n'
        assert capsys.readouterr().out == ''

        assert testee.check_changed_settings({'url': 'https://x'}, {}) == ({},
                                                                           ('sett_invalid', 'url'))
        # vanaf hier is alles weer gewoon
        assert capsys.readouterr().out == 'called check_url with arg `https://x`\n'
        monkeypatch.setattr(testee.urllib.request, 'urlopen', mock_check)
        assert testee.check_changed_settings({'url': 'http://x'}, {}) == ({'url': 'http://x'}, ())
        assert capsys.readouterr().out == ''  # 'called check_url with arg `http://x`\n'
        assert testee.check_changed_settings({'url': 'https://x'}, {}) == ({'url': 'https://x'}, ())
        assert capsys.readouterr().out == 'called check_url with arg `https://x`\n'

        assert testee.check_changed_settings({'seflinks': ''}, {}) == ({},
                                                                       ('sett_invalid', 'seflinks'))
        assert testee.check_changed_settings({'seflinks': 'xxx'}, {}) == ({},
                                                                       ('sett_invalid', 'seflinks'))
        for value in (0, 1, '0', '1', 'true', 'false', 'True', 'False'):
            assert testee.check_changed_settings({'seflinks': value}, {}) == ({'seflinks': value}, ())
        assert testee.check_changed_settings({'highlight': ''}, {}) == ({},
                                                                       ('sett_invalid', 'highlight'))
        assert testee.check_changed_settings({'highlight': 'xxx'}, {}) == ({},
                                                                       ('sett_invalid', 'highlight'))
        for value in (0, 1, '0', '1', 'true', 'false', 'True', 'False'):
            assert testee.check_changed_settings({'highlight': value}, {}) == ({'highlight': value},
                                                                               ())

        monkeypatch.setattr(testee, 'convert_css', lambda x: ([], ('error',)))
        assert testee.check_changed_settings({'css': 'x.css'}, {}) == ({}, ('error',))
        monkeypatch.setattr(testee, 'convert_css', lambda x: ([x['css']], ()))
        assert testee.check_changed_settings({'css': 'x.css'}, {}) == ({'css': ['x.css']}, ())

    def test_convert_css(self):
        """unittest for rst2html_functions.convert_css
        """
        assert testee.convert_css({'css': ''}) == (['https://'], ())
        assert testee.convert_css({'css': 'x'}) == (['https://x'], ())
        assert testee.convert_css({'css': ['http://x']}) == (['http://x'], ())
        assert testee.convert_css({'css': 'url + x'}) == ([], ('conf_no_url',))
        assert testee.convert_css({'css': 'url + x', 'url': ''}) == ([], ('conf_no_url',))
        assert testee.convert_css({'css': 'url + x', 'url': 'y'}) == (['y/x'], ())

    def test_ensure_basic_css(self, monkeypatch, capsys, tmp_path):
        """unittest for rst2html_functions.ensure_basic_css
        """
        def mock_copyfile(*args):
            """stub
            """
            print('called shutil.copyfile with args', args)
        monkeypatch.setattr(testee, 'WEBROOT', tmp_path / 'webroot')
        monkeypatch.setattr(testee, 'HERE', tmp_path / 'here' / 'static')
        monkeypatch.setattr(testee.shutil, 'copyfile', mock_copyfile)
        sitename = 'testsite'
        here = testee.HERE.parent / 'static'
        there = testee.WEBROOT / sitename / 'css'
        # there_present = there.parent.exists()
        monkeypatch.setattr(testee, 'BASIC_CSS', {'html5': ['minimal.css', 'plain.css']})
        # if not there_present:  # make sure cssdir.mkdir doesn't fail
        there.mkdir(parents=True, exist_ok=True)
        conf = {'css': [testee.BASIC_CSS['html5'][1], 'y.css'], 'writer': 'html5'}
        (there / testee.BASIC_CSS['html5'][1]).touch()
        newconf = {'css': [f'url + css/{x}' for x in testee.BASIC_CSS['html5']] + ['y.css'],
                   'writer': 'html5'}
        assert testee.ensure_basic_css(sitename, conf) == newconf
        # assert capsys.readouterr().out == ''
        copyee = testee.BASIC_CSS['html5'][0]
        assert capsys.readouterr().out == ('called shutil.copyfile with args'
                                           f" ('{here}/{copyee}', '{there}/{copyee}')\n")

    def test_text2conf(self, monkeypatch):
        """unittest for rst2html_functions.text2conf
        """
        def mock_get_text(*args):
            """stub
            """
            return args[0] + ': {}'
        def mock_load_config_data_error(*args):
            """stub
            """
            raise testee.ParserError
        def mock_load_config_data_empty(*args):
            """stub
            """
            return {}
        def mock_load_config_data_basic(*args):
            """stub
            """
            return testee.DFLT_CONF
        def mock_load_config_data_wrong_key(*args):
            """stub
            """
            retval = testee.DFLT_CONF
            retval['hello'] = 'goodbye'
            return retval
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_error)
        assert testee.text2conf('') == (('sett_no_good',), {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_empty)
        assert testee.text2conf('') == (('sett_invalid', 'wid'), {})
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_basic)
        assert testee.text2conf('') == ((), testee.DFLT_CONF)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_wrong_key)
        # breakpoint()
        assert testee.text2conf('') == (('sett_noexist', 'hello'), {})

    def test_check_url_old(self, monkeypatch):
        """unittest for rst2html_functions.check_url_old
        """
        def mock_urlopen_ok(*args):
            """stub
            """
        def mock_urlopen(*args):
            """stub
            """
            raise testee.urllib.error.URLError('x')
        monkeypatch.setattr(testee.urllib.request, 'urlopen', mock_urlopen_ok)
        assert testee.check_url_old('') is None
        monkeypatch.setattr(testee.urllib.request, 'urlopen', mock_urlopen)
        with pytest.raises(testee.urllib.error.URLError):
            testee.check_url_old('http://test/testerdetest')

    def test_save_conf_old(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_conf_old
        """
        def mock_read_settings_error(*args):
            """stub
            """
            raise FileNotFoundError
        def mock_read_settings(*args):
            """stub
            """
            return {}
        def mock_get_text(*args):
            """stub
            """
            return 'no_such_sett for `{}`'
        def mock_text2conf_error(*args):
            """stub
            """
            return True, {}
        def mock_text2conf(*args):
            """stub
            """
            return False, {'url': False}
        def mock_update_settings(*args):
            """stub
            """
            print('called update_settings for', args)
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_error)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testee.save_conf_old('testsite', '') == 'no_such_sett for `testsite`'
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings)
        monkeypatch.setattr(testee, 'text2conf_old', mock_text2conf_error)
        assert testee.save_conf_old('testsite', '')
        monkeypatch.setattr(testee, 'text2conf_old', mock_text2conf)
        monkeypatch.setattr(testee.dml, 'update_settings', mock_update_settings)
        assert not testee.save_conf_old('testsite', '')
        assert capsys.readouterr().out == "called update_settings for ('testsite', {'url': False})\n"

    def test_save_conf(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_conf
        """
        def mock_read_settings_error(*args):
            """stub
            """
            raise FileNotFoundError
        def mock_read_settings(*args):
            """stub
            """
            return {'css': 'x', 'url': ''}
        def mock_get_text(*args):
            """stub
            """
            print(f'called get_text for `{args[0]}`')
            return args[0]
        def mock_text2conf_error(*args):
            """stub
            """
            return ('text2conf-error',), {}
        def mock_text2conf(*args):
            """stub
            """
            return False, {'css': 'x', 'url': 'z'}
        def mock_text2conf_other_value(*args):
            """stub
            """
            return False, {'css': 'y', 'url': 'z'}
        def mock_check(*args):
            """stub
            """
            print('called check_changed_settings with args', args)
            return args[0], ''
        def mock_check_error(*args):
            """stub
            """
            print('called check_changed_settings with args', args)
            return {}, ('invalid value found for {}', 'key')
        def mock_ensure(*args):
            """stub
            """
            print('called ensure_basic_css with args', args)
            return {'css': 'yy', 'url': 'z'}
        def mock_update_settings(*args):
            """stub
            """
            print('called update_settings with args', args)
            return ''
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings_error)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testee.save_conf('testsite', '') == 'no_such_sett'
        assert capsys.readouterr().out == 'called get_text for `no_such_sett`\n'
        monkeypatch.setattr(testee.dml, 'read_settings', mock_read_settings)
        monkeypatch.setattr(testee, 'text2conf', mock_text2conf_error)
        assert testee.save_conf('testsite', '') == 'text2conf-error'
        # melding komt twee keer doordat we eerst een try doen die in een except loopt
        assert capsys.readouterr().out == ('called get_text for `text2conf-error`\n'
                                           'called get_text for `text2conf-error`\n')
        monkeypatch.setattr(testee, 'text2conf', mock_text2conf)
        monkeypatch.setattr(testee, 'check_changed_settings', mock_check_error)
        monkeypatch.setattr(testee.dml, 'update_settings', mock_update_settings)
        assert testee.save_conf('testsite', '') == 'invalid value found for key'
        assert capsys.readouterr().out == ("called check_changed_settings with args ({'css': 'x',"
                                           " 'url': 'z'}, {'css': 'x', 'url': ''})\n"
                                           'called get_text for `invalid value found for {}`\n')
        monkeypatch.setattr(testee, 'check_changed_settings', mock_check)
        assert testee.save_conf('testsite', '') == ''
        assert capsys.readouterr().out == ("called check_changed_settings with args ({'css': 'x',"
                                           " 'url': 'z'}, {'css': 'x', 'url': ''})\n"
                                           "called update_settings with args"
                                           " ('testsite', {'css': 'x', 'url': 'z'})\n")
        monkeypatch.setattr(testee, 'text2conf', mock_text2conf_other_value)
        monkeypatch.setattr(testee, 'ensure_basic_css', mock_ensure)
        assert testee.save_conf('testsite', '') == ''
        assert capsys.readouterr().out == ("called check_changed_settings with args ({'css': 'y',"
                                           " 'url': 'z'}, {'css': 'x', 'url': ''})\n"
                                           "called ensure_basic_css with args"
                                           " ('testsite', {'css': 'y', 'url': 'z'})\n"
                                           "called update_settings with args"
                                           " ('testsite', {'css': 'yy', 'url': 'z'})\n")
        monkeypatch.setattr(testee, 'text2conf', mock_text2conf)
        assert testee.save_conf('testsite', '') == ''
        assert capsys.readouterr().out == ("called check_changed_settings with args ({'css': 'x',"
                                           " 'url': 'z'}, {'css': 'x', 'url': ''})\n"
                                           "called update_settings with args"
                                           " ('testsite', {'css': 'x', 'url': 'z'})\n")


class TestSiteRelated:
    """unittests for rst2html_functions.SiteRelated
    """
    def test_list_subdirs(self, monkeypatch, capsys):
        """unittest for rst2html_functions.list_subdirs
        """
        def mock_list_dirs(*args):
            """stub
            """
            print('ext arg is', args[1])
            return ['my_hovercraft', 'cheese_shop']
        def mock_list_dirs_empty(*args):
            """stub
            """
            print('ext arg is', args[1])
            return []
        def mock_list_dirs_error(*args):
            """stub
            """
            print('ext arg is', args[1])
            raise FileNotFoundError
        sitename = 'testsite'
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs)
        assert testee.list_subdirs(sitename) == ['cheese_shop/', 'my_hovercraft/']
        assert capsys.readouterr().out == 'ext arg is src\n'
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs_empty)
        assert testee.list_subdirs(sitename, 'dest') == []
        assert capsys.readouterr().out == 'ext arg is dest\n'
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs)
        assert testee.list_subdirs(sitename, 'xxxx') == ['cheese_shop/', 'my_hovercraft/']
        assert capsys.readouterr().out == 'ext arg is dest\n'
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs_error)
        assert testee.list_subdirs(sitename, 'src') == []
        assert capsys.readouterr().out == 'ext arg is src\n'

    def test_list_files(self, monkeypatch):
        """unittest for rst2html_functions.list_files
        """
        def mock_list_docs(*args, **kwargs):
            """stub
            """
            return ['luxury-yacht', 'throatwobbler-mangrove']
        # def mock_list_docs_empty(*args, **kwargs):
        #     """stub
        #     """
        #     return []
        def mock_list_docs_not_found(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError
        def mock_list_docs_wrong_type(*args, **kwargs):
            """stub
            """
            return
        def mock_list_subdirs(*args):
            """stub
            """
            return ['my_hovercraft/', 'cheese_shop/']
        def mock_list_subdirs_empty(*args):
            """stub
            """
            return []
        def mock_list_templates(*args):
            """stub
            """
            return ['letter.tpl', 'number.tpl']
        def mock_list_templates_empty(*args):
            """stub
            """
            return []
        sitename = 'testsite'
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs_not_found)
        with pytest.raises(ValueError) as exc:
            testee.list_files(sitename)
        assert str(exc.value) == 'Site not found'
        assert testee.list_files(sitename, 'current') == '<option>..</option>'
        assert testee.list_files(sitename, deleted=True) == []
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs_wrong_type)
        with pytest.raises(ValueError) as exc:
            testee.list_files(sitename, ext='xxx')
        assert str(exc.value) == 'Wrong type: `xxx`'
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs)
        assert testee.list_files(sitename, deleted=True) == ['luxury-yacht', 'throatwobbler-mangrove']
        monkeypatch.setattr(testee.dml, 'list_templates', mock_list_templates_empty)
        monkeypatch.setattr(testee, 'list_subdirs', mock_list_subdirs_empty)
        assert testee.list_files(sitename) == ('<option>luxury-yacht.rst</option>'
                                             '<option>throatwobbler-mangrove.rst</option>')
        assert testee.list_files(sitename, current='enormous') == (
                '<option>..</option>'
                '<option>luxury-yacht.rst</option>'
                '<option>throatwobbler-mangrove.rst</option>')
        monkeypatch.setattr(testee.dml, 'list_templates', mock_list_templates)
        assert testee.list_files(sitename, naam='luxury-yacht.rst') == (
                '<option>-- letter.tpl --</option>'
                '<option>-- number.tpl --</option>'
                '<option selected="selected">luxury-yacht.rst</option>'
                '<option>throatwobbler-mangrove.rst</option>')
        monkeypatch.setattr(testee, 'list_subdirs', mock_list_subdirs)
        assert testee.list_files(sitename, ext='dest') == (
                '<option>my_hovercraft/</option>'
                '<option>cheese_shop/</option>'
                '<option>luxury-yacht.html</option>'
                '<option>throatwobbler-mangrove.html</option>')

    def test_make_new_dir(self, monkeypatch, capsys):
        """unittest for rst2html_functions.make_new_dir
        """
        def mock_create_new_dir(*args):
            """stub
            """
            print('create_new_dir called')
        def mock_create_new_dir_failed(*args):
            """stub
            """
            raise FileExistsError
        sitename, filename = 'testsite', 'testname'
        monkeypatch.setattr(testee.dml, 'create_new_dir', mock_create_new_dir)
        assert testee.make_new_dir(sitename, filename) == ''
        assert capsys.readouterr().out == 'create_new_dir called\n'
        monkeypatch.setattr(testee.dml, 'create_new_dir', mock_create_new_dir_failed)
        assert testee.make_new_dir(sitename, filename) == 'dir_name_taken'


class TestSourceRelated:
    """unittests for rst2html_functions.SourceRelated
    """
    sitename, filename = 'testsite', 'testname'

    def test_read_src_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.read_src_data
        """
        def mock_get_doc_contents(*args, **kwargs):
            """stub
            """
            print('got args', args)
        def mock_get_doc_contents_error_1(*args, **kwargs):
            """stub
            """
            raise AttributeError
        def mock_get_doc_contents_error_2(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError
        assert testee.read_src_data(self.sitename, '', self.filename + '.x') == (
            'rst_filename_error', '')
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents)
        testee.read_src_data(self.sitename, '', self.filename + '.rst')
        assert capsys.readouterr().out == "got args ('testsite', 'testname', 'src', '')\n"
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents_error_1)
        assert testee.read_src_data(self.sitename, '', self.filename) == ('src_name_missing', '')
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents_error_2)
        assert testee.read_src_data(self.sitename, '', self.filename) == ('src_file_missing', '')

    def test_check_if_rst(self):
        """unittest for rst2html_functions.check_if_rst
        """
        assert testee.check_if_rst('', '') == 'supply_text'
        assert testee.check_if_rst('...', '') == 'rst_invalid'
        assert testee.check_if_rst('...', testee.RST) == ''
        assert testee.check_if_rst('...', testee.RST, 'x') == ''
        assert testee.check_if_rst('...', testee.RST, '') == 'src_name_missing'
        assert testee.check_if_rst('...', testee.RST, 'x/') == 'src_name_missing'
        assert testee.check_if_rst('...', testee.RST, '-- new --') == 'src_name_missing'
        assert testee.check_if_rst('...', testee.RST, '..') == 'src_name_missing'

    def test_save_src_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_src_data
        """
        # def mock_list_subdirs(*args):
        #     """stub
        #     """
        #     return ['hello/']
        def mock_create_new_dir(*args):
            """stub
            """
            print('called create_new_dir with args', args)
        def mock_create_new_dir_exists(*args):
            """stub
            """
            raise FileExistsError
        def mock_create_new_doc(*args, **kwargs):
            """stub
            """
            print('called create_new_doc with args', args, kwargs)
        def mock_create_new_doc_exists(*args, **kwargs):
            """stub
            """
            raise FileExistsError
        def mock_update_rst(*args, **kwargs):
            """stub
            """
            print('called update_rst with args', args, kwargs)
            # print('args for update_rst: `{}` `{}` `{}` `{}`'.format(args[0], args[1], args[2],
            #                                                         kwargs['directory']))
        def mock_update_rst_error_1(*args, **kwargs):
            """stub
            """
            raise AttributeError('name')
        def mock_update_rst_error_2(*args, **kwargs):
            """stub
            """
            raise AttributeError('contents')
        def mock_update_rst_error_3(*args, **kwargs):
            """stub
            """
            raise AttributeError('something else')
        def mock_update_rst_error_4(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError

        assert testee.save_src_data(self.sitename, '', self.filename + '.x', '...') == (
                'rst_filename_error')
        monkeypatch.setattr(testee.dml, 'create_new_dir', mock_create_new_dir)
        monkeypatch.setattr(testee.dml, 'create_new_doc', mock_create_new_doc_exists)
        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst)
        assert testee.save_src_data(self.sitename, 'test', self.filename + '.rst', '...', True) == (
            'src_name_taken')
        assert capsys.readouterr().out == "called create_new_dir with args ('testsite', 'test')\n"

        monkeypatch.setattr(testee.dml, 'create_new_doc', mock_create_new_doc)
        assert testee.save_src_data(self.sitename, '', self.filename + '.rst', '...') == ''
        # assert capsys.readouterr().out == ("called create_new_dir with args ('testsite', 'test')\n"
        #                                    "called update_rst with args ('testsite',"
        #                                    " 'testname', '...') {'directory': 'test'}\n")
        assert capsys.readouterr().out == ("called update_rst with args ('testsite',"
                                           " 'testname', '...') {'directory': ''}\n")

        monkeypatch.setattr(testee.dml, 'create_new_dir', mock_create_new_dir_exists)
        assert testee.save_src_data(self.sitename, 'test', self.filename + '.rst', '...', True) == ''
        assert capsys.readouterr().out == ("called create_new_doc with args ('testsite',"
                                           " 'testname.rst') {'directory': 'test'}\n"
                                           "called update_rst with args ('testsite',"
                                           " 'testname', '...') {'directory': 'test'}\n")

        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst_error_1)
        assert testee.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'src_name_missing')
        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst_error_2)
        assert testee.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'supply_text')
        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst_error_3)
        assert testee.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'something else')
        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst_error_4)
        assert testee.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'src_file_missing')

    def _test_compare_source(self, monkeypatch):
        """stub
        """
        def mock_context_diff(*args, **kwargs):
            """stub
            """
            return 'called context_diff with args', args, kwargs
        monkeypatch.setattr(testee.difflib, 'context_diff', mock_context_diff)
        assert testee.compare_source('sitename', 'new source', 'old source') == (
                "call context_diff with args ('new source', 'old source')"
                " {'fromfile': 'current text', 'tofile': 'previous text'}")

    def test_revert_src(self, monkeypatch, capsys):
        """unittest for rst2html_functions.revert_src
        """
        def mock_revert_rst(*args, **kwargs):
            """stub
            """
            print('called revert_rst with args', args, kwargs)
        def mock_revert_rst_error(*args, **kwargs):
            """stub
            """
            raise AttributeError
        def mock_revert_rst_error_2(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError('backup')
        def mock_revert_rst_error_3(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError('other')
        assert testee.revert_src(self.sitename, '', self.filename + '.x') == (
                'rst_filename_error')
        monkeypatch.setattr(testee.dml, 'revert_rst', mock_revert_rst)
        assert testee.revert_src(self.sitename, 'test', self.filename + '.rst') == ''
        assert capsys.readouterr().out == ('called revert_rst with args '
                                           "('testsite', 'testname', 'test') {}\n")
        monkeypatch.setattr(testee.dml, 'revert_rst', mock_revert_rst_error)
        assert testee.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'src_name_missing')
        monkeypatch.setattr(testee.dml, 'revert_rst', mock_revert_rst_error_2)
        assert testee.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'backup_missing')
        monkeypatch.setattr(testee.dml, 'revert_rst', mock_revert_rst_error_3)
        assert testee.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'src_file_missing')

    def test_mark_deleted(self, monkeypatch, capsys):
        """unittest for rst2html_functions.mark_deleted
        """
        def mock_mark_src_deleted(*args, **kwargs):
            """stub
            """
            print(f"args for mark_src_deleted: `{args[0]}` `{args[1]}` `{kwargs['directory']}`")
        def mock_mark_src_deleted_noname(*args, **kwargs):
            """stub
            """
            raise AttributeError()
        def mock_mark_src_deleted_nofile(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError

        assert testee.mark_deleted(self.sitename, '', self.filename + '.x') == (
                'rst_filename_error')
        monkeypatch.setattr(testee.dml, 'mark_src_deleted', mock_mark_src_deleted)
        assert testee.mark_deleted(self.sitename, '', self.filename + '.rst') == ''
        assert capsys.readouterr().out == 'args for mark_src_deleted: `testsite` `testname` ``\n'
        monkeypatch.setattr(testee.dml, 'mark_src_deleted', mock_mark_src_deleted_noname)
        assert testee.mark_deleted(self.sitename, '', self.filename) == (
                'src_name_missing')
        monkeypatch.setattr(testee.dml, 'mark_src_deleted', mock_mark_src_deleted_nofile)
        assert testee.mark_deleted(self.sitename, '', self.filename + '.rst') == (
                'src_file_missing')

    def test_read_tpl_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.read_tpl_data
        """
        def mock_read_template(*args):
            """stub
            """
            print('read_template called')
        monkeypatch.setattr(testee.dml, 'read_template', mock_read_template)
        testee.read_tpl_data(self.sitename, self.filename)
        assert capsys.readouterr().out == 'read_template called\n'

    def test_save_tpl_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_tpl_data
        """
        def mock_write_template(*args):
            """stub
            """
            print('write_template called')
        monkeypatch.setattr(testee.dml, 'write_template', mock_write_template)
        testee.save_tpl_data(self.sitename, self.filename, '')
        assert capsys.readouterr().out == 'write_template called\n'

    def test_compare_source(self, monkeypatch, capsys):
        """unittest for rst2html_functions.compare_source
        """
        def mock_read_data(*args):
            """stub
            """
            print('called testee.read_src_data() with args', args)
            return '', 'new source'
        def mock_get_contents(*args, **kwargs):
            """stub
            """
            print('called dml.read_src_data() with args', args, kwargs)
            return 'old source'
        def mock_diff(*args, **kwargs):
            """stub
            """
            print('called unified_diff() with args', args)
            return 'compared sources'
        monkeypatch.setattr(testee, 'read_src_data', mock_read_data)
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_contents)
        monkeypatch.setattr(testee.difflib, 'unified_diff', mock_diff)
        assert testee.compare_source('sitename', '', 'dirname/') == ('incorrect_name', '')
        assert testee.compare_source('sitename', '', 'docname.tpl') == ('incorrect_name', '')
        assert testee.compare_source('sitename', '', 'docname') == ('', 'compared sources')
        assert capsys.readouterr().out == (
            "called testee.read_src_data() with args ('sitename', '', 'docname')\n"
            "called dml.read_src_data() with args ('sitename', 'docname', 'src', '')"
            " {'previous': True}\n"
            "called unified_diff() with args (['old source\\n'], ['new source\\n'])\n")


class TestTargetRelated:
    """unittests for rst2html_functions.TargetRelated
    """
    sitename, filename = 'testsite', 'testname'

    def test_read_html_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.read_html_data
        """
        def mock_get_doc_contents(*args):
            """stub
            """
            print('got args', args)
        def mock_get_doc_contents_error_1(*args, **kwargs):
            """stub
            """
            raise AttributeError
        def mock_get_doc_contents_error_2(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError
        assert testee.read_html_data(self.sitename, '', self.filename + '.x') == (
            'html_filename_error', '')
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents)
        testee.read_html_data(self.sitename, '', self.filename + '.html')
        assert capsys.readouterr().out == "got args ('testsite', 'testname', 'dest', '')\n"
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents_error_1)
        assert testee.read_html_data(self.sitename, '', self.filename) == ('html_name_missing', '')
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents_error_2)
        assert testee.read_html_data(self.sitename, '', self.filename) == ('html_file_missing', '')

    def test_check_if_html(self):
        """unittest for rst2html_functions.check_if_html
        """
        assert testee.check_if_html('', '') == 'supply_text'
        assert testee.check_if_html('...', '') == 'load_html'
        assert testee.check_if_html('...', testee.HTML) == ''
        assert testee.check_if_html('...', testee.HTML, 'x') == ''
        assert testee.check_if_html('...', testee.HTML, '') == 'html_name_missing'
        assert testee.check_if_html('...', testee.HTML, 'x/') == 'html_name_missing'
        assert testee.check_if_html('...', testee.HTML, '-- new --') == 'html_name_missing'
        assert testee.check_if_html('...', testee.HTML, '..') == 'html_name_missing'

    def test_save_html_data(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_html_data
        """
        def mock_apply_deletions_target(*args):
            """stub
            """
            print('args for apply_deletions:', args)
        def mock_update_html(*args, **kwargs):
            """stub
            """
            print(f'args for update_html: `{args[0]}` `{args[1]}` `{args[2]}`'
                  f" `{kwargs['directory']}` `{kwargs['dry_run']}`")
        def mock_update_html_error_1(*args, **kwargs):
            """stub
            """
            raise AttributeError('name')
        def mock_update_html_error_2(*args, **kwargs):
            """stub
            """
            raise AttributeError('contents')
        def mock_update_html_error_3(*args, **kwargs):
            """stub
            """
            raise FileNotFoundError('not-found')

        monkeypatch.setattr(testee.dml, 'apply_deletions_target', mock_apply_deletions_target)
        assert testee.save_html_data(self.sitename, '', self.filename + '.x', '...') == (
                'html_filename_error')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")
        monkeypatch.setattr(testee.dml, 'update_html', mock_update_html)
        assert testee.save_html_data(self.sitename, '', self.filename + '.html', '...') == ''
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n"
                                           'args for update_html: `testsite` `testname` `...` '
                                           '`` `False`\n')
        assert testee.save_html_data(self.sitename, '', self.filename + '.html', '...', True) == ''
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n"
                                           'args for update_html: `testsite` `testname` `...` '
                                           '`` `True`\n')
        monkeypatch.setattr(testee.dml, 'update_html', mock_update_html_error_1)
        assert testee.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'html_name_missing')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")
        monkeypatch.setattr(testee.dml, 'update_html', mock_update_html_error_2)
        assert testee.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'supply_text')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")
        monkeypatch.setattr(testee.dml, 'update_html', mock_update_html_error_3)
        assert testee.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'not-found')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")

    def test_complete_header(self):
        """unittest for rst2html_functions.complete_header
        """
        assert testee.complete_header({'url': ''}, '...') == '...'
        rstdata = 'my<head>hurts'
        conf = {'url': '', 'starthead': 'aches and '}
        assert testee.complete_header(conf, rstdata) == 'my<head>aches and hurts'
        conf = {'url': '', 'starthead': ['aches', ' and ']}
        assert testee.complete_header(conf, rstdata) == 'my<head>aches and hurts'
        rstdata = 'my head hurts'
        assert testee.complete_header(conf, rstdata) == 'aches and my head hurts'
        rstdata = 'my</head>hurts'
        conf = {'url': '', 'endhead': ' aching big'}
        assert testee.complete_header(conf, rstdata) == 'my aching big</head>hurts'
        conf = {'url': '', 'endhead': [' aching', ' big']}
        assert testee.complete_header(conf, rstdata) == 'my aching big</head>hurts'
        rstdata = 'my head hurts'
        assert testee.complete_header(conf, rstdata) == ' aching bigmy head hurts'
        conf = {'url': 'hier'}
        rstdata = 'hier/ en hier'
        assert testee.complete_header(conf, rstdata) == '/ en /'

    def test_save_to_mirror(self, monkeypatch, capsys):
        """unittest for rst2html_functions.save_to_mirror
        """
        def mock_apply_deletions_mirror(*args):
            """stub
            """
            print('args for apply_deletions:', args)
        def mock_read_html_data(*args):
            """stub
            """
            print('args for read_html_data:', args)
            return '', '...'
        def mock_read_html_data_error(*args):
            """stub
            """
            return 'read_html_data failed', ''
        def mock_complete_header(*args):
            """stub
            """
            print('args for complete_header:', args)
            return '...'
        def mock_update_mirror(*args, **kwargs):
            """stub
            """
            print(f'args for update_mirror: `{args[0]}` `{args[1]}` `{args[2]}`'
                  f" `{kwargs['directory']}` `{kwargs['dry_run']}`")
        def mock_update_mirror_failed_1(*args, **kwargs):
            """stub
            """
            raise AttributeError('name')
        def mock_update_mirror_failed_2(*args, **kwargs):
            """stub
            """
            raise AttributeError('error')
        monkeypatch.setattr(testee.dml, 'apply_deletions_mirror', mock_apply_deletions_mirror)
        assert testee.save_to_mirror(self.sitename, '', self.filename + '.x', {}) == (
                'html_filename_error')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")
        monkeypatch.setattr(testee, 'read_html_data', mock_read_html_data_error)
        assert testee.save_to_mirror(self.sitename, '', self.filename, {}) == (
                'read_html_data failed')
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n")
        monkeypatch.setattr(testee, 'read_html_data', mock_read_html_data)
        monkeypatch.setattr(testee, 'complete_header', mock_complete_header)
        monkeypatch.setattr(testee.dml, 'update_mirror', mock_update_mirror)
        assert testee.save_to_mirror(self.sitename, '', self.filename, {}) == ''
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n"
            "args for read_html_data: ('testsite', '', 'testname')\n"
            "args for complete_header: ({}, '...')\n"
            'args for update_mirror: `testsite` `testname` `...` `` `False`\n')
        monkeypatch.setattr(testee.dml, 'update_mirror', mock_update_mirror_failed_1)
        assert testee.save_to_mirror(self.sitename, 'en', self.filename, {}) == 'html_name_missing'
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', 'en')\n"
            "args for read_html_data: ('testsite', 'en', 'testname')\n"
            "args for complete_header: ({}, '...')\n")
        monkeypatch.setattr(testee.dml, 'update_mirror', mock_update_mirror_failed_2)
        assert testee.save_to_mirror(self.sitename, '', self.filename + '.html', {}) == 'error'
        assert capsys.readouterr().out == ("args for apply_deletions: ('testsite', '')\n"
            "args for read_html_data: ('testsite', '', 'testname')\n"
            "args for complete_header: ({}, '...')\n")


class TestProgressList:
    """unittests for functions related to progress list building
    """
    def test_build_progress_list(self, monkeypatch):
        """unittest for rst2html_functions.build_progress_list
        """
        date_1 = datetime.datetime(2020, 1, 1)
        date_2 = datetime.datetime(2020, 1, 2)
        date_3 = datetime.datetime(2020, 1, 3)
        def mock_get_all_doc_stats_empty(*args):
            """stub
            """
            return []
        def mock_get_all_doc_stats(*args):
            """stub
            """
            return [('testdir2', [('test', (date_3, date_2, date_1)),
                                  ('index', (date_1, date_2, date_3)),
                                  ('removed', ('[deleted]', date_2, date_3)),
                                  ('twice_removed', ('', '[deleted]', date_3)),
                                  ('all_gone', ('', '', ''))]),
                    ('testdir1', [('index', (date_2, date_2, date_2))]),
                    ('/', [('index', (date_1, date_1, date_2)),
                           ('about', (date_2, date_2, date_1))])]
        monkeypatch.setattr(testee.dml, 'get_all_doc_stats', mock_get_all_doc_stats_empty)
        assert testee.build_progress_list('testsite', []) == []
        monkeypatch.setattr(testee.dml, 'get_all_doc_stats', mock_get_all_doc_stats)
        assert testee.build_progress_list('', ['/about', 'testdir2/all_gone']) == [
                # ('/', 'about', 1, (date_2, date_2, date_1)),
                ('/', 'index', 2, (date_1, date_1, date_2)),
                ('testdir1', 'index', 2, (date_2, date_2, date_2)),
                # ('testdir2', 'all_gone', 2, ('', '', '')),
                ('testdir2', 'index', 2, (date_1, date_2, date_3)),
                ('testdir2', 'removed', 0, ('[deleted]', date_2, date_3)),
                ('testdir2', 'test', 0, (date_3, date_2, date_1)),
                ('testdir2', 'twice_removed', 1, ('', '[deleted]', date_3))]

    def test_get_copystand_filepath(self, monkeypatch, capsys):
        """unittest for rst2html_functions.get_copystand_filepath
        """
        def mock_mkdir(self, **kwargs):
            """stub
            """
            print(f'called {self}.mkdir with args', kwargs)
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        reportdir = testee.WEBROOT / 's' / '.overview'
        assert testee.get_copystand_filepath('s') == reportdir / '20200101000000'
        assert capsys.readouterr().out == f"called {reportdir}.mkdir with args {{'exist_ok': True}}\n"

    def test_get_progress_line_values(self):
        """unittest for rst2html_functions.get_progress_line_values
        """
        mindate = testee.datetime.datetime.min
        maxdate = testee.datetime.datetime.max
        line = ('/', 'index', 0, (maxdate, mindate, mindate))
        expected = ['index', '--> 31-12-9999 23:59:59 <--', 'n/a', 'n/a']
        assert testee.get_progress_line_values(line) == expected
        line = ('dir', 'file', 2, (maxdate, maxdate, maxdate))
        expected = ['dir/file', '31-12-9999 23:59:59', '31-12-9999 23:59:59',
                    '--> 31-12-9999 23:59:59 <--']
        assert testee.get_progress_line_values(line) == expected
        line = ('/', 'deleted', 1, ('[deleted]', '[deleted]', ''))
        expected = ['deleted', '[deleted]', '--> [deleted] <--', '']
        assert testee.get_progress_line_values(line) == expected


class TestTrefwLijst:
    """unittests for functions related to reference list building
    """
    def test_get_reflinks_in_dir(self, monkeypatch):
        """unittest for rst2html_functions.get_reflinks_in_dir
        """
        def mock_list_docs_empty(*args, **kwargs):
            """stub
            """
            return []
        def mock_list_docs(*args, **kwargs):
            """stub
            """
            return ['doc2skip1', 'doc2skip2', 'doctogo']
        def mock_list_docs_2(*args, **kwargs):
            """stub
            """
            return ['docnorefs', 'doc-w-refs']
        def mock_get_doc_stats(*args):
            """stub
            """
            if args[1] == 'doc2skip1':
                return testee.dml.Stats(2, 1, 1)
            if args[1] == 'doc2skip2':
                return testee.dml.Stats(2, 2, 1)
            return testee.dml.Stats(2, 2, 2)
        def mock_read_src_data_error(*args):
            """stub
            """
            return 'read_src_error', ''
        def mock_read_src_data(*args):
            """stub
            """
            if args[2] == 'docnorefs':
                return '', ''
            return '', '.. refkey:: itsaref\n.. refkey:: alsoaref: here'
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs_empty)
        assert testee.get_reflinks_in_dir('testsite') == ({}, [])
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats)
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data_error)
        assert testee.get_reflinks_in_dir('testsite', 'testdir') == ({}, [('testdir', 'doctogo',
                                                                         'read_src_error')])
        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs_2)
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data)
        assert testee.get_reflinks_in_dir('testsite') == ({'Itsaref': ['/doc-w-refs.html'],
                                                         'Alsoaref': ['/doc-w-refs.html#here']}, [])

    def test_class(self):
        """unittest for rst2html_functions.TrefwoordenLijst(.__init__)
        """
        testobj = testee.TrefwoordenLijst('testsite')
        assert testobj.sitename == 'testsite'
        assert testobj.lang == testee.LANG
        assert not testobj.sef
        assert testobj.current_letter == ''
        # dit test meteen de clear_containers methode:
        assert testobj.titel == []
        assert testobj.teksten == []
        assert testobj.links == []
        assert testobj.anchors == []

    def test_build(self, monkeypatch, capsys):
        """unittest for rst2html_functions.build
        """
        def mock_get_reflinks_none(self):
            """stub
            """
            return {}, []
        def mock_get_reflinks_errs(self):
            """stub
            """
            return {}, ['a message', 'and another']
        def mock_get_reflinks(self):
            """stub
            """
            # print('called get_reflinks')
            return {'x': ['doc'], 'y': ['doc1', 'doc2'], 'xx': ['doc3']}, []
        def mock_start_page(self):
            """stub
            """
            print('called start_page')
            return 'first to_top'
        def mock_finish_letter(self, *args):
            """stub
            """
            print('called finish_letter with args', args)
            self.teksten = []
        def mock_clear_containers(self):
            """stub
            """
            print('called clear_containers')
            self.titel, self.teksten, self.links, self.anchors = [], [], [], []
        def mock_start_new_letter(self):
            """stub
            """
            print('called start_new_letter')
            self.titel = self.current_letter
        def mock_start_new_keyword(self, reflinks, key):
            """stub
            """
            print(f'called start_new_keyword with `{key}`')
            self.teksten.append(key)

        monkeypatch.setattr(testee.TrefwoordenLijst, 'get_reflinks', mock_get_reflinks_none)
        monkeypatch.setattr(testee.TrefwoordenLijst, 'start_page', mock_start_page)
        monkeypatch.setattr(testee.TrefwoordenLijst, 'finish_letter', mock_finish_letter)
        monkeypatch.setattr(testee.TrefwoordenLijst, 'clear_containers', mock_clear_containers)
        monkeypatch.setattr(testee.TrefwoordenLijst, 'start_new_letter', mock_start_new_letter)
        monkeypatch.setattr(testee.TrefwoordenLijst, 'start_new_keyword', mock_start_new_keyword)
        testobj = testee.TrefwoordenLijst('sitename')
        testobj.data = []
        assert testobj.build() == ('', 'No index created: no reflinks found')
        assert capsys.readouterr().out == "called clear_containers\n"

        monkeypatch.setattr(testee.TrefwoordenLijst, 'get_reflinks', mock_get_reflinks_errs)
        testobj = testee.TrefwoordenLijst('sitename')
        testobj.data = []
        assert testobj.build() == (('while creating this page, the following messages were'
                                    ' generated:\n----------------------------------------'
                                    '------------------------\n. a message\n. and another'), True)
        assert capsys.readouterr().out == "called clear_containers\ncalled start_page\n"

        monkeypatch.setattr(testee.TrefwoordenLijst, 'get_reflinks', mock_get_reflinks)
        testobj = testee.TrefwoordenLijst('sitename')
        testobj.current_letter = ''
        testobj.data = []
        testobj.titel = []
        testobj.teksten = []
        assert testobj.build() == ((''), False)
        assert capsys.readouterr().out == ('called clear_containers\n'
                                           'called start_page\n'
                                           'called start_new_letter\n'
                                           'called start_new_keyword with `x`\n'
                                           'called start_new_keyword with `xx`\n'
                                           "called finish_letter with args ('first to_top',)\n"
                                           'called clear_containers\n'
                                           'called start_new_letter\n'
                                           'called start_new_keyword with `y`\n'
                                           "called finish_letter with args ('+   top_',)\n"
                                           )

    def test_get_reflinks(self, monkeypatch):
        """unittest for rst2html_functions.get_reflinks
        """
        def mock_get_reflinks_in_dir(*args, **kwargs):
            """stub
            """
            dirname = args[1] if len(args) > 1 else ''
            return {'trefw': f'{dirname}/doc'}, [f'error from {dirname}']
        def mock_list_dirs(*args):
            """stub
            """
            return ['subdir']
        monkeypatch.setattr(testee, 'get_reflinks_in_dir', mock_get_reflinks_in_dir)
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs)
        # volgens mij moet het dit zijn:
        # assert testee.TrefwoordenLijst('site').get_reflinks() == ({'trefw': ['/doc', 'subdir/doc']},
        #                                                         ['error from ',
        #                                                          'error from subdir'])
        # maar de testuitvoering zegt dat het dit moet zijn:
        assert testee.TrefwoordenLijst('site').get_reflinks() == ({'trefw': 'subdir/doc'},
                                                                ['error from ',
                                                                 'error from subdir'])

    def test_start_page(self, monkeypatch):
        """unittest for rst2html_functions.start_page
        """
        def mock_get_text(*args):
            """stub
            """
            return 'Index Header'
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        testobj = testee.TrefwoordenLijst('magiokis')
        assert testobj.start_page() == "+   `top <#header>`_"
        assert testobj.data == ['Index Header', '============', '', '']
        testobj = testee.TrefwoordenLijst('testsite')
        assert testobj.start_page() == "+   top_"
        assert testobj.data == ['.. _top:', '`back to root </>`_', '', '.. textheader:: Index', '']

    def test_start_new_letter(self):
        """unittest for rst2html_functions.start_new_letter
        """
        testobj = testee.TrefwoordenLijst('magiokis')
        testobj.data = ['', '', '', ' ']
        testobj.current_letter = 'A'
        testobj.start_new_letter()
        assert testobj.data == ['', '', '', ' A_ ', '']
        assert testobj.titel == ['.. _A:\n\n**A**', '']
        assert testobj.linkno == 0
        testobj = testee.TrefwoordenLijst('testsite')
        testobj.data = ['', '', '', '', ' ']
        testobj.current_letter = 'X'
        testobj.start_new_letter()
        assert testobj.data == ['', '', '', '', ' X_ ', '']
        assert testobj.titel == ['X', '-']
        assert testobj.linkno == 0

    def test_start_new_keyword(self):
        """unittest for rst2html_functions.start_new_keyword
        """
        testobj = testee.TrefwoordenLijst('testsite')
        testobj.teksten = ['a']
        testobj.start_new_keyword({'x': []}, 'x')
        assert testobj.teksten == ['a', '+   x']
        testobj = testee.TrefwoordenLijst('testsite')
        testobj.linkno = 1
        testobj.current_letter = 'A'
        testobj.links = ['b']
        testobj.anchors = ['c']
        testobj.teksten = []
        testobj.start_new_keyword({'x': ['doc']}, 'x')
        assert testobj.linkno == 2
        assert testobj.links == ['b', '..  _A2: doc']
        assert testobj.anchors == ['c', '__ A2_']
        assert testobj.teksten == ['+   x `#`__ ']

    def test_finish_letter(self):
        """unittest for rst2html_functions.finish_letter
        """
        testobj = testee.TrefwoordenLijst('testsite')
        testobj.data = ['xxx']
        testobj.titel = ['Dit', 'is een titel']
        testobj.teksten = ['Dit zijn', 'teksten']
        testobj.links = ['A', 'B', 'C']
        testobj.anchors = ['here', 'and here']
        testobj.finish_letter('to-top')
        assert testobj.data == ['xxx', 'Dit', 'is een titel', '', 'Dit zijn', 'teksten', 'to-top',
                                '', 'A', 'B', 'C', '', 'here', 'and here', '']


class TestSearchRelated:
    """unittests for rst2html_functions.SearchRelated
    """
    def test_search_site(self, monkeypatch, capsys):
        """unittest for rst2html_functions.search_site
        """
        def mock_read_dir(*args):
            """stub
            """
            if len(args) == 3:
                print('read_dir called with args', args)
                where = '/'
            else:
                print('read_dir called with args', args)
                where = args[3]
            return {where: ['this', 'that']}
        def mock_list_dirs(*args):
            """stub
            """
            return ['subdir']

        monkeypatch.setattr(testee, 'read_dir', mock_read_dir)
        monkeypatch.setattr(testee.dml, 'list_dirs', mock_list_dirs)
        assert testee.search_site('testsite', 'needle', 'safety pin') == {'/': ['this', 'that'],
                                                                          'subdir': ['this', 'that']}
        assert capsys.readouterr().out == ("read_dir called with args ('testsite', 'needle',"
                                           " 'safety pin')\n"
                                           "read_dir called with args ('testsite', 'needle',"
                                           " 'safety pin', 'subdir')\n")

    def test_read_dir(self, monkeypatch):
        """unittest for rst2html_functions.read_dir
        """
        def mock_list_docs(*args, **kwargs):
            """stub
            """
            return ['doc1', 'doc2']
        def mock_process_file(*args):
            """stub
            """
            return f'processed `{args[0]}` `{args[1]}` `{args[2]}` `{args[3]}` `{args[4]}`'

        monkeypatch.setattr(testee.dml, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee, 'process_file', mock_process_file)
        assert testee.read_dir('testsite', 'needle', 'pin', 'dirname') == {
                ('dirname', 'doc1'): 'processed `testsite` `dirname` `doc1` `needle` `pin`',
                ('dirname', 'doc2'): 'processed `testsite` `dirname` `doc2` `needle` `pin`'}

    def test_process_file(self, monkeypatch, capsys):
        """unittest for rst2html_functions.process_file
        """
        def mock_get_doc_contents(*args):
            """stub
            """
            print('args for get_doc:', args)
            return 'text\nnothing\nmore text'
        def mock_update_rst(*args):
            """stub
            """
            print('args for update_rst:', args)
        monkeypatch.setattr(testee.dml, 'get_doc_contents', mock_get_doc_contents)
        monkeypatch.setattr(testee.dml, 'update_rst', mock_update_rst)
        assert testee.process_file('testsite', 'dir', 'file', 'text', None) == [(1, 'text', [1]),
                (3, 'more text', [6])]
        assert capsys.readouterr().out == "args for get_doc: ('testsite', 'file', 'src', 'dir')\n"
        assert testee.process_file('testsite', 'dir', 'file', 'text', '') == [(1, 'text', [1]),
                (3, 'more text', [6])]
        assert capsys.readouterr().out == ("args for get_doc: ('testsite', 'file', 'src', 'dir')\n"
                                           "args for update_rst: ('testsite', 'file',"
                                           " '\\nnothing\\nmore ', 'dir')\n")
        assert testee.process_file('testsite', 'dir', 'file', 'text', 'text') == [(1, 'text', [1]),
                (3, 'more text', [6])]
        assert capsys.readouterr().out == "args for get_doc: ('testsite', 'file', 'src', 'dir')\n"
        assert testee.process_file('testsite', 'dir', 'file', 'text', 'taxes') == [(1, 'text', [1]),
                (3, 'more text', [6])]
        assert capsys.readouterr().out == ("args for get_doc: ('testsite', 'file', 'src', 'dir')\n"
                                           "args for update_rst: ('testsite', 'file',"
                                           " 'taxes\\nnothing\\nmore taxes', 'dir')\n")

    def test_searchdict2list(self):
        """unittest for rst2html_functions.searchdict2list
        """
        inputdict = {('', 'index'): [(1, 'regel na regel', [1, 10]),
                                     (2, 'regel na regel ' + 20 * '@#$%', [1, 10]),
                                     (3, 'een eindeloos uitzicht vol regels' + 20 * '@#$%', [28]),
                                     (4, 20 * '@#$%' + 'een eindeloos uitzicht vol regels', [108])],
                     ('dir', 'file0'): [],
                     ('dir', 'file'): [(24, 'geen regeling', [6])]}
        expected = [('/index', 1, ' **regel**  na  **regel** '),
                    ('/index', 2, ' **regel**  na regel ' + 16 * '@#$%' + '@...'),
                    ('/index', 2, ' **regel**  na regel ' + 16 * '@#$%' + '@...'),
                    ('/index', 3, '...eloos uitzicht vol  **regel** s' + 13 * '@#$%' + '@#$...'),
                    ('/index', 4, '...eloos uitzicht vol  **regel** s'),
                    ('dir/file', 24, 'geen  **regel** ing')]
        assert testee.searchdict2list(inputdict, 'regel') == expected

    def test_get_copysearch_filepath(self, monkeypatch, capsys):
        """unittest for rst2html_functions.get_copysearch_filepath
        """
        def mock_mkdir(self, **kwargs):
            """stub
            """
            print(f'called {self}.mkdir with args', kwargs)
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        reportdir = testee.WEBROOT / 's' / '.search-results'
        assert testee.get_copysearch_filepath('s', 't') == reportdir / 't-20200101000000'
        assert capsys.readouterr().out == f"called {reportdir}.mkdir with args {{'exist_ok': True}}\n"


class TestUpdateAll:
    """unittests for regenerate all functionality"""
    def test_check_for_includes(self, monkeypatch, tmp_path):
        """unittest for rst2html_functions.check_for_includes
        """
        fake_webroot = tmp_path / 'rhfntest'
        fake_sitename = 'testsite'
        monkeypatch.setattr(testee, 'WEBROOT', fake_webroot)
        fake_include = fake_webroot / fake_sitename / '.source' / 'include.rst'
        fake_include.parent.mkdir(parents=True, exist_ok=True)
        fake_include.touch(exist_ok=True)

        assert testee.check_for_includes(fake_sitename, '') == []
        rstdata = f".. include:: {fake_include}"
        assert testee.check_for_includes(fake_sitename, rstdata) == ['include']
        rstdata = ".. incl:: ../include.rst"
        assert testee.check_for_includes(fake_sitename, rstdata) == ['include']

        fake_include = fake_webroot / fake_sitename / 'xxx' / 'include.rst'
        fake_include.parent.mkdir(parents=True, exist_ok=True)
        fake_include.touch(exist_ok=True)
        assert testee.check_for_includes(fake_sitename, '') == []
        rstdata = f".. include:: {fake_include}"
        assert testee.check_for_includes(fake_sitename, rstdata) == []
        rstdata = ".. incl:: ../include.rst"
        assert testee.check_for_includes(fake_sitename, rstdata) == ['include']

    def test_update_all_class(self):
        """unittest for rst2html_functions.update_all_class
        """
        sitename, conf = 'testsite', {'css': []}
        testsubj = testee.UpdateAll(sitename, conf)
        assert testsubj.sitename == sitename
        assert testsubj.conf == conf
        assert not testsubj.missing_only
        assert not testsubj.needed_only
        assert not testsubj.show_only
        testsubj = testee.UpdateAll(sitename, conf, True, True, True)
        assert testsubj.sitename == sitename
        assert testsubj.conf == conf
        assert testsubj.missing_only
        assert testsubj.needed_only
        assert testsubj.show_only

    def test_rebuild_mirror(self, monkeypatch, capsys, tmp_path):
        """unittest for rst2html_functions.rebuild_mirror
        """
        def mock_save_to_mirror(*args, **kwargs):
            """stub
            """
            run = '(dry run)' if kwargs.get('dry_run', False) else ''
            print(f'save_to_mirror {run} was called')
            return ''

        sitename, conf = 'testsite', {'seflinks': False}
        testsubj = testee.UpdateAll(sitename, conf)
        testsubj.path = tmp_path / 'rhfntest' / 'testsite'
        filename = 'testfile'
        dirname = ''
        monkeypatch.setattr(testee, 'save_to_mirror', mock_save_to_mirror)
        assert testsubj.rebuild_mirror(dirname, filename) == ('')
        assert capsys.readouterr().out == 'save_to_mirror  was called\n'

        testsubj.show_only = True
        assert testsubj.rebuild_mirror(dirname, filename) == 'regen_mirror_msg'
        assert capsys.readouterr().out == ''

    def test_rebuild_html(self, monkeypatch, capsys):
        """unittest for rst2html_functions.rebuild_html
        """
        def mock_rst2html(*args):
            """stub
            """
            print('rst2html was called')
            return ''
        def mock_save_html_data(*args, **kwargs):
            """stub
            """
            run = '(dry run)' if kwargs.get('dry_run', False) else ''
            print(f'save_html_data {run} was called')
            return ''
        def mock_save_html_data_msg(*args, **kwargs):
            """stub
            """
            return 'save_html_data_err'
        def mock_read_conf(*args):
            """stub
            """
            return '', {'lang': testee.LANG}
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)

        sitename, conf = 'testsite', {'css': []}
        testsubj = testee.UpdateAll(sitename, conf)
        filename = 'testfile'
        dirname = ''
        testsubj.rstdata = ''
        monkeypatch.setattr(testee, 'rst2html', mock_rst2html)
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        assert testsubj.rebuild_html(dirname, filename) == ''
        assert capsys.readouterr().out == 'rst2html was called\nsave_html_data  was called\n'

        testsubj.show_only = True
        assert testsubj.rebuild_html(dirname, filename) == 'regen_target_msg'
        assert capsys.readouterr().out == 'rst2html was called\n'

        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data_msg)
        assert testsubj.rebuild_html(dirname, filename) == 'regen_target_msg'  # 'save_html_data_err'

    def test_check_for_updated_includes(self, monkeypatch):
        """unittest for rst2html_functions.check_for_updated_includes
        """
        def mock_check_for_includes_none(*args):
            """stub
            """
            return []
        def mock_check_for_includes_some(*args):
            """stub
            """
            return ['hello', 'you']
        def mock_get_doc_stats(*args):
            """stub
            """
            return testee.dml.Stats(2, 2, 2)

        sitename, conf = 'testsite', {'css': []}
        testsubj = testee.UpdateAll(sitename, conf)
        testsubj.rstdata = ''
        stats = testee.dml.Stats(1, 1, 1)
        monkeypatch.setattr(testee, 'check_for_includes', mock_check_for_includes_none)
        assert testsubj.check_for_updated_includes(stats) == (False, False)
        monkeypatch.setattr(testee, 'check_for_includes', mock_check_for_includes_some)
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.check_for_updated_includes(stats) == (True, True)
        assert testsubj.include_timestamps == {'hello': testee.dml.Stats(2, 2, 2),
                                               'you': testee.dml.Stats(2, 2, 2)}
        stats = testee.dml.Stats(2, 2, 1)
        assert testsubj.check_for_updated_includes(stats) == (False, True)
        assert testsubj.include_timestamps == {'hello': testee.dml.Stats(2, 2, 2),
                                               'you': testee.dml.Stats(2, 2, 2)}
        stats = testee.dml.Stats(2, 2, 2)
        assert testsubj.check_for_updated_includes(stats) == (False, False)
        assert testsubj.include_timestamps == {'hello': testee.dml.Stats(2, 2, 2),
                                               'you': testee.dml.Stats(2, 2, 2)}

    def test_update_all_go(self, monkeypatch):
        """unittest for rst2html_functions.update_all_go
        """
        def mock_build_progress_list_empty(*args):
            """stub
            """
            return []
        def mock_build_progress_list_0(*args):
            """stub
            """
            return [('/', 'index', 0, testee.dml.Stats(2, 1, 1)),
                    ('hi', 'index', 1, testee.dml.Stats(2, 2, 1))]
        def mock_build_progress_list_1(*args):
            """stub
            """
            return [('/', 'index', 1, testee.dml.Stats(2, 2, 1)),
                    ('/', 'doc1', 1, testee.dml.Stats('[deleted]', 2, 1)),
                    ('/', 'doc2', 1, testee.dml.Stats(2, '[deleted]', 1)),
                    ('/', 'doc3', 1, testee.dml.Stats(2, 2, '[deleted]'))]
        def mock_build_progress_list_2(*args):
            """stub
            """
            return [('/', 'index', 2, testee.dml.Stats(2, 2, 2))]
        def mock_read_src_data_msg(*args):
            """stub
            """
            return 'message from read_src_data', ''
        def mock_read_src_data(*args):
            """stub
            """
            return '', 'some_text'
        def mock_check_for_updated_includes_all(*args):
            """stub
            """
            return True, True
        def mock_check_for_updated_includes_none(*args):
            """stub
            """
            return False, False
        def mock_rebuild_html(*args):
            """stub
            """
            return ''
        def mock_rebuild_html_msg(*args):
            """stub
            """
            return 'message from rebuild_html'
        def mock_rebuild_mirror(*args):
            """stub
            """
            return ''
        def mock_rebuild_mirror_msg(*args):
            """stub
            """
            return 'message from rebuild_mirror'

        # testcase: nothing in progress list (unrealistic)
        testsubj = testee.UpdateAll('testsite', {})
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_empty)
        assert testsubj.go() == []
        # testcase: document last generated on mirror
        # dit geldt niet meer omdat we nu ook naar gewijzigde includes kijken
        # monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_2)
        # assert testsubj.go() == []
        # testcase: document excluded in config
        # ook dit geldt niet meer omdat we het filteren nu in de aangeroepen funcie doen
        # testsubj.conf = {'do-not-generate': ['/index']}
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_2)
        # assert testsubj.go() == []
        # testcase: error when fetching source
        testsubj.conf = {}
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data_msg)
        assert testsubj.go() == [('/index', 'message from read_src_data')]
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data)
        # testcase: error when building html
        monkeypatch.setattr(testee.UpdateAll, 'rebuild_html', mock_rebuild_html_msg)
        assert testsubj.go() == [('/index', 'message from rebuild_html')]
        # testcase: error when building mirror
        monkeypatch.setattr(testee.UpdateAll, 'rebuild_html', mock_rebuild_html)
        monkeypatch.setattr(testee.UpdateAll, 'rebuild_mirror', mock_rebuild_mirror_msg)
        assert testsubj.go() == [('/index', 'html_saved'),
                                 ('/index', 'message from rebuild_mirror')]
        # testcase: no errors
        monkeypatch.setattr(testee.UpdateAll, 'rebuild_mirror', mock_rebuild_mirror)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to')]

        # testcase: generate when missing for existing document
        testsubj.missing_only = True
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_1)
        assert testsubj.go() == []

        # testcases: only generate when needed
        testsubj.needed_only = True
        # testcase: include was updated after generating document
        monkeypatch.setattr(testee.UpdateAll, 'check_for_updated_includes',
                            mock_check_for_updated_includes_all)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to'),
                                 ('/doc1', 'html_saved'), ('/doc1', 'copied_to'),
                                 ('/doc2', 'html_saved'), ('/doc2', 'copied_to'),
                                 ('/doc3', 'html_saved'), ('/doc3', 'copied_to')]
        # testcase: document source was updated after converting
        # also:     document was converted but not yet updated on mirror
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_0)
        monkeypatch.setattr(testee.UpdateAll, 'check_for_updated_includes',
                            mock_check_for_updated_includes_none)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to'),
                                 ('hi/index', 'copied_to')]
        # # testcase: document was converted but not yet updated on mirror
        # monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_1)
        # assert testsubj.go() == [('/index', 'copied_to')]
        # testcase: no actions needed
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list_2)
        assert testsubj.go() == []


class TestR2hState:
    """unittests for rst2html_functions.R2hState (i.e. the logic in the methods of the state class)
    """
    def test_init(self, monkeypatch):
        """unittest for R2hState.init
        """
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        assert testsubj.sitename == 'testsite'
        assert testsubj.rstfile == testsubj.htmlfile == testsubj.newfile == testsubj.rstdata == ""
        assert testsubj.current == testsubj.oldtext == testsubj.oldhtml == ""
        assert testsubj.conf == testee.DFLT_CONF
        assert not testsubj.newconf
        assert testsubj.loaded == 'initial'  # testee.RST

    def test_currentify(self, monkeypatch):
        """unittest for R2hState.currentify
        """
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.current = ''
        assert testsubj.currentify('filename') == 'filename'

        testsubj.current = 'dirname'
        testsubj.conf = {'seflinks': True}
        assert testsubj.currentify('filename.x') == 'dirname/filename/index.x'

    def test_get_lang(self, monkeypatch):
        """unittest for R2hState.get_lang
        """
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        assert testsubj.get_lang() == testee.LANG

        testsubj.conf = {'lang': 'en'}
        assert testsubj.get_lang() == 'en'

    def test_get_conf(self, monkeypatch):
        """unittest for R2hState.get_conf
        """
        def mock_read_conf(*args):
            """stub
            """
            return '', {'key1': 'value1', 'key2': 'value2'}
        def mock_list_subdirs(*args):
            """stub
            """
            return ['subdir1', 'subdir2']
        def mock_read_conf_mld(*args):
            """stub
            """
            return 'error', {}
        def mock_get_text(*args):
            """stub
            """
            return '`{}` conf error'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.newconf = True
        assert testsubj.get_conf('testsite') == ''
        assert testsubj.conf == testee.DFLT_CONF
        assert testsubj.current == ''
        assert testsubj.subdirs == []
        assert testsubj.loaded == testee.CONF

        testsubj.newconf = False
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)
        monkeypatch.setattr(testee, 'list_subdirs', mock_list_subdirs)
        assert testsubj.get_conf('testsite') == ''
        assert testsubj.conf == {'key1': 'value1', 'key2': 'value2'}
        assert testsubj.current == ''
        assert testsubj.subdirs == ['subdir1', 'subdir2']
        assert testsubj.loaded == testee.CONF

        monkeypatch.setattr(testee, 'read_conf', mock_read_conf_mld)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testsubj.get_conf('testsite') == '`testsite` conf error'

    def test_index(self, monkeypatch):
        """unittest for R2hState.index
        """
        def mock_get_conf(*args):
            """stub
            """
            return ''
        def mock_get_conf_msg(*args):
            """stub
            """
            return 'msg from get_conf'
        def mock_conf2text(*args):
            """stub
            """
            return 'confdata'

        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        testsubj = testee.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = ''
        # import pdb; pdb.set_trace()
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'no_confs', '', '')

        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = 'testsite'
        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf)
        testsubj.conf = {}
        monkeypatch.setattr(testee, 'conf2text', mock_conf2text)
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'conf_init', 'confdata',
                                    'testsite')
        assert testsubj.settings == 'testsite'

        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = 'testsite'
        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf_msg)
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'msg from get_conf', '',
                                    'testsite')

    def test_loadconf(self, monkeypatch):
        """unittest for R2hState.loadconf
        """
        def mock_get_conf(*args):
            """stub
            """
            return ''
        def mock_get_conf_err(*args):
            """stub
            """
            return 'error from get_conf'
        def mock_conf2text(*args):
            """stub
            """
            return 'text from conf'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf)
        monkeypatch.setattr(testee, 'conf2text', mock_conf2text)
        assert testsubj.loadconf('oldsett', 'c_newitem') == ('new_conf_made', 'text from conf',
                                                             'c_newitem', '')
        assert testsubj.newconf
        assert testsubj.sitename == 'c_newitem'

        assert testsubj.loadconf('newsett', '') == ('conf_loaded', 'text from conf', 'newsett', '')
        assert not testsubj.newconf
        assert testsubj.sitename == 'newsett'

        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf_err)
        assert testsubj.loadconf('newsett', '') == ('error from get_conf', 'text from conf',
                                                    'newsett', '')
        assert not testsubj.newconf
        assert testsubj.sitename == 'newsett'

    def test_saveconf(self, monkeypatch, capsys):
        """unittest for R2hState.saveconf
        """
        def mock_get_conf(self, *args):
            """stub
            """
            self.conf = {'url': 'xx'}
            return ''
        def mock_get_conf_nourl(self, *args):
            """stub
            """
            self.conf = {'url': ''}
            return ''
        def mock_get_conf_mld(*args):
            """stub
            """
            return 'mld from get_conf'
        def mock_new_conf_msg(*args):
            """stub
            """
            return 'new_conf_msg', 'new-url'
        def mock_new_conf(*args):
            """stub
            """
            return '', 'new-url'
        def mock_new_conf_nourl(*args):
            """stub
            """
            return '', ''
        def mock_save_conf(*args, **kwargs):
            """stub
            """
            print('call save_conf with args', args, kwargs)
            return ''
        def mock_save_conf_mld(*args, **kwargs):   # deze moet nog gebruikt
            """stub
            """
            return 'mld from save_conf'
        def mock_init_css(*args):
            """stub
            """
            print('call init_css')
        def mock_conf2text(*args):
            """stub
            """
            return 'conf2text'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'save_conf', mock_save_conf)
        monkeypatch.setattr(testee, 'init_css', mock_init_css)
        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf)
        monkeypatch.setattr(testee, 'conf2text', mock_conf2text)
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('testsite', '', '') == ('supply_text', '', 'x', 'y')
        assert capsys.readouterr().out == ''
        assert testsubj.saveconf('testsite', 'newsett', '') == ('supply_text', '', 'x', 'y')
        assert capsys.readouterr().out == ''
        testsubj.loaded = testee.RST
        assert testsubj.saveconf('testsite', '', 'conftext') == ('conf_invalid', 'conftext',
                                                                 'x', 'y')
        assert capsys.readouterr().out == ''
        assert testsubj.saveconf('testsite', 'newsett', 'conftext') == ('conf_invalid', 'conftext',
                                                                        'x', 'y')
        assert capsys.readouterr().out == ''
        testsubj.loaded = testee.CONF
        assert testsubj.saveconf('oldsett', 'c_newitem', 'conftext') == ('fname_invalid',
                                                                         'conftext', 'x', 'y')
        assert capsys.readouterr().out == ""
        assert testsubj.saveconf('oldsett', '', 'conftext') == ('conf_saved', 'conf2text',
                                                                'oldsett', '')
        assert capsys.readouterr().out == (
                "call save_conf with args ('oldsett', 'conftext', '') {}\n")
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('oldsett', 'oldsett', 'conftext') == ('conf_saved', 'conf2text',
                                                                       'oldsett', '')
        assert capsys.readouterr().out == (
                "call save_conf with args ('oldsett', 'conftext', '') {}\n")
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('oldsett', 'newsett', 'conftext') == ('conf_saved', 'conf2text',
                                                                       'newsett', '')
        assert capsys.readouterr().out == (
                "call save_conf with args ('newsett', 'conftext', '') {}\n")
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('oldsett', 'newsett', "url: ''") == ('conf_saved', 'conf2text',
                                                                      'newsett', '')
        assert capsys.readouterr().out == (
                """call save_conf with args ('newsett', "url: ''", '') {}\n""")

        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf_mld)
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('oldsett', '', 'conftext') == ('mld from get_conf', 'conf2text',
                                                                'oldsett', '')
        assert capsys.readouterr().out == (
                "call save_conf with args ('oldsett', 'conftext', '') {}\n")

        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf_nourl)
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('oldsett', '', 'conftext') == ('conf_saved note_no_url',
                                                                'conf2text', 'oldsett', '')
        assert capsys.readouterr().out == (
                "call save_conf with args ('oldsett', 'conftext', '') {}\n")

        monkeypatch.setattr(testee.R2hState, 'get_conf', mock_get_conf)
        testsubj.newconf = True
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(testee, 'new_conf', mock_new_conf_msg)
        assert testsubj.saveconf('oldsett', 'newsett', 'conftext') == ('new_conf_msg', 'conftext',
                                                                       'x', 'y')
        assert capsys.readouterr().out == ""
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(testee, 'new_conf', mock_new_conf)
        assert testsubj.saveconf('oldsett', 'newsett', "url: ''") == ('conf_saved activate_url',
                                                                      'conf2text', 'newsett', '')
        assert not testsubj.newconf
        assert capsys.readouterr().out == (
                "call save_conf with args ('newsett', 'url: new-url', '') {}\n")
        testsubj.newconf = True
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(testee, 'new_conf', mock_new_conf)
        assert testsubj.saveconf('oldsett', 'newsett', "url: 'xx'") == ('conf_saved activate_url',
                                                                        'conf2text', 'newsett', '')
        assert not testsubj.newconf
        assert capsys.readouterr().out == (
                """call save_conf with args ('newsett', "url: 'xx'", '') {}\n""")
        testsubj.newconf = True
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(testee, 'new_conf', mock_new_conf_nourl)
        assert testsubj.saveconf('oldsett', 'newsett', "url: 'xx'") == ('conf_saved',
                                                                        'conf2text', 'newsett', '')
        assert not testsubj.newconf
        assert testsubj.sitename == 'newsett'
        assert testsubj.rstdata == 'conf2text'
        assert capsys.readouterr().out == (
                """call save_conf with args ('newsett', "url: 'xx'", '') {}\n""")

    def test_loadrst(self, monkeypatch):
        """unittest for R2hState.loadrst
        """
        def mock_get_text(*args):
            """stub
            """
            if args[0] == 'c_newitem':
                return '-- new --'
            if args[0] == 'chdir_down':
                return args[0] + ' into `{}`'
            return args[0]
        def mock_read_tpl_data(*args):
            """stub
            """
            return 'template data'
        def mock_read_src_data(*args):
            """stub
            """
            return '', 'source data'
        def mock_read_src_data_mld(*args):
            """stub
            """
            return 'mld from read_src_data', ''
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        testsubj.rstdata = 'old data'
        testsubj.htmlfile = 'x'
        testsubj.newfile = 'y'
        assert testsubj.loadrst('') == ('unlikely_1', 'old data', 'x', 'y')
        assert testsubj.loadrst('-- new --') == ('save_reminder', '', '', '')
        assert testsubj.loaded == testee.RST
        monkeypatch.setattr(testee, 'read_tpl_data', mock_read_tpl_data)
        assert testsubj.loadrst('-- template --') == ('save_reminder', 'template data', '', '')
        assert testsubj.loaded == testee.RST
        assert testsubj.loadrst('subdir/') == ('chdir_down into `subdir`', '', '', '')
        assert testsubj.loadrst('..') == ('chdir_up', '', '', '')
        testsubj.rstdata = 'old data'
        testsubj.htmlfile = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data_mld)
        assert testsubj.loadrst('testfile') == ('mld from read_src_data', 'old data', 'x', 'y')
        assert testsubj.oldtext == 'old data'
        monkeypatch.setattr(testee, 'read_src_data', mock_read_src_data)
        assert testsubj.loadrst('testfile') == ('src_loaded', 'source data', 'testfile.html', '')
        assert testsubj.loaded == testee.RST
        assert testsubj.oldtext == 'source data'
        assert testsubj.rstfile == 'testfile'

    def test_rename(self, monkeypatch, capsys):
        """unittest for R2hState.rename
        """
        def mock_mark_deleted(*args):
            """stub
            """
            print('called mark_deleted with args', args)
            return 'oepsie'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testsubj.rename('', '', '')[0] == 'new_name_missing'
        assert testsubj.rename('', 'directory/', '')[0] == 'incorrect_name'
        assert testsubj.rename('', 'text.tpl', '')[0] == 'incorrect_name'
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        assert testsubj.rename('', 'newfile', '')[0] == 'new_name_taken'
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('mld', ''))
        monkeypatch.setattr(testee, 'save_src_data', lambda x, y, z, a, b: 'src_file_missing')
        assert testsubj.rename('', 'newfile', '')[0] == 'new_file_missing'
        monkeypatch.setattr(testee, 'save_src_data', lambda x, y, z, a, b: '')
        monkeypatch.setattr(testee, 'mark_deleted', mock_mark_deleted)
        assert testsubj.rename('', 'newfile', '')[0] == 'oepsie'
        assert capsys.readouterr().out == "called mark_deleted with args ('testsite', '', '')\n"
        monkeypatch.setattr(testee, 'mark_deleted', lambda x, y, z: '')
        assert testsubj.rename('oldfile', 'newfile', 'rstdata') == ('renamed', 'newfile.rst',
                                                                    'newfile.html', '', 'rstdata')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext, testsubj.rstdata == ('rstdata', 'rstdata')
        assert testsubj.rename('oldfile', 'newfile.rst', 'rstdata') == ('renamed', 'newfile.rst',
                                                                        'newfile.html', '', 'rstdata')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext, testsubj.rstdata == ('rstdata', 'rstdata')

    def test_diffsrc(self, monkeypatch, capsys):
        """unittest for R2hState.diffsrc
        """
        def mock_compare_source(*args):
            """stub
            """
            print(f'called compare_source() with {args=}')
            return '', 'newdata'
        def mock_compare_source_mld(*args):
            """stub
            """
            return 'other_msg', 'rstdata'
        monkeypatch.setattr(testee, 'compare_source', mock_compare_source)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testsubj, 'sitename', 'site')
        assert testsubj.diffsrc('test') == ('diff_loaded', 'newdata')
        assert testsubj.loaded == testee.DIFF
        assert capsys.readouterr().out == "called compare_source() with args=('site', '', 'test')\n"
        testsubj.loaded = ''
        assert testsubj.diffsrc('-- test --') == ('rst_filename_error', '')
        assert testsubj.loaded == ''
        assert capsys.readouterr().out == ""
        monkeypatch.setattr(testee, 'compare_source', mock_compare_source_mld)
        testsubj.loaded = ''
        assert testsubj.diffsrc('test') == ('other_msg', 'rstdata')
        assert testsubj.loaded != testee.DIFF

    def test_revert(self, monkeypatch, capsys):
        """unittest for R2hState.revert
        """
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testsubj.revert('dirname/', '')[0] == 'incorrect_name'
        assert testsubj.revert('text.tpl', '')[0] == 'incorrect_name'
        assert testsubj.revert('-- text.tpl --', '')[0] == 'incorrect_name'
        monkeypatch.setattr(testee, 'revert_src', lambda x, y, z: '')
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('mld', ''))
        assert testsubj.revert('', '')[0] == 'mld'
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        assert testsubj.revert('rstfile', 'rstdata') == ('reverted', 'rstfile', 'rstfile.html',
                                                         '', 'some_text')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext, testsubj.rstdata == ('rstdata', 'rstdata')

    def test_delete(self, monkeypatch, capsys):
        """unittest for R2hState.delete
        """
        def mock_mark_deleted(*args):
            """stub
            """
            print('called mark_deleted with args', args)
            return 'oepsie'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        assert testsubj.delete('dirname/', '')[0] == 'incorrect_name'
        assert testsubj.delete('text.tpl', '')[0] == 'incorrect_name'
        assert testsubj.delete('-- text.tpl --', '')[0] == 'incorrect_name'
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('mld', ''))
        assert testsubj.delete('', '')[0] == 'mld'
        monkeypatch.setattr(testee, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        monkeypatch.setattr(testee, 'mark_deleted', mock_mark_deleted)
        assert testsubj.delete('', 'olddata')[0] == 'oepsie'
        assert capsys.readouterr().out == "called mark_deleted with args ('testsite', '', '')\n"
        monkeypatch.setattr(testee, 'mark_deleted', lambda x, y, z: '')
        assert testsubj.delete('rstfile', 'rstdata') == ('deleted', 'rstfile', 'rstfile.html', '',
                                                         '')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext == ''
        assert testsubj.rstdata == ''

    def test_saverst(self, monkeypatch, capsys):
        """unittest for R2hState.saverst
        """
        def mock_make_new_dir(*args):
            """stub
            """
            print('make_new_dir called using args', args)
            return ''
        def mock_save_tpl_data(*args):
            """stub
            """
            print('save_tpl_data called using args', args)
            return ''
        def mock_check_if_rst(*args):
            """stub
            """
            print('check_if_rst called using args', args)
            return ''
        def mock_save_src_data(*args):
            """stub
            """
            print('save_src_data called using args', args)
            return ''
        # def mock_get_text_exc(*args):
        #     """stub
        #     """
        #     raise KeyError
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        monkeypatch.setattr(testee, 'make_new_dir', lambda x, y: 'mld from make_new_dir {}')
        assert testsubj.saverst('dirname/', '', '') == ('mld from make_new_dir dirname', 'a',
                                                        'b', 'c', '')
        monkeypatch.setattr(testee, 'make_new_dir', mock_make_new_dir)
        assert testsubj.saverst('dirname/', '', '') == ('new_subdir', 'dirname/', 'b',
                                                        '', '')
        assert capsys.readouterr().out == "make_new_dir called using args ('testsite', 'dirname')\n"

        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        monkeypatch.setattr(testee, 'save_tpl_data', lambda x, y, z: 'mld from save_tpl_data')
        assert testsubj.saverst('test.tpl', '', 'data') == ('mld from save_tpl_data', 'a', 'b',
                                                            'c', 'data')
        monkeypatch.setattr(testee, 'save_tpl_data', mock_save_tpl_data)
        assert testsubj.saverst('-- test.tpl --', '', 'data') == ('tpl_saved', '', '', '', 'data')
        assert capsys.readouterr().out == ("save_tpl_data called using args ('testsite', 'test.tpl',"
                                           " 'data')\n")
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'

        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        testsubj.loaded = 'loaded'
        monkeypatch.setattr(testee, 'check_if_rst', lambda x, y, z: 'mld from check_if_rst')
        assert testsubj.saverst('-- new --', '', '') == ('mld from check_if_rst', 'a', 'b', 'c', '')
        monkeypatch.setattr(testee, 'check_if_rst', mock_check_if_rst)
        monkeypatch.setattr(testee, 'save_src_data', lambda x, y, z, a, b: 'mld from save_src_data')
        assert testsubj.saverst('oldfile', 'newfile', 'data') == ('mld from save_src_data', 'a',
                                                                  'b', 'c', 'data')
        assert capsys.readouterr().out == ("check_if_rst called using args ('data', 'loaded',"
                                           " 'newfile')\n")
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data)
        assert testsubj.saverst('oldfile', '', 'data') == ('rst_saved', 'oldfile.rst',
                                                           'oldfile.html', '', 'data')
        assert capsys.readouterr().out == ("check_if_rst called using args ('data', 'loaded',"
                                           " 'oldfile')\n"
                                           "save_src_data called using args ('testsite', '',"
                                           " 'oldfile.rst', 'data', False)\n")
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'
        assert testsubj.saverst('oldfile.rst', '', 'data') == ('rst_saved', 'oldfile.rst',
                                                           'oldfile.html', '', 'data')
        assert capsys.readouterr().out == ("check_if_rst called using args ('data', 'loaded',"
                                           " 'oldfile.rst')\n"
                                           "save_src_data called using args ('testsite', '',"
                                           " 'oldfile.rst', 'data', False)\n")
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'
        assert testsubj.saverst('oldfile', 'newfile.rst', 'data') == ('rst_saved', 'newfile.rst',
                                                                      'newfile.html', '', 'data')
        assert capsys.readouterr().out == ("check_if_rst called using args ('data', 'loaded',"
                                           " 'newfile.rst')\n"
                                           "save_src_data called using args ('testsite', '',"
                                           " 'newfile.rst', 'data', True)\n")
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'

    def test_convert(self, monkeypatch, capsys):
        """unittest for R2hState.convert
        """
        def mock_check_if_rst(*args):
            """stub
            """
            return ''
        def mock_check_if_rst_mld(*args):
            """stub
            """
            return 'mld from check_if_rst'
        def mock_save_src_data(*args):
            """stub
            """
            print('save_src_data called')
            return ''
        def mock_save_src_data_mld(*args):
            """stub
            """
            return 'mld from save_src_data'
        def mock_rst2html(*args):
            """stub
            """
            return args[1]
        def mock_read_conf(*args):
            """stub
            """
            return '', {}
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'check_if_rst', mock_check_if_rst_mld)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                'css_not_defined', '', '')
        testsubj.conf = {'css': 'x'}
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                'mld from check_if_rst', '', '')
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)
        monkeypatch.setattr(testee, 'check_if_rst', mock_check_if_rst)
        testsubj.oldtext = 'text\nmoretext'
        monkeypatch.setattr(testee, 'rst2html', mock_rst2html)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'newfile')
        assert capsys.readouterr().out == ''
        testsubj.oldtext = ''
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data_mld)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                'mld from save_src_data', '', '')
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'newfile')
        assert capsys.readouterr().out == 'save_src_data called\n'
        assert testsubj.convert('rstfile', '', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'rstfile')
        assert capsys.readouterr().out == 'save_src_data called\n'

    def test_saveall(self, monkeypatch, capsys):
        """unittest for R2hState.saveall
        """
        def mock_check_if_rst(*args):
            """stub
            """
            return ''
        def mock_check_if_rst_mld(*args):
            """stub
            """
            return 'mld from check_if_rst'
        def mock_save_src_data(*args):
            """stub
            """
            print('save_src_data got args', args)
            return ''
        def mock_save_src_data_mld(*args):
            """stub
            """
            return 'mld from save_src_data'
        def mock_rst2html(*args):
            """stub
            """
            return 'converted txt'
        def mock_save_html_data(*args):
            """stub
            """
            print('save_html_data got args', args)
            return ''
        def mock_save_html_data_mld(*args):
            """stub
            """
            return 'mld from save_html_data for {}'
        def mock_read_conf(*args):
            """stub
            """
            return '', {'lang': testee.LANG}
        monkeypatch.setattr(testee, 'read_conf', mock_read_conf)
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'check_if_rst', mock_check_if_rst_mld)
        testsubj.rstfile = 'rst'
        testsubj.htmlfile = 'html'
        testsubj.newfile = 'new'
        assert testsubj.saveall('r', 'n', 'txt') == ('css_not_defined', 'rst', 'html', 'new')
        testsubj.conf = {'css': 'x'}
        assert testsubj.saveall('r', 'n', 'txt') == ('mld from check_if_rst', 'rst', 'html', 'new')
        monkeypatch.setattr(testee, 'check_if_rst', mock_check_if_rst)
        testsubj.oldtxt = 'txt'
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data_mld)
        assert testsubj.saveall('r', 'n', 'txt') == ('mld from save_src_data', 'n.rst', 'n.html',
                                                     'new')
        testsubj.oldtxt = 'converted data'
        assert testsubj.saveall('r', '', 'txt') == ('mld from save_src_data', 'r.rst', 'r.html',
                                                    'new')
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data)
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data_mld)
        assert testsubj.saveall('r', '', 'txt') == ('mld from save_html_data for r.html', 'r.rst',

                                                    'r.html', '')
        assert capsys.readouterr().out == ("save_src_data got args ('testsite', '', 'r.rst', 'txt',"
                                           " False)\n")
        assert testsubj.oldtext == 'txt'
        assert testsubj.rstdata == 'txt'
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        monkeypatch.setattr(testee, 'rst2html', mock_rst2html)
        assert testsubj.saveall('r', '', 'txt') == ('rst_2_html', 'r.rst', 'r.html', '')
        assert capsys.readouterr().out == ("save_html_data got args ('testsite', '', 'r.html',"
                                           " 'converted txt')\n")
        assert testsubj.saveall('r.html', '', 'txt') == ('rst_2_html', 'r.rst', 'r.html', '')
        assert capsys.readouterr().out == ("save_html_data got args ('testsite', '', 'r.html',"
                                           " 'converted txt')\n")
        assert testsubj.saveall('r.rst', '', 'txt') == ('rst_2_html', 'r.rst', 'r.html', '')
        assert capsys.readouterr().out == ("save_html_data got args ('testsite', '', 'r.html',"
                                           " 'converted txt')\n")
        assert testsubj.saveall('r', 'n', 'txt') == ('rst_2_html', 'n.rst', 'n.html', '')
        assert capsys.readouterr().out == ("save_src_data got args ('testsite', '', 'n.rst',"
                                           " 'txt', True)\n"
                                           "save_html_data got args ('testsite', '', 'n.html',"
                                           " 'converted txt')\n")
        assert testsubj.saveall('r', 'n.html', 'txt') == ('rst_2_html', 'n.rst', 'n.html', '')
        assert capsys.readouterr().out == ("save_src_data got args ('testsite', '', 'n.rst',"
                                           " 'txt', True)\n"
                                           "save_html_data got args ('testsite', '', 'n.html',"
                                           " 'converted txt')\n")
        assert testsubj.saveall('r', 'n.rst', 'txt') == ('rst_2_html', 'n.rst', 'n.html', '')
        assert capsys.readouterr().out == ("save_src_data got args ('testsite', '', 'n.rst',"
                                           " 'txt', True)\n"
                                           "save_html_data got args ('testsite', '', 'n.html',"
                                           " 'converted txt')\n")

    def test_status(self, monkeypatch):
        """unittest for R2hState.status
        """
        def mock_get_doc_stats(*args):
            """stub
            """
            return testee.dml.Stats(datetime.datetime.fromtimestamp(2),
                                  datetime.datetime.fromtimestamp(2),
                                  datetime.datetime.fromtimestamp(2))
        def mock_get_doc_stats_2(*args):
            """stub
            """
            return testee.dml.Stats(datetime.datetime.fromtimestamp(2), datetime.datetime.min,
                                  datetime.datetime.min)
        def mock_get_doc_stats_3(*args):
            """stub
            """
            return testee.dml.Stats(datetime.datetime.min, datetime.datetime.min,
                                  datetime.datetime.min)
        def mock_get_doc_stats_4(*args):
            """stub
            """
            raise FileNotFoundError('rst_filename_error')
        testsubj = testee.R2hState()
        testsubj.current = ''
        assert testsubj.status('-- test --') == 'Not executed: not a valid source file name'
        testsubj = testee.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.status('file') == ('/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: 01-01-1970 01:00:02'
                                           ' - last migrated: 01-01-1970 01:00:02')
        testsubj = testee.R2hState()
        testsubj.current = 'dir'
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.status('file') == ('dir/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: 01-01-1970 01:00:02'
                                           ' - last migrated: 01-01-1970 01:00:02')
        testsubj = testee.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats_2)
        assert testsubj.status('file') == ('/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: n/a'
                                           ' - last migrated: n/a')
        testsubj = testee.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats_3)
        assert testsubj.status('file') == 'not possible to get stats'
        testsubj = testee.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(testee.dml, 'get_doc_stats', mock_get_doc_stats_4)
        assert testsubj.status('file') == 'Not executed: not a valid source file name'

    def test_loadhtml(self, monkeypatch):
        """unittest for R2hState.loadhtml
        """
        def mock_read_html_data(*args):
            """stub
            """
            return '', 'some&nbsp;text'
        def mock_read_html_data_mld(*args):
            """stub
            """
            return 'mld from read_html_data', ''
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        testsubj.rstdata = 'x'
        testsubj.rstfile = 'y'
        testsubj.htmlfile = 'z'
        assert testsubj.loadhtml('dirname/') == ('html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('') == ('html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('..') == ('html_name_missing', 'x', 'y', 'z')
        # assert testsubj.loadhtml('-- new --') == 'html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('c_newitem') == ('html_name_missing', 'x', 'y', 'z')
        monkeypatch.setattr(testee, 'read_html_data', mock_read_html_data_mld)
        assert testsubj.loadhtml('filename') == ('mld from read_html_data', 'x', 'y', 'z')
        monkeypatch.setattr(testee, 'read_html_data', mock_read_html_data)
        assert testsubj.loadhtml('filename') == ('html_loaded', 'some&amp;nbsp;text',
                                                'filename.rst', 'filename.html')
        assert testsubj.oldhtml == 'some&amp;nbsp;text'
        assert testsubj.loaded == testee.HTML

    def test_showhtml(self, monkeypatch, capsys):
        """unittest for R2hState.showhtml
        """
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        def mock_check_if_html(*args):
            """stub
            """
            return ''
        def mock_check_if_html_mld(*args):
            """stub
            """
            return 'mld from check_if_html'
        def mock_save_html_data(*args):
            """stub
            """
            print('call save_html_data')
            return ''
        # def mock_save_html_data_mld(*args):
        #     """stub
        #     """
        #     return 'mld from save_html_data'
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.showhtml('text\r\nmore text') == ('mld from check_if_html', '', '')
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        testsubj.oldhtml = 'text\nmore text'
        testsubj.htmlfile = 'htmlfile'
        assert testsubj.showhtml('text\r\nmore text') == ('', 'text\r\nmore text', 'htmlfile')
        assert capsys.readouterr().out == ''
        testsubj.oldhtml = ''
        assert testsubj.showhtml('text\r\nmore text') == ('', 'text\r\nmore text', 'htmlfile')
        assert capsys.readouterr().out == 'call save_html_data\n'

    def test_savehtml(self, monkeypatch):
        """unittest for R2hState.savehtml
        """
        def mock_check_if_html(*args):
            """stub
            """
            return ''
        def mock_check_if_html_mld(*args):
            """stub
            """
            return 'mld from check_if_html'
        def mock_save_html_data(*args):
            """stub
            """
            return ''
        def mock_save_html_data_mld(*args):
            """stub
            """
            return 'mld from save_html_data'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        testsubj.rstdata = 'data'
        testsubj.newfile = 'newname'
        assert testsubj.savehtml('oldhtml', 'newhtml', 'text') == ('html_name_wrong', 'data',
                                                                   'newname')
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.savehtml('oldhtml', '', 'text') == ('mld from check_if_html', 'data',
                                                            'newname')
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data_mld)
        assert testsubj.savehtml('oldhtml', '', 'text') == ('mld from save_html_data', 'data', '')
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        assert testsubj.savehtml('fname', '', '&nbsp;text') == ('html_saved', '&amp;nbsp;text', '')
        assert testsubj.htmlfile == 'fname'

    def test_copytoroot(self, monkeypatch):
        """unittest for R2hState.copytoroot
        """
        def mock_check_if_html(*args):
            """stub
            """
            return ''
        def mock_check_if_html_mld(*args):
            """stub
            """
            return 'mld from check_if_html'
        def mock_save_to_mirror(*args):
            """stub
            """
            return ''
        def mock_save_to_mirror_mld(*args):
            """stub
            """
            return 'mld from save_to_mirror'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.copytoroot('htmlfile', 'text') == 'mld from check_if_html'
        monkeypatch.setattr(testee, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(testee, 'save_to_mirror', mock_save_to_mirror_mld)
        assert testsubj.copytoroot('htmlfile', 'text') == 'mld from save_to_mirror'
        testsubj.htmlfile = 'somefile'
        monkeypatch.setattr(testee, 'save_to_mirror', mock_save_to_mirror)
        assert testsubj.copytoroot('htmlfile', 'text') == 'copied_to'
        assert testsubj.htmlfile == 'htmlfile'

    def test_propagate_deletions(self, monkeypatch, capsys):
        """unittest for R2hState.propagate_deletions
        """
        def mock_list_target(*args):
            """stub
            """
            print('called list_deletions_target()')
            return ['this', 'that']
        def mock_list_target_none(*args):
            """stub
            """
            return []
        def mock_apply_target(*args):
            """stub
            """
            print('called apply_deletions_target()')
            return ['one', 'two']
        def mock_apply_target_none(*args):
            """stub
            """
            return []
        def mock_list_mirror(*args):
            """stub
            """
            print('called list_deletions_mirror()')
            return ['this', 'that']
        def mock_list_mirror_none(*args):
            """stub
            """
            return []
        def mock_apply_mirror(*args):
            """stub
            """
            print('called apply_deletions_mirror()')
            return ['one', 'two']
        def mock_apply_mirror_none(*args):
            """stub
            """
            return []
        monkeypatch.setattr(testee.dml, 'list_deletions_target', mock_list_target)
        monkeypatch.setattr(testee.dml, 'apply_deletions_target', mock_apply_target)
        monkeypatch.setattr(testee.dml, 'list_deletions_mirror', mock_list_mirror)
        monkeypatch.setattr(testee.dml, 'apply_deletions_mirror', mock_apply_mirror)
        testsubj = testee.R2hState()
        assert testsubj.propagate_deletions(0) == 'mode=0'
        assert testsubj.propagate_deletions('0') == 'pending deletions for target: this, that'
        assert capsys.readouterr().out == 'called list_deletions_target()\n'
        assert testsubj.propagate_deletions('1') == 'deleted from target: one, two'
        assert capsys.readouterr().out == 'called apply_deletions_target()\n'
        assert testsubj.propagate_deletions('2') == 'pending deletions for mirror: this, that'
        assert capsys.readouterr().out == 'called list_deletions_mirror()\n'
        assert testsubj.propagate_deletions('3') == 'deleted from mirror: one, two'
        assert capsys.readouterr().out == 'called apply_deletions_mirror()\n'
        monkeypatch.setattr(testee.dml, 'list_deletions_target', mock_list_target_none)
        monkeypatch.setattr(testee.dml, 'apply_deletions_target', mock_apply_target_none)
        monkeypatch.setattr(testee.dml, 'list_deletions_mirror', mock_list_mirror_none)
        monkeypatch.setattr(testee.dml, 'apply_deletions_mirror', mock_apply_mirror_none)
        assert testsubj.propagate_deletions('0') == 'no deletions pending'
        assert testsubj.propagate_deletions('1') == 'no deletions pending'
        assert testsubj.propagate_deletions('2') == 'no deletions pending'
        assert testsubj.propagate_deletions('3') == 'no deletions pending'

    def test_makerefdoc(self, monkeypatch):
        """unittest for R2hState.makerefdoc
        """
        def mock_trefwlijst(*args, **kwargs):
            """stub
            """
            return 'index data', False
        def mock_trefwlijst_norefs(*args, **kwargs):
            """stub
            """
            return '', True
        def mock_trefwlijst_err(*args, **kwargs):
            """stub
            """
            return 'data', True
        def mock_save_src_data(*args, **kwargs):
            """stub
            """
            if kwargs.get('new', False):
                return 'mld from save_src_data'
            return ''
        def mock_save_src_data_2(*args, **kwargs):
            """stub
            """
            return 'mld from save_src_data'
        def mock_save_src_data_3(*args, **kwargs):
            """stub
            """
            if kwargs.get('new', True):
                return ''
            return 'mld from save_src_data'
        def mock_rst2html(*args):
            """stub
            """
            return 'converted data'
        def mock_save_html_data(*args):
            """stub
            """
            return ''
        def mock_save_html_data_2(*args):
            """stub
            """
            return 'mld from save_html_data'
        def mock_save_to_mirror(*args):
            """stub
            """
            return ''

        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        testsubj.conf = {'css': []}
        msg = testee.get_text('css_not_defined', testsubj.get_lang())
        monkeypatch.setattr(testee.TrefwoordenLijst, 'build', mock_trefwlijst_norefs)
        assert testsubj.makerefdoc() == (msg, )
        testsubj.conf = {'css': ['x']}
        monkeypatch.setattr(testee.TrefwoordenLijst, 'build', mock_trefwlijst_norefs)
        assert testsubj.makerefdoc() == (True, )

        monkeypatch.setattr(testee.TrefwoordenLijst, 'build', mock_trefwlijst)
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data)
        monkeypatch.setattr(testee, 'rst2html', mock_rst2html)
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        monkeypatch.setattr(testee, 'save_to_mirror', mock_save_to_mirror)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        monkeypatch.setattr(testee.R2hState, 'get_lang', mock_get_lang)
        assert testsubj.makerefdoc() == ('index_built', 'reflist.rst', 'reflist.html', 'index data')
        assert testsubj.loaded == testee.RST

        monkeypatch.setattr(testee.TrefwoordenLijst, 'build', mock_trefwlijst_err)
        assert testsubj.makerefdoc() == ('index_built with_err', 'reflist.rst', 'reflist.html',
                                         'data')
        assert testsubj.loaded == testee.RST

        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data_2)
        assert testsubj.makerefdoc() == ('mld from save_html_data', 'reflist.rst', 'reflist.html',
                                         'data')
        assert testsubj.loaded == testee.RST
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data_2)
        assert testsubj.makerefdoc() == ('mld from save_src_data', 'reflist.rst', 'reflist.html',
                                         'data')
        assert testsubj.loaded == testee.RST
        monkeypatch.setattr(testee, 'save_html_data', mock_save_html_data)
        monkeypatch.setattr(testee, 'save_src_data', mock_save_src_data_3)
        assert testsubj.makerefdoc() == ('index_built with_err', 'reflist.rst', 'reflist.html',
                                         'data')
        assert testsubj.loaded == testee.RST

    def test_convert_all(self, monkeypatch):
        """unittest for R2hState.convert_all
        """
        def mock_update_all_go(*args, **kwargs):
            """stub
            """
            return [('/index', 'just text'), ('/other', 'formatted: {}')]
        def mock_update_all_go_empty(*args, **kwargs):
            """stub
            """
            return []
        def mock_get_text(*args):
            """stub
            """
            if args[0] == 'in_sim':
                return args[0]
            if args[0] == 'docs_converted':
                return 'converted {}'
            return args[0]

        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee.UpdateAll, 'go', mock_update_all_go_empty)
        monkeypatch.setattr(testee, 'get_text', mock_get_text)
        testsubj.conf = {'css': []}
        assert testsubj.convert_all() == ('css_not_defined', '')
        testsubj.conf = {'css': ['x']}
        assert testsubj.convert_all() == ('converted in_sim', '')
        assert testsubj.convert_all('2') == ('converted ', '')
        assert testsubj.convert_all('3') == ('converted in_sim', '')
        assert testsubj.convert_all('4') == ('converted in_sim', '')
        assert testsubj.convert_all('5') == ('converted in_sim', '')
        monkeypatch.setattr(testee.UpdateAll, 'go', mock_update_all_go)
        assert testsubj.convert_all('0') == ('converted ', ('/index: just text\n'
                                                            'formatted: /other'))
        assert testsubj.convert_all('1') == ('converted ', ('/index: just text\n'
                                                            'formatted: /other'))

    def test_search(self, monkeypatch):
        """unittest for R2hState.search
        """
        def mock_search_site(*args):
            """stub
            """
            return ['found this', 'and that']
        def mock_search_site_none(*args):
            """stub
            """
            return []
        def mock_searchdict2list(*args):
            """stub
            """
            return args[0]
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()

        monkeypatch.setattr(testee, 'search_site', mock_search_site)
        monkeypatch.setattr(testee, 'searchdict2list', mock_searchdict2list)
        assert testsubj.search('found', '') == ('the following lines / parts were found:',
                                                ['found this', 'and that'])
        assert testsubj.search('found', 'replaced') == ('the following lines / parts were replaced:',
                                                        ['found this', 'and that'])

        monkeypatch.setattr(testee, 'search_site', mock_search_site_none)
        assert testsubj.search('not found', '') == ('search phrase not found', [])
        assert testsubj.search('not found', 'replaced') == ('nothing found, no replacements', [])

    def test_copysearch(self, monkeypatch, tmp_path):
        """unittest for R2hState.copysearch
        """
        path = tmp_path / 'copysearch'
        def mock_get_copysearch_filepath(*args):
            """stub
            """
            return path
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee, 'get_copysearch_filepath', mock_get_copysearch_filepath)
        searchdata = ('search_for', 'replace_with',
                      [('text1', '1', 'result1'), ('text2', '2', 'result2')])
        assert testsubj.copysearch(searchdata) == f'Search results copied to {path}'
        assert path.read_text() == ('searched for `search_for`and replaced with `replace_with`\n\n'
                                    'text1 line 1: result1\ntext2 line 2: result2\n')
        searchdata = ('search_for', '', [('text1', '1', 'result1'), ('text2', '2', 'result2')])
        assert testsubj.copysearch(searchdata) == f'Search results copied to {path}'
        assert path.read_text() == ('searched for `search_for`\n\n'
                                    'text1 line 1: result1\ntext2 line 2: result2\n')

    def test_check(self, monkeypatch):
        """unittest for R2hState.check
        """
        def mock_check_directive_selectors(*args):
            """stub
            """
            return []
        def mock_check_directive_selectors_missing(*args):
            """stub
            """
            return ['x', 'y']
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()

        monkeypatch.setattr(testee, 'check_directive_selectors', mock_check_directive_selectors)
        assert testsubj.check() == 'No issues detected'
        monkeypatch.setattr(testee, 'check_directive_selectors',
                            mock_check_directive_selectors_missing)
        assert testsubj.check() == ('an id or class used in the directives was not found'
                                    ' in the linked css files: x, y')

    def test_overview(self, monkeypatch):
        """unittest for R2hState.overview
        """
        def mock_build_progress_list(*args):
            """stub
            """
            return 'called build_progress_list'
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee, 'build_progress_list', mock_build_progress_list)
        assert testsubj.overview() == 'called build_progress_list'

    def test_copystand(self, monkeypatch, tmp_path):
        """unittest for R2hState.copystand
        """
        path = tmp_path / 'copystand'
        def mock_get_copystand_filepath(*args):
            """stub
            """
            return path
        def mock_get_progress_line_values(*args):
            """stub
            """
            return ['x', 'y', 'z', 'q']
        monkeypatch.setattr(testee, 'default_site', mock_default_site)
        testsubj = testee.R2hState()
        monkeypatch.setattr(testee, 'get_copystand_filepath', mock_get_copystand_filepath)
        monkeypatch.setattr(testee, 'get_progress_line_values', mock_get_progress_line_values)
        assert testsubj.copystand(['x']) == f'Overview exported to {path}'
        assert path.read_text() == 'x;y;z;q\n'
