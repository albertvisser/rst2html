"""Data processing routines for MongoDB version
"""
import datetime
import shutil
import pathlib
import contextlib
from pymongo import MongoClient
# from pymongo.collection import Collection   # needed for unittests?
from app_settings import WEBROOT, LOC2EXT, LOCS, Stats
from .docs2fs import save_to
cl = MongoClient()
db = cl.rst2html_database
site_coll = db.site_coll
# support for older pymongo versions
# try:
#     test = Collection.update_one
# except AttributeError:
#     # Collection.insert_one = Collection.insert
#     Collection.update_one = Collection.update
#     Collection.replace_one = Collection.update
#     # Collection.find_one_and_delete = Collection.remove
#     Collection.delete_many = Collection.remove

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
    # try:
    id_ = site_coll.insert_one(doc).inserted_id
    # except TypeError:
    #     id_ = site_coll.insert(doc)
    return id_


def _update_doc(docid, doc):
    """change a document in the site document
    """
    # site_coll.update({'_id': docid}, doc)
    site_coll.update_one({'_id': docid}, {'$set': doc})


def _get_stats(docinfo):
    """retrieve site stats from database"""
    stats = []
    # deleted = False
    for key in LOCS:
        if key in docinfo:
            if 'deleted' in docinfo[key]:
                # deleted = True
                # break
                stats.append('[deleted]')
            elif 'updated' in docinfo[key]:
                stats.append(docinfo[key]['updated'])
            else:
                stats.append('')
        else:
            stats.append(datetime.datetime.min)
    # if deleted:
    #    return None
    return Stats(*stats)


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
    path = WEBROOT / site_name
    if _get_site_doc(site_name) is not None or path.exists():
        raise FileExistsError('site_name_taken')

    # create sitedoc
    new_site = {'name': site_name, 'settings': {}, 'docs': {'/': {}, 'templates': {}}}
    # try:
    site_coll.insert_one(new_site)
    # except TypeError:
    #     site_coll.insert(new_site)

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
    return site_coll.update_one({'name': site_name}, {'$set': {'settings': settings_dict}})


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
            if doctype in ('', 'src'):
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
    doctype = doctype or LOCS[0]
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
            elif not deleted:
                doclist.append(docname)
    return doclist  # returns all documents of the given type


def list_templates(site_name):
    """return a list of template names for this site"""
    sitedoc = _get_site_doc(site_name)
    if 'templates' not in sitedoc:
        return []
    return sorted([x for x in sitedoc['templates']])


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
    sitedoc.setdefault('templates', {})
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


