"""unittests for ./app/docs2pg.py
"""
import datetime
import pytest
import app.docs2pg as testee


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
    def now(*args):
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


def mock_get_no_site_id(*args):
    "stub"
    print('called _get_site_id with args', args)
    return None


def mock_get_site_id(*args):
    "stub"
    print('called _get_site_id with args', args)
    return 'site_id'


def mock_get_no_dir_id(*args):
    "stub"
    print('called _get_dir_id with args', args)
    return None


def mock_get_dir_id(*args):
    "stub"
    print('called _get_dir_id with args', args)
    return 'dir_id'


def mock_get_ids(*args):
    "stub: no document"
    print('called _get_doc_ids with args', args)
    return None, None, None


def mock_get_ids_2(*args):
    "stub: no source"
    print('called _get_doc_ids with args', args)
    return 1, None, 3


def mock_get_ids_3(*args):
    "stub: no target"
    print('called _get_doc_ids with args', args)
    return 1, 2, None


def mock_get_ids_4(*args):
    "stub: all there"
    print('called _get_doc_ids with args', args)
    return 1, 2, 3


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
        def mock_get_tpl(*args):
            print("called _get_templates_for_site with args", args)
            return {'tpl1': 'text tpl1', 'tpl2': 'text tpl2'}
        def mock_get_map(*args):
            print('called _fetch_dirmap with args', args)
            return {2: '/', 3: 'subdir'}
        def mock_get_ids(*args):
            print("called _get_all_dir_ids with args", args)
            return (x for x in [{'id': 2, 'dirname': '/'}, {'id': 3, 'dirname': 'subdir'},
                                {'id': 4, 'dirname': 'deleted_dir'}])
        def mock_get_stats(*args):
            print("called _fetch_site_data with args", args)
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
        def mock_get_docs(*args):
            print('called _fetch_doc_data with args', args)
            result = []
            for row in [{'id': 4, 'currtext': '/doc1 src text', 'previous': ''},
                        {'id': 5, 'currtext': '/doc1 dest text', 'previous': 'old txt'},
                        {'id': 6, 'currtext': 'subdir/doc2 src', 'previous': 'old'},
                        {'id': 7, 'currtext': 'subdir/doc2 dest', 'previous': ''}]:
                result.append({'_id': args[0][row['id']], 'current': row['currtext'],
                     'previous': row['previous']})
            return result
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        with pytest.raises(FileNotFoundError):
            testee.list_site_data('testsite')
        monkeypatch.setattr(testee, '_get_site_id', lambda x: 1)
        monkeypatch.setattr(testee, '_get_settings', lambda x: {'sett1': 'val1', 'sett2': 'val2'})
        monkeypatch.setattr(testee, '_get_templates_for_site', mock_get_tpl)
        monkeypatch.setattr(testee, '_get_all_dir_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_fetch_dirmap', mock_get_map)
        monkeypatch.setattr(testee, '_fetch_site_data', mock_get_stats)
        monkeypatch.setattr(testee, '_fetch_doc_data', mock_get_docs)
        assert testee.list_site_data('sitename') == ({'_id': 1, 'name': 'sitename',
            'settings': {'sett1': 'val1', 'sett2': 'val2'},
            'docs': {'/': {'doc0': {},
                           'doc1': {'src': {'docid': 4, 'updated': 4, 'deleted': False},
                                    'dest': {'docid': 5, 'updated': 5, 'deleted': False},
                                    'mirror': {'updated': 5}}},
            'subdir': {'doc2': {'src': {'docid': 6, 'updated': 6, 'deleted': True},
                                'dest': {'docid': 7, 'updated': 7, 'deleted': True},
                                'mirror': {'updated': 7}}}},
            'templates': {'tpl1': 'text tpl1', 'tpl2': 'text tpl2'}}, [
            {'_id': ('doc1', 'dest'), 'current': '/doc1 dest text', 'previous': 'old txt'},
            {'_id': ('doc1', 'src'), 'current': '/doc1 src text', 'previous': ''},
            {'_id': ('subdir/doc2', 'dest'), 'current': 'subdir/doc2 dest', 'previous': ''},
            {'_id': ('subdir/doc2', 'src'), 'current': 'subdir/doc2 src', 'previous': 'old'}])
        assert capsys.readouterr().out == (
                "called _get_templates_for_site with args (1,)\n"
                "called _fetch_dirmap with args (1,)\n"
                "called _get_all_dir_ids with args (1,)\n"
                "called _fetch_site_data with args ([2, 3],)\n"
                "called _fetch_doc_data with args ({4: ('doc1', 'src'), 5: ('doc1', 'dest'),"
                " None: ('doc0', 'dest'), 6: ('subdir/doc2', 'src'),"
                " 7: ('subdir/doc2', 'dest')},)\n")

    def test_clear_site_data(self, monkeypatch, capsys):
        """unittest for docs2pg.clear_site_data
        """
        def mock_rmtree_err(*args):
            """stub
            """
            print(f'called rmtree() with arg `{args[0]}`')
            raise FileNotFoundError
        def mock_rmtree_ok(*args):
            """stub
            """
            print(f'called rmtree() with arg `{args[0]}`')
        def mock_get_all(*args):
            print('called _get_all_dir_ids with args', args)
            return [2, 3]
        def mock_delete(*args):
            print('called _delete_dir_data with args', args)
        monkeypatch.setattr(testee, '_get_site_id', lambda x: None)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        testee.clear_site_data('site_name')
        assert capsys.readouterr().out == ''

        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_err)
        testee.clear_site_data('site_name')
        assert capsys.readouterr().out == (
                f'called rmtree() with arg `{testee.WEBROOT / 'site_name'}`\n')

        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_all_dir_ids', mock_get_all)
        monkeypatch.setattr(testee, '_delete_dir_data', mock_delete)
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_ok)
        testee.clear_site_data('site_name')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_all_dir_ids with args ('site_id',)\n"
                "called _delete_dir_data with args ('site_id', [2, 3])\n"
                f'called rmtree() with arg `{testee.WEBROOT / 'site_name'}`\n')


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
        def mock_make(*args):
            print('called _make_site with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_make_site', mock_make)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        with pytest.raises(FileExistsError) as e:
            testee.create_new_site('site_name')
        assert str(e.value) == 'site_name_taken'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        with pytest.raises(FileExistsError) as e:
            testee.create_new_site('site_name')
        assert str(e.value) == 'site_name_taken'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        testee.create_new_site('site_name')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _make_site with args ('site_name',)\n"
                'called mkdir() for `/home/albert/projects/rst2html/rst2html-data/site_name`\n')

    def test_rename_site(self, monkeypatch, capsys):
        """unittest for docs2pg.rename_site
        """
        def mock_rename(self, *args, **kwargs):
            """stub
            """
            print(f'called rename() for `{self}` to `{args[0]}`')
        def mock_do(*args):
            print('called _do_renames with args', args)
        monkeypatch.setattr(testee, '_do_rename', mock_do)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        with pytest.raises(FileNotFoundError):
            testee.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename)
        testee.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _do_renames with args ('site_id', 'newname')\n"
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
            print('called _get_settings with args', args)
            counter += 1
            if counter == 1:
                return {'css': ['x', 'y'], 'nam': 'val', 'nam0': 'val0'}
            return 'new site settings'
        def mock_get_settings_2(*args):
            """stub
            """
            nonlocal counter
            print('called _get_settings with args', args)
            counter += 1
            if counter == 1:
                return {'nam': 'val', 'nam0': 'val0'}
            return 'new site settings'
        def mock_modify(*args):
            print('called _modify_settings with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_settings', mock_get_settings)
        monkeypatch.setattr(testee, '_modify_settings', mock_modify)
        counter = 0
        assert testee.update_settings('site_name', {'nam': 'newval', 'nam2': 'val2',
                                                    'css': ['q', 'r']}) == 'new site settings'
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_settings with args ('site_id',)\n"
                "called _modify_settings with args ('site_id',"
                " {'css': 'x;y', 'nam': 'val', 'nam0': 'val0'},"
                " {'nam': 'newval', 'nam2': 'val2', 'css': 'q;r'})\n"
                "called _get_settings with args ('site_id',)\n")
        monkeypatch.setattr(testee, '_get_settings', mock_get_settings_2)
        counter = 0
        assert testee.update_settings('site_name', {'nam': 'val', 'nam2': 'val2'}) == (
                'new site settings')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_settings with args ('site_id',)\n"
                "called _modify_settings with args ('site_id',"
                " {'nam': 'val', 'nam0': 'val0'},"
                " {'nam': 'val', 'nam2': 'val2'})\n"
                "called _get_settings with args ('site_id',)\n")

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
        def mock_list(*args):
            print('called _get_dirlist with args', args)
            return ['subdir']
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        with pytest.raises(FileNotFoundError):
            testee.list_dirs('site_name')
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_dirlist', mock_list)
        # monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        # monkeypatch.setattr(testee, 'conn', MockConn())
        with pytest.raises(RuntimeError):
            testee.list_dirs('site_name', 'x')
        assert testee.list_dirs('site_name') == testee.list_dirs('site_name', 'src')
        capsys.readouterr()  # flush capture
        assert testee.list_dirs('site_name') == ['subdir']
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dirlist with args ('site_id', '')\n")

    def test_create_new_dir(self, monkeypatch, capsys):
        """unittest for docs2pg.create_new_dir
        """
        def mock_list(*args):
            print('called _get_dirlist with args', args)
            return ['subdir']
        def mock_list_2(*args):
            print('called _get_dirlist with args', args)
            return []
        def mock_make(*args):
            print('called _make_dir with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        with pytest.raises(FileNotFoundError):
            testee.create_new_dir('site_name', 'subdir')
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(RuntimeError):
            testee.create_new_dir('site_name', '/')
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, 'list_dirs', mock_list)
        with pytest.raises(FileExistsError):
            testee.create_new_dir('site_name', 'subdir')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dirlist with args ('site_name',)\n")
        monkeypatch.setattr(testee, 'list_dirs', mock_list_2)
        monkeypatch.setattr(testee, '_make_dir', mock_make)
        testee.create_new_dir('site_name', 'subdir')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dirlist with args ('site_name',)\n"
                                           "called _make_dir with args ('site_id', 'subdir')\n")

    def test_rename_dir(self, monkeypatch, capsys):
        """unittest for docs2pg.rename_dir
        """
        def mock_get_siteid(*args):
            print('called _get_site_id with args', args)
            return 'site_id'
        def mock_get_dirid(*args):
            print('called _get_dir_id with args', args)
            return 'dir_id'
        def mock_rename(*args):
            print('called _do_rename_dir with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_siteid)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dirid)
        monkeypatch.setattr(testee, '_do_rename_dir', mock_rename)
        assert testee.rename_dir('testsite', 'olddir', 'newdir') == ''
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('testsite',)\n"
                "called _get_dir_id with args ('site_id', 'olddir')\n"
                "called _do_rename_dir with args ('dir_id', 'newdir')\n")

    def test_remove_dir(self):
        """unittest for docs2pg.remove_dir
        """
        with pytest.raises(NotImplementedError):
            testee.remove_dir('site_name', 'directory')


