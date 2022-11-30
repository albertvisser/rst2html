"""Data processing routines for Postgres SQL version
"""
import datetime
import shutil
import functools
import pathlib
import psycopg2 as pg
import psycopg2.extras as pgx
from app_settings_postgres import user, password, Stats, WEBROOT, LOC2EXT  # , LOCS
from docs2fs import save_to
conn = pg.connect(database="rst2html", user=user, password=password)
TABLES = ('sites', 'site_settings', 'directories', 'doc_stats', 'documents', 'templates')


#
# dml-specifieke subroutines:
#
# originally I had the idea to factor out database boilerplate code using a decorator
# alternatief: hulpfunctie om de query uit te voeren
def execute_query(querystring, parameters, multi=False):
    if querystring.upper().startswith('SELECT'):
        cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    else:
        cur =  conn.cursor()
    if multi:
        cur.executemany(querystring, parameters)
    else:
        cur.execute(querystring, parameters)
    if querystring.upper().startswith('SELECT'):
        result = [x for x in cur.fetchall()]
    return result


def _is_equal(x, y):
    """special comparison used in get_all_doc_starts"""
    return x[0] == y


def _get_site_id(site_name):
    """returns the id of the site with the given name
    """
    querystring = 'select id from {} where sitename = %s;'.format(TABLES[0])
    result = execute_query(querystring, (site_name,))
    if result:
        return result[0][0]
    return None


def _get_dir_id(site_id, dirname):
    """returns the id of the site subdirectory
    """
    querystring = 'select id from {} where site_id = %s and dirname = %s;'.format(TABLES[2])
    res = execute_query(querystring, (site_id, dirname))
    if res:
        return res[0][0]
    return None


def _get_all_dir_ids(site_id):
    """returns the ids of all site subdirectories
    """
    result = None
    querystring = 'select id from {} where site_id = %s;'.format(TABLES[2])
    res = execute_query(querystring, (site_id,))
    if res:
        result =  [x[0] for x in res]
    return result


def _get_docs_in_dir(dir_id):
    """returns the names of all documents in a site subdirectory
    """
    querystring = 'select docname from {} where dir_id = %s;'.format(TABLES[3])
    result = execute_query(querystring, (dir_id,))
    if result:
        return [x[0] for x in result]
    return []


def _get_doc_ids(dir_id, docname):
    """returns the ids of all documents in a site subdirectory
    """
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = ('select id, source_docid, target_docid from {} where dir_id = %s and docname = %s;'
    result = execute_query(querystring.format(TABLES[3])), (dir_id, docname))
    if result:
        return result['id'], result['source_docid'], result['target_docid']
    return None, None, None


def _get_doc_text(doc_id):
    """returns the text of a document
    """
    querystring = 'select currtext from {} where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, (doc_id,))
    if result:
        result = result[0]
    return None, None, None  # waarom zo?


def _get_settings(site_id):
    """returns a dictionary containg the site settings
    """
    settings = {}
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select settname, settval from {} where site_id = %s'.format(TABLES[1])
    result = execute_query(querystring, (site_id,))
    for row in result:
        settings[row['settname']] = row['settval']
    return settings


def _add_doc():
    """create new document
    """
    querystring = 'insert into {} (currtext, previous) values (%s, %s) returning id'
    result = execute_query(querystring.format(TABLES[4]), ('', ''))
    if result:
        return result[0][0]  # new_doc_id = cur.fetchone()[0]
    return None


def _get_stats(docinfo):
    """retrieve site stats from database"""
    stats = []
    for value in docinfo:
        if value:
            stats.append(value)
        else:
            stats.append(datetime.datetime.min)
    return Stats(*stats)


#
# zelfde API als de andere dml-modules:
#
def clear_db():
    """remove all data from the database
    """
    for name in TABLES:
        result = execute_query('truncate table {};'.format(name)), ())


