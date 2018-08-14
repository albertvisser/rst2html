"""Rst@HTML unit tests for dml modules: same tests apply for all variants

can be configured which module to use via app_settings
"""
import os
import sys
import pprint
import datetime
## import pathlib
## import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app_settings import DML, WEBROOT
if DML == 'fs':
    print('using file system dml')
    import docs2fs as dml
elif DML == 'mongo':
    print('using mongodb dml')
    import docs2mongo as dml
elif DML == 'postgres':
    print('using postgresql dml')
    import docs2pg as dml


def assert_equal(left, right):
    """compare two terms and display them when unequal
    """
    try:
        assert left == right
    except AssertionError:
        print(left)
        print('  is not the same as')
        print(right)
        raise


def list_site_contents(sitename, filename=''):
    """show site contents in a standard structure, independent of the data backend
    """
    errs = ''
    try:
        sitedoc, docdata = dml.list_site_data(sitename)
    except FileNotFoundError as e:
        errs = str(e)
        sitedoc, docdata = {}, []
    if not filename:
        print('\n--------- Listing contents of site {} ----------'.format(sitename))
        if errs:
            print(errs)
        else:
            pprint.pprint(sitedoc)
            print("----")
            for doc in docdata:
                pprint.pprint(doc)
            print("----")
    else:
        with open(filename, 'w') as _out:
            if errs:
                _out.write(errs)
            else:
                pprint.pprint(sitedoc, stream=_out)
                for doc in docdata:
                    pprint.pprint(doc, stream=_out)
    return sitedoc, docdata

    ## outdata = 'Listing contents of site "{}"'.format(sitedoc["doc"])
    ## outline = 'Settings: {}: {}'
    ## for setting, value in ordered([(x, y) for x, y in sitedoc["settings"].items()]):
        ## outdata.append(outline.format(


def clear_site_contents(sitename):
    "remove site"
    dml.clear_site_data(sitename)


