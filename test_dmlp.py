import datetime
import pytest
import docs2pg as dmlp

# class DbWrapper
# r. 25:      def __init__(self, f):
#                 pass
# r. 28:      def __call__(self, *args, **kwargs):
#                 pass
# module level code
# r. 36:  def wrapit(f):
#             pass
# function wrapit
# r. 39:      def wrapping(*args, **kwargs):
#                 pass


def test_is_equal():
    assert dmlp._is_equal([1], 1)
    assert not dmlp._is_equal([0], 1)
    with pytest.raises(TypeError):
        dmlp._is_equal(1, 1)


class MockDatetime:
    def utcnow(*args):
        return 'now'


class MockConn:
    def cursor(self, *args, **kwargs):
        return MockCursor()

    def commit(self, *args, **kwargs):
        print('called commit() on connection')


class MockCursor:
    def __iter__(self):
        pass

    def execute(self, *args):
        print('execute SQL: `{}`'.format(args[0]))
        if len(args) > 1:
            print('  with:', ', '.join(['`{}`'.format(x) for x in args[1]]))

    def executemany(self, *args):
        print('execute SQL: `{}`'.format(args[0]))
        if len(args) > 1:
            print('  with:', ', '.join(['`{}`'.format(x) for x in args[1]]))

    def commit(self, *args, **kwargs):
        print('called commit() on cursor')

    def close(self, *args, **kwargs):
        print('called close()')

    def fetchone(self, *args, **kwargs):
        pass

    def fetchall(self, *args, **kwargs):
        pass


class TestNonApiFunctions:
    def test_get_site_id(self, monkeypatch, capsys):
        def mock_fetchone(self, *args):
            return (99,)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert dmlp._get_site_id('site_name') == 99
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id from sites where sitename = %s;`\n',
            '  with: `site_name`\n',
            'called close()\n'))

    def test_get_dir_id(self, monkeypatch, capsys):
        def mock_fetchone(self, *args):
            return ('dir_id',)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert dmlp._get_dir_id('site_id', 'dir_id') == 'dir_id'
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id from directories where site_id = %s and dirname = %s;`\n',
            '  with: `site_id`, `dir_id`\n',
            'called close()\n'))

    def test_get_all_dir_ids(self, monkeypatch, capsys):
        def mock_fetchall(self, *args):
            return (('dirid01',), ('dirid02',))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        assert dmlp._get_all_dir_ids('site_id') == ['dirid01', 'dirid02']
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id from directories where site_id = %s;`\n',
            '  with: `site_id`\n',
            'called close()\n'))

    def test_get_docs_in_dir(self, monkeypatch, capsys):
        def mock_fetchall(self, *args):
            return (('docname_01',), ('docname_02',))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        assert dmlp._get_docs_in_dir('dir_id') == ['docname_01', 'docname_02']
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select docname from doc_stats where dir_id = %s;`\n',
            '  with: `dir_id`\n',
            'called close()\n'))

    def test_get_doc_ids(self, monkeypatch, capsys):
        def mock_fetchone(self, *args):
            return {'id': 1, 'source_docid': 2, 'target_docid': 3}
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {})
        assert dmlp._get_doc_ids('dir_id', 'docname') == (None, None, None)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, source_docid, target_docid from doc_stats'
            ' where dir_id = %s and docname = %s;`\n',
            '  with: `dir_id`, `docname`\n',
            'called close()\n'))
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert dmlp._get_doc_ids('dir_id', 'docname') == (1, 2, 3)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, source_docid, target_docid from doc_stats'
            ' where dir_id = %s and docname = %s;`\n',
            '  with: `dir_id`, `docname`\n',
            'called close()\n'))

    def test_get_doc_text(self, monkeypatch, capsys):
        def mock_fetchone(self, *args):
            return ('some_text',)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {})
        assert dmlp._get_doc_text('doc_id') == (None, None, None)
        assert capsys.readouterr().out == ''.join((
             'execute SQL: `select currtext from documents where id = %s;`\n',
             '  with: `doc_id`\n',
             'called close()\n'))
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert dmlp._get_doc_text('doc_id') == 'some_text'
        assert capsys.readouterr().out == ''.join((
             'execute SQL: `select currtext from documents where id = %s;`\n',
             '  with: `doc_id`\n',
             'called close()\n'))

    def test_get_settings(self, monkeypatch, capsys):
        def mock_iter(self):
            return (x for x in [{'settname': 'sett1', 'settval': 'val1'},
                                {'settname': 'sett2', 'settval': 'val2'}])
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        assert dmlp._get_settings('site_id') == {'sett1': 'val1', 'sett2': 'val2'}
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select settname, settval from site_settings where site_id = %s`\n',
            '  with: `site_id`\n',
            'called close()\n'))

    def test_add_doc(self, monkeypatch, capsys):
        def mock_fetchone(self, *args):
            return ('some_id',)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ('some_id',))
        assert dmlp._add_doc() == 'some_id'
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `insert into documents (currtext, previous) values (%s, %s)'
            ' returning id`\n',
            '  with: ``, ``\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_get_stats(self, monkeypatch, capsys):
        assert dmlp._get_stats(('docinfo', '', 0)) == dmlp.Stats('docinfo', datetime.datetime.min,
                datetime.datetime.min)


