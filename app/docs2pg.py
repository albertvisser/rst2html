"""Data processing routines for Postgres SQL version
"""
import datetime
import shutil
import functools
import pathlib
import contextlib
import psycopg2 as pg
import psycopg2.extras as pgx
from app_settings_postgres import user, password, Stats, WEBROOT, LOC2EXT  # , LOCS
from .docs2fs import save_to
conn = pg.connect(database="rst2html", user=user, password=password)
TABLES = ('sites', 'site_settings', 'directories', 'doc_stats', 'documents', 'templates')


# factor out database boilerplate code using a decorator
def with_cursor(f):
    """boilerplate code for doing work on the database

    (open cursor, execute, commit, close cursor)
    """
    def wrapping(*args, **kwargs):
        cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
        result = f(cur, *args, **kwargs)
        conn.commit()
        cur.close()
        return result
    return wrapping


#
# zelfde API als de andere dml-modules:
#
@with_cursor
def clear_db(cur):
    """remove all data from the database
    """
    for name in TABLES:
        ## sql = 'truncate table {};'.format(name)
        ## cur.execute(sql)
        cur.execute(f'truncate table {name};')


@with_cursor
def read_db(cur):
    """read and return all data from the database
    """
    result = []
    cur.execute(f'select sitename, id from {TABLES[0]} order by sitename;')
    sites = [(x['sitename'], x['id']) for x in cur.fetchall()]
    for sitename, site_id in sites:
        sitedict = {'name': sitename}
        cur.execute(f'select settname, settval from {TABLES[1]} where site_id = %s'
                    ' order by settname;', (site_id,))
        sitedict['settings'] = dict(cur.fetchall())
        cur.execute(f'select dirname, id from {TABLES[2]} where site_id = %s order by dirname;',
                    (site_id,))
        sitedirs = [(x['dirname'], x['id']) for x in cur.fetchall()]
        sitedict['docs'] = []
        # if we keep the site_id in the docstats table we could restrict this to one db-query
        # and filter the result set inside the loop
        # although this should also be possible with a subselect or something like that
        for dirname, dir_id in sitedirs:
            dirlist = []
            cur.execute(f'select * from {TABLES[3]} where dir_id = %s order by docname;',
                        (dir_id,))
            for resultdict in cur:
                resultdict['dirname'] = dirname
                dirlist.append(resultdict)
            sitedict['docs'].append(dirlist)
        result.append(sitedict)
    return result


@with_cursor
def list_sites(cur):
    """list all sites registered in the database
    """
    result = []
    cur.execute(f'select sitename from {TABLES[0]};')
    result = [x['sitename'] for x in cur.fetchall()]
    return result


def create_new_site(site_name):
    """set up the database and file system for managing a new site
    """
    path = WEBROOT / site_name
    if _get_site_id(site_name) is not None or path.exists():
        raise FileExistsError('site_name_taken')
    _make_site(site_name)
    # create the physical destination (mirror) so that css and images can be moved there
    path.mkdir(parents=True)


def rename_site(site_name, newname):
    """change the site's name unconditionally
    """
    siteid = _get_site_id(site_name)
    if siteid is None:  # or not path.exists():
        raise FileNotFoundError
    _do_rename(siteid, newname)
    # create the physical destination (mirror) so that css and images can be moved there
    path = WEBROOT / site_name
    newpath = WEBROOT / newname
    path.rename(newpath)


def read_settings(site_name):
    """read the site settings and make sure they are returned in the format
    used by the processing code
    """
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    settings = _get_settings(siteid)
    if 'css' in settings:
        if settings['css'] == '':
            settings['css'] = []
        else:
            settings['css'] = settings['css'].split(';')
    for test in ('wid', 'hig'):
        if test in settings:
            with contextlib.suppress(ValueError):
                settings[test] = int(settings[test])
    return settings


