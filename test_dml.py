import os, sys
import pprint
import datetime
import pathlib
import shutil
from app_settings import DML, WEBROOT, SETTFILE
if DML == 'fs':
    print('using file system dml')
    import docs2fs as dml
elif DML == 'mongo':
    print('using mongodb dml')
    import docs2mongo as dml
elif DML == 'postgres':
    print('using postgresql dml')
    import docs2pg as dml

## def list_database_contents():
    ## print('\n--------------- Listing database contents -------------')
    ## for doc in dml.read_db():
        ## pprint.pprint(doc)

## def clear_database_contents():
    ## dml.clear_db()
    ## path = os.path.join(os.path.dirname(__file__), 'rst2html-data')
    ## shutil.rmtree(path)
    ## os.mkdir(path)

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
    dml.clear_site_data(sitename)
    if DML == 'fs':
        path = WEBROOT / sitename
    else:
        path = pathlib.Path(__file__).parent / 'rst2html-data' / sitename
    try:
        shutil.rmtree(str(path))
    except FileNotFoundError:
        pass
    ## path.mkdir()

def full_update_mirror(site_name, docname, directory = ''):
    dml.update_mirror(site_name, docname, directory)
    if DML == 'fs': # need to also physically copy to mirror
        frompath = WEBROOT / site_name / 'target'
        destpath = WEBROOT / site_name
        if directory:
            frompath /= directory
            destpath /= directory
            if not destpath.exists():
                destpath.mkdir(parents=True)
        frompath /= docname
        destpath /= docname
        dml.save_to(destpath, dml.read_data(frompath)[1])

def test_dml(site_name):

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
    setting = 'unknown_setting'
    value = 'secret value'
    dml.change_setting(site_name, setting, value)
    setting = 'url'
    value = '/rst2html-data/test'
    dml.change_setting(site_name, setting, value)
    rootdoc = 'jansen'
    print('ok')

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
    assert data == ""
    print('ok')

    print('creating first doc in root...', end=' ')
    assert dml.list_dirs(site_name, 'src') == []
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == []
    print('ok')

    print('updating first doc in root...', end=' ')
    dml.update_rst(site_name, rootdoc, 'ladida')
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest == datetime.datetime.min and
            stats.to_mirror == datetime.datetime.min)
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == []
    print('ok')

    print('updating first doc`s html in root...', end=' ')
    dml.update_html(site_name, rootdoc, '<p>ladida</p>')
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.to_mirror == datetime.datetime.min)
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == ['jansen']
    print('ok')

    print('testing administrative move to mirror...', end=' ')
    is_ok = False
    try:
        dml.update_mirror(site_name, '')
    except AttributeError:
        is_ok = True
    assert is_ok
    full_update_mirror(site_name, rootdoc)
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.to_mirror != datetime.datetime.min)
    dml.update_rst(site_name, rootdoc, 'bah humbug')
    dml.update_html(site_name, rootdoc, '<p>bah humbug</p>')
    full_update_mirror(site_name, rootdoc)
    print('ok')

    print('getting contents of documents in root...', end=' ')
    data = dml.get_doc_contents(site_name, rootdoc, 'src')
    assert data == 'bah humbug'
    data = dml.get_doc_contents(site_name, rootdoc, 'dest')
    assert data == '<p>bah humbug</p>'
    print('ok')

    newdir = 'guichelheil'
    print('creating new dir {}...'.format(newdir), end=' ')
    otherdoc = 'hendriksen'
    dml.create_new_dir(site_name, newdir)
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src', directory=newdir) == []
    failed = False
    try:
        assert dml.list_docs(site_name, 'dest', directory=newdir) == []
    except FileNotFoundError:
        failed = True
    assert failed
    # try again to catch error - apparently this doesn't fail
    failed = False
    try:
        dml.create_new_dir(site_name, newdir)
    except FileExistsError:
        failed = True
    assert failed
    print('ok')

    mld = dml.create_new_doc(site_name, otherdoc, directory=newdir)
    print('updating rst in {}...'.format(newdir), end=' ')
    dml.update_rst(site_name, otherdoc, 'zoinks', directory=newdir)
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    failed = False
    try:
        assert dml.list_docs(site_name, 'dest', directory=newdir) == []
    except FileNotFoundError:
        failed = True
    assert failed
    print('ok')

    print('updating html in {}...'.format(newdir), end=' ')
    dml.update_html(site_name, otherdoc, '<p>zoinks</p>', directory=newdir)
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == ['guichelheil']
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    assert dml.list_docs(site_name, 'dest', directory=newdir) == ['hendriksen']
    print('ok')

    print('testing administrative move to mirror from {}...'.format(newdir),
        end=' ')
    full_update_mirror(site_name, otherdoc, directory=newdir)
    dml.update_rst(site_name, otherdoc, 'but not them', directory=newdir)
    dml.update_html(site_name, otherdoc, '<p>but not them</p>', directory=newdir)
    full_update_mirror(site_name, otherdoc, directory=newdir)
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    assert dml.list_docs(site_name, 'dest', directory=newdir) == ['hendriksen']
    print('ok')

    print('getting contents of documents in {}...'.format(newdir), end=' ')
    data = dml.get_doc_contents(site_name, otherdoc, 'src', directory=newdir)
    assert data == 'but not them'
    data = dml.get_doc_contents(site_name, otherdoc, 'dest', directory=newdir)
    assert data == '<p>but not them</p>'
    print('ok')

def main():
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
