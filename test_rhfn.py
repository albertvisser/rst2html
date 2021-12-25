"""test suite uitvoerbaar met bv. `pytest test.rhfn`

verifiëren dat hulpmethodes aangeroepen worden heb ik gedaan door deze te monkeypatchen met een
methode die een print statement doet en dat dan met capsys te controleren;
later bedacht ik dat ik dan meteen de argumenten kon laten tonen, dit kan desgewenst nog toegevoegd
worden in de eerder geschreven mock methoden
"""
import os
import pathlib
import shutil
import datetime
import pytest

import rst2html_functions as rhfn

FIXDATE = datetime.datetime(2020, 1, 1)

def mock_default_site():
    return 'testsite'


def mock_get_lang(*args):
    return ''


def mock_get_text(*args):
    return args[0]


class MockDatetime:
    @classmethod
    def today(cls):
        return FIXDATE


class TestLangRelated:
    def test_get_text(self):
        "voorlopig even met hard gecodeerde verwachte uitkomsten"
        lang_keyword = 't_settings'
        lang_string_nl = 'selecteer een settings bestand'
        lang_string_en = ('Select a settings file, indicating the site to work on and other'
                          ' parameters')

        assert rhfn.get_text(lang_keyword, 'en') == lang_string_en
        assert rhfn.get_text(lang_keyword, 'nl') == lang_string_nl
        from app_settings import LANG
        if LANG == 'en':
            assert rhfn.get_text(lang_keyword) == lang_string_en
        elif lang == 'nl':
            assert rhfn.get_text(lang_keyword) == lang_string_nl

    def test_translate_action(self, monkeypatch):
        def mock_get_text(*args):
            return args[0]
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert rhfn.translate_action('rename') == 'rename'
        assert rhfn.translate_action('c_rename') == 'rename'
        assert rhfn.translate_action('revert') == 'revert'
        assert rhfn.translate_action('c_revert') == 'revert'
        assert rhfn.translate_action('delete') == 'delete'
        assert rhfn.translate_action('c_delete') == 'delete'

    def test_format_message(self, monkeypatch):
        def mock_get_text(*args):
            raise KeyError
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert rhfn.format_message('test: {}', '', 'parm') == 'test: parm'
        assert rhfn.format_message('hallo', '', 'x') == 'hallo'
        monkeypatch.setattr(rhfn, 'get_text', lambda x, y: 'test: {}')
        assert rhfn.format_message('', '', 'arg') == 'test: arg'


class TestR2HRelated:
    "functies die met het omzetproces te maken hebben"
    def test_post_process_title(self):
        ""
        wo_title = ('<html><head></head>'
                    '<body><h1 class="page-titel">Welkom</h1>Hallo allemaal</body>')
        w_title_nok = ('<html><head></head>'
                       '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')
        w_title_ok = ('<html><head><title>stuff</title></head>'
                      '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')
        expected = ('<html><head><title>Welkom</title></head>'
                    '<body><h1 class="page-title">Welkom</h1>Hallo allemaal</body>')

        assert rhfn.post_process_title(wo_title) == wo_title
        with pytest.raises(ValueError):
            rhfn.post_process_title(w_title_nok)
        assert rhfn.post_process_title(w_title_ok) == expected

    def test_rst2html(self, monkeypatch, capsys):
        def mock_publish_string(*args, **kwargs):
            print('docutils.publish_string got called')
            return bytes()
        def mock_post_process_title(*args):
            print('post_process_title got called')
        invoer = "Hababarulala"
        with pytest.raises(TypeError):
            rhfn.rst2html(invoer)
        monkeypatch.setattr(rhfn, 'publish_string', mock_publish_string)
        monkeypatch.setattr(rhfn, 'post_process_title', mock_post_process_title)
        rhfn.rst2html(invoer, 'test.css')
        assert capsys.readouterr().out == ('docutils.publish_string got called\n'
                                           'post_process_title got called\n')

    def test_register_directives(self, monkeypatch, capsys):
        def mock_register_directive(*args):
            print('args for directives.register_directive: `{}` `{}`'.format(*args))
        def mock_load_custom_directives():
            print('load_custom_directives got called')
        monkeypatch.setattr(rhfn, 'standard_directives', {'name1': 'fun1', 'name2': 'fun2'})
        monkeypatch.setattr(rhfn.rd.directives, 'register_directive', mock_register_directive)
        monkeypatch.setattr(rhfn, 'load_custom_directives', mock_load_custom_directives)
        monkeypatch.setattr(rhfn, 'custom_directives', pathlib.Path('nonexistant.py'))
        rhfn.register_directives()
        assert capsys.readouterr().out == ('args for directives.register_directive: `name1`'
                                           ' `fun1`\n'
                                           'args for directives.register_directive: `name2`'
                                           ' `fun2`\n')
        monkeypatch.setattr(rhfn, 'standard_directives', {})
        monkeypatch.setattr(rhfn, 'custom_directives', pathlib.Path('test_rhfn.py'))
        rhfn.register_directives()
        assert capsys.readouterr().out == 'load_custom_directives got called\n'

    def test_load_custom_directives(self, monkeypatch, capsys):
        def mock_get_modulename(*args):
            return 'mymodule'
        def mock_import_module(*args):
            print('import_module got called for `{}`'.format(args[0]))
        def mock_getmembers(*args):
            class Dummy:
                ''
                pass
            class MockDir:
                """Mockup of a directive

                usage: ..this::
                description: some text
                """
            return (('name1', Dummy), ('name2', rhfn.rd.Directive), ('w_docs', MockDir()))
        def mock_register_directive(*args):
            print('args for directives.register_directive: `{}` `{}`'.format(*args))
        def mock_getmro_ok(*args):
            return (rhfn.rd.Directive, '')
        def mock_getmro_nok(*args):
            return ()
        monkeypatch.setattr(rhfn.inspect, 'getmodulename', mock_get_modulename)
        monkeypatch.setattr(rhfn.importlib, 'import_module', mock_import_module)
        monkeypatch.setattr(rhfn.inspect, 'getmembers', mock_getmembers)
        monkeypatch.setattr(rhfn.inspect, 'getmro', mock_getmro_ok)
        monkeypatch.setattr(rhfn.rd.directives, 'register_directive', mock_register_directive)
        rhfn.load_custom_directives()
        assert capsys.readouterr().out == ('import_module got called for `mymodule`\n'
                                           'args for directives.register_directive: `name1` ``\n'
                                           'args for directives.register_directive: `this`'
                                           ' `some text`\n')
        monkeypatch.setattr(rhfn.inspect, 'getmro', mock_getmro_nok)
        rhfn.load_custom_directives()
        assert capsys.readouterr().out == 'import_module got called for `mymodule`\n'

    def test_get_custom_directives_filename(self):
        ""
        assert rhfn.get_custom_directives_filename() == (rhfn.custom_directives_template, 'init')
        rhfn.custom_directives.touch()
        assert rhfn.get_custom_directives_filename() == (rhfn.custom_directives, 'loaded')
        rhfn.custom_directives.unlink()

    def test_get_directives_used(self):
        assert rhfn.get_directives_used({}) == set()
        data = {('', 'index'): [(1, '.. directive::', [1]), (2, '.. direct::', [1])],
                ('dir', 'text'): [(1, '.. directive', [1])]}
        assert rhfn.get_directives_used(data) == {'directive', 'direct'}

    def test_get_idcls(self):
        rhfn.rhdir.directive_selectors = {'directive': [('selector', 'class'),
                                                        ('selector', 'id_1')],
                                          'direct': [('selector', 'class'), ('selector', 'id_2')]}
        assert rhfn.get_idcls([]) == set()
        assert rhfn.get_idcls({'directive', 'direct'}) == {'class', 'id_1', 'id_2'}

    def test_check_directive_selectors(self, monkeypatch, capsys):
        def mock_search_site(*args):
            return {('', 'index'): [(1, 'directive', [1]), (2, 'direct', [1])]}
        def mock_get_directives_used(*args):
            print('called get_directives_used')
            return {'directive', 'direct'}
        def mock_get_directives_used_none(*args):
            print('called get_directives_used')
            return {}
        def mock_get_idcls(*args):
            print('called get_idcls')
            return {'class_1', 'id_1', 'id_2', 'class_2'}
        def mock_get_idcls_none(*args):
            print('called get_idcls')
            return {}
        def mock_read_conf(*args):
            return '', {'css': ['test1.css', 'test2.css']}
        def mock_run_found_all(*args):
            print('call subprocess with args', ' '.join(['`{}`'.format(x) for x in args[0]]))
            with open('/tmp/r2h_css.css', 'w') as out:
                out.write('selector.class_1 #id_1 .class_2 selector#id_2\n')
        def mock_run_not_all(*args):
            print('call subprocess with args', ' '.join(['`{}`'.format(x) for x in args[0]]))
            with open('/tmp/r2h_css.css', 'w') as out:
                out.write('selector.class_1 #id_1 \n')
        monkeypatch.setattr(rhfn, 'search_site', mock_search_site)
        monkeypatch.setattr(rhfn, 'get_directives_used', mock_get_directives_used)
        monkeypatch.setattr(rhfn, 'get_idcls', mock_get_idcls)
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)
        monkeypatch.setattr(rhfn.subprocess, 'run', mock_run_found_all)
        assert rhfn.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\ncalled get_idcls\n'
                                           'call subprocess with args `wget` `test1.css`'
                                           ' `test2.css` `-O` `/tmp/r2h_css.css`\n')
        monkeypatch.setattr(rhfn, 'get_directives_used', mock_get_directives_used_none)
        assert rhfn.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\n')
        monkeypatch.setattr(rhfn, 'get_directives_used', mock_get_directives_used)
        monkeypatch.setattr(rhfn, 'get_idcls', mock_get_idcls_none)
        assert rhfn.check_directive_selectors('testsite') == ''
        assert capsys.readouterr().out == ('called get_directives_used\ncalled get_idcls\n')
        monkeypatch.setattr(rhfn, 'get_idcls', mock_get_idcls)
        monkeypatch.setattr(rhfn.subprocess, 'run', mock_run_not_all)
        assert sorted(rhfn.check_directive_selectors('testsite')) == ['class_2', 'id_2']
        capsys.readouterr()  # swallow stdout/err


    def test_preprocess_includes(self, monkeypatch, capsys):
        def mock_read_conf(*args):
            return '', {'lang': rhfn.LANG}
        def mock_read_src_data(*args):
            return '', 'include {} {} {}'.format(args[0], args[1], args[2])
        def mock_read_src_data_msg(*args):
            return 'fname_invalid', ''
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)
        # lege invoer
        assert rhfn.preprocess_includes('testsite', '', '') == ''
        # fout bij ophalen include
        data = 'eerste regel\n\n.. incl:: jansen\n\ntweede regel\n'
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data_msg)
        expected = ('eerste regel\n\n.. error:: Not a valid filename: jansen\n\ntweede regel\n')
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: docname' in root
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data)
        expected = 'eerste regel\n\ninclude testsite  jansen\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: docname' in subdir
        expected = 'eerste regel\n\ninclude testsite subdir jansen\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', 'subdir', data) == expected
        # '.. incl:: subdir/docname' in root
        data = 'eerste regel\n\n.. incl:: subdir/jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite subdir jansen\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # fout: '.. incl:: subdir/docname' in subdir
        data = 'eerste regel\n\n.. incl:: subdir/jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: subdir/jansen\n\n'
                    'tweede regel\n')
        assert rhfn.preprocess_includes('testsite', 'ix', data) == expected
        # '.. incl:: ../docname' in subdir
        data = 'eerste regel\n\n.. incl:: ../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite  jansen\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', 'subdir', data) == expected
        # fout: '.. incl:: ../docname' in root
        data = 'eerste regel\n\n.. incl:: ../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\n.. error:: Not a valid filename: ../jansen\n\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # '.. incl:: ../subdir/docname' in andere subdir
        data = 'eerste regel\n\n.. incl:: topdir/../jansen\n\ntweede regel\n'
        expected = 'eerste regel\n\ninclude testsite topdir jansen\ntweede regel\n'
        assert rhfn.preprocess_includes('testsite', 'subdir', data) == expected
        # fout: '.. incl:: ../subdir/docname' in root
        data = 'eerste regel\n\n.. incl:: topdir/../jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: topdir/../jansen\n\n'
                    'tweede regel\n')
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # fout: geen includenaam
        data = 'eerste regel\n\n.. incl::\n\ntweede regel\n'
        expected = ("eerste regel\n\n.. error:: Not a valid filename: it's missing...\n\n"
                    'tweede regel\n')
        assert rhfn.preprocess_includes('testsite', '', data) == expected
        # fout: teveel pad-onderdelen
        data = 'eerste regel\n\n.. incl:: top/dir/../jansen\n\ntweede regel\n'
        expected = ('eerste regel\n\n.. error:: Not a valid filename: top/dir/../jansen\n\n'
                    'tweede regel\n')
        assert rhfn.preprocess_includes('testsite', '', data) == expected


