"""unittests for ./app/docs2mongo.py
"""
import types
import datetime
import pathlib
import pytest
import app.docs2mongo as dmlm


# for monkeypatching
def mock_settings_seflinks_yes(*args):
    """stub to simulate a site with search engine friendly links
    """
    return {'seflinks': True}


def mock_settings_seflinks_no(*args):
    """stub to simulate a site without search engine friendly links
    """
    return {}


class MockDatetime:
    """stub for datetime.DateTime object
    """
    def utcnow(*args):
        """stub
        """
        return 'now'


class MockColl:
    """stub for pymongo.collection.Collection object
    """
    # find wordt 6x gebruikt, find_one 3x, find_one_and_delete 1x
    def find(self, *args, **kwargs):
        """stub - in testmethode monkeypatchen met gewenst resultaat
        """

    def find_one(self, *args, **kwargs):
        """stub - in testmethode monkeypatchen met gewenst resultaat
        """

    def find_one_and_delete(self, *args, **kwargs):
        """stub - in testmethode monkeypatchen met gewenst resultaat
        """

    # update wordt 2x gebruikt, update_one 3x
    def update(self, *args, **kwargs):
        """stub
        """
        self.print_out('called update with', args, kwargs)

    def update_one(self, *args, **kwargs):
        """stub
        """
        self.print_out('called update_one with', args, kwargs)

    # insert / insert_one wordt 2x gebruikt (in een if/else)
    def insert(self, *args, **kwargs):
        """stub
        """
        self.print_out('called insert with', args, kwargs)
        return 'x'

    def insert_one(self, *args, **kwargs):
        """stub
        """
        self.print_out('called insert_one with', args, kwargs)
        return types.SimpleNamespace(inserted_id='x')

    # verder nog 1x drop_collection (methode van db), 1x remove en 1x delete_many
    def remove(self, *args, **kwargs):
        """stub
        """
        self.print_out('called remove with', args, kwargs)

    def delete_many(self, *args, **kwargs):
        """stub
        """
        self.print_out('called delete_many with', args, kwargs)

    def print_out(self, out, args, kwargs):
        """stub
        """
        if args:
            out += ' args ' + ', '.join([f'`{x}`' for x in args])
            if kwargs:
                out += ' en'
        if kwargs:
            out += f' kwargs `{kwargs}`'
        print(out)