class TestDocLevelTemplates:
    """unittests for document level api functions
    """
    def test_list_templates(self, monkeypatch, capsys):
        """unittest for docs2pg.list_templates
        """
        def mock_get(*args):
            print('called _get_tpllist with args', args)
            return ['tpl1', 'tpl2']
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_tpllist', mock_get)
        assert testee.list_templates('site_name') == ['tpl1', 'tpl2']
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_tpllist with args ('site_id',)\n")

    def test_read_template(self, monkeypatch, capsys):
        """unittest for docs2pg.read_template
        """
        def mock_get(*args):
            print('called _get_template with args', args)
            return 'template'
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_template', mock_get)
        assert testee.read_template('site_name', 'doc_name') == 'template'
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_template with args ('site_id', 'doc_name')\n")

    def test_write_template(self, monkeypatch, capsys):
        """unittest for docs2pg.write_template
        """
        def mock_put(*args):
            print('called _put_template with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_put_template', mock_put)
        testee.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _put_template with args ('site_id', 'doc_name', 'data')\n")

    def test_rename_template(self, monkeypatch, capsys):
        """unittest for docs2pg.rename_template
        """
        def mock_get_siteid(*args):
            print('called _get_site_id with args', args)
            return 'site_id'
        def mock_get_templateid(*args):
            print('called _get_template_id with args', args)
            return 'tpl_id'
        def mock_rename_template(*args):
            print('called _do_rename_template with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_siteid)
        monkeypatch.setattr(testee, '_get_template_id', mock_get_templateid)
        monkeypatch.setattr(testee, '_do_rename_template', mock_rename_template)
        assert testee.rename_template('site_name', 'oldname', 'newname') == ''
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_template_id with args ('site_id', 'oldname')\n"
                "called _do_rename_template with args ('site_id', 'tpl_id', 'newname')\n")

    def test_remove_template(self, monkeypatch, capsys):
        """unittest for docs2pg.remove_template
        """
        def mock_get_siteid(*args):
            print('called _get_site_id with args', args)
            return 'site_id'
        def mock_get_templateid(*args):
            print('called _get_template_id with args', args)
            return 'tpl_id'
        def mock_delete_template(*args):
            print('called _do_delete_template with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_siteid)
        monkeypatch.setattr(testee, '_get_template_id', mock_get_templateid)
        monkeypatch.setattr(testee, '_do_delete_template', mock_delete_template)
        assert testee.remove_template('site_name', 'tplname') == ''
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_template_id with args ('site_id', 'tplname')\n"
                "called _do_delete_template with args ('site_id', 'tpl_id')\n")