class TestConfRelated:
    "tests for site / configuration related functions"
    def test_default_site(self, monkeypatch):
        def no_sitelist():
            return []
        def sitelist_without_dflt():
            return ['site_1', 'site_2']
        def sitelist_with_dflt():
            return ['site_0', 'blabla']
        monkeypatch.setattr(rhfn.dml, 'list_sites', no_sitelist)
        assert rhfn.default_site() == ''
        monkeypatch.setattr(rhfn.dml, 'list_sites', sitelist_without_dflt)
        assert rhfn.default_site() == 'site_1'
        monkeypatch.setattr(rhfn, 'DFLT', 'blabla')
        monkeypatch.setattr(rhfn.dml, 'list_sites', sitelist_with_dflt)
        assert rhfn.default_site() == 'blabla'

    def test_new_conf(self, monkeypatch):
        def text2conf_notok(*args):
            return 'Not OK', {}
        def text2conf_emptyurl(*args):
            return '', {'url': ''}
        def text2conf_ok(*args):
            return '', {'url': 'http://www.example.org'}
        def get_text_msg(*args):
            return 'Not Created'
        def create_conf(*args):
            return 'new_site'
        def create_site_exc(*args):
            raise FileExistsError('Exists')
        def create_site_ok(*args):
            pass
        monkeypatch.setattr(rhfn, 'text2conf', text2conf_notok)
        monkeypatch.setattr(rhfn, 'get_text', get_text_msg)
        assert rhfn.new_conf('', '') == ('Not Created Not OK', '')
        monkeypatch.setattr(rhfn, 'text2conf', text2conf_emptyurl)
        monkeypatch.setattr(rhfn, 'create_server_config', create_conf)
        monkeypatch.setattr(rhfn.dml, 'create_new_site', create_site_exc)
        assert rhfn.new_conf('', '') == ('Exists', '')  # 'http://new_site')
        monkeypatch.setattr(rhfn.dml, 'create_new_site', create_site_ok)
        assert rhfn.new_conf('', '') == ('', 'http://new_site')
        monkeypatch.setattr(rhfn, 'text2conf', text2conf_ok)
        assert rhfn.new_conf('', '') == ('', '')

    def test_create_server_config(self, monkeypatch):
        def mock_get_tldname(*args):
            return 'example.com'
        def mock_add_to_hostsfile(*args):
            print('mock_add_to_hostsfile was called')
        def mock_add_to_server(*args):
            print('mock_add_to_server was called')
        monkeypatch.setattr(rhfn, 'get_tldname', mock_get_tldname)
        monkeypatch.setattr(rhfn, 'add_to_hostsfile', mock_add_to_hostsfile)
        monkeypatch.setattr(rhfn, 'add_to_server', mock_add_to_server)
        assert rhfn.create_server_config('mysite') == 'mysite.example.com'

    # eigenlijk betekent het gegeven dat de volgende drie methoden niet te testen zijn dat deze
    # thuishoren in een data-benaderingsmodule, dan wel dat het ophalen van gegevens uit een extern
    # bestand in zo'n module thuishoort waardoor het wel monkeypatchbaar wordt
    def test_get_tldname(self):
        # voor bepalen tldname kijken we in eerst /etc/hosts: eerste entry met een punt erin
        # pas als die niet bestaat kijken we of er iets in /etc/hostname staat (computernaam)
        # maar dat is niet te testen zonder /etc/hosts aan te passen
        assert rhfn.get_tldname() == 'lemoncurry.nl'

    def add_to_hostsfile(self):  # not really testable (yet)
        pass

    def add_to_server(self):  # not really testable (yet)
        pass

    def test_init_css(self, monkeypatch, capsys):
        def mock_read_settings_empty(*args):
            return {'css': [] }
        def mock_read_settings_basic_plus(*args):
            return {'css': ['html4css1.css', 'reset.css', '960.css', 'myowncss.css',
                            'http://www.example.com/static/css.css'] }
        def mock_copyfile(*args):
            print('copying `{}` to `{}`'.format(*args))
        def mock_update_settings(*args):
            print('update_settings called with args `{}` `{}`'.format(*args))
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings_empty)
        monkeypatch.setattr(rhfn.shutil, 'copyfile', mock_copyfile)
        monkeypatch.setattr(rhfn.dml, 'update_settings', mock_update_settings)
        # als deze nog niet bestaat wordt er een directory css aangemaakt onder `sitename`
        # alle files in BASIC_CSS die nog niet in conf['css'] zitten worden daarin opgevoerd
        # en ook aan conf['css'] toegevoegd dat daarna aangepast wordt
        sitename = 'testsite'
        here = rhfn.HERE / 'static'
        there = rhfn.WEBROOT / sitename / 'css'
        there_present = there.parent.exists()
        copy_lines = ['copying `{0}/{2}` to `{1}/{2}`\n'.format(here, there, x) for x in
                      rhfn.BASIC_CSS]
        update_lines = ["'url + css/{}'".format(x) for x in rhfn.BASIC_CSS]
        if not there_present:  # make sure cssdir.mkdir doesn't fail
            there.parent.mkdir(parents=True, exist_ok=True)
        rhfn.init_css(sitename)
        assert capsys.readouterr().out == (''.join(copy_lines) + "update_settings called with"
                                           " args `testsite` `{{'css': [{}, {}, {}]}}`"
                                           "\n".format(*update_lines))
        if not there_present: # teardown if necessary
            there.parent.rmdir()
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings_basic_plus)
        rhfn.init_css(sitename)
        assert capsys.readouterr().out == ''

    def test_list_confs(self, monkeypatch):
        def mock_list_sites_none():
            return []
        def mock_list_sites_one():
            return ['one']
        def mock_list_sites_more():
            return ['first', 'next', 'last']
        monkeypatch.setattr(rhfn.dml, 'list_sites', mock_list_sites_none)
        assert rhfn.list_confs() == ''
        monkeypatch.setattr(rhfn.dml, 'list_sites', mock_list_sites_one)
        assert rhfn.list_confs() == '<option>one</option>'
        assert rhfn.list_confs('two') == '<option>one</option>'
        monkeypatch.setattr(rhfn.dml, 'list_sites', mock_list_sites_more)
        assert rhfn.list_confs() == ('<option>first</option><option>next</option>'
                                     '<option>last</option>')
        assert rhfn.list_confs('last') == ('<option>first</option><option>next</option>'
                                           '<option selected="selected">last</option>')

    def test_read_conf(self, monkeypatch):
        mocked_settings = {'x': 'y'}
        def mock_read_settings_notfound(*args):
            raise FileNotFoundError
        def mock_read_settings_found(*args):
            return mocked_settings
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings_notfound)
        assert rhfn.read_conf('testsite') == ('no_such_sett', None)
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings_found)
        assert rhfn.read_conf('testsite') == ('', mocked_settings)

    def test_conf2text(self, monkeypatch):
        def mock_save_config_data(confdict, **kwargs):
            return confdict
        monkeypatch.setattr(rhfn, 'save_config_data', mock_save_config_data)
        conf_in = {'test': 'tested', 'url': 'gargl', 'css': ['gargl/snork.css', 'test.css']}
        conf_out = {'test': 'tested', 'url': 'gargl', 'css': ['url + snork.css', 'test.css']}
        assert rhfn.conf2text(conf_in) == conf_out

    def check_url(self, monkeypatch):
        def mock_urlopen_fout(*args):
            raise rhfn.urllib.error.HTTPError

    def test_text2conf(self, monkeypatch):
        def mock_get_text(*args):
            return args[0] + ': {}'
        def mock_load_config_data_error(*args):
            raise rhfn.ParserError
        def mock_load_config_data_empty(*args):
            return {}
        def mock_load_config_data_basic(*args):
            return rhfn.DFLT_CONF
        def mock_load_config_data_hig_fout(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['hig'] = 'hallo'
            return conf
        def mock_load_config_data_lang_fout(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['lang'] = 'du'
            return conf
        def mock_load_config_url_not_http(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['url'] = 'x'
            print(conf)
            return conf
        def mock_load_config_url_other(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['url'] = 'http://x/'
            return conf
        def mock_check_url(*args):
            # raise rhfn.urllib.error.HTTPError
            raise rhfn.urllib.error.URLError('x')
        def mock_load_config_css_simple(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['css'] = 'a_string'
            return conf
        def mock_load_config_css_double(*args):
            conf = {x: y for x, y in rhfn.DFLT_CONF.items()}
            conf['url'] = 'http://x'
            conf['css'] = ['url + a_string', 'http://stuff']
            return conf
        def mock_check_url_ok(*args):
            pass

        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_data_error)
        assert rhfn.text2conf('') == ('sett_no_good: {}', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_data_empty)
        assert rhfn.text2conf('') == ('sett_invalid: wid', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_data_basic)
        assert rhfn.text2conf('') == ('', rhfn.DFLT_CONF)
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_data_hig_fout)
        assert rhfn.text2conf('') == ('sett_invalid: hig', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_data_lang_fout)
        assert rhfn.text2conf('') == ('sett_invalid: lang', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_url_not_http)
        assert rhfn.text2conf('') == ('sett_invalid: url', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_url_other)
        monkeypatch.setattr(rhfn, 'check_url', mock_check_url)
        assert rhfn.text2conf('') == ('sett_invalid: url', {})
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_css_simple)
        expected = {x: y for x, y in rhfn.DFLT_CONF.items()}
        expected.update({'css': ['https://a_string']})
        assert rhfn.text2conf('') == ('', expected)
        monkeypatch.setattr(rhfn, 'load_config_data', mock_load_config_css_double)
        monkeypatch.setattr(rhfn, 'check_url', mock_check_url_ok)
        expected = {x: y for x, y in rhfn.DFLT_CONF.items()}
        expected.update({'url': 'http://x','css': ['http://x/a_string', 'http://stuff']})
        assert rhfn.text2conf('') == ('', expected)

    def test_check_url(self, monkeypatch):
        def mock_urlopen_ok(*args):
            pass
        def mock_urlopen(*args):
            raise rhfn.urllib.error.URLError('x')
        monkeypatch.setattr(rhfn.urllib.request, 'urlopen', mock_urlopen_ok)
        assert rhfn.check_url('') == None
        monkeypatch.setattr(rhfn.urllib.request, 'urlopen', mock_urlopen)
        with pytest.raises(rhfn.urllib.error.URLError):
            rhfn.check_url('http://test/testerdetest')


    def test_save_conf(self, monkeypatch, capsys):
        def mock_read_settings_error(*args):
            raise FileNotFoundError
        def mock_read_settings(*args):
            return {}
        def mock_get_text(*args):
            return 'no_such_sett for `{}`'
        def mock_text2conf_error(*args):
            return True, {}
        def mock_text2conf(*args):
            return False, {'url': False}
        def mock_update_settings(*args):
            print('called update_settings for `{}` `{}`'.format(*args))
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings_error)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert rhfn.save_conf('testsite', '') == 'no_such_sett for `testsite`'
        monkeypatch.setattr(rhfn.dml, 'read_settings', mock_read_settings)
        monkeypatch.setattr(rhfn, 'text2conf', mock_text2conf_error)
        assert rhfn.save_conf('testsite', '')
        monkeypatch.setattr(rhfn, 'text2conf', mock_text2conf)
        monkeypatch.setattr(rhfn.dml, 'update_settings', mock_update_settings)
        assert not rhfn.save_conf('testsite', '')
        assert capsys.readouterr().out == "called update_settings for `testsite` `{'url': False}`\n"


class TestSiteRelated:
    def test_list_subdirs(self, monkeypatch, capsys):
        def mock_list_dirs(*args):
            print('ext arg is', args[1])
            return ['my_hovercraft', 'cheese_shop']
        def mock_list_dirs_empty(*args):
            print('ext arg is', args[1])
            return []
        def mock_list_dirs_error(*args):
            print('ext arg is', args[1])
            raise FileNotFoundError
        sitename = 'testsite'
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs)
        assert rhfn.list_subdirs(sitename) == ['cheese_shop/', 'my_hovercraft/']
        assert capsys.readouterr().out == 'ext arg is src\n'
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs_empty)
        assert rhfn.list_subdirs(sitename, 'dest') == []
        assert capsys.readouterr().out == 'ext arg is dest\n'
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs)
        assert rhfn.list_subdirs(sitename, 'xxxx') == ['cheese_shop/', 'my_hovercraft/']
        assert capsys.readouterr().out == 'ext arg is dest\n'
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs_error)
        assert rhfn.list_subdirs(sitename, 'src') == []
        assert capsys.readouterr().out == 'ext arg is src\n'

    def test_list_files(self, monkeypatch):
        def mock_list_docs(*args, **kwargs):
            return ['luxury-yacht', 'throatwobbler-mangrove']
        def mock_list_docs_empty(*args, **kwargs):
            return []
        def mock_list_docs_not_found(*args, **kwargs):
            raise FileNotFoundError
        def mock_list_docs_wrong_type(*args, **kwargs):
            return
        def mock_list_subdirs(*args):
            return ['my_hovercraft/', 'cheese_shop/']
        def mock_list_subdirs_empty(*args):
            return []
        def mock_list_templates(*args):
            return ['letter.tpl', 'number.tpl']
        def mock_list_templates_empty(*args):
            return []
        sitename = 'testsite'
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs_not_found)
        assert rhfn.list_files(sitename) == 'Site not found'
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs_wrong_type)
        assert rhfn.list_files(sitename, ext='xxx') == 'Wrong type: `xxx`'
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs)
        assert rhfn.list_files(sitename, deleted=True) == ['luxury-yacht', 'throatwobbler-mangrove']
        monkeypatch.setattr(rhfn.dml, 'list_templates', mock_list_templates_empty)
        assert rhfn.list_files(sitename) == ('<option>luxury-yacht.rst</option>'
                                             '<option>throatwobbler-mangrove.rst</option>')
        monkeypatch.setattr(rhfn, 'list_subdirs', mock_list_subdirs_empty)
        assert rhfn.list_files(sitename, current='enormous') == (
                '<option>..</option>'
                '<option>luxury-yacht.rst</option>'
                '<option>throatwobbler-mangrove.rst</option>')
        monkeypatch.setattr(rhfn.dml, 'list_templates', mock_list_templates)
        assert rhfn.list_files(sitename, naam='luxury-yacht.rst') == (
                '<option>-- letter.tpl --</option>'
                '<option>-- number.tpl --</option>'
                '<option selected="selected">luxury-yacht.rst</option>'
                '<option>throatwobbler-mangrove.rst</option>')
        monkeypatch.setattr(rhfn, 'list_subdirs', mock_list_subdirs)
        assert rhfn.list_files(sitename, ext='dest') == (
                '<option>my_hovercraft/</option>'
                '<option>cheese_shop/</option>'
                '<option>luxury-yacht.html</option>'
                '<option>throatwobbler-mangrove.html</option>')

    def test_make_new_dir(self, monkeypatch, capsys):
        def mock_create_new_dir(*args):
            print('create_new_dir called')
        def mock_create_new_dir_failed(*args):
            raise FileExistsError
        sitename, filename = 'testsite', 'testname'
        monkeypatch.setattr(rhfn.dml, 'create_new_dir', mock_create_new_dir)
        assert rhfn.make_new_dir(sitename, filename) == ''
        assert capsys.readouterr().out == 'create_new_dir called\n'
        monkeypatch.setattr(rhfn.dml, 'create_new_dir', mock_create_new_dir_failed)
        assert rhfn.make_new_dir(sitename, filename) == 'dir_name_taken'


