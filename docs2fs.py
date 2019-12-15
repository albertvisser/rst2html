"""Data processing routines for plain file system version
"""
# import datetime
from collections import defaultdict
import datetime
import shutil
import pathlib
import yaml
from app_settings import FS_WEBROOT, DB_WEBROOT, LOC2EXT, LOCS, Stats
HERE = pathlib.Path(__file__).parent
SETTFILE = 'settings.yml'
DELMARK = '.deleted'
SRC_LOC, DEST_LOC = '.source', '.target'

# zelfde API als docs2mongo plus:


def _locify(path, loc=''):
    """append the location to save the file to to the path
    """
    if not loc or loc == LOCS[0]:
        path /= SRC_LOC
    elif loc == LOCS[1]:
        path /= DEST_LOC
    elif loc != LOCS[2]:
        raise ValueError('invalid type')
    return path


def read_data(fname):   # to be used for actual file system data
    """reads data from file <fname>

    on success: returns empty message and data as a string
    on failure: returns error message and empty string for data
    """
    sitename = fname.relative_to(FS_WEBROOT).parts[0]
    if read_settings(sitename).get('seflinks', False):
        if fname.suffix == '.html' and fname.stem != 'index':
            fname = fname.with_suffix('') / 'index.html'
    #
    mld = data = ''
    try:
        with fname.open(encoding='utf-8') as f_in:
            data = ''.join(f_in.readlines())
    except UnicodeDecodeError:
        try:
            with fname.open(encoding='iso-8859-1') as f_in:
                data = ''.join(f_in.readlines())
        except IOError as e:
            mld = str(e)
    except IOError as e:
        mld = str(e)
    data = data.replace('\r\n', '\n')
    return mld, data


def save_to(fullname, data, settings=None):  # to be used for actual file system data
    """backup file, then write data to file

    gebruikt copyfile i.v.m. permissies (user = webserver ipv end-user)
    """
    if settings:
        sitename = fullname.relative_to(DB_WEBROOT).parts[0]
    else:
        sitename = fullname.relative_to(FS_WEBROOT).parts[0]
        settings = read_settings(sitename)
    if settings.get('seflinks', False):
        if fullname.suffix == '.html' and fullname.stem != 'index':
            new_fname = fullname.with_suffix('')
            if new_fname.exists() and not new_fname.is_dir():
                new_fname.replace(new_fname.with_suffix('.bak'))
            if not new_fname.exists():
                new_fname.mkdir()
            fullname = new_fname / 'index.html'
    #
    mld = ''
    if fullname.exists():
        shutil.copyfile(str(fullname), str(fullname.with_suffix(fullname.suffix + '.bak')))
    with fullname.open("w", encoding='utf-8') as f_out:
        try:
            f_out.write(data)
        except OSError as err:
            mld = str(err)
    return mld

## def clear_db(): pass # alle directories onder SITEROOT met source/target erin weggooien?
## def read_db(): pass
save_config_data = yaml.dump
load_config_data = yaml.safe_load  # let's be paranoid
#    notok = False
#    try:
#        conf = load_config_data(text)
#    except ParserError:
ParserError = yaml.parser.ParserError

def list_sites():
    """list all directories under FS_WEBROOT having subdirectories source en target
    (and a settings file)
    """
    ## """build list of options containing all settings files in current directory"""
    ## return [x.stem.replace('settings_', '') for x in HERE.glob('settings*.yml')]
    ## return [x.name for x in HERE.glob('settings*.yml')]
    path = FS_WEBROOT
    sitelist = []
    for item in path.iterdir():
        if not item.is_dir():
            continue
        test1 = item / SRC_LOC
        test2 = item / DEST_LOC
        test3 = item / SETTFILE
        if all((test1.exists(), test1.is_dir(), test2.exists(), test2.is_dir(),
                test3.exists(), test3.is_file())):
            sitelist.append(item.stem)
    return sitelist


def create_new_site(sitename):
    """aanmaken nieuwe directory onder FS_WEBROOT plus subdirectories source en target
    alsmede initieel settings file
    """
    path = FS_WEBROOT / sitename
    try:
        path.mkdir()
    except FileExistsError:
        raise FileExistsError('site_name_taken')
    src = path / SRC_LOC
    src.mkdir()
    targ = path / DEST_LOC
    targ.mkdir()
    path = path / SETTFILE
    path.touch()


def rename_site(sitename, newname):
    """change the site's name unconditionally
    """
    raise NotImplementedError


def read_settings(sitename):
    "lezen settings file"
    conf = None
    path = FS_WEBROOT / sitename / SETTFILE
    try:
        with path.open(encoding='utf-8') as _in:
            conf = load_config_data(_in)
    except FileNotFoundError:
        raise
    if conf is None:
        conf = {}
    return conf
    ## return 'reading settings from {}'.format(path)


