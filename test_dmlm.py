import types
import datetime
import pathlib
import pytest
import docs2mongo as dmlm


# for monkeypatching
def mock_settings_seflinks_yes(*args):
    return {'seflinks': True}


def mock_settings_seflinks_no(*args):
    return {}


def return_true(*args):
    return True


def return_false(*args):
    return False


class MockColl:
    # find wordt 6x gebruikt, find_one 3x, find_one_and_delete 1x
    def find(self, *args, **kwargs):
        pass    # in testmethode monkeypatchen met gewenst resultaat

    def find_one(self, *args, **kwargs):
        pass    # in testmethode monkeypatchen met gewenst resultaat

    def find_one_and_delete(self, *args, **kwargs):
        pass    # in testmethode monkeypatchen met gewenst resultaat

    # update wordt 2x gebruikt, update_one 3x
    def update(self, *args, **kwargs):
        self.print_out('called update with', args, kwargs)

    def update_one(self, *args, **kwargs):
        self.print_out('called update_one with', args, kwargs)

    # insert / insert_one wordt 2x gebruikt (in een if/else)
    def insert(self, *args, **kwargs):
        self.print_out('called insert with', args, kwargs)
        return 'x'

    def insert_one(self, *args, **kwargs):
        self.print_out('called insert_one with', args, kwargs)
        return types.SimpleNamespace(inserted_id='x')

    # verder nog 1x drop_collection (methode van db), 1x remove en 1x delete_many
    def remove(self, *args, **kwargs):
        self.print_out('called remove with', args, kwargs)

    def delete_many(self, *args, **kwargs):
        self.print_out('called delete_many with', args, kwargs)

    def print_out(self, out, args, kwargs):
        if args:
            out += ' args ' + ', '.join(['`{}`'.format(x) for x in args])
            if kwargs:
                out += ' en'
        if kwargs:
            out += ' kwargs `{}`'.format(kwargs)
        print(out)