class TestSourceRelated:
    sitename, filename = 'testsite', 'testname'

    def test_read_src_data(self, monkeypatch, capsys):
        def mock_get_doc_contents(*args, **kwargs):
            print('got args `{}`, `{}`, `{}`, `{}`'.format(*args))
        def mock_get_doc_contents_error_1(*args, **kwargs):
            raise AttributeError
        def mock_get_doc_contents_error_2(*args, **kwargs):
            raise FileNotFoundError
        assert rhfn.read_src_data(self.sitename, '', self.filename + '.x') == (
            'rst_filename_error', '')
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents)
        rhfn.read_src_data(self.sitename, '', self.filename + '.rst')
        assert capsys.readouterr().out == 'got args `testsite`, `testname`, `src`, ``\n'
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents_error_1)
        assert rhfn.read_src_data(self.sitename, '', self.filename) == ('src_name_missing', '')
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents_error_2)
        assert rhfn.read_src_data(self.sitename, '', self.filename) == ('src_file_missing', '')

    def test_check_if_rst(self, monkeypatch):
        assert rhfn.check_if_rst('', '') == 'supply_text'
        assert rhfn.check_if_rst('...', '') == 'rst_invalid'
        assert rhfn.check_if_rst('...', rhfn.RST) == ''
        assert rhfn.check_if_rst('...', rhfn.RST, 'x') == ''
        assert rhfn.check_if_rst('...', rhfn.RST, '') == 'src_name_missing'
        assert rhfn.check_if_rst('...', rhfn.RST, 'x/') == 'src_name_missing'
        assert rhfn.check_if_rst('...', rhfn.RST, '-- new --') == 'src_name_missing'
        assert rhfn.check_if_rst('...', rhfn.RST, '..') == 'src_name_missing'

    def test_save_src_data(self, monkeypatch, capsys):
        def mock_list_subdirs(*args):
            return ['hello/']
        def mock_create_new_dir(*args):
            print('args for creating dir: `{}` `{}`'.format(*args))
        def mock_create_new_dir_exists(*args):
            raise FileExistsError
        def mock_create_new_doc(*args, **kwargs):
            print('args for creating doc: `{}` `{}`'.format(args[0], args[1], kwargs['directory']))
        def mock_create_new_doc_exists(*args, **kwargs):
            raise FileExistsError
        def mock_update_rst(*args, **kwargs):
            print('args for update_rst: `{}` `{}` `{}` `{}`'.format(args[0], args[1], args[2],
                                                                    kwargs['directory']))
        def mock_update_rst_error_1(*args, **kwargs):
            raise AttributeError('name')
        def mock_update_rst_error_2(*args, **kwargs):
            raise AttributeError('contents')
        def mock_update_rst_error_3(*args, **kwargs):
            raise AttributeError('something else')
        def mock_update_rst_error_4(*args, **kwargs):
            raise FileNotFoundError

        assert rhfn.save_src_data(self.sitename, '', self.filename + '.x', '...') == (
                'rst_filename_error')
        monkeypatch.setattr(rhfn.dml, 'create_new_dir', mock_create_new_dir)
        monkeypatch.setattr(rhfn.dml, 'create_new_doc', mock_create_new_doc_exists)
        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst)
        assert rhfn.save_src_data(self.sitename, 'test', self.filename + '.rst', '...', True) == (
            'src_name_taken')
        assert capsys.readouterr().out == 'args for creating dir: `testsite` `test`\n'

        monkeypatch.setattr(rhfn.dml, 'create_new_doc', mock_create_new_doc)
        assert rhfn.save_src_data(self.sitename, 'test', self.filename + '.rst', '...') == ''
        assert capsys.readouterr().out == ('args for creating dir: `testsite` `test`\n'
                                           'args for update_rst: `testsite` `testname` `...` '
                                           '`test`\n')

        monkeypatch.setattr(rhfn.dml, 'create_new_dir', mock_create_new_dir_exists)
        assert rhfn.save_src_data(self.sitename, 'test', self.filename + '.rst', '...', True) == ''
        assert capsys.readouterr().out == ('args for creating doc: `testsite` `testname.rst`\n'
                                           'args for update_rst: `testsite` `testname` `...` '
                                           '`test`\n')

        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst_error_1)
        assert rhfn.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'src_name_missing')
        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst_error_2)
        assert rhfn.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'supply_text')
        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst_error_3)
        assert rhfn.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'something else')
        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst_error_4)
        assert rhfn.save_src_data(self.sitename, 'hello', self.filename + '.rst', '...') == (
            'src_file_missing')

    def test_revert_src(self, monkeypatch, capsys):
        def mock_revert_rst(*args, **kwargs):
            print('args for revert_rst: `{}` `{}`'.format(args, kwargs))
        def mock_revert_rst_error(*args, **kwargs):
            raise AttributeError
        def mock_revert_rst_error_2(*args, **kwargs):
            raise FileNotFoundError('backup')
        def mock_revert_rst_error_3(*args, **kwargs):
            raise FileNotFoundError('other')
        assert rhfn.revert_src(self.sitename, '', self.filename + '.x') == (
                'rst_filename_error')
        monkeypatch.setattr(rhfn.dml, 'revert_rst', mock_revert_rst)
        assert rhfn.revert_src(self.sitename, 'test', self.filename + '.rst') == ''
        assert capsys.readouterr().out == ('args for revert_rst: '
                                           "`('testsite', 'testname', 'test')` `{}`\n")
        monkeypatch.setattr(rhfn.dml, 'revert_rst', mock_revert_rst_error)
        assert rhfn.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'src_name_missing')
        monkeypatch.setattr(rhfn.dml, 'revert_rst', mock_revert_rst_error_2)
        assert rhfn.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'backup_missing')
        monkeypatch.setattr(rhfn.dml, 'revert_rst', mock_revert_rst_error_3)
        assert rhfn.revert_src(self.sitename, 'hello', self.filename + '.rst') == (
            'src_file_missing')

    def test_mark_deleted(self, monkeypatch, capsys):
        def mock_mark_src_deleted(*args, **kwargs):
            print('args for mark_src_deleted: `{}` `{}` `{}`'.format(args[0], args[1],
                                                              kwargs['directory']))
        def mock_mark_src_deleted_noname(*args, **kwargs):
            raise AttributeError()
        def mock_mark_src_deleted_nofile(*args, **kwargs):
            raise FileNotFoundError

        assert rhfn.mark_deleted(self.sitename, '', self.filename + '.x') == (
                'rst_filename_error')
        monkeypatch.setattr(rhfn.dml, 'mark_src_deleted', mock_mark_src_deleted)
        assert rhfn.mark_deleted(self.sitename, '', self.filename + '.rst') == ''
        assert capsys.readouterr().out == 'args for mark_src_deleted: `testsite` `testname` ``\n'
        monkeypatch.setattr(rhfn.dml, 'mark_src_deleted', mock_mark_src_deleted_noname)
        assert rhfn.mark_deleted(self.sitename, '', self.filename) == (
                'src_name_missing')
        monkeypatch.setattr(rhfn.dml, 'mark_src_deleted', mock_mark_src_deleted_nofile)
        assert rhfn.mark_deleted(self.sitename, '', self.filename + '.rst') == (
                'src_file_missing')

    def test_read_tpl_data(self, monkeypatch, capsys):
        def mock_read_template(*args):
            print('read_template called')
        monkeypatch.setattr(rhfn.dml, 'read_template', mock_read_template)
        rhfn.read_tpl_data(self.sitename, self.filename)
        assert capsys.readouterr().out == 'read_template called\n'

    def test_save_tpl_data(self, monkeypatch, capsys):
        def mock_write_template(*args):
            print('write_template called')
        monkeypatch.setattr(rhfn.dml, 'write_template', mock_write_template)
        rhfn.save_tpl_data(self.sitename, self.filename, '')
        assert capsys.readouterr().out == 'write_template called\n'