def update_settings(sitename, conf):
    "update (save) settings file"
    path = FS_WEBROOT / sitename / SETTFILE
    if path.exists():
        shutil.copyfile(str(path), str(path.with_suffix(path.suffix + '.bak')))
    with path.open('w', encoding='utf-8') as _out:
        save_config_data(conf, _out, default_flow_style=False)
    return 'ok'


def clear_settings(sitename):
    """update settings to empty dict instead of initialized)
    """
    raise NotImplementedError


def list_dirs(sitename, loc=''):
    "list subdirs for type"
    test = FS_WEBROOT / sitename
    if not test.exists():
        raise FileNotFoundError('no_site')
    path = _locify(test, loc)
    ## return [str(f.relative_to(path)) for f in path.iterdir() if f.is_dir()]
    if loc == 'src' and read_settings(sitename).get('seflinks', False):
        lines = [f.stem for f in path.iterdir() if f.is_dir() and (f / '.files').exists()]
    else:
        lines = [f.stem for f in path.iterdir() if f.is_dir()]
    return lines


def create_new_dir(sitename, dirname):
    "create site subdirectory in source tree"
    path = FS_WEBROOT / sitename / SRC_LOC / dirname
    path.mkdir()    # can raise FileExistsError - is caught in caller
    (path / '.files').touch()   # mark as site subdirectory


def remove_dir(sitename, directory):
    """remove site directory and all documents in it
    """
    raise NotImplementedError


def list_docs(sitename, loc, directory='', deleted=False):
    """list the documents of a given type in a given directory

    if requested, list files marked as deleted instead
    raises FileNotFoundError if site or directory doesn't exist
    """
    path = FS_WEBROOT / sitename
    if not path.exists():
        raise FileNotFoundError('no_site')
    path = _locify(path, loc)
    if directory:
        path /= directory
        if not path.exists():
            ## raise FileNotFoundError('no_subdir')
            return []
    testsuffix = DELMARK if deleted else LOC2EXT[loc]
    if loc == 'dest' and read_settings(sitename).get('seflinks', False):
        lines = [f.stem for f in path.iterdir()
                 if f.is_dir() and (f / ('index' + testsuffix)).exists()]
        if not directory and (FS_WEBROOT / sitename / 'index.html').exists():
            lines.append('index')
    else:
        lines = [f.stem for f in path.iterdir() if f.is_file() and f.suffix == testsuffix]
    return lines


def list_templates(sitename):
    """return a list of template names for this site"""
    path = FS_WEBROOT / sitename / '.templates'
    if not path.exists():
        return []
    return sorted([f.name for f in path.iterdir() if f.suffix == '.tpl'])


def read_template(sitename, docname):
    """get the source of a specific template"""
    # moet eigenlijk met read_data maar dan moet ik die eerst geschikt maken
    with (FS_WEBROOT / sitename / '.templates' / docname).open() as f_in:
        data = ''.join(f_in.readlines()).replace('\r\n', '\n')
    return data


def write_template(sitename, fnaam, data):
    """store the source for a template"""
    # moet eigenlijk met save_to maar dan moet ik die eerst geschikt maken
    fullname = FS_WEBROOT / sitename / '.templates' / fnaam
    if fullname.exists():
        shutil.copyfile(str(fullname), str(fullname.with_suffix(fullname.suffix + '.bak')))
    mld = ''
    with fullname.open("w", encoding='utf-8') as f_out:
        try:
            f_out.write(data)
        except OSError as err:
            mld = str(err)
    return mld


def create_new_doc(sitename, docname, directory=''):
    """add a new (source) document to the given directory

    assumes site exists
    raises AttributeError on missing doc_name,
           FileNotFoundError if directory doesn't exist
    """
    if not docname:
        raise AttributeError('no_name')
    path = _locify(FS_WEBROOT / sitename, 'src')
    if directory:
        path = path / directory
    if not path.exists():
        raise FileNotFoundError('no_subdir')
    path = path / docname
    if path.suffix != '.rst':
        path = path.with_suffix('.rst')
    path.touch(exist_ok=False)        # FileExistsError will be handled in the caller


def get_doc_contents(sitename, docname, doctype='', directory=''):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not docname:
        raise AttributeError('No name provided')
    path = FS_WEBROOT / sitename
    path = _locify(path, doctype)
    if directory:
        path /= directory
    path = path / docname
    ext = LOC2EXT[doctype]
    if path.suffix != ext:
        path = path.with_suffix(ext)
    with open('get_doc_contents', 'w') as f:
        print('in get_doc_contents - path =', path, file=f)
    mld, doc_data = read_data(path)
    with open('get_doc_contents', 'a') as f:
        print('in get_doc_contents - mld =', mld, file=f)
    if mld:
        raise FileNotFoundError(mld)
    return doc_data


