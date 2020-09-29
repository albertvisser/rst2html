import os
import pathlib
import datetime

import pytest
import rst2html as r2h

def format_output(monkeypatch):
    def mock_list_files(*args):
        if args[3] == 'src':
            return ['x.src', 'y.src']
        elif args[3] == 'dest':
            return ['x.html', 'y.html']
    def mock_get_text(*args):
        pass
    def mock_list_confs(*args):
        pass
    def mock_conf_get(*args):
        pass
    raw_data = r2h.TEMPLATE.read_text()
    assert r2h.format_output('', '', '', '', '', '', state_class) == ''


def test_format_progress_list(capsys):
    raw_data = (r2h.HERE / 'stand.html').read_text()
    begin = raw_data.split('{%', 1)[0]
    end = raw_data.rsplit('%}', 1)[1]
    assert r2h.format_progress_list([]) == begin + end
    dates = datetime.datetime.min, datetime.datetime.max, datetime.datetime.max
    data = [('q', 'r', 2, dates)]
    middle = '\n'.join(('',
                        '            <tr>',
                        '                <td>q/r</td>',
                        '                <td>n/a</td>',
                        '                <td>31-12-9999 23:59:59</td>',
                        '                <td><strong>31-12-9999 23:59:59</strong></td>',
                        '            </tr>',
                        '            '))
    assert r2h.format_progress_list(data) == begin + middle + end


def resolve_images():
    assert r2h.resolve_images('', '', '',) == ''


def format_previewdata(monkeypatch):
    def mock_resolve_images(*args):
        return '...'
    assert r2h.format_previewdata(state_class, '', '', '', '') == ''


def format_search():
    raw_data = (r2h.HERE / 'search.html').read_text()
    assert r2h.format_search() == ''

class TestRst2Html:

    def setup_class(self):
        return r2h.Rst2Html()

    def test_init(self, monkeypatch, capsys):
        def mock_register_directives():
            print('called register_directives')
        monkeypatch.setattr(r2h.rhfn, 'register_directives', mock_register_directives)
        testsubj = r2h.Rst2Html()   # self.setup_class(monkeypatch)
        assert capsys.readouterr().out == 'called register_directives\n'
        assert type(getattr(testsubj, 'state', None)) == r2h.rhfn.R2hState

    def index(self, monkeypatch, capsys):
        def mock_register_directives():
            pass
        def mock_format_output(*args):
            return 'format_output for ' + ', '.join(['{}'.format(x) for x in args])
        monkeypatch.setattr(r2h.rhfn, 'register_directives', mock_register_directives)
        testsubj = r2h.Rst2Html()   # self.setup_class(monkeypatch)
        monkeypatch.setattr(r2h, 'format_output', mock_format_output)
        assert testsubj.index() == ''
