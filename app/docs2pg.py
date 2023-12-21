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

#
# dml-specifieke subroutines:
#
# originally I had the idea to factor out database boilerplate code using a decorator
class DbWrapper:
    """boilerplate code for doing work on the database

    (open cursor, execute, commit, close cursor)
    """
    # maybe works now that I replaced `return` with `yield`?
    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        "wrapping the function"
        cur = conn.cursor()
        yield self.f(*args, **kwargs)
        conn.commit()
        cur.close()


def wrapit(f):
    "another stab at a decorating function"

    def wrapping(*args, **kwargs):
        "wrapping the decorated function"
        cur = conn.cursor()
        result = f(*args, **kwargs)
        conn.commit()
        cur.close()
        return result
    return wrapping
# geen idee of decoreren zin heeft, eerst maar proberen zonder


def _is_equal(x, y):
    """special comparison used in get_all_doc_starts"""
    return x[0] == y


def _get_site_id(site_name):
    """returns the id of the site with the given name
    """
    cur = conn.cursor()
    cur.execute(f'select id from {TABLES[0]} where sitename = %s;', (site_name,))
    result = cur.fetchone()
    cur.close()
    if result:
        result = result[0]
    return result


def _get_dir_id(site_id, dirname):
    """returns the id of the site subdirectory
    """
    result = None
    cur = conn.cursor()
    cur.execute(f'select id from {TABLES[2]} where site_id = %s and dirname = %s;',
                (site_id, dirname))
    result = cur.fetchone()
    cur.close()
    if result:
        result = result[0]
    return result


def _get_all_dir_ids(site_id):
    """returns the ids of all site subdirectories
    """
    result = None
    cur = conn.cursor()
    cur.execute(f'select id from {TABLES[2]} where site_id = %s;', (site_id,))
    result = [x for x in cur.fetchall()]
    cur.close()
    if result:
        result = [x[0] for x in result]
    return result


def _get_docs_in_dir(dir_id):
    """returns the names of all documents in a site subdirectory
    """
    result = []
    cur = conn.cursor()
    cur.execute(f'select docname from {TABLES[3]} where dir_id = %s;', (dir_id,))
    result = [x for x in cur.fetchall()]
    cur.close()
    if result:
        result = [x[0] for x in result]
    return result


def _get_doc_ids(dir_id, docname):
    """returns the ids of all documents in a site subdirectory
    """
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select id, source_docid, target_docid from {TABLES[3]} '
                'where dir_id = %s and docname = %s;', (dir_id, docname))
    result = cur.fetchone()
    cur.close()
    if result:
        result = result['id'], result['source_docid'], result['target_docid']
    else:
        result = None, None, None
    return result


def _get_doc_text(doc_id):
    """returns the text of a document
    """
    cur = conn.cursor()
    cur.execute(f'select currtext from {TABLES[4]} where id = %s;', (doc_id,))
    result = cur.fetchone()
    cur.close()
    result = result[0] if result else (None, None, None)  # waarom zo?
    return result


def _get_settings(site_id):
    """returns a dictionary containg the site settings
    """
    settings = {}
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select settname, settval from {TABLES[1]} where site_id = %s', (site_id,))
    for row in cur:
        settings[row['settname']] = row['settval']
    cur.close()
    return settings


def _add_doc():
    """create new document
    """
    cur = conn.cursor()
    cur.execute(f'insert into {TABLES[4]} (currtext, previous) values (%s, %s) returning id',
                ('', ''))
    new_doc_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
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


#
# zelfde API als de andere dml-modules:
#
def clear_db():
    """remove all data from the database
    """
    cur = conn.cursor()
    for name in TABLES:
        ## sql = 'truncate table {};'.format(name)
        ## cur.execute(sql)
        cur.execute(f'truncate table {name};')
    conn.commit()
    cur.close()


def read_db():
    """read and return all data from the database
    """
    result = []
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)

    cur.execute(f'select sitename, id from {TABLES[0]} order by sitename;')
    sites = [(x['sitename'], x['id']) for x in cur.fetchall()]
    for sitename, site_id in sites:

        sitedict = {'name': sitename}

        cur.execute(f'select settname, settval from {TABLES[1]} order by settname'
                    ' where site_id = %s;', (site_id,))
        sitedict['settings'] = {x: y for x, y in cur.fetchall()}

        cur.execute(f'select dirname, id from {TABLES[2]} order by dirname where site_id = %s;',
                    (site_id,))
        sitedirs = [(x['dirname'], x['id']) for x in cur.fetchall()]
        sitedict['docs'] = []
        # if we keep the site_id in the docstats table we could restrict this to one db-query
        # and filter the result set inside the loop
        # although this should also be possible with a subselect or something like that
        for dirname, dir_id in sitedirs:

            dirlist = []
            cur.execute(f'select * from {TABLES[3]} order by docname where dir_id = %s;', (dir_id,))
            for resultdict in cur:
                resultdict['dirname'] = dirname
                dirlist.append(resultdict)
            sitedict['docs'].append(dirlist)

        result.append(sitedict)

    conn.commit()
    cur.close()
    return result


