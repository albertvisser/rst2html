"""unittests for ./app/docs2pg.py
"""
import datetime
import pytest
import app.docs2pg as testee

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
    """unittest for docs2pg.is_equal
    """
    assert testee._is_equal([1], 1)
    assert not testee._is_equal([0], 1)
    with pytest.raises(TypeError):
        testee._is_equal(1, 1)


class MockDatetime:
    """stub for datetime.DateTime object
    """
    def utcnow(*args):
        """stub
        """
        return 'now'


class MockConn:
    """stub for psycopg2.Connection object
    """
    def cursor(self, *args, **kwargs):
        """stub
        """
        return MockCursor()

    def commit(self, *args, **kwargs):
        """stub
        """
        print('called commit() on connection')


class MockCursor:
    """stub for psycopg2.Cursor object
    """
    def __iter__(self):
        """stub
        """

    def execute(self, *args):
        """stub
        """
        print(f'execute SQL: `{args[0]}`')
        if len(args) > 1:
            print('  with:', ', '.join([f'`{x}`' for x in args[1]]))

    def executemany(self, *args):
        """stub
        """
        print(f'execute SQL: `{args[0]}`')
        if len(args) > 1:
            print('  with:', ', '.join([f'`{x}`' for x in args[1]]))

    def commit(self, *args, **kwargs):
        """stub
        """
        print('called commit() on cursor')

    def close(self, *args, **kwargs):
        """stub
        """
        print('called close()')

    def fetchone(self, *args, **kwargs):
        """stub
        """

    def fetchall(self, *args, **kwargs):
        """stub
        """