class TestDocLevel:
    """unittests for document level api functions
    """
    def test_list_docs(self, monkeypatch, capsys):
        """unittest for docs2pg.list_docs
        """
        def mock_get(*args):
            print('called _get_doclist with args', args)
            return ['doc1', 'doc2']
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doclist', mock_get)
        with pytest.raises(FileNotFoundError) as e:
            testee.list_docs('site_name')
        assert str(e.value) == 'no_site'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.list_docs('site_name')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        assert testee.list_docs('site_name') == ['doc1', 'doc2']
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doclist with args ('dir_id', '', False)\n")
        assert testee.list_docs('site_name', 'doctype', 'dir_name') == ['doc1', 'doc2']
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'dir_name')\n"
                "called _get_doclist with args ('dir_id', 'doctype', False)\n")

    def test_create_new_doc(self, monkeypatch, capsys):
        """unittest for docs2pg.create_new_doc
        """
        def mock_get(*args):
            print('called _get_docs_in_dir with args', args)
            return 'doc_name'
        def mock_add(*args):
            print('called _add_doc with args', args)
            return 'new_docid'
        def mock_dts(*args):
            print('called _add_dts with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_docs_in_dir', mock_get)
        monkeypatch.setattr(testee, '_add_doc', mock_add)
        monkeypatch.setattr(testee, '_add_dts', mock_dts)
        with pytest.raises(AttributeError)as e:
            testee.create_new_doc('site_name', '')
        assert str(e.value) == 'no_name'
        assert capsys.readouterr().out == ''

        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(AttributeError) as e:
            testee.create_new_doc('site_name', '')
        assert str(e.value) == 'no_name'
        assert capsys.readouterr().out == ''

        with pytest.raises(FileNotFoundError) as e:
            testee.create_new_doc('site_name', 'doc_name')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.create_new_doc('site_name', 'doc_name', 'subdir')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'subdir')\n")

        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileExistsError) as e:
            testee.create_new_doc('site_name', 'doc_name')
        assert str(e.value) == ''
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_docs_in_dir with args ('dir_id',)\n")
        with pytest.raises(FileExistsError) as e:
            testee.create_new_doc('site_name', 'doc_name', 'subdir')
        assert str(e.value) == ''
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'subdir')\n"
                                           "called _get_docs_in_dir with args ('dir_id',)\n")

        testee.create_new_doc('site_name', 'docname')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_docs_in_dir with args ('dir_id',)\n"
                "called _add_doc with args ()\n"
                "called _add_dts with args ('dir_id', 'docname', 'new_docid')\n")
        testee.create_new_doc('site_name', 'docname', 'subdir')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'subdir')\n"
                "called _get_docs_in_dir with args ('dir_id',)\n"
                "called _add_doc with args ()\n"
                "called _add_dts with args ('dir_id', 'docname', 'new_docid')\n")

    def test_get_doc_contents(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_contents
        """
        def mock_fetch(*args):
            print('called _fetch_doc_contents with args', args)
            return 'stuff'
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_fetch_doc_contents', mock_fetch)
        with pytest.raises(AttributeError) as e:
            testee.get_doc_contents('site_name', '')
        assert str(e.value) == 'no_name'
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_contents('site_name', 'doc_name')
        assert str(e.value) == "Document 'doc_name' not found in collection"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        # monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_2)
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_contents('site_name', 'doc_name', 'src')
        assert str(e.value) == "Document 'doc_name' not found in collection"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_2)
        # assert testee.get_doc_contents('site_name', 'doc_name') == 'stuff'
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_contents('site_name', 'doc_name')
        assert str(e.value) == "src_file_missing"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        # assert testee.get_doc_contents('site_name', 'doc_name', 'src') == 'stuff'
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_contents('site_name', 'doc_name', 'src')
        assert str(e.value) == "src_file_missing"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_3)
        assert testee.get_doc_contents('site_name', 'doc_name') == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (2, False)\n")
        assert testee.get_doc_contents('site_name', 'doc_name', directory='subdir') == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'subdir')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (2, False)\n")
        assert testee.get_doc_contents('site_name', 'doc_name', previous=True) == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (2, True)\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_contents('site_name', 'doc_name', 'dest')
        assert str(e.value) == "html_file_missing"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_4)
        assert testee.get_doc_contents('site_name', 'doc_name', 'dest') == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (3, False)\n")
        assert testee.get_doc_contents('site_name', 'doc_name', 'dest', 'subdir') == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'subdir')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (3, False)\n")
        assert testee.get_doc_contents('site_name', 'doc_name', 'dest', previous=True) == 'stuff'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _fetch_doc_contents with args (3, True)\n")

    def test_update_rst(self, monkeypatch, capsys):
        """unittest for docs2pg.update_rst
        """
        def mock_get_text(*args):
            print('called _get_doc_text with args', args)
            return 'text'
        def mock_put(*args):
            print('called _put_update with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_get_doc_text', mock_get_text)
        monkeypatch.setattr(testee, '_put_update', mock_put)
        with pytest.raises(AttributeError) as e:
            testee.update_rst('site_name', '', 'contents')
        assert str(e.value) == "no_name"
        assert capsys.readouterr().out == ("")
        with pytest.raises(AttributeError) as e:
            testee.update_rst('site_name', 'doc_name', '')
        assert str(e.value) == "no_contents"
        assert capsys.readouterr().out == ("")
        with pytest.raises(FileNotFoundError) as e:
            testee.update_rst('site_name', 'doc_name', 'contents')
        assert str(e.value) == "no_site"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n")
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_rst('site_name', 'doc_name', 'contents')
        assert str(e.value) == "no_subdir"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.update_rst('site_name', 'doc_name', 'contents', 'dirname')
        assert str(e.value) == "no_subdir"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_rst('site_name', 'doc_name', 'contents')
        assert str(e.value) == "no_document"
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.update_rst('site_name', 'doc_name', 'contents', 'subdir')
        assert str(e.value) == "no_document"
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'subdir')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_4)
        testee.update_rst('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _get_doc_text with args (2,)\n"
                "called _put_update with args (1, 2, 'contents', 'text')\n")
        testee.update_rst('site_name', 'doc_name', 'contents', 'subdir')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'subdir')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _get_doc_text with args (2,)\n"
                "called _put_update with args (1, 2, 'contents', 'text')\n")

    def test_revert_rst(self, monkeypatch, capsys):
        """unittest for docs2pg.revert_rst
        """
        def mock_do(*args):
            print('called _do_revert with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_do_revert', mock_do)
        with pytest.raises(AttributeError) as e:
            testee.revert_rst('site_name', '')
        assert str(e.value) == "no_name"
        assert capsys.readouterr().out == ""
        with pytest.raises(FileNotFoundError) as e:
            testee.revert_rst('site_name', 'doc_name')
        assert str(e.value) == "no_site"
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        # with pytest.raises(FileNotFoundError) as e:
        #     testee.update_rst('site_name', 'doc_name', 'contents')
        # assert str(e.value) == "no_site"
        # assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n")
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        # with pytest.raises(FileNotFoundError) as e:
        #     testee.update_rst('site_name', 'doc_name', 'contents')
        # assert str(e.value) == "no_subdir"
        # assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
        #                                    "called _get_dir_id with args ('site_id', '/')\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.revert_rst('site_name', 'doc_name', 'dirname')
        assert str(e.value) == "no_subdir"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.revert_rst('site_name', 'doc_name')
        assert str(e.value) == "no_document"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_4)

        testee.revert_rst('site_name', 'doc_name')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _do_revert with args (2, 1)\n")

    def test_update_html(self, monkeypatch, capsys):
        """unittest for docs2pg.update_html
        """
        def mock_add(*args):
            print('called _add_doc with args', args)
            return 'new html_id'
        def mock_get(*args):
            print('called _get_doc_text with args', args)
            return 'oldtext'
        def mock_put(*args):
            print('called _put_html with args', args)
        monkeypatch.setattr(testee, '_add_doc', mock_add)
        monkeypatch.setattr(testee, '_get_doc_text', mock_get)
        monkeypatch.setattr(testee, '_put_html', mock_put)
        with pytest.raises(AttributeError) as e:
            testee.update_html('site_name', '', 'contents')
        assert str(e.value) == 'no_name'
        with pytest.raises(AttributeError) as e:
            testee.update_html('site_name', 'docname', '')
        assert str(e.value) == 'no_contents'
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_html('site_name', 'doc_name', 'contents')
        assert str(e.value) == 'no_site'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_html('site_name', 'doc_name', 'contents', 'dirname')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_html('site_name', 'doc_name', 'contents')
        assert str(e.value) == 'no_document'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")

        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_3)
        testee.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        testee.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _add_doc with args ()\n"
                "called _put_html with args (None, 'new html_id', 1, 'contents', '')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_4)
        testee.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        testee.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _get_doc_text with args (3,)\n"
                "called _put_html with args (3, None, 1, 'contents', 'oldtext')\n")

    def test_update_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.update_mirror
        """
        def mock_update(*args):
            print('called _update_mirror_dts with args', args)
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
            print('called save_to() with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_update_mirror_dts', mock_update)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        with pytest.raises(AttributeError) as e:
            testee.update_mirror('site_name', '', 'contents')
        assert str(e.value) == 'no_name'
        with pytest.raises(AttributeError) as e:
            testee.update_mirror('site_name', 'docname', '')
        assert str(e.value) == 'no_contents'
        with pytest.raises(FileNotFoundError) as e:
            testee.update_mirror('site_name', 'doc_name', 'contents')
        assert str(e.value) == 'no_site'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_mirror('site_name', 'doc_name', 'contents')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.update_mirror('site_name', 'doc_name', 'contents', 'dirname')
        assert str(e.value) == 'no_document'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_2)
        testee.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_3)
        testee.update_mirror('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_4)
        testee.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")

        testee.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _update_mirror_dts with args (1,)\n"
                f"called mkdir() with arg `{testee.WEBROOT}/site_name`\n"
                "called save_to() with args"
                f" ({testee.WEBROOT / 'site_name' / 'doc_name.html'!r}, 'data', True)\n")
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        testee.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _update_mirror_dts with args (1,)\n"
                f"called mkdir() with arg `{testee.WEBROOT}/site_name`\n"
                f"called touch() with arg `{testee.WEBROOT}/site_name/doc_name.html`\n"
                "called save_to() with args"
                f" ({testee.WEBROOT / 'site_name' / 'doc_name.html'!r}, 'data', False)\n")
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        testee.update_mirror('site_name', 'doc_name', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'dirname')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _update_mirror_dts with args (1,)\n"
                "called save_to() with args"
                f" ({testee.WEBROOT / 'site_name' / 'dirname' / 'doc_name.html'!r}, 'data', False)\n")
        testee.update_mirror('site_name', 'doc_name.html', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', 'dirname')\n"
                "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                "called _update_mirror_dts with args (1,)\n"
                "called save_to() with args"
                f" ({testee.WEBROOT / 'site_name' / 'dirname' / 'doc_name.html'!r}, 'data', False)\n")

    def test_get_doc_stats(self, monkeypatch, capsys):
        """unittest for docs2pg.get_doc_stats
        """
        def mock_get_dts(*args):
            print('called _get_datetimestamps with args', args)
            return f'dts_{args[0]}'
        def mock_stats(*args):
            """stub
            """
            print('called _get_stats with args', args)
            return args[0]
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_get_datetimestamps', mock_get_dts)
        monkeypatch.setattr(testee, '_get_stats', mock_stats)
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_stats('site_name', 'docname')
        assert str(e.value) == 'no_site'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_stats('site_name', 'docname')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_stats('site_name', 'docname', 'dirname')
        assert str(e.value) == 'no_subdir'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_dir_id)
        with pytest.raises(FileNotFoundError) as e:
            testee.get_doc_stats('site_name', 'doc_name')
        assert str(e.value) == 'no_document'
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_2)
        testee.get_doc_stats('site_name', 'doc_name')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _get_datetimestamps with args (1,)\n"
                                           "called _get_stats with args ('dts_1',)\n")

    def test_get_all_doc_stats(self, monkeypatch, capsys):
        """unittest for docs2pg.get_all_doc_stats
        """
        def mock_get_all(*args):
            print('called _get_all_site_id with args', args)
            return [1, 2, 3]
        def mock_get_stats(*args):
            print('called _get_stats_for_dirs with args', args)
            return ['dir', 'name'], [('x', 'y', 'z'), ('q', 'r', 's')]
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_all_dir_ids', mock_get_all)
        monkeypatch.setattr(testee, '_get_stats_for_dirs', mock_get_stats)
        with pytest.raises(FileNotFoundError) as e:
            testee.get_all_doc_stats('site_name')
        assert str(e.value) == 'no_site'
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        assert testee.get_all_doc_stats('site_name') == [('dir', []), ('name', [])]
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_all_site_id with args ('site_id',)\n"
                "called _get_stats_for_dirs with args ('site_id', [1, 2, 3])\n")

    def test_get_stats(self):  # non-Api
        """unittest for docs2pg.get_stats
        """
        assert testee._get_stats((1, None, 2, None, 3)) == testee.Stats(1, 2, 3)
        assert testee._get_stats((1, True, 2, True, 0)) == testee.Stats(
                '[deleted]', '[deleted]', datetime.datetime.min)
        assert testee._get_stats((0, None, 0, None, 0)) == testee.Stats(
                datetime.datetime.min, datetime.datetime.min, datetime.datetime.min)
        with pytest.raises(ValueError):
            assert testee._get_stats(()) == testee.Stats('', '', '')