def list_sites():
    """list all sites registered in the database
    """
    result = []
    cur = conn.cursor()
    cur.execute(f'select sitename from {TABLES[0]};')
    result = [x[0] for x in cur.fetchall()]
    conn.commit()
    cur.close()
    return result


def create_new_site(site_name):
    """set up the database and file system for managing a new site
    """
    path = WEBROOT / site_name
    if _get_site_id(site_name) is not None or path.exists():
        raise FileExistsError('site_name_taken')

    cur = conn.cursor()
    cur.execute(f'insert into {TABLES[0]} (sitename) values (%s) returning id;', (site_name,))
    siteid = cur.fetchone()[0]
    cur.execute(f'insert into {TABLES[2]} (site_id, dirname) values (%s, %s)', (siteid, '/'))
    conn.commit()
    cur.close()

    # create the physical destination (mirror) so that css and images can be moved there
    path.mkdir(parents=True)


def rename_site(site_name, newname):
    """change the site's name unconditionally
    """
    siteid = _get_site_id(site_name)
    if siteid is None:  # or not path.exists():
        raise FileNotFoundError

    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute('update sites set name = %s where id = %s;', (newname, siteid))
    conn.commit()
    cur.close()

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
    ## cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    ## cur.execute('select count(*) from sites where sitename = %s', (site_name,))
    ## if cur.fetchone()['count'] == 0:
        ## conn.rollback()
        ## cur.close()
        ## raise FileNotFoundError
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
    ## conn.commit()
    ## cur.close()
    return settings


def update_settings(site_name, settings_dict):
    """replace all settings at once
    """
    siteid = _get_site_id(site_name)
    oldsett = _get_settings(siteid)
    ## print('oldsett incoming:', oldsett)
    if 'css' in oldsett:
        oldsett['css'] = ';'.join([x for x in oldsett['css']])
    ## print('oldsett updated:', oldsett)
    newsett = {x: y for x, y in settings_dict.items()}
    ## print('newsett incoming:', newsett)
    if 'css' in newsett:
        newsett['css'] = ';'.join([x for x in newsett['css']])
    ## print('newsett updated:', newsett)
    cur = conn.cursor()
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
    conn.commit()
    cur.close()
    return _get_settings(siteid)


def clear_settings(site_name):  # untested - do I need/want this?
    """update settings to empty dict instead of initialized)
    """
    return update_settings(site_name, {})


def list_dirs(site_name, doctype=''):
    """list subdirs with documents of a given type in a given site

    raises FileNotFoundError if site doesn't exist
    """
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')

    ## probable inefficient approach
    ## for dir_id in dirids:
        ## docs = _get_docs_in_dir(dir_id)
        ## for docname in docs:
            ## docids = _get_doc_ids(dir_id, docname)
            ## if docids[1] is not None:
                ## diridlist.append(dir_id)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select id, dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    dirmap = {row['id']: row['dirname'] for row in cur}
    dirids = [x for x in dirmap]
    if doctype in ('', 'src'):
        pass
    elif doctype == 'dest':
        cur.execute(f'select dir_id, target_docid from {TABLES[3]} where dir_id = any(%s);',
                    (dirids,))
        dirids = set()
        for row in cur:
            if row['target_docid'] is not None:
                dirids.add(row['dir_id'])
    else:
        raise RuntimeError('wrong doctype for list_dirs')
    dirlist = []
    for id in dirids:
        test = dirmap[id]
        if test != '/':
            dirlist.append(test)
    return dirlist  # returns all dirs that have documents of the given type


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
    cur = conn.cursor()
    cur.execute(f'insert into {TABLES[2]} (site_id, dirname) values (%s, %s)',
                (siteid, directory))
    conn.commit()
    cur.close()


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
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute('select docname, source_docid, source_deleted, target_docid, target_deleted,'
                f' mirror_updated from {TABLES[3]} where dir_id = %s;', (dirid,))
    doclist = []
    for row in cur:
        # print(doctype, row['source_docid'], deleted, row['source_deleted'])
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
    conn.commit()
    cur.close()
    return doclist  # returns all documents of the given type


def list_templates(site_name):
    """return a list of template names for this site"""
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select id, name from {TABLES[5]} where site_id = %s;', (siteid,))
    tplist = [row['name'] for row in cur]
    conn.commit()
    cur.close()
    return tplist