def read_db():
    """read and return all data from the database
    """
    f_result = []
    result = execute_query('select sitename, id from {} order by sitename;'.format(TABLES[0]))
    sites = [(x['sitename'], x['id']) for x in result]
    for sitename, site_id in sites:
        sitedict = {'name': sitename}
        querystring = 'select settname, settval from {} order by settname where site_id = %s;'
        result = execute_query(querystring.format(TABLES[1]), (site_id,))
        sitedict['settings'] = {x: y for x, y in cur.fetchall()}
        querystring = 'select dirname, id from {} order by dirname where site_id = %s;'
        result = execute_query(querystring.format(TABLES[2]), (site_id,))
        sitedirs = [(x['dirname'], x['id']) for x in cur.fetchall()]
        sitedict['docs'] = []
        # if we keep the site_id in the docstats table we could restrict this to one db-query
        # and filter the result set inside the loop
        # although this should also be possible with a subselect or something like that
        for dirname, dir_id in sitedirs:
            dirlist = []
            querystring = 'select * from {} order by docname where dir_id = %s;'
            result = execute_query(querystring.format(TABLES[3]), (dir_id,))
            for resultdict in cur:
                resultdict['dirname'] = dirname
                dirlist.append(resultdict)
            sitedict['docs'].append(dirlist)
        f_result.append(sitedict)
    return f_result


def list_sites():
    """list all sites registered in the database
    """
    result = []
    querystring = 'select sitename from {};'.format(TABLES[0]))
    res = execute_query(querystring)
    if res:
        result = [x[0] for x in res]
    return result


def create_new_site(site_name):
    """set up the database and file system for managing a new site
    """
    path = WEBROOT / site_name
    if _get_site_id(site_name) is not None or path.exists():
        raise FileExistsError('site_name_taken')
    querystring = 'insert into {} (sitename) values (%s) returning id;'
    result = execute_query(querystring.format(TABLES[0]), (site_name,))
    siteid = result[0][0]
    querystring = 'insert into {} (site_id, dirname) values (%s, %s)'
    result = execute_query(querystring.format(TABLES[2]), (siteid, '/'))
    # create the physical destination (mirror) so that css and images can be moved there
    path.mkdir(parents=True)


def rename_site(site_name, newname):
    """change the site's name unconditionally
    """
    siteid = _get_site_id(site_name)
    if siteid is None:  # or not path.exists():
        raise FileNotFoundError
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'update sites set name = %s where id = %s;'
    result = execute_query(querystring, (newname, siteid))
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
    # cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    # querystring = 'select count(*) from sites where sitename = %s', (site_name,))
    # if cur.fetchone()['count'] == 0:
        # conn.rollback()
        # raise FileNotFoundError
    settings = _get_settings(siteid)
    if 'css' in settings:
        if settings['css'] == '':
            settings['css'] = []
        else:
            settings['css'] = settings['css'].split(';')
    for test in ('wid', 'hig'):
        if test in settings:
            try:
                settings[test] = int(settings[test])
            except ValueError:
                pass
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

    sel = 'site_id = %s and settname = %s'
    for sett, oldsettval in oldsett.items():
        try:
            newsettval = newsett.pop(sett)
        except KeyError:
            querystring = 'delete from {} where {}'.format(TABLES[1], sel)
            result = execute_query(querystring, (siteid, sett))
            continue
        if newsettval != oldsettval:
            querystring = 'update {} set settval = %s where {}'.format(TABLES[1], sel)
            result = execute_query(querystring, (newsettval, siteid, sett))
    for sett, newsettval in newsett.items():  # left over new items
        querystring = 'insert into {} (site_id, settname, settval) values (%s, %s, %s)'
        result = execute_query(querystring.format(TABLES[1]), (siteid, sett, newsettval))
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
    querystring = 'select id, dirname from {} where site_id = %s;'
    result = execute_query(querystring.format(TABLES[2]), (siteid,))
    dirmap = {row['id']: row['dirname'] for row in result}
    dirids = [x for x in dirmap]
    if doctype in ('', 'src'):
        pass
    elif doctype == 'dest':
        querystring = 'select dir_id, target_docid from {} where dir_id = any(%s);'
        result = execute_query(querystring.format(TABLES[3]), (dirids,))
        dirids = set()
        for row in result:
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

    querystring = 'insert into {} (site_id, dirname) values (%s, %s)'
    result = execute_query(querystring, (siteid.format(TABLES[2]), directory))


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
    querystring = ('select docname, source_docid, source_deleted, target_docid, target_deleted, '
                   'mirror_updated from {} where dir_id = %s;')
    result = execute_query(querystring.format(TABLES[3]), (dirid,))
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

    return doclist  # returns all documents of the given type


def list_templates(site_name):
    """return a list of template names for this site"""
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select id, name from {} where site_id = %s;'
    result = execute_query(querystring.format(TABLES[5]), (siteid,))
    tplist = [row['name'] for row in cur]
    return tplist


