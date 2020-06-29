"""Data processing routines for MongoDB version
"""
import datetime
import shutil
import pathlib
from pymongo import MongoClient
from pymongo.collection import Collection
from app_settings import DB_WEBROOT, LOC2EXT, LOCS, Stats
from docs2fs import save_to
cl = MongoClient()
db = cl.rst2html_database
site_coll = db.site_coll
# support for older pymongo versions
try:
    test = Collection.update_one
except AttributeError:
    ## Collection.insert_one = Collection.insert
    Collection.update_one = Collection.update
    Collection.replace_one = Collection.update
    ## # Collection.find_one_and_delete = Collection.remove
    Collection.delete_many = Collection.remove


#
# dml-specifieke subroutines:
#
def _get_site_id(site_name):
    """returns the id of the document for the site with the given name
    """
    return site_coll.find_one({'name': site_name})['_id']


def _get_site_doc(site_name):
    """returns the stats document for the site with the given name
    """
    return site_coll.find_one({'name': site_name})


def _update_site_doc(site_name, site_docs):
    """(re)save the document containing the site data
    """
    site_coll.update_one({'name': site_name}, {'$set': {'docs': site_docs}})


def _add_doc(doc):
    """create new document in the site document
    """
    try:
        id_ = site_coll.insert_one(doc).inserted_id
    except TypeError:
        id_ = site_coll.insert(doc)
    return id_


def _update_doc(docid, doc):
    """change a document in the site document
    """
    site_coll.update({'_id': docid}, doc)


def _get_stats(docinfo):
    """retrieve site stats from database"""
    stats = []
    for key in LOCS:
        if key in docinfo and 'updated' in docinfo[key]:
            stats.append(docinfo[key]['updated'])
        else:
            stats.append(datetime.datetime.min)
    return Stats(*stats)


## def _add_sitecoll_doc(data):
    ## site_coll.insert_one(data)


#
# zelfde API als de andere dml-modules:
#
def clear_db():
    """remove all data from the database
    """
    db.drop_collection(site_coll)


def read_db():
    """read and return all data from the database
    """
    return site_coll.find()


def list_sites():
    """list all sites registered in the database
    """
    return [doc['name'] for doc in site_coll.find() if 'name' in doc]


def create_new_site(site_name):
    """set up the database and file system for managing a new site
    """
    path = DB_WEBROOT / site_name
    if _get_site_doc(site_name) is not None or path.exists():
        raise FileExistsError('site_name_taken')

    # create sitedoc
    new_site = {'name': site_name, 'settings': {}, 'docs': {'/': {}, 'templates': {}}}
    try:
        site_coll.insert_one(new_site)
    except TypeError:
        site_coll.insert(new_site)

    # create the physical destination (mirror) so that css and images can be moved there
    path.mkdir(parents=True)


def rename_site(site_name, newname):
    """change the site's name unconditionally
    """
    site_id = _get_site_id(site_name)
    site_coll.update_one({'_id': site_id}, {'$set': {'name': newname}})


def read_settings(site_name):
    """returns a dictionary containg the site settings
    """
    sitedoc = _get_site_doc(site_name)
    if sitedoc is None:
        raise FileNotFoundError
    return sitedoc['settings']


def update_settings(site_name, settings_dict):
    """replace all settings at once
    """
    return site_coll.update({'name': site_name}, {'$set': {'settings': settings_dict}})


def clear_settings(site_name):  # untested - do I need/want this?
    """update settings to empty dict instead of initialized)
    """
    return update_settings(site_name, {})


def list_dirs(site_name, doctype=''):
    """list subdirs with documents of a given type in a given site

    raises FileNotFoundError if site doesn't exist
    """
    sitedoc = _get_site_doc(site_name)
    if sitedoc is None:
        raise FileNotFoundError('no_site')
    dirlist = []
    for dirname, doclist in sitedoc['docs'].items():
        if dirname == '/':
            continue
        found = False
        # for docname, typelist in doclist.items():
        for typelist in doclist.values():
            found = doctype in typelist
            if found:
                dirlist.append(dirname)
                break
        else:
            if doctype == 'src':
                dirlist.append(dirname)
        if found:
            continue
    return dirlist  # returns all dirs that have documents of the given type


def create_new_dir(site_name, directory):
    """make it possible to add files in a separate section

    allows for organizing the site somewhat logically
    translates physically to directories directly under the site root
    """
    sitedoc = _get_site_doc(site_name)
    if directory in sitedoc['docs']:
        raise FileExistsError
    sitedoc['docs'][directory] = {}
    _update_site_doc(site_name, sitedoc['docs'])


def remove_dir(site_name, directory):  # untested - do I need/want this?
    """remove site directory and all documents in it
    """
    sitedoc = _get_site_doc(site_name)
    sitedoc['docs'].pop(directory)
    _update_site_doc(site_name, sitedoc['docs'])