class TestTargetRelated:
    sitename, filename = 'testsite', 'testname'

    def test_read_html_data(self, monkeypatch, capsys):
        def mock_get_doc_contents(*args):
            print('got args `{}`, `{}`, `{}`, `{}`'.format(*args))
        def mock_get_doc_contents_error_1(*args, **kwargs):
            raise AttributeError
        def mock_get_doc_contents_error_2(*args, **kwargs):
            raise FileNotFoundError
        assert rhfn.read_html_data(self.sitename, '', self.filename + '.x') == (
            'html_filename_error', '')
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents)
        rhfn.read_html_data(self.sitename, '', self.filename + '.html')
        assert capsys.readouterr().out == 'got args `testsite`, `testname`, `dest`, ``\n'
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents_error_1)
        assert rhfn.read_html_data(self.sitename, '', self.filename) == ('html_name_missing', '')
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents_error_2)
        assert rhfn.read_html_data(self.sitename, '', self.filename) == ('html_file_missing', '')

    def test_check_if_html(self, monkeypatch):
        assert rhfn.check_if_html('', '') == 'supply_text'
        assert rhfn.check_if_html('...', '') == 'load_html'
        assert rhfn.check_if_html('...', rhfn.HTML) == ''
        assert rhfn.check_if_html('...', rhfn.HTML, 'x') == ''
        assert rhfn.check_if_html('...', rhfn.HTML, '') == 'html_name_missing'
        assert rhfn.check_if_html('...', rhfn.HTML, 'x/') == 'html_name_missing'
        assert rhfn.check_if_html('...', rhfn.HTML, '-- new --') == 'html_name_missing'
        assert rhfn.check_if_html('...', rhfn.HTML, '..') == 'html_name_missing'

    def test_save_html_data(self, monkeypatch, capsys):
        def mock_apply_deletions_target(*args):
            print('args for apply_deletions: `{}` `{}`'.format(*args))
        def mock_update_html(*args, **kwargs):
            print('args for update_html: `{}` `{}` `{}` `{}` `{}`'.format(args[0], args[1], args[2],
                                                                          kwargs['directory'],
                                                                          kwargs['dry_run']))
        def mock_update_html_error_1(*args, **kwargs):
            raise AttributeError('name')
        def mock_update_html_error_2(*args, **kwargs):
            raise AttributeError('contents')
        def mock_update_html_error_3(*args, **kwargs):
            raise FileNotFoundError('not-found')

        monkeypatch.setattr(rhfn.dml, 'apply_deletions_target', mock_apply_deletions_target)
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.x', '...') == (
                'html_filename_error')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')
        monkeypatch.setattr(rhfn.dml, 'update_html', mock_update_html)
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.html', '...') == ''
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n'
                                           'args for update_html: `testsite` `testname` `...` '
                                           '`` `False`\n')
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.html', '...', True) == ''
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n'
                                           'args for update_html: `testsite` `testname` `...` '
                                           '`` `True`\n')
        monkeypatch.setattr(rhfn.dml, 'update_html', mock_update_html_error_1)
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'html_name_missing')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')
        monkeypatch.setattr(rhfn.dml, 'update_html', mock_update_html_error_2)
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'supply_text')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')
        monkeypatch.setattr(rhfn.dml, 'update_html', mock_update_html_error_3)
        assert rhfn.save_html_data(self.sitename, '', self.filename + '.html', '...') == (
            'not-found')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')

    def test_complete_header(self):
        assert rhfn.complete_header({'url': ''}, '...') == '...'
        rstdata = 'my<head>hurts'
        conf = {'url': '', 'starthead': 'aches and '}
        assert rhfn.complete_header(conf, rstdata) == 'my<head>aches and hurts'
        conf = {'url': '', 'starthead': ['aches', ' and ']}
        assert rhfn.complete_header(conf, rstdata) == 'my<head>aches and hurts'
        rstdata = 'my head hurts'
        assert rhfn.complete_header(conf, rstdata) == 'aches and my head hurts'
        rstdata = 'my</head>hurts'
        conf = {'url': '', 'endhead': ' aching big'}
        assert rhfn.complete_header(conf, rstdata) == 'my aching big</head>hurts'
        conf = {'url': '', 'endhead': [' aching', ' big']}
        assert rhfn.complete_header(conf, rstdata) == 'my aching big</head>hurts'
        rstdata = 'my head hurts'
        assert rhfn.complete_header(conf, rstdata) == ' aching bigmy head hurts'
        conf = {'url': 'hier'}
        rstdata = 'hier/ en hier'
        assert rhfn.complete_header(conf, rstdata) == '/ en /'

    def test_save_to_mirror(self, monkeypatch, capsys):
        def mock_apply_deletions_mirror(*args):
            print('args for apply_deletions: `{}` `{}`'.format(*args))
        def mock_read_html_data(*args):
            print('args for read_html_data: `{}` `{}` `{}`'.format(*args))
            return '', '...'
        def mock_read_html_data_error(*args):
            return 'read_html_data failed', ''
        def mock_complete_header(*args):
            print('args for complete_header: `{}` `{}`'.format(*args))
            return '...'
        def mock_update_mirror(*args, **kwargs):
            print('args for update_mirror: `{}` `{}` `{}` `{}` `{}`'.format(args[0], args[1],
                                                                            args[2],
                                                                            kwargs['directory'],
                                                                            kwargs['dry_run']))
        def mock_update_mirror_failed_1(*args, **kwargs):
            raise AttributeError('name')
        def mock_update_mirror_failed_2(*args, **kwargs):
            raise AttributeError('error')
        monkeypatch.setattr(rhfn.dml, 'apply_deletions_mirror', mock_apply_deletions_mirror)
        assert rhfn.save_to_mirror(self.sitename, '', self.filename + '.x', {}) == (
                'Not a valid html file name')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')
        monkeypatch.setattr(rhfn, 'read_html_data', mock_read_html_data_error)
        assert rhfn.save_to_mirror(self.sitename, '', self.filename, {}) == (
                'read_html_data failed')
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n')
        monkeypatch.setattr(rhfn, 'read_html_data', mock_read_html_data)
        monkeypatch.setattr(rhfn, 'complete_header', mock_complete_header)
        monkeypatch.setattr(rhfn.dml, 'update_mirror', mock_update_mirror)
        assert rhfn.save_to_mirror(self.sitename, '', self.filename, {}) == ''
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n'
            'args for read_html_data: `testsite` `` `testname`\n'
            'args for complete_header: `{}` `...`\n'
            'args for update_mirror: `testsite` `testname` `...` `` `False`\n')
        monkeypatch.setattr(rhfn.dml, 'update_mirror', mock_update_mirror_failed_1)
        assert rhfn.save_to_mirror(self.sitename, 'en', self.filename, {}) == 'html_name_missing'
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` `en`\n'
            'args for read_html_data: `testsite` `en` `testname`\n'
            'args for complete_header: `{}` `...`\n')
        monkeypatch.setattr(rhfn.dml, 'update_mirror', mock_update_mirror_failed_2)
        assert rhfn.save_to_mirror(self.sitename, '', self.filename + '.html', {}) == 'error'
        assert capsys.readouterr().out == ('args for apply_deletions: `testsite` ``\n'
            'args for read_html_data: `testsite` `` `testname`\n'
            'args for complete_header: `{}` `...`\n')


class TestProgressList:
    def test_build_progress_list(self, monkeypatch):
        def mock_get_all_doc_stats_empty(*args):
            return []
        def mock_get_all_doc_stats(*args):
            return [('testdir2', [('test', (3, 2, 1)), ('index', (1, 2, 3))]),
                    ('testdir1', [('index', (2, 2, 2))]),
                    ('/', [('index', (1, 1, 2)), ('about', (2, 2, 1))])]
        monkeypatch.setattr(rhfn.dml, 'get_all_doc_stats', mock_get_all_doc_stats_empty)
        assert rhfn.build_progress_list('testsite') == []
        monkeypatch.setattr(rhfn.dml, 'get_all_doc_stats', mock_get_all_doc_stats)
        assert rhfn.build_progress_list('') == [('/', 'about', 1, (2, 2, 1)),
                                                ('/', 'index', 2, (1, 1, 2)),
                                                ('testdir1', 'index', 2, (2, 2, 2)),
                                                ('testdir2', 'index', 2, (1, 2, 3)),
                                                ('testdir2', 'test', 0, (3, 2, 1))]

    def test_get_copystand_filepath(self, monkeypatch):
        monkeypatch.setattr(rhfn.datetime, 'datetime', MockDatetime)
        reportname = 'overview-20200101000000'
        assert rhfn.get_copystand_filepath('s') == pathlib.Path(rhfn.WEBROOT / 's' / reportname)

    def test_get_progress_line_values(self):
        mindate = rhfn.datetime.datetime.min
        maxdate = rhfn.datetime.datetime.max
        line = ('/', 'index', 0,  (maxdate, mindate, mindate))
        expected = ['index', '--> 31-12-9999 23:59:59 <--', 'n/a', 'n/a']
        assert rhfn.get_progress_line_values(line) == expected
        line = ('dir', 'file', 2,  (maxdate, maxdate, maxdate))
        expected = ['dir/file', '31-12-9999 23:59:59', '31-12-9999 23:59:59',
                    '--> 31-12-9999 23:59:59 <--']
        assert rhfn.get_progress_line_values(line) == expected


class TestTrefwLijst:
    def test_get_reflinks_in_dir(self, monkeypatch):
        def mock_list_docs_empty(*args, **kwargs):
            return []
        def mock_list_docs(*args, **kwargs):
            return ['doc2skip1', 'doc2skip2', 'doctogo']
        def mock_list_docs_2(*args, **kwargs):
            return ['docnorefs', 'doc-w-refs']
        def mock_get_doc_stats(*args):
            if args[1] == 'doc2skip1':
                return rhfn.dml.Stats(2, 1, 1)
            elif args[1] == 'doc2skip2':
                return rhfn.dml.Stats(2, 2, 1)
            else:
                return rhfn.dml.Stats(2, 2, 2)
        def mock_read_src_data_error(*args):
            return 'read_src_error', ''
        def mock_read_src_data(*args):
            if args[2] == 'docnorefs':
                return '', ''
            else:
                return '', '.. refkey:: itsaref\n.. refkey:: alsoaref: here'
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs_empty)
        assert rhfn.get_reflinks_in_dir('testsite') == ({}, [])
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs)
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats)
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data_error)
        assert rhfn.get_reflinks_in_dir('testsite', 'testdir') == ({}, [('testdir', 'doctogo',
                                                                         'read_src_error')])
        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs_2)
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data)
        assert rhfn.get_reflinks_in_dir('testsite') == ({'Itsaref': ['/doc-w-refs.html'],
                                                         'Alsoaref': ['/doc-w-refs.html#here']}, [])

    def test_class(self):
        testobj = rhfn.TrefwoordenLijst('testsite')
        assert testobj.sitename == 'testsite'
        assert testobj.lang == rhfn.LANG
        assert not testobj.sef
        assert testobj.current_letter == ''
        # dit test meteen de clear_containers methode:
        assert testobj.titel == []
        assert testobj.teksten == []
        assert testobj.links == []
        assert testobj.anchors == []

    def test_build(self, monkeypatch, capsys):
        def mock_get_reflinks_none(*args):
            return {}, []
        def mock_get_reflinks(*args):
            # print('called get_reflinks')
            return {'x': ['doc'], 'y': ['doc1', 'doc2']}, ['a message']
        def mock_start_page(*args):
            print('called start_page')
            return 'first to_top'
        def mock_finish_letter(*args):
            print('called finish_letter with `{}`'.format(args[1]))
        def mock_clear_containers(*args):
            print('called clear_containers')
        def mock_start_new_letter(*args):
            print('called start_new_letter')
        def mock_start_new_keyword(*args):
            print('called start_new_keyword with `{}`'.format(args[2]))

        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'get_reflinks', mock_get_reflinks_none)
        testobj = rhfn.TrefwoordenLijst('sitename')
        testobj.data = []
        assert testobj.build() == ('', 'No index created: no reflinks found')

        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'get_reflinks', mock_get_reflinks)
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'start_page', mock_start_page)
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'finish_letter', mock_finish_letter)
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'clear_containers', mock_clear_containers)
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'start_new_letter', mock_start_new_letter)
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'start_new_keyword', mock_start_new_keyword)
        testobj = rhfn.TrefwoordenLijst('sitename')
        testobj.data = []
        testobj.titel = 'xx'
        testobj.teksten = ['yy']
        assert testobj.build() == (('while creating this page, the following messages were'
                                    ' generated:\n----------------------------------------'
                                    '------------------------\n. a message'), True)
        assert capsys.readouterr().out == ('called clear_containers\n'
                                           'called start_page\n'
                                           'called finish_letter with `first to_top`\n'
                                           'called clear_containers\n'
                                           'called start_new_letter\n'
                                           'called start_new_keyword with `x`\n'
                                           'called finish_letter with `+   top_`\n'
                                           'called clear_containers\n'
                                           'called start_new_letter\n'
                                           'called start_new_keyword with `y`\n'
                                           'called finish_letter with `+   top_`\n')

    def test_get_reflinks(self, monkeypatch):
        def mock_get_reflinks_in_dir(*args, **kwargs):
            dirname = args[1] if len(args) > 1 else ''
            return {'trefw': '{}/doc'.format(dirname)}, ['error from {}'.format(dirname)]
        def mock_list_dirs(*args):
            return ['subdir']
        monkeypatch.setattr(rhfn, 'get_reflinks_in_dir', mock_get_reflinks_in_dir)
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs)
        # volgens mij moet het dit zijn:
        # assert rhfn.TrefwoordenLijst('site').get_reflinks() == ({'trefw': ['/doc', 'subdir/doc']},
        #                                                         ['error from ',
        #                                                          'error from subdir'])
        # maar de testuitvoering zegt dat het dit moet zijn:
        assert rhfn.TrefwoordenLijst('site').get_reflinks() == ({'trefw': 'subdir/doc'},
                                                                ['error from ',
                                                                 'error from subdir'])

    def test_start_page(self, monkeypatch):
        def mock_get_text(*args):
            return 'Index Header'
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        testobj = rhfn.TrefwoordenLijst('magiokis')
        assert testobj.start_page() == "+   `top <#header>`_"
        assert testobj.data == ['Index Header', '============', '', '']
        testobj = rhfn.TrefwoordenLijst('testsite')
        assert testobj.start_page() == "+   top_"
        assert testobj.data == ['.. _top:', '`back to root </>`_', '', '.. textheader:: Index', '']

    def test_start_new_letter(self):
        testobj = rhfn.TrefwoordenLijst('magiokis')
        testobj.data = ['', '', '', ' ']
        testobj.current_letter = 'A'
        testobj.start_new_letter()
        assert testobj.data == ['', '', '', ' A_ ', '']
        assert testobj.titel == ['.. _A:\n\n**A**', '']
        assert testobj.linkno == 0
        testobj = rhfn.TrefwoordenLijst('testsite')
        testobj.data = ['', '', '', '', '', '', ' ']
        testobj.current_letter = 'X'
        testobj.start_new_letter()
        assert testobj.data == ['', '', '', '', '', '', ' X_ ', '']
        assert testobj.titel == ['X', '-']
        assert testobj.linkno == 0

    def test_start_new_keyword(self):
        testobj = rhfn.TrefwoordenLijst('testsite')
        testobj.teksten = ['a']
        testobj.start_new_keyword({'x': []}, 'x')
        assert testobj.teksten == ['a', '+   x']
        testobj = rhfn.TrefwoordenLijst('testsite')
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
        testobj = rhfn.TrefwoordenLijst('testsite')
        testobj.data = ['xxx']
        testobj.titel = ['Dit', 'is een titel']
        testobj.teksten = ['Dit zijn', 'teksten']
        testobj.links = ['A', 'B', 'C']
        testobj.anchors = ['here', 'and here']
        testobj.finish_letter('to-top')
        assert testobj.data == ['xxx', 'Dit', 'is een titel', '', 'Dit zijn', 'teksten', 'to-top',
                                '', 'A', 'B', 'C', '', 'here', 'and here', '']