def read_template(site_name, doc_name):
    """get the source of a specific template"""
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select text from {} where site_id = %s and name = %s;'
    result = execute_query(querystring.format(TABLES[5]), (siteid, doc_name))
    row = cur.fetchone()
    result = row['text']
    return result


def write_template(site_name, doc_name, data):
    """store the source for a template"""
    # TODO: backup tekst indien reeds aanwezig
    mld = ''
    siteid = _get_site_id(site_name)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select text from {} where site_id = %s and name = %s;'
    result = execute_query(querystring.format(TABLES[5]), (siteid, doc_name))
    if not cur.fetchone():
        querystring = 'insert into {} (site_id, name, text) values (%s, %s, %s);'
        result = execute_query(querystring.format(TABLES[5]), (siteid, doc_name, data))
    else:
        querystring = 'update {} set text = %s where site_id = %s and name = %s;'
        result = execute_query(querystring.format(TABLES[5]), (data, siteid, doc_name))
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
    # add into site collection
    dts = datetime.datetime.utcnow()
    querystring = ('insert into {} (dir_id, docname, source_docid, source_updated) '
                   'values (%s, %s, %s, %s);')
    result = execute_query(querystring.format(TABLES[3]), (dirid, doc_name, new_doc_id, dts))


def get_doc_contents(site_name, doc_name, doctype='', directory='', previous=False):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    result = ''
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
    querystring = 'select {} from {} where id = %s;'.format(column, TABLES[4])
    result = execute_query(querystring, (docid,))
    if result:
        result = result[0][column]
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

    querystring = 'update {} set previous = %s, currtext = %s where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, (oldtext, contents, rst_id))
    dts = datetime.datetime.utcnow()
    querystring = 'update {} set source_updated = %s where id = %s;'.format( TABLES[3])
    result = execute_query(querystring, (dts, doc_id))


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

    querystring = 'select previous from {} where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, (rst_id,))
    oldtext = result[0]['previous']
    querystring = 'update {} set previous = %s, currtext = %s where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, ('', oldtext, rst_id))
    dts = datetime.datetime.utcnow()
    querystring = 'update {} set source_updated = %s where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, (dts, doc_id))


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

    querystring = 'select source_docid from {} where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, (doc_id,))
    docid = result[0][0]
    querystring = 'delete from {} where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, (docid,))
    querystring = 'update {} set source_deleted = %s where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, (True, doc_id))


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

    dts = datetime.datetime.utcnow()
    if html_id is None:
        querystring = 'update {} set currtext = %s where id = %s;'
        result = execute_query(querystring.format(TABLES[4]), (contents, new_html_id))
        querystring = 'update {} set target_docid = %s, target_updated = %s where id = %s;'
        result = execute_query(querystring.format(TABLES[3]), (new_html_id, dts, doc_id))
    else:
        querystring = 'update {} set previous = %s, currtext = %s where id = %s;'
        result = execute_query(querystring.format(TABLES[4]), (oldtext, contents, html_id))
        querystring = 'update {} set target_updated = %s where id = %s;'
        result = execute_query(querystring.format(TABLES[3]), (dts, doc_id))