class TestNonApiFunctions:
    """unittests for functions outside of the dml API
    """
    def test_get_site_id(self, monkeypatch):
        """unittest for docs2mongo.get_site_id
        """
        def mock_find_one(self, *args, **kwargs):
            """stub
            """
            return {'_id': 'site_id'}
        monkeypatch.setattr(MockColl, 'find_one', mock_find_one)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._get_site_id('site_name') == 'site_id'

    def test_get_site_doc(self, monkeypatch):
        """unittest for docs2mongo.get_site_doc
        """
        def mock_find_one(self, *args, **kwargs):
            """stub
            """
            return {'docs': ['doc1', 'doc2']}
        monkeypatch.setattr(MockColl, 'find_one', mock_find_one)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._get_site_doc('site_name') == {'docs': ['doc1', 'doc2']}

    def test_update_site_doc(self, monkeypatch, capsys):
        """unittest for docs2mongo.update_site_doc
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm._update_site_doc('site_name', {'docs': ['doc1', 'doc2']})
        assert capsys.readouterr().out == 'called update_one with args `{}`, `{}`\n'.format(
            "{'name': 'site_name'}", "{'$set': {'docs': {'docs': ['doc1', 'doc2']}}}")

    def test_add_doc(self, monkeypatch, capsys):
        """unittest for docs2mongo.add_doc
        """
        # def mock_insert_one(*args): - noodzaak voor testen op TypeError vervallen zie docs2mongo.py
        #     raise TypeError
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm._add_doc('doc') == 'x'
        assert capsys.readouterr().out == 'called insert_one with args `doc`\n'
        # monkeypatch.setattr(MockColl, 'insert_one', mock_insert_one)
        # assert dmlm._add_doc('doc') == 'x'
        # assert capsys.readouterr().out == 'called insert with args `doc`\n'

    def test_update_doc(self, monkeypatch, capsys):
        """unittest for docs2mongo.update_doc
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm._update_doc('docid', 'doc')
        # assert capsys.readouterr().out == 'called update with args `{}`, `{}`\n'.format(
        assert capsys.readouterr().out == 'called update_one with args `{}`, `{}`\n'.format(
                "{'_id': 'docid'}", "{'$set': 'doc'}")

    def test_get_stats(self, monkeypatch):
        """unittest for docs2mongo.get_stats
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        docinfo = {}
        assert dmlm._get_stats(docinfo) == dmlm.Stats(datetime.datetime.min, datetime.datetime.min,
                                                      datetime.datetime.min)
        docinfo = {'src': {'updated': 1}, 'dest': {'updated': 2}, 'mirror': {'updated': 3}}
        assert dmlm._get_stats(docinfo) == dmlm.Stats(1, 2, 3)
        docinfo = {'src': {'deleted': 1}, 'dest': {'updated': 2}, 'mirror': {'updated': 3}}
        assert dmlm._get_stats(docinfo) == dmlm.Stats('[deleted]', 2, 3)
        docinfo = {'dest': {'deleted': 2}, 'mirror': {}}
        assert dmlm._get_stats(docinfo) == dmlm.Stats(datetime.datetime.min, '[deleted]', '')


class TestTestApi:
    """unittests for api functions related to testing
    """
    def test_clear_db(self, monkeypatch, capsys):
        """unittest for docs2mongo.clear_db
        """
        def mock_drop(*args):
            """stub
            """
            print(f'called drop_collection for `{args[0]}`')
        monkeypatch.setattr(dmlm, 'site_coll', 'MockColl()')
        monkeypatch.setattr(dmlm.db, 'drop_collection', mock_drop)
        dmlm.clear_db()
        assert capsys.readouterr().out == 'called drop_collection for `MockColl()`\n'

    def test_read_db(self, monkeypatch):
        """unittest for docs2mongo.read_db
        """
        def mock_find(self, *args, **kwargs):
            """stub
            """
            return 'result from site_coll.find()'
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.read_db() == 'result from site_coll.find()'

    def test_list_site_data(self, monkeypatch):
        """unittest for docs2mongo.list_site_data
        """
        def mock_find(self, *args, **kwargs):
            """stub
            """
            return [{'_id': 'x'}, {'_id': 'y'}, {'_id': 'z'}, {'_id': 'xx'}, {'_id': 'yy'},
                    {'_id': 'zz'}]
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.list_site_data('sitename')

        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        sitedoc = {'docs': {
            '/': {'doc1': {'src': {'docid': 'x', 'updated': datetime.datetime.fromtimestamp(1)},
                          'dest': {'docid': 'y', 'updated': datetime.datetime.fromtimestamp(2)},
                          'mirror': {'docid': 'z', 'updated': datetime.datetime.fromtimestamp(3)}}},
            'dir1': {'doc2': {'src': {'docid': 'xx',
                                     'updated': datetime.datetime.fromtimestamp(1)}}},
            'dir2': {'doc3': {'dest': {'docid': 'yy',
                                      'updated': datetime.datetime.fromtimestamp(2)}}},
            'dir3': {'doc4': {'mirror': {'docid': 'zz',
                                        'updated': datetime.datetime.fromtimestamp(3)}}}}}
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: sitedoc)
        doclist = [{'_id': ('dir1/doc2', 'src')}, {'_id': ('dir2/doc3', 'dest')},
                   {'_id': ('dir3/doc4', 'mirror')}, {'_id': ('doc1', 'dest')},
                   {'_id': ('doc1', 'mirror')}, {'_id': ('doc1', 'src')}]
        assert dmlm.list_site_data('sitename') == (sitedoc, doclist)

    def test_clear_site_data(self, monkeypatch, capsys):
        """unittest for docs2mongo.clear_site_data
        """
        def mock_find_delete_ok(self, *args, **kwargs):
            """stub
            """
            print('called find_one_and_delete')
            return {'docs': {1: {11: {111: {'docid': 111}, 112: {}}, 12: {121: {'docid': 121}}},
                             2: {21: {211: {'docid': 211}, 22: {221: {'docis': 222}}}}}}
        # niet meer nodig
        # def mock_find_delete_nok(self, *args, **kwargs):
        #     raise TypeError
        # def mock_find(self, *args, **kwargs):
        #     print('called find_one')
        #     return {'docs': {1: {11: {111: {'docid': 111}, 112: {}}, 12: {121: {'docid': 121}}},
        #                     2: {21: {211: {'docid': 211}, 22: {221: {'docis': 222}}}}}}
        def mock_rmtree(*args):
            """stub
            """
            print('called rmtree')
        def mock_rmtree_fail(*args):
            """stub
            """
            print('called rmtree_fail')
            raise FileNotFoundError
        monkeypatch.setattr(MockColl, 'find_one_and_delete', mock_find_delete_ok)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm.shutil, 'rmtree', mock_rmtree)
        dmlm.clear_site_data('site_name')
        assert capsys.readouterr().out == ('called find_one_and_delete\n'
                                           "called delete_many with args `{'_id':"
                                           " {'$in': [111, 121, 211]}}`\n"
                                           'called rmtree\n')
        # niet meer nodig
        # monkeypatch.setattr(MockColl, 'find_one_and_delete', mock_find_delete_nok)
        # monkeypatch.setattr(MockColl, 'find_one', mock_find)
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm.shutil, 'rmtree', mock_rmtree_fail)
        dmlm.clear_site_data('site_name')
        # assert capsys.readouterr().out == ('called find_one\n'
        #                                    "called remove with args `{'name': 'site_name'}`\n"
        #                                    "called delete_many with args `{'_id':"
        #                                    " {'$in': [111, 121, 211]}}`\n"
        #                                    'called rmtree_fail\n')
        assert capsys.readouterr().out == ('called find_one_and_delete\n'
                                           "called delete_many with args `{'_id':"
                                           " {'$in': [111, 121, 211]}}`\n"
                                           'called rmtree_fail\n')


class TestSiteLevel:
    """unittests for site level api functions
    """
    def test_list_sites(self, monkeypatch):
        """unittest for docs2mongo.list_sites
        """
        def mock_find(self, *args, **kwargs):
            """stub
            """
            return [{'name': 'site_1'}, {}, {'name': 'site_2', 'data': 'gargl'}, {'id': 15}]
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.list_sites() == ['site_1', 'site_2']

    def test_create_new_site(self, monkeypatch, capsys):
        """unittest for docs2mongo.create_new_site
        """
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print('called mkdir()')
        # niet meer nodig
        # def mock_insert_one(*args):
        #     raise TypeError
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: 'x')
        with pytest.raises(FileExistsError):
            dmlm.create_new_site('sitename')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        monkeypatch.setattr(pathlib.Path, 'exists', lambda x: True)  # turn_true)
        with pytest.raises(FileExistsError):
            dmlm.create_new_site('sitename')
        monkeypatch.setattr(pathlib.Path, 'exists', lambda x: False)
        monkeypatch.setattr(pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.create_new_site('site_name')
        assert capsys.readouterr().out == (
                "called insert_one with args `{'name': 'site_name', 'settings': {}, "
                "'docs': {'/': {}, 'templates': {}}}`\n"
                'called mkdir()\n')
        # monkeypatch.setattr(MockColl, 'insert_one', mock_insert_one)
        # dmlm.create_new_site('site_name')
        # assert capsys.readouterr().out == ''.join((
        #     "called insert with args `{'name': 'site_name', 'settings': {}, "
        #     "'docs': {'/': {}, 'templates': {}}}`\n",
        #     'called mkdir()\n'))

    def test_rename_site(self, monkeypatch, capsys):
        """unittest for docs2mongo.rename_site
        """
        monkeypatch.setattr(dmlm, '_get_site_id', lambda x: 'site_id')
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.rename_site('site_name', 'newname')
        assert capsys.readouterr().out == ("called update_one with args `{'_id': 'site_id'}`, "
                                           "`{'$set': {'name': 'newname'}}`\n")

    def test_read_settings(self, monkeypatch):
        """unittest for docs2mongo.read_settings
        """
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.read_settings('site_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'settings': {'name': 'value'}})
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        assert dmlm.read_settings('site_name') == {'name': 'value'}

    def test_update_settings(self, monkeypatch, capsys):
        """unittest for docs2mongo.update_settings
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.update_settings('site_name', 'settings_dict')
        assert capsys.readouterr().out == ("called update_one with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'settings': 'settings_dict'}}`\n")

    def test_clear_settings(self, monkeypatch, capsys):
        """unittest for docs2mongo.clear_settings
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.clear_settings('site_name')
        assert capsys.readouterr().out == ("called update_one with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'settings': {}}}`\n")

    def test_list_dirs(self, monkeypatch):
        """unittest for docs2mongo.list_dirs
        """
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        with pytest.raises(FileNotFoundError):
            dmlm.list_dirs('site_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': 'maakt niet uit deze wordt toch genegeerd',
             'dir1': {'doc1': {'src': 'deze directory heeft alleen een source versie'}},
             'dir2': {'doc2': {'dest': 'deze directory heeft alleen een html versie'}},
             'dir3': {'doc3': {'mirror': 'deze directory bestaat alleen in mirror'}}}})
        assert dmlm.list_dirs('site_name') == ['dir1', 'dir2', 'dir3']
        assert dmlm.list_dirs('site_name', doctype='src') == ['dir1', 'dir2', 'dir3']
        assert dmlm.list_dirs('site_name', doctype='dest') == ['dir2']
        assert dmlm.list_dirs('site_name', doctype='mirror') == ['dir3']
        # assert capsys.readouterr().out == ''

    def test_create_new_dir(self, monkeypatch, capsys):
        """unittest for docs2mongo.create_new_dir
        """
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
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
        """unittest for docs2mongo.remove_dir
        """
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
        # monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'directory': {}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        dmlm.remove_dir('site_name', 'directory')
        assert capsys.readouterr().out == ("called update_site_doc() with args `site_name`, `{}`\n")


class TestDocLevel:
    """unittests for document level api functions
    """
    def test_list_docs(self, monkeypatch):
        """unittest for docs2mongo.list_docs
        """
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
        assert dmlm.list_docs('site_name') == ['doc1']
        assert dmlm.list_docs('site_name', 'src') == ['doc1']
        assert dmlm.list_docs('site_name', 'dest') == ['doc2']
        assert dmlm.list_docs('site_name', 'mirror') == ['doc3']
        assert dmlm.list_docs('site_name', 'src', 'dirname', deleted=True) == ['doc4']

    def test_list_templates(self, monkeypatch):
        """unittest for docs2mongo.list_templates
        """
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {})
        assert dmlm.list_templates('site_name') == []
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {}})
        assert dmlm.list_templates('site_name') == []
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {'x': '', 'y': ''}})
        assert dmlm.list_templates('site_name') == ['x', 'y']

    def test_read_template(self, monkeypatch):
        """unittest for docs2mongo.read_template
        """
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {}})
        assert dmlm.read_template('site_name', 'doc_name') == ''
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'templates': {'doc_name': 'data'}})
        assert dmlm.read_template('site_name', 'doc_name') == 'data'

    def test_write_template(self, monkeypatch, capsys):
        """unittest for docs2mongo.write_template
        """
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        # eerste template voor site; templates key bestaat nog niet
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {})
        dmlm.write_template('site_name', 'doc_name', 'data')
        assert capsys.readouterr().out == ("called update_one with args `{'name': 'site_name'}`,"
                                           " `{'$set': {'templates': {'doc_name': 'data'}}}`\n")
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
        """unittest for docs2mongo.create_new_doc
        """
        with pytest.raises(AttributeError):
            dmlm.create_new_doc('site_name', '')
        def mock_add_doc(*args):
            """stub
            """
            print(f'called add_doc() with args `{args[0]}`')
            return 'new_id'
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {}})
        with pytest.raises(FileNotFoundError):
            dmlm.create_new_doc('site_name', 'doc_name', 'dir_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'doc_name': {}}}})
        with pytest.raises(FileExistsError):
            dmlm.create_new_doc('site_name', 'doc_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        dmlm.create_new_doc('site_name', 'doc_name')
        assert capsys.readouterr().out == (
                "called add_doc() with args `{'current': '', 'previous': ''}`\n"
                "called update_site_doc() with args `site_name`,"
                " `{'/': {'doc_name': {'src': {'docid': 'new_id', 'updated': 'now'}}}}`\n")

    def test_get_doc_contents(self, monkeypatch, capsys):
        """unittest for docs2mongo.get_doc_contents
        """
        def mock_find(self, *args):
            """stub
            """
            print(f'called find() with arg `{args[0]}`')
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
        assert dmlm.get_doc_contents('site_name', 'doc_name') == 'data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"
        assert dmlm.get_doc_contents('site_name', 'doc_name', 'src') == 'data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'dirname': {'doc_name': {'dest': {'docid': 'doc_id'}}}}})
        assert dmlm.get_doc_contents('site_name', 'doc_name', 'dest', 'dirname') == 'data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"
        assert dmlm.get_doc_contents('site_name', 'doc_name', 'dest', 'dirname',
                                     previous=True) == 'old data'
        assert capsys.readouterr().out == "called find() with arg `{'_id': 'doc_id'}`\n"

    def test_update_rst(self, monkeypatch, capsys):
        """unittest for docs2mongo.update_rst
        """
        def mock_find(self, *args):
            """stub
            """
            print(f'called find() with arg `{args[0]}`')
            return [{'_id': 'doc_id', 'current': 'data', 'previous': 'old data'}]
        def mock_update_doc(*args):
            """stub
            """
            print(f'called update_doc() with args `{args[0]}`, `{args[1]}`')
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
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
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        dmlm.update_rst('site_name', 'doc_name', 'contents')  # , 'dirname')
        assert capsys.readouterr().out == (
                "called find() with arg `{'_id': 'doc_id'}`\n"
                "called update_doc() with args `doc_id`,"
                " `{'_id': 'doc_id', 'current': 'contents', 'previous': 'data'}`\n"
                "called update_site_doc() with args `site_name`,"
                " `{'/': {'doc_name': {'src': {'docid': 'doc_id', 'updated': 'now'}}}}`\n")
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'dirname': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        with pytest.raises(FileNotFoundError):
            dmlm.update_rst('site_name', 'doc_name', 'contents', 'otherdir')

    def test_revert_rst(self, monkeypatch, capsys):
        """unittest for docs2mongo.revert_rst
        """
        def mock_find(self, *args):
            """stub
            """
            print(f'called find() with arg `{args[0]}`')
            return [{'_id': 'doc_id', 'current': 'data', 'previous': 'old data'}]
        def mock_update_doc(*args):
            """stub
            """
            print(f'called update_doc() with args `{args[0]}`, `{args[1]}`')
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {'/': {'other_doc': {}}}})
        with pytest.raises(AttributeError):
            dmlm.revert_rst('site_name', '')
        with pytest.raises(FileNotFoundError):
            dmlm.revert_rst('site_name', 'doc_name')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        monkeypatch.setattr(dmlm, '_update_doc', mock_update_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        dmlm.revert_rst('site_name', 'doc_name')  # , 'dirname')
        assert capsys.readouterr().out == (
                "called find() with arg `{'_id': 'doc_id'}`\n"
                "called update_doc() with args `doc_id`,"
                " `{'_id': 'doc_id', 'current': 'old data', 'previous': ''}`\n"
                "called update_site_doc() with args `site_name`,"
                " `{'/': {'doc_name': {'src': {'docid': 'doc_id', 'updated': 'now'}}}}`\n")
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'subdir': {'doc_name': {'src': {'docid': 'doc_id'}}}}})
        with pytest.raises(FileNotFoundError):
            dmlm.revert_rst('site_name', 'doc_name', 'otherdir')

    def test_mark_src_deleted(self, monkeypatch, capsys):
        """unittest for docs2mongo.mark_src_deleted
        """
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'call update_site_doc with args `{args[0]}`, `{args[1]}`')
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
        """unittest for docs2mongo.update_html
        """
        def mock_add_doc(*args):  # als 'dest' nog niet aanwezig
            """stub
            """
            print(f'called add_doc() with args `{args[0]}`')
            return 'doc_id'
        def mock_find(self, *args):  # op sitecoll, als 'dest' al wel aanwezig
            """stub
            """
            print(f'called find() with arg `{args[0]}`')
            return ({'_id': 'doc_id', 'current': 'old_data'},)
        def mock_update_doc(*args):
            """stub
            """
            print(f'called update_doc() with args `{args[0]}`, `{args[1]}`')
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
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
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {
            'docs': {'/': {'doc_name': {'src': {'docid': 'x'}}}}})
        monkeypatch.setattr(dmlm, '_update_doc', mock_update_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        dmlm.update_html('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        monkeypatch.setattr(MockColl, 'find', mock_find)
        monkeypatch.setattr(dmlm, 'site_coll', MockColl())
        dmlm.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
            "called add_doc() with args `{'current': '', 'previous': ''}`\n"
            "called update_doc() with args `doc_id`, `{'current': 'contents', 'previous': ''}`\n"
            "called update_site_doc() with args `site_name`, `{'/': {'doc_name':"
            " {'src': {'docid': 'x'}, 'dest': {'docid': 'doc_id', 'updated': 'now'}}}}`\n")
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc_name': {'src': {'docid': 'x'}, 'dest': {'docid': 'doc_id'}}}}})
        dmlm.update_html('site_name', 'doc_name', 'contents', dry_run=False)
        assert capsys.readouterr().out == (
            "called find() with arg `{'_id': 'doc_id'}`\n"
            "called update_doc() with args `doc_id`, `{'_id': 'doc_id', 'current': 'contents',"
            " 'previous': 'old_data'}`\n"
            "called update_site_doc() with args `site_name`, `{'/': {'doc_name':"
            " {'src': {'docid': 'x'}, 'dest': {'docid': 'doc_id', 'updated': 'now'}}}}`\n")

    def test_list_deletions_target(self, monkeypatch):
        """unittest for docs2mongo.list_deletions_target
        """
        monkeypatch.setattr(dmlm, 'list_dirs', lambda x, y: ['dirname'])
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'src': {'docid': 'x', 'deleted': True}, 'dest': {}},
                   'doc2': {'src': {'deleted': {}}}},
             'dirname': {'doc3': {'src': {'deleted': True}},
                         'doc4': {'src': {'deleted': False}}}}})
        assert dmlm.list_deletions_target('site_name') == ['doc1']
        assert dmlm.list_deletions_target('site_name', '*') == ['doc1', 'dirname/doc3']
        assert dmlm.list_deletions_target('site_name', 'dirname') == ['dirname/doc3']
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'src': {'docid': 'x'}, 'dest': {}},
                   'doc2': {'src': {}}},
             'dirname': {'doc3': {'src': {}}}}})
        assert dmlm.list_deletions_target('site_name') == []
        assert dmlm.list_deletions_target('site_name', '*') == []
        assert dmlm.list_deletions_target('site_name', 'dirname') == []

    def test_apply_deletions_target(self, monkeypatch, capsys):
        """unittest for docs2mongo.apply_deletions_target
        """
        def mock_add_doc(*args):  # als 'dest' nog niet aanwezig
            """stub
            """
            print(f'called add_doc() with args `{args[0]}`')
            return 'doc_id'
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'src': {'docid': 'x', 'deleted': True}, 'dest': {}},
                   'doc2': {'src': {'deleted': {}}}},
             'dirname': {'doc3': {'src': {'deleted': True}},
                         'doc4': {'src': {'deleted': False}}}}})
        monkeypatch.setattr(dmlm, '_add_doc', mock_add_doc)
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        assert dmlm.apply_deletions_target('site_name') == ['doc1']
        assert capsys.readouterr().out == (
                "called update_site_doc() with args `site_name`, `{'/':"
                " {'doc1': {'dest': {'deleted': True}},"
                " 'doc2': {'src': {'deleted': {}}}},"
                " 'dirname': {'doc3': {'src': {'deleted': True}},"
                " 'doc4': {'src': {'deleted': False}}}}`\n")
        assert dmlm.apply_deletions_target('site_name', 'dirname') == ['dirname/doc3']
        assert capsys.readouterr().out == (
                "called add_doc() with args `{'current': '', 'previous': ''}`\n"
                "called update_site_doc() with args `site_name`, `{'/':"
                " {'doc1': {'src': {'docid': 'x', 'deleted': True}, 'dest': {}},"
                " 'doc2': {'src': {'deleted': {}}}},"
                " 'dirname': {'doc3': {'dest': {'docid': 'doc_id', 'deleted': True}},"
                " 'doc4': {'src': {'deleted': False}}}}`\n")
        assert dmlm.apply_deletions_target('site_name', '*') == ['doc1', 'dirname/doc3']
        assert capsys.readouterr().out == (
                "called add_doc() with args `{'current': '', 'previous': ''}`\n"
                "called update_site_doc() with args `site_name`, `{'/':"
                " {'doc1': {'dest': {'deleted': True}},"
                " 'doc2': {'src': {'deleted': {}}}},"
                " 'dirname': {'doc3': {'dest': {'docid': 'doc_id', 'deleted': True}},"
                " 'doc4': {'src': {'deleted': False}}}}`\n")
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'src': {}, 'dest': {}},
                   'doc2': {'src': {}}},
             'dirname': {'doc3': {'src': {}}}}})
        assert dmlm.apply_deletions_mirror('site_name', '*') == []
        assert capsys.readouterr().out == ''

    def test_update_mirror(self, monkeypatch, capsys):
        """unittest for docs2mongo.update_mirror
        """
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'called update_site_doc() with args `{args[0]}`, `{args[1]}`')
        def mock_save_to(*args):
            """stub
            """
            print(f'called save_to() for `{args[0]}`')
        def mock_mkdir(self, *args, **kwargs):
            """stub
            """
            print(f'called mkdir() for `{self}`')
        def mock_touch(self, *args):
            """stub
            """
            print(f'called touch() for `{self}`')
        with pytest.raises(AttributeError):
            dmlm.update_mirror('site_name', '', 'contents')
        with pytest.raises(AttributeError):
            dmlm.update_mirror('site_name', 'doc_name', '')
        # no checking if the document exists ?
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
        #         {'dirname': {'mirror': {'other_doc': {}}}}})
        dmlm.update_mirror('site_name', 'doc_name', 'contents')
        assert capsys.readouterr().out == ''
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'doc_name': {'mirror': {}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', lambda *x: True)
        monkeypatch.setattr(dmlm, 'read_settings', mock_settings_seflinks_no)
        monkeypatch.setattr(dmlm, 'save_to', mock_save_to)
        dmlm.update_mirror('site_name', 'doc_name', 'data', dry_run=False)
        assert capsys.readouterr().out == (
                "called update_site_doc() with args `site_name`,"
                " `{'/': {'doc_name': {'mirror': {'updated': 'now'}}}}`\n"
                f'called save_to() for `{dmlm.WEBROOT}/site_name/doc_name.html`\n')
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'dirname': {'doc_name': {'mirror': {}}}}})
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', lambda *x: False)
        monkeypatch.setattr(dmlm.pathlib.Path, 'mkdir', mock_mkdir)
        monkeypatch.setattr(dmlm.pathlib.Path, 'touch', mock_touch)
        dmlm.update_mirror('site_name', 'doc_name', 'data', 'dirname', dry_run=False)
        assert capsys.readouterr().out == (
                "called update_site_doc() with args `site_name`,"
                " `{'dirname': {'doc_name': {'mirror': {'updated': 'now'}}}}`\n"
                f'called mkdir() for `{dmlm.WEBROOT}/site_name/dirname`\n'
                f'called touch() for `{dmlm.WEBROOT}/site_name/dirname/doc_name.html`\n'
                f'called save_to() for `{dmlm.WEBROOT}/site_name/dirname/doc_name.html`\n')

    def test_list_deletions_mirror(self, monkeypatch):
        """unittest for docs2mongo.list_deletions_mirror
        """
        monkeypatch.setattr(dmlm, 'list_dirs', lambda x, y: ['dirname'])
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'dest': {'deleted': True}, 'mirror': {}},
                   'doc2': {'dest': {'deleted': {}}},
                   'docx': {'src': {'': {}}}},                # nog niet in dest omgeving
             'dirname': {'doc3': {'dest': {'deleted': True}},
                         'doc4': {'dest': {'deleted': False}}}}})
        assert dmlm.list_deletions_mirror('site_name') == ['doc1']
        assert dmlm.list_deletions_mirror('site_name', '*') == ['doc1', 'dirname/doc3']
        assert dmlm.list_deletions_mirror('site_name', 'dirname') == ['dirname/doc3']
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'dest': {}, 'mirror': {}},
                   'doc2': {'dest': {}}},
             'dirname': {'doc3': {'dest': {}}}}})
        assert dmlm.list_deletions_mirror('site_name') == []
        assert dmlm.list_deletions_mirror('site_name', '*') == []
        assert dmlm.list_deletions_mirror('site_name', 'dirname') == []

    def test_apply_deletions_mirror(self, monkeypatch, capsys):
        """unittest for docs2mongo.apply_deletions_mirror
        """
        def mock_update_site_doc(*args):
            """stub
            """
            print(f'call update_site_doc() with args `{args[0]}`, `{args[1]}`')
        def mock_unlink(self, *args):
            """stub
            """
            print(f'called unlink() for `{self}`')
        # monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: None)
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs': {
            '/': {'doc1': {'dest': {'deleted': True}, 'mirror': {}},
                  'doc2': {'dest': {'deleted': {}}},
                  'docx': {'src': {'': {}}}},                # nog niet in dest omgeving
            'dirname': {'doc3': {'dest': {'deleted': True}},
                        'doc4': {'dest': {'deleted': False}}}}})
        monkeypatch.setattr(dmlm, '_update_site_doc', mock_update_site_doc)
        monkeypatch.setattr(dmlm.datetime, 'datetime', MockDatetime)
        monkeypatch.setattr(dmlm.pathlib.Path, 'exists', lambda *x: True)
        monkeypatch.setattr(dmlm.pathlib.Path, 'unlink', mock_unlink)
        assert dmlm.apply_deletions_mirror('site_name') == ['doc1']
        loc = dmlm.WEBROOT / 'site_name'
        assert capsys.readouterr().out == ''.join((
            "call update_site_doc() with args `site_name`,"
            " `{'/': {'doc2': {'dest': {'deleted': {}}}, 'docx': {'src': {'': {}}}},"
            " 'dirname': {'doc3': {'dest': {'deleted': True}},"
            " 'doc4': {'dest': {'deleted': False}}}}`\n",
            f'called unlink() for `{loc}/doc1.html`\n'))
        assert dmlm.apply_deletions_mirror('site_name', 'dirname') == ['dirname/doc3']
        assert capsys.readouterr().out == ''.join((
            "call update_site_doc() with args `site_name`,"
            " `{'/': {'doc1': {'dest': {'deleted': True}, 'mirror': {}},"
            " 'doc2': {'dest': {'deleted': {}}}, 'docx': {'src': {'': {}}}},"
            " 'dirname': {'doc4': {'dest': {'deleted': False}}}}`\n",
            f'called unlink() for `{loc}/dirname/doc3.html`\n'))
        assert dmlm.apply_deletions_mirror('site_name', '*') == ['doc1', 'dirname/doc3']
        assert capsys.readouterr().out == ''.join((
            "call update_site_doc() with args `site_name`, `{'/':"
            " {'doc2': {'dest': {'deleted': {}}}, 'docx': {'src': {'': {}}}},"
            " 'dirname': {'doc4': {'dest': {'deleted': False}}}}`\n",
            f'called unlink() for `{loc}/doc1.html`\n',
            f'called unlink() for `{loc}/dirname/doc3.html`\n'))
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
            {'/': {'doc1': {'dest': {}, 'mirror': {}},
                   'doc2': {'dest': {}}},
             'dirname': {'doc3': {'dest': {'deleted': {}}}}}})
        assert dmlm.apply_deletions_mirror('site_name') == []
        assert capsys.readouterr().out == ''

    def test_get_doc_stats(self, monkeypatch):
        """unittest for docs2mongo.get_doc_stats
        """
        def mock_get_stats(*args):
            """stub
            """
            return args[0]
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'docname': 'stats for docname'},
                 'dirname': {'docname2': 'stats for docname2'}}})
        monkeypatch.setattr(dmlm, '_get_stats', mock_get_stats)
        assert dmlm.get_doc_stats('site_name', 'docname') == 'stats for docname'
        assert dmlm.get_doc_stats('site_name', 'docname2', 'dirname') == 'stats for docname2'

    def test_get_all_doc_stats(self, monkeypatch):
        """unittest for docs2mongo.get_all_doc_stats
        """
        def mock_get_stats(*args):
            """stub
            """
            return args[0]
        monkeypatch.setattr(dmlm, '_get_site_doc', lambda x: {'docs':
                {'/': {'docname': 'stats for docname'},
                 'dirname': {'docname2': 'stats for docname2'}}})
        monkeypatch.setattr(dmlm, '_get_stats', mock_get_stats)
        assert dmlm.get_all_doc_stats('site_name') == [('/', [('docname', 'stats for docname')]),
            ('dirname', [('docname2', 'stats for docname2')])]