def list_docs(site_name, doctype='', directory='', deleted=False):
    """list the documents of a given type in a given directory

    raises FileNotFoundError if site or directory doesn't exist
    """
    if not directory:
        directory = '/'
    sitedoc = _get_site_doc(site_name)
    if sitedoc is None:
        raise FileNotFoundError('no_site')
    if directory not in sitedoc['docs']:
        raise FileNotFoundError('no_subdir')
    doclist = []
    for docname, typelist in sitedoc['docs'][directory].items():
        if doctype in typelist:
            if 'deleted' in sitedoc['docs'][directory][docname][doctype]:
                test = sitedoc['docs'][directory][docname][doctype]['deleted']
                if deleted and test:
                    doclist.append(docname)
            else:
                if not deleted:
                    doclist.append(docname)
    return doclist  # returns all documents of the given type


def list_templates(site_name):
    """return a list of template names for this site"""
    sitedoc = _get_site_doc(site_name)
    if 'templates' not in sitedoc:
        return []
    return sorted([x for x in sitedoc['templates'].keys()])


def read_template(site_name, doc_name):
    """get the source of a specific template"""
    sitedoc = _get_site_doc(site_name)
    if doc_name in sitedoc['templates']:
        return sitedoc['templates'][doc_name]
    return ''


def write_template(site_name, doc_name, data):
    """store the source for a template
    """
    # TODO: backup tekst indien reeds aanwezig
    sitedoc = _get_site_doc(site_name)
    sitedoc['templates'][doc_name] = data
    site_coll.update_one({'name': site_name}, {'$set': {'templates': sitedoc['templates']}})
    return ''


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
    sitedoc = _get_site_doc(site_name)
    if directory not in sitedoc['docs']:
        raise FileNotFoundError('no_subdir')
    if doc_name in sitedoc['docs'][directory]:
        raise FileExistsError
    new_doc = {'current': '', 'previous': ''}
    new_doc_id = _add_doc(new_doc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name] = {'src': {'docid': new_doc_id, 'updated': dts}}
    _update_site_doc(site_name, sitedoc['docs'])


