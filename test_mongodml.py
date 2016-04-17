import os, sys
import pprint
import datetime
import shutil
import docs2mongo as dml

def list_database_contents():
    print('\n--------------- Listing database contents -------------')
    for doc in dml.read_db():
        pprint.pprint(doc)

def clear_database_contents():
    dml.clear_db()
    path = os.path.join(os.path.dirname(__file__), 'rst2html-data')
    shutil.rmtree(path)
    os.mkdir(path)

def list_site_contents(sitename, filename=''):
    """looks like pprint shows the keys in alphabetic order,
    so probably no ordering of my own needed
    """
    errs = ''
    try:
        sitedoc, docdata = dml.list_site_data(sitename)
    except FileNotFoundError as e:
        errs = str(e)
        sitedoc, docdata = {}, []
    if not filename:
        print('\n--------------- Listing contents of site {} -------------'.format(
            sitename))
        if errs:
            print(errs)
        else:
            pprint.pprint(sitedoc)
            for doc in docdata:
                pprint.pprint(doc)
        return
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
    dml.clear_site_data()
    path = os.path.join(os.path.dirname(__file__), 'rst2html-data')
    shutil.rmtree(path)
    os.mkdir(path)

def test_dml():
    test = dml.create_new_site(site_name)
    assert test is ''
    test = dml.create_new_site(site_name)
    assert test == 'Site already exists'
    test = dml.list_sites()
    assert site_name in test
    ## list_database_contents()
    setting = 'unknown_setting'
    value = 'secret value'
    dml.change_setting(site_name, setting, value)
    setting = 'url'
    value = '/rst2html-data/test'
    dml.change_setting(site_name, setting, value)
    ## list_database_contents()
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
    assert data == ""
    print('ok')
    ## list_database_contents()
    print('creating first doc in root...', end=' ')
    assert dml.list_dirs(site_name, 'src') == []
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == []
    print('ok')
    print('updating first doc in root...', end=' ')
    dml.update_rst(site_name, rootdoc, 'ladida')
    ## list_database_contents()
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest == datetime.datetime.min and
            stats.to_mirror == datetime.datetime.min)
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == []
    print('ok')
    print('updating first doc`s html in root...', end=' ')
    dml.update_html(site_name, rootdoc, '<p>ladida</p>')
    ## list_database_contents()
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.to_mirror == datetime.datetime.min)
    assert dml.list_docs(site_name, 'src') == ['jansen']
    assert dml.list_docs(site_name, 'dest') == ['jansen']
    print('ok')
    dml.update_mirror(site_name, rootdoc)
    ## list_database_contents()
    stats = dml.get_doc_stats(site_name, rootdoc)
    assert (stats.src != datetime.datetime.min and
            stats.dest != datetime.datetime.min and
            stats.to_mirror != datetime.datetime.min)
    dml.update_rst(site_name, rootdoc, 'bah humbug')
    ## list_database_contents()
    dml.update_html(site_name, rootdoc, '<p>bah humbug</p>')
    ## list_database_contents()
    dml.update_mirror(site_name, rootdoc)
    print('getting contents of documents in root...', end=' ')
    data = dml.get_doc_contents(site_name, rootdoc, 'src')
    assert data == 'bah humbug'
    data = dml.get_doc_contents(site_name, rootdoc, 'dest')
    assert data == '<p>bah humbug</p>'
    print('ok')
    ## list_database_contents()
    newdir = 'guichelheil'
    print('creating new dir {}...'.format(newdir), end=' ')
    otherdoc = 'hendriksen'
    dml.create_new_dir(site_name, newdir)
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src', directory=newdir) == []
    assert dml.list_docs(site_name, 'dest', directory=newdir) == []
    # try again to catch error - apparently this doesn't fail
    failed = True
    try:
        dml.create_new_dir(site_name, newdir)
    except FileExistsError:
        failed = True
    assert failed
    print('ok')

    ## list_database_contents()
    mld = dml.create_new_doc(site_name, otherdoc, directory=newdir)
    ## list_database_contents()
    print('updating rst in {}...'.format(newdir), end=' ')
    dml.update_rst(site_name, otherdoc, 'zoinks', directory=newdir)
    ## list_database_contents()
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == []
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    assert dml.list_docs(site_name, 'dest', directory=newdir) == []
    ## list_database_contents()
    print('ok')
    print('updating html in {}...'.format(newdir), end=' ')
    dml.update_html(site_name, otherdoc, '<p>zoinks</p>', directory=newdir)
    assert dml.list_dirs(site_name, 'src') == ['guichelheil']
    assert dml.list_dirs(site_name, 'dest') == ['guichelheil']
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    assert dml.list_docs(site_name, 'dest', directory=newdir) == ['hendriksen']
    ## list_database_contents()
    print('ok')
    dml.update_mirror(site_name, otherdoc, directory=newdir)
    ## list_database_contents()
    dml.update_rst(site_name, otherdoc, 'but not them', directory=newdir)
    ## list_database_contents()
    dml.update_html(site_name, otherdoc, '<p>but not them</p>', directory=newdir)
    ## list_database_contents()
    dml.update_mirror(site_name, otherdoc, directory=newdir)
    assert dml.list_docs(site_name, 'src', directory=newdir) == ['hendriksen']
    assert dml.list_docs(site_name, 'dest', directory=newdir) == ['hendriksen']
    print('getting contents of documents in {}...'.format(newdir), end=' ')
    data = dml.get_doc_contents(site_name, otherdoc, 'src', directory=newdir)
    assert data == 'but not them'
    data = dml.get_doc_contents(site_name, otherdoc, 'dest', directory=newdir)
    assert data == '<p>but not them</p>'
    print('ok')

def main()
    ## print(dml.list_dirs('blub'))
    site_name = 'test'
    clear_site_contents(site_name)
    try:
        test_dml(site_name)
    except AssertionError:
        raise
    finally:
        list_database_contents()
    clear_site_contents(site_name)

if __name__ == '__main__':
    main()