class TestSearchRelated:
    def test_search_site(self, monkeypatch, capsys):
        def mock_read_dir(*args):
            if len(args) == 3:
                print('read_dir called with args `{}` `{}` `{}`'.format(*args))
                where = '/'
            else:
                print('read_dir called with args `{}` `{}` `{}` `{}`'.format(*args))
                where = args[3]
            return {where: ['this', 'that']}
        def mock_list_dirs(*args):
            return ['subdir']

        monkeypatch.setattr(rhfn, 'read_dir', mock_read_dir)
        monkeypatch.setattr(rhfn.dml, 'list_dirs', mock_list_dirs)
        assert rhfn.search_site('testsite', 'needle', 'safety pin') == {'/': ['this', 'that'],
                                                                        'subdir':['this', 'that']}
        assert capsys.readouterr().out == ('read_dir called with args `testsite` `needle`'
                                           ' `safety pin`\n'
                                           'read_dir called with args `testsite` `needle`'
                                           ' `safety pin` `subdir`\n')

    def test_read_dir(self, monkeypatch):
        def mock_list_docs(*args, **kwargs):
            return ['doc1', 'doc2']
        def mock_process_file(*args):
            return 'processed `{}` `{}` `{}` `{}` `{}`'.format(*args)

        monkeypatch.setattr(rhfn.dml, 'list_docs', mock_list_docs)
        monkeypatch.setattr(rhfn, 'process_file', mock_process_file)
        assert rhfn.read_dir('testsite', 'needle', 'pin', 'dirname') == {
                ('dirname', 'doc1'): 'processed `testsite` `dirname` `doc1` `needle` `pin`',
                ('dirname', 'doc2'): 'processed `testsite` `dirname` `doc2` `needle` `pin`'}

    def test_process_file(self, monkeypatch, capsys):
        def mock_get_doc_contents(*args):
            print('args for get_doc `{}`, `{}`, `{}`, `{}`'.format(*args))
            return 'text\nnothing\nmore text'
        def mock_update_rst(*args):
            print('args for update_rst: `{}` `{}` `{}` `{}`'.format(*args))
        monkeypatch.setattr(rhfn.dml, 'get_doc_contents', mock_get_doc_contents)
        monkeypatch.setattr(rhfn.dml, 'update_rst', mock_update_rst)
        assert rhfn.process_file('testsite', 'dir', 'file', 'text', 'taxes') == [(1, 'text', [1]),
                (3, 'more text', [6])]
        assert capsys.readouterr().out == ( 'args for get_doc `testsite`, `file`, `src`, `dir`\n'
                                            'args for update_rst: `testsite` `file`'
                                            ' `taxes\nnothing\nmore taxes` `dir`\n')

    def test_searchdict2list(self, monkeypatch):
        inputdict = {('', 'index'): [(1, 'regel na regel', [1, 10]),
                                     (3, 'een eindeloos uitzicht vol regels' + 20 * '@#$%' , [28])],
                     ('dir', 'file0'): [],
                     ('dir', 'file'): [(24, 'geen regeling', [6])]}
        expected = [('/index', 1, ' **regel**  na  **regel** '),
                    ('/index', 3, '...eloos uitzicht vol  **regel** s' + 13 * '@#$%' + '@#$...'),
                    ('dir/file', 24, 'geen  **regel** ing')]
        assert rhfn.searchdict2list(inputdict, 'regel') == expected

    def test_get_copysearch_filepath(self, monkeypatch):
        monkeypatch.setattr(rhfn.datetime, 'datetime', MockDatetime)
        reportname = 'search-results-20200101000000'
        assert rhfn.get_copysearch_filepath('s') == pathlib.Path(rhfn.WEBROOT / 's' / reportname)