def update_settings(site_name, settings_dict):
    """replace all settings at once
    """
    siteid = _get_site_id(site_name)
    oldsett = _get_settings(siteid)
    if 'css' in oldsett:
        oldsett['css'] = ';'.join(list(oldsett['css']))
    newsett = dict(settings_dict)
    if 'css' in newsett:
        newsett['css'] = ';'.join(list(newsett['css']))
    _modify_settings(siteid, oldsett, newsett)
    return _get_settings(siteid)


def clear_settings(site_name):  # untested - do I need/want this?
    """update settings to empty dict instead of initialized)
    """
    return update_settings(site_name, {})


def list_dirs(site_name, doctype=''):
    """list subdirs with documents of a given type in a given site

    raises FileNotFoundError if site doesn't exist
    """
    if doctype not in ('', 'src', 'dest'):
        raise RuntimeError('wrong doctype for list_dirs')
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    return _get_dirlist(siteid, doctype)


def create_new_dir(site_name, directory):
    """make it possible to add files in a separate section

    allows for organizing the site somewhat logically
    translates physically to directories directly under the site root
    """
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    if directory == '/':
        raise RuntimeError('')
    if directory in list_dirs(site_name):
        raise FileExistsError
    _make_dir(siteid, directory)


@with_cursor
def rename_dir(cur, site_name, oldname, newname):
    """rename the entry for the given directory name
    """
    mld = ''
    siteid = _get_site_id(site_name)
    dirid = _get_dir_id(siteid, oldname)
    cur.execute(f'update {TABLES[2]} set dirname = %s where site_id = %s and id = %s;',
                (newname, siteid, dirid))
    return mld


def remove_dir(site_name, directory):  # untested - do I need/want this?
    """remove site directory and all documents in it
    """
    # remove all documents from table site_documents where directory = given directory
    # we'd also need to remove the actual documents (I think no dml version does that yet)
    # if we add a per-site directories table also remove it from there
    raise NotImplementedError


def list_docs(site_name, doctype='', directory='', deleted=False):
    """list the documents of a given type in a given directory

    raises FileNotFoundError if site or directory doesn't exist
    """
    if not directory:
        directory = '/'
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    ## doclist = _get_docs_in_dir(dirid)
    return _get_doclist(dirid, doctype, deleted)


def list_templates(site_name):
    """return a list of template names for this site"""
    siteid = _get_site_id(site_name)
    return _get_tpllist(siteid)


def read_template(site_name, doc_name):
    """get the source of a specific template"""
    siteid = _get_site_id(site_name)
    return _get_template(siteid, doc_name)


def write_template(site_name, doc_name, data):
    """store the source for a template"""
    mld = ''
    siteid = _get_site_id(site_name)
    _put_template(siteid, doc_name, data)
    return mld


@with_cursor
def rename_template(cur, site_name, doc_name, new_name):
    """change the name of a template"""
    mld = ''
    siteid = _get_site_id(site_name)
    cur.execute(f'select id from {TABLES[5]} where site_id = %s and name = %s;', (siteid, doc_name))
    row = cur.fetchone()
    cur.execute(f'update {TABLES[5]} set name = %s where site_id = %s and id = %s;',
                (new_name, siteid, row['id']))
    return mld


def create_new_doc(site_name, doc_name, directory=''):
    """add a new (source) document to the given directory

    raises AttributeError on missing doc_name,
           FileNotFoundError if directory doesn't exist
    """
    if not doc_name:
        raise AttributeError('no_name')

    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem
    siteid = _get_site_id(site_name)
    ## if siteid is None:
        ## raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    if doc_name in _get_docs_in_dir(dirid):
        raise FileExistsError

    new_doc_id = _add_doc()
    _add_dts(dirid, doc_name, new_doc_id)


