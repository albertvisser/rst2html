import datetime
from collections import namedtuple
from pymongo import MongoClient
cl = MongoClient()
db = cl.rst2html_database
site_coll = db.site_coll
stat_keys = ('src', 'dest', 'to_mirror')
Stats = namedtuple('Stats', stat_keys)


def clear_db():
    db.drop_collection(site_coll)

def read_db():
    return site_coll.find()

def create_new_site(site_name):
    """set up the database for managing a new site
    """
    if site_coll.find_one({'name': site_name}) is not None:
        return 'Site already exists'
    new_site = {
        'name': site_name,
        'settings': {},
        'docs': {'/': {}}
        }
    try:
        site_coll.insert_one(new_site)
    except TypeError:
        site_coll.insert(new_site)
    return ''

def list_sites():
    return [doc['name'] for doc in site_coll.find() if 'name' in doc]

def _get_site_id(site_name):
    """returns the id of the document for the site with the given name
    """
    return site_coll.find_one({'name': site_name})['_id']

def rename_site(site_name, newname):
    """change the site's name unconditionally
    """
    site_id = _get_site_id(site_name)
    try:
        site_coll.update_one({'_id': site_id}, {'$set': {'name': site_name}})
    except TypeError:
        site_coll.update({'_id': site_id}, {'$set': {'name': site_name}})

def list_site_data(site_name):
    sitedoc = site_coll.find_one({'name': site_name})
    if sitedoc is None:
        raise FileNotFoundError('Site bestaat niet')
    print('\n--------------- Listing site contents -------------')
    id_list = []
    for dirname, diritem in sitedoc['docs'].items():
        for docname, docitem in diritem.items():
            for locname, locitem in docitem.items():
                if 'docid' in locitem:
                    id_list.append(locitem['docid'])
    data = site_coll.find({'_id': {'$in': sorted(id_list)}})
    return sitedoc, data

def clear_site_data(site_name):
    try:
        sitedoc = site_coll.find_one_and_delete({'name': site_name})
    except TypeError:
        sitedoc = site_coll.find_one({'name': site_name})
    if sitedoc is None:
        return
    id_list = []
    for dirname, diritem in sitedoc['docs'].items():
        for docname, docitem in diritem.items():
            for locname, locitem in docitem.items():
                if 'docid' in locitem:
                    id_list.append(locitem['docid'])
    try:
        data = site_coll.delete_many({'_id': {'$in': sorted(id_list)}})
    except TypeError:
        data = site_coll.remove({'_id': {'$in': sorted(id_list)}})

def read_settings(site_name):
    sitedoc = site_coll.find_one({'name': site_name})
    if sitedoc:
        return sitedoc['settings']

def change_setting(site_name, sett_name, value):
    """modify a site setting to the given value

    can also add a new setting
    """
    ## sitedoc = site_coll.find_one({'name': site_name})
    ## settings = sitedoc['settings']
    settings = read_settings(site_name)
    settings[sett_name] = value
    ## site_coll.update_one({'name': site_name}, {'$set': {'settings': settings}})
    result = update_settings(site_name, settings)
    return result

def update_settings(site_name, settings_dict):
    """replace all settings at once
    """
    try:
        result = site_coll.update_one({'name': site_name},
            {'$set': {'settings': settings_dict}})
    except TypeError:
        result = site_coll.update({'name': site_name},
            {'$set': {'settings': settings_dict}})
    return result

def clear_settings(site_name): # untested - do I need/want this?
    ## try:
        ## sitedoc = site_coll.find_one_and_update({'name': site_name},
            ## {'$set': {'settings': {}}})
    ## except TypeError:
        ## sitedoc = site_coll.find_one({'name': site_name})
        ## sitedoc = site_coll.update({'name': site_name}, {'$set': {'settings': {}}})
    return update_settings(site_name, {})

def _update_site_docs(site_name, site_docs):
    try:
        site_coll.update_one({'name': site_name}, {'$set': {'docs': site_docs}})
    except TypeError:
        site_coll.update({'name': site_name}, {'$set': {'docs': site_docs}})