class TestUpdateAll:
    """tests for regenerate all functionality"""
    def test_check_for_includes(self, monkeypatch):
        fake_webroot = pathlib.Path('/tmp/rhfntest')
        fake_sitename = 'testsite'
        monkeypatch.setattr(rhfn, 'WEBROOT', fake_webroot)
        fake_include = fake_webroot / fake_sitename / '.source' / 'include.rst'
        fake_include.parent.mkdir(parents=True, exist_ok=True)
        fake_include.touch(exist_ok=True)

        assert rhfn.check_for_includes(fake_sitename, '') == []
        rstdata = ".. include:: {}".format(fake_include)
        assert rhfn.check_for_includes(fake_sitename, rstdata) == ['include']
        rstdata = ".. incl:: {}".format('../include.rst')
        assert rhfn.check_for_includes(fake_sitename, rstdata) == ['include']

    def test_update_all_class(self):
        sitename, conf = 'testsite', {'css': []}
        testsubj = rhfn.UpdateAll(sitename, conf)
        assert testsubj.sitename == sitename
        assert testsubj.conf == conf
        assert testsubj.missing_only == False
        assert testsubj.needed_only == False
        assert testsubj.show_only == False
        testsubj = rhfn.UpdateAll(sitename, conf, True, True, True)
        assert testsubj.sitename == sitename
        assert testsubj.conf == conf
        assert testsubj.missing_only == True
        assert testsubj.needed_only == True
        assert testsubj.show_only == True

    def test_rebuild_mirror(self, monkeypatch, capsys):
        def mock_save_to_mirror(*args, **kwargs):
            run = '(dry run)' if kwargs.get('dry_run', False) else ''
            print('save_to_mirror {} was called'.format(run))
            return ''

        sitename, conf = 'testsite', {'seflinks': False}
        testsubj = rhfn.UpdateAll(sitename, conf)
        testsubj.path = pathlib.Path('/tmp/rhfntest/testsite')
        filename = 'testfile'
        dirname = ''
        monkeypatch.setattr(rhfn, 'save_to_mirror', mock_save_to_mirror)
        assert testsubj.rebuild_mirror(dirname, filename) == ('')
        assert capsys.readouterr().out == 'save_to_mirror  was called\n'

        testsubj.show_only = True
        assert testsubj.rebuild_mirror(dirname, filename) == 'regen_mirror_msg'
        assert capsys.readouterr().out == ''

    def test_rebuild_html(self, monkeypatch, capsys):
        def mock_rst2html(*args):
            print('rst2html was called')
            return ''
        def mock_save_html_data(*args, **kwargs):
            run = '(dry run)' if kwargs.get('dry_run', False) else ''
            print('save_html_data {} was called'.format(run))
            return ''
        def mock_save_html_data_msg(*args, **kwargs):
            return 'save_html_data_err'
        def mock_read_conf(*args):
            return '', {'lang': rhfn.LANG}
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)

        sitename, conf = 'testsite', {'css': []}
        testsubj = rhfn.UpdateAll(sitename, conf)
        filename = 'testfile'
        dirname = ''
        testsubj.rstdata = ''
        monkeypatch.setattr(rhfn, 'rst2html', mock_rst2html)
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data)
        assert testsubj.rebuild_html(dirname, filename) == ''
        assert capsys.readouterr().out == 'rst2html was called\nsave_html_data  was called\n'

        testsubj.show_only = True
        assert testsubj.rebuild_html(dirname, filename) == 'regen_target_msg'
        assert capsys.readouterr().out == 'rst2html was called\n'

        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data_msg)
        assert testsubj.rebuild_html(dirname, filename) == 'regen_target_msg'  # 'save_html_data_err'

    def test_check_for_updated_includes(self, monkeypatch):
        def mock_check_for_includes_none(*args):
            return []
        def mock_check_for_includes_some(*args):
            return ['hello', 'you']
        def mock_get_doc_stats(*args):
            return rhfn.dml.Stats(2, 2, 2)

        sitename, conf = 'testsite', {'css': []}
        testsubj = rhfn.UpdateAll(sitename, conf)
        testsubj.rstdata = ''
        stats = rhfn.dml.Stats(1, 1, 1)
        monkeypatch.setattr(rhfn, 'check_for_includes', mock_check_for_includes_none)
        assert testsubj.check_for_updated_includes(stats) == (False, False)
        monkeypatch.setattr(rhfn, 'check_for_includes', mock_check_for_includes_some)
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.check_for_updated_includes(stats) == (True, True)
        assert testsubj.include_timestamps == {'hello': rhfn.dml.Stats(2, 2, 2),
                                               'you': rhfn.dml.Stats(2, 2, 2)}
        stats = rhfn.dml.Stats(2, 2, 1)
        assert testsubj.check_for_updated_includes(stats) == (False, True)
        assert testsubj.include_timestamps == {'hello': rhfn.dml.Stats(2, 2, 2),
                                               'you': rhfn.dml.Stats(2, 2, 2)}
        stats = rhfn.dml.Stats(2, 2, 2)
        assert testsubj.check_for_updated_includes(stats) == (False, False)
        assert testsubj.include_timestamps == {'hello': rhfn.dml.Stats(2, 2, 2),
                                               'you': rhfn.dml.Stats(2, 2, 2)}

    def test_update_all_go(self, monkeypatch, capsys):
        def mock_build_progress_list_empty(*args):
            return []
        def mock_build_progress_list_0(*args):
            return [('/', 'index', 0, rhfn.dml.Stats(2, 1, 1)),
                    ('hi', 'index', 1, rhfn.dml.Stats(2, 2, 1))]
        def mock_build_progress_list_1(*args):
            return [('/', 'index', 1, rhfn.dml.Stats(2, 2, 1))]
        def mock_build_progress_list_2(*args):
            return [('/', 'index', 2, rhfn.dml.Stats(2, 2, 2))]
        def mock_read_src_data_msg(*args):
            return 'message from read_src_data', ''
        def mock_read_src_data(*args):
            return '', 'some_text'
        def mock_check_for_updated_includes_all(*args):
            return True, True
        def mock_check_for_updated_includes_none(*args):
            return False, False
        def mock_rebuild_html(*args):
            return ''
        def mock_rebuild_html_msg(*args):
            return 'message from rebuild_html'
        def mock_rebuild_mirror(*args):
            return ''
        def mock_rebuild_mirror_msg(*args):
            return 'message from rebuild_mirror'
            return '', True

        # testcase: nothing in progress list (unrealistic)
        testsubj = rhfn.UpdateAll('testsite', {})
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_empty)
        assert testsubj.go() == []
        # testcase: document last generated on mirror
        # dit geldt niet meer omdat we nu ook naar gewijzigde includes kijken
        # monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_2)
        # assert testsubj.go() == []
        # testcase: document excluded in config
        testsubj.conf = {'do-not-generate': ['/index']}
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_2)
        assert testsubj.go() == []
        # testcase: error when fetching source
        testsubj.conf = {}
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data_msg)
        assert testsubj.go() == [('/index', 'message from read_src_data')]
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data)
        # testcase: error when building html
        monkeypatch.setattr(rhfn.UpdateAll, 'rebuild_html', mock_rebuild_html_msg)
        assert testsubj.go() == [('/index', 'message from rebuild_html')]
        # testcase: error when building mirror
        monkeypatch.setattr(rhfn.UpdateAll, 'rebuild_html', mock_rebuild_html)
        monkeypatch.setattr(rhfn.UpdateAll, 'rebuild_mirror', mock_rebuild_mirror_msg)
        assert testsubj.go() == [('/index', 'html_saved'),
                                 ('/index', 'message from rebuild_mirror')]
        # testcase: no errors
        monkeypatch.setattr(rhfn.UpdateAll, 'rebuild_mirror', mock_rebuild_mirror)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to')]

        # testcase: generate when missing for existing document
        testsubj.missing_only = True
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_1)
        assert testsubj.go() == []

        # testcases: only generate when needed
        testsubj.needed_only = True
        # testcase: include was updated after generating document
        monkeypatch.setattr(rhfn.UpdateAll, 'check_for_updated_includes',
                            mock_check_for_updated_includes_all)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to')]
        # testcase: document source was updated after converting
        # also:     document was converted but not yet updated on mirror
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_0)
        monkeypatch.setattr(rhfn.UpdateAll, 'check_for_updated_includes',
                            mock_check_for_updated_includes_none)
        assert testsubj.go() == [('/index', 'html_saved'), ('/index', 'copied_to'),
                                 ('hi/index', 'copied_to')]
        # # testcase: document was converted but not yet updated on mirror
        # monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_1)
        # assert testsubj.go() == [('/index', 'copied_to')]
        # testcase: no actions needed
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list_2)
        assert testsubj.go() == []