class TestDocLevelDelete:
    """unittests for document level api functions
    """
    def test_mark_src_deleted(self, monkeypatch, capsys):
        """unittest for docs2pg.mark_src_deleted
        """
        def mock_dir_id(*args):
            """stub"""
            nonlocal dirid_counter
            print('called _get_dir_id with args', args)
            dirid_counter += 1
            if dirid_counter == 1:
                return 'dir_id'
            return None  # entry is een document, geen directory
        def mock_dir_id_2(*args):
            """stub"""
            nonlocal dirid_counter
            print('called _get_dir_id with args', args)
            dirid_counter += 1
            if dirid_counter == 1:
                return 'dir_id'
            return 'test_dir_id'
        def mock_mark_doc(doc_id):
            "stub"
            print(f"called _mark_doc_deleted with arg {doc_id}")
        def mock_mark_dir(*args):
            "stub"
            print('called _mark_dir_deleted with args', args)
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        monkeypatch.setattr(testee, '_get_dir_id', mock_get_no_dir_id)
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids)
        monkeypatch.setattr(testee, '_mark_doc_deleted', mock_mark_doc)
        monkeypatch.setattr(testee, '_mark_dir_deleted', mock_mark_dir)
        with pytest.raises(AttributeError):
            testee.mark_src_deleted('site_name', '')
        assert capsys.readouterr().out == ""
        with pytest.raises(FileNotFoundError) as exc:
            testee.mark_src_deleted('site_name', 'doc_name')
        assert str(exc.value) == "no_site"
        assert capsys.readouterr().out == "called _get_site_id with args ('site_name',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        with pytest.raises(FileNotFoundError) as exc:
            testee.mark_src_deleted('site_name', 'doc_name', 'dirname')
        assert str(exc.value) == "no_subdir"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', 'dirname')\n")

        with pytest.raises(FileNotFoundError) as exc:
            testee.mark_src_deleted('site_name', 'doc_name')
        assert str(exc.value) == "no_subdir"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n")

        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id)
        dirid_counter = 0
        with pytest.raises(FileNotFoundError) as exc:
            testee.mark_src_deleted('site_name', 'doc_name')
        assert str(exc.value) == "no_document"
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_dir_id with args ('site_id', 'doc_name')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n")
        dirid_counter = 0
        monkeypatch.setattr(testee, '_get_doc_ids', mock_get_ids_2)
        testee.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == ("called _get_site_id with args ('site_name',)\n"
                                           "called _get_dir_id with args ('site_id', '/')\n"
                                           "called _get_dir_id with args ('site_id', 'doc_name')\n"
                                           "called _get_doc_ids with args ('dir_id', 'doc_name')\n"
                                           "called _mark_doc_deleted with arg 1\n")
        monkeypatch.setattr(testee, '_get_dir_id', mock_dir_id_2)
        dirid_counter = 0
        testee.mark_src_deleted('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('site_name',)\n"
                "called _get_dir_id with args ('site_id', '/')\n"
                "called _get_dir_id with args ('site_id', 'doc_name')\n"
                "called _mark_dir_deleted with args ('test_dir_id',)\n")

    def test_list_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2pg.list_deletions_target
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() with {args=}')
            # if args[1] == '':
            #     return [('/', 99)]
            # if args[1] == '*':
            #     return [('/', 99), ('subdir', 99)]
            # return [('dirname', 99)]
            return [('/', 99), ('subdir', 99)]
        def mock_list_deletions(*args):
            """stub
            """
            print(f'called list_deletions() with {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2')
            return retval
        monkeypatch.setattr(testee, '_get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'list_deletions', mock_list_deletions)
        assert testee.list_deletions_target('sitename') == ['doc1', 'subdir/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() with args=('sitename',)\n"
                "called list_deletions() with args=([('/', 99), ('subdir', 99)], 'source')\n")

    def test_apply_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2pg.apply_deletions_target
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            # if args[1] == '':
            #     return [('/', 99)]
            # if args[1] == '*':
            #     return [('/', 99), ('subdir', 99)]
            # return [('dirname', 99)]
            return [('/', 99), ('subdir', 99)]
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
        monkeypatch.setattr(testee, '_get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'apply_deletions', mock_apply_deletions)
        testee.apply_deletions_target('sitename',)
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename',)\n"
                "called apply_deletions() met args=([('/', 99), ('subdir', 99)], 'source')\n")

    def test_list_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.list_deletions_mirror
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() met {args=}')
            # if args[1] == '':
            #     return [('/', 99)]
            # if args[1] == '*':
            #     return [('/', 99), ('subdir', 99)]
            # return [('dirname', 99)]
            return [('/', 99), ('subdir', 99)]
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
        monkeypatch.setattr(testee, '_get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'list_deletions', mock_list_deletions)
        assert testee.list_deletions_mirror('sitename') == ['doc1', 'subdir/doc2']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() met args=('sitename',)\n"
                "called list_deletions() met args=([('/', 99), ('subdir', 99)], 'target')\n")

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2pg.apply_deletions_mirror
        """
        def mock_get_dirlist(*args):
            """stub
            """
            print(f'called get_dirlist_for_site() with {args=}')
            # if args[1] == '':
            #     return [('/', 99)]
            # if args[1] == '*':
            #     return [('/', 99), ('subdir', 99)]
            # return [('dirname', 99)]
            return [('/', 99), ('subdir', 99)]
        def mock_apply_deletions(*args):
            """stub
            """
            print(f'called apply_deletions() with {args=}')
            return [], []
        def mock_apply_deletions_2(*args):
            """stub
            """
            print(f'called apply_deletions() with {args=}')
            retval = []
            for x, y in args[0]:
                if x == '/':
                    retval.append('doc1')
                else:
                    retval.append(f'{x}/doc2.html')
            retval.append('dir/')
            return [], retval
        def mock_is_dir(self, *args):
            print(f'called path.is_dir with args `{self}`', args)
            return self.name.endswith('dir')
        def mock_unlink(self, *args, **kwargs):
            """stub
            """
            print(f'called path.unlink with args `{self}`', args, kwargs)
        def mock_rmdir(self, *args):
            """stub
            """
            print(f'called path.rmdir with args `{self}`', args)
        monkeypatch.setattr(testee, '_get_dirlist_for_site', mock_get_dirlist)
        monkeypatch.setattr(testee, 'apply_deletions', mock_apply_deletions)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', mock_is_dir)
        monkeypatch.setattr(testee.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(testee.pathlib.Path, 'rmdir', mock_rmdir)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        destloc = f'{testee.WEBROOT}/sitename'
        assert testee.apply_deletions_mirror('sitename',) == []
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() with args=('sitename',)\n"
                "called apply_deletions() with args=([('/', 99), ('subdir', 99)], 'target')\n")
        monkeypatch.setattr(testee, 'apply_deletions', mock_apply_deletions_2)
        assert testee.apply_deletions_mirror('sitename',) == ['dir/', 'doc1', 'subdir/doc2.html']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() with args=('sitename',)\n"
                "called apply_deletions() with args=([('/', 99), ('subdir', 99)], 'target')\n"
                f'called path.is_dir with args `{destloc}/doc1` ()\n'
                f'called path.is_dir with args `{destloc}/subdir/doc2.html` ()\n'
                f'called path.is_dir with args `{destloc}/dir` ()\n')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        assert testee.apply_deletions_mirror('sitename',) == ['dir/', 'doc1', 'subdir/doc2.html']
        assert capsys.readouterr().out == (
                "called get_dirlist_for_site() with args=('sitename',)\n"
                "called apply_deletions() with args=([('/', 99), ('subdir', 99)], 'target')\n"
                f'called path.is_dir with args `{destloc}/doc1` ()\n'
                f'called path.unlink with args `{destloc}/doc1.html` () {{}}\n'
                "called path.unlink with args"
                f" `{destloc}/doc1.html.bak` () {{'missing_ok': True}}\n"
                f'called path.is_dir with args `{destloc}/subdir/doc2.html` ()\n'
                f'called path.unlink with args `{destloc}/subdir/doc2.html` () {{}}\n'
                "called path.unlink with args"
                f" `{destloc}/subdir/doc2.html.bak` () {{'missing_ok': True}}\n"
                f'called path.is_dir with args `{destloc}/dir` ()\n'
                f'called path.rmdir with args `{destloc}/dir` ()\n')

    def test_list_deletions(self, monkeypatch, capsys):   # non-Api
        """unittest for docs2pg.list_deletions
        """
        def mock_get(*args):
            print('called get_deletions with args', args)
            return [(1, 'xxx', 101), (2, 'yyy', 102)]
        monkeypatch.setattr(testee, 'get_deletions', mock_get)

        assert testee.list_deletions([], 'x') == []
        assert testee.list_deletions([('/', 1), ('subdir', 2)], 'stage') == sorted(
                ['xxx', 'yyy', 'subdir/xxx', 'subdir/yyy'])
        assert capsys.readouterr().out == (
                "called get_deletions with args (1, 'stage')\n"
                "called get_deletions with args (2, 'stage')\n")

    def test_apply_deletions(self, monkeypatch, capsys):  # non-Api
        """unittest for docs2pg.apply_deletions
        """
        def mock_get(*args):
            print('called get_deletions with args', args)
            return []
        def mock_get_2(*args):
            print('called get_deletions with args', args)
            return [(1, 'xxx', 101), (2, 'yyy', 102), (3, '', 103)]
        def mock_execute(*args):
            print('called execute_deletions with args', args)
        monkeypatch.setattr(testee, 'get_deletions', mock_get)
        monkeypatch.setattr(testee, 'execute_deletions', mock_execute)
        assert testee.apply_deletions([('/', 1)], 'source') == ([], [])
        assert capsys.readouterr().out == ("called get_deletions with args (1, 'source')\n")
        assert testee.apply_deletions([('subdir', 2)], 'other') == ([], [])
        assert capsys.readouterr().out == ("called get_deletions with args (2, 'other')\n")
        monkeypatch.setattr(testee, 'get_deletions', mock_get_2)
        assert testee.apply_deletions([('/', 1)], 'source') == ([], ['xxx', 'yyy', ''])
        assert capsys.readouterr().out == (
                "called get_deletions with args (1, 'source')\n"
                "called execute_deletions with args ('source', [(1, 101), (2, 102)], [3])\n")
        assert testee.apply_deletions([('subdir', 2)], 'other') == ([], ['subdir/xxx',
                                                                         'subdir/yyy',
                                                                         'subdir/'])
        assert capsys.readouterr().out == (
                "called get_deletions with args (2, 'other')\n"
                "called execute_deletions with args ('other', [1, 2], [(3, 103)])\n")


class TestNonApiFunctions:
    """unittests for functions outside of the dml API

    most of these do the database manipulation
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
        assert not testee._get_dir_id('site_id', 'dir_id')
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

    def test_get_dir_name(self, monkeypatch, capsys):
        """unittest for docs2pg.get_dir_name
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return {}
        def mock_fetchone_2(self, *args):
            """stub
            """
            return {'dirname': 'xxx'}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert not testee._get_dir_name('site_id', 'dir_id')
        assert capsys.readouterr().out == (
                "execute SQL: `select dirname from directories where site_id = %s and id = %s;`\n"
                "  with: `site_id`, `dir_id`\n"
                "called commit() on connection\n"
                "called close()\n")
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone_2)
        assert testee._get_dir_name('site_id', 'dir_id') == 'xxx'
        assert capsys.readouterr().out == (
                "execute SQL: `select dirname from directories where site_id = %s and id = %s;`\n"
                "  with: `site_id`, `dir_id`\n"
                "called commit() on connection\n"
                "called close()\n")

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

    def test_make_site(self, monkeypatch, capsys):
        "unittest for docs2pg._make_site"
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ({'id': 'q'}))
        testee._make_site('site_name')
        assert capsys.readouterr().out == (
                'execute SQL: `insert into sites (sitename) values (%s) returning id;`\n'
                '  with: `site_name`\n'
                'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)`\n'
                '  with: `q`, `/`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_make_dir(self, monkeypatch, capsys):
        "unittest for docs2pg._make_dir"
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ({'id': 'some_id'}))
        assert testee._make_dir('site_name', 'directory') == 'some_id'
        assert capsys.readouterr().out == (
                'execute SQL: `insert into directories (site_id, dirname) values (%s, %s)'
                ' returning id`\n'
                '  with: `site_name`, `directory`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_do_rename(self, monkeypatch, capsys):
        "unittest for docs2pg._do_rename"
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._do_rename('site_name', 'newname')
        assert capsys.readouterr().out == (
                'execute SQL: `update sites set sitename = %s where id = %s;`\n'
                '  with: `newname`, `site_name`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_do_rename_dir(self, monkeypatch, capsys):
        "unittest for docs2pg._do_rename_dir"
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._do_rename_dir('dir_id', 'newdir')
        assert capsys.readouterr().out == (
                'execute SQL: `update directories set dirname = %s where id = %s;`\n'
                "  with: `newdir`, `dir_id`\n"
                'called commit() on connection\n'
                'called close()\n')

    def test_modify_settings(self, monkeypatch, capsys):
        "unittest for docs2pg._modify_settings"
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._modify_settings('siteid', {}, {'nam': 'val', 'nam2': 'new', 'nam4': 'val4'})
        assert capsys.readouterr().out == (
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `siteid`, `nam`, `val`\n'
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `siteid`, `nam2`, `new`\n'
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `siteid`, `nam4`, `val4`\n'
                'called commit() on connection\n'
                'called close()\n')
        testee._modify_settings('siteid', {'nam': 'val', 'nam2': 'old', 'nam3': 'val3'},
                                {'nam': 'val', 'nam2': 'new', 'nam4': 'val4'})
        assert capsys.readouterr().out == (
                'execute SQL: `update site_settings set settval = %s'
                ' where site_id = %s and settname = %s`\n'
                '  with: `new`, `siteid`, `nam2`\n'
                'execute SQL: `delete from site_settings'
                ' where site_id = %s and settname = %s`\n'
                '  with: `siteid`, `nam3`\n'
                'execute SQL: `insert into site_settings (site_id, settname, settval)'
                ' values (%s, %s, %s)`\n'
                '  with: `siteid`, `nam4`, `val4`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_dirlist(self, monkeypatch, capsys):
        """unittest for docs2pg.list_dirs
        """
        counter = 0
        def mock_iter(self, *args):
            """stub
            """
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'id': 1, 'dirname': '/'},
                                    {'id': 2, 'dirname': 'subdir'},
                                    {'id': 3, 'dirname': 'subdir2'},
                                    {'id': 4, 'dirname': 'subdir3'}])
            return (x for x in [{'dir_id': 1, 'docname': 'xx', 'source_deleted': False,
                                 'target_docid': 3, 'target_deleted': False},
                                {'dir_id': 2, 'docname': 'xx', 'source_deleted': False,
                                 'target_docid': 4, 'target_deleted': False},
                                {'dir_id': 3, 'docname': 'xx', 'source_deleted': True,
                                 'target_docid': 5, 'target_deleted': False},
                                {'dir_id': 4, 'docname': 'xx', 'source_deleted': False,
                                 'target_docid': 6, 'target_deleted': True}])
        def mock_iter_2(self, *args):
            nonlocal counter
            counter += 1
            if counter == 1:
                return (x for x in [{'id': 1, 'dirname': '/'},
                                    {'id': 2, 'dirname': 'subdir'},
                                    {'id': 3, 'dirname': 'subdir2'},
                                    {'id': 4, 'dirname': 'subdir3'}])
            return (x for x in [{'dir_id': 1, 'docname': '', 'source_deleted': False,
                                 'target_docid': 3, 'target_deleted': False},
                                {'dir_id': 2, 'docname': '', 'source_deleted': True,
                                 'target_docid': 5, 'target_deleted': False},
                                {'dir_id': 3, 'docname': '', 'source_deleted': False,
                                 'target_docid': 6, 'target_deleted': True},
                                {'dir_id': 4, 'docname': '', 'source_deleted': True,
                                 'target_docid': 4, 'target_deleted': True}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._get_dirlist('site_name', '') == ['subdir', 'subdir2', 'subdir3']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._get_dirlist('site_name', 'src') == ['subdir', 'subdir2', 'subdir3']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._get_dirlist('site_name', 'dest') == ['subdir', 'subdir2', 'subdir3']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter_2)
        assert testee._get_dirlist('site_name', 'src') == ['subdir2']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        assert testee._get_dirlist('site_name', 'src') == ['subdir2']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        assert testee._get_dirlist('site_name', 'dest') == ['subdir']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')
        counter = 0
        assert testee._get_dirlist('site_name', 'dest') == ['subdir']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, dirname from directories where site_id = %s;`\n'
                '  with: `site_name`\n'
                'execute SQL: `select dir_id, docname, source_deleted, target_docid,'
                ' target_deleted from doc_stats where dir_id = any(%s);`\n'
                '  with: `[1, 2, 3, 4]`\ncalled commit() on connection\ncalled close()\n')

    def test_get_dirlist_for_site(self, monkeypatch, capsys):
        """unittest for docs2pg.get_dirlist_for_site
        """
        def mock_iter(self, *args):
            """stub
            """
            return (x for x in [{'id': 1, 'dirname': '/'},
                                {'id': 2, 'dirname': 'subdir'}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee, '_get_site_id', mock_get_no_site_id)
        with pytest.raises(FileNotFoundError) as excinfo:
            testee._get_dirlist_for_site('sitename')
            assert 'no_site' in excinfo.value
        assert capsys.readouterr().out == "called _get_site_id with args ('sitename',)\n"
        monkeypatch.setattr(testee, '_get_site_id', mock_get_site_id)
        assert testee._get_dirlist_for_site('sitename') == [('/', 1), ('subdir', 2)]
        assert capsys.readouterr().out == (
                "called _get_site_id with args ('sitename',)\n"
                "execute SQL: `select id, dirname from directories where site_id = %s;`\n"
                "  with: `site_id`\n"
                "called commit() on connection\ncalled close()\n")

    def test_get_doclist(self, monkeypatch, capsys):
        "unittest for docs2pg._get_doclist"
        def mock_iter(self, *args):
            """stub
            """
            if doctype in ('', 'src'):
                return (x for x in [{'docname': 'd4', 'source_docid': 4, 'source_deleted': False},
                                    {'docname': 'd5', 'source_docid': None, 'source_deleted': True}])
            if doctype == 'dest':
                return (x for x in [{'docname': 'd6', 'target_docid': 6, 'target_deleted': False},
                                    {'docname': 'd7', 'target_docid': 7, 'target_deleted': True}])
            # if doctype == 'mirror':
            return (x for x in [{'docname': 'd8', 'mirror_docid': 8, 'mirror_updated': False},
                                {'docname': 'd9', 'mirror_docid': 9, 'mirror_updated': True}])
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in []))
        monkeypatch.setattr(testee, 'conn', MockConn())
        capsysout = ('execute SQL: `select docname, source_docid, source_deleted, target_docid,'
                     ' target_deleted, mirror_updated from doc_stats where dir_id = %s;`\n'
                     '  with: `dir_id`\n'
                     'called commit() on connection\n'
                     'called close()\n')
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        doctype = ''
        assert testee._get_doclist('dir_id', doctype, False) == ['d4']
        assert capsys.readouterr().out == capsysout
        assert testee._get_doclist('dir_id', doctype, True) == []
        assert capsys.readouterr().out == capsysout
        doctype = 'src'
        assert testee._get_doclist('dir_id', doctype, False) == ['d4']
        assert capsys.readouterr().out == capsysout
        assert testee._get_doclist('dir_id', doctype, True) == []
        assert capsys.readouterr().out == capsysout
        doctype = 'dest'
        assert testee._get_doclist('dir_id', doctype, False) == ['d6']
        assert capsys.readouterr().out == capsysout
        assert testee._get_doclist('dir_id', doctype, True) == ['d7']
        assert capsys.readouterr().out == capsysout
        doctype = 'mirror'
        assert testee._get_doclist('dir_id', doctype, True) == []
        assert capsys.readouterr().out == capsysout
        assert testee._get_doclist('dir_id', doctype, False) == ['d9']
        assert capsys.readouterr().out == capsysout

    def test_get_tpllist(self, monkeypatch, capsys):
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'id': 1, 'name': 'tpl1'}, {'id': 2, 'name': 'tpl2'}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._get_tpllist('site_id') == ['tpl1', 'tpl2']
        assert capsys.readouterr().out == (
                'execute SQL: `select id, name from templates where site_id = %s;`\n'
                '  with: `site_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_template(self, monkeypatch, capsys):
        "unittest for docs2pg._get_template"
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'text': 'contents'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._get_template('site_id', 'doc_name')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `site_id`, `doc_name`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_templates_for_site(self, monkeypatch, capsys):
        "unittest for docs2pg._get_templates_for_site"
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'name': 'tpl1', 'text': 'xxx'}, {'name': 'tpl2', 'text': 'yyy'}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._get_templates_for_site('site_id') == {'tpl1': 'xxx', 'tpl2': 'yyy'}
        assert capsys.readouterr().out == (
                'execute SQL: `select name, text from templates where site_id = %s;`\n'
                '  with: `site_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_put_template(self, monkeypatch, capsys):
        "unittest for docs2pg._put_template"
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: None)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._put_template('site_id', 'doc_name', 'data')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `site_id`, `doc_name`\n'
                'execute SQL: `insert into templates (site_id, name, text) values (%s, %s, %s);`\n'
                '  with: `site_id`, `doc_name`, `data`\n'
                'called commit() on connection\n'
                'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: ('oldtext',))
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._put_template('site_id', 'doc_name', 'data')
        assert capsys.readouterr().out == (
                'execute SQL: `select text from templates where site_id = %s and name = %s;`\n'
                '  with: `site_id`, `doc_name`\n'
                'execute SQL: `update templates set text = %s where site_id = %s and name = %s;`\n'
                '  with: `data`, `site_id`, `doc_name`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_template_id(self, monkeypatch, capsys):
        """unittest for docs2pg.get_template_id
        """
        def mock_fetchone(self, *args):
            """stub
            """
            return ()
        def mock_fetchone_2(self, *args):
            """stub
            """
            return {'id': 'tpl_id'}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        assert not testee._get_template_id('site_id', 'tplname')
        assert capsys.readouterr().out == (
            'execute SQL: `select id from templates where site_id = %s and name = %s;`\n'
            '  with: `site_id`, `tplname`\n'
            'called commit() on connection\n'
            'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone_2)
        assert testee._get_template_id('site_id', 'tplname') == 'tpl_id'
        assert capsys.readouterr().out == (
            'execute SQL: `select id from templates where site_id = %s and name = %s;`\n'
            '  with: `site_id`, `tplname`\n'
            'called commit() on connection\n'
            'called close()\n')

    def test_do_rename_template(self, monkeypatch, capsys):
        """unittest for docs2pg.do_rename_template)
        """
        def mock_fetchone(cur, *args):
            print('called cursor.fetchone')
            return {'id': 'tpl_id'}
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._do_rename_template('site_id', 'tpl_id', 'newname')
        assert capsys.readouterr().out == (
                'execute SQL: `update templates set name = %s where site_id = %s and id = %s;`\n'
                "  with: `newname`, `site_id`, `tpl_id`\n"
                'called commit() on connection\n'
                'called close()\n')

    def test_do_delete_template(self, monkeypatch, capsys):
        """unittest for docs2pg.do_delete_template)
        """
        def mock_fetchone(cur, *args):
            print('called cursor.fetchone')
            return {'id': 'tpl_id'}
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._do_delete_template('site_id', 'tpl_id')
        assert capsys.readouterr().out == (
                'execute SQL: `delete from templates where site_id = %s and id = %s;`\n'
                "  with: `site_id`, `tpl_id`\n"
                'called commit() on connection\n'
                'called close()\n')

    def test_add_dts(self, monkeypatch, capsys):
        "unittest for docs2pg._add_dts"
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._add_dts('dir_id', 'doc_name', 'doc_id')
        assert capsys.readouterr().out == (
                'execute SQL: `insert into doc_stats'
                ' (dir_id, docname, source_docid, source_updated) values (%s, %s, %s, %s);`\n'
                '  with: `dir_id`, `doc_name`, `doc_id`, `now`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_fetch_doc_contents(self, monkeypatch, capsys):
        "unittest for docs2pg._fetch_doc_contents"
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'currtext': 'text'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._fetch_doc_contents('doc_id', False) == 'text'
        assert capsys.readouterr().out == (
                'execute SQL: `select currtext from documents where id = %s;`\n'
                '  with: `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'previous': 'old text'})
        assert testee._fetch_doc_contents('doc_id', True) == 'old text'
        assert capsys.readouterr().out == (
                'execute SQL: `select previous from documents where id = %s;`\n'
                '  with: `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_put_update(self, monkeypatch, capsys):
        "unittest for docs2pg._put_update"
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._put_update('doc_id', 'rst_id', 'text', 'oldtext')
        assert capsys.readouterr().out == (
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: `oldtext`, `text`, `rst_id`\n'
                'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n'
                '  with: `now`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_do_revert(self, monkeypatch, capsys):
        "unittest for docs2pg._do_revert"
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'previous': 'oldtext'})
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee._do_revert('rst_id', 'doc_id')
        assert capsys.readouterr().out == (
                'execute SQL: `select previous from documents where id = %s;`\n'
                '  with: `rst_id`\n'
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: ``, `oldtext`, `rst_id`\n'
                'execute SQL: `update doc_stats set source_updated = %s where id = %s;`\n'
                '  with: `now`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_mark_dir_deleted(self, monkeypatch, capsys):
        """unittest for docs2pg.mark_dir_deleted
        """
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._mark_dir_deleted('dir_id')
        assert capsys.readouterr().out == (
                'execute SQL: `insert into doc_stats (dir_id, docname, source_deleted)'
                ' values (%s, %s, %s);`\n'
                '  with: `dir_id`, ``, `True`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_mark_doc_deleted(self, monkeypatch, capsys):
        """unittest for docs2pg.mark_doc_deleted
        """
        def mock_fetchone(self):
            return {'source_docid': 'rst_id'}
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, 'fetchone', mock_fetchone)
        testee._mark_doc_deleted('doc_id')
        assert capsys.readouterr().out == (
                'execute SQL: `select source_docid from doc_stats where id = %s;`\n'
                '  with: `doc_id`\n'
                'execute SQL: `delete from documents where id = %s;`\n'
                '  with: `rst_id`\n'
                'execute SQL: `update doc_stats set source_deleted = %s where id = %s;`\n'
                '  with: `True`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_deletions(self, monkeypatch, capsys):
        """unittest for docs2pg.get_deletion_ids
        """
        def mock_iter(*args):
            """stub
            """
            return (x for x in [{'id': 1, 'docname': 'xxx', 'target_docid': 11},
                                {'id': 2, 'docname': 'yyy.html', 'target_docid': 12},
                                {'id': 3, 'docname': ''}])
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        assert testee.get_deletions('dir_id', 'stg') == [
                (1, 'xxx', 11), (2, 'yyy.html', 12), (3, '', 'dir_id')]
        assert capsys.readouterr().out == (
                "execute SQL: `select id, dirname from directories;`\n"
                "execute SQL: `select id, docname, target_docid from doc_stats"
                " where dir_id = %s and stg_deleted = %s;`\n"
                "  with: `dir_id`, `True`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_execute_deletions(self, monkeypatch, capsys):
        """unittest for docs2pg.execute_deletions
        """
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee.execute_deletions('source', [(11, 1), (12, 2)], [])
        assert capsys.readouterr().out == (
                'execute SQL: `delete from documents where id = %s;`\n'
                '  with: `(1,)`, `(2,)`\n'
                'execute SQL: `update doc_stats set source_docid = %s, source_updated = %s,'
                ' source_deleted = %s, target_docid = %s, target_deleted = %s where id = %s;`\n'
                '  with: `(None, None, None, 1, True, 11)`, `(None, None, None, 1, True, 12)`\n'
                'called commit() on connection\n'
                'called close()\n')
        testee.execute_deletions('source', [], [1, 2])
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set target_deleted = %s where id = %s;`\n'
                '  with: `(True, 1)`, `(True, 2)`\n'
                'called commit() on connection\n'
                'called close()\n')
        testee.execute_deletions('xxxx', [1, 2], [])
        assert capsys.readouterr().out == (
                'execute SQL: `delete from doc_stats where id = %s;`\n'
                '  with: `(1,)`, `(2,)`\n'
                'called commit() on connection\n'
                'called close()\n')
        testee.execute_deletions('xxxx', [], [(1, 11), (2, 12)])
        assert capsys.readouterr().out == (
                'execute SQL: `delete from doc_stats where id = %s;`\n'
                '  with: `(1,)`, `(2,)`\n'
                'execute SQL: `delete from directories where id = %s;`\n'
                '  with: `(11,)`, `(12,)`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_put_html(self, monkeypatch, capsys):
        "unittest for docs2pg._put_html"
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee._put_html(None, 'new_id', 'doc_id', 'contents', 'oldtext')
        assert capsys.readouterr().out == (
                'execute SQL: `update documents set currtext = %s where id = %s;`\n'
                '  with: `contents`, `new_id`\n'
                'execute SQL: `update doc_stats set target_docid = %s, target_updated = %s'
                ' where id = %s;`\n'
                '  with: `new_id`, `now`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')
        testee._put_html('html_id', 'new_id', 'doc_id', 'contents', 'oldtext')
        assert capsys.readouterr().out == (
                'execute SQL: `update documents set previous = %s, currtext = %s where id = %s;`\n'
                '  with: `oldtext`, `contents`, `html_id`\n'
                'execute SQL: `update doc_stats set target_updated = %s where id = %s;`\n'
                '  with: `now`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_update_target_directory(self, monkeypatch, capsys):
        "unittest for docs2pg._update_target_directory"
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._update_target_directory([('x', 'y', 'z', 'q'), ('a', 'b', 'c', 'd')])
        assert capsys.readouterr().out == (
                "execute SQL: `update doc_stats set source_docid = %s, source_updated = %s,"
                " source_deleted = %s, target_docid = %s, target_deleted = %s where id = %s;`\n"
                "  with: `('x', 'x', 'x', 'y', 'z', 'q')`, `('a', 'a', 'a', 'b', 'c', 'd')`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_update_mirror_dts(self, monkeypatch, capsys):
        "unittest for docs2pg._update_mirror_dts"
        monkeypatch.setattr(testee, 'conn', MockConn())
        monkeypatch.setattr(testee.datetime, 'datetime', MockDatetime)
        testee._update_mirror_dts('doc_id')
        assert capsys.readouterr().out == (
                'execute SQL: `update doc_stats set mirror_updated = %s where id = %s;`\n'
                '  with: `now`, `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_update_mirror_directory(self, monkeypatch, capsys):
        "unittest for docs2pg._update_mirror_directory"
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._update_mirror_directory(['x', 'y', 'z'])
        assert capsys.readouterr().out == (
                "execute SQL: `delete from doc_stats where id = %s;`\n"
                "  with: `x`, `y`, `z`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_get_stats_get_datetimestamps(self, monkeypatch, capsys):
        "unittest for docs2pg._get_datetimestamps"
        monkeypatch.setattr(MockCursor, 'fetchone', lambda x: {'source_updated': 1,
                                                               'source_deleted': False,
                                                               'target_updated': 2,
                                                               'target_deleted': False,
                                                               'mirror_updated': 3})
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert list(testee._get_datetimestamps('doc_id')) == [1, False, 2, False, 3]
        assert capsys.readouterr().out == (
                'execute SQL: `select source_updated, source_deleted, target_updated,'
                ' target_deleted, mirror_updated from doc_stats where id = %s;`\n'
                '  with: `doc_id`\n'
                'called commit() on connection\n'
                'called close()\n')

    def test_get_stats_for_dirs(self, monkeypatch, capsys):
        "unittest for docs2pg._get_stats_for_dirs"
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
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        counter = 0
        assert testee._get_stats_for_dirs('site_id', ['/', 'subdir']) == (
                ['/', 'subdir'], [
                    ('/', 'x', testee.Stats(src=1, dest=2, mirror=3)),
                    ('/', 'y', testee.Stats(src=1, dest=4, mirror=5)),
                    ('/', 'y', testee.Stats(src='[deleted]', dest=4, mirror=5)),
                    ('/', 'y', testee.Stats(src='[deleted]', dest='[deleted]', mirror=5)),
                    ('subdir', 'a', testee.Stats(src=2, dest=4, mirror=5)),
                    ('subdir', 'b', testee.Stats(src=3, dest=4, mirror=6))])
        assert capsys.readouterr().out == (
                'execute SQL: `select dirname from directories where site_id = %s;`\n'
                '  with: `site_id`\n'
                'execute SQL: `select dirname, docname, source_updated, target_updated,'
                ' mirror_updated, source_deleted, target_deleted from doc_stats, directories'
                ' where dir_id = directories.id and dir_id = any(%s);`\n'
                "  with: `['/', 'subdir']`\n"
                'called commit() on connection\n'
                'called close()\n')

    def test_fetch_dirmap(self, monkeypatch, capsys):
        "unittest for docs2pg._fetch_dirmap"
        def mock_iter(*args):
            return (x for x in [{'id': 1, 'dirname': '/'}, {'id': 2, 'dirname': 'subdir'}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._fetch_dirmap('siteid') == {1: '/', 2: 'subdir'}
        assert capsys.readouterr().out == (
                "execute SQL: `select id, dirname from directories where site_id = %s;`\n"
                "  with: `siteid`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_fetch_site_data(self, monkeypatch, capsys):
        "unittest for docs2pg._fetch_site_data"
        def mock_iter(*args):
            return (x for x in [
                {'docname': 'x', 'source_docid': 1, 'source_updated': 'y',
                 'source_deleted': False, 'target_docid': 2, 'target_updated': 'z',
                 'target_deleted': False, 'mirror_updated': 'q', 'dir_id': 1},
                {'docname': 'a', 'source_docid': 3, 'source_updated': 'b',
                 'source_deleted': False, 'target_docid': 3, 'target_updated': 'c',
                 'target_deleted': False, 'mirror_updated': 'q', 'dir_id': 2},
                {'docname': 'a', 'source_docid': 3, 'source_updated': 'b',
                 'source_deleted': False, 'target_docid': 3, 'target_updated': 'c',
                 'target_deleted': False, 'mirror_updated': 'd', 'dir_id': 3}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._fetch_site_data([1, 2]) == [
                {'docname': 'x', 'source_docid': 1, 'source_updated': 'y',
                 'source_deleted': False, 'target_docid': 2, 'target_updated': 'z',
                 'target_deleted': False, 'mirror_updated': 'q', 'dir_id': 1},
                {'docname': 'a', 'source_docid': 3, 'source_updated': 'b',
                 'source_deleted': False, 'target_docid': 3, 'target_updated': 'c',
                 'target_deleted': False, 'mirror_updated': 'q', 'dir_id': 2},
                {'docname': 'a', 'source_docid': 3, 'source_updated': 'b',
                 'source_deleted': False, 'target_docid': 3, 'target_updated': 'c',
                 'target_deleted': False, 'mirror_updated': 'd', 'dir_id': 3}]
        assert capsys.readouterr().out == (
                "execute SQL: `select docname, source_docid, source_updated, source_deleted,"
                " target_docid, target_updated, target_deleted, mirror_updated, dir_id"
                " from doc_stats where dir_id = any(%s);`\n"
                "  with: `[1, 2]`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_fetch_doc_data(self, monkeypatch, capsys):
        "unittest for docs2pg._fetch_doc_data"
        def mock_iter(*args):
            return (x for x in [{'id': 1, 'currtext': 'xxx1', 'previous': 'yyy1'},
                                {'id': 2, 'currtext': 'xxx2', 'previous': 'yyy2'},
                                {'id': 3, 'currtext': 'xxx3', 'previous': 'yyy3'}])
        monkeypatch.setattr(MockCursor, '__iter__', mock_iter)
        monkeypatch.setattr(testee, 'conn', MockConn())
        assert testee._fetch_doc_data({1: 'aaa', 2: 'bbb', 3: 'ccc'}) == [
                {'_id': 'aaa', 'current': 'xxx1', 'previous': 'yyy1'},
                {'_id': 'bbb', 'current': 'xxx2', 'previous': 'yyy2'},
                {'_id': 'ccc', 'current': 'xxx3', 'previous': 'yyy3'}]
        assert capsys.readouterr().out == (
                "execute SQL: `select id, currtext, previous from documents where id = any(%s)`\n"
                "  with: `[1, 2, 3]`\n"
                "called commit() on connection\n"
                "called close()\n")

    def test_delete_dir_data(self, monkeypatch, capsys):
        "unittest for docs2pg._delete_dir_data"
        monkeypatch.setattr(MockCursor, '__iter__', lambda x: (x for x in [
            {'source_docid': 4, 'target_docid': 7},
            {'source_docid': 5, 'target_docid': 0},
            {'source_docid': 6, 'target_docid': 9}]))
        monkeypatch.setattr(testee, 'conn', MockConn())
        testee._delete_dir_data('site_id', [2, 3])
        assert capsys.readouterr().out == (
            'execute SQL: `select source_docid, target_docid from doc_stats'
            ' where dir_id = any(%s);`\n'
            '  with: `[2, 3]`\n'
            'execute SQL: `delete from documents where id = any(%s);`\n'
            '  with: `[4, 7, 5, 6, 9]`\n'
            'execute SQL: `delete from doc_stats where dir_id = any(%s);`\n'
            '  with: `[2, 3]`\n'
            'execute SQL: `delete from templates where site_id = %s;`\n'
            '  with: `site_id`\n'
            'execute SQL: `delete from directories where site_id = %s;`\n'
            '  with: `site_id`\n'
            'execute SQL: `delete from site_settings where site_id = %s;`\n'
            '  with: `site_id`\n'
            'execute SQL: `delete from sites where id = %s;`\n'
            '  with: `site_id`\n'
            'called commit() on connection\n'
            'called close()\n')