def read_template(site_name, doc_name):
    """get the source of a specific template"""
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select text from {TABLES[5]} where site_id = %s and name = %s;', (siteid, doc_name))
    row = cur.fetchone()
    result = row['text']
    conn.commit()
    cur.close()
    return result


def write_template(site_name, doc_name, data):
    """store the source for a template"""
    # TODO: backup tekst indien reeds aanwezig
    mld = ''
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select text from {TABLES[5]} where site_id = %s and name = %s;', (siteid, doc_name))
    if not cur.fetchone():
        cur.execute(f'insert into {TABLES[5]} (site_id, name, text) values (%s, %s, %s);',
                    (siteid, doc_name, data))
    else:
        cur.execute(f'update {TABLES[5]} set text = %s where site_id = %s and name = %s;',
                    (data, siteid, doc_name))
    conn.commit()
    cur.close()
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
    cur = conn.cursor()
    # add into site collection
    dts = datetime.datetime.utcnow()
    cur.execute(f'insert into {TABLES[3]} (dir_id, docname, source_docid, source_updated)'
                ' values (%s, %s, %s, %s);', (dirid, doc_name, new_doc_id, dts))
    conn.commit()
    cur.close()


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
        raise FileNotFoundError("no_document".format(doc_name))
    if doctype in ('', 'src'):
        if src_id is None:
            ## raise FileNotFoundError("Document {} source not found".format(doc_name))
            raise FileNotFoundError("src_file_missing")
        docid = src_id
    elif doctype == 'dest':
        if dest_id is None:
            ## raise FileNotFoundError("Document {} html not found".format(doc_name))
            raise FileNotFoundError("html_file_missing")
        docid = dest_id

    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    column = 'previous' if previous else 'currtext'
    cur.execute(f'select {column} from {TABLES[4]} where id = %s;', (docid,))
    row = cur.fetchone()
    if row:
        result = row[column]
    else:
        result = f'{directory}/{doc_name} has id {docid}, but no {column} contents'
    conn.commit()
    cur.close()
    return result


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
    ## if contents == oldtext:
        ## return 'text has not changed'

    cur = conn.cursor()
    cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                (oldtext, contents, rst_id))
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set source_updated = %s where id = %s;', (dts, doc_id))
    conn.commit()
    cur.close()


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

    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select previous from {TABLES[4]} where id = %s;', (rst_id,))
    oldtext = cur.fetchone()['previous']
    cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                ('', oldtext, rst_id))
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set source_updated = %s where id = %s;', (dts, doc_id))
    conn.commit()
    cur.close()


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

    cur = conn.cursor()
    cur.execute(f'select source_docid from {TABLES[3]} where id = %s;', (doc_id,))
    docid = cur.fetchone()[0]
    cur.execute(f'delete from {TABLES[4]} where id = %s;', (docid,))
    cur.execute(f'update {TABLES[3]} set source_deleted = %s where id = %s;', (True, doc_id))
    conn.commit()
    cur.close()


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
        oldtext = _get_doc_text(html_id)
    ## if contents == oldtext:
        ## return 'text has not changed'

    cur = conn.cursor()
    dts = datetime.datetime.utcnow()
    if html_id is None:
        cur.execute(f'update {TABLES[4]} set currtext = %s where id = %s;', (contents, new_html_id))
        cur.execute(f'update {TABLES[3]} set target_docid = %s, target_updated = %s where id = %s;',
                    (new_html_id, dts, doc_id))
    else:
        cur.execute(f'update {TABLES[4]} set previous = %s, currtext = %s where id = %s;',
                    (oldtext, contents, html_id))
        cur.execute(f'update {TABLES[3]} set target_updated = %s where id = %s;', (dts, doc_id))
    conn.commit()
    cur.close()


def list_deletions_target(sitename, directory=''):
    """list pending deletions in source environment"""
    return list_deletions(get_dirlist_for_site(sitename, directory), 'source')


