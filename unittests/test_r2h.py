import os
import pathlib
import datetime

import pytest
import app.rst2html as r2h


def test_load_template():
    name = 'rst2html.html'
    assert r2h.load_template(name) == (r2h.HERE / name).read_text()


def test_apply_lang(monkeypatch):
    def mock_get_text(*args):
        return 'xxxx'
    monkeypatch.setattr(r2h.rhfn, 'get_text', mock_get_text)
    state = r2h.Rst2Html().state
    assert r2h.apply_lang(['o _(q) _(q)', '', '_(q) o ', 'zzz'], state) == ('o xxxx xxxx\n\nxxxx'
                                                                            ' o \nzzz')


def test_format_output(monkeypatch):
    def mock_list_files(*args):
        if args[3] == 'src':
            return 'src'
        elif args[3] == 'dest':
            return 'html'
    def mock_load_template(*args):
        return 'template text:\n {} {} {} {} {} {} {} {} {} {}'
    def mock_apply_lang(*args):
        return ''.join(args[0])
    def mock_list_confs(*args):
        return 'confs'
    monkeypatch.setattr(r2h.rhfn, 'list_files', mock_list_files)
    monkeypatch.setattr(r2h, 'load_template', mock_load_template)
    monkeypatch.setattr(r2h, 'apply_lang', mock_apply_lang)
    monkeypatch.setattr(r2h.rhfn, 'list_confs', mock_list_confs)
    state = r2h.Rst2Html().state
    state.newfile = True
    state.loaded = ''
    state.conf = {'wid': 20, 'hig': 10}
    r2h.codemirror_stuff = ['cc' 'cc']
    r2h.scriptspec = '{}'
    r2h.scriptdict = {'rst': ('REsT',)}
    assert r2h.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: [] [] new mld data 20 10'
                                                        ' confs  ')

    state.newfile = False
    state.loaded = 'rst'
    state.conf['highlight'] = True
    assert r2h.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: src html new mld data'
                                                        ' 20 10 confs rst ccccREsT')


def test_format_progress_list(capsys):
    raw_data = (r2h.HERE / 'stand.html').read_text()
    begin, rest = raw_data.split('{% if data %}', 1)
    thead, rest = rest.split('{% for row in data %}', 1)
    data_stuff, rest = rest.split('{% endfor %}', 1)
    tfoot, rest = rest.split('{% else %}', 1)
    no_data, end = rest.split('{% endif %}', 1)
    assert r2h.format_progress_list([]) == begin + no_data + end
    dates = datetime.datetime.min, datetime.datetime.max, datetime.datetime.max
    data = [('q', 'r', 2, dates)]
    middle = data_stuff.replace('{row.0}', 'q/r').replace('{row.1}', 'n/a').replace('{row.2}',
            '31-12-9999 23:59:59').replace('{row.3}', '<strong>31-12-9999 23:59:59</strong>')
    assert r2h.format_progress_list(data) == begin + thead + middle + tfoot + end


def test_resolve_images():
    assert r2h.resolve_images('', '', '') == ''
    assert r2h.resolve_images('x', 'y', 'z') == 'x'
    assert r2h.resolve_images(' <img', 'url', 'loc') == ' <imurl/loc/g'
    assert r2h.resolve_images(' <img src="x">', 'url/', 'loc') == ' <img src="url/loc/x">'
    assert r2h.resolve_images(' <img src="x">', 'url', 'loc/') == ' <img src="url/loc/x">'
    assert r2h.resolve_images(' <img src="httpx">', '', '') == ' <img src="httpx">'
    # import pdb; pdb.set_trace()
    # assert r2h.resolve_images(' <img src="/xyz"> <img src="/abc"> ',
    #                           '', '') == ' <img src="/xyz"> <img src="/abc"> '
    assert r2h.resolve_images(' <img src="/xyz"> <img src="/abc"> ',
                              'url', '') == ' <img src="url/xyz"> <img src="url/abc"> '
    assert r2h.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True) == ' <img src="x"> '
    assert r2h.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True, fname='y') == ' <img src="y/x"> '
    assert r2h.resolve_images(' <img src="x"> ', '', '',
                              'index') == ' <img src="x"> '
    assert r2h.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True, fname='index') == ' <img src="x"> '


def test_format_previewdata(monkeypatch):
    def mock_resolve_images(*args):
        return args[0]
    program = r2h.Rst2Html()
    r2h.previewbutton = '[{}]'
    assert r2h.format_previewdata(program.state, '<---',
                                  'x', 'y', 'z') == ('[/loady/?yfile=x&settings=z]<---')
    assert r2h.format_previewdata(program.state, '<body></body>',
                                  '', '', '') == ('<body>[/load/?file=&settings=]</body>')