def create_new_dir(site_name, directory):
    """make it possible to add files in a separate section

    allows for organizing the site somewhat logically
    translates physically to directories directly under the site root
    """
    sitedoc = site_coll.find_one({'name': site_name})
    if directory in sitedoc['docs']:
        raise FileExistsError
    sitedoc['docs'][directory] = {}
    ## try:
        ## site_coll.update_one({'name': site_name}, {'$set': {'docs': sitedoc['docs']}})
    ## except TypeError:
        ## site_coll.update({'name': site_name}, {'$set': {'docs': sitedoc['docs']}})
    _update_site_docs(site_name, sitedoc['docs'])

def list_dirs(site_name, doctype=''):
    """list subdirs with documents of a given type in a given site

    raises FileNotFoundError if site doesn't exist
    """
    sitedoc = site_coll.find_one({'name': site_name})
    if sitedoc is None:
        raise FileNotFoundError('Site bestaat niet')
    dirlist = []
    for dirname, doclist in sitedoc['docs'].items():
        if dirname == '/':
            continue
        found = False
        for docname, typelist in doclist.items():
            found = doctype in typelist
            if found:
                dirlist.append(dirname)
                break
        else:
            if doctype == 'src':
                dirlist.append(dirname)
        if found:
            continue
    return dirlist # returns all dirs that have documents of the given type
    ## return [x for x in sitedoc['docs'][directory]] # returns all lists regardless

def remove_dir(site_name, directory): # untested - do I need/want this?
    sitedoc = site_coll.find_one({'name': site_name})
    ## sitedoc['docs'][directory] = {}
    ## set_to = sitedoc['docs']
    ## site_coll.update_one({'name': site_name}, {'$set': {'docs': set_to}})
    sitedoc['docs'].pop('directory')
    _update_site_docs(site_name, sitedoc['docs'])

def _add_doc(doc):
    try:
        new_doc_id = site_coll.insert_one(doc).inserted_id
    except TypeError:
        new_doc_id = site_coll.insert(doc)
    return new_doc_id

def _update_doc(docid, doc):
    try:
        site_coll.replace_one({'_id': docid}, doc)
    except TypeError:
        site_coll.update({'_id': docid}, doc)

def create_new_doc(site_name, doc_name, directory=''):
    """add a new (source) document to the given directory

    raises AttributeError on missing doc_name,
           FileNotFoundError if directory doesn't exist
    """
    if not doc_name:
        raise AttributeError('No name provided')
    if not directory:
        directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    if directory not in sitedoc['docs']:
        raise FileNotFoundError('Subdirectory bestaat niet')
    if doc_name in sitedoc['docs'][directory]:
        raise FileExistsError
    new_doc = {'current': '', 'previous': ''}
    ## new_doc_id = site_coll.insert_one(new_doc).inserted_id
    new_doc_id = _add_doc(new_doc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name] = {
        'src': {'docid': new_doc_id, 'updated': dts }
        }
    ## site_coll.replace_one({'name': site_name}, sitedoc)
    _update_site_docs(site_name, sitedoc['docs'])

def list_docs(site_name, doctype='', directory=''):
    """list the documents of a given type in a given directory

    assumes site exists
    raises FileNotFoundError if directory doesn't exist
    """
    ## if doctype not in locs:
        ## return # caller should test for return value being None: 'Wrong directory tree type'
    if not directory: directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    if sitedoc is None:
        raise FileNotFoundError('Site bestaat niet')
    if directory not in sitedoc['docs']:
        raise FileNotFoundError('Subdirectory bestaat niet')
    doclist = []
    for docname, typelist in sitedoc['docs'][directory].items():
        if doctype in typelist: doclist.append(docname)
    return doclist # returns all documents of the given type


def _get_stats(docinfo):
    stats = []
    for key in stat_keys:
        if key in docinfo and 'updated' in docinfo[key]:
            stats.append(docinfo[key]['updated'])
        else:
            stats.append(datetime.datetime.min)
    return Stats(*stats)

def get_doc_stats(site_name, docname, dirname=''):
    sitedoc = site_coll.find_one({'name': site_name})
    if dirname:
        docinfo = sitedoc['docs'][dirname][docname]
    else:
        docinfo = sitedoc['docs']['/'][docname]
    return _get_stats(docinfo)