def get_doc_contents(site_name, doc_name, doctype='', directory=''):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem
    sitedoc = _get_site_doc(site_name)
    try:
        doc_id = sitedoc['docs'][directory][doc_name][doctype]['docid']
        # throws TypeError when doc_name doesn't exist, KeyError on nonexisting docid
    except (TypeError, KeyError):
        ## raise FileNotFoundError("Document {} doesn't exist".format(doc_name))
        raise FileNotFoundError("no_document".format(doc_name))
    doc_data = site_coll.find({'_id': doc_id})[0]
    return doc_data['current']


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
    sitedoc = _get_site_doc(site_name)
    if doc_name not in sitedoc['docs'][directory]:
        ## raise FileNotFoundError("Document doesn't exist")
        raise FileNotFoundError("no_document")
    doc_id = sitedoc['docs'][directory][doc_name]['src']['docid']
    rstdoc = site_coll.find({'_id': doc_id})[0]
    ## if contents == rstdoc['current']:
        ## return 'text has not changed'

    rstdoc['previous'] = rstdoc['current']
    rstdoc['current'] = contents
    _update_doc(doc_id, rstdoc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['src']['updated'] = dts
    _update_site_doc(site_name, sitedoc['docs'])


def mark_src_deleted(site_name, doc_name, directory=''):
    """mark a source document in the given directory as deleted
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem
    sitedoc = _get_site_doc(site_name)
    if doc_name not in sitedoc['docs'][directory]:
        ## raise FileNotFoundError("Document doesn't exist")
        raise FileNotFoundError("no_document")
    sitedoc['docs'][directory][doc_name]['src']['deleted'] = True
    _update_site_doc(site_name, sitedoc['docs'])


def update_html(site_name, doc_name, contents, directory=''):
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
    sitedoc = _get_site_doc(site_name)
    if doc_name not in sitedoc['docs'][directory]:
        raise FileNotFoundError("no_document")
    if 'dest' not in sitedoc['docs'][directory][doc_name]:
        htmldoc = {'current': '', 'previous': ''}
        doc_id = _add_doc(htmldoc)
        sitedoc['docs'][directory][doc_name]['dest'] = {'docid': doc_id}
    else:
        doc_id = sitedoc['docs'][directory][doc_name]['dest']['docid']
        htmldoc = site_coll.find({'_id': doc_id})[0]
        htmldoc['previous'] = htmldoc['current']
    htmldoc['current'] = contents
    _update_doc(doc_id, htmldoc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['dest']['updated'] = dts
    _update_site_doc(site_name, sitedoc['docs'])


def apply_deletions_target(site_name, directory=''):
    """Copy deletion markers from source to target environment (if not already there)
    """
    if not directory:
        directory = '/'
    sitedoc = _get_site_doc(site_name)
    for doc_name in sitedoc['docs'][directory]:
        # print('checking deletion mark for', doc_name)
        # print(sitedoc['docs'][directory][doc_name])
        if 'deleted' in sitedoc['docs'][directory][doc_name]['src']:
            sitedoc['docs'][directory][doc_name]['src']['deleted'] = False
            if 'dest' not in sitedoc['docs'][directory][doc_name]:
                htmldoc = {'current': '', 'previous': ''}
                doc_id = _add_doc(htmldoc)
                sitedoc['docs'][directory][doc_name]['dest'] = {'docid': doc_id}
            sitedoc['docs'][directory][doc_name]['dest']['deleted'] = True
    _update_site_doc(site_name, sitedoc['docs'])


def update_mirror(site_name, doc_name, data, directory=''):
    """administer promoting the converted document in the given directory
    to the mirror site
    some additions are only saved in the mirror html hence the data argument
    otherwise we could get it from the target location

    raise AttributeError if no name provided
    create a new entry if it's the first time
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not directory:
        directory = '/'
    sitedoc = _get_site_doc(site_name)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['mirror'] = {'updated': dts}
    _update_site_doc(site_name, sitedoc['docs'])

    path = DB_WEBROOT / site_name
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
    save_to(path, data, sett)


def apply_deletions_mirror(site_name, directory=''):
    """Copy deletion markers from target to mirror environment and remove in all envs
    """
    if not directory:
        directory = '/'
    sitedoc = _get_site_doc(site_name)
    deleted = []
    for doc_name in sitedoc['docs'][directory]:
        # if 'deleted' in sitedoc['docs'][directory][doc_name]['dest']:
        if 'deleted' in sitedoc['docs'][directory][doc_name].get('dest', {}):
            deleted.append(doc_name)
    for doc_name in deleted:
        sitedoc['docs'][directory].pop(doc_name)
    _update_site_doc(site_name, sitedoc['docs'])

    path = DB_WEBROOT / site_name
    if directory != '/':
        path /= directory
    for doc_name in deleted:
        path /= doc_name
        ext = LOC2EXT['dest']
        if path.suffix != ext:
            path = path.with_suffix(ext)
        if path.exists():
            path.unlink()


def get_doc_stats(site_name, docname, dirname=''):
    """get statistics for all documents in a site subdirectory"""
    sitedoc = _get_site_doc(site_name)
    if dirname:
        docinfo = sitedoc['docs'][dirname][docname]
    else:
        docinfo = sitedoc['docs']['/'][docname]
    return _get_stats(docinfo)


def get_all_doc_stats(site_name):
    """get statistics for all site subdirectories"""
    sitedoc = _get_site_doc(site_name)
    filelist = []
    for dirname, doclist in sitedoc['docs'].items():
        docs = []
        for docname, docinfo in doclist.items():
            docs.append((docname, _get_stats(docinfo)))
        filelist.append((dirname, docs))
    return filelist


# deze worden niet gebruikt door de applicatie, maar wel door de testroutines
def list_site_data(site_name):
    """list all data on the site in a readable form

    for testing purposes and such
    """
    sitedoc = _get_site_doc(site_name)
    if sitedoc is None:
        raise FileNotFoundError('no_site')
    id_list, id_dict = [], {}
    for dirname, diritem in sitedoc['docs'].items():
        for docname, docitem in diritem.items():
            for locname, locitem in docitem.items():
                if 'docid' in locitem:
                    id_list.append(locitem['docid'])
                    id_dict[locitem['docid']] = (docname, locname, dirname)
    data = []
    for item in site_coll.find({'_id': {'$in': id_list}}):
        docname, locname, dirname = id_dict[item['_id']]
        if dirname != '/':
            docname = '/'.join((dirname, docname))
        item['_id'] = (docname, locname)
        data.append(item)
    return sitedoc, sorted(data, key=lambda x: x['_id'])


def clear_site_data(site_name):
    """remove site from database, also delete mirror site files from file system
    """
    path = DB_WEBROOT / site_name
    try:
        sitedoc = site_coll.find_one_and_delete({'name': site_name})
    except TypeError:
        sitedoc = site_coll.find_one({'name': site_name})
        site_coll.remove({'name': site_name})

    ## if sitedoc is None:
        ## if path.exists():
            ## raise RuntimeError("data inconstent: mirror without database site")
        ## else:
            ## return
    ## else:
        ## if not path.exists():
            ## raise RuntimeError("data inconstent: database without mirror site")

    if sitedoc:
        id_list = []
        # for dirname, diritem in sitedoc['docs'].items():
        for diritem in sitedoc['docs'].values():
            # for docname, docitem in diritem.items():
            for docitem in diritem.values():
                # for locname, locitem in docitem.items():
                for locitem in docitem.values():
                    if 'docid' in locitem:
                        id_list.append(locitem['docid'])
        ## try:
        site_coll.delete_many({'_id': {'$in': sorted(id_list)}})
        ## except TypeError:
            ## site_coll.remove({'_id': {'$in': sorted(id_list)}})

    try:
        shutil.rmtree(str(path))
    except FileNotFoundError:
        pass
