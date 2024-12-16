"""unittests for ./app/rst2html.py
"""
import datetime
import app.rst2html as testee


def test_load_template():
    """unittest for rst2html.load_template
    """
    name = 'rst2html.html'
    assert testee.load_template(name) == (testee.HERE / name).read_text()


def test_apply_lang(monkeypatch):
    """unittest for rst2html.apply_lang
    """
    def mock_get_text(*args):
        """stub
        """
        return 'xxxx'
    monkeypatch.setattr(testee.rhfn, 'get_text', mock_get_text)
    state = testee.Rst2Html().state
    assert testee.apply_lang(['o _(q) _(q)', '', '_(q) o ', 'zzz'], state) == ('o xxxx xxxx\n\nxxxx'
                                                                            ' o \nzzz')


def test_format_output(monkeypatch):
    """unittest for rst2html.format_output
    """
    def mock_list_files(*args):
        """stub
        """
        if args[3] == 'src':
            return 'src'
        # elif args[3] == 'dest':
        return 'html'
    def mock_load_template(*args):
        """stub
        """
        return ('template text:\n {rstnames} {htmlnames} {newname} {message} {content} {cols} {rows}'
                ' {settnames} {editor_addon} {spellcheck_button} {editor_loader}')
    def mock_apply_lang(*args):
        """stub
        """
        return ''.join(args[0])
    def mock_list_confs(*args):
        """stub
        """
        return 'confs'
    def mock_get_text(*args):
        """stub
        """
        return 'xxxx'
    monkeypatch.setattr(testee.rhfn, 'list_files', mock_list_files)
    monkeypatch.setattr(testee.rhfn, 'get_text', mock_get_text)
    monkeypatch.setattr(testee, 'load_template', mock_load_template)
    monkeypatch.setattr(testee, 'apply_lang', mock_apply_lang)
    monkeypatch.setattr(testee.rhfn, 'list_confs', mock_list_confs)
    monkeypatch.setattr(testee, 'load_editor', '{}')
    monkeypatch.setattr(testee, 'spellbuttontext', '{} {} {}')
    state = testee.Rst2Html().state
    state.newfile = True
    state.noformat = False
    state.loaded = ''
    state.conf = {'wid': 20, 'hig': 10}
    testee.codemirror_stuff = ['cc', 'cc']
    testee.scriptspec = '{}'
    testee.scriptdict = {'rst': ('REsT',), 'conf': ('conf',)}
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: [] [] new mld data 20 10'
                                                        ' confs   ')
    state.conf = {'wid': 20, 'hig': 10, 'highlight': True}
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: [] [] new mld data 20 10'
                                                        ' confs cccc xxxx spellcheck true ')

    state.newfile = False
    state.loaded = 'rst'
    state.conf['highlight'] = True
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: src html new mld data 20 10'
                                                        ' confs ccccREsT xxxx spellcheck true rst')

    state.newconf = True
    state.loaded = 'conf'
    state.conf['highlight'] = True
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: [] [] new mld data 20 10'
                                                        ' confs ccccconf xxxx spellcheck true conf')
    state.noformat = True
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: [] [] new mld data 20 10'
                                                        ' confs   code highlighting false ')
    state.newconf = False
    state.loaded = 'rst'
    assert testee.format_output('rst', 'html', 'new', 'mld',
                             'data', {1: 2}, state) == ('template text: src html new mld data 20 10'
                                                        ' confs   code highlighting false ')


def test_format_progress_list():
    """unittest for rst2html.format_progress_list
    """
    raw_data = (testee.HERE / 'stand.html').read_text()
    begin, rest = raw_data.split('{% if data %}', 1)
    thead, rest = rest.split('{% for row in data %}', 1)
    data_stuff, rest = rest.split('{% endfor %}', 1)
    tfoot, rest = rest.split('{% else %}', 1)
    no_data, end = rest.split('{% endif %}', 1)
    assert testee.format_progress_list([], 'html5') == begin + no_data + end
    dates = datetime.datetime.min, datetime.datetime.max, datetime.datetime.max
    data = [('q', 'r', 2, dates)]
    middle = data_stuff.replace('{row.0}', 'q/r').replace('{row.1}', 'n/a').replace('{row.2}',
            '31-12-9999 23:59:59').replace('{row.3}', '<strong>31-12-9999 23:59:59</strong>')
    assert testee.format_progress_list(data, 'html5') == begin + thead + middle + tfoot + end
    begin = begin.replace('main', 'div class="document"')
    end = end.replace('main', 'div')
    assert testee.format_progress_list(data, 'html4') == begin + thead + middle + tfoot + end