class TestTestApi:
    def test_clear_db(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.clear_db()
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `truncate table sites;`\n',
            'execute SQL: `truncate table site_settings;`\n',
            'execute SQL: `truncate table directories;`\n',
            'execute SQL: `truncate table doc_stats;`\n',
            'execute SQL: `truncate table documents;`\n',
            'execute SQL: `truncate table templates;`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_read_db(self, monkeypatch, capsys):
        def mock_fetchall(self, *args):
            nonlocal counter
            counter += 1
            if counter == 1:
                result = [{'sitename': 'a_site', 'id': 1}, {'sitename': 'another', 'id': 2}]
            elif counter == (2, 4):
                result = [('sett1', 'value1'), ('sett2', 'value2')]
            elif counter == 3:
                result = [{'dirname': '/', 'id': 1}]
            elif counter == 5:
                result = [{'dirname': '/', 'id': 2}, {'dirname': 'otherdir', 'id': 3}]
            else:
                result = []
            return result
        def mock_iter(self, *args):
            return (x for x in [{'docname': 'doc1', 'id': 'id1'},
                                {'docname': 'doc2', 'id': 'id2'}])
        counter = 0
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.read_db() == [{'name': 'a_site', 'settings': {},
                                   'docs': [[{'docname': 'doc1', 'id': 'id1', 'dirname': '/'},
                                             {'docname': 'doc2', 'id': 'id2', 'dirname': '/'}]]},
                                  {'name': 'another', 'settings': {},
                                   'docs': [[{'docname': 'doc1', 'id': 'id1', 'dirname': '/'},
                                             {'docname': 'doc2', 'id': 'id2', 'dirname': '/'}],
                                            [{'docname': 'doc1', 'id': 'id1',
                                              'dirname': 'otherdir'},
                                             {'docname': 'doc2', 'id': 'id2',
                                              'dirname': 'otherdir'}]]}]

        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select sitename, id from sites order by sitename;`\n',
            'execute SQL: `select settname, settval from site_settings order by settname'
            ' where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `select dirname, id from directories order by dirname'
            ' where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `select * from doc_stats order by docname where dir_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `select settname, settval from site_settings order by settname'
            ' where site_id = %s;`\n',
            '  with: `2`\n',
            'execute SQL: `select dirname, id from directories order by dirname'
            ' where site_id = %s;`\n',
            '  with: `2`\n',
            'execute SQL: `select * from doc_stats order by docname where dir_id = %s;`\n',
            '  with: `2`\n',
            'execute SQL: `select * from doc_stats order by docname where dir_id = %s;`\n',
            '  with: `3`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_list_site_data(self, monkeypatch, capsys):
        counter = 0
        def mock_iter(*args):
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'id': 2, 'dirname': '/'}, {'id': 3, 'dirname': 'subdir'}])
            elif counter == 2:
                return (x for x in [
                    {'docname': 'doc1', 'dir_id': 2, 'source_docid': 4, 'source_updated': 4,
                        'source_deleted': False, 'target_docid': 5, 'target_updated': 5,
                        'target_deleted': False, 'mirror_updated': 6},
                    {'docname': 'doc0', 'dir_id': 2, 'source_docid': None, 'source_updated': None,
                        'source_deleted': None, 'target_docid': None, 'target_updated': None,
                        'target_deleted': None, 'mirror_updated': None},
                    {'docname': 'doc2', 'dir_id': 3, 'source_docid': 6, 'source_updated': 6,
                        'source_deleted': True, 'target_docid': 7, 'target_updated': 7,
                        'target_deleted': True, 'mirror_updated': 8}])
            elif counter == 3:
                return (x for x in [{'id': 4, 'currtext': '/doc1 src text', 'previous': ''},
                                    {'id': 5, 'currtext': '/doc1 dest text', 'previous': 'old txt'},
                                    {'id': 6, 'currtext': 'subdir/doc2 src', 'previous': 'old'},
                                    {'id': 7, 'currtext': 'subdir/doc2 dest', 'previous': ''}])
            elif counter == 4:
                return (x for x in [{'name': 'tpl1', 'text': 'text tpl1'},
                                    {'name': 'tpl2', 'text': 'text tpl2'}])

        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.list_site_data('testsite')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 1)
        monkeypatch.setattr(dmlp, '_get_settings', lambda x: {'sett1': 'val1', 'sett2': 'val2'})
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        # import pdb; pdb.set_trace()
        assert dmlp.list_site_data('sitename') == ({ '_id': 1, 'name': 'sitename',
            'settings': {'sett1': 'val1', 'sett2': 'val2'},
            'docs': {'/': {'doc0': {},
                           'doc1': {'src': {'docid': 4, 'updated': 4, 'deleted': False},
                                    'dest': {'docid': 5, 'updated': 5, 'deleted': False},
                                    'mirror': {'updated': 5}}},
            'subdir': {'doc2': {'src': {'docid': 6, 'updated': 6, 'deleted': True},
                                'dest': {'docid': 7, 'updated': 7, 'deleted': True},
                                'mirror': {'updated': 7}}}}}, [
            {'_id': ('doc1', 'dest'), 'current': '/doc1 dest text', 'previous': 'old txt'},
            {'_id': ('doc1', 'src'), 'current': '/doc1 src text', 'previous': ''},
            {'_id': ('subdir/doc2', 'dest'), 'current': 'subdir/doc2 dest', 'previous': ''},
            {'_id': ('subdir/doc2', 'src'), 'current': 'subdir/doc2 src', 'previous': 'old'},
            {'_id': ('tpl1',), 'template contents': 'text tpl1'},
            {'_id': ('tpl2',), 'template contents': 'text tpl2'} ])
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, dirname from directories where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `select docname, source_docid, source_updated, source_deleted,'
            ' target_docid, target_updated, target_deleted, mirror_updated, dir_id'
            ' from doc_stats where dir_id = any(%s);`\n',
            '  with: `[2, 3]`\n',
            'execute SQL: `select id, currtext, previous from documents where id = any(%s)`\n',
            '  with: `[4, 5, None, 6, 7]`\n',
            'execute SQL: `select name, text from templates where site_id = %s;`\n',
            '  with: `1`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_clear_site_data(self, monkeypatch, capsys):
        def mock_rmtree_err(*args):
            print('called rmtree()')
            raise FileNotFoundError
        def mock_rmtree_ok(*args):
            print('called rmtree() with arg `{}`'.format(args[0]))
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: False)
        dmlp.clear_site_data('site_name')
        assert capsys.readouterr().out == ''

        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(dmlp.shutil, 'rmtree', mock_rmtree_err)
        dmlp.clear_site_data('site_name')
        assert capsys.readouterr().out == 'called rmtree()\n'

        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 1)
        monkeypatch.setattr(dmlp, '_get_all_dir_ids', lambda x: [2, 3])
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in [
            {'source_docid': 4, 'target_docid': 7},
            {'source_docid': 5, 'target_docid': 8},
            {'source_docid': 6, 'target_docid': 9}]))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.shutil, 'rmtree', mock_rmtree_ok)
        dmlp.clear_site_data('site_name')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select source_docid, target_docid from doc_stats'
            ' where dir_id = any(%s);`\n',
            '  with: `[2, 3]`\n',
            'execute SQL: `delete from documents where id = any(%s);`\n',
            '  with: `[4, 7, 5, 8, 6, 9]`\n',
            'execute SQL: `delete from doc_stats where dir_id = any(%s);`\n',
            '  with: `[2, 3]`\n',
            'execute SQL: `delete from templates where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `delete from directories where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `delete from site_settings where site_id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `delete from sites where id = %s;`\n',
            '  with: `1`\n',
            'called commit() on connection\n',
            # 'called close()\n'
            'called rmtree() with arg `{}`\n'.format(dmlp.WEBROOT / 'site_name')))