def get_all_doc_stats(site_name):
    sitedoc = site_coll.find_one({'name': site_name})
    filelist = []
    for dirname, doclist in sitedoc['docs'].items():
        docs = []
        for docname, docinfo in doclist.items():
            docs.append((docname, _get_stats(docinfo)))
        filelist.append((dirname, docs))
    return filelist

def get_doc_contents(site_name, doc_name, doctype='', directory=''):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    ## print('in get_doc_contents:', site_name, directory, doc_name, doctype)
    if not doc_name:
        raise AttributeError('No name provided')
    if not directory: directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    try:
        doc_id = sitedoc['docs'][directory][doc_name][doctype]['docid']
        #trows TypeError when doc_name doesn't exist, KeyError on nonexisting docid
    except (TypeError, KeyError) as e:
        ## print(str(e))
        raise FileNotFoundError("Document doesn't exist")
    doc_data = site_coll.find_one({'_id': doc_id})
    return doc_data['current']

def remove_doc(site_name, doc_name, directory=''): # untested - do I need/want this?
    sitedoc = site_coll.find_one({'name': site_name})
    sitedoc['docs'][directory][doc_name] = {}
    ## set_to = sitedoc['docs']
    ## site_coll.update_one({'name': site_name}, {'$set': {'docs': set_to}})
    _update_site_docs(site_name, sitedoc['docs'])

def update_rst(site_name, doc_name, contents, directory=''):
    """update a source document in the given directory

    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist (should have been created
            using create_new_doc first)
    """
    if not doc_name:
        raise AttributeError('No name provided')
    if not contents:
        raise AttributeError('No contents provided')
    if not directory: directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    if doc_name not in sitedoc['docs'][directory]:
        raise FileNotFoundError("Document doesn't exist")
    doc_id = sitedoc['docs'][directory][doc_name]['src']['docid']
    rstdoc = site_coll.find_one({'_id': doc_id})
    rstdoc['previous'] = rstdoc['current']
    rstdoc['current'] = contents
    ## site_coll.replace_one({'_id': doc_id}, rstdoc)
    _update_doc(doc_id, rstdoc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['src']['updated'] = dts
    ## site_coll.replace_one({'name': site_name}, sitedoc)
    _update_site_docs(site_name, sitedoc['docs'])

def update_html(site_name, doc_name, contents, directory=''):
    """update a converted document in the given directory

    create a new entry if it's the first-time conversion
    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('No name provided')
    if not contents:
        raise AttributeError('No contents provided')
    if not directory: directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    if doc_name not in sitedoc['docs'][directory]:
        raise FileNotFoundError("Document doesn't exist")
    if 'dest' not in sitedoc['docs'][directory][doc_name]:
        htmldoc = {'current': '', 'previous': ''}
        ## doc_id = site_coll.insert_one(htmldoc).inserted_id
        doc_id = _add_doc(htmldoc)
        sitedoc['docs'][directory][doc_name]['dest'] = {'docid': doc_id}
    else:
        doc_id = sitedoc['docs'][directory][doc_name]['dest']['docid']
        htmldoc = site_coll.find_one({'_id': doc_id})
        htmldoc['previous'] = htmldoc['current']
    htmldoc['current'] = contents
    ## site_coll.replace_one({'_id': doc_id}, htmldoc)
    _update_doc(doc_id, htmldoc)
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['dest']['updated'] = dts
    ## site_coll.replace_one({'name': site_name}, sitedoc)
    _update_site_docs(site_name, sitedoc['docs'])

def update_mirror(site_name, doc_name, directory=''):
    """administer promoting the converted document in the given directory
    to the mirror site

    create a new entry if it's the first time
    """
    if not doc_name: return 'Geen naam opgegeven'
    if not directory: directory = '/'
    sitedoc = site_coll.find_one({'name': site_name})
    dts = datetime.datetime.utcnow()
    sitedoc['docs'][directory][doc_name]['to_mirror']= {'updated': dts}
    ## site_coll.replace_one({'name': site_name}, sitedoc)
    _update_site_docs(site_name, sitedoc['docs'])
