import os
import pathlib
import pytest
import docs2fs as dmlf


def mock_settings_seflinks_yes(*args):
    return {'seflinks': True}


def mock_settings_seflinks_no(*args):
    return {}


def return_true(*args):
    return True


def return_false(*args):
    return False


def mock_copyfile(*args):
    print('called copyfile: from `{}` to `{}`'.format(args[0], args[1]))


def test_locify():
    path = pathlib.Path('test')
    assert dmlf._locify(path) == path / '.source'
    assert dmlf._locify(path, '') == path / '.source'
    assert dmlf._locify(path, 'src') == path / '.source'
    assert dmlf._locify(path, 'dest') == path / '.target'
    assert dmlf._locify(path, 'mirror') == path
    with pytest.raises(ValueError):
        dmlf._locify(path, 'x')


class TestNonApiFunctions:
    def test_get_dir_ftype_stats(self, monkeypatch):
        def mock_locify(*args):
            return pathlib.Path('.')
        def mock_is_file(*args):
            return True if args[0].suffix else False
        def mock_is_dir(*args):
            return False if args[0].suffix else True
        def mock_iterdir_src(*args):
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'),
                    pathlib.Path('index.rst'), pathlib.Path('test.src'))
        def mock_iterdir_dest(*args):
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'),
                    pathlib.Path('index.html'), pathlib.Path('test.src'))
        def mock_iterdir_dest_sef(*args):
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('hello'),
                    pathlib.Path('kitty'))
        def mock_relative_to(*args):
            return args[0]
        def mock_stat(*args):
            import types
            result = types.SimpleNamespace()
            result.st_mtime = 'x'
            return result
        def mock_stat_error(*args):
            raise FileNotFoundError
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir_src)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', mock_is_file)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', mock_is_dir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_symlink', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'relative_to', mock_relative_to)
        monkeypatch.setattr(dmlf.pathlib.Path, 'stat', mock_stat)
        assert dmlf._get_dir_ftype_stats('sitename', 'src') == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_symlink', return_false)
        assert dmlf._get_dir_ftype_stats('sitename', 'src', '') == [('index', 'x')]

        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir_dest)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_symlink', return_true)
        assert dmlf._get_dir_ftype_stats('sitename', 'dest') == [('index', 'x')]
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_symlink', return_false)
        assert dmlf._get_dir_ftype_stats('sitename', 'dest') == [('subdir', 'x'),
                                                                       ('index', 'x')]
        # import pdb; pdb.set_trace()
        assert dmlf._get_dir_ftype_stats('sitename', 'dest', 'dirname') == [('subdir', 'x')]
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_no)
        assert dmlf._get_dir_ftype_stats('sitename', 'dest', 'dirname') == [('index', 'x')]
        monkeypatch.setattr(dmlf.pathlib.Path, 'stat', mock_stat_error)
        assert dmlf._get_dir_ftype_stats('sitename', 'dest', 'dirname') == []

    def test_get_dir_stats(self, monkeypatch):
        def mock_get_dir_ftype_stats(*args):
            return ('name2', 2), ('name1', 1)
        monkeypatch.setattr(dmlf, '_get_dir_ftype_stats', mock_get_dir_ftype_stats)
        time1 = dmlf.datetime.datetime.fromtimestamp(1)
        time2 = dmlf.datetime.datetime.fromtimestamp(2)
        assert dmlf._get_dir_stats('testsite') == [('name1', dmlf.Stats(time1, time1, time1)),
                                                   ('name2', dmlf.Stats(time2, time2, time2))]

    def test_get_dir_stats_for_docitem(self, monkeypatch):
        def mock_get_dir_ftype_stats(*args):
            return ('name2', 2), ('name1', 1)
        monkeypatch.setattr(dmlf, '_get_dir_ftype_stats', mock_get_dir_ftype_stats)
        time1 = dmlf.datetime.datetime.fromtimestamp(1)
        time2 = dmlf.datetime.datetime.fromtimestamp(2)
        assert dmlf._get_dir_stats_for_docitem('testsite') == {'name1': {'dest': {'docid': 4,
                                                                                   'updated': time1},
                                                                          'mirror': {'updated': time1},
                                                                          'src': {'docid': 2,
                                                                                  'updated': time1}},
                                                                'name2': {'dest': {'docid': 3,
                                                                                   'updated': time2},
                                                                          'mirror': {'updated': time2},
                                                                          'src': {'docid': 1,
                                                                                  'updated': time2}}}

    def test_get_sitedoc_data(self, monkeypatch):
        def mock_get_docitem_stats(*args):
            return 'hello, world!'
        def mock_list_dirs(*args):
            return 'x', 'y'
        monkeypatch.setattr(dmlf, '_get_dir_stats_for_docitem', mock_get_docitem_stats)
        monkeypatch.setattr(dmlf, 'list_dirs', mock_list_dirs)
        assert dmlf._get_sitedoc_data('sitename') == {'/': 'hello, world!', 'x': 'hello, world!',
                                                      'y': 'hello, world!'}

    def test_read_data(self, monkeypatch, capsys):
        with open('/tmp/dmlftmpfile', 'w') as out:
            out.write('regel 1\rregel 2\r\nregel 3\n')
        with open('/tmp/dmlftmpfileiso', 'w', encoding='iso-8859-1') as out:
            out.write('règle 1\rrègle 2\r\nrègle 3\n')
        def mock_relative_to(self, *args):
            return self
        def mock_open_utf(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            return open('/tmp/dmlftmpfile')
        def mock_open_utf_err(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            raise IOError('IO error on utf file')
        def mock_open_iso(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            # if kwargs['encoding'] != 'iso-8859-1':
            #     raise UnicodeDecodeError
            return open('/tmp/dmlftmpfileiso')
        def mock_open_iso_err(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            # if kwargs['encoding'] != 'iso-8859-1':
            #     raise UnicodeDecodeError
            open('/tmp/dmlftmpfileiso')
            raise IOError('IO error on iso file')
        def mock_readlines(*args):
            return ['regel 1\r', 'regel 2\r\n', 'regel 3\n']
        monkeypatch.setattr(dmlf.pathlib.Path, 'relative_to',  mock_relative_to)
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open',  mock_open_utf)
        assert dmlf.read_data(pathlib.Path('sitename/docname.rst')) == ('',
                                                                        'regel 1\nregel 2\nregel 3\n')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'
        assert dmlf.read_data(pathlib.Path('sitename/docname.html')) == ('',
                                                                        'regel 1\nregel 2\nregel 3\n')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname/index.html`\n'
        monkeypatch.setattr(dmlf.pathlib.Path, 'open',  mock_open_utf_err)
        assert dmlf.read_data(pathlib.Path('sitename/docname.rst')) == ('IO error on utf file', '')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_no)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open',  mock_open_iso)
        # blijkbaar gaat dit ook mis als hij het iso file gaat proberen te lezen...
        # assert dmlf.read_data(pathlib.Path('sitename/docname.html')) == ('',
        #                                                                 'regel 1\nregel 2\nregel 3\n')
        # assert capsys.readouterr().out == 'called open() for file `sitename/docname.html`\n'
        monkeypatch.setattr(dmlf.pathlib.Path, 'open',  mock_open_iso_err)
        assert dmlf.read_data(pathlib.Path('sitename/docname.rst')) == ('IO error on iso file', '')
        assert capsys.readouterr().out == 'called open() for file `sitename/docname.rst`\n'

    def test_save_to(self, monkeypatch, capsys):
        tmpfilename = '/tmp/dmlfsaveto'
        def mock_open_err(self, *args, **kwargs):
            raise OSError
        def mock_open(self, *args, **kwargs):
            return open(tmpfilename, 'w')
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir for `{}`'.format(self))
        def mock_replace(self, *args, **kwargs):
            print('called replace for `{}` with `{}`'.format(self, args[0]))
        def read_and_remove(filename):
            with open(filename) as read_file:
                data = read_file.read()
            os.unlink(filename)
            return data
        fulldocname = dmlf.WEBROOT / 'testsite'/ 'docname'
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_no)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open_err)
        assert dmlf.save_to(fulldocname, 'data') == 'OSError without message'
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        monkeypatch.setattr(dmlf.shutil, 'copyfile', mock_copyfile)
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open)
        assert dmlf.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == ''
        assert read_and_remove(tmpfilename) == 'data'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        fulldocname = dmlf.WEBROOT / 'testsite'/ 'docname.rst'
        assert dmlf.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == 'called copyfile: from `{}` to `{}`\n'.format(
            str(fulldocname), str(fulldocname) + '.bak')
        assert read_and_remove(tmpfilename) == 'data'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        fulldocname = dmlf.WEBROOT / 'testsite'/ 'docname.html'
        assert dmlf.save_to(fulldocname, 'data') == ''
        assert capsys.readouterr().out == 'called mkdir for `{}`\n'.format(
            str(fulldocname).replace('.html', ''))
        assert read_and_remove(tmpfilename) == 'data'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_false)
        monkeypatch.setattr(dmlf.pathlib.Path, 'replace', mock_replace)
        assert dmlf.save_to(fulldocname, 'data') == ''
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
    def test_clear_db(self):
        with pytest.raises(NotImplementedError):
            dmlf.clear_db()

    def test_read_db(self):
        with pytest.raises(NotImplementedError):
            dmlf.read_db()

    def test_list_site_data(self, monkeypatch, capsys):
        def mock_read_settings(*args):
            return 'called read_settings for `{}`'.format(args[0])
        def mock_get_sitedoc_data(*args):
            return 'called get_sitedoc_data for `{}`'.format(args[0])
        def mock_list_docs(*args):
            rest = '/{}'.format(args[2]) if len(args) > 2 else ''
            return ['doc1']
        def mock_list_dirs(*args):
            return ['dir1']
        def mock_read_data(*args):
            return '', 'called read_data for {}'.format(args[0])
        sitename = 'testsite'
        monkeypatch.setattr(dmlf, 'read_settings', mock_read_settings)
        monkeypatch.setattr(dmlf, '_get_sitedoc_data', mock_get_sitedoc_data)
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs)
        monkeypatch.setattr(dmlf, 'list_dirs', mock_list_dirs)
        monkeypatch.setattr(dmlf, 'read_data', mock_read_data)
        siteloc = dmlf.WEBROOT / sitename
        assert dmlf.list_site_data(sitename) == (
            {'_id': 0, 'name': 'testsite',
             'settings': 'called read_settings for `testsite`',
             'docs': 'called get_sitedoc_data for `testsite`'},
            [{'_id': ('dir1/doc1', 'dest'),
              'current': 'called read_data for {}/.target/dir1/doc1.html'.format(siteloc),
              'previous': 'called read_data for {}/.target/dir1/doc1.html.bak'.format(siteloc)},
             {'_id': ('dir1/doc1', 'src'),
              'current': 'called read_data for {}/.source/dir1/doc1.rst'.format(siteloc),
              'previous': 'called read_data for {}/.source/dir1/doc1.rst.bak'.format(siteloc)},
             {'_id': ('doc1', 'dest'),
              'current': 'called read_data for {}/.target/doc1.html'.format(siteloc),
              'previous': 'called read_data for {}/.target/doc1.html.bak'.format(siteloc)},
             {'_id': ('doc1', 'src'),
              'current': 'called read_data for {}/.source/doc1.rst'.format(siteloc),
              'previous': 'called read_data for {}/.source/doc1.rst.bak'.format(siteloc)}])

    def test_clear_site_data(self, monkeypatch, capsys):
        def mock_rmtree_ok(*args):
            print('called rmtree for `{}`'.format(args[0]))
        def mock_rmtree_err(*args):
            raise FileNotFoundError
        sitename = 'testsite'
        monkeypatch.setattr(dmlf.shutil, 'rmtree', mock_rmtree_ok)
        dmlf.clear_site_data(sitename)
        assert capsys.readouterr().out == 'called rmtree for `{}`\n'.format(dmlf.WEBROOT / sitename)
        monkeypatch.setattr(dmlf.shutil, 'rmtree', mock_rmtree_err)
        dmlf.clear_site_data(sitename)
        assert capsys.readouterr().out == ''


class TestSiteLevel:
    def test_list_sites(self, monkeypatch):
        def mock_iterdir(*args):
            return [pathlib.Path(x) for x in ('y', 'z')]
        def mock_is_dir_yes(*args):
            return True
        def mock_is_dir_no(*args):
            return False
        def mock_exists_yes(*args):
            return True
        def mock_exists_no(*args):
            return False
        def mock_is_file_yes(*args):
            return True
        def mock_is_file_no(*args):
            return False
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', mock_is_dir_no)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', mock_is_file_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', mock_exists_yes)
        assert dmlf.list_sites() == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', mock_is_dir_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', mock_is_file_no)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', mock_exists_yes)
        assert dmlf.list_sites() == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', mock_is_dir_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', mock_is_file_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', mock_exists_yes)
        assert dmlf.list_sites() == ['y', 'z']

    def test_create_new_site(self, monkeypatch, capsys):
        def mock_mkdir_err(self, *args, **kwargs):
            raise FileExistsError
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir for `{}`'.format(self))
        def mock_touch(self, *args, **kwargs):
            print('called touch for `{}`'.format(self))
        sitename = 'testsite'
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir_err)
        with pytest.raises(FileExistsError):
            dmlf.create_new_site(sitename)
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'touch', mock_touch)
        dmlf.create_new_site(sitename)
        siteloc = str(dmlf.WEBROOT / sitename)
        assert capsys.readouterr().out == ''.join((
            'called mkdir for `{}`\n'.format(siteloc),
            'called mkdir for `{}`\n'.format(siteloc + '/.source'),
            'called mkdir for `{}`\n'.format(siteloc + '/.target'),
            'called touch for `{}`\n'.format(siteloc + '/settings.yml')))

    def test_rename_site(self):
        with pytest.raises(NotImplementedError):
            dmlf.rename_site('sitename', 'newname')

    def test_read_settings(self, monkeypatch, capsys):
        with open('/tmp/dmlfreadsett', 'w') as out:
            out.write('regel 1\rregel 2\r\nregel 3\n')
        def mock_open(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            return open('/tmp/dmlfreadsett')
        def mock_load_config_data(*args):
            return {'x': 'y'}
        def mock_load_config_data_2(*args):
            return None
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open)
        monkeypatch.setattr(dmlf, 'load_config_data', mock_load_config_data)
        sitename = 'testsite'
        assert dmlf.read_settings(sitename) == {'x': 'y'}
        settfile = dmlf.WEBROOT / sitename / dmlf.SETTFILE
        assert capsys.readouterr().out == 'called open() for file `{}`\n'.format(settfile)
        monkeypatch.setattr(dmlf, 'load_config_data', mock_load_config_data_2)
        assert dmlf.read_settings(sitename) == {}
        settfile = dmlf.WEBROOT / sitename / dmlf.SETTFILE
        assert capsys.readouterr().out == 'called open() for file `{}`\n'.format(settfile)

    def test_update_settings(self, monkeypatch, capsys):
        def mock_open(self, *args, **kwargs):
            print('called open() for file `{}`'.format(self))
            return open('/tmp/dmlfupd_sett', 'w')
        def mock_save_config_data(*args, **kwargs):
            print('called save_config_data')
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open)
        monkeypatch.setattr(dmlf, 'save_config_data', mock_save_config_data)
        sitename = 'testsite'
        settfile = dmlf.WEBROOT / sitename / dmlf.SETTFILE
        assert dmlf.update_settings(sitename, {'x': 'y'}) == 'ok'
        assert capsys.readouterr().out == ''.join(('called open() for file `{}`\n'.format(settfile),
                                                   'called save_config_data\n'))
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.shutil, 'copyfile', mock_copyfile)
        assert dmlf.update_settings(sitename, {'x': 'y'}) == 'ok'
        assert capsys.readouterr().out == ''.join((
            'called copyfile: from `{}` to `{}`\n'.format(str(settfile), str(settfile) + '.bak'),
            'called open() for file `{}`\n'.format(settfile),
            'called save_config_data\n'))

    def test_clear_settings(self):
        with pytest.raises(NotImplementedError):
            dmlf.clear_settings('sitename')

    def test_list_dirs(self, monkeypatch, capsys):
        def mock_locify(*args):
            return args[0] / args[1]
        def mock_iterdir(self, *args):
            print('called iterdir for path `{}`'.format(self))
            return (pathlib.Path('.x'), pathlib.Path('css'), pathlib.Path('subdir'))
        sitename = 'testsite'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf, '_locify', mock_locify)
        with pytest.raises(FileNotFoundError):
            dmlf.list_dirs(sitename)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_true)
        assert dmlf.list_dirs(sitename) == ['.x', 'css', 'subdir']
        sitepath = dmlf.WEBROOT / sitename
        assert capsys.readouterr().out == 'called iterdir for path `{}`\n'.format(sitepath)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_false)
        assert dmlf.list_dirs(sitename, loc='dest') == []
        sitepath = dmlf.WEBROOT / sitename / 'dest'
        assert capsys.readouterr().out == 'called iterdir for path `{}`\n'.format(sitepath)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_true)
        assert dmlf.list_dirs(sitename, loc='src') == ['.x', 'css', 'subdir']
        sitepath = dmlf.WEBROOT / sitename / 'src'
        assert capsys.readouterr().out == 'called iterdir for path `{}`\n'.format(sitepath)
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        assert dmlf.list_dirs(sitename, loc='src') == ['.x', 'css', 'subdir']
        assert capsys.readouterr().out == 'called iterdir for path `{}`\n'.format(sitepath)

    def test_create_new_dir(self, monkeypatch, capsys):
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir for `{}`'.format(self))
        def mock_touch(self, *args, **kwargs):
            print('called touch for `{}`'.format(self))
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'touch', mock_touch)
        sitename = 'testsite'
        dirname = 'testdir'
        newdir = dmlf.WEBROOT / sitename / dmlf.SRC_LOC / dirname
        dmlf.create_new_dir(sitename, dirname)
        assert capsys.readouterr().out == ''.join(('called mkdir for `{}`\n'.format(newdir),
                                                   'called touch for `{}`\n'.format(newdir / '.files')))

    def test_remove_dir(self):
        with pytest.raises(NotImplementedError):
            dmlf.remove_dir('sitename', 'directory')


class TestDocLevel:
    def test_list_docs(self, monkeypatch, capsys):
        def mock_exists_1(*args, **kwargs):
            self.times_called += 1
            if self.times_called == 1:
                return True
            return False
        def mock_iterdir(self, *args, **kwargs):
            return [dmlf.pathlib.Path(x) for x in ['file2', 'file3.rst', 'file5.html', 'file1.rst',
                                                   'file4.html', 'file0.deleted']]
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        with pytest.raises(FileNotFoundError):
            dmlf.list_docs('testsite', 'x')
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', mock_exists_1)
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', lambda x: (x for x in []))
        self.times_called = 0
        assert dmlf.list_docs('testsite') == []
        self.times_called = 0
        assert dmlf.list_docs('testsite', 'src', 'subdir') == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', return_false)
        assert dmlf.list_docs('testsite', 'src') == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_file', return_true)
        assert dmlf.list_docs('testsite', 'src') == ['file3', 'file1']
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_no)
        assert dmlf.list_docs('testsite', 'dest') == ['file5', 'file4']
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_false)
        assert dmlf.list_docs('testsite', 'dest', 'directory') == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'is_dir', return_true)
        assert dmlf.list_docs('testsite', 'dest', 'directory') == ['file2', 'file3', 'file5',
                                                                   'file1', 'file4', 'file0']
        assert dmlf.list_docs('testsite', 'dest', ) == ['file2', 'file3', 'file5', 'file1',
                                                        'file4', 'file0', 'index']
        assert dmlf.list_docs('testsite', 'src', deleted=True) == ['file0']

    def test_list_templates(self, monkeypatch, capsys):
        def mock_iterdir(self):
            return (pathlib.Path('x'), pathlib.Path('y.rst'), pathlib.Path('y.html'),
                    pathlib.Path('z.tpl'), pathlib.Path('a.tpl'))
        sitename = 'testsite'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf.pathlib.Path, 'iterdir', mock_iterdir)
        assert dmlf.list_templates(sitename) == []
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        assert dmlf.list_templates(sitename) == ['a.tpl', 'z.tpl']

    def test_read_template(self, monkeypatch, capsys):
        tmpfile = '/tmp/dmlfread_tpl'
        with open(tmpfile, 'w') as out:
            out.write('hello\rhello\r\nhello\n')
        def mock_open(self, *args):
            print('called open() for `{}`'.format(self))
            return open(tmpfile)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open)
        sitename, docname = 'testsite', 'template'
        assert dmlf.read_template(sitename, docname) == 'hello\nhello\nhello\n'
        tplname = dmlf.WEBROOT / sitename / '.templates' / docname
        assert capsys.readouterr().out == 'called open() for `{}`\n'.format(tplname)

    def test_write_template(self, monkeypatch, capsys):
        tmpfilename = '/tmp/dmlfwritetpl'
        def mock_open(self, *args, **kwargs):
            return open(tmpfilename, 'w')
        def mock_open_err(self, *args, **kwargs):
            raise OSError('file open failed')
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir() for `{}`'.format(self))
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf.shutil, 'copyfile', mock_copyfile)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open)
        assert dmlf.write_template('sitename', 'fnaam', 'data') == ''
        loc = dmlf.WEBROOT / 'sitename' / '.templates'
        assert capsys.readouterr().out == 'called mkdir() for `{}`\n'.format(loc)
        with open(tmpfilename) as out:
            testdata = out.read()
        assert testdata == 'data'
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'open', mock_open_err)
        assert dmlf.write_template('sitename', 'fnaam', 'data') == 'file open failed'
        assert capsys.readouterr().out == ''.join((
            'called mkdir() for `{}`\n'.format(loc),
            'called copyfile: from `{0}/fnaam` to `{0}/fnaam.bak`\n'.format(loc)))

    def test_create_new_doc(self, monkeypatch, capsys):
        def mock_touch(self, *args, **kwargs):
            print('called touch() for `{}`'.format(self))
        with pytest.raises(AttributeError):
            dmlf.create_new_doc('sitename', '')
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        with pytest.raises(FileNotFoundError):
            dmlf.create_new_doc('sitename', 'docname')
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'touch', mock_touch)
        path = dmlf.WEBROOT / 'sitename' / '.source' / ('docname' + '.rst')
        dmlf.create_new_doc('sitename', 'docname')
        assert capsys.readouterr().out == 'called touch() for `{}`\n'.format(path)
        # path = dmlf.WEBROOT / 'sitename' / '.source'
        dmlf.create_new_doc('sitename', 'docname.rst')
        assert capsys.readouterr().out == 'called touch() for `{}`\n'.format(path)
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / ('docname' + '.rst')
        dmlf.create_new_doc('sitename', 'docname', 'directory')
        assert capsys.readouterr().out == 'called touch() for `{}`\n'.format(path)

    def test_get_doc_contents(self, monkeypatch, capsys):
        def mock_read_data(*args):
            return '', 'read data from `{}`'.format(args[0])
        def mock_read_data_mld(*args):
            return 'read data failed', ''
        with pytest.raises(AttributeError):
            dmlf.get_doc_contents('sitename', '')
        monkeypatch.setattr(dmlf, 'read_data', mock_read_data_mld)
        with pytest.raises(FileNotFoundError):
            dmlf.get_doc_contents('sitename', 'docname')
        monkeypatch.setattr(dmlf, 'read_data', mock_read_data)
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'docname.rst'
        assert dmlf.get_doc_contents('sitename', 'docname') == 'read data from `{}`'.format(path)
        assert dmlf.get_doc_contents('sitename', 'docname.rst') == ('read data from '
                                                                    '`{}`'.format(path))
        path = dmlf.WEBROOT / 'sitename' / '.target' / 'docname.html'
        assert dmlf.get_doc_contents('sitename', 'docname', 'dest') == ('read data from '
                                                                        '`{}`'.format(path))
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / 'docname.rst'
        assert dmlf.get_doc_contents('sitename', 'docname', 'src',
                                     'directory') == 'read data from `{}`'.format(path)

    def test_update_rst(self, monkeypatch, capsys):
        def mock_list_docs_none(*args):
            return []
        def mock_list_docs(*args):
            return ['doc_name']
        def mock_save_to(*args):
            print('call save_to(): save `{}` in `{}`'.format(args[1], args[0]))
        with pytest.raises(AttributeError):
            dmlf.update_rst('sitename', '', '')
        with pytest.raises(AttributeError):
            dmlf.update_rst('sitename', 'doc_name', '')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            dmlf.update_rst('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs)
        monkeypatch.setattr(dmlf, 'save_to', mock_save_to)
        dmlf.update_rst('sitename', 'doc_name', 'contents')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        assert capsys.readouterr().out == 'call save_to(): save `contents` in `{}`\n'.format(path)
        dmlf.update_rst('sitename', 'doc_name', 'contents', 'directory')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        assert capsys.readouterr().out == 'call save_to(): save `contents` in `{}`\n'.format(path)

    def test_revert_rst(self, monkeypatch, capsys):
        def mock_list_docs_none(*args):
            return []
        def mock_list_docs(*args):
            return ['doc_name']
        def mock_rename(self, *args):
            print('call rename() to replace `{}` with `{}`'.format(args[0], self))
        def mock_rename_err(self, *args):
            raise FileNotFoundError
        with pytest.raises(AttributeError):
            dmlf.revert_rst('sitename', '')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            dmlf.revert_rst('sitename', 'doc_name')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs)
        monkeypatch.setattr(dmlf.pathlib.Path, 'rename', mock_rename_err)
        with pytest.raises(FileNotFoundError):
            dmlf.revert_rst('sitename', 'doc_name')
        monkeypatch.setattr(dmlf.pathlib.Path, 'rename', mock_rename)
        dmlf.revert_rst('sitename', 'doc_name')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        assert capsys.readouterr().out == 'call rename() to replace `{}` with `{}`\n'.format(
                path, str(path) + '.bak')
        dmlf.revert_rst('sitename', 'doc_name', 'directory')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        assert capsys.readouterr().out == 'call rename() to replace `{}` with `{}`\n'.format(
                path, str(path) + '.bak')

    def test_mark_src_deleted(self, monkeypatch, capsys):
        def mock_list_docs_none(*args):
            return []
        def mock_list_docs(*args):
            return ['doc_name']
        def mock_rename(self, *args):
            print('call rename(): from `{}` to `{}`'.format(self, args[0]))
        with pytest.raises(AttributeError):
            dmlf.mark_src_deleted('sitename', '')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            dmlf.mark_src_deleted('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs)
        monkeypatch.setattr(dmlf.pathlib.Path, 'rename', mock_rename)
        dmlf.mark_src_deleted('sitename', 'doc_name')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'doc_name.rst'
        path_n = dmlf.WEBROOT / 'sitename' / '.source' / ('doc_name' + dmlf.DELMARK)
        assert capsys.readouterr().out == 'call rename(): from `{}` to `{}`\n'.format(path, path_n)
        dmlf.mark_src_deleted('sitename', 'doc_name', 'directory')
        path = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / 'doc_name.rst'
        path_n = dmlf.WEBROOT / 'sitename' / '.source' / 'directory' / ('doc_name' + dmlf.DELMARK)
        assert capsys.readouterr().out == 'call rename(): from `{}` to `{}`\n'.format(path, path_n)

    def test_update_html(self, monkeypatch, capsys):
        def mock_list_docs_none(*args):
            return []
        def mock_list_docs(*args):
            return ['doc_name']
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir() for `{}`'.format(self))
        def mock_save_to(*args):
            print('call save_to(): save `{}` in `{}`'.format(args[1], args[0]))
        with pytest.raises(AttributeError):
            dmlf.update_html('sitename', '', '')
        with pytest.raises(AttributeError):
            dmlf.update_html('sitename', 'doc_name', '')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs_none)
        with pytest.raises(FileNotFoundError):
            dmlf.update_html('sitename', 'doc_name', 'contents')
        monkeypatch.setattr(dmlf, 'list_docs', mock_list_docs)
        monkeypatch.setattr(dmlf, 'save_to', mock_save_to)
        path = dmlf.WEBROOT / 'sitename' / '.target' / 'doc_name.html'
        dmlf.update_html('sitename', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        dmlf.update_html('sitename', 'doc_name', 'contents', '/', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'called mkdir() for `{}`\n'.format(path.parent),
            'call save_to(): save `contents` in `{}`\n'.format(path)))
        path = dmlf.WEBROOT / 'sitename' / '.target' / 'directory' / 'doc_name.html'
        dmlf.update_html('sitename', 'doc_name', 'contents', 'directory', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'called mkdir() for `{}`\n'.format(path.parent),
            'call save_to(): save `contents` in `{}`\n'.format(path)))

    def test_apply_deletions_target(self, monkeypatch, capsys):
        def mock_glob(self, *args, **kwargs):
            return [self / 'file1.deleted', self / 'file2.deleted']
        def mock_unlink(self, *args, **kwargs):
            print('deleted file `{}`'.format(self))
        def mock_rename(self, *args, **kwargs):
            print('renamed file `{}`'.format(self))
        def mock_touch(self, *args, **kwargs):
            print('created file `{}`'.format(self))
        monkeypatch.setattr(dmlf.pathlib.Path, 'glob', mock_glob)
        monkeypatch.setattr(dmlf.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(dmlf.pathlib.Path, 'rename', mock_rename)
        monkeypatch.setattr(dmlf.pathlib.Path, 'touch', mock_touch)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        dmlf.apply_deletions_target('sitename')
        old = dmlf.WEBROOT / 'sitename' / '.source'
        loc = dmlf.WEBROOT / 'sitename' / '.target'
        assert capsys.readouterr().out == ''.join(('deleted file `{}/file1.deleted`\n'.format(old),
                                                   'deleted file `{}/file2.deleted`\n'.format(old),
                                                   'renamed file `{}/file1.html`\n'.format(loc),
                                                   'renamed file `{}/file2.html`\n'.format(loc)))
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        dmlf.apply_deletions_target('sitename', 'directory')
        old = dmlf.WEBROOT / 'sitename' / '.source' / 'directory'
        loc = dmlf.WEBROOT / 'sitename' / '.target' / 'directory'
        assert capsys.readouterr().out == ''.join(('deleted file `{}/file1.deleted`\n'.format(old),
                                                   'deleted file `{}/file2.deleted`\n'.format(old),
                                                   'created file `{}/file1.deleted`\n'.format(loc),
                                                   'created file `{}/file2.deleted`\n'.format(loc)))

    def test_update_mirror(self, monkeypatch, capsys):
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir() for `{}`'.format(self))
        def mock_save_to(*args):
            print('called save_to(): save `{}` in `{}`'.format(args[1], args[0]))
        with pytest.raises(AttributeError):
            dmlf.update_mirror('sitename', '', 'data')
        monkeypatch.setattr(dmlf.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlf, 'save_to', mock_save_to)
        loc = dmlf.WEBROOT / 'sitename' / 'doc_name.html'
        dmlf.update_mirror('sitename', 'doc_name', 'data')
        assert capsys.readouterr().out == ''
        dmlf.update_mirror('sitename', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == 'called save_to(): save `data` in `{}`\n'.format(loc)
        dmlf.update_mirror('sitename', 'doc_name.rst', 'data', dry_run=False)
        assert capsys.readouterr().out == 'called save_to(): save `data` in `{}`\n'.format(loc)
        dmlf.update_mirror('sitename', 'doc_name.html', 'data', '/', dry_run=False)
        assert capsys.readouterr().out == 'called save_to(): save `data` in `{}`\n'.format(loc)
        loc = dmlf.WEBROOT / 'sitename' / 'directory' / 'doc_name.html'
        dmlf.update_mirror('sitename', 'doc_name.html', 'data', 'directory', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'called mkdir() for `{}`\n'.format(loc.parent),
            'called save_to(): save `data` in `{}`\n'.format(loc)))

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        def mock_glob(self, *args, **kwargs):
            return [self / 'file1.deleted', self / 'file2.deleted']
        def mock_unlink(self, *args, **kwargs):
            print('deleted file `{}`'.format(self))
        monkeypatch.setattr(dmlf.pathlib.Path, 'glob', mock_glob)
        monkeypatch.setattr(dmlf.pathlib.Path, 'unlink', mock_unlink)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        dmlf.apply_deletions_mirror('sitename')
        loc = dmlf.WEBROOT / 'sitename' / '.target'
        dest = dmlf.WEBROOT / 'sitename'
        assert capsys.readouterr().out == ''.join(('deleted file `{}/file1.deleted`\n'.format(loc),
                                                   'deleted file `{}/file2.deleted`\n'.format(loc),
                                                   'deleted file `{}/file1.html`\n'.format(dest),
                                                   'deleted file `{}/file2.html`\n'.format(dest)))
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        dmlf.apply_deletions_mirror('sitename', 'directory')
        loc = dmlf.WEBROOT / 'sitename' / '.target' / 'directory'
        assert capsys.readouterr().out == ''.join(('deleted file `{}/file1.deleted`\n'.format(loc),
                                                   'deleted file `{}/file2.deleted`\n'.format(loc)))

    def test_remove_doc(self):
        with pytest.raises(NotImplementedError):
            dmlf.remove_doc('sitename', 'docname')

    def test_get_doc_stats(self, monkeypatch, capsys):
        def mock_stat(self, *args, **kwargs):
            import types
            result = types.SimpleNamespace()
            result.st_mtime = 1
            return result
        monkeypatch.setattr(dmlf, 'read_settings', mock_settings_seflinks_yes)
        # monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlf.pathlib.Path, 'stat', mock_stat)
        assert dmlf.get_doc_stats('sitename', 'docname') == dmlf.Stats(dmlf.datetime.datetime.min,
                                                                       dmlf.datetime.datetime.min,
                                                                       dmlf.datetime.datetime.min)
        monkeypatch.setattr(dmlf.pathlib.Path, 'exists', return_true)
        assert dmlf.get_doc_stats('sitename', 'docname', 'dirname') == dmlf.Stats(
                dmlf.datetime.datetime.fromtimestamp(1),
                dmlf.datetime.datetime.fromtimestamp(1),
                dmlf.datetime.datetime.fromtimestamp(1))

    def test_get_all_doc_stats(self, monkeypatch):
        def mock_get_dir_stats(*args):
            return 'hello, world!'
        def mock_list_dirs(*args):
            return 'x', 'y'
        monkeypatch.setattr(dmlf, '_get_dir_stats', mock_get_dir_stats)
        monkeypatch.setattr(dmlf, 'list_dirs', mock_list_dirs)
        assert dmlf.get_all_doc_stats('sitename') == [('/', 'hello, world!'),
                                                      ('x', 'hello, world!'),
                                                      ('y', 'hello, world!')]