class TestSiteLevel:
    def test_list_sites(self, monkeypatch, capsys):
        def mock_fetchall(self, *args):
            return [('site1',), ('site2',)]
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        # monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.list_sites() == ['site1', 'site2']
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select sitename from sites;`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_create_new_site(self, monkeypatch, capsys):
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir() for `{}`'.format(self))
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: False)
        with pytest.raises(FileExistsError):
            dmlp.create_new_site('site_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: True)
        with pytest.raises(FileExistsError):
            dmlp.create_new_site('site_name')
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ('q',))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.pathlib.Path, 'mkdir', mock_mkdir)
        dmlp.create_new_site('site_name')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `insert into sites (sitename) values (%s) returning id;`\n',
            '  with: `site_name`\n',
            'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)`\n',
            '  with: `q`, `/`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called mkdir() for `/home/albert/projects/rst2html/rst2html-data/site_name`\n'))

    def test_rename_site(self, monkeypatch, capsys):
        def mock_rename(self, *args, **kwargs):
            print('called rename() for `{}` to `{}`'.format(self, args[0]))
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.rename_site('site_name', 'newname')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(dmlp.pathlib.Path, 'rename', mock_rename)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update sites set name = %s where id = %s;`\n',
            '  with: `newname`, `y`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called rename() for `{0}/site_name` to `{0}/newname`\n'.format(dmlp.WEBROOT)))

    def test_read_settings(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.read_settings('site_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(dmlp, '_get_settings', lambda x: {})
        # monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.read_settings('site_name') == {}
        monkeypatch.setattr(dmlp, '_get_settings', lambda x: {'css': '', 'wid': '1', 'hig': 2})
        assert dmlp.read_settings('site_name') == {'css': [], 'wid': 1, 'hig': 2}
        monkeypatch.setattr(dmlp, '_get_settings', lambda x: {'css': 'q;r', 'wid': 1, 'hig': '2'})
        assert dmlp.read_settings('site_name') == {'css': ['q', 'r'], 'wid': 1, 'hig': 2}
        monkeypatch.setattr(dmlp, '_get_settings', lambda x: {'test': '&', 'wid': 'x', 'hig': 'y'})
        assert dmlp.read_settings('site_name') == {'test': '&', 'wid': 'x', 'hig': 'y'}

    def test_update_settings(self, monkeypatch, capsys):
        counter = 0
        def mock_get_settings(*args):
            nonlocal counter
            counter += 1
            if counter == 1:
                return {'css': ['x', 'y'], 'nam': 'val', 'nam0': 'val0'}
            elif counter == 2:
                print('called get_settings()')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 15)
        monkeypatch.setattr(dmlp, '_get_settings', mock_get_settings)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.update_settings('site_name', {'nam': 'newval', 'nam2': 'val2',
                                           'css': ['q', 'r']})
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update site_settings set settval = %s'
            ' where site_id = %s and settname = %s`\n',
            '  with: `q;r`, `15`, `css`\n',
            'execute SQL: `update site_settings set settval = %s'
            ' where site_id = %s and settname = %s`\n',
            '  with: `newval`, `15`, `nam`\n',
            'execute SQL: `delete from site_settings'
            ' where site_id = %s and settname = %s`\n',
            '  with: `15`, `nam0`\n',
            'execute SQL: `insert into site_settings (site_id, settname, settval)'
            ' values (%s, %s, %s)`\n',
            '  with: `15`, `nam2`, `val2`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called get_settings()\n'))

    def test_clear_settings(self, monkeypatch, capsys):
        def mock_update_settings(*args):
            return 'called update_settings with `{}`, `{}`'.format(args[0], args[1])
        monkeypatch.setattr(dmlp, 'update_settings', mock_update_settings)
        assert dmlp.clear_settings('site_name') == ('called update_settings with'
                                                    ' `site_name`, `{}`')

    def test_list_dirs(self, monkeypatch, capsys):
        def mock_iter(self, *args):
            return (x for x in [{'id': 1, 'dirname': '/'},
                                {'id': 2, 'dirname': 'subdir'}])
        counter = 0
        def mock_iter_2(self, *args):
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'id': 1, 'dirname': '/'},
                                    {'id': 2, 'dirname': 'subdir'}])
            elif counter == 2:
                return (x for x in [{'dir_id': 1, 'target_docid': 3},
                                    {'dir_id': 1, 'target_docid': 4}])
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.list_dirs('site_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        with pytest.raises(RuntimeError):
            dmlp.list_dirs('site_name', 'x')
        assert dmlp.list_dirs('site_name') == dmlp.list_dirs('site_name', 'src')
        capsys.readouterr()  # flush capture
        assert dmlp.list_dirs('site_name') == ['subdir']
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, dirname from directories where site_id = %s;`\n',
            '  with: `99`\n'))
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter_2)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.list_dirs('site_name', 'dest') == []
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, dirname from directories where site_id = %s;`\n',
            '  with: `99`\n',
            'execute SQL: `select dir_id, target_docid from doc_stats'
            ' where dir_id = any(%s);`\n',
            '  with: `[1, 2]`\n'))

    def test_create_new_dir(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.create_new_dir('site_name', 'directory')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 'site_id')
        with pytest.raises(RuntimeError):
            dmlp.create_new_dir('site_name', '/')
        monkeypatch.setattr(dmlp, 'list_dirs', lambda x: ['directory'])
        with pytest.raises(FileExistsError):
            dmlp.create_new_dir('site_name', 'directory')
        monkeypatch.setattr(dmlp, 'list_dirs', lambda x: [])
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.create_new_dir('site_name', 'directory')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)`\n',
            '  with: `site_id`, `directory`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_remove_dir(self, monkeypatch, capsys):
        with pytest.raises(NotImplementedError):
            dmlp.remove_dir('site_name', 'directory')


class TestDocLevel:
    def test_list_docs(self, monkeypatch, capsys):
        def mock_dir_id(*args):
            print('called get_dir_id() for `{}`'.format(args[1]))
            if return_none:
                return None
            else:
                return 2
        def mock_iter(self, *args):
            if return_for in ('', 'src'):
                return (x for x in [{'docname': 'd4', 'source_docid': 4, 'source_deleted': False},
                                    {'docname': 'd5', 'source_docid': 5, 'source_deleted': True}])
            elif return_for == 'dest':
                return (x for x in [{'docname': 'd6', 'target_docid': 6, 'target_deleted': False},
                                    {'docname': 'd7', 'target_docid': 7, 'target_deleted': True}])
            elif return_for == 'mirror':
                return (x for x in [{'docname': 'd8', 'mirror_docid': 8, 'mirror_updated': False},
                                    {'docname': 'd9', 'mirror_docid': 9, 'mirror_updated': True}])
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.list_docs('site_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 1)
        return_none = True
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.list_docs('site_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        return_none = False
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in []))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.list_docs('site_name', directory='dirname') == []
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id() for `dirname`\n',
            'execute SQL: `select docname, source_docid, source_deleted, target_docid,'
            ' target_deleted, mirror_updated from doc_stats where dir_id = %s;`\n',
            '  with: `2`\n',
            'called commit() on connection\n',
            'called close()\n'))
        # contents are identical for each test, so no need to verify this every time
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        return_for = ''
        assert dmlp.list_docs('site_name', doctype=return_for) == ['d4']
        capsys.readouterr()  # flush
        assert dmlp.list_docs('site_name', doctype=return_for, deleted=True) == ['d5']
        capsys.readouterr()  # flush
        return_for = 'src'
        assert dmlp.list_docs('site_name', doctype=return_for) == ['d4']
        capsys.readouterr()  # flush
        assert dmlp.list_docs('site_name', doctype=return_for, deleted=False) == ['d4']
        capsys.readouterr()  # flush
        assert dmlp.list_docs('site_name', doctype=return_for, deleted=True) == ['d5']
        capsys.readouterr()  # flush
        return_for = 'dest'
        assert dmlp.list_docs('site_name', doctype=return_for) == ['d6']
        capsys.readouterr()  # flush
        assert dmlp.list_docs('site_name', doctype=return_for, deleted=True) == ['d7']
        capsys.readouterr()  # flush
        return_for = 'mirror'
        assert dmlp.list_docs('site_name', doctype=return_for, deleted=True) == []
        capsys.readouterr()  # flush
        assert dmlp.list_docs('site_name', doctype=return_for) == ['d9']
        capsys.readouterr()  # flush

    def test_list_templates(self, monkeypatch, capsys):
        def mock_iter(*args):
            return (x for x in [{'id': 1, 'name': 'tpl1'}, {'id': 2, 'name': 'tpl2'}])
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.list_templates('site_name') == ['tpl1', 'tpl2']
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select id, name from templates where site_id = %s;`\n',
            '  with: `99`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_read_template(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'text': 'contents'})
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.read_template('site_name', 'doc_name')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select text from templates where site_id = %s and name = %s;`\n',
            '  with: `99`, `doc_name`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_write_template(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: None)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select text from templates where site_id = %s and name = %s;`\n',
            '  with: `99`, `doc_name`\n',
            'execute SQL: `insert into templates (site_id, name, text) values (%s, %s, %s);`\n',
            '  with: `99`, `doc_name`, `data`\n',
            'called commit() on connection\n',
            'called close()\n'))
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ('oldtext',))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select text from templates where site_id = %s and name = %s;`\n',
            '  with: `99`, `doc_name`\n',
            'execute SQL: `update templates set text = %s where site_id = %s and name = %s;`\n',
            '  with: `data`, `99`, `doc_name`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_create_new_doc(self, monkeypatch, capsys):
        def mock_dir_id(*args):
            print('called get_dir_id for `{}`'.format(args[1]))
            if return_none:
                return None
            else:
                return 9
        with pytest.raises(AttributeError):
            dmlp.create_new_doc('site_name', '')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        return_none = True
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        return_none = False
        monkeypatch.setattr(dmlp, '_get_docs_in_dir', lambda x: ['doc_name'])
        with pytest.raises(FileExistsError):
            dmlp.create_new_doc('site_name', 'doc_name', 'subdir')
        assert capsys.readouterr().out == 'called get_dir_id for `subdir`\n'
        monkeypatch.setattr(dmlp, '_get_docs_in_dir', lambda x: [])
        monkeypatch.setattr(dmlp, '_add_doc', lambda: 15)
        monkeypatch.setattr(dmlp.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id for `/`\n'
            'execute SQL: `insert into doc_stats (dir_id, docname,'
            ' source_docid, source_updated) values (%s, %s, %s, %s);`\n',
            '  with: `9`, `doc_name`, `15`, `now`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_get_doc_contents(self, monkeypatch, capsys):
        def mock_dir_id(*args):
            print('called get_dir_id for `{}`'.format(args[1]))
            return 9
        with pytest.raises(AttributeError):
            dmlp.get_doc_contents('site_name', '')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (None, None, None))
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_contents('site_name', 'docname')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, None, 3))
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_contents('site_name', 'doc_name', 'src')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, 2, None))
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_contents('site_name', 'doc_name', 'dest', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id for `dirname`\n'
        # monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, 2, 3))
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'currtext': 'text'})
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.get_doc_contents('site_name', 'doc_name') == 'text'
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id for `/`\n',
            'execute SQL: `select currtext from documents where id = %s;`\n',
            '  with: `2`\n',
            'called commit() on connection\n',
            'called close()\n'))
        assert dmlp.get_doc_contents('site_name', 'doc_name', doctype='src') == 'text'
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id for `/`\n',
            'execute SQL: `select currtext from documents where id = %s;`\n',
            '  with: `2`\n',
            'called commit() on connection\n',
            'called close()\n'))
        assert dmlp.get_doc_contents('site_name', 'doc_name', doctype='dest') == 'text'
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id for `/`\n',
            'execute SQL: `select currtext from documents where id = %s;`\n',
            '  with: `3`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_update_rst(self, monkeypatch, capsys):
        def mock_get_dir_id(*args):
            print('called get_dir_id() for `{}`'.format(args[1]))
            return None
        def mock_get_dir_id_2(*args):
            print('called get_dir_id() for `{}`'.format(args[1]))
            return 99
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(AttributeError):
            dmlp.update_rst('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlp.update_rst('site_name', 'doc_name', '')
        with pytest.raises(FileNotFoundError):
            dmlp.update_rst('site_name', 'doc_name', 'contents')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 9)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.update_rst('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_get_dir_id_2)
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (None, 2, 3))
        # monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, None, 3))
        with pytest.raises(FileNotFoundError):
            dmlp.update_rst('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        monkeypatch.setattr(dmlp, '_get_dir_id', lambda x, y: 99 )
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, 2, 3) )
        monkeypatch.setattr(dmlp, '_get_doc_text', lambda x: 'old text' )
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        # monkeypatch.setattr(dmlp, 'now', lambda: 'now')
        monkeypatch.setattr(dmlp.datetime, 'datetime', MockDatetime)
        dmlp.update_rst('site_name', 'doc_name', 'contents', directory='')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n',
            '  with: `old text`, `contents`, `2`\n',
            'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_revert_rst(self, monkeypatch, capsys):
        def mock_get_dir_id(*args):
            print('called get_dir_id() for `{}`'.format(args[1]))
            return None
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(AttributeError):
            dmlp.revert_rst('site_name', '')
        with pytest.raises(FileNotFoundError):
            dmlp.revert_rst('site_name', 'doc_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 9)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_get_dir_id)  # lambda x, y: None)
        with pytest.raises(FileNotFoundError):
            dmlp.revert_rst('site_name', 'doc_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        monkeypatch.setattr(dmlp, '_get_dir_id', lambda x, y: 99)
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (None, 2, 3))
        with pytest.raises(FileNotFoundError):
            dmlp.revert_rst('site_name', 'doc_name')
        monkeypatch.setattr(dmlp, '_get_doc_ids', lambda x, y: (1, 2, 3) )

        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'previous': 'oldtext'})
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.datetime, 'datetime', MockDatetime)
        dmlp.revert_rst('site_name', 'doc_name')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select previous from documents where id = %s;`\n',
            '  with: `2`\n',
            'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n',
            '  with: ``, `oldtext`, `2`\n',
            'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_mark_src_deleted(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_doc_ids(*args):
            if counter == 3:
                return None, 2, 3
            else:
                return 1, 2, 3
        with pytest.raises(AttributeError):
            dmlp.mark_src_deleted('site_name', '')
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            dmlp.mark_src_deleted('site_name', 'doc_name')
        counter += 1
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.mark_src_deleted('site_name', 'doc_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(dmlp, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            dmlp.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        counter += 1

        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: (5,))
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select source_docid from doc_stats where id = %s;`\n',
            '  with: `1`\n',
            'execute SQL: `delete from documents where id = %s;`\n',
            '  with: `5`\n',
            'execute SQL: `update doc_stats set source_deleted = %s where id = %s;`\n',
            '  with: `True`, `1`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_update_html(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_doc_ids(*args):
            if counter == 3:
                return None, 2, 3
            elif counter == 4:
                return 1, 2, None
            else:
                return 1, 2, 3
        with pytest.raises(AttributeError):
            dmlp.update_html('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlp.update_html('site_name', 'docname', '')
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            dmlp.update_html('site_name', 'doc_name', 'contents')
        counter += 1
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.update_html('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(dmlp, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            dmlp.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'

        counter += 1
        monkeypatch.setattr(dmlp, '_add_doc', lambda: 15)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.datetime, 'datetime', MockDatetime)
        dmlp.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update documents set currtext = %s where id = %s;`\n',
            '  with: `contents`, `15`\n',
            'execute SQL: `update doc_stats set target_docid = %s, target_updated = %s'
            ' where id = %s;`\n',
            '  with: `15`, `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n'))
        counter += 1
        monkeypatch.setattr(dmlp, '_get_doc_text', lambda x: 'old doc text')
        dmlp.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n',
            '  with: `old doc text`, `contents`, `3`\n',
            'execute SQL: `update doc_stats set target_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n'))
        counter += 1
        dmlp.update_html('site_name', 'doc_name', 'contents')  # dry_run=True
        assert capsys.readouterr().out == ''

    def test_apply_deletions_target(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_iter(*args):
            return (x for x in [{'id': 1, 'target_docid': 11}, {'id': 2, 'target_docid': 12}])
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.apply_deletions_target('site_name')
        counter += 1
        with pytest.raises(FileNotFoundError):
            dmlp.apply_deletions_target('site_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        dmlp.apply_deletions_target('site_name')
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id() for `/`\n',
            'execute SQL: `select id, target_docid from doc_stats where source_deleted = %s;`\n',
            '  with: `True`\n',
            'execute SQL: `delete from documents where id = %s;`\n',
            '  with: `(11,)`, `(12,)`\n',
            'execute SQL: `update doc_stats set source_deleted = %s, target_docid = %s,'
            ' target_deleted = %s where id = %s;`\n',
            '  with: `(None, 1, True, 1)`, `(None, 1, True, 2)`\n',
            'called commit() on connection\n',
            'called close()\n'))

    def test_update_mirror(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_doc_ids(*args):
            if counter == 3:
                return None, 2, 3
            # elif counter == 4:
            #     return 1, 2, None
            else:
                return 1, 2, 3
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir() with arg `{}`'.format(self))
        def mock_touch(self, *args):
            print('called touch() with arg `{}`'.format(self))
        def mock_save_to(*args):
            print('called save_to() with args `{}` `{}`'.format(args[0], args[1]))
        with pytest.raises(AttributeError):
            dmlp.update_mirror('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlp.update_mirror('site_name', 'docname', '')
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            dmlp.update_mirror('site_name', 'doc_name', 'contents')
        counter += 1
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.update_mirror('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(dmlp, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            dmlp.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'

        counter += 1
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(dmlp.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlp, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(dmlp.pathlib.Path, 'touch', mock_touch)
        monkeypatch.setattr(dmlp, 'save_to', mock_save_to)
        dmlp.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called mkdir() with arg `{}/site_name`\n'.format(dmlp.WEBROOT),
            'called save_to() with args `{}/site_name/doc_name.html`'
            ' `data`\n'.format(dmlp.WEBROOT)))
        counter += 1
        monkeypatch.setattr(dmlp, 'read_settings', lambda x: {})
        dmlp.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called mkdir() with arg `{}/site_name`\n'.format(dmlp.WEBROOT),
            'called touch() with arg `{}/site_name/doc_name.html`\n'.format(dmlp.WEBROOT),
            'called save_to() with args `{}/site_name/doc_name.html`'
            ' `data`\n'.format(dmlp.WEBROOT)))
        counter += 1
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: True)
        dmlp.update_mirror('site_name', 'doc_name', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n',
            '  with: `now`, `1`\n',
            'called commit() on connection\n',
            'called close()\n',
            'called save_to() with args `{}/site_name/dirname/doc_name.html`'
            ' `data`\n'.format(dmlp.WEBROOT)))

        counter += 1
        dmlp.update_mirror('site_name', 'doc_name', 'contents')  # dry_run=True
        assert capsys.readouterr().out == ''

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_iter(*args):
            return (x for x in [{'id': 1, 'docname': 'xxx', 'target_docid': 11},
                                {'id': 2, 'docname': 'yyy.html', 'target_docid': 12}])
        def mock_unlink(self, *args):
            print('called unlink() with argument `{}`'.format(self))
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            dmlp.apply_deletions_mirror('site_name')
        counter += 1
        with pytest.raises(FileNotFoundError):
            dmlp.apply_deletions_mirror('site_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: False)
        dmlp.apply_deletions_mirror('site_name')
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id() for `/`\n',
            'execute SQL: `select id, docname, target_docid from doc_stats'
            ' where target_deleted = %s;`\n',
            '  with: `True`\n',
            'execute SQL: `delete from doc_stats where id = %s;`\n',
            '  with: `(1,)`, `(2,)`\n',
            'called commit() on connection\n',
            'called close()\n'
            ))
        monkeypatch.setattr(dmlp.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(dmlp.pathlib.Path, 'unlink', mock_unlink)
        dmlp.apply_deletions_mirror('site_name', 'dirname')
        destloc = '{}/site_name/dirname'.format(dmlp.WEBROOT)
        assert capsys.readouterr().out == ''.join((
            'called get_dir_id() for `dirname`\n',
            'execute SQL: `select id, docname, target_docid from doc_stats'
            ' where target_deleted = %s;`\n',
            '  with: `True`\n',
            'execute SQL: `delete from doc_stats where id = %s;`\n',
            '  with: `(1,)`, `(2,)`\n',
            'called commit() on connection\n',
            'called close()\n'
            'called unlink() with argument `{}/xxx.html`\n'.format(destloc),
            'called unlink() with argument `{}/yyy.html`\n'.format(destloc)))

    def test_get_doc_stats(self, monkeypatch, capsys):
        def mock_site_id(*args):
            if counter == 1:
                return None
            else:
                return 9
        def mock_dir_id(*args):
            if counter <= 3:
                print('called get_dir_id() for `{}`'.format(args[1]))
            if counter == 2:
                return None
            else:
                return 99
        def mock_doc_ids(*args):
            if counter == 3:
                return None, 2, 3
            # elif counter == 4:
            #     return 1, 2, None
            else:
                return 1, 2, 3
        def mock_stats(*args):
            return args[0]
        counter = 1
        monkeypatch.setattr(dmlp, '_get_site_id', mock_site_id)
        monkeypatch.setattr(dmlp, '_get_dir_id', mock_dir_id)
        monkeypatch.setattr(dmlp, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_stats('site_name', 'docname')
        counter += 1
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_stats('site_name', 'docname', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        with pytest.raises(FileNotFoundError):
            dmlp.get_doc_stats('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        counter += 1
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'source_updated': 1,
                                                               'target_updated': 2,
                                                               'mirror_updated': 3})
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        monkeypatch.setattr(dmlp, '_get_stats', mock_stats)
        assert dmlp.get_doc_stats('site_name', 'docname') == {'source_updated': 1,
                                                              'target_updated': 2,
                                                              'mirror_updated': 3}
        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select source_updated, target_updated, mirror_updated from doc_stats'
            ' where id = %s;`\n',
            '  with: `1`\n',
            'called close()\n'))

    def test_get_all_doc_stats(self, monkeypatch, capsys):
        counter = 0
        def mock_iter(*args):
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'dirname': '/'}, {'dirname': 'subdir'}])
            else:
                return (x for x in [{'docname': 'x', 'source_updated': 1, 'target_updated': 2,
                                     'mirror_updated': 3, 'dirname': '/'},
                                    {'docname': 'y', 'source_updated': 1, 'target_updated': 4,
                                     'mirror_updated': 5, 'dirname': '/'},
                                    {'docname': 'a', 'source_updated': 2, 'target_updated': 4,
                                     'mirror_updated': 5, 'dirname': 'subdir'},
                                    {'docname': 'b', 'source_updated': 3, 'target_updated': 4,
                                     'mirror_updated': 6, 'dirname': 'subdir'}])
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlp.get_all_doc_stats('site_name')
        monkeypatch.setattr(dmlp, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(dmlp, '_get_all_dir_ids', lambda x: [1, 2, 3])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(dmlp, 'conn', MockConn())
        assert dmlp.get_all_doc_stats('site_name') == [
                ('/', [('x', dmlp.Stats(src=1, dest=2, mirror=3)),
                       ('y', dmlp.Stats(src=1, dest=4, mirror=5))]),
                ('subdir',
                      [('a', dmlp.Stats(src=2, dest=4, mirror=5)),
                       ('b', dmlp.Stats(src=3, dest=4, mirror=6))])]

        assert capsys.readouterr().out == ''.join((
            'execute SQL: `select dirname from directories where site_id = %s;`\n',
            '  with: `99`\n',
            'execute SQL: `select docname, source_updated, target_updated, mirror_updated,'
            ' dirname from doc_stats, directories where dir_id = directories.id'
            ' and dir_id = any(%s);`\n',
            '  with: `[1, 2, 3]`\n',
            'called commit() on connection\n',
            'called close()\n'))