def get_doc_contents(site_name, doc_name, doctype='', directory='', previous=False):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(site_name)
    dirid = _get_dir_id(siteid, directory)
    docid, src_id, dest_id = _get_doc_ids(dirid, doc_name)
    if docid is None:
        raise FileNotFoundError(f"Document '{doc_name}' not found in collection")
    if doctype in ('', 'src'):
        if src_id is None:
            ## raise FileNotFoundError("Document {} source not found".format(doc_name))
            raise FileNotFoundError("src_file_missing")
        docid = src_id
    else:  # if doctype == 'dest': vooralsnog de enige andere mogelijkheid
        if dest_id is None:
            ## raise FileNotFoundError("Document {} html not found".format(doc_name))
            raise FileNotFoundError("html_file_missing")
        docid = dest_id
    result = _fetch_doc_contents(docid, previous)
    return result or (f"{directory.replace('/', '')}/{doc_name} has id {docid},"
                      f" but no {'previous' if previous else 'current'} contents")


def update_rst(site_name, doc_name, contents, directory=''):
    """update a source document in the given directory

    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist (should have been created
            using create_new_doc first)
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not contents:
        raise AttributeError('no_contents')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id, rst_id, _ = _get_doc_ids(dirid, doc_name)
    if doc_id is None:
        raise FileNotFoundError("no_document")

    oldtext = _get_doc_text(rst_id)
    _put_update(doc_id, rst_id, contents, oldtext)


def revert_rst(sitename, doc_name, directory=''):
    """reset a source document in the given directory to the previous contents

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
           FileNotFoundError if no backup present
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(sitename)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id, rst_id, _ = _get_doc_ids(dirid, doc_name)
    if doc_id is None:
        raise FileNotFoundError("no_document")
    _do_revert(rst_id, doc_id)


def mark_src_deleted(site_name, doc_name, directory=''):
    """mark a source document in the given directory as deleted
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id = _get_doc_ids(dirid, doc_name)[0]
    if doc_id is None:
        raise FileNotFoundError("no_document")
    _do_delete(doc_id)


def update_html(site_name, doc_name, contents, directory='', dry_run=True):
    """update a converted document in the given directory

    create a new entry if it's the first-time conversion
    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not contents:
        raise AttributeError('no_contents')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id, _, html_id = _get_doc_ids(dirid, doc_name)
    if doc_id is None:
        raise FileNotFoundError("no_document")
    if dry_run:
        return

    if html_id is None:
        new_html_id = _add_doc()
        oldtext = ''
    else:
        new_html_id = None
        oldtext = _get_doc_text(html_id)
    _put_html(html_id, new_html_id, doc_id, contents, oldtext)


def list_deletions_target(sitename, directory=''):
    """list pending deletions in source environment"""
    return list_deletions(get_dirlist_for_site(sitename, directory), 'source')


def apply_deletions_target(site_name, directory=''):
    """Copy deletion markers from source to target environment (if not already there)
    """
    dirlist = get_dirlist_for_site(site_name, directory)
    deleted, deleted_names = apply_deletions(dirlist, 'source')
    _update_target_directory(deleted)
    return sorted(deleted_names)