def test_dml(site_name):
    """execute all the tests"""
    print('test creation of site and settings...', end=' ')
    ok = True
    try:
        dml.create_new_site(site_name)
    except FileExistsError:
        ok = False
    assert ok
    try:
        test = dml.create_new_site(site_name)
    except FileExistsError:
        ok = False
    assert not ok
    test = dml.list_sites()
    assert site_name in test
    data = dml.read_settings(site_name)
    assert_equal(data, {})
    olddata = {'unknown_setting': 'secret value', 'url': 'fish-slapping-dance'}
    dml.update_settings(site_name, olddata)
    data = dml.read_settings(site_name)
    assert_equal(data, olddata)
    olddata = {'url': 'fish-slapping-dance'}
    dml.update_settings(site_name, olddata)
    data = dml.read_settings(site_name)
    assert_equal(data, olddata)
    olddata = {'url': '/rst2html-data/test'}
    dml.update_settings(site_name, olddata)
    data = dml.read_settings(site_name)
    assert_equal(data, olddata)
    print('ok')

    rootdoc = 'jansen'
    print('getting contents of nonexistent document...', end=' ')
    try:
        data = dml.get_doc_contents(site_name, rootdoc, 'src')
        found = True
    except FileNotFoundError:
        found = False
    assert found is False
    print('ok')

    mld = dml.create_new_doc(site_name, rootdoc)
    print('getting contents of empty document...', end=' ')
    data = dml.get_doc_contents(site_name, rootdoc, 'src')
    assert_equal(data, "")
    print('ok')

    print('creating first doc in root...', end=' ')
    assert_equal(dml.list_dirs(site_name, 'src'), [])
    assert_equal(dml.list_dirs(site_name, 'dest'), [])
    assert_equal(dml.list_docs(site_name, 'src'), ['jansen'])
    assert_equal(dml.list_docs(site_name, 'dest'), [])
    print('ok')

    print('updating first doc in root...', end=' ')
    dml.update_rst(site_name, rootdoc, 'ladida')
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest == datetime.datetime.min and
            stats.mirror == datetime.datetime.min)
    assert_equal(dml.list_docs(site_name, 'src'), ['jansen'])
    assert_equal(dml.list_docs(site_name, 'dest'), [])
    print('ok')

    print('updating first doc`s html in root...', end=' ')
    dml.update_html(site_name, rootdoc, '<p>ladida</p>')
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.mirror == datetime.datetime.min)
    assert_equal(dml.list_docs(site_name, 'src'), ['jansen'])
    assert_equal(dml.list_docs(site_name, 'dest'), ['jansen'])
    print('ok')

    print('getting contents of documents in root...', end=' ')
    dml.update_rst(site_name, rootdoc, 'bah humbug')
    data = dml.get_doc_contents(site_name, rootdoc, 'src')
    assert_equal(data, 'bah humbug')
    dml.update_html(site_name, rootdoc, '<p>bah humbug</p>')
    data = dml.get_doc_contents(site_name, rootdoc, 'dest')
    assert_equal(data, '<p>bah humbug</p>')
    print('ok')

    print('testing move to mirror...', end=' ')
    is_ok = False
    try:
        dml.update_mirror(site_name, '', data)
    except AttributeError:
        is_ok = True
    assert is_ok
    dml.update_mirror(site_name, rootdoc, data)
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.mirror != datetime.datetime.min)
    ## dml.update_mirror(site_name, rootdoc, data)
    print('ok')

    rootdeldoc = 'jansens'
    fsroot = '/home/albert/www'
    print('testing mark for deletion ...', end='')
    dml.create_new_doc(site_name, rootdeldoc)
    dml.update_rst(site_name, rootdeldoc, 'ladida')
    assert 'jansens' in dml.list_docs(site_name, 'src')
    assert 'jansens' not in dml.list_docs(site_name, 'src', deleted=True)
    dml.update_html(site_name, rootdeldoc, '<p>ladida</p>')  # migrate first
    dml.mark_src_deleted(site_name, rootdeldoc)
    assert 'jansens' not in dml.list_docs(site_name, 'src')
    assert 'jansens' in dml.list_docs(site_name, 'src', deleted=True)
    print('ok')

    print('checking migration of deletion mark...', end='')
    assert 'jansens' in dml.list_docs(site_name, 'dest')
    dml.update_mirror(site_name, rootdeldoc, '<p>ladida</p>')  # migrate first
    dml.apply_deletions_target(site_name, directory='')
    assert 'jansens' not in dml.list_docs(site_name, 'dest')
    assert 'jansens' not in dml.list_docs(site_name, 'src', deleted=True)
    assert 'jansens' in dml.list_docs(site_name, 'dest', deleted=True)
    print('ok')

    print('checking final result of delete action...', end='')
    assert 'jansens' in dml.list_docs(site_name, 'mirror')
    dml.apply_deletions_mirror(site_name, directory='')
    assert 'jansens' not in dml.list_docs(site_name, 'dest', deleted=True)
    assert 'jansens' not in dml.list_docs(site_name, 'mirror')
    print('ok')

    newdir = 'guichelheil'
    print('creating new dir {}...'.format(newdir), end=' ')
    otherdoc = 'hendriksen'
    dml.create_new_dir(site_name, newdir)
    assert_equal(dml.list_dirs(site_name, 'src'), ['guichelheil'])
    assert_equal(dml.list_dirs(site_name, 'dest'), [])
    assert_equal(dml.list_docs(site_name, 'src', directory=newdir), [])
    assert_equal(dml.list_docs(site_name, 'dest', directory=newdir), [])
    failed = False
    try:
        dml.create_new_dir(site_name, newdir)
    except FileExistsError:
        failed = True
    assert failed
    print('ok')

    dml.create_new_doc(site_name, otherdoc, directory=newdir)
    print('updating rst in {}...'.format(newdir), end=' ')
    dml.update_rst(site_name, otherdoc, 'zoinks', directory=newdir)
    assert_equal(dml.list_dirs(site_name, 'src'), ['guichelheil'])
    assert_equal(dml.list_dirs(site_name, 'dest'), [])
    assert_equal(dml.list_docs(site_name, 'src', directory=newdir), ['hendriksen'])
    assert_equal(dml.list_docs(site_name, 'dest', directory=newdir), [])
    print('ok')

    print('updating html in {}...'.format(newdir), end=' ')
    dml.update_html(site_name, otherdoc, '<p>zoinks</p>', directory=newdir)
    assert_equal(dml.list_dirs(site_name, 'src'), ['guichelheil'])
    assert_equal(dml.list_dirs(site_name, 'dest'), ['guichelheil'])
    assert_equal(dml.list_docs(site_name, 'src', directory=newdir), ['hendriksen'])
    assert_equal(dml.list_docs(site_name, 'dest', directory=newdir), ['hendriksen'])
    print('ok')

    print('getting contents of documents in {}...'.format(newdir), end=' ')
    dml.update_rst(site_name, otherdoc, 'but not them', directory=newdir)
    data = dml.get_doc_contents(site_name, otherdoc, 'src', directory=newdir)
    assert_equal(data, 'but not them')
    dml.update_html(site_name, otherdoc, '<p>but not them</p>', directory=newdir)
    data = dml.get_doc_contents(site_name, otherdoc, 'dest', directory=newdir)
    assert_equal(data, '<p>but not them</p>')
    print('ok')

    print('testing move to mirror from {}...'.format(newdir), end=' ')
    dml.update_mirror(site_name, otherdoc, data, directory=newdir)
    assert_equal(dml.list_docs(site_name, 'src', directory=newdir), ['hendriksen'])
    assert_equal(dml.list_docs(site_name, 'dest', directory=newdir), ['hendriksen'])
    print('ok')

    print('test retrieving site statistics:')  # .format(newdir))
    data = dml.get_all_doc_stats(site_name)
    pprint.pprint(data)  # date/time dependent, no use comparing output
    print('ok')


def main():
    """define a test site, buid it and clean up after use
    """
    ## print(dml.list_dirs('blub'))
    site_name = 'test'
    clear_site_contents(site_name)
    try:
        test_dml(site_name)
    except AssertionError:
        raise
    finally:
        list_site_contents(site_name)
    clear_site_contents(site_name)

if __name__ == '__main__':
    main()