def test_resolve_images():
    """unittest for rst2html.resolve_images
    """
    assert testee.resolve_images('', '', '') == ''
    assert testee.resolve_images('x', 'y', 'z') == 'x'
    assert testee.resolve_images(' <img', 'url', 'loc') == ' <img'  # ' <imurl/loc/g'
    assert testee.resolve_images(' <img src="x">', 'url/', 'loc') == ' <img src="url/loc/x">'
    assert testee.resolve_images(' <img src="x">', 'url', 'loc/') == ' <img src="url/loc/x">'
    assert testee.resolve_images(' <img src="httpx">', '', '') == ' <img src="httpx">'
    assert testee.resolve_images(' <img src="httpx">', 'url', 'loc') == ' <img src="httpx">'
    assert testee.resolve_images(' <img src="x"> <img src="y">', 'url/', 'loc') == (
            ' <img src="url/loc/x"> <img src="url/loc/y">')
    assert testee.resolve_images(' <img src="x"> <img src="y">', 'url', 'loc/') == (
            ' <img src="url/loc/x"> <img src="url/loc/y">')
    assert testee.resolve_images(' <img src="httpx"> <img src="httpx">', '', '') == (
        ' <img src="httpx"> <img src="httpx">')
    assert testee.resolve_images(' <img src="httpx"> <img src="httpx">', 'url', 'loc') == (
        ' <img src="httpx"> <img src="httpx">')
    assert testee.resolve_images(' <img src="/xyz"> <img src="/abc"> ',
                              '', '') == ' <img src="/xyz"> <img src="/abc"> '
    assert testee.resolve_images(' <img src="/xyz"> <img src="/abc"> ',
                              'url', '') == ' <img src="url/xyz"> <img src="url/abc"> '
    assert testee.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True) == ' <img src="x"> '
    assert testee.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True, fname='y') == ' <img src="y/x"> '
    assert testee.resolve_images(' <img src="x"> ', '', '',
                              'index') == ' <img src="x"> '
    assert testee.resolve_images(' <img src="x"> ', '', '',
                              use_sef=True, fname='index') == ' <img src="x"> '


def test_format_previewdata():
    """unittest for rst2html.format_previewdata
    """
    program = testee.Rst2Html()
    testee.previewbutton = '[{}]'
    assert testee.format_previewdata(program.state, '<---',
                                  'x', 'y', 'z') == ('[/loady/?yfile=x&settings=z]<---')
    assert testee.format_previewdata(program.state, '<body></body>',
                                  '', '', '') == ('<body>[/load/?file=&settings=]</body>')


def test_format_search(monkeypatch):
    """unittest for rst2html.format_search
    """
    def mock_load_template_1(*args):
        """stub
        """
        return ('The beginning {% if results %}x{% for row in data %}y{% endfor %}z'
                '{% endif %} **and**  the end')
    def mock_load_template_2(*args):
        """stub
        """
        return ('x{% if results %}y{% for row in data %}-{row.0}-{row.1}-{row.2}-'
                '{% endfor %}q{% endif %}r')
    def mock_load_template_3(*args):
        """stub
        """
        return '<main>{% if results %}x{% for row in data %}y{% endfor %}z{% endif %}</main>'
    monkeypatch.setattr(testee, 'load_template', mock_load_template_1)
    assert testee.format_search([], 'html5') == 'The beginning <strong>and</strong> the end'
    monkeypatch.setattr(testee, 'load_template', mock_load_template_2)
    assert testee.format_search([['1', '2', '3'], ['a', 'b', 'c']], 'html5') == ('xy-1-2-3--a-b-c-qr')
    monkeypatch.setattr(testee, 'load_template', mock_load_template_3)
    assert testee.format_search([], 'html4') == '<div class="document"></div>'


def mock_register_directives():
    """stub for rst2html_functions.register_directives
    """
    print('called register_directives')


def mock_format_output(*args):
    """stub for rst2html.format_output (when used in views)
    """
    return 'format_output for ' + ', '.join([f'{x}' for x in args])