def get_doc_contents(site_name, doc_name, doctype='', directory='', previous=False):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('no_name')
    doctype = doctype or LOCS[0]
    if not directory:
        directory = '/'
    doc_name = pathlib.Path(doc_name).stem
    sitedoc = _get_site_doc(site_name)
    try:
        doc_id = sitedoc['docs'][directory][doc_name][doctype]['docid']
        # throws TypeError when doc_name doesn't exist, KeyError on nonexisting docid
    except (TypeError, KeyError) as exc:
        ## raise FileNotFoundError("Document {} doesn't exist".format(doc_name))
        raise FileNotFoundError("no_document".format(doc_name)) from exc
    doc_data = site_coll.find({'_id': doc_id})[0]
    if previous:
        return doc_data['previous']
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
    if directory not in sitedoc['docs']:
        raise FileNotFoundError("no_subdir")
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
    sitedoc = _get_site_doc(sitename)
    if directory not in sitedoc['docs']:
        raise FileNotFoundError("no_subdir")
    if doc_name not in sitedoc['docs'][directory]:
        raise FileNotFoundError("no_document")
    doc_id = sitedoc['docs'][directory][doc_name]['src']['docid']
    rstdoc = site_coll.find({'_id': doc_id})[0]

    rstdoc['current'] = rstdoc['previous']
    rstdoc['previous'] = ''
    _update_doc(doc_id, rstdoc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['src']['updated'] = dts
    _update_site_doc(sitename, sitedoc['docs'])


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
    sitedoc = _get_site_doc(site_name)
    if doc_name not in sitedoc['docs'][directory]:
        raise FileNotFoundError("no_document")
    if dry_run:
        return
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


def list_deletions_target(site_name, directory=''):
    """list pending deletions in source environment"""
    if not directory:
        directory = '/'
    directories = ['/'] + list_dirs(site_name, 'src') if directory == '*' else [directory]
    sitedoc = _get_site_doc(site_name)
    deletions = []
    for directory in directories:
        for doc_name in sitedoc['docs'][directory]:
            if sitedoc['docs'][directory][doc_name]['src'].get('deleted', False):
                if directory != '/':
                    doc_name = f'{directory}/{doc_name}'
                deletions.append(doc_name)
    return deletions


def apply_deletions_target(site_name, directory=''):
    """Copy deletion markers from source to target environment (if not already there)
    """
    if not directory:
        directory = '/'
    directories = ['/'] + list_dirs(site_name, 'src') if directory == '*' else [directory]
    sitedoc = _get_site_doc(site_name)
    changed = False
    deleted = []
    for directory in directories:
        for doc_name in sitedoc['docs'][directory]:
            # print('checking deletion mark for', doc_name)
            # print(sitedoc['docs'][directory][doc_name])
            if sitedoc['docs'][directory][doc_name]['src'].get('deleted', False):
                # sitedoc['docs'][directory][doc_name]['src']['deleted'] = False
                sitedoc['docs'][directory][doc_name].pop('src')
                if 'dest' not in sitedoc['docs'][directory][doc_name]:
                    htmldoc = {'current': '', 'previous': ''}
                    doc_id = _add_doc(htmldoc)
                    sitedoc['docs'][directory][doc_name]['dest'] = {'docid': doc_id}
                sitedoc['docs'][directory][doc_name]['dest']['deleted'] = True
                if directory != '/':
                    doc_name = f'{directory}/{doc_name}'
                deleted.append(doc_name)
                changed = True
    if changed:
        _update_site_doc(site_name, sitedoc['docs'])
    return deleted


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
    if dry_run:
        return
    if not directory:
        directory = '/'
    sitedoc = _get_site_doc(site_name)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['mirror'] = {'updated': dts}
    _update_site_doc(site_name, sitedoc['docs'])

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


def list_deletions_mirror(site_name, directory=''):
    """list pending deletions in target environment"""
    if not directory:
        directory = '/'
    directories = ['/'] + list_dirs(site_name, 'dest') if directory == '*' else [directory]
    sitedoc = _get_site_doc(site_name)
    deletions = []
    for directory in directories:
        for doc_name in sitedoc['docs'][directory]:
            if sitedoc['docs'][directory][doc_name].get('dest', {}).get('deleted', False):
                if directory != '/':
                    doc_name = f'{directory}/{doc_name}'
                deletions.append(doc_name)
    return deletions


def apply_deletions_mirror(site_name, directory=''):
    """Copy deletion markers from target to mirror environment and remove in all envs
    """
    if not directory:
        directory = '/'
    directories = ['/'] + list_dirs(site_name, 'dest') if directory == '*' else [directory]
    sitedoc = _get_site_doc(site_name)
    deleted = []
    for directory in directories:
        for doc_name in sitedoc['docs'][directory]:
            destdict = sitedoc['docs'][directory][doc_name].get('dest', {})
            if destdict.get('deleted', False):
                deleted.append((directory, doc_name))
    if not deleted:
        return []
    for directory, doc_name in deleted:
        sitedoc['docs'][directory].pop(doc_name)
    _update_site_doc(site_name, sitedoc['docs'])

    path = WEBROOT / site_name
    deletions = []
    for directory, doc_name in deleted:
        docpath = path / doc_name if directory == '/' else path / directory / doc_name
        ext = LOC2EXT['dest']
        if docpath.suffix != ext:
            docpath = docpath.with_suffix(ext)
        if docpath.exists():
            docpath.unlink()
        # dir_name = directory.replace('/', '')
        # deletions.append(f'{dir_name}/{doc_name}')
        if directory != '/':
            doc_name = f'{directory}/{doc_name}'
        deletions.append(doc_name)
    return deletions


def get_doc_stats(site_name, docname, dirname=''):
    """get statistics for a document in a site subdirectory"""
    docname = pathlib.Path(docname).stem
    sitedoc = _get_site_doc(site_name)
    docinfo = sitedoc['docs'][dirname][docname] if dirname else sitedoc['docs']['/'][docname]
    return _get_stats(docinfo)


def get_all_doc_stats(site_name):
    """get statistics for all site subdirectories"""
    sitedoc = _get_site_doc(site_name)
    filelist = []
    for dirname, doclist in sitedoc['docs'].items():
        docs = []
        for docname, docinfo in doclist.items():
            test = _get_stats(docinfo)
            if test:
                docs.append((docname, test))
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
                # if 'docid' in locitem:
                if 'docid' in locitem and 'deleted' not in locitem:
                    id_list.append(locitem['docid'])
                    id_dict[locitem['docid']] = (docname, locname, dirname)
    data = []
    for item in site_coll.find({'_id': {'$in': id_list}}):
        docname, locname, dirname = id_dict[item['_id']]
        if dirname != '/':
            docname = f'{dirname}/{docname}'
        item['_id'] = (docname, locname)
        data.append(item)
    return sitedoc, sorted(data, key=lambda x: x['_id'])


def clear_site_data(site_name):
    """remove site from database, also delete mirror site files from file system
    """
    path = WEBROOT / site_name
    # try:
    sitedoc = site_coll.find_one_and_delete({'name': site_name})
    # except TypeError:
    #     sitedoc = site_coll.find_one({'name': site_name})
    #     site_coll.remove_one({'name': site_name})

    ## if sitedoc is None:
        ## if path.exists():
            ## raise RuntimeError("data inconstent: mirror without database site")
        ## else:
            ## return
    ## else:
        ## if not path.exists():
            ## raise RuntimeError("data inconstent: database without mirror site")

    if sitedoc:  # zou betekenen dat find_one_and_delete misgaat
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

    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(str(path))