def test_format_search(monkeypatch):
    def mock_load_template_1(*args):
        return ('The beginning {% if results %}x{% for row in data %}y{% endfor %}z'
                '{% endif %} **and**  the end')
    def mock_load_template_2(*args):
        return ('x{% if results %}y{% for row in data %}-{row.0}-{row.1}-{row.2}-'
                '{% endfor %}q{% endif %}r')
    monkeypatch.setattr(r2h, 'load_template', mock_load_template_1)
    assert r2h.format_search() == 'The beginning <strong>and</strong> the end'
    monkeypatch.setattr(r2h, 'load_template', mock_load_template_2)
    assert r2h.format_search([['1', '2', '3'], ['a', 'b', 'c']]) == ('xy-1-2-3--a-b-c-qr')


def mock_register_directives():
    print('called register_directives')


def mock_format_output(*args):
    return 'format_output for ' + ', '.join(['{}'.format(x) for x in args])


class TestRst2Html:
    def test_init(self, monkeypatch, capsys):
        monkeypatch.setattr(r2h.rhfn, 'register_directives', mock_register_directives)
        testsubj = r2h.Rst2Html()
        assert capsys.readouterr().out == 'called register_directives\n'
        assert type(getattr(testsubj, 'state', None)) == r2h.rhfn.R2hState

    def test_index(self, monkeypatch, capsys):
        def mock_index():
            print('called R2hState.index')
            return 'rst', 'html', 'new', 'mld', 'data', 'sett'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'index', mock_index)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.index() == ('format_output for rst, html, new, mld, data, sett,'
                                    ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.index\n'

    def test_loadconf(self, monkeypatch, capsys):
        def mock_loadconf(*args):
            print('called R2hState.loadconf')
            return 'mld', 'data', 'sett', 'new'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadconf', mock_loadconf)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.loadconf(rstfile='r', htmlfile='h') == ('format_output for r, h, new, mld,'
                                                                ' data, sett,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.loadconf\n'

    def test_saveconf(self, monkeypatch, capsys):
        def mock_saveconf(*args):
            print('called R2hState.saveconf')
            return 'mld', 'data', 'sett', 'new'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'saveconf', mock_saveconf)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.saveconf(rstfile='r', htmlfile='h') == ('format_output for r, h, new, mld,'
                                                                ' data, sett,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.saveconf\n'

    def test_loadxtra(self, monkeypatch, capsys):
        def mock_loadxtra(*args):
            print('called R2hState.loadxtra')
            return 'mld', 'data'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadxtra', mock_loadxtra)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.loadxtra(settings='s', rstfile='r',
                                 htmlfile='h', newfile='n') == ('format_output for r, h, n, mld,'
                                                                ' data, s,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.loadxtra\n'

    def test_savextra(self, monkeypatch, capsys):
        def mock_savextra(*args):
            print('called R2hState.savextra')
            return 'mld', 'data'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'savextra', mock_savextra)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.savextra(settings='s', rstfile='r',
                                 htmlfile='h', newfile='n') == ('format_output for r, h, n, mld,'
                                                                ' data, s,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.savextra\n'

    def test_loadrst(self, monkeypatch, capsys):
        def mock_loadrst(*args):
            print('called R2hState.loadrst')
            return 'mld', 'data', 'html', 'new'
        def mock_status(*args):
            print('called R2hState.status')
            return 'message'
        def mock_diffsrc(*args):
            print('called R2hState.diffsrc')
            return 'message', 'diff'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadrst', mock_loadrst)
        monkeypatch.setattr(testsubj.state, 'status', mock_status)
        monkeypatch.setattr(testsubj.state, 'diffsrc', mock_diffsrc)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.loadrst(settings='s', rstfile='r', htmlfile='h', newfile='n', rstdata='d',
                                l_action='status') == ('format_output for r, h, n, message,'
                                                       ' d, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.status\n'
        assert testsubj.loadrst(settings='s', rstfile='r', htmlfile='h', newfile='n', rstdata='d',
                                l_action='changes') == ('format_output for r, h, n, message,'
                                                       ' diff, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.diffsrc\n'
        assert testsubj.loadrst(settings='s', rstfile='r') == ('format_output for r, html, new,'
                                                                ' mld, data, s,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.loadrst\n'

    def test_saverst(self, monkeypatch, capsys):
        def mock_rename(*args):
            print('called R2hState.rename')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_revert(*args):
            print('called R2hState.revert')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_delete(*args):
            print('called R2hState.delete')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_saverst(*args):
            print('called R2hState.saverst')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'rename', mock_rename)
        monkeypatch.setattr(testsubj.state, 'revert', mock_revert)
        monkeypatch.setattr(testsubj.state, 'delete', mock_delete)
        monkeypatch.setattr(testsubj.state, 'saverst', mock_saverst)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='revert') == ('format_output for rstfile, htmlfile, newfile,'
                                                       ' mld, rstdata, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.revert\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='rename') == ('format_output for rstfile, htmlfile, newfile,'
                                                       ' mld, rstdata, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.rename\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='delete') == ('format_output for rstfile, htmlfile, newfile,'
                                                       ' mld, rstdata, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.delete\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='x') == ('format_output for rstfile, htmlfile, newfile,'
                                                  ' mld, rstdata, s, {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.saverst\n'

    def test_convert(self, monkeypatch, capsys):
        def mock_convert(*args):
            print('called R2hState.convert')
            return 'mld', 'data', 'fn'
        def mock_format_previewdata(*args):
            return 'called format_previewdata'
        def mock_convert_nomld(*args):
            print('called R2hState.convert_nomld')
            return '', 'data', 'fn'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'convert', mock_convert)
        monkeypatch.setattr(r2h, 'format_previewdata', mock_format_previewdata)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.convert(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                    ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.convert\n'
        monkeypatch.setattr(testsubj.state, 'convert', mock_convert_nomld)
        assert testsubj.convert(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('called format_previewdata')
        assert capsys.readouterr().out == 'called R2hState.convert_nomld\n'

    def test_saveall(self, monkeypatch, capsys):
        def mock_saveall(*args):
            print('called R2hState.saveall')
            return 'mld', 'rst', 'html', 'new'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'saveall', mock_saveall)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.saveall(settings='s', rstdata='r') == ('format_output for rst, html, new,'
                                                                ' mld, r, s,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.saveall\n'

    def test_loadhtml(self, monkeypatch, capsys):
        def mock_loadhtml(*args):
            print('called R2hState.loadhtml')
            return 'mld', 'data', 'rst', 'html'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadhtml', mock_loadhtml)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.loadhtml(settings='s', newfile='n') == ('format_output for rst, html, n,'
                                                                ' mld, data, s,'
                                                                ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.loadhtml\n'

    def test_showhtml(self, monkeypatch, capsys):
        def mock_showhtml(*args):
            print('called R2hState.showhtml')
            return 'mld', 'data', 'fn'
        def mock_format_previewdata(*args):
            return 'called format_previewdata'
        def mock_showhtml_nomld(*args):
            print('called R2hState.showhtml_nomld')
            return '', 'data', 'fn'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'showhtml', mock_showhtml)
        monkeypatch.setattr(r2h, 'format_previewdata', mock_format_previewdata)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.showhtml(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                    ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.showhtml\n'
        monkeypatch.setattr(testsubj.state, 'showhtml', mock_showhtml_nomld)
        assert testsubj.showhtml(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('called format_previewdata')
        assert capsys.readouterr().out == 'called R2hState.showhtml_nomld\n'

    def test_savehtml(self, monkeypatch, capsys):
        def mock_savehtml(*args):
            print('called R2hState.savehtml')
            return 'mld', 'data', 'new'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'savehtml', mock_savehtml)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.savehtml(settings='s', rstfile='r',
                                 htmlfile='h') == ('format_output for r, h, new, mld, data, s,'
                                                   ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.savehtml\n'

    def test_copytoroot(self, monkeypatch, capsys):
        def mock_copytoroot(*args):
            print('called R2hState.copytoroot')
            return 'mld'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'copytoroot', mock_copytoroot)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.copytoroot(settings='s', rstfile='r',
                                   htmlfile='h', newfile='n',
                                   rstdata='rst') == ('format_output for r, h, n, mld, rst, s,'
                                                      ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.copytoroot\n'

    def test_migdel(self, monkeypatch, capsys):
        def mock_propagate(*args):
            print('called R2hState.propagate_deletions')
            return 'mld'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'propagate_deletions', mock_propagate)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.migdel(settings='s', rstfile='r',
                               htmlfile='h', newfile='n',
                               rstdata='rst') == ('format_output for r, h, n, mld, rst, s,'
                                                  ' {}'.format(testsubj.state))
        assert capsys.readouterr().out == 'called R2hState.propagate_deletions\n'

    def test_makerefdoc(self, monkeypatch, capsys):
        def mock_makerefdoc(*args):
            return 'ok', 'rref', 'href', 'dref'
        def mock_makerefdoc_nok(*args):
            return ['nok']
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'makerefdoc', mock_makerefdoc)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.makerefdoc(settings='s', rstfile='r',
                                   htmlfile='h', newfile='n',
                                   rstdata='d') == ('format_output for rref, href, n, ok, dref,'
                                                    ' s, {}'.format(testsubj.state))
        monkeypatch.setattr(testsubj.state, 'makerefdoc', mock_makerefdoc_nok)
        assert testsubj.makerefdoc(settings='s', rstfile='r',
                                   htmlfile='h', newfile='n',
                                   rstdata='d') == ('format_output for r, h, n, nok, d,'
                                                    ' s, {}'.format(testsubj.state))

    def test_convert_all(self, monkeypatch, capsys):
        def mock_convert_all(*args, **kwargs):
            return 'mld', 'data'
        def mock_format_output_all(*args):
            return '<select name="regsubj"><option value="x"></select>'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'convert_all', mock_convert_all)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output_all)
        assert testsubj.convert_all(regsubj='x') == ('<select name="regsubj"><option'
                                                     ' selected="selected" value="x"></select>' )

    def test_find_screen(self, monkeypatch, capsys):
        def mock_format_search(*args):
            print('called R2hState.format_search')
            return 'mld'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(r2h, 'format_search', mock_format_search)
        assert testsubj.find_screen() == 'mld'

    def test_find_results(self, monkeypatch, capsys):
        def mock_search(*args):
            return 'mld', 'results for {} {} {} {} {}'
        def mock_search_not_found(*args):
            return 'search phrase not found', ''
        def mock_format_search(*args):
            return args[0] or '{4}'
        testsubj = r2h.Rst2Html()
        testsubj.state.settings = 's'
        monkeypatch.setattr(r2h, 'format_search', mock_format_search)
        monkeypatch.setattr(r2h, 'copybuttontext', 'b')
        monkeypatch.setattr(testsubj.state, 'search', mock_search_not_found)
        assert testsubj.find_results(search='f') == 'search phrase not found'
        monkeypatch.setattr(testsubj.state, 'search', mock_search)
        assert testsubj.find_results(search='f', replace='r') == 'results for s b f r mld'
        assert testsubj.find_results(search='', replace='r') == 'Please tell me what to search for'

    def test_copy_results(self, monkeypatch, capsys):
        def mock_copys(*args):
            return 'copied'
        def mock_format_search(*args):
            return 'results for {} {} {} {} {}'
        testsubj = r2h.Rst2Html()
        testsubj.state.settings = 's'
        testsubj.search_stuff = ('f', 'r', [('page1', '1', 'first s'), ('page2', '11', 'second s')])
        monkeypatch.setattr(testsubj.state, 'copysearch', mock_copys)
        monkeypatch.setattr(r2h, 'format_search', mock_format_search)
        monkeypatch.setattr(r2h, 'copybuttontext', 'b')
        assert testsubj.copysearch() == 'results for s b f r copied'

    def test_check(self, monkeypatch, capsys):
        def mock_check(*args):
            return 'mld'
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'check', mock_check)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.check(settings='s', rstfile='r',
                              htmlfile='h', newfile='n',
                              rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                  ' {}'.format(testsubj.state))

    def test_overview(self, monkeypatch, capsys):
        def mock_overview(*args):
            return 'overview data {} {}'
        def mock_format_progress_list(*args):
            return args[0]
        testsubj = r2h.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'overview', mock_overview)
        monkeypatch.setattr(r2h, 'format_progress_list', mock_format_progress_list)
        assert testsubj.overview(settings='s') == 'overview data s '
        assert testsubj.overviewdata == 'overview data {} {}'

    def test_copystand(self, monkeypatch, capsys):
        def mock_copystand(*args):
            return 'msg'
        def mock_format_progress_list(*args):
            return args[0]
        testsubj = r2h.Rst2Html()
        testsubj.state.sitename = 'testsite'
        testsubj.overviewdata = 'copystand data {} {}'
        monkeypatch.setattr(testsubj.state, 'copystand', mock_copystand)
        monkeypatch.setattr(r2h, 'format_progress_list', mock_format_progress_list)
        assert testsubj.copystand() == 'copystand data testsite msg'