def apply_deletions_target(site_name, directory=''):
    """Copy deletion markers from source to target environment (if not already there)
    """
    if not directory:
        directory = '/'
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select id, target_docid from {} where source_deleted = %s;'.format(TABLES[3])
    result = execute_query(querystring, (True,))
    deleted = [row for row in result]
    docids = [(row['target_docid'],) for row in deleted]
    querystring = y('delete from {} where id = %s;'.format(TABLES[4])
    result = execute_query(querystring, docids, multi=True)
    deleted = [(None, 1, True, row['id']) for row in deleted]
    querystring =('update {} set source_deleted = %s, target_docid = %s, target_deleted = %s '
                  'where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, deleted, multi=True)


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

    dts = datetime.datetime.utcnow()
    querystring = 'update {} set mirror_updated = %s where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, (dts, doc_id))

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
    if not path.exists() and not sett.get('seflinks', False):
        path.touch()
    save_to(path, data)


def apply_deletions_mirror(site_name, directory=''):
    """Copy deletion markers from target to mirror environment and remove in all envs
    """
    if not directory:
        directory = '/'
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')
    dirid = _get_dir_id(siteid, directory)
    if dirid is None:
        raise FileNotFoundError('no_subdir')
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select id, docname, target_docid from {} where target_deleted = %s;'
    result = execute_query(querystring.format(TABLES[3]), (True,))
    deleted = [row for row in cur]
    # docids = [(row['target_docid'],) for row in deleted]
    # querystring = 'delete from {} where id = %s'.format(TABLES[4])
    # result = execute_query(querystring, docids, multi=True)
    delids = [(row['id'],) for row in deleted]
    querystring = 'delete from {} where id = %s;'.format(TABLES[3])
    result = execute_query(querystring, delids, multi=True)

    path = WEBROOT / site_name
    if directory != '/':
        path /= directory
    deleted = [row['docname'] for row in deleted]
    for doc_name in deleted:
        docpath = path / doc_name
        ext = LOC2EXT['dest']
        if docpath.suffix != ext:
            docpath = docpath.with_suffix(ext)
        if docpath.exists():
            docpath.unlink()


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

    querystring = 'select source_updated, target_updated, mirror_updated from {} where id = %s;'
    result = execute_query(querystring.format(TABLES[3]), (doc_id,))
    docinfo = result[0]
    return _get_stats(docinfo)


def get_all_doc_stats(site_name):
    """get statistics for all site subdirectories"""
    siteid = _get_site_id(site_name)
    if siteid is None:
        raise FileNotFoundError('no_site')

    dirids = _get_all_dir_ids(siteid)
    cur = conn.cursor(cursor_factory=pgx.RealDictCursor)
    querystring = 'select dirname from {} where site_id = %s;'.format(TABLES[2])
    result = execute_query(querystring, (siteid,))
    dirnames = [row['dirname'] for row in result]
    querystring = ('select dirname, docname, source_updated, target_updated, mirror_updated,'
                   ' source_deleted, target_deleted from {0}, {1} where dir_id = {1}.id'
                   ' and dir_id = any(%s);'.format(TABLES[3], TABLES[2]))
    result = execute_query(querystring, (dirids,))
    all_stats = [(row['dirname'],
                  row['docname'],
                  _get_stats((row['source_updated'], row['target_updated'], row['mirror_updated'])))
                 for row in result if not any((row['source_deleted'], row['target_deleted']))]

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
    querystring = 'select id, dirname from {} where site_id = %s;'.format(TABLES[2])
    result = execute_query(querystring, (siteid,))
    dirmap = {row['id']: row['dirname'] for row in result}
    dirids = [x for x in dirmap]
    sitedoc['docs'] = {x: {} for x in dirmap.values()}

    querystring = ('select docname, source_docid, source_updated, source_deleted, target_docid, '
                   'target_updated, target_deleted, mirror_updated, dir_id from {} '
                   'where dir_id = any(%s);'.format(TABLES[3]))
    result = execute_query(querystring, (dirids,))
    docstats, docnames = [], {}
    for row in result:
        doc, dir = row['docname'], dirmap[row['dir_id']]
        docitem = doc if dir == '/' else '/'.join((dir, doc))
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
    querystring = 'select id, currtext, previous from {} where id = any(%s)'.format(TABLES[4])
    result = execute_query(querystring, ([x for x in docnames],))
    for row in result:
        data.append({'_id': docnames[row['id']], 'current': row['currtext'],
                     'previous': row['previous']})

    querystring = 'select name, text from {} where site_id = %s;'.format(TABLES[5])
    result = execute_query(querystring, (siteid,))
    for row in result:
        data.append({'_id': (row['name'],), 'template contents': row['text']})



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
        sql = 'select source_docid, target_docid from {} where {};'.format(TABLES[3], dirsel)
        result = execute_query(sql, (dirids,))
        docids = []
        for row in cur:
            for item in (row['source_docid'], row['target_docid']):
                if item:
                    docids.append(item)
        base_sql = 'delete from {} where {};'
        docsel = 'id = any(%s)'
        result = execute_query(base_sql.format(TABLES[4], docsel), (docids,))
        result = execute_query(base_sql.format(TABLES[3], dirsel), (dirids,))
        sel = 'site_id = %s'
        result = execute_query(base_sql.format(TABLES[5], sel), (siteid,))
        result = execute_query(base_sql.format(TABLES[2], sel), (siteid,))
        result = execute_query(base_sql.format(TABLES[1], sel), (siteid,))
        sel = 'id = %s'
        result = execute_query(base_sql.format(TABLES[0], sel), (siteid,))

    if fs_data:
        ## if not db_data
            ## raise RuntimeError("data inconstent: mirror without database site")
        try:
            shutil.rmtree(str(path))
        except FileNotFoundError:
            pass