class TestNonApiFunctions:
    """unittests for functions outside of the dml API
    """
    def test_get_site_id(self, monkeypatch, capsys):
        """unittest for docs2pg.get_site_id
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return ()
        def mock_fetchone_2(self, *args):
            """stub
            """
            return {'id': 99}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert testee._get_site_id('site_name') == ()
        assert capsys.readouterr().out == (
            'execute SQL: `select id from sites where sitename = %s;`\n'
            '  with: `site_name`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone_2)
        assert testee._get_site_id('site_name') == 99
        assert capsys.readouterr().out == (
            'execute SQL: `select id from sites where sitename = %s;`\n'
            '  with: `site_name`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_get_dir_id(self, monkeypatch, capsys):
        """unittest for docs2pg.get_dir_id
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return ()
        def mock_fetchone_2(self, *args):
            """stub
            """
            return {'id': 'dir_id'}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert testee._get_dir_id('site_id', 'dir_id') == ()
        assert capsys.readouterr().out == (
            'execute SQL: `select id from directories where site_id = %s and dirname = %s;`\n'
            '  with: `site_id`, `dir_id`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone_2)
        assert testee._get_dir_id('site_id', 'dir_id') == 'dir_id'
        assert capsys.readouterr().out == (
            'execute SQL: `select id from directories where site_id = %s and dirname = %s;`\n'
            '  with: `site_id`, `dir_id`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_get_all_dir_ids(self, monkeypatch, capsys):
        """unittest for docs2pg.get_all_dir_ids
        """
        def mock_fetchall(self, *args):
            """stub
            """
            return []
        def mock_fetchall_2(self, *args):
            """stub
            """
            return [{'id': 'dirid01'}, {'id': 'dirid02'}]
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        assert testee._get_all_dir_ids('site_id') == []
        assert capsys.readouterr().out == (
            'execute SQL: `select id from directories where site_id = %s;`\n'
            '  with: `site_id`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall_2)
        assert testee._get_all_dir_ids('site_id') == ['dirid01', 'dirid02']
        assert capsys.readouterr().out == (
            'execute SQL: `select id from directories where site_id = %s;`\n'
            '  with: `site_id`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_get_docs_in_dir(self, monkeypatch, capsys):
        """unittest for docs2pg.get_docs_in_dir
        """
        def mock_fetchall(self, *args):
            """stub
            """
            return []
        def mock_fetchall_2(self, *args):
            """stub
            """
            return [{'docname': 'docname_01'}, {'docname': 'docname_02'}]
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        assert testee._get_docs_in_dir('dir_id') == []
        assert capsys.readouterr().out == (
            'execute SQL: `select docname from doc_stats where dir_id = %s;`\n'
            '  with: `dir_id`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall_2)
        assert testee._get_docs_in_dir('dir_id') == ['docname_01', 'docname_02']
        assert capsys.readouterr().out == (
            'execute SQL: `select docname from doc_stats where dir_id = %s;`\n'
            '  with: `dir_id`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_get_doc_ids(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_ids
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return {'id': 1, 'source_docid': 2, 'target_docid': 3}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {})
        assert testee._get_doc_ids('dir_id', 'docname') == (None, None, None)
        assert capsys.readouterr().out == (
            'execute SQL: `select id, source_docid, target_docid from doc_stats'
            ' where dir_id = %s and docname = %s;`\n'
            '  with: `dir_id`, `docname`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert testee._get_doc_ids('dir_id', 'docname') == (1, 2, 3)
        assert capsys.readouterr().out == (
            'execute SQL: `select id, source_docid, target_docid from doc_stats'
            ' where dir_id = %s and docname = %s;`\n'
            '  with: `dir_id`, `docname`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_get_doc_text(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_text
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return {'currtext': 'some_text'}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {})
        assert testee._get_doc_text('doc_id') == (None, None, None)
        assert capsys.readouterr().out == (
             'execute SQL: `select currtext from documents where id = %s;`\n'
             '  with: `doc_id`\n'
             'called commit() on connection\n'
             'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert testee._get_doc_text('doc_id') == 'some_text'
        assert capsys.readouterr().out == (
             'execute SQL: `select currtext from documents where id = %s;`\n'
             '  with: `doc_id`\n'
             'called commit() on connection\n'
             'called close()\n')

    def test_get_settings(self, monkeypatch, capsys):
        """unittest for docs2pg.get_settings
        """
        def mock_iter(self):
            """stub
            """
            return (x for x in [{'settname': 'sett1', 'settval': 'val1'},
                                {'settname': 'sett2', 'settval': 'val2'}])
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        assert testee._get_settings('site_id') == {'sett1': 'val1', 'sett2': 'val2'}
        assert capsys.readouterr().out == (
            'execute SQL: `select settname, settval from site_settings where site_id = %s`\n'
            '  with: `site_id`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_add_doc(self, monkeypatch, capsys):
        """unittest for docs2pg.add_doc
        """
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ({'id': 'some_id'}))
        assert testee._add_doc() == 'some_id'
        assert capsys.readouterr().out == (
                'execute SQL: `insert into documents (currtext, previous) values (%s, %s)'
                ' returning id`\n'
                '  with: ``, ``\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_stats(self):
        """unittest for docs2pg.get_stats
        """
        mindate = datetime.datetime.min
        assert testee._get_stats((1, None, 2, None, 3)) == testee.Stats(1, 2, 3)
        assert testee._get_stats((1, True, 2, True, 0)) == testee.Stats('[deleted]', '[deleted]', mindate)
        assert testee._get_stats((0, None, 0, None, 0)) == testee.Stats(mindate, mindate, mindate)
        with pytest.raises(ValueError):
            assert testee._get_stats(()) == testee.Stats('', '', '')


class TestTestApi:
    """unittests for api functions related to testing
    """
    def test_clear_db(self, monkeypatch, capsys):
        """unittest for docs2pg.clear_db
        """
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.clear_db()
        assert capsys.readouterr().out == (
                'execute SQL: `truncate table sites;`\n'
                'execute SQL: `truncate table site_settings;`\n'
                'execute SQL: `truncate table directories;`\n'
                'execute SQL: `truncate table doc_stats;`\n'
                'execute SQL: `truncate table documents;`\n'
                'execute SQL: `truncate table templates;`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_read_db(self, monkeypatch, capsys):
        """unittest for docs2pg.read_db
        """
        def mock_fetchall(self, *args):
            """stub
            """
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
            """stub
            """
            return (x for x in [{'docname': 'doc1', 'id': 'id1'},
                                {'docname': 'doc2', 'id': 'id2'}])
        counter = 0
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.read_db() == [{'name': 'a_site', 'settings': {},
                                   'docs': [[{'docname': 'doc1', 'id': 'id1', 'dirname': '/'},
                                             {'docname': 'doc2', 'id': 'id2', 'dirname': '/'}]]},
                                  {'name': 'another', 'settings': {},
                                   'docs': [[{'docname': 'doc1', 'id': 'id1', 'dirname': '/'},
                                             {'docname': 'doc2', 'id': 'id2', 'dirname': '/'}],
                                            [{'docname': 'doc1', 'id': 'id1',
                                              'dirname': 'otherdir'},
                                             {'docname': 'doc2', 'id': 'id2',
                                              'dirname': 'otherdir'}]]}]

        assert capsys.readouterr().out == (
                'execute SQL: `select sitename, id from sites order by sitename;`\n'
                'execute SQL: `select settname, settval from site_settings'
                ' where site_id = %s order by settname;`\n'
                '  with: `1`\n'
                'execute SQL: `select dirname, id from directories'
                ' where site_id = %s order by dirname;`\n'
                '  with: `1`\n'
                'execute SQL: `select * from doc_stats where dir_id = %s order by docname;`\n'
                '  with: `1`\n'
                'execute SQL: `select settname, settval from site_settings'
                ' where site_id = %s order by settname;`\n'
                '  with: `2`\n'
                'execute SQL: `select dirname, id from directories'
                ' where site_id = %s order by dirname;`\n'
                '  with: `2`\n'
                'execute SQL: `select * from doc_stats where dir_id = %s order by docname;`\n'
                '  with: `2`\n'
                'execute SQL: `select * from doc_stats where dir_id = %s order by docname;`\n'
                '  with: `3`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_list_site_data(self, monkeypatch, capsys):
        """unittest for docs2pg.list_site_data
        """
        counter = 0
        def mock_iter(*args):
            """stub
            """
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'id': 2, 'dirname': '/'}, {'id': 3, 'dirname': 'subdir'}])
            if counter == 2:
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
            if counter == 3:
                return (x for x in [{'id': 4, 'currtext': '/doc1 src text', 'previous': ''},
                                    {'id': 5, 'currtext': '/doc1 dest text', 'previous': 'old txt'},
                                    {'id': 6, 'currtext': 'subdir/doc2 src', 'previous': 'old'},
                                    {'id': 7, 'currtext': 'subdir/doc2 dest', 'previous': ''}])
            if counter == 4:
                return (x for x in [{'name': 'tpl1', 'text': 'text tpl1'},
                                    {'name': 'tpl2', 'text': 'text tpl2'}])
            return ()
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.list_site_data('testsite')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 1)
        monkeypatch.setattr(testee, '_get_settings', lambda x: {'sett1': 'val1', 'sett2': 'val2'})
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        # import pdb; pdb.set_trace()
        assert testee.list_site_data('sitename') == ({'_id': 1, 'name': 'sitename',
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
            {'_id': ('tpl2',), 'template contents': 'text tpl2'}])
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `1`\n'
                'called commit() on connection\n'
                'called close()\n'
                'execute SQL: `select docname, source_docid, source_updated, source_deleted,'
                ' target_docid, target_updated, target_deleted, mirror_updated, dir_id'
                ' from doc_stats where dir_id = any(%s);`\n'
                '  with: `[2, 3]`\n'
                'called commit() on connection\n'
                'called close()\n'
                'execute SQL: `select id, currtext, previous from documents where id = any(%s)`\n'
                '  with: `[4, 5, None, 6, 7]`\n'
                'execute SQL: `select name, text from templates where site_id = %s;`\n'
                '  with: `1`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_clear_site_data(self, monkeypatch, capsys):
        """unittest for docs2pg.clear_site_data
        """
        def mock_rmtree_err(*args):
            """stub
            """
            print('called rmtree()')
            raise FileNotFoundError
        def mock_rmtree_ok(*args):
            """stub
            """
            print(f'called rmtree() with arg `{args[0]}`')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        testee.clear_site_data('site_name')
        assert capsys.readouterr().out == ''

        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_err)
        testee.clear_site_data('site_name')
        assert capsys.readouterr().out == 'called rmtree()\n'

        monkeypatch.setattr(testee, '_get_site_id', lambda x: 1)
        monkeypatch.setattr(testee, '_get_all_dir_ids', lambda x: [2, 3])
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in [
            {'source_docid': 4, 'target_docid': 7},
            {'source_docid': 5, 'target_docid': 0},
            {'source_docid': 6, 'target_docid': 9}]))
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_ok)
        testee.clear_site_data('site_name')
        dest = testee.WEBROOT / 'site_name'
        assert capsys.readouterr().out == (
            'execute SQL: `select source_docid, target_docid from doc_stats'
            ' where dir_id = any(%s);`\n'
            '  with: `[2, 3]`\n'
            'execute SQL: `delete from documents where id = any(%s);`\n'
            '  with: `[4, 7, 5, 6, 9]`\n'
            'execute SQL: `delete from doc_stats where dir_id = any(%s);`\n'
            '  with: `[2, 3]`\n'
            'execute SQL: `delete from templates where site_id = %s;`\n'
            '  with: `1`\n'
            'execute SQL: `delete from directories where site_id = %s;`\n'
            '  with: `1`\n'
            'execute SQL: `delete from site_settings where site_id = %s;`\n'
            '  with: `1`\n'
            'execute SQL: `delete from sites where id = %s;`\n'
            '  with: `1`\n'
            'called commit() on connection\n'
            'called close()\n'
            f'called rmtree() with arg `{dest}`\n')


class TestSiteLevel:
    """unittests for site level api functions
    """
    def test_list_sites(self, monkeypatch, capsys):
        """unittest for docs2pg.list_sites
        """
        def mock_fetchall(self, *args):
            """stub
            """
            return [{'sitename': 'site1'}, {'sitename': 'site2'}]
        monkeypatch.setattr(MockCursor, 'fetchall', mock_fetchall)
        # monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.list_sites() == ['site1', 'site2']
        assert capsys.readouterr().out == (
                'execute SQL: `select sitename from sites;`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_create_new_site(self, monkeypatch, capsys):
        """unittest for docs2pg.create_new_site
        """
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() for `{self}`')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        with pytest.raises(FileExistsError):
            testee.create_new_site('site_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        with pytest.raises(FileExistsError):
            testee.create_new_site('site_name')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ({'id': 'q'}))
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        testee.create_new_site('site_name')
        assert capsys.readouterr().out == (
                'execute SQL: `insert into sites (sitename) values (%s) returning id;`\n'
                '  with: `site_name`\n'
                'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)`\n'
                '  with: `q`, `/`\n'
                'called commit() on connection\n'
                'called close()\n'
                'called mkdir() for `/home/albert/projects/rst2html/rst2html-data/site_name`\n')

    def test_rename_site(self, monkeypatch, capsys):
        """unittest for docs2pg.rename_site
        """
        def mock_rename(self, *args, **kwargs):
            """stub
            """
            print(f'called rename() for `{self}` to `{args[0]}`')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.rename_site('site_name', 'newname')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == (
                'execute SQL: `update sites set sitename = %s where id = %s;`\n'
                '  with: `newname`, `y`\n'
                'called commit() on connection\n'
                'called close()\n'
                f'called rename() for `{testee.WEBROOT}/site_name` to `{testee.WEBROOT}/newname`\n')

    def test_read_settings(self, monkeypatch):
        """unittest for docs2pg.read_settings
        """
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.read_settings('site_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 'y')
        monkeypatch.setattr(testee, '_get_settings', lambda x: {})
        # monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.read_settings('site_name') == {}
        monkeypatch.setattr(testee, '_get_settings', lambda x: {'css': '', 'wid': '1', 'hig': 2})
        assert testee.read_settings('site_name') == {'css': [], 'wid': 1, 'hig': 2}
        monkeypatch.setattr(testee, '_get_settings', lambda x: {'css': 'q;r', 'wid': 1, 'hig': '2'})
        assert testee.read_settings('site_name') == {'css': ['q', 'r'], 'wid': 1, 'hig': 2}
        monkeypatch.setattr(testee, '_get_settings', lambda x: {'test': '&', 'wid': 'x', 'hig': 'y'})
        assert testee.read_settings('site_name') == {'test': '&', 'wid': 'x', 'hig': 'y'}

    def test_update_settings(self, monkeypatch, capsys):
        """unittest for docs2pg.update_settings
        """
        def mock_get_settings(*args):
            """stub
            """
            nonlocal counter
            print('called get_settings()')
            counter += 1
            if counter == 1:
                return {'css': ['x', 'y'], 'nam': 'val', 'nam0': 'val0'}
            return 'new site settings'
        def mock_get_settings_2(*args):
            """stub
            """
            nonlocal counter
            print('called get_settings()')
            counter += 1
            if counter == 1:
                return {'nam': 'val', 'nam0': 'val0'}
            return 'new site settings'
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 15)
        monkeypatch.setattr(testee, '_get_settings', mock_get_settings)
        monkeypatch.setattr(testee, 'conn', MockConn())
        counter = 0
        assert testee.update_settings('site_name', {'nam': 'newval', 'nam2': 'val2',
                                                    'css': ['q', 'r']}) == 'new site settings'
        assert capsys.readouterr().out == (
                'called get_settings()\n'
                'execute SQL: `update site_settings set settval = %s'
                ' where site_id = %s and settname = %s`\n'
                '  with: `q;r`, `15`, `css`\n'
                'execute SQL: `update site_settings set settval = %s'
                ' where site_id = %s and settname = %s`\n'
                '  with: `newval`, `15`, `nam`\n'
                'execute SQL: `delete from site_settings'
                ' where site_id = %s and settname = %s`\n'
                '  with: `15`, `nam0`\n'
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `15`, `nam2`, `val2`\n'
                'called commit() on connection\n'
                'called close()\n'
                'called get_settings()\n')
        counter = 0
        monkeypatch.setattr(testee, '_get_settings', mock_get_settings_2)
        assert testee.update_settings('site_name', {'nam': 'val', 'nam2': 'val2'}) == (
                'new site settings')
        assert capsys.readouterr().out == (
                'called get_settings()\n'
                'execute SQL: `delete from site_settings'
                ' where site_id = %s and settname = %s`\n'
                '  with: `15`, `nam0`\n'
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `15`, `nam2`, `val2`\n'
                'called commit() on connection\n'
                'called close()\n'
                'called get_settings()\n')

    def test_clear_settings(self, monkeypatch):
        """unittest for docs2pg.clear_settings
        """
        def mock_update_settings(*args):
            """stub
            """
            return f'called update_settings with `{args[0]}`, `{args[1]}`'
        monkeypatch.setattr(testee, 'update_settings', mock_update_settings)
        assert testee.clear_settings('site_name') == ('called update_settings with `site_name`, `{}`')

    def test_list_dirs(self, monkeypatch, capsys):
        """unittest for docs2pg.list_dirs
        """
        def mock_iter(self, *args):
            """stub
            """
            return (x for x in [{'id': 1, 'dirname': '/'},
                                {'id': 2, 'dirname': 'subdir'}])
        counter = 0
        def mock_iter_2(self, *args):
            """stub
            """
            nonlocal counter
            counter += 1
            if counter % 2 == 1:
                return (x for x in [{'id': 1, 'dirname': '/'},
                                    {'id': 2, 'dirname': 'subdir'}])
            if counter == 2:
                return (x for x in [{'dir_id': 1, 'target_docid': 3},
                                    {'dir_id': 1, 'target_docid': 4}])
            if counter == 4:
                return (x for x in [{'dir_id': 1, 'target_docid': 3},
                                    {'dir_id': 2, 'target_docid': 4}])
            return (x for x in [{'dir_id': 1, 'target_docid': 3},
                                {'dir_id': 2, 'target_docid': None}])
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.list_dirs('site_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        with pytest.raises(RuntimeError):
            testee.list_dirs('site_name', 'x')
        assert testee.list_dirs('site_name') == testee.list_dirs('site_name', 'src')
        capsys.readouterr()  # flush capture
        assert testee.list_dirs('site_name') == ['subdir']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `99`\ncalled commit() on connection\ncalled close()\n')
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter_2)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.list_dirs('site_name', 'dest') == []
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `99`\n'
                'execute SQL: `select dir_id, target_docid from doc_stats'
                ' where dir_id = any(%s);`\n'
                '  with: `[1, 2]`\ncalled commit() on connection\ncalled close()\n')
        assert testee.list_dirs('site_name', 'dest') == ['subdir']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `99`\n'
                'execute SQL: `select dir_id, target_docid from doc_stats'
                ' where dir_id = any(%s);`\n'
                '  with: `[1, 2]`\ncalled commit() on connection\ncalled close()\n')
        assert testee.list_dirs('site_name', 'dest') == []
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `99`\n'
                'execute SQL: `select dir_id, target_docid from doc_stats'
                ' where dir_id = any(%s);`\n'
                '  with: `[1, 2]`\ncalled commit() on connection\ncalled close()\n')

    def test_create_new_dir(self, monkeypatch, capsys):
        """unittest for docs2pg.create_new_dir
        """
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.create_new_dir('site_name', 'directory')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 'site_id')
        with pytest.raises(RuntimeError):
            testee.create_new_dir('site_name', '/')
        monkeypatch.setattr(testee, 'list_dirs', lambda x: ['directory'])
        with pytest.raises(FileExistsError):
            testee.create_new_dir('site_name', 'directory')
        monkeypatch.setattr(testee, 'list_dirs', lambda x: [])
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.create_new_dir('site_name', 'directory')
        assert capsys.readouterr().out == (
                'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)`\n'
                '  with: `site_id`, `directory`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_remove_dir(self):
        """unittest for docs2pg.remove_dir
        """
        with pytest.raises(NotImplementedError):
            testee.remove_dir('site_name', 'directory')


class TestDocLevel:
    """unittests for document level api functions
    """
    def test_list_docs(self, monkeypatch, capsys):
        """unittest for docs2pg.list_docs
        """
        def mock_dir_id(*args):
            """stub
            """
            print(f'called get_dir_id() for `{args[1]}`')
            if return_none:
                return None
            return 2
        def mock_iter(self, *args):
            """stub
            """
            if return_for in ('', 'src'):
                return (x for x in [{'docname': 'd4', 'source_docid': 4, 'source_deleted': False},
                                    {'docname': 'd5', 'source_docid': 5, 'source_deleted': True}])
            if return_for == 'dest':
                return (x for x in [{'docname': 'd6', 'target_docid': 6, 'target_deleted': False},
                                    {'docname': 'd7', 'target_docid': 7, 'target_deleted': True}])
            # if return_for == 'mirror':
            return (x for x in [{'docname': 'd8', 'mirror_docid': 8, 'mirror_updated': False},
                                {'docname': 'd9', 'mirror_docid': 9, 'mirror_updated': True}])
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.list_docs('site_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 1)
        return_none = True
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.list_docs('site_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        return_none = False
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in []))
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.list_docs('site_name', directory='dirname') == []
        assert capsys.readouterr().out == (
                'called get_dir_id() for `dirname`\n'
                'execute SQL: `select docname, source_docid, source_deleted, target_docid,'
                ' target_deleted, mirror_updated from doc_stats where dir_id = %s;`\n'
                '  with: `2`\n'
                'called commit() on connection\n'
                'called close()\n')
        # contents are identical for each test, so no need to verify this every time
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        return_for = ''
        assert testee.list_docs('site_name', doctype=return_for) == ['d4']
        capsys.readouterr()  # flush
        assert testee.list_docs('site_name', doctype=return_for, deleted=True) == ['d5']
        capsys.readouterr()  # flush
        return_for = 'src'
        assert testee.list_docs('site_name', doctype=return_for) == ['d4']
        capsys.readouterr()  # flush
        assert testee.list_docs('site_name', doctype=return_for, deleted=False) == ['d4']
        capsys.readouterr()  # flush
        assert testee.list_docs('site_name', doctype=return_for, deleted=True) == ['d5']
        capsys.readouterr()  # flush
        return_for = 'dest'
        assert testee.list_docs('site_name', doctype=return_for) == ['d6']
        capsys.readouterr()  # flush
        assert testee.list_docs('site_name', doctype=return_for, deleted=True) == ['d7']
        capsys.readouterr()  # flush
        return_for = 'mirror'
        assert testee.list_docs('site_name', doctype=return_for, deleted=True) == []
        capsys.readouterr()  # flush
        assert testee.list_docs('site_name', doctype=return_for) == ['d9']
        capsys.readouterr()  # flush

    def test_list_templates(self, monkeypatch, capsys):
        """unittest for docs2pg.list_templates
        """
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'id': 1, 'name': 'tpl1'}, {'id': 2, 'name': 'tpl2'}])
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.list_templates('site_name') == ['tpl1', 'tpl2']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, name from templates where site_id = %s;`\n'
                '  with: `99`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_read_template(self, monkeypatch, capsys):
        """unittest for docs2pg.read_template
        """
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'text': 'contents'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.read_template('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `99`, `doc_name`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_write_template(self, monkeypatch, capsys):
        """unittest for docs2pg.write_template
        """
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: None)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `99`, `doc_name`\n'
                'execute SQL: `insert into templates (site_id, name, text) values (%s, %s, %s);`\n'
                '  with: `99`, `doc_name`, `data`\n'
                'called commit() on connection\n'
                'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ('oldtext',))
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `99`, `doc_name`\n'
                'execute SQL: `update templates set text = %s where site_id = %s and name = %s;`\n'
                '  with: `data`, `99`, `doc_name`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_create_new_doc(self, monkeypatch, capsys):
        """unittest for docs2pg.create_new_doc
        """
        def mock_dir_id(*args):
            """stub
            """
            print(f'called get_dir_id for `{args[1]}`')
            if return_none:
                return None
            return 9
        with pytest.raises(AttributeError):
            testee.create_new_doc('site_name', '')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        return_none = True
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        return_none = False
        monkeypatch.setattr(testee, '_get_docs_in_dir', lambda x: ['doc_name'])
        with pytest.raises(FileExistsError):
            testee.create_new_doc('site_name', 'doc_name', 'subdir')
        assert capsys.readouterr().out == 'called get_dir_id for `subdir`\n'
        monkeypatch.setattr(testee, '_get_docs_in_dir', lambda x: [])
        monkeypatch.setattr(testee, '_add_doc', lambda: 15)
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `insert into doc_stats (dir_id, docname,'
                ' source_docid, source_updated) values (%s, %s, %s, %s);`\n'
                '  with: `9`, `doc_name`, `15`, `now`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_doc_contents(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_contents
        """
        def mock_dir_id(*args):
            """stub
            """
            print(f'called get_dir_id for `{args[1]}`')
            return 9
        with pytest.raises(AttributeError):
            testee.get_doc_contents('site_name', '')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (None, None, None))
        with pytest.raises(FileNotFoundError):
            testee.get_doc_contents('site_name', 'docname')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, None, 3))
        with pytest.raises(FileNotFoundError):
            testee.get_doc_contents('site_name', 'doc_name', 'src')
        assert capsys.readouterr().out == 'called get_dir_id for `/`\n'
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, 2, None))
        with pytest.raises(FileNotFoundError):
            testee.get_doc_contents('site_name', 'doc_name', 'dest', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id for `dirname`\n'
        # monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, 2, 3))
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'currtext': 'text',
                                                               'previous': 'old text'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.get_doc_contents('site_name', 'doc_name') == 'text'
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `select currtext from documents where id = %s;`\n'
                '  with: `2`\n'
                'called commit() on connection\n'
                'called close()\n')
        assert testee.get_doc_contents('site_name', 'doc_name', previous=True) == 'old text'
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `select previous from documents where id = %s;`\n'
                '  with: `2`\n'
                'called commit() on connection\n'
                'called close()\n')
        assert testee.get_doc_contents('site_name', 'doc_name', doctype='src') == 'text'
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `select currtext from documents where id = %s;`\n'
                '  with: `2`\n'
                'called commit() on connection\n'
                'called close()\n')
        assert testee.get_doc_contents('site_name', 'doc_name', doctype='dest') == 'text'
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `select currtext from documents where id = %s;`\n'
                '  with: `3`\n'
                'called commit() on connection\n'
                'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {})
        assert testee.get_doc_contents('site_name', 'doc_name', previous=True) == (
                '/doc_name has id 2, but no previous contents')
        assert capsys.readouterr().out == (
                'called get_dir_id for `/`\n'
                'execute SQL: `select previous from documents where id = %s;`\n'
                '  with: `2`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_update_rst(self, monkeypatch, capsys):
        """unittest for docs2pg.update_rst
        """
        def mock_get_dir_id(*args):
            """stub
            """
            print(f'called get_dir_id() for `{args[1]}`')
        def mock_get_dir_id_2(*args):
            """stub
            """
            print(f'called get_dir_id() for `{args[1]}`')
            return 99
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(AttributeError):
            testee.update_rst('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            testee.update_rst('site_name', 'doc_name', '')
        with pytest.raises(FileNotFoundError):
            testee.update_rst('site_name', 'doc_name', 'contents')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 9)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.update_rst('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id_2)
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (None, 2, 3))
        # monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, None, 3))
        with pytest.raises(FileNotFoundError):
            testee.update_rst('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        monkeypatch.setattr(testee, '_get_dir_id', lambda x, y: 99)
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, 2, 3))
        monkeypatch.setattr(testee, '_get_doc_text', lambda x: 'old text')
        monkeypatch.setattr(testee, 'conn', MockConn())
        # monkeypatch.setattr(testee, 'now', lambda: 'now')
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee.update_rst('site_name', 'doc_name', 'contents', directory='')
        assert capsys.readouterr().out == ''.join(
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: `old text`, `contents`, `2`\n'
                'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_revert_rst(self, monkeypatch, capsys):
        """unittest for docs2pg.revert_rst
        """
        def mock_get_dir_id(*args):
            """stub
            """
            print(f'called get_dir_id() for `{args[1]}`')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(AttributeError):
            testee.revert_rst('site_name', '')
        with pytest.raises(FileNotFoundError):
            testee.revert_rst('site_name', 'doc_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 9)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)  # lambda x, y: None)
        with pytest.raises(FileNotFoundError):
            testee.revert_rst('site_name', 'doc_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        monkeypatch.setattr(testee, '_get_dir_id', lambda x, y: 99)
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (None, 2, 3))
        with pytest.raises(FileNotFoundError):
            testee.revert_rst('site_name', 'doc_name')
        monkeypatch.setattr(testee, '_get_doc_ids', lambda x, y: (1, 2, 3))

        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'previous': 'oldtext'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee.revert_rst('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                'execute SQL: `select previous from documents where id = %s;`\n'
                '  with: `2`\n'
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: ``, `oldtext`, `2`\n'
                'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_mark_src_deleted(self, monkeypatch, capsys):
        """unittest for docs2pg.mark_src_deleted
        """
        def mock_site_id(*args):
            """stub
            """
            if counter == 1:
                return None
            return 9
        def mock_dir_id(*args):
            """stub
            """
            if counter <= 3:
                print(f'called get_dir_id() for `{args[1]}`')
            if counter == 2:
                return None
            return 99
        def mock_doc_ids(*args):
            """stub
            """
            if counter == 3:
                return None, 2, 3
            return 1, 2, 3
        with pytest.raises(AttributeError):
            testee.mark_src_deleted('site_name', '')
        counter = 1
        monkeypatch.setattr(testee, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            testee.mark_src_deleted('site_name', 'doc_name')
        counter += 1
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.mark_src_deleted('site_name', 'doc_name', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(testee, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            testee.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        counter += 1

        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: (5,))
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                'execute SQL: `select source_docid from doc_stats where id = %s;`\n'
                '  with: `1`\n'
                'execute SQL: `delete from documents where id = %s;`\n'
                '  with: `5`\n'
                'execute SQL: `update doc_stats set source_deleted = %s where id = %s;`\n'
                '  with: `True`, `1`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_update_html(self, monkeypatch, capsys):
        """unittest for docs2pg.update_html
        """
        def mock_site_id(*args):
            """stub
            """
            if counter == 1:
                return None
            return 9
        def mock_dir_id(*args):
            """stub
            """
            if counter <= 3:
                print(f'called get_dir_id() for `{args[1]}`')
            if counter == 2:
                return None
            return 99
        def mock_doc_ids(*args):
            """stub
            """
            if counter == 3:
                return None, 2, 3
            if counter == 4:
                return 1, 2, None
            return 1, 2, 3
        with pytest.raises(AttributeError):
            testee.update_html('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            testee.update_html('site_name', 'docname', '')
        counter = 1
        monkeypatch.setattr(testee, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            testee.update_html('site_name', 'doc_name', 'contents')
        counter += 1
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.update_html('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(testee, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            testee.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'

        counter += 1
        monkeypatch.setattr(testee, '_add_doc', lambda: 15)
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update documents set currtext = %s where id = %s;`\n'
                '  with: `contents`, `15`\n'
                'execute SQL: `update doc_stats set target_docid = %s, target_updated = %s'
                ' where id = %s;`\n'
                '  with: `15`, `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n')
        counter += 1
        monkeypatch.setattr(testee, '_get_doc_text', lambda x: 'old doc text')
        testee.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: `old doc text`, `contents`, `3`\n'
                'execute SQL: `update doc_stats set target_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n')
        counter += 1
        testee.update_html('site_name', 'doc_name', 'contents')  # dry_run=True
        assert capsys.readouterr().out == ''

    def test_list_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2pg.list_deletions_target
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            if args[1] == '':
                return [('/', 99)]
            if args[1] == '*':
                return [('/', 99), ('subdir', 99)]
            return [('dirname', 99)]
        def mock_list_deletions(*args):
            """stub
            """
            print(f'called list_deletions() met {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2')
            return retval
        monkeypatch.setattr(testee, 'get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'list_deletions', mock_list_deletions)
        assert testee.list_deletions_target('sitename', '') == ['doc1']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '')\n"
                "called list_deletions() met args=([('/', 99)], 'source')\n")
        assert testee.list_deletions_target('sitename', '*') == ['doc1', 'subdir/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '*')\n"
                "called list_deletions() met args=([('/', 99), ('subdir', 99)], 'source')\n")
        assert testee.list_deletions_target('sitename', 'dirname') == ['dirname/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', 'dirname')\n"
                "called list_deletions() met args=([('dirname', 99)], 'source')\n")

    def test_apply_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2pg.apply_deletions_target
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            if args[1] == '':
                return [('/', 99)]
            if args[1] == '*':
                return [('/', 99), ('subdir', 99)]
            return [('dirname', 99)]
        def mock_apply_deletions(*args):
            """stub
            """
            print(f'called apply_deletions() met {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2')
            return [('x', 1, 'y', 99), ('x', 1, 'y', 98)], retval
        monkeypatch.setattr(testee, 'get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'apply_deletions', mock_apply_deletions)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.apply_deletions_target('sitename', '')
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '')\n"
                "called apply_deletions() met args=([('/', 99)], 'source')\n"
                "execute SQL: `update doc_stats set source_docid = %s, source_updated = %s,"
                " source_deleted = %s, target_docid = %s, target_deleted = %s where id = %s;`\n"
                "  with: `('x', 'x', 'x', 1, 'y', 99)`, `('x', 'x', 'x', 1, 'y', 98)`\n"
                "called commit() on connection\n"
                "called close()\n")
        testee.apply_deletions_target('sitename', '*')
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '*')\n"
                "called apply_deletions() met args=([('/', 99), ('subdir', 99)], 'source')\n"
                "execute SQL: `update doc_stats set source_docid = %s, source_updated = %s,"
                " source_deleted = %s, target_docid = %s, target_deleted = %s where id = %s;`\n"
                "  with: `('x', 'x', 'x', 1, 'y', 99)`, `('x', 'x', 'x', 1, 'y', 98)`\n"
                "called commit() on connection\n"
                "called close()\n")
        testee.apply_deletions_target('sitename', 'dirname')
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', 'dirname')\n"
                "called apply_deletions() met args=([('dirname', 99)], 'source')\n"
                "execute SQL: `update doc_stats set source_docid = %s, source_updated = %s,"
                " source_deleted = %s, target_docid = %s, target_deleted = %s where id = %s;`\n"
                "  with: `('x', 'x', 'x', 1, 'y', 99)`, `('x', 'x', 'x', 1, 'y', 98)`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_update_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.update_mirror
        """
        def mock_site_id(*args):
            """stub
            """
            if counter == 1:
                return None
            return 9
        def mock_dir_id(*args):
            """stub
            """
            if counter <= 3:
                print(f'called get_dir_id() for `{args[1]}`')
            if counter == 2:
                return None
            return 99
        def mock_doc_ids(*args):
            """stub
            """
            if counter == 3:
                return None, 2, 3
            # elif counter == 4:
            #     return 1, 2, None
            return 1, 2, 3
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() with arg `{self}`')
        def mock_touch(self, *args):
            """stub
            """
            print(f'called touch() with arg `{self}`')
        def mock_save_to(*args):
            """stub
            """
            print(f'called save_to() with args `{args[0]}` `{args[1]}`')
        with pytest.raises(AttributeError):
            testee.update_mirror('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            testee.update_mirror('site_name', 'docname', '')
        counter = 1
        monkeypatch.setattr(testee, '_get_site_id', mock_site_id)
        with pytest.raises(FileNotFoundError):
            testee.update_mirror('site_name', 'doc_name', 'contents')
        counter += 1
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        with pytest.raises(FileNotFoundError):
            testee.update_mirror('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        monkeypatch.setattr(testee, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            testee.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'

        counter += 1
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        testee.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n'
                f'called mkdir() with arg `{testee.WEBROOT}/site_name`\n'
                f'called save_to() with args `{testee.WEBROOT}/site_name/doc_name.html`'
                ' `data`\n')
        counter += 1
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        testee.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n'
                f'called mkdir() with arg `{testee.WEBROOT}/site_name`\n'
                f'called touch() with arg `{testee.WEBROOT}/site_name/doc_name.html`\n'
                f'called save_to() with args `{testee.WEBROOT}/site_name/doc_name.html`'
                ' `data`\n')
        counter += 1
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        testee.update_mirror('site_name', 'doc_name', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n'
                f'called save_to() with args `{testee.WEBROOT}/site_name/dirname/doc_name.html`'
                ' `data`\n')
        testee.update_mirror('site_name', 'doc_name.html', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n'
                '  with: `now`, `1`\n'
                'called commit() on connection\n'
                'called close()\n'
                f'called save_to() with args `{testee.WEBROOT}/site_name/dirname/doc_name.html`'
                ' `data`\n')

        counter += 1
        testee.update_mirror('site_name', 'doc_name', 'contents')  # dry_run=True
        assert capsys.readouterr().out == ''

    def test_list_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.list_deletions_mirror
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            if args[1] == '':
                return [('/', 99)]
            if args[1] == '*':
                return [('/', 99), ('subdir', 99)]
            return [('dirname', 99)]
        def mock_list_deletions(*args):
            """stub
            """
            print(f'called list_deletions() met {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2')
            return retval
        monkeypatch.setattr(testee, 'get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'list_deletions', mock_list_deletions)
        assert testee.list_deletions_mirror('sitename', '') == ['doc1']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '')\n"
                "called list_deletions() met args=([('/', 99)], 'target')\n")
        assert testee.list_deletions_mirror('sitename', '*') == ['doc1', 'subdir/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '*')\n"
                "called list_deletions() met args=([('/', 99), ('subdir', 99)], 'target')\n")
        assert testee.list_deletions_mirror('sitename', 'dirname') == ['dirname/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', 'dirname')\n"
                "called list_deletions() met args=([('dirname', 99)], 'target')\n")

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.apply_deletions_mirror
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            if args[1] == '':
                return [('/', 99)]
            if args[1] == '*':
                return [('/', 99), ('subdir', 99)]
            return [('dirname', 99)]
        def mock_apply_deletions(*args):
            """stub
            """
            print(f'called apply_deletions() met {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2.html')
            return [], retval
        def mock_unlink(self, *args):
            """stub
            """
            print(f'called unlink() with argument `{self}`')
        monkeypatch.setattr(testee, 'get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'apply_deletions', mock_apply_deletions)
        # monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        destloc = f'{testee.WEBROOT}/sitename'
        assert testee.apply_deletions_mirror('sitename', '') == ['doc1']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '')\n"
                "called apply_deletions() met args=([('/', 99)], 'target')\n")
        assert testee.apply_deletions_mirror('sitename', 'dirname') == ['dirname/doc2.html']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', 'dirname')\n"
                "called apply_deletions() met args=([('dirname', 99)], 'target')\n")
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        assert testee.apply_deletions_mirror('sitename', '*') == ['doc1', 'subdir/doc2.html']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename', '*')\n"
                "called apply_deletions() met args=([('/', 99), ('subdir', 99)], 'target')\n"
                f'called unlink() with argument `{destloc}/doc1.html`\n'
                f'called unlink() with argument `{destloc}/subdir/doc2.html`\n')

    def test_get_dirlist_for_site(self, monkeypatch):
        """unittest for docs2pg.get_dirlist_for_site
        """
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError) as excinfo:
            testee.get_dirlist_for_site('sitename', '')
            assert 'no_site' in excinfo.value
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 15)
        monkeypatch.setattr(testee, 'list_dirs', lambda x, y: ['subdir'])
        monkeypatch.setattr(testee, '_get_dir_id', lambda x, y: None)
        with pytest.raises(FileNotFoundError) as excinfo:
            testee.get_dirlist_for_site('sitename', '')
            assert 'no_subdir' in excinfo.value
        monkeypatch.setattr(testee, '_get_dir_id', lambda x, y: 99)
        assert testee.get_dirlist_for_site('sitename', '') == [('/', 99)]
        assert testee.get_dirlist_for_site('sitename', '*') == [('/', 99), ('subdir', 99)]
        assert testee.get_dirlist_for_site('sitename', 'dirname') == [('dirname', 99)]

    def test_list_deletions(self, monkeypatch, capsys):
        """unittest for docs2pg.list_deletions
        """
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'id': 1, 'docname': 'xxx', 'target_docid': 11},
                                {'id': 2, 'docname': 'yyy.html', 'target_docid': 12}])
        assert testee.list_deletions([], 'x') == []
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.list_deletions([('/', 1), ('subdir', 2)], 'stage') == sorted(['xxx', 'yyy.html',
                'subdir/xxx', 'subdir/yyy.html'])
        assert capsys.readouterr().out == (
                'execute SQL: `select id, docname, target_docid from doc_stats'
                ' where dir_id = %s and stage_deleted = %s;`\n'
                '  with: `1`, `True`\n'
                'execute SQL: `select id, docname, target_docid from doc_stats'
                ' where dir_id = %s and stage_deleted = %s;`\n'
                '  with: `2`, `True`\n'
                "called commit() on connection\n"
                "called close()\n")

    def test_apply_deletions(self, monkeypatch, capsys):
        """unittest for docs2pg.apply_deletions
        """
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'id': 1, 'docname': 'xxx', 'target_docid': 11},
                                {'id': 2, 'docname': 'yyy.html', 'target_docid': 12}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.apply_deletions([('/', 1)], 'source') == (([(None, 1, True, 1),
            (None, 1, True, 2)], ['xxx', 'yyy.html']))
        assert capsys.readouterr().out == (
                'execute SQL: `select id, docname, target_docid from doc_stats'
                ' where dir_id = %s and source_deleted = %s;`\n'
                '  with: `1`, `True`\n'
                'execute SQL: `delete from documents where id = %s;`\n'
                '  with: `(11,)`, `(12,)`\n'
                'called commit() on connection\n'
                'called close()\n')
        assert testee.apply_deletions([('subdir', 2)], 'other') == (([(None, 1, True, 1),
            (None, 1, True, 2)], ['subdir/xxx', 'subdir/yyy.html']))
        assert capsys.readouterr().out == (
                'execute SQL: `select id, docname, target_docid from doc_stats'
                ' where dir_id = %s and other_deleted = %s;`\n'
                '  with: `2`, `True`\n'
                'execute SQL: `delete from doc_stats where id = %s;`\n'
                '  with: `(1,)`, `(2,)`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_doc_stats(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_stats
        """
        def mock_site_id(*args):
            """stub
            """
            if counter == 1:
                return None
            return 9
        def mock_dir_id(*args):
            """stub
            """
            if counter <= 3:
                print(f'called get_dir_id() for `{args[1]}`')
            if counter == 2:
                return None
            return 99
        def mock_doc_ids(*args):
            """stub
            """
            if counter == 3:
                return None, 2, 3
            # elif counter == 4:
            #     return 1, 2, None
            return 1, 2, 3
        def mock_stats(*args):
            """stub
            """
            return args[0]
        counter = 1
        monkeypatch.setattr(testee, '_get_site_id', mock_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_doc_ids)
        with pytest.raises(FileNotFoundError):
            testee.get_doc_stats('site_name', 'docname')
        counter += 1
        with pytest.raises(FileNotFoundError):
            testee.get_doc_stats('site_name', 'docname', 'dirname')
        assert capsys.readouterr().out == 'called get_dir_id() for `dirname`\n'
        counter += 1
        with pytest.raises(FileNotFoundError):
            testee.get_doc_stats('site_name', 'doc_name')
        assert capsys.readouterr().out == 'called get_dir_id() for `/`\n'
        counter += 1
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'source_updated': 1,
                                                               'target_updated': 2,
                                                               'mirror_updated': 3})
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee, '_get_stats', mock_stats)
        assert list(testee.get_doc_stats('site_name', 'docname')) == [1, 2, 3]
        assert capsys.readouterr().out == (
                'execute SQL: `select source_updated, source_deleted, target_updated,'
                ' target_deleted, mirror_updated from doc_stats where id = %s;`\n'
                '  with: `1`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_all_doc_stats(self, monkeypatch, capsys):
        """unittest for docs2pg.get_all_doc_stats
        """
        counter = 0
        def mock_iter(*args):
            """stub
            """
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'dirname': '/'}, {'dirname': 'subdir'}])
            return (x for x in [{'docname': 'x', 'source_updated': 1, 'target_updated': 2,
                                 'mirror_updated': 3, 'source_deleted': None,
                                 'target_deleted': None, 'dirname': '/'},
                                {'docname': 'y', 'source_updated': 1, 'target_updated': 4,
                                 'mirror_updated': 5, 'source_deleted': None,
                                 'target_deleted': None, 'dirname': '/'},
                                {'docname': 'y', 'source_updated': 1, 'target_updated': 4,
                                 'mirror_updated': 5, 'source_deleted': 8,
                                 'target_deleted': None, 'dirname': '/'},
                                {'docname': 'y', 'source_updated': 1, 'target_updated': 4,
                                 'mirror_updated': 5, 'source_deleted': 8,
                                 'target_deleted': 9, 'dirname': '/'},
                                {'docname': 'a', 'source_updated': 2, 'target_updated': 4,
                                 'mirror_updated': 5, 'source_deleted': None,
                                 'target_deleted': None, 'dirname': 'subdir'},
                                {'docname': 'b', 'source_updated': 3, 'target_updated': 4,
                                 'mirror_updated': 6, 'source_deleted': None,
                                 'target_deleted': None, 'dirname': 'subdir'}])
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.get_all_doc_stats('site_name')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 99)
        monkeypatch.setattr(testee, '_get_all_dir_ids', lambda x: [1, 2, 3])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee.get_all_doc_stats('site_name') == [
                ('/', [('x', testee.Stats(src=1, dest=2, mirror=3)),
                       ('y', testee.Stats(src=1, dest=4, mirror=5)),
                       ('y', testee.Stats(src='[deleted]', dest=4, mirror=5)),
                       ('y', testee.Stats(src='[deleted]', dest='[deleted]', mirror=5))]),
                ('subdir', [('a', testee.Stats(src=2, dest=4, mirror=5)),
                            ('b', testee.Stats(src=3, dest=4, mirror=6))])]

        assert capsys.readouterr().out == (
                'execute SQL: `select dirname from directories where site_id = %s;`\n'
                '  with: `99`\n'
                'execute SQL: `select dirname, docname, source_updated, target_updated,'
                ' mirror_updated, source_deleted, target_deleted from doc_stats, directories'
                ' where dir_id = directories.id and dir_id = any(%s);`\n'
                '  with: `[1, 2, 3]`\n'
                'called commit() on connection\n'
                'called close()\n')