class TestNonApiFunctions:
    def test_get_site_id(self, monkeypatch):
        def mock_find_one(self, *args, **kwargs):
            return {'_id': 'site_id'}
        monkeypatch.setattr(MockColl, 'find_one', mock_find_one)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._get_site_id('site_name') == 'site_id'

    def test_get_site_doc(self, monkeypatch):
        def mock_find_one(self, *args, **kwargs):
            return {'docs': ['doc1', 'doc2']}
        monkeypatch.setattr(MockColl, 'find_one', mock_find_one)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._get_site_doc('site_name') == {'docs': ['doc1', 'doc2']}

    def test_update_site_doc(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm._update_site_doc('site_name', {'docs': ['doc1', 'doc2']})
        assert capsys.readouterr().out == 'called update_one with args `{}`, `{}`\n'.format(
            "{'name': 'site_name'}", "{'$set': {'docs': {'docs': ['doc1', 'doc2']}}}")

    def test_add_doc(self, monkeypatch, capsys):
        def mock_insert_one(*args):
            raise TypeError
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._add_doc('doc') == 'x'
        assert capsys.readouterr().out == 'called insert_one with args `doc`\n'
        monkeypatch.setattr(MockColl, 'insert_one', mock_insert_one)
        assert dmlm._add_doc('doc') == 'x'
        assert capsys.readouterr().out == 'called insert with args `doc`\n'

    def test_update_doc(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm._update_doc('docid', 'doc')
        assert capsys.readouterr().out == 'called update with args `{}`, `{}`\n'.format(
                "{'_id': 'docid'}", 'doc')

    def test_get_stats(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        docinfo = {}
        assert dmlm._get_stats(docinfo) == dmlm.Stats(datetime.datetime.min, datetime.datetime.min,
                                                      datetime.datetime.min)
        docinfo = {'src': {'updated': 1}, 'dest': {'updated': 2}, 'mirror': {'updated': 3}}
        assert dmlm._get_stats(docinfo) == dmlm.Stats(1, 2, 3)


class TestTestApi:
    def test_clear_db(self, monkeypatch, capsys):
        def mock_drop(*args):
            print('called drop_collection for `{}`'.format(args[0]))
        monkeypatch.setattr(dmlm, 'site_coll', 'MockColl()')
        monkeypatch.setattr(dmlm.db, 'drop_collection', mock_drop)
        dmlm.clear_db()
        assert capsys.readouterr().out == 'called drop_collection for `MockColl()`\n'

    def test_read_db(self, monkeypatch, capsys):
        def mock_find(self, *args, **kwargs):
            return 'result from site_coll.find()'
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.read_db() == 'result from site_coll.find()'

    def list_site_data(self, monkeypatch, capsys):
        # dit moet er in elk geval in:
        def mock_get_site_doc(*args):
            return {}
        def mock_find(self, *args, **kwargs):
            return [{}, {}, {}, {}]
        monkeypatch(dmlf, '_get_site_doc', mock_get_site_doc)
        sitename = 'testsite'
        siteloc = dmlm.WEBROOT / sitename
        # zo moet het resultaat er ongeveer uitzien:
        assert dmlm.list_site_data(sitename) == (
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

    def clear_site_data(self, monkeypatch, capsys):
        sitedoc = {}
        def mock_find_delete_ok(self, *args, **kwargs):
            print('called find_one_and_delete')
            return sitedoc
        def mock_find_delete_nok(self, *args, **kwargs):
            raise TypeError
        def mock_find(self, *args, **kwargs):
            print('called find_one')
            return sitedoc
        def mock_rmtree(*args):
            print('called rmtree')
        def mock_rmtree_fail(*args):
            print('called rmtree_fail')
            raise FileNotFoundError
        monkeypatch.setattr(MockColl, 'find_and_delete', mock_find_delete_ok)
        monkeypatch.setattr(dmlm.shutil, 'rmtree', mock_rmtree)
        assert dmlm.clear_site_data(site_name) == ''
        monkeypatch.setattr(MockColl, 'find_and_delete', mock_find_delete_nok)
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm.shutil, 'rmtree', mock_rmtree_fail)
        assert dmlm.clear_site_data(site_name) == ''


class TestSiteLevel:
    def test_list_sites(self, monkeypatch, capsys):
        def mock_find(self, *args, **kwargs):
            return [{'name': 'site_1'}, {}, {'name': 'site_2', 'data': 'gargl'}, {'id': 15}]
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.list_sites() == ['site_1', 'site_2']

    def test_create_new_site(self, monkeypatch, capsys):
        def mock_mkdir(self, *args, **kwargs):
            print('called mkdir()')
        def mock_insert_one(*args):
            raise TypeError
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: 'x')
        with pytest.raises(FileExistsError):
            dmlm.create_new_site('sitename')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        monkeypatch.setattr(pathlib.Path, 'exists', lambda x: True)  #  turn_true)
        with pytest.raises(FileExistsError):
            dmlm.create_new_site('sitename')
        monkeypatch.setattr(pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.create_new_site('site_name')
        assert capsys.readouterr().out == ''.join((
            "called insert_one with args `{'name': 'site_name', 'settings': {}, "
            "'docs': {'/': {}, 'templates': {}}}`\n",
            'called mkdir()\n'))
        monkeypatch.setattr(MockColl, 'insert_one', mock_insert_one)
        dmlm.create_new_site('site_name')
        assert capsys.readouterr().out == ''.join((
            "called insert with args `{'name': 'site_name', 'settings': {}, "
            "'docs': {'/': {}, 'templates': {}}}`\n",
            'called mkdir()\n'))

    def test_rename_site(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, '_get_site_id', lambda x: 'site_id')
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == ("called update_one with args `{'_id': 'site_id'}`, "
                                           "`{'$set': {'name': 'newname'}}`\n")

    def test_read_settings(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.read_settings('site_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'settings': {'name': 'value'}})
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.read_settings('site_name') == {'name': 'value'}

    def test_update_settings(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.update_settings('site_name', 'settings_dict')
        assert capsys.readouterr().out == ("called update with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'settings': 'settings_dict'}}`\n")

    def test_clear_settings(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.clear_settings('site_name')
        assert capsys.readouterr().out == ("called update with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'settings': {}}}`\n")

    def test_list_dirs(self, monkeypatch, capsys):
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.list_dirs('site_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': 'maakt niet uit deze wordt toch genegeerd',
             'dir1': {'doc1': {'src': 'deze directory heeft alleen een source versie'}},
             'dir2': {'doc2': {'dest': 'deze directory heeft alleen een html versie'}},
             'dir3': {'doc3': {'mirror': 'deze directory bestaat alleen in mirror'}}}})
        assert dmlm.list_dirs('site_name') == []
        assert dmlm.list_dirs('site_name', doctype='src') == ['dir1', 'dir2', 'dir3']
        assert dmlm.list_dirs('site_name', doctype='dest') == ['dir2']
        assert dmlm.list_dirs('site_name', doctype='mirror') == ['dir3']
        # assert capsys.readouterr().out == ''

    def test_create_new_dir(self, monkeypatch, capsys):
        def mock_update_site_doc(*args):
            print('called update_site_doc() with args `{}`, `{}`'.format(args[0], args[1]))
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'directory': {}}})
        with pytest.raises(FileExistsError):
            dmlm.create_new_dir('site_name', 'directory')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.create_new_dir('site_name', 'directory')
        assert capsys.readouterr().out == ('called update_site_doc() with args '
                                           "`site_name`, `{'directory': {}}`\n")

    def test_remove_dir(self, monkeypatch, capsys):
        def mock_update_site_doc(*args):
            print('called update_site_doc() with args `{}`, `{}`'.format(args[0], args[1]))
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'directory': {}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.remove_dir('site_name', 'directory')
        assert capsys.readouterr().out == ('called update_site_doc() with args '
                                           "`site_name`, `{}`\n")


class TestDocLevel:
    """voorbeeld van een site_doc "doc" gedeelte:
    monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
        {'/': {'doc': {'src': {'docid': 'x', 'updated': datetime.datetime.fromtimestamp(1)},
                       'dest': {'docid': 'y', 'updated': datetime.datetime.fromtimestamp(2)},
                       'mirror': {'docid': 'z', 'updated': datetime.datetime.fromtimestamp(3)}
                       }},
         'dir1': {'doc': {'src': {'docid': 'x',
                                  'updated': datetime.datetime.fromtimestamp(1)}}},
         'dir2': {'doc': {'dest': {'docid': 'y',
                                   'updated': datetime.datetime.fromtimestamp(2)}}},
         'dir3': {'doc': {'mirror': {'docid': 'z',
                                     'updated': datetime.datetime.fromtimestamp(3)}}}}})
    """
    def test_list_docs(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.list_docs('site_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {}})
        with pytest.raises(FileNotFoundError):
            dmlm.list_docs('site_name', directory='x')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {
             'doc1': {'src': {'docid': 'x', 'updated': datetime.datetime.fromtimestamp(1)}},
             'doc2': {'dest': {'docid': 'y', 'updated': datetime.datetime.fromtimestamp(2)}},
             'doc3': {'mirror': {'docid': 'z', 'updated': datetime.datetime.fromtimestamp(3)}}},
             'dirname': {'doc4': {'src': {'deleted': True}}}}})
        assert dmlm.list_docs('site_name') == []  # ik had 'doc1' verwacht
        assert dmlm.list_docs('site_name', 'src') == ['doc1']
        assert dmlm.list_docs('site_name', 'dest') == ['doc2']
        assert dmlm.list_docs('site_name', 'mirror') == ['doc3']
        assert dmlm.list_docs('site_name', 'src', 'dirname', deleted=True) == ['doc4']

    def test_list_templates(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {})
        assert dmlm.list_templates('site_name') == []
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {}})
        assert dmlm.list_templates('site_name') == []
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {'x': '', 'y': ''}})
        assert dmlm.list_templates('site_name') == ['x', 'y']

    def test_read_template(self, monkeypatch, capsys):
        # zie TODO in docs2mongo.py
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {})
        #assert dmlm.read_template('site_name', 'doc_name') == ''
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {}})
        assert dmlm.read_template('site_name', 'doc_name') == ''
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {'doc_name': 'data'}})
        assert dmlm.read_template('site_name', 'doc_name') == 'data'

    def test_write_template(self, monkeypatch, capsys):
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        # eerste template voor site; templates key bestaat nog niet
        #   zie eerste TODO in docs2mongo.py
        #  monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {})
        #  dmlm.write_template('site_name', 'doc_name', 'data')
        #  assert capsys.readouterr().out == 'call update_doc with args `` ``'
        # nieuw template
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {}})
        dmlm.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == ("called update_one with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'templates': {'doc_name': 'data'}}}`\n")
        # overschrijven bestaand template
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {'doc_name': 'data'}})
        dmlm.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == ("called update_one with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'templates': {'doc_name': 'data'}}}`\n")

    def test_create_new_doc(self, monkeypatch, capsys):
        with pytest.raises(AttributeError):
            dmlm.create_new_doc('site_name', '')
        def mock_add_doc(*args):
            print('called add_doc() with args `{}`'.format(args[0]))
            return 'new_id'
        def mock_update_site_doc(*args):
            docname = list(args[1]['/'])[0]
            doc = args[0] + '/' + docname
            docid = args[1]['/'][docname]['src']['docid']
            print('called update_site_doc() for document {} with id `{}`'.format(doc, docid))
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {}})
        with pytest.raises(FileNotFoundError):
            dmlm.create_new_doc('site_name', 'doc_name', 'dir_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'doc_name': {}}}})
        with pytest.raises(FileExistsError):
            dmlm.create_new_doc('site_name', 'doc_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        dmlm.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == ''.join((
            "called add_doc() with args `{'current': '', 'previous': ''}`\n",
            'called update_site_doc() for document site_name/doc_name with id `new_id`\n'))

    def test_get_doc_contents(self, monkeypatch, capsys):
        def mock_find(self, *args):
            print('called find() with arg `{}`'.format(args[0]))
            return [{'_id': 'doc_id', 'current': 'data', 'previous': 'old data'}]
        with pytest.raises(AttributeError):
            dmlm.get_doc_contents('sitename', '')
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {}}})
        with pytest.raises(FileNotFoundError):
            assert dmlm.get_doc_contents('site_name', 'doc_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'src': {}}}}})
        with pytest.raises(FileNotFoundError):
            assert dmlm.get_doc_contents('site_name', 'doc_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        # dit gaat mis, zie TODO in docs2mongo.py
        # assert dmlm.get_doc_contents('site_name', 'doc_name', 'src') == 'data'
        assert dmlm.get_doc_contents('site_name', 'doc_name', 'src') == 'data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'dirname': {'doc_name': {'dest': {'docid': 'doc_id'}}}}})
        assert dmlm.get_doc_contents('site_name', 'doc_name', 'dest', 'dirname') == 'data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"

    def test_update_rst(self, monkeypatch, capsys):
        def mock_find(self, *args):
            print('called find() with arg `{}`'.format(args[0]))
            return [{'_id': 'doc_id', 'current': 'data', 'previous': 'old data'}]
        def mock_update_doc(*args):
            print('called update_doc() with args `{}`, `{}`'.format(args[0], args[1]))
        def mock_update_site_doc(*args):
            docname = list(args[1]['/'])[0]
            doc = args[0] + '/' + docname
            docid = args[1]['/'][docname]['src']['docid']
        def mock_update_site_doc_2(*args):
            docname = list(args[1]['dirname'])[0]
            doc = args[0] + '/dirname/' + docname
            docid = args[1]['dirname'][docname]['src']['docid']
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(AttributeError):
            dmlm.update_rst('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlm.update_rst('site_name', 'doc_name', '')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'other_doc': {}}}})
        with pytest.raises(FileNotFoundError):
            dmlm.update_rst('site_name', 'doc_name', 'contents')
        # tussenliggende niveaus wordt niet op gecontroleerd
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'doc_name': {}}}})
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_update_doc', mock_update_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.update_rst('site_name', 'doc_name', 'contents') # , 'dirname')
        assert capsys.readouterr().out == ''.join((
            "called find() with arg `{'_id': 'doc_id'}`\n",
            "called update_doc() with args `doc_id`,"
            " `{'_id': 'doc_id', 'current': 'contents', 'previous': 'data'}`\n"))
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'dirname': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc_2)
        dmlm.update_rst('site_name', 'doc_name', 'contents', 'dirname')
        assert capsys.readouterr().out == ''.join((
            "called find() with arg `{'_id': 'doc_id'}`\n",
            "called update_doc() with args `doc_id`,"
            " `{'_id': 'doc_id', 'current': 'contents', 'previous': 'data'}`\n"))

    def test_mark_src_deleted(self, monkeypatch, capsys):
        def mock_update_site_doc(*args):
            print('call update_site_doc with args `{}`, `{}`'.format(args[0], args[1]))
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        with pytest.raises(AttributeError):
            dmlm.mark_src_deleted('site_name', '')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'dirname': {'other_doc': {'src': {}}}}})
        with pytest.raises(FileNotFoundError):
            dmlm.mark_src_deleted('site_name', 'doc_name', 'dirname')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'src': {}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.mark_src_deleted('site_name', 'doc_name', directory='')
        assert capsys.readouterr().out == ("call update_site_doc with args `site_name`, "
                                           "`{'/': {'doc_name': {'src': {'deleted': True}}}}`\n")

    def test_update_html(self, monkeypatch, capsys):
        #TODO add args for mocked methods
        def mock_add_doc(*args):  # als 'dest' nog niet aanwezig
            print('called add_doc()')
            return 'doc_id'
        def mock_find(self, *args):  # op sitecoll, als 'dest' al wel aanwezig
            print('called find()')
            return ({'_id': 'doc_id', 'current': 'old_data'},)
        def mock_update_doc(*args):
            print('called update_doc()')
        def mock_update_site_doc(*args):
            print('called update_site_doc()')
        with pytest.raises(AttributeError):
            dmlm.update_html('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlm.update_html('site_name', 'doc_name', '')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'dirname': {'other_doc': {'dest': {}}}}})
        with pytest.raises(FileNotFoundError):
            dmlm.update_html('site_name', 'doc_name', 'contents', directory='dirname')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {}}})
        with pytest.raises(FileNotFoundError):
            dmlm.update_html('site_name', 'doc_name', 'contents')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'doc_name': {}}}})
        monkeypatch.setattr(dmlm, '_update_doc', mock_update_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'called add_doc()\n',
            'called update_doc()\n',
            'called update_site_doc()\n'))
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'dest': {'docid': 'doc_id'}}}}})
        dmlm.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == ''.join((
            'called find()\n',
            'called update_doc()\n',
            'called update_site_doc()\n'))

    def test_apply_deletions_target(self, monkeypatch, capsys):
        #TODO: add args to mocked methods
        def mock_add_doc(*args):  # als 'dest' nog niet aanwezig
            print('called add_doc()')
            return 'doc_id'
        def mock_update_site_doc(*args):
            print('called update_site_doc()')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'src': {'deleted': True}, 'dest': {}},
                   'doc2': {'src': {'deleted': {}}}},
             'dirname': {'doc3': {'src': {}}}}})
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.apply_deletions_target('site_name')
        assert capsys.readouterr().out == ''.join(('called add_doc()\n',
                                                   'called update_site_doc()\n'))
        dmlm.apply_deletions_target('site_name', 'dirname')
        assert capsys.readouterr().out == 'called update_site_doc()\n'

    def test_update_mirror(self, monkeypatch, capsys):
        def mock_update_site_doc(*args):
            print('called update_site_doc()')
        def mock_save_to(*args):
            print('called save_to()')
        def mock_mkdir(*args, **kwargs):
            print('called mkdir()')
        def mock_touch(*args):
            print('called touch()')
        with pytest.raises(AttributeError):
            dmlm.update_mirror('site_name', '', 'contents')
        # geen test op of data gevuld?
        # with pytest.raises(AttributeError):
        #     dmlm.update_mirror('site_name', 'doc_name', '')
        # no checking if the document exists
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
        #         {'dirname': {'mirror': {'other_doc': {}}}}})
        dmlm.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'doc_name': {'mirror': {}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlm, 'read_settings', mock_settings_seflinks_no)
        monkeypatch.setattr(dmlm, 'save_to', mock_save_to)
        dmlm.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == 'called update_site_doc()\ncalled save_to()\n'
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'dirname': {'doc_name': {'mirror': {}}}}})
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', return_false)
        monkeypatch.setattr(dmlm.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlm.pathlib.Path, 'touch', mock_touch)
        dmlm.update_mirror('site_name', 'doc_name', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == ('called update_site_doc()\ncalled mkdir()\n'
                                           'called touch()\ncalled save_to()\n')

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        # TODO: add args to mocked methods
        def mock_update_site_doc(*args):
            print('called update_site_doc()')
        def mock_unlink(*args):
            print('called unlink()')
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'dest': {'deleted': True}, 'mirror': {}},
                   'doc2': {'dest': {'deleted': {}}}},
             'dirname': {'doc3': {'dest': {}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', return_true)
        monkeypatch.setattr(dmlm.pathlib.Path, 'unlink', mock_unlink)
        dmlm.apply_deletions_mirror('site_name'),
        assert capsys.readouterr().out == ('called update_site_doc()\n'
                                           'called unlink()\ncalled unlink()\n')
        dmlm.apply_deletions_mirror('site_name', 'dirname')
        assert capsys.readouterr().out == 'called update_site_doc()\n'

    def test_get_doc_stats(self, monkeypatch, capsys):
        def mock_get_stats(*args):
            return args[0]
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'docname': 'stats for docname'},
                 'dirname': {'docname2': 'stats for docname2'}}})
        monkeypatch.setattr(dmlm, '_get_stats', mock_get_stats)
        assert dmlm.get_doc_stats('site_name', 'docname') == 'stats for docname'
        assert dmlm.get_doc_stats('site_name', 'docname2', 'dirname') == 'stats for docname2'

    def test_get_all_doc_stats(self, monkeypatch, capsys):
        def mock_get_stats(*args):
            return args[0]
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'docname': 'stats for docname'},
                 'dirname': {'docname2': 'stats for docname2'}}})
        monkeypatch.setattr(dmlm, '_get_stats', mock_get_stats)
        assert dmlm.get_all_doc_stats('site_name') == [('/', [('docname', 'stats for docname')]),
            ('dirname', [('docname2', 'stats for docname2')])]