def update_mirror(site_name, doc_name, data, directory='', dry_run=True):
    """administer promoting the converted document in the given directory
    to the mirror site
    some additions are only saved in the mirror html hence the data argument
    otherwise we could get it from the target location

    raise AttributeError if no name provided
    create a new entry if it's the first time
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not data:
        raise AttributeError('no_contents')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem

    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id = _get_doc_ids(dirid, doc_name)[0]
    if doc_id is None:
        raise FileNotFoundError("no_document")
    if dry_run:
        return

    _update_mirror_dts(doc_id)

    path = WEBROOT / site_name
    if directory != '/':
        path /= directory
    if not path.exists():
        path.mkdir(parents=True)
    path /= doc_name
    path = path.with_suffix(LOC2EXT['dest'])
    sett = read_settings(site_name)
    seflinks = sett.get('seflinks', False)
    if not path.exists() and not seflinks:
        path.touch()
    save_to(path, data, seflinks)


def list_deletions_mirror(sitename, directory=''):
    """list pending deletions in target environment"""
    return list_deletions(get_dirlist_for_site(sitename, directory), 'target')


def apply_deletions_mirror(site_name, directory=''):
    """Copy deletion markers from target to mirror environment and remove in all envs
    """
    dirlist = get_dirlist_for_site(site_name, directory)
    deleted, deleted_names = apply_deletions(dirlist, 'target')
    # cur = conn.cursor()
    deleted = [(x[3],) for x in deleted]
    # regels komen terug als None, 1, True, row['id']
    # effectief gebeurt er niks met source_id
    _update_mirror_directory(deleted)

    path = WEBROOT / site_name
    # if directory != '/':
    #     path /= directory
    for doc_name in deleted_names:
        docpath = path / doc_name
        ext = LOC2EXT['dest']
        if docpath.suffix != ext:
            docpath = docpath.with_suffix(ext)
        if docpath.exists():
            docpath.unlink()
    return sorted(deleted_names)


def get_dirlist_for_site(sitename, directory):
    "get a list of dirids (can be just one)"
    siteid = _get_site_id(sitename)
    if siteid is None:
        raise FileNotFoundError('no_site')
    if not directory:
        dirlist = ['/']
    elif directory == '*':
        dirlist = ['/'] + list_dirs(sitename, 'src')
    else:
        dirlist = [directory]
    for ix, directory in enumerate(dirlist):
        dirid = _get_dir_id(siteid, directory)
        if dirid is None:
            raise FileNotFoundError('no_subdir')
        dirlist[ix] = (directory, dirid)
    return dirlist


@with_cursor
def list_deletions(cur, dirlist, stage):
    "list pending deletions for given directories in a given environment"
    deletions = []
    for directory, dirid in dirlist:
        cur.execute(f'select id, docname, target_docid from {TABLES[3]}'
                    f' where dir_id = %s and {stage}_deleted = %s;', (dirid, True))
        to_be_deleted = list(cur)
        if directory == '/':
            deletions.extend([row['docname'] for row in to_be_deleted])
        else:
            deletions.extend(['/'.join((directory, row['docname'])) for row in to_be_deleted])
    return sorted(deletions)


@with_cursor
def apply_deletions(cur, dirlist, stage):
    "apply deletions for given directories in the given environment"
    docids, deleted, deleted_names = [], [], []
    for directory, dirid in dirlist:
        cur.execute(f'select id, docname, target_docid from {TABLES[3]}'
                    f' where dir_id = %s and {stage}_deleted = %s;', (dirid, True))
        to_delete = list(cur)
        if stage == 'source':
            docids += [(row['target_docid'],) for row in to_delete]
            from_table = TABLES[4]
        else:
            docids = [(row['id'],) for row in to_delete]
            from_table = TABLES[3]
        if directory == '/':
            deleted_names += [row['docname'] for row in to_delete]
        else:
            deleted_names += ['/'.join((directory, row['docname'])) for row in to_delete]
        deleted += [(None, 1, True, row['id']) for row in to_delete]

    cur.executemany(f'delete from {from_table} where id = %s;', docids)
    return deleted, deleted_names


def get_doc_stats(site_name, docname, dirname=''):
    """get statistics for a document in a site subdirectory"""
    if not dirname:
        dirname = '/'
    doc_name = pathlib.Path(docname).stem
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, dirname)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    doc_id = _get_doc_ids(dirid, doc_name)[0]
    if doc_id is None:
        raise FileNotFoundError("no_document")
    return _get_stats(_get_datetimestamps(doc_id))


def get_all_doc_stats(site_name):
    """get statistics for all site subdirectories"""
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirids = _get_all_dir_ids(siteid)
    dirnames, all_stats = _get_stats_for_dirs(siteid, dirids)
    stats_list = []
    for name in sorted(dirnames):
        cp = functools.partial(_is_equal, y=name)
        dirlist = filter(cp, all_stats)  # Pylint: using a list comprehension can be clearer?
        stats_list.append((name, [x[1:] for x in dirlist]))
    return stats_list


# deze worden niet gebruikt door de applicatie, maar wel door de testroutines
def list_site_data(site_name):
    """list all data on the site in a readable form

    for testing purposes and such
    """
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')

    sitedoc = {'_id': siteid, 'name': site_name, 'settings': _get_settings(siteid)}

    dirmap = _fetch_dirmap(siteid)
    dirids = list(dirmap)
    sitedoc['docs'] = {x: {} for x in dirmap.values()}

    docstats, docnames = [], {}
    for row in _fetch_site_data(dirids):
        doc, dir = row['docname'], dirmap[row['dir_id']]
        docitem = doc if dir == '/' else f'{dir}/{doc}'
        ## docstats.append((dir, doc,
            ## ('src', {'docid': row['source_docid'], 'updated': row['source_updated']}),
            ## ('dest', {'docid': row['target_docid'], 'updated': row['target_updated']}),
            ## ('to_mirror', {'updated': row['mirror_updated']})))
        docdata = [dir, doc]
        sourcedoc, destdoc = {}, {}
        if row['source_docid'] is not None:
            sourcedoc['docid'] = row['source_docid']
        if row['source_updated'] is not None:
            sourcedoc['updated'] = row['source_updated']
        if row['source_deleted'] is not None:
            sourcedoc['deleted'] = row['source_deleted']
        if sourcedoc:
            docdata.append(('src', sourcedoc))
        if row['target_docid'] is not None:
            destdoc['docid'] = row['target_docid']
        if row['target_updated'] is not None:
            destdoc['updated'] = row['target_updated']
        if row['target_deleted'] is not None:
            destdoc['deleted'] = row['target_deleted']
        if destdoc:
            docdata.append(('dest', destdoc))
        if row['mirror_updated'] is not None:
            docdata.append(('mirror', {'updated': row['target_updated']}))
        docstats.append(tuple(docdata))
        docnames[row['source_docid']] = (docitem, 'src')
        docnames[row['target_docid']] = (docitem, 'dest')

    for dir, doc, *items in sorted(docstats):
        sitedoc['docs'][dir][doc] = dict(items)

    data = _fetch_doc_data(siteid, docnames)
    return sitedoc, sorted(data, key=lambda x: x['_id'])


def clear_site_data(site_name):
    """remove site from database, also delete mirror site files from file system
    """
    db_data = fs_data = True
    siteid = _get_site_id(site_name)
    if siteid is None:
        db_data = False
    path = WEBROOT / site_name
    if not path.exists():
        fs_data = False

    if db_data:
        # if not fs_data
        #     raise RuntimeError("data inconstent: database without mirror site")
        dirids = _get_all_dir_ids(siteid)

        _delete_dir_data(siteid, dirids)

    if fs_data:
        # if not db_data
        #     raise RuntimeError("data inconstent: mirror without database site")
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(str(path))


#
# deze-dml-specifieke subroutines:
#
def _is_equal(x, y):
    """special comparison used in get_all_doc_starts"""
    return x[0] == y


@with_cursor
def _get_site_id(cur, site_name):
    """returns the id of the site with the given name
    """
    cur.execute(f'select id from {TABLES[0]} where sitename = %s;', (site_name,))
    result = cur.fetchone()
    if result:
        result = result['id']
    return result


@with_cursor
def _get_dir_id(cur, site_id, dirname):
    """returns the id of the site subdirectory
    """
    result = None
    cur.execute(f'select id from {TABLES[2]} where site_id = %s and dirname = %s;',
                (site_id, dirname))
    result = cur.fetchone()
    if result:
        result = result['id']
    return result


@with_cursor
def _get_all_dir_ids(cur, site_id):
    """returns the ids of all site subdirectories
    """
    result = None
    cur.execute(f'select id from {TABLES[2]} where site_id = %s;', (site_id,))
    result = list(cur.fetchall())
    if result:
        result = [x['id'] for x in result]
    return result


@with_cursor
def _get_docs_in_dir(cur, dir_id):
    """returns the names of all documents in a site subdirectory
    """
    result = []
    cur.execute(f'select docname from {TABLES[3]} where dir_id = %s;', (dir_id,))
    result = list(cur.fetchall())
    if result:
        result = [x['docname'] for x in result]
    return result


@with_cursor
def _get_doc_ids(cur, dir_id, docname):
    """returns various ids for a given document in a given site subdirectory
    """
    # do you need the directory if you know the document id?
    # Not if you work by docid but this is using the docname
    cur.execute(f'select id, source_docid, target_docid from {TABLES[3]} '
                'where dir_id = %s and docname = %s;', (dir_id, docname))
    result = cur.fetchone()
    if result:
        result = result['id'], result['source_docid'], result['target_docid']
    else:
        result = None, None, None
    return result


@with_cursor
def _get_doc_text(cur, doc_id):
    """returns the text of a document
    """
    cur.execute(f'select currtext from {TABLES[4]} where id = %s;', (doc_id,))
    result = cur.fetchone()
    result = result['currtext'] if result else (None, None, None)  # waarom zo?
    return result


@with_cursor
def _get_settings(cur, site_id):
    """returns a dictionary containg the site settings
    """
    settings = {}
    cur.execute(f'select settname, settval from {TABLES[1]} where site_id = %s', (site_id,))
    for row in cur:
        settings[row['settname']] = row['settval']
    return settings


@with_cursor
def _add_doc(cur):
    """create new document
    """
    cur.execute(f'insert into {TABLES[4]} (currtext, previous) values (%s, %s) returning id',
                ('', ''))
    new_doc_id = cur.fetchone()['id']
    return new_doc_id


def _get_stats(docinfo):
    """retrieve site stats from database"""
    source_updated, source_deleted, target_updated, target_deleted, mirror_updated = docinfo
    stats = []
    if source_deleted:
        stats.append('[deleted]')
    elif source_updated:
        stats.append(source_updated)
    else:
        stats.append(datetime.datetime.min)
    if target_deleted:
        stats.append('[deleted]')
    elif target_updated:
        stats.append(target_updated)
    else:
        stats.append(datetime.datetime.min)
    if mirror_updated:
        stats.append(mirror_updated)
    else:
        stats.append(datetime.datetime.min)
    return Stats(*stats)


@with_cursor
def _make_site(cur, site_name):
    "create the new site in the database"
    cur.execute(f'insert into {TABLES[0]} (sitename) values (%s) returning id;', (site_name,))
    siteid = cur.fetchone()['id']
    cur.execute(f'insert into {TABLES[2]} (site_id, dirname) values (%s, %s)', (siteid, '/'))


@with_cursor
def _make_dir(cur, siteid, directory):
    "add the directory to the database"
    cur.execute(f'insert into {TABLES[2]} (site_id, dirname) values (%s, %s)', (siteid, directory))


@with_cursor
def _do_rename(cur, siteid, site_name):
    "rename the new site in the database"
    cur.execute('update sites set sitename = %s where id = %s;', (site_name, siteid))


@with_cursor
def _modify_settings(cur, siteid, oldsett, newsett):
    sel = 'site_id = %s and settname = %s'
    for sett, oldsettval in oldsett.items():
        try:
            newsettval = newsett.pop(sett)
        except KeyError:
            cur.execute(f'delete from {TABLES[1]} where {sel}', (siteid, sett))
            continue
        if newsettval != oldsettval:
            cur.execute(f'update {TABLES[1]} set settval = %s where {sel}',
                        (newsettval, siteid, sett))
    for sett, newsettval in newsett.items():  # left over new items
        cur.execute(f'insert into {TABLES[1]} (site_id, settname, settval) values (%s, %s, %s)',
                    (siteid, sett, newsettval))


@with_cursor
def _get_dirlist(cur, siteid, doctype):
    """returns all dirs that have documents of the given type
    """
    cur.execute(f'select id, dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    dirmap = {row['id']: row['dirname'] for row in cur}
    dirids = list(dirmap)
    if doctype == 'dest':
        cur.execute(f'select dir_id, target_docid from {TABLES[3]} where dir_id = any(%s);',
                    (dirids,))
        dirids = set()
        for row in cur:
            if row['target_docid'] is not None:
                dirids.add(row['dir_id'])
    dirlist = []
    for id in dirids:
        test = dirmap[id]
        if test != '/':
            dirlist.append(test)
    return dirlist


@with_cursor
def _get_doclist(cur, dirid, doctype, deleted):
    """returns all documents of the given type
    """
    cur.execute('select docname, source_docid, source_deleted, target_docid, target_deleted,'
                f' mirror_updated from {TABLES[3]} where dir_id = %s;', (dirid,))
    doclist = []
    for row in cur:
        add = False
        if doctype in ('', 'src') and row['source_docid']:
            # print(row['source_deleted'])
            add = bool(row['source_deleted']) == deleted
        elif doctype == 'dest' and row['target_docid']:
            add = bool(row['target_deleted']) == deleted
        elif doctype == 'mirror' and row['mirror_updated']:
            add = not deleted
        if add:
            doclist.append(row['docname'])
    return doclist


@with_cursor
def _get_tpllist(cur, siteid):
    """returns a list of al templates in the database"""
    cur.execute(f'select id, name from {TABLES[5]} where site_id = %s;', (siteid,))
    return [row['name'] for row in cur]


@with_cursor
def _get_template(cur, siteid, doc_name):
    """returns the contents of a given template (name)"""
    cur.execute(f'select text from {TABLES[5]} where site_id = %s and name = %s;', (siteid, doc_name))
    row = cur.fetchone()
    return row['text']


@with_cursor
def _put_template(cur, siteid, doc_name, data):
    "store the updated template in the database"
    cur.execute(f'select text from {TABLES[5]} where site_id = %s and name = %s;', (siteid, doc_name))
    if not cur.fetchone():
        cur.execute(f'insert into {TABLES[5]} (site_id, name, text) values (%s, %s, %s);',
                    (siteid, doc_name, data))
    else:
        cur.execute(f'update {TABLES[5]} set text = %s where site_id = %s and name = %s;',
                    (data, siteid, doc_name))


@with_cursor
def _add_dts(cur, dir_id, docname, doc_id):
    "create the date-time stamp for the new document"
    dts = datetime.datetime.utcnow()
    cur.execute(f'insert into {TABLES[3]} (dir_id, docname, source_docid, source_updated)'
                ' values (%s, %s, %s, %s);', (dir_id, docname, doc_id, dts))


@with_cursor
def _fetch_doc_contents(cur, docid, previous):
    "get data from database"
    column = 'previous' if previous else 'currtext'
    cur.execute(f'select {column} from {TABLES[4]} where id = %s;', (docid,))
    row = cur.fetchone()
    return row[column] if row else ''


@with_cursor
def _put_update(cur, doc_id, rst_id, contents, oldtext):
    "add update doc to database"
    cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                (oldtext, contents, rst_id))
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set source_updated = %s where id = %s;', (dts, doc_id))


@with_cursor
def _do_revert(cur, rst_id, doc_id):
    """"undo" last update
    """
    cur.execute(f'select previous from {TABLES[4]} where id = %s;', (rst_id,))
    oldtext = cur.fetchone()['previous']
    cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                ('', oldtext, rst_id))
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set source_updated = %s where id = %s;', (dts, doc_id))


@with_cursor
def _do_delete(cur, doc_id):
    "mark as deleted in the database"
    cur.execute(f'select source_docid from {TABLES[3]} where id = %s;', (doc_id,))
    rst_id = cur.fetchone()[0]
    cur.execute(f'delete from {TABLES[4]} where id = %s;', (rst_id,))
    cur.execute(f'update {TABLES[3]} set source_deleted = %s where id = %s;', (True, doc_id))


@with_cursor
def _put_html(cur, html_id, new_html_id, doc_id, contents, oldtext):
    "add the new or updated html to the database"
    dts = datetime.datetime.utcnow()
    if html_id is None:
        cur.execute(f'update {TABLES[4]} set currtext = %s where id = %s;', (contents, new_html_id))
        cur.execute(f'update {TABLES[3]} set target_docid = %s, target_updated = %s where id = %s;',
                    (new_html_id, dts, doc_id))
    else:
        cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                    (oldtext, contents, html_id))
        cur.execute(f'update {TABLES[3]} set target_updated = %s where id = %s;', (dts, doc_id))


@with_cursor
def _update_target_directory(cur, deleted):
    "update directory in database after deletion from target"
    # regels komen binnen als None, 1, True, row['id']
    # effectief gebeurt er niks met source_id
    deleted = [(x[0], x[0], x[0], x[1], x[2], x[3]) for x in deleted]
    cur.executemany(f'update {TABLES[3]} set source_docid = %s, source_updated = %s,'
                    ' source_deleted = %s, target_docid = %s, target_deleted = %s'
                    ' where id = %s;', deleted)


@with_cursor
def _update_mirror_dts(cur, doc_id):
    "update date-time stamp in database"
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set mirror_updated = %s where id = %s;', (dts, doc_id))


@with_cursor
def _update_mirror_directory(cur, deleted):
    "update directory in database after deletion from mirror"
    cur.executemany(f'delete from {TABLES[3]} where id = %s;', deleted)


@with_cursor
def _get_datetimestamps(cur, doc_id):
    "get data from database"
    cur.execute('select source_updated, source_deleted, target_updated, target_deleted,'
                f' mirror_updated from {TABLES[3]} where id = %s;', (doc_id,))
    return cur.fetchone().values()


@with_cursor
def _get_stats_for_dirs(cur, siteid, dirids):
    "get data from database"
    cur.execute(f'select dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    dirnames = [row['dirname'] for row in cur]
    cur.execute('select dirname, docname, source_updated, target_updated, mirror_updated,'
                f' source_deleted, target_deleted from {TABLES[3]}, {TABLES[2]}'
                f' where dir_id = {TABLES[2]}.id and dir_id = any(%s);', (dirids,))
    return (dirnames,
            [(row['dirname'], row['docname'],
              _get_stats((row['source_updated'], row['source_deleted'], row['target_updated'],
                          row['target_deleted'], row['mirror_updated']))) for row in cur])


@with_cursor
def _fetch_dirmap(cur, siteid):
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select id, dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    return {row['id']: row['dirname'] for row in cur}


@with_cursor
def _fetch_site_data(cur, dirids):
    cur.execute('select docname, source_docid, source_updated, source_deleted, target_docid,'
                f' target_updated, target_deleted, mirror_updated, dir_id from {TABLES[3]}'
                ' where dir_id = any(%s);', (dirids,))
    return list(cur)


@with_cursor
def _fetch_doc_data(cur, siteid, docnames):
    data = []
    cur.execute(f'select id, currtext, previous from {TABLES[4]} where id = any(%s)',
                (list(docnames),))
    for row in cur:
        data.append({'_id': docnames[row['id']], 'current': row['currtext'],
                     'previous': row['previous']})

    cur.execute(f'select name, text from {TABLES[5]} where site_id = %s;', (siteid,))
    for row in cur:
        data.append({'_id': (row['name'],), 'template contents': row['text']})
    return data


@with_cursor
def _delete_dir_data(cur, siteid, dirids):
    "delete site from database"
    # select all site documentids (via stats)
    dirsel = 'dir_id = any(%s)'
    sql = f'select source_docid, target_docid from {TABLES[3]} where {dirsel};'
    cur.execute(sql, (dirids,))
    docids = []
    for row in cur:
        for item in (row['source_docid'], row['target_docid']):
            if item:
                docids.append(item)

    base_sql = 'delete from {} where {};'
    docsel = 'id = any(%s)'
    sql = base_sql.format(TABLES[4], docsel)
    cur.execute(sql, (docids,))

    sql = base_sql.format(TABLES[3], dirsel)
    cur.execute(sql, (dirids,))

    sel = 'site_id = %s'
    sql = base_sql.format(TABLES[5], sel)
    cur.execute(sql, (siteid,))
    sql = base_sql.format(TABLES[2], sel)
    cur.execute(sql, (siteid,))
    sql = base_sql.format(TABLES[1], sel)
    cur.execute(sql, (siteid,))

    sel = 'id = %s'
    sql = base_sql.format(TABLES[0], sel)
    cur.execute(sql, (siteid,))