class TestR2hState:
    """tests for the logic in the methods of the state class
    """
    def test_init(self, monkeypatch):
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        assert testsubj.sitename == 'testsite'
        assert testsubj.rstfile == testsubj.htmlfile == testsubj.newfile == testsubj.rstdata == ""
        assert testsubj.current == testsubj.oldtext == testsubj.oldhtml == ""
        assert testsubj.conf == rhfn.DFLT_CONF
        assert testsubj.newconf == False
        assert testsubj.loaded == 'initial'  # rhfn.RST

    def test_currentify(self, monkeypatch):
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.current = ''
        assert testsubj.currentify('filename') == 'filename'

        testsubj.current = 'dirname'
        testsubj.conf = {'seflinks': True}
        assert testsubj.currentify('filename.x') == 'dirname/filename/index.x'

    def test_get_lang(self, monkeypatch):
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        assert testsubj.get_lang() == rhfn.LANG

        testsubj.conf = {'lang': 'en'}
        assert testsubj.get_lang() == 'en'

    def test_get_conf(self, monkeypatch):
        def mock_read_conf(*args):
            return '', {'key1': 'value1', 'key2': 'value2'}
        def mock_list_subdirs(*args):
            return ['subdir1', 'subdir2']
        def mock_read_conf_mld(*args):
            return 'error', {}
        def mock_get_text(*args):
            return '`{}` conf error'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.newconf = True
        assert testsubj.get_conf('testsite') == ''
        assert testsubj.conf == rhfn.DFLT_CONF
        assert testsubj.current == ''
        assert testsubj.subdirs == []
        assert testsubj.loaded == rhfn.CONF

        testsubj.newconf = False
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)
        monkeypatch.setattr(rhfn, 'list_subdirs', mock_list_subdirs)
        assert testsubj.get_conf('testsite') == ''
        assert testsubj.conf == {'key1': 'value1', 'key2': 'value2'}
        assert testsubj.current == ''
        assert testsubj.subdirs == ['subdir1', 'subdir2']
        assert testsubj.loaded == rhfn.CONF

        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf_mld)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.get_conf('testsite') == '`testsite` conf error'

    def test_index(self, monkeypatch):
        def mock_get_conf(*args):
            return ''
        def mock_get_conf_msg(*args):
            return 'msg from get_conf'
        def mock_conf2text(*args):
            return 'confdata'

        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        testsubj = rhfn.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = ''
        # import pdb; pdb.set_trace()
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'no_confs', '', '')

        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = 'testsite'
        monkeypatch.setattr(rhfn.R2hState, 'get_conf', mock_get_conf)
        testsubj.conf = {}
        monkeypatch.setattr(rhfn, 'conf2text', mock_conf2text)
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'conf_init', 'confdata',
                                    'testsite')
        assert testsubj.settings == 'testsite'

        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.rstfile = 'rstfile'
        testsubj.htmlfile = 'htmlfile'
        testsubj.newfile = 'newfile'
        testsubj.sitename = 'testsite'
        monkeypatch.setattr(rhfn.R2hState, 'get_conf', mock_get_conf_msg)
        assert testsubj.index() == ('rstfile', 'htmlfile', 'newfile', 'msg from get_conf', '',
                                    'testsite')

    def test_loadconf(self, monkeypatch):
        def mock_get_conf(*args):
            return ''
        def mock_get_conf_err(*args):
            return 'error from get_conf'
        def mock_conf2text(*args):
            return 'text from conf'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn.R2hState, 'get_conf', mock_get_conf)
        monkeypatch.setattr(rhfn, 'conf2text', mock_conf2text)
        assert testsubj.loadconf('oldsett', 'c_newitem') == ('new_conf_made', 'text from conf',
                                                             'c_newitem', '')
        assert testsubj.newconf
        assert testsubj.sitename == 'c_newitem'

        assert testsubj.loadconf('newsett', '') == ('conf_loaded', 'text from conf', 'newsett', '')
        assert not testsubj.newconf
        assert testsubj.sitename == 'newsett'

    def test_saveconf(self, monkeypatch, capsys):
        def mock_get_conf(*args):
            return ''
        def mock_get_conf_err(*args):
            return 'error from get_conf'
        def mock_new_conf_msg(*args):
            return 'new_conf_msg', 'new-url'
        def mock_new_conf(*args):
            return '', 'new-url'
        def mock_new_conf_nourl(*args):
            return '', 'new-url'
        def mock_save_conf(*args, **kwargs):
            print('call save_conf with args `{}`, kwargs `{}`'.format(args, kwargs))
            return ''
        def mock_save_conf_mld(*argsi, **kwargs):
            return 'mld from save_conf'
        def mock_init_css(*args):
            print('call init_css')
        def mock_get_conf(*args):
            return ''
        def mock_get_conf_mld(*args):
            return 'mld from get_conf'
        def mock_conf2text(*args):
            return 'conf2text'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        testsubj.settings = 'x'
        testsubj.newfile = 'y'
        assert testsubj.saveconf('testsite', 'newsett', '') == ('supply_text', '', 'x', 'y')
        testsubj.loaded = rhfn.RST
        assert testsubj.saveconf('testsite', 'newsett', 'conftext') == ('conf_invalid', 'conftext',
                                                                        'x', 'y')
        testsubj.loaded = rhfn.CONF
        assert testsubj.saveconf('oldsett', 'c_newitem', 'conftext') == ('fname_invalid',
                                                                         'conftext', 'x', 'y')
        testsubj.newconf = True
        monkeypatch.setattr(rhfn, 'new_conf', mock_new_conf_msg)
        assert testsubj.saveconf('oldsett', 'newsett', 'conftext') == ('new_conf_msg', 'conftext',
                                                                       'x', 'y')
        monkeypatch.setattr(rhfn, 'new_conf', mock_new_conf)
        monkeypatch.setattr(rhfn, 'save_conf', mock_save_conf)
        monkeypatch.setattr(rhfn, 'init_css', mock_init_css)
        monkeypatch.setattr(rhfn.R2hState, 'get_conf', mock_get_conf)
        monkeypatch.setattr(rhfn, 'conf2text', mock_conf2text)
        assert testsubj.saveconf('oldsett', 'newsett', "url: ''") == ('conf_saved activate_url',
                                                                      'conf2text', 'newsett', '')
        assert testsubj.newconf == False
        assert testsubj.sitename == 'newsett'
        assert testsubj.rstdata == 'conf2text'
        assert capsys.readouterr().out == ("call save_conf with args `('newsett', 'url: new-url',"
                                           " '')`, kwargs `{'urlcheck': False}`\n"
                                           'call init_css\n')
        testsubj.newconf = False
        monkeypatch.setattr(rhfn, 'new_conf', mock_new_conf_nourl)
        assert testsubj.saveconf('oldsett', 'newsett', "url: ''") == ('conf_saved note_no_url',
                                                                      'conf2text', 'newsett', '')

    def test_loadxtra(self, monkeypatch):
        def mock_get_custom_directives_filename(*args):
            return 'directives.py', 'a_word'
        def mock_read_data(filename):
            return '', 'read data from `{}`'.format(filename)
        def mock_read_data_err(*args):
            return 'mld from read_data', ''
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'get_custom_directives_filename',
                            mock_get_custom_directives_filename)
        monkeypatch.setattr(rhfn, 'read_data', mock_read_data_err)
        assert testsubj.loadxtra() == ('mld from read_data', '')
        monkeypatch.setattr(rhfn, 'read_data', mock_read_data)
        assert testsubj.loadxtra() ==('dirs_loaded', 'read data from `directives.py`')
        assert testsubj.loaded == rhfn.XTRA

    def test_savextra(self, monkeypatch):
        def mock_save_to(*args):
            return ''
        def mock_save_to_mld(*args):
            return 'mld from save_to'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.savextra('') == 'supply_text'
        testsubj.loaded = rhfn.RST
        assert testsubj.savextra('some_content') == 'dirs_invalid'
        testsubj.loaded = rhfn.XTRA
        monkeypatch.setattr(rhfn, 'save_to', mock_save_to_mld)
        assert testsubj.savextra('some_content') == 'mld from save_to'
        monkeypatch.setattr(rhfn, 'save_to', mock_save_to)
        assert testsubj.savextra('some_content') == 'dirs_saved'

    def test_loadrst(self, monkeypatch):
        def mock_get_text(*args):
            if args[0] == 'c_newitem':
                return '-- new --'
            elif args[0] == 'chdir_down':
                return args[0] + ' into `{}`'
            return args[0]
        def mock_read_tpl_data(*args):
            return 'template data'
        def mock_read_src_data(*args):
            return '', 'source data'
        def mock_read_src_data_mld(*args):
            return 'mld from read_src_data', ''
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        testsubj.rstdata = 'old data'
        testsubj.htmlfile = 'x'
        testsubj.newfile = 'y'
        assert testsubj.loadrst('') == ('unlikely_1', 'old data', 'x', 'y')
        assert testsubj.loadrst('-- new --') == ('save_reminder', '', '', '')
        assert testsubj.loaded == rhfn.RST
        monkeypatch.setattr(rhfn, 'read_tpl_data', mock_read_tpl_data)
        assert testsubj.loadrst('-- template --') == ('save_reminder', 'template data', '', '')
        assert testsubj.loaded == rhfn.RST
        assert testsubj.loadrst('subdir/') == ('chdir_down into `subdir`', '', '', '')
        assert testsubj.loadrst('..') == ('chdir_up', '', '', '')
        testsubj.rstdata = 'old data'
        testsubj.htmlfile = 'x'
        testsubj.newfile = 'y'
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data_mld)
        assert testsubj.loadrst('testfile') == ('mld from read_src_data', 'old data', 'x', 'y')
        assert testsubj.oldtext == 'old data'
        monkeypatch.setattr(rhfn, 'read_src_data', mock_read_src_data)
        assert testsubj.loadrst('testfile') == ('src_loaded', 'source data', 'testfile.html', '')
        assert testsubj.loaded == rhfn.RST
        assert testsubj.oldtext == 'source data'
        assert testsubj.rstfile == 'testfile'

    def test_rename(self, monkeypatch, capsys):
        def mock_mark_deleted(*args):
            print('called mark_deleted with args `{}`'.format(args))
            return 'oepsie'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.rename('', '', '')[0] == 'new_name_missing'
        assert testsubj.rename('', 'directory/', '')[0] == 'incorrect_name'
        assert testsubj.rename('', 'text.tpl', '')[0] == 'incorrect_name'
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        assert testsubj.rename('', 'newfile', '')[0] == 'new_name_taken'
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('mld', ''))
        monkeypatch.setattr(rhfn, 'save_src_data', lambda x, y, z, a, b: 'src_file_missing')
        assert testsubj.rename('', 'newfile', '')[0] == 'new_file_missing'
        monkeypatch.setattr(rhfn, 'save_src_data', lambda x, y, z, a, b: '')
        monkeypatch.setattr(rhfn, 'mark_deleted', mock_mark_deleted)
        assert testsubj.rename('', 'newfile', '')[0] == 'oepsie'
        assert capsys.readouterr().out == "called mark_deleted with args `('testsite', '', '')`\n"
        monkeypatch.setattr(rhfn, 'mark_deleted', lambda x, y, z: '')
        assert testsubj.rename('oldfile', 'newfile', 'rstdata') == ('renamed', 'newfile.rst',
                                                                    'newfile.html', '', 'rstdata')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext, testsubj.rstdata == ('rstdata', 'rstdata')

    def test_revert(self, monkeypatch, capsys):
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.revert('dirname/', '')[0] == 'incorrect_name'
        assert testsubj.revert('text.tpl', '')[0] == 'incorrect_name'
        monkeypatch.setattr(rhfn, 'revert_src', lambda x, y, z: '')
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('mld', ''))
        assert testsubj.revert('', '')[0] == 'mld'
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        assert testsubj.revert('rstfile', 'rstdata') == ('reverted', 'rstfile', 'rstfile.html',
                                                         '', 'some_text')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext, testsubj.rstdata == ('rstdata', 'rstdata')

    def test_delete(self, monkeypatch, capsys):
        def mock_mark_deleted(*args):
            print('called mark_deleted with args `{}`'.format(args))
            return 'oepsie'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.delete('dirname/', '')[0] == 'incorrect_name'
        assert testsubj.delete('text.tpl', '')[0] == 'incorrect_name'
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('mld', ''))
        assert testsubj.delete('', '')[0] == 'mld'
        monkeypatch.setattr(rhfn, 'read_src_data', lambda x, y, z: ('', 'some_text'))
        monkeypatch.setattr(rhfn, 'mark_deleted', mock_mark_deleted)
        assert testsubj.delete('', 'olddata')[0] == 'oepsie'
        assert capsys.readouterr().out == "called mark_deleted with args `('testsite', '', '')`\n"
        monkeypatch.setattr(rhfn, 'mark_deleted', lambda x, y, z: '')
        assert testsubj.delete('rstfile', 'rstdata') == ('deleted', 'rstfile', 'rstfile.html', '',
                                                         '')
        assert capsys.readouterr().out == ''
        assert testsubj.oldtext == ''
        assert testsubj.rstdata == ''

    def test_saverst(self, monkeypatch, capsys):
        def mock_translate_action(*args):
            return args[0]
        def mock_make_new_dir(*args):
            print('make_new_dir called using args `{}` `{}`'.format(*args))
            return ''
        def mock_save_tpl_data(*args):
            print('save_tpl_data called using args `{}` `{}` `{}`'.format(*args))
            return ''
        def mock_check_if_rst(*args):
            print('check_if_rst called using args `{}` `{}` `{}`'.format(*args))
            return ''
        def mock_save_src_data(*args):
            print('save_src_data called using args `{}` `{}` `{}` `{}` `{}`'.format(*args))
            return ''
        def mock_get_text_exc(*args):
            raise KeyError
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        monkeypatch.setattr(rhfn, 'make_new_dir', lambda x, y: 'mld from make_new_dir {}')
        assert testsubj.saverst('dirname/', '', '') == ('mld from make_new_dir dirname', 'a',
                                                            'b', 'c', '')
        monkeypatch.setattr(rhfn, 'make_new_dir', mock_make_new_dir)
        assert testsubj.saverst('dirname/', '', '') == ('new_subdir', 'dirname/', 'b',
                                                            '', '')
        assert capsys.readouterr().out == 'make_new_dir called using args `testsite` `dirname`\n'

        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        monkeypatch.setattr(rhfn, 'save_tpl_data',lambda x, y, z: 'mld from save_tpl_data')
        assert testsubj.saverst('test.tpl', '', 'data') == ('mld from save_tpl_data', 'a', 'b',
                                                                'c', 'data')
        monkeypatch.setattr(rhfn, 'save_tpl_data', mock_save_tpl_data)
        assert testsubj.saverst('-- test.tpl --', '', 'data') == ('tpl_saved', '', '', '', 'data')
        assert capsys.readouterr().out == ('save_tpl_data called using args `testsite` `test.tpl`'
                                           ' `data`\n')
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'

        testsubj.rstfile = 'a'
        testsubj.htmlfile = 'b'
        testsubj.newfile = 'c'
        testsubj.loaded = 'loaded'
        monkeypatch.setattr(rhfn, 'check_if_rst', lambda x, y, z: 'mld from check_if_rst')
        assert testsubj.saverst('-- new --', '', '') == ('mld from check_if_rst', 'a', 'b', 'c', '')
        monkeypatch.setattr(rhfn, 'check_if_rst', mock_check_if_rst)
        monkeypatch.setattr(rhfn, 'save_src_data', lambda x, y, z, a, b: 'mld from save_src_data')
        assert testsubj.saverst('oldfile', 'newfile', 'data') == ('mld from save_src_data', 'a',
                                                                  'b', 'c', 'data')
        assert capsys.readouterr().out == ('check_if_rst called using args `data` `loaded`'
                                           ' `newfile`\n')
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data)
        assert testsubj.saverst('oldfile', '', 'data') == ('rst_saved', 'oldfile.rst',
                                                           'oldfile.html', '', 'data')
        assert capsys.readouterr().out == ('check_if_rst called using args `data` `loaded`'
                                           ' `oldfile`\n'
                                           'save_src_data called using args `testsite` ``'
                                           ' `oldfile.rst` `data` `False`\n')
        assert testsubj.oldtext == 'data'
        assert testsubj.rstdata == 'data'

    def test_convert(self, monkeypatch, capsys):
        """ in: rstfile, newfile, rstdata; out: mld, previewdata, fname
        """
        def mock_check_if_rst(*args):
            return ''
        def mock_check_if_rst_mld(*args):
            return 'mld from check_if_rst'
        def mock_save_src_data(*args):
            print('save_src_data called')
            return ''
        def mock_save_src_data_mld(*args):
            return 'mld from save_src_data'
        def mock_rst2html(*args):
            return args[0]
        def mock_read_conf(*args):
            return '', {}
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'check_if_rst', mock_check_if_rst_mld)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                'mld from check_if_rst', '', '')
        monkeypatch.setattr(rhfn, 'check_if_rst', mock_check_if_rst)
        testsubj.oldtext = 'text\nmoretext'
        monkeypatch.setattr(rhfn, 'rst2html', mock_rst2html)
        # import pdb; pdb.set_trace()
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'newfile')
        assert capsys.readouterr().out == ''
        testsubj.oldtext = ''
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data_mld)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                'mld from save_src_data', '', '')
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data)
        assert testsubj.convert('rstfile', 'newfile', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'newfile')
        assert capsys.readouterr().out == 'save_src_data called\n'
        assert testsubj.convert('rstfile', '', 'text\r\nmoretext') == (
                '', 'text\nmoretext', 'rstfile')
        assert capsys.readouterr().out == 'save_src_data called\n'

    def test_saveall(self, monkeypatch, capsys):
        """in: rstfile, newfile, rstdata; out: mld, rstfile, htmlfile, newfile
        """
        def mock_check_if_rst(*args):
            return ''
        def mock_check_if_rst_mld(*args):
            return 'mld from check_if_rst'
        def mock_save_src_data(*args):
            print('save_src_data got args `{}` `{}` `{}` `{}` `{}`'.format(*args))
            return ''
        def mock_save_src_data_mld(*args):
            return 'mld from save_src_data'
        def mock_rst2html(*args):
            return 'converted txt'
        def mock_save_html_data(*args):
            print('save_html_data got args `{}` `{}` `{}` `{}`'.format(*args))
            return ''
        def mock_save_html_data_mld(*args):
            return 'mld from save_html_data for {}'
        def mock_read_conf(*args):
            return '', {'lang': rhfn.LANG}
        monkeypatch.setattr(rhfn, 'read_conf', mock_read_conf)
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'check_if_rst', mock_check_if_rst_mld)
        testsubj.rstfile = 'rst'
        testsubj.htmlfile = 'html'
        testsubj.newfile = 'new'
        assert testsubj.saveall('r', 'n', 'txt') == ('mld from check_if_rst', 'rst', 'html', 'new')
        monkeypatch.setattr(rhfn, 'check_if_rst', mock_check_if_rst)
        testsubj.conf = {'css': ''}
        testsubj.oldtxt = 'txt'
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data_mld)
        assert testsubj.saveall('r', 'n', 'txt') == ('mld from save_src_data', 'n.rst', 'n.html',
                                                     'new')
        testsubj.oldtxt = 'converted data'
        assert testsubj.saveall('r', '', 'txt') == ('mld from save_src_data', 'r.rst', 'r.html',
                                                     'new')
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data)
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data_mld)
        assert testsubj.saveall('r', '', 'txt') == ('mld from save_html_data for r.html', 'r.rst',

                                                    'r.html', '')
        assert capsys.readouterr().out == ('save_src_data got args `testsite` `` `r.rst` `txt`'
                                           ' `False`\n')
        assert testsubj.oldtext == 'txt'
        assert testsubj.rstdata == 'txt'
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data)
        monkeypatch.setattr(rhfn, 'rst2html', mock_rst2html)
        assert testsubj.saveall('r', '', 'txt') == ('rst_2_html', 'r.rst', 'r.html', '')
        assert capsys.readouterr().out == ('save_html_data got args `testsite` `` `r.html`'
                                           ' `converted txt`\n')

    def test_status(self, monkeypatch):
        def mock_get_doc_stats(*args):
            return rhfn.dml.Stats(datetime.datetime.fromtimestamp(2),
                                  datetime.datetime.fromtimestamp(2),
                                  datetime.datetime.fromtimestamp(2))
        def mock_get_doc_stats_2(*args):
            return rhfn.dml.Stats(datetime.datetime.fromtimestamp(2), datetime.datetime.min,
                                  datetime.datetime.min)
        def mock_get_doc_stats_3(*args):
            return rhfn.dml.Stats(datetime.datetime.min, datetime.datetime.min,
                                  datetime.datetime.min)
        testsubj = rhfn.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.status('file') == ('/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: 01-01-1970 01:00:02'
                                           ' - last migrated: 01-01-1970 01:00:02')
        testsubj = rhfn.R2hState()
        testsubj.current = 'dir'
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats)
        assert testsubj.status('file') == ('dir/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: 01-01-1970 01:00:02'
                                           ' - last migrated: 01-01-1970 01:00:02')
        testsubj = rhfn.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats_2)
        assert testsubj.status('file') == ('/file: last modified: 01-01-1970 01:00:02'
                                           ' - last converted: n/a'
                                           ' - last migrated: n/a')
        testsubj = rhfn.R2hState()
        testsubj.current = ''
        monkeypatch.setattr(rhfn.dml, 'get_doc_stats', mock_get_doc_stats_3)
        assert testsubj.status('file') == 'not possible to get stats'

    def test_loadhtml(self, monkeypatch):
        def mock_read_html_data(*args):
            return '', 'some&nbsp;text'
        def mock_read_html_data_mld(*args):
            return 'mld from read_html_data', ''
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        testsubj.rstdata = 'x'
        testsubj.rstfile = 'y'
        testsubj.htmlfile = 'z'
        assert testsubj.loadhtml('dirname/') == ('html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('') == ('html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('..') == ('html_name_missing', 'x', 'y', 'z')
        # assert testsubj.loadhtml('-- new --') == 'html_name_missing', 'x', 'y', 'z')
        assert testsubj.loadhtml('c_newitem') == ('html_name_missing', 'x', 'y', 'z')
        monkeypatch.setattr(rhfn, 'read_html_data', mock_read_html_data_mld)
        assert testsubj.loadhtml('filename') == ('mld from read_html_data', 'x', 'y', 'z')
        monkeypatch.setattr(rhfn, 'read_html_data', mock_read_html_data)
        assert testsubj.loadhtml('filename') == ('html_loaded', 'some&amp;nbsp;text',
                                                'filename.rst', 'filename.html')
        assert testsubj.oldhtml == 'some&amp;nbsp;text'
        assert testsubj.loaded == rhfn.HTML

    def test_showhtml(self, monkeypatch, capsys):
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        def mock_check_if_html(*args):
            return ''
        def mock_check_if_html_mld(*args):
            return 'mld from check_if_html'
        def mock_save_html_data(*args):
            print('call save_html_data')
            return ''
        def mock_save_html_data_mld(*args):
            return 'mld from save_html_data'
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.showhtml('text\r\nmore text') == ('mld from check_if_html', '', '')
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data)
        testsubj.oldhtml = 'text\nmore text'
        testsubj.htmlfile = 'htmlfile'
        assert testsubj.showhtml('text\r\nmore text') == ('', 'text\r\nmore text', 'htmlfile')
        assert capsys.readouterr().out == ''
        testsubj.oldhtml = ''
        assert testsubj.showhtml('text\r\nmore text') == ('', 'text\r\nmore text', 'htmlfile')
        assert capsys.readouterr().out == 'call save_html_data\n'

    def test_savehtml(self, monkeypatch):
        def mock_check_if_html(*args):
            return ''
        def mock_check_if_html_mld(*args):
            return 'mld from check_if_html'
        def mock_save_html_data(*args):
            return ''
        def mock_save_html_data_mld(*args):
            return 'mld from save_html_data'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        testsubj.rstdata = 'data'
        testsubj.newfile = 'newname'
        assert testsubj.savehtml('oldhtml', 'newhtml', 'text') == ('html_name_wrong', 'data',
                                                                   'newname')
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.savehtml('oldhtml', '', 'text') == ('mld from check_if_html', 'data',
                                                                   'newname')
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data_mld)
        assert testsubj.savehtml('oldhtml', '', 'text') == ('mld from save_html_data', 'data', '')
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data)
        assert testsubj.savehtml('fname', '', '&nbsp;text') == ('html_saved', '&amp;nbsp;text', '')
        assert testsubj.htmlfile == 'fname'

    def test_copytoroot(self, monkeypatch):
        def mock_check_if_html(*args):
            return ''
        def mock_check_if_html_mld(*args):
            return 'mld from check_if_html'
        def mock_save_to_mirror(*args):
            return ''
        def mock_save_to_mirror_mld(*args):
            return 'mld from save_to_mirror'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html_mld)
        assert testsubj.copytoroot('htmlfile', 'text') == 'mld from check_if_html'
        monkeypatch.setattr(rhfn, 'check_if_html', mock_check_if_html)
        monkeypatch.setattr(rhfn, 'save_to_mirror', mock_save_to_mirror_mld)
        assert testsubj.copytoroot('htmlfile', 'text') == 'mld from save_to_mirror'
        testsubj.htmlfile = 'somefile'
        monkeypatch.setattr(rhfn, 'save_to_mirror', mock_save_to_mirror)
        assert testsubj.copytoroot('htmlfile', 'text') == 'copied_to'
        assert testsubj.htmlfile == 'htmlfile'

    def test_makerefdoc(self, monkeypatch):
        def mock_trefwlijst(*args, **kwargs):
            return 'index data', False
        def mock_trefwlijst_norefs(*args, **kwargs):
            return '', True
        def mock_trefwlijst_err(*args, **kwargs):
            return 'data', True
        def mock_save_src_data(*args, **kwargs):
            if kwargs.get('new', False):
                return 'mld from save_src_data'
            return ''
        def mock_rst2html(*args):
            return 'converted data'
        def mock_save_html_data(*args):
            return ''
        def mock_save_to_mirror(*args):
            return ''

        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        testsubj.conf = {'css': []}
        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'build', mock_trefwlijst_norefs)
        assert testsubj.makerefdoc() == (True, )

        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'build', mock_trefwlijst)
        monkeypatch.setattr(rhfn, 'save_src_data', mock_save_src_data)
        monkeypatch.setattr(rhfn, 'rst2html', mock_rst2html)
        monkeypatch.setattr(rhfn, 'save_html_data', mock_save_html_data)
        monkeypatch.setattr(rhfn, 'save_to_mirror', mock_save_to_mirror)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        monkeypatch.setattr(rhfn.R2hState, 'get_lang', mock_get_lang)
        assert testsubj.makerefdoc() == ('index_built', 'reflist.rst', 'reflist.html', 'index data')
        assert testsubj.loaded == rhfn.RST

        monkeypatch.setattr(rhfn.TrefwoordenLijst, 'build', mock_trefwlijst_err)
        assert testsubj.makerefdoc() == ('index_built with_err', 'reflist.rst', 'reflist.html',
                                         'data')
        assert testsubj.loaded == rhfn.RST

    def test_convert_all(self, monkeypatch):
        def mock_update_all_go(*args, **kwargs):
            return [('/index', 'just text'), ('/other', 'formatted: {}')]
        def mock_update_all_go_empty(*args, **kwargs):
            return []
        def mock_get_text(*args):
            if args[0] == 'in_sim':
                return args[0]
            elif args[0] == 'docs_converted':
                return 'converted {}'
            return args[0]

        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        # FIXME: bij het simuleren van deze klasse ook teruggeven met welke argumenten deze wordt
        # aangeroepen/geinstantieerd
        monkeypatch.setattr(rhfn.UpdateAll, 'go', mock_update_all_go_empty)
        monkeypatch.setattr(rhfn, 'get_text', mock_get_text)
        assert testsubj.convert_all() == ('converted in_sim', '')
        assert testsubj.convert_all('2') == ('converted ', '')
        assert testsubj.convert_all('3') == ('converted in_sim', '')
        assert testsubj.convert_all('4') == ('converted in_sim', '')
        assert testsubj.convert_all('5') == ('converted in_sim', '')
        monkeypatch.setattr(rhfn.UpdateAll, 'go', mock_update_all_go)
        assert testsubj.convert_all('0') == ('converted ', ('/index: just text\n'
                                                            'formatted: /other'))
        assert testsubj.convert_all('1') == ('converted ', ('/index: just text\n'
                                                            'formatted: /other'))

    def test_search(self, monkeypatch):
        def mock_search_site(*args):
            return ['found this', 'and that']
        def mock_search_site_none(*args):
            return []
        def mock_searchdict2list(*args):
            return args[0]
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()

        monkeypatch.setattr(rhfn, 'search_site', mock_search_site)
        monkeypatch.setattr(rhfn, 'searchdict2list', mock_searchdict2list)
        assert testsubj.search('found', '') == ('de onderstaande regels/regeldelen zijn gevonden:',
                                                ['found this', 'and that'])
        assert testsubj.search('found', 'replaced') == ('de onderstaande regels/regeldelen zijn '
                                                        'vervangen:', ['found this', 'and that'])

        monkeypatch.setattr(rhfn, 'search_site', mock_search_site_none)
        testsubj.search('not found', '') == ('search phrase not found', {})
        testsubj.search('not found', 'replaced') == ('nothing found, no replacements', {})

    def test_copysearch(self, monkeypatch):
        path = pathlib.Path('/tmp/copysearch')
        def mock_get_copysearch_filepath(*args):
            return path
        def mock_get_progress_line_values(*args):
            return ['x', 'y', 'z', 'q']
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn, 'get_copysearch_filepath', mock_get_copysearch_filepath)
        searchdata = ('search_for', 'replace_with',
                      [('text1', '1', 'result1'), ('text2', '2', 'result2')])
        assert testsubj.copysearch(searchdata) == 'Search results copied to /tmp/copysearch'
        assert path.read_text() == ('searched for `search_for`and replaced with `replace_with`\n\n'
                                    'text1 line 1: result1\ntext2 line 2: result2\n')

    def test_check(self, monkeypatch):
        def mock_check_directive_selectors(*args):
            return []
        def mock_check_directive_selectors_missing(*args):
            return ['x', 'y']
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()

        monkeypatch.setattr(rhfn, 'check_directive_selectors', mock_check_directive_selectors)
        assert testsubj.check() == 'No issues detected'
        monkeypatch.setattr(rhfn, 'check_directive_selectors',
                            mock_check_directive_selectors_missing)
        assert testsubj.check() == ('an id or class used in the directives was not found'
                                    ' in the linked css files: x, y')

    def test_overview(self, monkeypatch):
        def mock_build_progress_list(*args):
            return 'called build_progress_list'
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn, 'build_progress_list', mock_build_progress_list)
        assert testsubj.overview() == 'called build_progress_list'

    def test_copystand(self, monkeypatch):
        path = pathlib.Path('/tmp/copystand')
        def mock_get_copystand_filepath(*args):
            return path
        def mock_get_progress_line_values(*args):
            return ['x', 'y', 'z', 'q']
        monkeypatch.setattr(rhfn, 'default_site', mock_default_site)
        testsubj = rhfn.R2hState()
        monkeypatch.setattr(rhfn, 'get_copystand_filepath', mock_get_copystand_filepath)
        monkeypatch.setattr(rhfn, 'get_progress_line_values', mock_get_progress_line_values)
        assert testsubj.copystand(['x']) == 'Overzicht geëxporteerd naar /tmp/copystand'
        assert path.read_text() == 'x;y;z;q\n'