def apply_deletions_target(site_name, directory=''):
    """Copy deletion markers from source to target environment (if not already there)
    """
    dirlist = get_dirlist_for_site(site_name, directory)
    deleted, deleted_names = apply_deletions(dirlist, 'source')
    cur = conn.cursor()
    # regels komen terug als None, 1, True, row['id']
    # effectief gebeurt er niks met source_id
    deleted = [(x[0], x[0], x[0], x[1], x[2], x[3]) for x in deleted]
    cur.executemany(f'update {TABLES[3]} set source_docid = %s, source_updated = %s,'
                    ' source_deleted = %s, target_docid = %s, target_deleted = %s'
                    ' where id = %s;', deleted)
    conn.commit()
    cur.close()
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

    cur = conn.cursor()
    dts = datetime.datetime.utcnow()
    cur.execute(f'update {TABLES[3]} set mirror_updated = %s where id = %s;', (dts, doc_id))
    conn.commit()
    cur.close()

    path = WEBROOT / site_name
    if directory != '/':
        path /= directory
    if not path.exists():
        path.mkdir(parents=True)
    path /= doc_name
    ext = LOC2EXT['dest']
    if path.suffix != ext:
        path = path.with_suffix(ext)
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
    cur = conn.cursor()
    deleted = [(x[3],) for x in deleted]
    # regels komen terug als None, 1, True, row['id']
    # effectief gebeurt er niks met source_id
    cur.executemany(f'delete from {TABLES[3]} where id = %s;', deleted)
    conn.commit()
    cur.close()

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


def list_deletions(dirlist, stage):
    "list pending deletions for given directories in a given environment"
    deletions = []
    for directory, dirid in dirlist:
        cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
        cur.execute(f'select id, docname, target_docid from {TABLES[3]}'
                    f' where dir_id = %s and {stage}_deleted = %s;', (dirid, True))
        to_be_deleted = [row for row in cur]
        if directory == '/':
            deletions.extend([row['docname'] for row in to_be_deleted])
        else:
            deletions.extend(['/'.join((directory, row['docname'])) for row in to_be_deleted])
    return sorted(deletions)


def apply_deletions(dirlist, stage):
    "apply deletions for given directories in the given environment"
    docids, deleted, deleted_names = [], [], []
    for directory, dirid in dirlist:
        cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
        cur.execute(f'select id, docname, target_docid from {TABLES[3]}'
                    f' where dir_id = %s and {stage}_deleted = %s;', (dirid, True))
        to_delete = [row for row in cur]
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
    conn.commit()
    cur.close()
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

    cur = conn.cursor()
    cur.execute('select source_updated, source_deleted, target_updated, target_deleted,'
                f' mirror_updated from {TABLES[3]} where id = %s;', (doc_id,))
    docinfo = cur.fetchone()
    cur.close()
    return _get_stats(docinfo)


def get_all_doc_stats(site_name):
    """get statistics for all site subdirectories"""
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')

    dirids = _get_all_dir_ids(siteid)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    dirnames = [row['dirname'] for row in cur]
    cur.execute('select dirname, docname, source_updated, target_updated, mirror_updated,'
                f' source_deleted, target_deleted from {TABLES[3]}, {TABLES[2]}'
                f' where dir_id = {TABLES[2]}.id and dir_id = any(%s);', (dirids,))
    all_stats = [(row['dirname'],
                  row['docname'],
                  _get_stats((row['source_updated'], row['source_deleted'], row['target_updated'],
                              row['target_deleted'], row['mirror_updated']))) for row in cur]
    conn.commit()
    cur.close()

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

    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    cur.execute(f'select id, dirname from {TABLES[2]} where site_id = %s;', (siteid,))
    dirmap = {row['id']: row['dirname'] for row in cur}
    dirids = [x for x in dirmap]
    sitedoc['docs'] = {x: {} for x in dirmap.values()}

    cur.execute('select docname, source_docid, source_updated, source_deleted, target_docid,'
                f' target_updated, target_deleted, mirror_updated, dir_id from {TABLES[3]}'
                ' where dir_id = any(%s);', (dirids,))
    docstats, docnames = [], {}
    for row in cur:
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
        sitedoc['docs'][dir][doc] = {x: y for x, y in items}
        ## if item[0] != olddir:
            ## if olddir:
                ## sitedoc['docs'][olddir] = dirdict
            ## olddir = item[0]
            ## dirdict = {}
        ## dirdict[item[1]] = {x:y for x, y in item[2:]}
    ## if olddir:
        ## [olddir] = dirdict

    data = []
    cur.execute(f'select id, currtext, previous from {TABLES[4]} where id = any(%s)',
                ([x for x in docnames],))
    for row in cur:
        data.append({'_id': docnames[row['id']], 'current': row['currtext'],
                     'previous': row['previous']})

    cur.execute(f'select name, text from {TABLES[5]} where site_id = %s;', (siteid,))
    for row in cur:
        data.append({'_id': (row['name'],), 'template contents': row['text']})

    conn.commit()
    cur.close()
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
        ## if not fs_data
            ## raise RuntimeError("data inconstent: database without mirror site")
        dirids = _get_all_dir_ids(siteid)

        cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
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
        conn.commit()

    if fs_data:
        ## if not db_data
            ## raise RuntimeError("data inconstent: mirror without database site")
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree(str(path))
