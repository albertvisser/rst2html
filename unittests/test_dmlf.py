"""unittests for ./app/docs2fs.py
"""
import os
import pathlib
import types
import pytest
import app.docs2fs as testee


def mock_copyfile(*args):
    """stub
    """
    print(f'called copyfile: from `{args[0]}` to `{args[1]}`')


def test_locify():
    """unittest for docs2fs.locify
    """
    path = pathlib.Path('test')
    assert testee._locify(path) == path / '.source'
    assert testee._locify(path, '') == path / '.source'
    assert testee._locify(path, 'src') == path / '.source'
    assert testee._locify(path, 'dest') == path / '.target'
    assert testee._locify(path, 'mirror') == path
    with pytest.raises(ValueError):
        testee._locify(path, 'x')


class TestNonApiFunctions:
    """unittests for functions outside of the dml API
    """
    def test_get_dir_ftype_stats(self, monkeypatch, capsys):
        """unittest for docs2fs.get_dir_ftype_stats
        """
        # def mock_locify(*args):
        #     """stub
        #     """
        #     return pathlib.Path('.')
        def mock_is_file(*args):
            """stub
            """
            return bool(args[0].suffix)
        def mock_is_dir(*args):
            """stub
            """
            return not bool(args[0].suffix)
        def mock_iterdir_src(*args):
            """stub
            """
            print('called path.iterdir with args', args)
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'),
                    pathlib.Path('index.rst'), pathlib.Path('test.src'),
                    pathlib.Path('revived.deleted'), pathlib.Path('revived.rst'),
                    pathlib.Path('overview-xxx'), pathlib.Path('search-results-xxx'),
                    pathlib.Path('removed.deleted'))
        def mock_iterdir_dest(*args):
            """stub
            """
            print('called path.iterdir with args', args)
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'),
                    pathlib.Path('index.html'), pathlib.Path('test.src'),
                    pathlib.Path('revived.deleted'), pathlib.Path('revived.html'),
                    pathlib.Path('removed.deleted'))
        # def mock_iterdir_dest_sef(*args):
        #     """stub
        #     """
        #     return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('hello'),
        #             pathlib.Path('kitty'))
        def mock_relative_to(*args):
            """stub
            """
            return args[0]
        def mock_stat(*args):
            """stub
            """
            result = types.SimpleNamespace()
            result.st_mtime = 'x'
            return result
        def mock_stat_error(*args):
            """stub
            """
            raise FileNotFoundError
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir_src)
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', mock_is_file)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', mock_is_dir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_symlink', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'relative_to', mock_relative_to)
        monkeypatch.setattr(testee.pathlib.Path, 'stat', mock_stat)
        assert testee._get_dir_ftype_stats('sitename', 'src') == ([], [])
        assert capsys.readouterr().out == (
                f"called path.iterdir with args ({testee.WEBROOT / 'sitename' / '.source'!r},)\n")
        monkeypatch.setattr(testee.pathlib.Path, 'is_symlink', lambda x: False)
        assert testee._get_dir_ftype_stats('sitename', 'src', '') == (
                [('index', 'x'), ('revived', 'x')], ['revived', 'removed'])
        assert capsys.readouterr().out == (
                f"called path.iterdir with args ({testee.WEBROOT / 'sitename' / '.source'!r},)\n")

        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir_dest)
        monkeypatch.setattr(testee.pathlib.Path, 'is_symlink', lambda x: True)
        assert testee._get_dir_ftype_stats('sitename', 'dest') == ([('index', 'x')], [])
        assert capsys.readouterr().out == (
                f"called path.iterdir with args ({testee.WEBROOT / 'sitename' / '.target'!r},)\n")
        monkeypatch.setattr(testee.pathlib.Path, 'is_symlink', lambda x: False)
        assert testee._get_dir_ftype_stats('sitename', 'dest') == ([('subdir', 'x'), ('index', 'x')],
                                                                 [])
        assert capsys.readouterr().out == (
                f"called path.iterdir with args ({testee.WEBROOT / 'sitename' / '.target'!r},)\n")
        # import pdb; pdb.set_trace()
        assert testee._get_dir_ftype_stats('sitename', 'dest', 'dirname') == ([('subdir', 'x')], [])
        assert capsys.readouterr().out == (
                "called path.iterdir with args"
                f" ({testee.WEBROOT / 'sitename' / '.target' / 'dirname'!r},)\n")
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        assert testee._get_dir_ftype_stats('sitename', 'dest', 'dirname') == (
                [('index', 'x'), ('revived', 'x')], ['revived', 'removed'])
        assert capsys.readouterr().out == (
                "called path.iterdir with args"
                f" ({testee.WEBROOT / 'sitename' / '.target' / 'dirname'!r},)\n")
        monkeypatch.setattr(testee.pathlib.Path, 'stat', mock_stat_error)
        assert testee._get_dir_ftype_stats('sitename', 'dest', 'dirname') == (
                [], ['revived', 'removed'])
        assert capsys.readouterr().out == (
                "called path.iterdir with args"
                f" ({testee.WEBROOT / 'sitename' / '.target' / 'dirname'!r},)\n")

        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        assert testee._get_dir_ftype_stats('sitename', 'src') == ([], [])
        assert capsys.readouterr().out == ""

    def test_get_dir_stats(self, monkeypatch):
        """unittest for docs2fs.get_dir_stats
        """
        def mock_get_dir_ftype_stats(*args):
            """stub
            """
            if args[1] == 'src':
                return (('name2', 2), ('name1', 1)), ['name3']
            if args[1] == 'dest':
                return (('name2', 2), ('name1', 1), ('name3', 1)), ['name4']
            # if args[1] == 'mirror':
            return (('name2', 2), ('name1', 1), ('name3', 2), ('name4', 2)), []
        monkeypatch.setattr(testee, '_get_dir_ftype_stats', mock_get_dir_ftype_stats)
        time1 = testee.datetime.datetime.fromtimestamp(1)
        time2 = testee.datetime.datetime.fromtimestamp(2)
        null = testee.datetime.datetime.min
        assert testee._get_dir_stats('testsite') == [('name1', testee.Stats(time1, time1, time1)),
                                                   ('name2', testee.Stats(time2, time2, time2)),
                                                   ('name3', testee.Stats('[deleted]', time1, time2)),
                                                   ('name4', testee.Stats(null, '[deleted]', time2))]

    def test_get_dir_stats_for_docitem(self, monkeypatch):
        """unittest for docs2fs.get_dir_stats_for_docitem
        """
        def mock_get_dir_ftype_stats(*args):
            """stub
            """
            return [('name2', 2), ('name1', 1)], ['name2', 'name3']
        def mock_get_dir_ftype_stats_2(*args):
            """stub
            """
            return [('name2', 1), ('name1', 2)], ['name2', 'name3']
        class MockDateTime:
            "stub"
            min = 1
            @classmethod
            def fromtimestamp(cls, arg):
                return arg
        monkeypatch.setattr(testee, '_get_dir_ftype_stats', mock_get_dir_ftype_stats)
        time1 = testee.datetime.datetime.fromtimestamp(1)
        time2 = testee.datetime.datetime.fromtimestamp(2)
        assert testee._get_dir_stats_for_docitem('testsite') == {
                'name1': {'dest': {'docid': 4, 'updated': time1},
                          'mirror': {'updated': time1},
                          'src': {'docid': 2, 'updated': time1}},
                'name2': {'dest': {'deleted': True, 'docid': 3, 'updated': time2},
                          'mirror': {'deleted': True, 'updated': time2},
                          'src': {'deleted': True, 'docid': 1, 'updated': time2}},
                'name3': {'dest': {'deleted': True},
                          'mirror': {'deleted': True},
                          'src': {'deleted': True}}}
        # for full branch coverage, unlikely because datetime.datetime.fromtimestamp(timestamp)
        # probably never gives datetime.datetime.min
        monkeypatch.setattr(testee.datetime, 'datetime', MockDateTime)
        monkeypatch.setattr(testee, '_get_dir_ftype_stats', mock_get_dir_ftype_stats)
        assert testee._get_dir_stats_for_docitem('testsite') == {
                'name1': {},
                'name2': {'dest': {'deleted': True, 'docid': 3, 'updated': 2},
                          'mirror': {'deleted': True, 'updated': 2},
                          'src': {'deleted': True, 'docid': 1, 'updated': 2}},
                'name3': {'dest': {'deleted': True},
                          'mirror': {'deleted': True},
                          'src': {'deleted': True}}}
        monkeypatch.setattr(testee, '_get_dir_ftype_stats', mock_get_dir_ftype_stats_2)
        assert testee._get_dir_stats_for_docitem('testsite') == {
                'name1': {'dest': {'docid': 4, 'updated': 2},
                          'mirror': {'updated': 2},
                          'src': {'docid': 2, 'updated': 2}},
                'name2': {'dest': {'deleted': True, 'docid': 3},
                          'mirror': {'deleted': True},
                          'src': {'deleted': True, 'docid': 1}},
                'name3': {'dest': {'deleted': True},
                          'mirror': {'deleted': True},
                          'src': {'deleted': True}}}

    def test_get_sitedoc_data(self, monkeypatch):
        """unittest for docs2fs.get_sitedoc_data
        """
        def mock_get_docitem_stats(*args):
            """stub
            """
            return 'hello, world!'
        def mock_list_dirs(*args):
            """stub
            """
            return 'x', 'y'
        monkeypatch.setattr(testee, '_get_dir_stats_for_docitem', mock_get_docitem_stats)
        monkeypatch.setattr(testee, 'list_dirs', mock_list_dirs)
        assert testee._get_sitedoc_data('sitename') == {'/': 'hello, world!', 'x': 'hello, world!',
                                                      'y': 'hello, world!'}

    def test_read_data(self, monkeypatch, capsys, tmp_path):
        """unittest for docs2fs.read_data
        """
        tmpfile = tmp_path / 'testeetmpfile'
        tmpfile.write_text('regel 1\rregel 2\r\nregel 3\n')
        tmpfileiso = tmp_path / 'testeetmpfileiso'
        tmpfileiso.write_text('règle 1\rrègle 2\r\nrègle 3\n', encoding='iso-8859-1')
        def mock_relative_to(self, *args):
            """stub
            """
            return self
        def mock_open_utf(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            return open(str(tmpfile))
        def mock_open_utf_err(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            raise OSError('IO error on utf file')
        def mock_open_iso(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            return open(str(tmpfileiso))
        def mock_open_iso_err(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            # return tmpfileiso.open()
            raise OSError('IO error on iso file')
        # def mock_readlines(*args):
        #     """stub
        #     """
        #     return ['regel 1\r', 'regel 2\r\n', 'regel 3\n']
        monkeypatch.setattr(testee.pathlib.Path, 'relative_to', mock_relative_to)
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open_utf)
        assert testee.read_data(pathlib.Path('sitename/docname.rst')) == ('',
                                                                        'regel 1\nregel 2\nregel 3\n')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'
        assert testee.read_data(pathlib.Path('sitename/docname.html')) == ('',
                                                                        'regel 1\nregel 2\nregel 3\n')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname/index.html`\n'
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open_utf_err)
        assert testee.read_data(pathlib.Path('sitename/docname.rst')) == ('IO error on utf file', '')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open_iso)
        # blijkbaar gaat dit ook mis als hij het iso file gaat proberen te lezen...
        # assert testee.read_data(pathlib.Path('sitename/docname.html')) == ('',
        #                                                                 'regel 1\nregel 2\nregel 3\n')
        # assert capsys.readouterr().out == 'called open() for file `sitename/docname.html`\n'
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open_iso_err)
        assert testee.read_data(pathlib.Path('sitename/docname.rst')) == ('IO error on iso file', '')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'

    def test_save_to(self, monkeypatch, capsys, tmp_path):
        """unittest for docs2fs.save_to
        """
        tmpfilename = str(tmp_path / 'testeesaveto')
        def mock_open_err(self, *args, **kwargs):
            """stub
            """
            raise OSError
        def mock_open(self, *args, **kwargs):
            """stub
            """
            return open(tmpfilename, 'w')
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir for `{self}`')
        def mock_replace(self, *args, **kwargs):
            """stub
            """
            print(f'called replace for `{self}` with `{args[0]}`')
        def read_and_remove(filename):
            """verificatie en teardown

            lees inhoud van zojuist weggeschreven file en verwijder het
            geef de gelezen inhoud terug
            """
            with open(filename) as read_file:
                data = read_file.read()
            os.unlink(filename)
            return data
        fulldocname = testee.WEBROOT / 'testsite' / 'docname'
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open_err)
        assert testee.save_to(fulldocname, 'data') == 'OSError without message'

        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.shutil, 'copyfile', mock_copyfile)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open)
        assert testee.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == ''
        assert read_and_remove(tmpfilename) == 'data'
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        fulldocname = testee.WEBROOT / 'testsite' / 'docname.rst'
        assert testee.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == 'called copyfile: from `{}` to `{}`\n'.format(
            str(fulldocname), str(fulldocname) + '.bak')
        assert read_and_remove(tmpfilename) == 'data'
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        fulldocname = testee.WEBROOT / 'testsite' / 'docname.html'
        assert testee.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == 'called mkdir for `{}`\n'.format(
            str(fulldocname).replace('.html', ''))
        assert read_and_remove(tmpfilename) == 'data'
        assert testee.save_to(fulldocname, 'data', False) == ''
        assert capsys.readouterr().out == ""
        assert read_and_remove(tmpfilename) == 'data'

        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'replace', mock_replace)
        assert testee.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == ''.join((
            'called replace for `{}` with `{}`\n'.format(str(fulldocname).replace('.html', ''),
                                                         str(fulldocname).replace('.html', '.bak')),
            'called mkdir for `{}`\n'.format(str(fulldocname).replace('.html', '')),
            'called copyfile: from `{}` to `{}`\n'.format(str(fulldocname).replace('.html',
                                                                                   '/index.html'),
                                                          str(fulldocname).replace('.html',
                                                                                   '/index.html.bak'))
                                                          ))
        assert read_and_remove(tmpfilename) == 'data'


class TestTestApi:
    """unittests for api functions related to testing
    """
    def test_clear_db(self):
        """unittest for docs2fs.clear_db
        """
        with pytest.raises(NotImplementedError):
            testee.clear_db()

    def test_read_db(self):
        """unittest for docs2fs.read_db
        """
        with pytest.raises(NotImplementedError):
            testee.read_db()

    def test_list_site_data(self, monkeypatch):
        """unittest for docs2fs.list_site_data
        """
        def mock_read_settings(*args):
            """stub
            """
            return f'called read_settings for `{args[0]}`'
        def mock_get_sitedoc_data(*args):
            """stub
            """
            return f'called get_sitedoc_data for `{args[0]}`'
        def mock_list_docs(*args):
            """stub
            """
            # rest = f'/{args[2]}' if len(args) > 2 else ''  # why if this is not used?
            return ['doc1']
        def mock_list_dirs(*args):
            """stub
            """
            return ['dir1']
        def mock_read_data(*args):
            """stub
            """
            return '', f'called read_data for {args[0]}'
        # formeel kloppen deze returns maar hou er rekening mee dat dit niks zegt over hoe
        # de gegevens er uit zien
        sitename = 'testsite'
        monkeypatch.setattr(testee, 'read_settings', mock_read_settings)
        monkeypatch.setattr(testee, '_get_sitedoc_data', mock_get_sitedoc_data)
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee, 'list_dirs', mock_list_dirs)
        monkeypatch.setattr(testee, 'read_data', mock_read_data)
        siteloc = testee.WEBROOT / sitename
        assert testee.list_site_data(sitename) == (
            {'_id': 0, 'name': 'testsite',
             'settings': 'called read_settings for `testsite`',
             'docs': 'called get_sitedoc_data for `testsite`'},
            [{'_id': ('dir1/doc1', 'dest'),
              'current': f'called read_data for {siteloc}/.target/dir1/doc1.html',
              'previous': f'called read_data for {siteloc}/.target/dir1/doc1.html.bak'},
             {'_id': ('dir1/doc1', 'src'),
              'current': f'called read_data for {siteloc}/.source/dir1/doc1.rst',
              'previous': f'called read_data for {siteloc}/.source/dir1/doc1.rst.bak'},
             {'_id': ('doc1', 'dest'),
              'current': f'called read_data for {siteloc}/.target/doc1.html',
              'previous': f'called read_data for {siteloc}/.target/doc1.html.bak'},
             {'_id': ('doc1', 'src'),
              'current': f'called read_data for {siteloc}/.source/doc1.rst',
              'previous': f'called read_data for {siteloc}/.source/doc1.rst.bak'}])

    def test_clear_site_data(self, monkeypatch, capsys):
        """unittest for docs2fs.clear_site_data
        """
        def mock_rmtree_ok(*args):
            """stub
            """
            print(f'called rmtree for `{args[0]}`')
        def mock_rmtree_err(*args):
            """stub
            """
            raise FileNotFoundError
        sitename = 'testsite'
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_ok)
        testee.clear_site_data(sitename)
        assert capsys.readouterr().out == f'called rmtree for `{testee.WEBROOT / sitename}`\n'
        monkeypatch.setattr(testee.shutil, 'rmtree', mock_rmtree_err)
        testee.clear_site_data(sitename)
        assert capsys.readouterr().out == ''


class TestSiteLevel:
    """unittests for site level api functions
    """
    def test_list_sites(self, monkeypatch):
        """unittest for docs2fs.list_sites
        """
        def mock_iterdir(*args):
            """stub
            """
            return [pathlib.Path(x) for x in ('y', 'z')]
        def mock_is_dir_yes(*args):
            """stub
            """
            return True
        def mock_is_dir_no(*args):
            """stub
            """
            return False
        def mock_exists_yes(*args):
            """stub
            """
            return True
        # def mock_exists_no(*args):
        #     """stub
        #     """
        #     return False
        def mock_is_file_yes(*args):
            """stub
            """
            return True
        def mock_is_file_no(*args):
            """stub
            """
            return False
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', mock_is_dir_no)
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', mock_is_file_yes)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', mock_exists_yes)
        assert testee.list_sites() == []
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', mock_is_dir_yes)
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', mock_is_file_no)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', mock_exists_yes)
        assert testee.list_sites() == []
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', mock_is_dir_yes)
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', mock_is_file_yes)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', mock_exists_yes)
        assert testee.list_sites() == ['y', 'z']

    def test_create_new_site(self, monkeypatch, capsys):
        """unittest for docs2fs.create_new_site
        """
        def mock_mkdir_err(self, *args, **kwargs):
            """stub
            """
            raise FileExistsError
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir for `{self}`')
        def mock_touch(self, *args, **kwargs):
            """stub
            """
            print(f'called touch for `{self}`')
        sitename = 'testsite'
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir_err)
        with pytest.raises(FileExistsError):
            testee.create_new_site(sitename)
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        testee.create_new_site(sitename)
        siteloc = str(testee.WEBROOT / sitename)
        assert capsys.readouterr().out == (f'called mkdir for `{siteloc}`\n'
                                           f'called mkdir for `{siteloc}/.source`\n'
                                           f'called mkdir for `{siteloc}/.target`\n'
                                           f'called touch for `{siteloc}/settings.yml`\n')

    def test_rename_site(self):
        """unittest for docs2fs.rename_site
        """
        with pytest.raises(NotImplementedError):
            testee.rename_site('sitename', 'newname')

    def test_read_settings(self, monkeypatch, capsys, tmp_path):
        """unittest for docs2fs.read_settings
        """
        testsettings = tmp_path / 'testeereadsett'
        testsettings.write_text('regel 1\rregel 2\r\nregel 3\n')
        def mock_open(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            return open(str(testsettings))
        def mock_load_config_data(*args):
            """stub
            """
            return {'x': 'y'}
        def mock_load_config_data_2(*args):
            """stub
            """
            return None
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open)
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data)
        sitename = 'testsite'
        assert testee.read_settings(sitename) == {'x': 'y'}
        settfile = testee.WEBROOT / sitename / testee.SETTFILE
        assert capsys.readouterr().out == f'called open() for file `{settfile}`\n'
        monkeypatch.setattr(testee, 'load_config_data', mock_load_config_data_2)
        assert testee.read_settings(sitename) == {}
        settfile = testee.WEBROOT / sitename / testee.SETTFILE
        assert capsys.readouterr().out == f'called open() for file `{settfile}`\n'

    def test_update_settings(self, monkeypatch, capsys, tmp_path):
        """unittest for docs2fs.update_settings
        """
        def mock_open(self, *args, **kwargs):
            """stub
            """
            print(f'called open() for file `{self}`')
            return open(str(tmp_path / 'testeeupd_sett'), 'w')
        def mock_save_config_data(*args, **kwargs):
            """stub
            """
            print('called save_config_data')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open)
        monkeypatch.setattr(testee, 'save_config_data', mock_save_config_data)
        sitename = 'testsite'
        settfile = testee.WEBROOT / sitename / testee.SETTFILE
        assert testee.update_settings(sitename, {'x': 'y'}) == 'ok'
        assert capsys.readouterr().out == (f'called open() for file `{settfile}`\n'
                                           'called save_config_data\n')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.shutil, 'copyfile', mock_copyfile)
        assert testee.update_settings(sitename, {'x': 'y'}) == 'ok'
        assert capsys.readouterr().out == (f'called copyfile: from `{settfile}` to `{settfile}.bak`\n'
                                           f'called open() for file `{settfile}`\n'
                                           'called save_config_data\n')

    def test_clear_settings(self):
        """unittest for docs2fs.clear_settings
        """
        with pytest.raises(NotImplementedError):
            testee.clear_settings('sitename')

    def test_list_dirs(self, monkeypatch, capsys):
        """unittest for docs2fs.list_dirs
        """
        def mock_locify(*args):
            """stub
            """
            return args[0] / args[1]
        def mock_iterdir(self, *args):
            """stub
            """
            print(f'called iterdir for path `{self}`')
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'))
        sitename = 'testsite'
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee, '_locify', mock_locify)
        with pytest.raises(FileNotFoundError):
            testee.list_dirs(sitename)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: True)
        assert testee.list_dirs(sitename) == ['.x', 'css', 'subdir']
        sitepath = testee.WEBROOT / sitename
        assert capsys.readouterr().out == f'called iterdir for path `{sitepath}`\n'
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: False)
        assert testee.list_dirs(sitename, loc='dest') == []
        sitepath = testee.WEBROOT / sitename / 'dest'
        assert capsys.readouterr().out == f'called iterdir for path `{sitepath}`\n'
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: True)
        assert testee.list_dirs(sitename, loc='src') == ['.x', 'css', 'subdir']
        sitepath = testee.WEBROOT / sitename / 'src'
        assert capsys.readouterr().out == f'called iterdir for path `{sitepath}`\n'
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        assert testee.list_dirs(sitename, loc='src') == ['.x', 'css', 'subdir']
        assert capsys.readouterr().out == f'called iterdir for path `{sitepath}`\n'

    def test_create_new_dir(self, monkeypatch, capsys):
        """unittest for docs2fs.create_new_dir
        """
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir for `{self}`')
        def mock_touch(self, *args, **kwargs):
            """stub
            """
            print(f'called touch for `{self}`')
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        sitename = 'testsite'
        dirname = 'testdir'
        newdir = testee.WEBROOT / sitename / testee.SRC_LOC / dirname
        testee.create_new_dir(sitename, dirname)
        assert capsys.readouterr().out == (f'called mkdir for `{newdir}`\n'
                                           f"called touch for `{newdir / '.files'}`\n")

    def test_remove_dir(self):
        """unittest for docs2fs.remove_dir
        """
        with pytest.raises(NotImplementedError):
            testee.remove_dir('sitename', 'directory')


class TestDocLevel:
    """unittests for document level api functions
    """
    def test_list_docs(self, monkeypatch):
        """unittest for docs2fs.list_docs
        """
        def mock_exists_1(*args, **kwargs):
            """stub
            """
            self.times_called += 1
            if self.times_called == 1:
                return True
            return False
        def mock_iterdir(self, *args, **kwargs):
            """stub
            """
            return [testee.pathlib.Path(x) for x in ['file2', 'file3.rst', 'file5.html', 'file1.rst',
                                                   'file4.html', 'file0.deleted']]
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        with pytest.raises(FileNotFoundError):
            testee.list_docs('testsite', 'x')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', mock_exists_1)
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', lambda x: (x for x in []))
        self.times_called = 0
        assert testee.list_docs('testsite') == []
        self.times_called = 0
        assert testee.list_docs('testsite', 'src', 'subdir') == []
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', lambda x: False)
        assert testee.list_docs('testsite', 'src') == []
        monkeypatch.setattr(testee.pathlib.Path, 'is_file', lambda x: True)
        assert testee.list_docs('testsite', 'src') == ['file3', 'file1']
        monkeypatch.setattr(testee, 'read_settings', lambda x: {})
        assert testee.list_docs('testsite', 'dest') == ['file5', 'file4']
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: False)
        assert testee.list_docs('testsite', 'dest', 'directory') == []
        monkeypatch.setattr(testee.pathlib.Path, 'is_dir', lambda x: True)
        assert testee.list_docs('testsite', 'dest', 'directory') == ['file2', 'file3', 'file5',
                                                                   'file1', 'file4', 'file0']
        assert testee.list_docs('testsite', 'dest', ) == ['file2', 'file3', 'file5', 'file1',
                                                        'file4', 'file0', 'index']
        assert testee.list_docs('testsite', 'src', deleted=True) == ['file0']

    def test_list_templates(self, monkeypatch):
        """unittest for docs2fs.list_templates
        """
        def mock_iterdir(self):
            """stub
            """
            return (pathlib.Path('x'), pathlib.Path('y.rst'), pathlib.Path('y.html'),
                    pathlib.Path('z.tpl'), pathlib.Path('a.tpl'))
        sitename = 'testsite'
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', mock_iterdir)
        assert testee.list_templates(sitename) == []
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        assert testee.list_templates(sitename) == ['a.tpl', 'z.tpl']

    def test_read_template(self, monkeypatch, capsys, tmp_path):
        """unittest for docs2fs.read_template
        """
        tmpfile = tmp_path / 'testeeread_tpl'
        tmpfile.write_text('hello\rhello\r\nhello\n')
        def mock_open(self, *args):
            """stub
            """
            print(f'called open() for `{self}`')
            return open(str(tmpfile))
        monkeypatch.setattr(testee.pathlib.Path, 'open', mock_open)
        sitename, docname = 'testsite', 'template'
        assert testee.read_template(sitename, docname) == 'hello\nhello\nhello\n'
        tplname = testee.WEBROOT / sitename / '.templates' / docname
        assert capsys.readouterr().out == f'called open() for `{tplname}`\n'

    def test_write_template(self, monkeypatch, tmp_path):
        """unittest for docs2fs.write_template
        """
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() for `{self}`')
        def mock_save_to(filename, data):
            """stub
            """
            return f'called save_to with args `{filename}`, `{data}`'
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        monkeypatch.setattr(testee, 'WEBROOT', tmp_path / 'testeewrite')
        fullname = tmp_path / 'testeewrite' / 'sitename' / '.templates' / 'fnaam'
        assert testee.write_template('sitename', 'fnaam', 'data') == ('called save_to with args'
                                                                    f" `{fullname}`, `data`")

    def test_create_new_doc(self, monkeypatch, capsys):
        """unittest for docs2fs.create_new_doc
        """
        def mock_touch(self, *args, **kwargs):
            """stub
            """
            print(f'called touch() for `{self}`')
        with pytest.raises(AttributeError):
            testee.create_new_doc('sitename', '')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        with pytest.raises(FileNotFoundError):
            testee.create_new_doc('sitename', 'docname')
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        path = testee.WEBROOT / 'sitename' / '.source' / ('docname' + '.rst')
        testee.create_new_doc('sitename', 'docname')
        assert capsys.readouterr().out == f'called touch() for `{path}`\n'
        # path = testee.WEBROOT / 'sitename' / '.source'
        testee.create_new_doc('sitename', 'docname.rst')
        assert capsys.readouterr().out == f'called touch() for `{path}`\n'
        path = testee.WEBROOT / 'sitename' / '.source' / 'directory' / ('docname' + '.rst')
        testee.create_new_doc('sitename', 'docname', 'directory')
        assert capsys.readouterr().out == f'called touch() for `{path}`\n'

    def test_get_doc_contents(self, monkeypatch):
        """unittest for docs2fs.get_doc_contents
        """
        def mock_read_data(*args):
            """stub
            """
            return '', f'read data from `{args[0]}`'
        def mock_read_data_mld(*args):
            """stub
            """
            return 'read data failed', ''
        with pytest.raises(AttributeError):
            testee.get_doc_contents('sitename', '')
        monkeypatch.setattr(testee, 'read_data', mock_read_data_mld)
        with pytest.raises(FileNotFoundError):
            testee.get_doc_contents('sitename', 'docname')
        monkeypatch.setattr(testee, 'read_data', mock_read_data)
        path = testee.WEBROOT / 'sitename' / '.source' / 'docname.rst'
        oldpath = testee.WEBROOT / 'sitename' / '.source' / 'docname.rst.bak'
        assert testee.get_doc_contents('sitename', 'docname') == f'read data from `{path}`'
        assert testee.get_doc_contents('sitename', 'docname', previous=True) == (
                f'read data from `{oldpath}`')
        assert testee.get_doc_contents('sitename', 'docname.rst') == (
                f'read data from `{path}`')
        assert testee.get_doc_contents('sitename', 'docname.rst', previous=True) == (
                f'read data from `{oldpath}`')
        path = testee.WEBROOT / 'sitename' / '.target' / 'docname.html'
        oldpath = testee.WEBROOT / 'sitename' / '.target' / 'docname.html.bak'
        assert testee.get_doc_contents('sitename', 'docname', 'dest') == (
                f'read data from `{path}`')
        assert testee.get_doc_contents('sitename', 'docname', 'dest', previous=True) == (
                f'read data from `{oldpath}`')
        path = testee.WEBROOT / 'sitename' / '.source' / 'directory' / 'docname.rst'
        assert testee.get_doc_contents('sitename', 'docname', 'src', 'directory') == (
                f'read data from `{path}`')

    def test_update_rst(self, monkeypatch, capsys):
        """unittest for docs2fs.update_rst
        """
        def mock_list_docs_none(*args):
            """stub
            """
            return []
        def mock_list_docs(*args):
            """stub
            """
            return ['doc_name', 'doc_name.rst']
        def mock_save_to(*args):
            """stub
            """
            print(f'call save_to(): save `{args[1]}` in `{args[0]}`')
        with pytest.raises(AttributeError):
            testee.update_rst('sitename', '', '')
        with pytest.raises(AttributeError):
            testee.update_rst('sitename', 'doc_name', '')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            testee.update_rst('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        testee.update_rst('sitename', 'doc_name', 'contents')
        path = testee.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        assert capsys.readouterr().out == f'call save_to(): save `contents` in `{path}`\n'
        testee.update_rst('sitename', 'doc_name.rst', 'contents', 'directory')
        path = testee.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        assert capsys.readouterr().out == f'call save_to(): save `contents` in `{path}`\n'

    def test_revert_rst(self, monkeypatch, capsys):
        """unittest for docs2fs.revert_rst
        """
        def mock_list_docs_none(*args):
            """stub
            """
            return []
        def mock_list_docs(*args):
            """stub
            """
            return ['doc_name', 'doc_name.rst']
        def mock_rename(self, *args):
            """stub
            """
            print(f'call rename() to replace `{args[0]}` with `{self}`')
        def mock_rename_err(self, *args):
            """stub
            """
            raise FileNotFoundError
        with pytest.raises(AttributeError):
            testee.revert_rst('sitename', '')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            testee.revert_rst('sitename', 'doc_name')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename_err)
        with pytest.raises(FileNotFoundError):
            testee.revert_rst('sitename', 'doc_name')
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename)
        testee.revert_rst('sitename', 'doc_name')
        path = testee.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        assert capsys.readouterr().out == f'call rename() to replace `{path}` with `{path}.bak`\n'
        testee.revert_rst('sitename', 'doc_name.rst', 'directory')
        path = testee.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        assert capsys.readouterr().out == f'call rename() to replace `{path}` with `{path}.bak`\n'

    def test_mark_src_deleted(self, monkeypatch, capsys):
        """unittest for docs2fs.mark_src_deleted
        """
        def mock_list_docs_none(*args):
            """stub
            """
            return []
        def mock_list_docs(*args):
            """stub
            """
            return ['doc_name', 'doc_name.rst']
        def mock_rename(self, *args):
            """stub
            """
            print(f'call rename(): from `{self}` to `{args[0]}`')
        with pytest.raises(AttributeError):
            testee.mark_src_deleted('sitename', '')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            testee.mark_src_deleted('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename)
        testee.mark_src_deleted('sitename', 'doc_name')
        path = testee.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        path_n = testee.WEBROOT / 'sitename' / '.source' / ('doc_name' + testee.DELMARK)
        assert capsys.readouterr().out == f'call rename(): from `{path}` to `{path_n}`\n'
        testee.mark_src_deleted('sitename', 'doc_name.rst', 'directory')
        path = testee.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        path_n = testee.WEBROOT / 'sitename' / '.source' / 'directory' / ('doc_name' + testee.DELMARK)
        assert capsys.readouterr().out == f'call rename(): from `{path}` to `{path_n}`\n'

    def test_update_html(self, monkeypatch, capsys):
        """unittest for docs2fs.update_html
        """
        def mock_list_docs_none(*args):
            """stub
            """
            return []
        def mock_list_docs(*args):
            """stub
            """
            return ['doc_name', 'doc_name.html']
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() for `{self}`')
        def mock_save_to(*args):
            """stub
            """
            print(f'call save_to(): save `{args[1]}` in `{args[0]}`')
        with pytest.raises(AttributeError):
            testee.update_html('sitename', '', '')
        with pytest.raises(AttributeError):
            testee.update_html('sitename', 'doc_name', '')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            testee.update_html('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(testee, 'list_docs', mock_list_docs)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        path = testee.WEBROOT / 'sitename' / '.target' / 'doc_name.html'
        testee.update_html('sitename', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        testee.update_html('sitename', 'doc_name.html', 'contents', '/', dry_run=False)
        assert capsys.readouterr().out == ''.join((f'called mkdir() for `{path.parent}`\n',
                                                   f'call save_to(): save `contents` in `{path}`\n'))
        path = testee.WEBROOT / 'sitename' / '.target' / 'directory' / 'doc_name.html'
        testee.update_html('sitename', 'doc_name', 'contents', 'directory', dry_run=False)
        assert capsys.readouterr().out == ''.join((f'called mkdir() for `{path.parent}`\n',
                                                   f'call save_to(): save `contents` in `{path}`\n'))

    def test_list_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2fs.list_deletions_target
        """
        def mock_build_dirlist(*args):
            """stub
            """
            if args[1] == '':
                return ['/']
            if args[1] == '*':
                return ['/', 'subdir']
            return [args[1]]
        def mock_glob(self, *args):
            """stub
            """
            name = str(self.relative_to(testee.WEBROOT / 'sitename'))
            print('called path.glob() for', args[0], 'in', name)
            return [self / 'file1.deleted', self / 'file2.deleted']
        monkeypatch.setattr(testee, 'build_dirlist', mock_build_dirlist)
        monkeypatch.setattr(testee.pathlib.Path, 'glob', mock_glob)
        assert testee.list_deletions_target('sitename', '') == ['file1', 'file2']
        assert capsys.readouterr().out == "called path.glob() for *.deleted in .source\n"
        assert testee.list_deletions_target('sitename', '*') == ['file1', 'file2', 'subdir/file1',
                                                               'subdir/file2']
        assert capsys.readouterr().out == ("called path.glob() for *.deleted in .source\n"
                                           "called path.glob() for *.deleted in .source/subdir\n")
        assert testee.list_deletions_target('sitename', 'dirname') == ['dirname/file1', 'dirname/file2']
        assert capsys.readouterr().out == "called path.glob() for *.deleted in .source/dirname\n"

    def test_apply_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2fs.apply_deletions_target
        """
        def mock_build_dirlist(*args):
            """stub
            """
            if args[1] == '':
                return ['/']
            if args[1] == '*':
                return ['/', 'subdir']
            return [args[1]]
        def mock_glob(self, *args, **kwargs):
            """stub
            """
            name = str(self.relative_to(testee.WEBROOT / 'sitename'))
            print('called path.glob() for', args[0], 'in', name)
            return [self / 'file1.deleted', self / 'file2.deleted']
        def mock_unlink(self, *args, **kwargs):
            """stub
            """
            print(f'called unlink with args `{self}`', args, kwargs)
        def mock_rename(self, *args, **kwargs):
            """stub
            """
            print(f'called rename with args `{self}`', args, kwargs)
        def mock_touch(self, *args, **kwargs):
            """stub
            """
            print(f'created file `{self}`')
        monkeypatch.setattr(testee, 'build_dirlist', mock_build_dirlist)
        monkeypatch.setattr(testee.pathlib.Path, 'glob', mock_glob)
        monkeypatch.setattr(testee.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(testee.pathlib.Path, 'rename', mock_rename)
        monkeypatch.setattr(testee.pathlib.Path, 'touch', mock_touch)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        old = testee.WEBROOT / 'sitename' / '.source'
        loc = testee.WEBROOT / 'sitename' / '.target'
        assert testee.apply_deletions_target('sitename', '') == ['file1', 'file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .source\n'
                f"called unlink with args `{old}/file1.deleted` () {{}}\n"
                f"called unlink with args `{old}/file1.rst.bak` () {{'missing_ok': True}}\n"
                f"called unlink with args `{old}/file2.deleted` () {{}}\n"
                f"called unlink with args `{old}/file2.rst.bak` () {{'missing_ok': True}}\n"
                f"called rename with args `{loc}/file1.html` ({loc / 'file1.deleted'!r},) {{}}\n"
                f"called rename with args `{loc}/file2.html` ({loc / 'file2.deleted'!r},) {{}}\n")
        oldsub = testee.WEBROOT / 'sitename' / '.source' / 'subdir'
        locsub = testee.WEBROOT / 'sitename' / '.target' / 'subdir'
        assert testee.apply_deletions_target('sitename', '*') == ['file1', 'file2', 'subdir/file1',
                                                                'subdir/file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .source\n'
                f'called unlink with args `{old}/file1.deleted` () {{}}\n'
                f"called unlink with args `{old}/file1.rst.bak` () {{'missing_ok': True}}\n"
                f'called unlink with args `{old}/file2.deleted` () {{}}\n'
                f"called unlink with args `{old}/file2.rst.bak` () {{'missing_ok': True}}\n"
                'called path.glob() for *.deleted in .source/subdir\n'
                f'called unlink with args `{oldsub}/file1.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file1.rst.bak` () {{'missing_ok': True}}\n"
                f'called unlink with args `{oldsub}/file2.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file2.rst.bak` () {{'missing_ok': True}}\n"
                f"called rename with args `{loc}/file1.html` ({loc / 'file1.deleted'!r},) {{}}\n"
                f"called rename with args `{loc}/file2.html` ({loc / 'file2.deleted'!r},) {{}}\n"
                f"called rename with args `{locsub}/file1.html` ({locsub / 'file1.deleted'!r},)"
                " {}\n"
                f"called rename with args `{locsub}/file2.html` ({locsub / 'file2.deleted'!r},)"
                " {}\n")
        oldsub = testee.WEBROOT / 'sitename' / '.source' / 'dirname'
        locsub = testee.WEBROOT / 'sitename' / '.target' / 'dirname'
        assert testee.apply_deletions_target('sitename', 'dirname') == ['dirname/file1',
                                                                      'dirname/file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .source/dirname\n'
                f'called unlink with args `{oldsub}/file1.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file1.rst.bak` () {{'missing_ok': True}}\n"
                f'called unlink with args `{oldsub}/file2.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file2.rst.bak` () {{'missing_ok': True}}\n"
                f"called rename with args `{locsub}/file1.html` ({locsub / 'file1.deleted'!r},)"
                " {}\n"
                f"called rename with args `{locsub}/file2.html` ({locsub / 'file2.deleted'!r},)"
                " {}\n")
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        testee.apply_deletions_target('sitename', 'dirname')
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .source/dirname\n'
                f'called unlink with args `{oldsub}/file1.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file1.rst.bak` () {{'missing_ok': True}}\n"
                f'called unlink with args `{oldsub}/file2.deleted` () {{}}\n'
                f"called unlink with args `{oldsub}/file2.rst.bak` () {{'missing_ok': True}}\n"
                f'created file `{locsub}/file1.deleted`\n'
                f'created file `{locsub}/file2.deleted`\n')

    def test_update_mirror(self, monkeypatch, capsys):
        """unittest for docs2fs.update_mirror
        """
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() for `{self}`')
        def mock_save_to(*args):
            """stub
            """
            print(f'called save_to(): save `{args[1]}` in `{args[0]}`')
        with pytest.raises(AttributeError):
            testee.update_mirror('sitename', '', 'data')
        with pytest.raises(AttributeError):
            testee.update_mirror('sitename', 'doc_name', '')
        monkeypatch.setattr(testee.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(testee, 'save_to', mock_save_to)
        loc = testee.WEBROOT / 'sitename' / 'doc_name.html'
        testee.update_mirror('sitename', 'doc_name', 'data')
        assert capsys.readouterr().out == ''
        testee.update_mirror('sitename', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == f'called save_to(): save `data` in `{loc}`\n'
        testee.update_mirror('sitename', 'doc_name.rst', 'data', dry_run=False)
        assert capsys.readouterr().out == f'called save_to(): save `data` in `{loc}`\n'
        testee.update_mirror('sitename', 'doc_name.html', 'data', '/', dry_run=False)
        assert capsys.readouterr().out == f'called save_to(): save `data` in `{loc}`\n'
        loc = testee.WEBROOT / 'sitename' / 'directory' / 'doc_name.html'
        testee.update_mirror('sitename', 'doc_name.html', 'data', 'directory', dry_run=False)
        assert capsys.readouterr().out == ''.join((f'called mkdir() for `{loc.parent}`\n',
                                                   f'called save_to(): save `data` in `{loc}`\n'))

    def test_list_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2fs.list_deletions_mirror
        """
        def mock_build_dirlist(*args):
            """stub
            """
            if args[1] == '':
                return ['/']
            if args[1] == '*':
                return ['/', 'subdir']
            return [args[1]]
        def mock_glob(self, *args):
            """stub
            """
            name = str(self.relative_to(testee.WEBROOT / 'sitename'))
            print('called path.glob() for', args[0], 'in', name)
            return [self / 'file1.deleted', self / 'file2.deleted']
        monkeypatch.setattr(testee, 'build_dirlist', mock_build_dirlist)
        monkeypatch.setattr(testee.pathlib.Path, 'glob', mock_glob)
        assert testee.list_deletions_mirror('sitename', '') == ['file1', 'file2']
        assert capsys.readouterr().out == "called path.glob() for *.deleted in .target\n"
        assert testee.list_deletions_mirror('sitename', '*') == ['file1', 'file2', 'subdir/file1',
                                                               'subdir/file2']
        assert capsys.readouterr().out == ("called path.glob() for *.deleted in .target\n"
                                           "called path.glob() for *.deleted in .target/subdir\n")
        assert testee.list_deletions_mirror('sitename', 'dirname') == ['dirname/file1', 'dirname/file2']
        assert capsys.readouterr().out == "called path.glob() for *.deleted in .target/dirname\n"

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2fs.apply_deletions_mirror
        """
        def mock_build_dirlist(*args):
            """stub
            """
            if args[1] == '':
                return ['/']
            if args[1] == '*':
                return ['/', 'subdir']
            return [args[1]]
        def mock_glob(self, *args, **kwargs):
            """stub
            """
            name = str(self.relative_to(testee.WEBROOT / 'sitename'))
            print('called path.glob() for', args[0], 'in', name)
            if testee.DELMARK in args[0]:
                return [self / 'file1.deleted', self / 'file2.deleted']
            return [self / 'index.html', self / 'index.html.bak']
        def mock_unlink(self, *args, **kwargs):
            """stub
            """
            print(f'deleted file `{self}`', kwargs)
        def mock_rmdir(self, *args, **kwargs):
            """stub
            """
            print(f'deleted directory `{self}`')
        monkeypatch.setattr(testee, 'build_dirlist', mock_build_dirlist)
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': False})
        monkeypatch.setattr(testee.pathlib.Path, 'glob', mock_glob)
        monkeypatch.setattr(testee.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(testee.pathlib.Path, 'rmdir', mock_rmdir)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', lambda x: [])
        src = testee.WEBROOT / 'sitename' / '.target'
        dest = testee.WEBROOT / 'sitename'
        assert testee.apply_deletions_mirror('sitename', '') == ['file1', 'file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .target\n'
                f'deleted file `{src}/file1.deleted` {{}}\n'
                f"deleted file `{src}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{src}/file2.deleted` {{}}\n'
                f"deleted file `{src}/file2.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{dest}/file1.html` {{}}\n'
                f"deleted file `{dest}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{dest}/file2.html` {{}}\n'
                f"deleted file `{dest}/file2.html.bak` {{'missing_ok': True}}\n")
        srcsub = testee.WEBROOT / 'sitename' / '.target' / 'subdir'
        destsub = testee.WEBROOT / 'sitename' / 'subdir'
        assert testee.apply_deletions_mirror('sitename', '*') == ['file1', 'file2', 'subdir/file1',
                                                                'subdir/file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .target\n'
                f'deleted file `{src}/file1.deleted` {{}}\n'
                f"deleted file `{src}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{src}/file2.deleted` {{}}\n'
                f"deleted file `{src}/file2.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for *.deleted in .target/subdir\n'
                f'deleted file `{srcsub}/file1.deleted` {{}}\n'
                f"deleted file `{srcsub}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{srcsub}/file2.deleted` {{}}\n'
                f"deleted file `{srcsub}/file2.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{dest}/file1.html` {{}}\n'
                f"deleted file `{dest}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{dest}/file2.html` {{}}\n'
                f"deleted file `{dest}/file2.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{destsub}/file1.html` {{}}\n'
                f"deleted file `{destsub}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{destsub}/file2.html` {{}}\n'
                f"deleted file `{destsub}/file2.html.bak` {{'missing_ok': True}}\n")
        srcsub = testee.WEBROOT / 'sitename' / '.target' / 'dirname'
        destsub = testee.WEBROOT / 'sitename' / 'dirname'
        assert testee.apply_deletions_mirror('sitename', 'dirname') == ['dirname/file1',
                                                                      'dirname/file2']
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .target/dirname\n'
                f'deleted file `{srcsub}/file1.deleted` {{}}\n'
                f"deleted file `{srcsub}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{srcsub}/file2.deleted` {{}}\n'
                f"deleted file `{srcsub}/file2.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{destsub}/file1.html` {{}}\n'
                f"deleted file `{destsub}/file1.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{destsub}/file2.html` {{}}\n'
                f"deleted file `{destsub}/file2.html.bak` {{'missing_ok': True}}\n")

        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        testee.apply_deletions_mirror('sitename', 'directory')
        loc = testee.WEBROOT / 'sitename' / '.target' / 'directory'
        dest = testee.WEBROOT / 'sitename' / 'directory'
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .target/directory\n'
                f'deleted file `{loc}/file1.deleted` {{}}\n'
                f"deleted file `{loc}/file1.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in .target/directory/file1\n'
                f"deleted file `{loc}/file1/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{loc}/file1/index.html.bak` {{'missing_ok': True}}\n"
                f"deleted directory `{loc}/file1`\n"
                f'deleted file `{loc}/file2.deleted` {{}}\n'
                f"deleted file `{loc}/file2.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in .target/directory/file2\n'
                f"deleted file `{loc}/file2/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{loc}/file2/index.html.bak` {{'missing_ok': True}}\n"
                f"deleted directory `{loc}/file2`\n"
                'called path.glob() for index.html* in directory/file1\n'
                f"deleted file `{dest}/file1/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{dest}/file1/index.html.bak` {{'missing_ok': True}}\n"
                f"deleted directory `{dest}/file1`\n"
                'called path.glob() for index.html* in directory/file2\n'
                f"deleted file `{dest}/file2/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{dest}/file2/index.html.bak` {{'missing_ok': True}}\n"
                f"deleted directory `{dest}/file2`\n")

        monkeypatch.setattr(testee.pathlib.Path, 'iterdir', lambda x: ['x'])
        testee.apply_deletions_mirror('sitename', 'directory')
        assert capsys.readouterr().out == (
                'called path.glob() for *.deleted in .target/directory\n'
                f'deleted file `{loc}/file1.deleted` {{}}\n'
                f"deleted file `{loc}/file1.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in .target/directory/file1\n'
                f"deleted file `{loc}/file1/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{loc}/file1/index.html.bak` {{'missing_ok': True}}\n"
                f'deleted file `{loc}/file2.deleted` {{}}\n'
                f"deleted file `{loc}/file2.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in .target/directory/file2\n'
                f"deleted file `{loc}/file2/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{loc}/file2/index.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in directory/file1\n'
                f"deleted file `{dest}/file1/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{dest}/file1/index.html.bak` {{'missing_ok': True}}\n"
                'called path.glob() for index.html* in directory/file2\n'
                f"deleted file `{dest}/file2/index.html` {{'missing_ok': True}}\n"
                f"deleted file `{dest}/file2/index.html.bak` {{'missing_ok': True}}\n")

    def test_build_dirlist(self, monkeypatch):
        """unittest for docs2fs.build_dirlist
        """
        def mock_list_dirs(*args):
            """stub
            """
            return ['subdir1', 'subdir2']
        monkeypatch.setattr(testee, 'list_dirs', mock_list_dirs)
        assert testee.build_dirlist('sitename', '') == ['/']
        assert testee.build_dirlist('sitename', '*') == ['/', 'subdir1', 'subdir2']
        assert testee.build_dirlist('sitename', 'dirname') == ['dirname']

    def test_remove_doc(self):
        """unittest for docs2fs.remove_doc
        """
        with pytest.raises(NotImplementedError):
            testee.remove_doc('sitename', 'docname')

    def test_get_doc_stats(self, monkeypatch):
        """unittest for docs2fs.get_doc_stats
        """
        def mock_stat(self, *args, **kwargs):
            """stub
            """
            result = types.SimpleNamespace()
            result.st_mtime = 1
            return result
        monkeypatch.setattr(testee, 'read_settings', lambda x: {'seflinks': True})
        # monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(testee.pathlib.Path, 'stat', mock_stat)
        assert testee.get_doc_stats('sitename', 'docname') == testee.Stats(
                testee.datetime.datetime.min,
                testee.datetime.datetime.min,
                testee.datetime.datetime.min)
        monkeypatch.setattr(testee.pathlib.Path, 'exists', lambda x: True)
        assert testee.get_doc_stats('sitename', 'docname.rst', 'dirname') == testee.Stats(
                testee.datetime.datetime.fromtimestamp(1),
                testee.datetime.datetime.fromtimestamp(1),
                testee.datetime.datetime.fromtimestamp(1))

    def test_get_all_doc_stats(self, monkeypatch):
        """unittest for docs2fs.get_all_doc_stats
        """
        def mock_get_dir_stats(*args):
            """stub
            """
            return 'hello, world!'
        def mock_list_dirs(*args):
            """stub
            """
            return 'x', 'y'
        monkeypatch.setattr(testee, '_get_dir_stats', mock_get_dir_stats)
        monkeypatch.setattr(testee, 'list_dirs', mock_list_dirs)
        assert testee.get_all_doc_stats('sitename') == [('/', 'hello, world!'),
                                                      ('x', 'hello, world!'),
                                                      ('y', 'hello, world!')]