def update_rst(sitename, doc_name, contents, directory=''):
    """update a source document in the given directory

    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist (should have been created
            using create_new_doc first)
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not contents:
        raise AttributeError('no_contents')
    if doc_name not in list_docs(sitename, 'src', directory):
        ## raise FileNotFoundError("Document {} doesn't exist".format(doc_name))
        raise FileNotFoundError("no_document")  # .format(doc_name))
    path = FS_WEBROOT / sitename / SRC_LOC
    if directory:
        path /= directory
    path = path / doc_name
    ext = LOC2EXT['src']
    if path.suffix != ext:
        path = path.with_suffix(ext)
    save_to(path, contents)


def mark_src_deleted(sitename, doc_name, directory=''):
    """mark a source document in the given directory as deleted
    """
    if not doc_name:
        raise AttributeError('no_name')
    if doc_name not in list_docs(sitename, 'src', directory):
        ## raise FileNotFoundError("Document {} doesn't exist".format(doc_name))
        raise FileNotFoundError("no_document")  # .format(doc_name))
    path = FS_WEBROOT / sitename / SRC_LOC
    if directory:
        path /= directory
    path = path / doc_name
    ext = LOC2EXT['src']
    if path.suffix != ext:
        path = path.with_suffix(ext)
    path.rename(path.with_suffix(DELMARK))


def update_html(sitename, doc_name, contents, directory=''):
    """update a converted document in the given directory

    create a new entry if it's the first-time conversion
    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist in source tree
    """
    if not doc_name:
        raise AttributeError('no_name')
    if not contents:
        raise AttributeError('load_html')
    if doc_name not in [x.replace('.rst', '.html') for x in list_docs(
            sitename, 'src', directory)]:
        raise FileNotFoundError("no_document")
    path = FS_WEBROOT / sitename / DEST_LOC
    if directory:
        path /= directory
    if not path.exists():
        path.mkdir()
    path = path / doc_name
    ext = LOC2EXT['dest']
    if path.suffix != ext:
        path = path.with_suffix(ext)
    save_to(path, contents)


def apply_deletions_target(sitename, directory=''):
    """Copy deletion markers from source to target environment
    """
    path = FS_WEBROOT / sitename / SRC_LOC
    if directory:
        path /= directory
    deleted = []
    for item in path.glob('*' + DELMARK):
        deleted.append(item.name)
        item.unlink()
    path = FS_WEBROOT / sitename / DEST_LOC
    if directory:
        path /= directory
    for item in deleted:
        newpath = path / item
        to_delete = newpath.with_suffix(LOC2EXT['dest'])
        if to_delete.exists():
            to_delete.rename(newpath)
        else:
            newpath.touch()


def update_mirror(sitename, doc_name, data, directory=''):
    """administer promoting the converted document in the given directory
    to the mirror site
    some additions are only saved in the mirror html hence the data argument
    otherwise we could get it from the target location

    raise AttributeError if no name provided
    create a new entry if it's the first time
    """
    if not doc_name:
        raise AttributeError('no_name')
    path = FS_WEBROOT / sitename
    if directory:
        path /= directory
        if not path.exists():
            path.mkdir(parents=True)
    path /= doc_name
    ext = LOC2EXT['mirror']
    if path.suffix != ext:
        path = path.with_suffix(ext)
    save_to(path, data)


def apply_deletions_mirror(sitename, directory=''):
    """Copy deletion markers from target to mirror environment and remove in all envs
    """
    path = FS_WEBROOT / sitename / DEST_LOC
    if directory:
        path /= directory
    deleted = []
    for item in path.glob('*' + DELMARK):
        deleted.append(item.name)
        item.unlink()
    path = FS_WEBROOT / sitename
    if directory:
        path /= directory
    for item in deleted:
        newpath = path / item
        to_delete = newpath.with_suffix(LOC2EXT['dest'])
        if to_delete.exists():
            to_delete.unlink()


def remove_doc(sitename, docname, directory=''):
    """delete document from site"""
    raise NotImplementedError


def get_doc_stats(sitename, docname, dirname=''):
    """get statistics for a document in a site subdirectory"""
    mtimes = [datetime.datetime.min, datetime.datetime.min, datetime.datetime.min]
    for ix, ftype in enumerate(LOCS):
        path = _locify(FS_WEBROOT / sitename, ftype)
        path = path / dirname if dirname else path
        path /= docname
        ext = LOC2EXT[ftype]
        if path.suffix != ext:
            path = path.with_suffix(ext)
        ## if ftype == LOCS[2] and not path.suffix:
            ## path = path.with_suffix('.html')
        if path.exists():
            mtimes[ix] = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return Stats(*mtimes)


def _get_dir_ftype_stats(sitename, ftype, dirname=''):
    """get statistics for all documents of a certain type in a site subdirectory"""
    do_seflinks = read_settings(sitename).get('seflinks')
    ext = '.rst' if not ftype else LOC2EXT[ftype]
    result = []
    path = _locify(FS_WEBROOT / sitename, ftype)
    if dirname:
        path = path / dirname
    if path.exists():
        for item in path.iterdir():
            if item.name.startswith('.') or item.name in ('css', SRC_LOC, DEST_LOC):
                continue
            if ftype in LOCS[1:] and do_seflinks:
                docname = item.stem
                if item.is_dir():
                    check_item = item / 'index.html'
                elif item.name == 'index.html' and not dirname:
                    check_item = item
                else:
                    continue
                result.append((docname, check_item.stat().st_mtime))
            else:
                if not item.is_file():
                    continue
                if item.suffix and item.suffix != ext:
                    continue
                docname = item.relative_to(path).stem
                result.append((docname, item.stat().st_mtime))
    return result


def _get_dir_stats(site_name, dirname=''):
    """get statistics for all documents in a site subdirectory"""
    result = defaultdict(lambda: [datetime.datetime.min, datetime.datetime.min,
                                  datetime.datetime.min])
    for ix, ftype in enumerate(LOCS):
        statslist = _get_dir_ftype_stats(site_name, ftype, dirname)
        for name, mtime in statslist:
            result[name][ix] = datetime.datetime.fromtimestamp(mtime)
    return sorted([(x, Stats(*y)) for x, y in result.items()])


def get_all_doc_stats(sitename):
    """get statistics for all site subdirectories"""
    filelist = [('/', _get_dir_stats(sitename))]
    for item in list_dirs(sitename, 'src'):
        filelist.append((item, _get_dir_stats(sitename, item)))
    return filelist


# deze worden niet gebruikt door de applicatie, maar wel door de testroutines
def _get_dir_stats_for_docitem(site_name, dirname=''):
    """get statistics for a document and return in a specific format
    """
    docid = 0
    result_dict = defaultdict(
        lambda: {x: {'updated': datetime.datetime.min} for x in LOCS})
    for ftype in LOCS:
        statslist = _get_dir_ftype_stats(site_name, ftype, dirname)
        for name, mtime in statslist:
            if ftype != 'mirror':  # for comparability with other backends
                docid += 1
                result_dict[name][ftype]['docid'] = docid
            result_dict[name][ftype]['updated'] = datetime.datetime.fromtimestamp(mtime)
    result = {}
    for name in result_dict:
        value = {}
        for ftype in result_dict[name]:
            if result_dict[name][ftype]['updated'] != datetime.datetime.min:
                value[ftype] = result_dict[name][ftype]
        result[name] = value
    ## return sorted((x, y) for x, y in result.items())

    return result


def _get_sitedoc_data(sitename):
    """build a "sitedoc" for processing in list_site_data"""
    filedict = {'/': _get_dir_stats_for_docitem(sitename)}
    for item in list_dirs(sitename, 'src'):
        filedict[item] = _get_dir_stats_for_docitem(sitename, item)
    return filedict


def list_site_data(sitename):
    """list all data on the site in a readable form

    for testing purposes and such
    """
    # caveat: we can't 100% derive the settings file name from the site name
    ## test = SETTFILE.format(sitename)
    ## settings = test if test in list_sites() else 'settings.yml'
    _id = 0
    sitedoc = {'_id': _id,
               'name': sitename,
               'settings': read_settings(sitename),
               'docs': _get_sitedoc_data(sitename)}
    fnames, data = [], []
    for ftype in LOCS[:2]:
        names = list_docs(sitename, ftype)
        fnames.extend([(x, ftype) for x in names])
        for dirname in list_dirs(sitename, ftype):
            names = list_docs(sitename, ftype, dirname)
            fnames.extend([('/'.join((dirname, x)), ftype) for x in names])
    base = FS_WEBROOT / sitename
    for name, ftype in sorted(fnames):
        path = base / SRC_LOC if ftype == 'src' else base / DEST_LOC
        path /= name
        mld1, data1 = read_data(path.with_suffix(LOC2EXT[ftype]))
        mld2, data2 = read_data(path.with_suffix(LOC2EXT[ftype] + '.bak'))
        data.append({'_id': (name, ftype),
                     'current': mld1 or data1,
                     'previous': mld2 or data2})
    return sitedoc, data


def clear_site_data(sitename):
    """remove site from file system by removing mirror and underlying
    """
    path = FS_WEBROOT / sitename
    try:
        shutil.rmtree(str(path))
    except FileNotFoundError:
        pass