class TestRst2Html:
    """unittests for rst2html.Rst2Html
    """
    def test_init(self, monkeypatch, capsys):
        """unittest for Rst2Html.init
        """
        monkeypatch.setattr(testee.rhfn, 'register_directives', mock_register_directives)
        testsubj = testee.Rst2Html()
        assert capsys.readouterr().out == 'called register_directives\n'
        # assert type(getattr(testsubj, 'state', None)) == testee.rhfn.R2hState
        assert isinstance(getattr(testsubj, 'state', None), testee.rhfn.R2hState)

    def test_index(self, monkeypatch, capsys):
        """unittest for Rst2Html.index
        """
        def mock_index():
            """stub
            """
            print('called R2hState.index')
            return 'rst', 'html', 'new', 'mld', 'data', 'sett'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'index', mock_index)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.index() == ('format_output for rst, html, new, mld, data, sett,'
                                    f' {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.index\n'

    def test_loadconf(self, monkeypatch, capsys):
        """unittest for Rst2Html.loadconf
        """
        def mock_loadconf(*args):
            """stub
            """
            print('called R2hState.loadconf')
            return 'mld', 'data', 'sett', 'new'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadconf', mock_loadconf)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.loadconf(rstfile='r', htmlfile='h') == ('format_output for r, h, new, mld,'
                                                                f' data, sett, {testsubj.state}')
        assert not testsubj.state.noformat
        assert capsys.readouterr().out == 'called R2hState.loadconf\n'

    def test_saveconf(self, monkeypatch, capsys):
        """unittest for Rst2Html.saveconf
        """
        def mock_saveconf(*args):
            """stub
            """
            print('called R2hState.saveconf')
            return 'mld', 'data', 'sett', 'new'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'saveconf', mock_saveconf)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.saveconf(rstfile='r', htmlfile='h') == ('format_output for r, h, new, mld,'
                                                                f' data, sett, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.saveconf\n'

    def test_loadrst(self, monkeypatch, capsys):
        """unittest for Rst2Html.loadrst
        """
        def mock_loadrst(*args):
            """stub
            """
            print('called R2hState.loadrst')
            return 'mld', 'data', 'html', 'new'
        def mock_status(*args):
            """stub
            """
            print('called R2hState.status')
            return 'message'
        def mock_diffsrc(*args):
            """stub
            """
            print('called R2hState.diffsrc')
            return 'message', 'diff'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadrst', mock_loadrst)
        monkeypatch.setattr(testsubj.state, 'status', mock_status)
        monkeypatch.setattr(testsubj.state, 'diffsrc', mock_diffsrc)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.loadrst(settings='s', rstfile='r', htmlfile='h', newfile='n', rstdata='d',
                                l_action='status') == ('format_output for r, h, n, message,'
                                                       f' d, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.status\n'
        assert testsubj.loadrst(settings='s', rstfile='r', htmlfile='h', newfile='n', rstdata='d',
                                l_action='changes') == ('format_output for r, h, n, message,'
                                                       f' diff, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.diffsrc\n'
        assert testsubj.loadrst(settings='s', rstfile='r') == ('format_output for r, html, new,'
                                                               f' mld, data, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.loadrst\n'
        assert testsubj.loadrst(settings='s', rstfile='r', highlighted='false') == (
                f'format_output for r, html, new, mld, data, s, {testsubj.state}')
        assert testsubj.state.noformat
        assert capsys.readouterr().out == 'called R2hState.loadrst\n'
        assert testsubj.loadrst(settings='s', rstfile='r', highlighted='true') == (
                f'format_output for r, html, new, mld, data, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.loadrst\n'
        assert not testsubj.state.noformat

    def test_saverst(self, monkeypatch, capsys):
        """unittest for Rst2Html.saverst
        """
        def mock_rename(*args):
            """stub
            """
            print('called R2hState.rename')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_revert(*args):
            """stub
            """
            print('called R2hState.revert')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_delete(*args):
            """stub
            """
            print('called R2hState.delete')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        def mock_saverst(*args):
            """stub
            """
            print('called R2hState.saverst')
            return ('mld', 'rstfile', 'htmlfile', 'newfile', 'rstdata')
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'rename', mock_rename)
        monkeypatch.setattr(testsubj.state, 'revert', mock_revert)
        monkeypatch.setattr(testsubj.state, 'delete', mock_delete)
        monkeypatch.setattr(testsubj.state, 'saverst', mock_saverst)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='revert') == ('format_output for rstfile, htmlfile, newfile,'
                                                       f' mld, rstdata, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.revert\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='rename') == ('format_output for rstfile, htmlfile, newfile,'
                                                       f' mld, rstdata, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.rename\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='delete') == ('format_output for rstfile, htmlfile, newfile,'
                                                       f' mld, rstdata, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.delete\n'
        assert testsubj.saverst(settings='s', rstfile='r', newfile='n', rstdata='d',
                                s_action='x') == ('format_output for rstfile, htmlfile, newfile,'
                                                  f' mld, rstdata, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.saverst\n'

    def test_convert(self, monkeypatch, capsys):
        """unittest for Rst2Html.convert
        """
        def mock_convert(*args):
            """stub
            """
            print('called R2hState.convert')
            return 'mld', 'data', 'fn'
        def mock_format_previewdata(*args):
            """stub
            """
            return 'called format_previewdata'
        def mock_convert_nomld(*args):
            """stub
            """
            print('called R2hState.convert_nomld')
            return '', 'data', 'fn'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'convert', mock_convert)
        monkeypatch.setattr(testee, 'format_previewdata', mock_format_previewdata)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.convert(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                    f' {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.convert\n'
        monkeypatch.setattr(testsubj.state, 'convert', mock_convert_nomld)
        assert testsubj.convert(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('called format_previewdata')
        assert capsys.readouterr().out == 'called R2hState.convert_nomld\n'

    def test_saveall(self, monkeypatch, capsys):
        """unittest for Rst2Html.saveall
        """
        def mock_saveall(*args):
            """stub
            """
            print('called R2hState.saveall')
            return 'mld', 'rst', 'html', 'new'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'saveall', mock_saveall)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.saveall(settings='s', rstdata='r') == ('format_output for rst, html, new,'
                                                               f' mld, r, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.saveall\n'

    def test_loadhtml(self, monkeypatch, capsys):
        """unittest for Rst2Html.loadhtml
        """
        def mock_loadhtml(*args):
            """stub
            """
            print('called R2hState.loadhtml')
            return 'mld', 'data', 'rst', 'html'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'loadhtml', mock_loadhtml)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.loadhtml(settings='s', newfile='n') == ('format_output for rst, html, n,'
                                                                f' mld, data, s, {testsubj.state}')
        assert not testsubj.state.noformat
        assert capsys.readouterr().out == 'called R2hState.loadhtml\n'

    def test_showhtml(self, monkeypatch, capsys):
        """unittest for Rst2Html.showhtml
        """
        def mock_showhtml(*args):
            """stub
            """
            print('called R2hState.showhtml')
            return 'mld', 'data', 'fn'
        def mock_format_previewdata(*args):
            """stub
            """
            return 'called format_previewdata'
        def mock_showhtml_nomld(*args):
            """stub
            """
            print('called R2hState.showhtml_nomld')
            return '', 'data', 'fn'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'showhtml', mock_showhtml)
        monkeypatch.setattr(testee, 'format_previewdata', mock_format_previewdata)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.showhtml(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                    f' {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.showhtml\n'
        monkeypatch.setattr(testsubj.state, 'showhtml', mock_showhtml_nomld)
        assert testsubj.showhtml(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                rstdata='data') == ('called format_previewdata')
        assert capsys.readouterr().out == 'called R2hState.showhtml_nomld\n'

    def test_savehtml(self, monkeypatch, capsys):
        """unittest for Rst2Html.savehtml
        """
        def mock_savehtml(*args):
            """stub
            """
            print('called R2hState.savehtml')
            return 'mld', 'data', 'new'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'savehtml', mock_savehtml)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.savehtml(settings='s', rstfile='r', htmlfile='h') == (
                f'format_output for r, h, new, mld, data, s, {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.savehtml\n'

    def test_copytoroot(self, monkeypatch, capsys):
        """unittest for Rst2Html.copytoroot
        """
        def mock_copytoroot(*args):
            """stub
            """
            print('called R2hState.copytoroot')
            return 'mld'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'copytoroot', mock_copytoroot)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.copytoroot(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                   rstdata='rst') == ('format_output for r, h, n, mld, rst, s,'
                                                      f' {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.copytoroot\n'

    def test_migdel(self, monkeypatch, capsys):
        """unittest for Rst2Html.migdel
        """
        def mock_propagate(*args):
            """stub
            """
            print('called R2hState.propagate_deletions')
            return 'mld'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'propagate_deletions', mock_propagate)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.migdel(settings='s', rstfile='r', htmlfile='h', newfile='n',
                               rstdata='rst') == ('format_output for r, h, n, mld, rst, s,'
                                                  f' {testsubj.state}')
        assert capsys.readouterr().out == 'called R2hState.propagate_deletions\n'

    def test_makerefdoc(self, monkeypatch):
        """unittest for Rst2Html.makerefdoc
        """
        def mock_makerefdoc(*args):
            """stub
            """
            return 'ok', 'rref', 'href', 'dref'
        def mock_makerefdoc_nok(*args):
            """stub
            """
            return ['nok']
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'makerefdoc', mock_makerefdoc)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.makerefdoc(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                   rstdata='d') == ('format_output for rref, href, n, ok, dref,'
                                                    f' s, {testsubj.state}')
        monkeypatch.setattr(testsubj.state, 'makerefdoc', mock_makerefdoc_nok)
        assert testsubj.makerefdoc(settings='s', rstfile='r', htmlfile='h', newfile='n',
                                   rstdata='d') == ('format_output for r, h, n, nok, d,'
                                                    f' s, {testsubj.state}')

    def test_convert_all(self, monkeypatch):
        """unittest for Rst2Html.convert_all
        """
        def mock_convert_all(*args, **kwargs):
            """stub
            """
            return 'mld', 'data'
        def mock_format_output_all(*args):
            """stub
            """
            return '<select name="regsubj"><option value="x"></select>'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'convert_all', mock_convert_all)
        monkeypatch.setattr(testee, 'format_output', mock_format_output_all)
        assert testsubj.convert_all(regsubj='x') == ('<select name="regsubj"><option'
                                                     ' selected="selected" value="x"></select>')

    def test_find_screen(self, monkeypatch):
        """unittest for Rst2Html.find_screen
        """
        def mock_format_search(*args):
            """stub
            """
            print('called R2hState.format_search')
            return 'mld'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testee, 'format_search', mock_format_search)
        assert testsubj.find_screen() == 'mld'

    def test_find_results(self, monkeypatch):
        """unittest for Rst2Html.find_results
        """
        def mock_search(*args):
            """stub
            """
            return 'mld', 'results for {sitename} {extrabutton} {search} {replace} {message}'
        def mock_search_not_found(*args):
            """stub
            """
            return 'search phrase not found', ''
        def mock_format_search(*args):
            """stub
            """
            return args[0] or '{message}'
        testsubj = testee.Rst2Html()
        testsubj.state.settings = 's'
        monkeypatch.setattr(testee, 'format_search', mock_format_search)
        monkeypatch.setattr(testee, 'copybuttontext', 'b')
        monkeypatch.setattr(testsubj.state, 'search', mock_search_not_found)
        assert testsubj.find_results(search='f') == 'search phrase not found'
        monkeypatch.setattr(testsubj.state, 'search', mock_search)
        assert testsubj.find_results(search='f', replace='r') == 'results for s b f r mld'
        assert testsubj.find_results(search='', replace='r') == 'Please tell me what to search for'

    def test_copy_results(self, monkeypatch):
        """unittest for Rst2Html.copy_results
        """
        def mock_copys(*args):
            """stub
            """
            return 'copied'
        def mock_format_search(*args):
            """stub
            """
            return 'results for {sitename} {extrabutton} {search} {replace} {message}'
        testsubj = testee.Rst2Html()
        testsubj.state.settings = 's'
        testsubj.search_stuff = ('f', 'r', [('page1', '1', 'first s'), ('page2', '11', 'second s')])
        monkeypatch.setattr(testsubj.state, 'copysearch', mock_copys)
        monkeypatch.setattr(testee, 'format_search', mock_format_search)
        monkeypatch.setattr(testee, 'copybuttontext', 'b')
        assert testsubj.copysearch() == 'results for s b f r copied'

    def test_check(self, monkeypatch):
        """unittest for Rst2Html.check
        """
        def mock_check(*args):
            """stub
            """
            return 'mld'
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'check', mock_check)
        monkeypatch.setattr(testee, 'format_output', mock_format_output)
        assert testsubj.check(settings='s', rstfile='r', htmlfile='h', newfile='n',
                              rstdata='data') == ('format_output for r, h, n, mld, data, s,'
                                                  f' {testsubj.state}')

    def test_overview(self, monkeypatch):
        """unittest for Rst2Html.overview
        """
        def mock_overview(*args):
            """stub
            """
            return 'overview data {sitename} {message}'
        def mock_format_progress_list(*args):
            """stub
            """
            return args[0]
        testsubj = testee.Rst2Html()
        monkeypatch.setattr(testsubj.state, 'overview', mock_overview)
        monkeypatch.setattr(testee, 'format_progress_list', mock_format_progress_list)
        assert testsubj.overview(settings='s') == 'overview data s '
        assert testsubj.overviewdata == 'overview data {sitename} {message}'

    def test_copystand(self, monkeypatch):
        """unittest for Rst2Html.copystand
        """
        def mock_copystand(*args):
            """stub
            """
            return 'msg'
        def mock_format_progress_list(*args):
            """stub
            """
            return args[0]
        testsubj = testee.Rst2Html()
        testsubj.state.sitename = 'testsite'
        testsubj.overviewdata = 'copystand data {sitename} {message}'
        monkeypatch.setattr(testsubj.state, 'copystand', mock_copystand)
        monkeypatch.setattr(testee, 'format_progress_list', mock_format_progress_list)
        assert testsubj.copystand() == 'copystand data testsite msg'
