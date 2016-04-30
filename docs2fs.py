# import datetime
from collections import namedtuple, defaultdict
import datetime
import yaml
import shutil
import pathlib
HERE = pathlib.Path(__file__).parent
from app_settings import WEBROOT, SETTFILE
stat_keys = ('src', 'dest', 'to_mirror')
Stats = namedtuple('Stats', stat_keys)

# zelfde API als docs2mongo plus:

def _extify(path, ext=''):
    if ext in ('', 'src'):
        path /= 'source'
    elif ext == 'dest':
        path /= 'target'
    ## elif path != 'to_mirror':
        ## return 'invalid type', ''
    ## return '', path
    return path

def read_data(fname):   # to be used for actual file system data
    """reads data from file <fname>

    on success: returns empty message and data as a string
    on failure: returns error message and empty string for data
    """
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
    return mld, data

def save_to(fullname, data): # to be used for actual file system data
    """backup file, then write data to file

    gebruikt copyfile i.v.m. permissies (user = webserver ipv end-user)"""
    mld = ''
    if fullname.exists():
        shutil.copyfile(str(fullname),
            str(fullname.with_suffix(fullname.suffix + '.bak')))
    with fullname.open("w", encoding='utf-8') as f_out:
        try:
            f_out.write(data)
        except OSError as err:
            mld = str(err)
    return mld

## def clear_db(): pass # alle directories onder SITEROOT met source/target erin weggooien?
## def read_db(): pass
def list_sites():
    """build list of options containing all settings files in current directory"""
    return [x.stem.replace('settings_', '') for x in HERE.glob('settings*.yml')]
    ## return [x.name for x in HERE.glob('settings*.yml')]
    "listen alle directories onder WEBROOT met subdirectories source en target"
    path = WEBROOT
    sitelist = []
    for item in path.iterdir():
        if not item.is_dir():
            continue
        test1 = item / 'source'
        test2 = item / 'target'
        if test1.exists() and test1.isdir() and test2.exists() and test2.isdir():
            sitelist.append(item)
    return sitelist

def create_new_site(sitename):
    """aanmaken nieuwe directory onder WEBROOT plus subdirectories source en target
    alsmede initieel settings file
    """
    path = WEBROOT / sitename
    try:
        path.mkdir()
    except FileExistsError:
        raise FileExistsError('Site already exists')
    src = path / 'source'
    src.mkdir()
    targ = path / 'target'
    targ.mkdir()
    path = HERE / SETTFILE.format(sitename)
    path.touch()

def rename_site(sitename, newname): pass
# deze twee worden niet gebruikt door de applicatie, maar wel door de testroutines
def list_site_data(sitename):
    # caveat: we can't 100% derive the settings file name from the site name
    ## test = SETTFILE.format(sitename)
    ## settings = test if test in list_sites() else 'settings.yml'
    _id = 0
    sitedoc = {'_id': _id,
        'name': sitename,
        'settings': read_settings(sitename),
        'docs':  _get_sitedoc_data(sitename)}
    fnames, data = [], []
    for ftype in stat_keys[:2]:
        names = list_docs(sitename, ftype)
        fnames.extend([(x, ftype) for x in names])
        for dirname in list_dirs(sitename, ftype):
            names = list_docs(sitename, ftype, dirname)
            fnames.extend([('/'.join((dirname, x)), ftype) for x in names])
    base = WEBROOT / sitename
    for name, ftype  in sorted(fnames):
        path = base / 'source' if ftype == 'src' else base / 'target'
        path /= name
        data.append({'_id': (name, ftype),
            'current': read_data(path)[1],
            'previous': read_data(path.with_suffix('.bak'))[1]})
    return sitedoc, data

def clear_site_data(sitename):
    # remove settings file
    path = HERE / SETTFILE.format(sitename)
    try:
        path.unlink()
    except FileNotFoundError:
        pass

def read_settings(sitename):
    "lezen settings file"
    conf = None
    path = HERE / SETTFILE.format(sitename)
    try:
        with path.open(encoding='utf-8') as _in:
            conf = yaml.safe_load(_in) # let's be paranoid
    except FileNotFoundError:
        raise
    if conf is None: conf = {}
    return conf

def change_setting(sitename, sett_name, value):
    """modify a site setting to the given value

    can also add a new setting
    """
    settings = read_settings(sitename)
    settings[sett_name] = value
    result = update_settings(sitename, settings)
    return result

def update_settings(sitename, conf):
    "update (save) settings file"
    path = HERE / SETTFILE.format(sitename)
    if path.exists():
        shutil.copyfile(str(path),
            str(path.with_suffix(path.suffix + '.bak')))
    with path.open('w', encoding='utf-8') as _out:
        yaml.dump(conf, _out, default_flow_style=False)
    return 'ok'

def clear_settings(sitename): pass
def list_dirs(sitename, ext=''):
    "list subdirs for type"
    test = WEBROOT / sitename
    if not test.exists():
        raise FileNotFoundError('Site bestaat niet')
    path = _extify(test, ext)
    return [str(f.relative_to(path)) for f in path.iterdir() if f.is_dir()]

def create_new_dir(sitename, dirname):
    "create site subdirectory in source tree"
    path = WEBROOT / sitename / 'source' / dirname
    path.mkdir()    # can raise FileExistsError - is caught in caller

def remove_dir(sitename, directory): pass
def list_docs(sitename, ext, directory=''):
    """list the documents of a given type in a given directory

    raises FileNotFoundError if site or directory doesn't exist
    """
    path = WEBROOT / sitename
    if not path.exists():
        raise FileNotFoundError('Site bestaat niet')
    path = _extify(path, ext)
    if directory:
        path /= directory
        if not path.exists():
            raise FileNotFoundError('Subdirectory bestaat niet')
            ## return []
    ## return [str(f.relative_to(path)) for f in path.glob("*.{}".format(ext))]
    ## return [str(f.relative_to(path)) for f in path.iterdir() if f.is_file()]
    return [str(f.relative_to(path)) for f in path.iterdir() if f.is_file()
        and f.suffix != '.bak']

def create_new_doc(sitename, docname, directory=''):
    """add a new (source) document to the given directory

    assumes site exists
    raises AttributeError on missing doc_name,
           FileNotFoundError if directory doesn't exist
    """
    if not docname:
        raise AttributeError('No name provided')
    path = _extify(WEBROOT / sitename, 'src')
    if directory:
        path = path / directory
    if not path.exists():
        raise FileNotFoundError('Subdirectory bestaat niet')
    path = path / docname
    path.touch(exist_ok=False)        # FileExistsError will be handled in the caller

def get_doc_contents(sitename, docname, doctype='', directory=''):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not docname:
        raise AttributeError('No name provided')
    path = WEBROOT / sitename
    path = _extify(path, doctype)
    if directory: path /= directory
    mld, doc_data = read_data(path / docname)
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
        raise AttributeError('No name provided')
    if not contents:
        raise AttributeError('No contents provided')
    if doc_name not in list_docs(sitename, 'src', directory):
        raise FileNotFoundError("Document doesn't exist")
    path = WEBROOT / sitename / 'source'
    if directory: path /= directory
    save_to(path / doc_name, contents)

def update_html(sitename, doc_name, contents, directory=''):
    """update a converted document in the given directory

    create a new entry if it's the first-time conversion
    raises AttributeError on missing document name or contents
           FileNotFoundError if document doesn't exist in source tree
    """
    if not doc_name:
        raise AttributeError('No name provided')
    if not contents:
        raise AttributeError('No contents provided')
    if doc_name not in list_docs(sitename, 'src', directory):
        raise FileNotFoundError("Document doesn't exist")
    path = WEBROOT / sitename / 'target'
    if directory: path /= directory
    if not path.exists():
        path.mkdir()
    save_to(path / doc_name, contents)

def update_mirror(sitename, doc_name, directory=''):
    """administer promoting the converted document in the given directory
    to the mirror site

    raise AttributeError if no name provided
    create a new entry if it's the first time
    """
    if not doc_name:
        raise AttributeError('No name provided')
    ## path = WEBROOT / sitename
    ## if directory: path /= directory
    ## if not path.exists():
        ## path.mkdir()
    # this does nothing more - the rest is done in the caller

def remove_doc(sitename, docname, directory=''): pass
def get_doc_stats(sitename, docname, dirname=''):
    mtimes = [datetime.datetime.min, datetime.datetime.min, datetime.datetime.min]
    for ix, ftype in enumerate(stat_keys):
        path = _extify(WEBROOT / sitename, ftype)
        path = path / dirname if dirname else path
        path /= docname
        if ftype == stat_keys[2] and not path.suffix:
            path = path.with_suffix('.html')
        if path.exists():
            mtimes[ix] = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return Stats(*mtimes)

def _get_dir_ftype_stats(sitename, ftype, dirname=''):
    if ftype in ('', 'src'):
        ext = '.rst'
    elif ftype in ('dest', 'to_mirror'):
        ext = '.html'
    else:
        return
    result = []
    path = _extify(WEBROOT / sitename, ftype)
    if dirname:
        path = path / dirname
    if path.exists():
        for item in path.iterdir():
            if not item.is_file(): continue
            if item.suffix and item.suffix != ext: continue
            docname = item.relative_to(path).stem
            result.append((docname, item.stat().st_mtime))
    return result

def _get_dir_stats(site_name, dirname=''):
    result = defaultdict(lambda : [datetime.datetime.min, datetime.datetime.min,
        datetime.datetime.min])
    for ix, ftype in enumerate(stat_keys):
        statslist = _get_dir_ftype_stats(site_name, ftype, dirname)
        for name, mtime in statslist:
            result[name][ix] = datetime.datetime.fromtimestamp(mtime)
    return sorted([(x, Stats(*y)) for x, y in result.items()])

def get_all_doc_stats(sitename):
    filelist = [('/', _get_dir_stats(sitename))]
    for item in list_dirs(sitename, 'src'):
        filelist.append((item, _get_dir_stats(sitename, item)))
    return filelist

def _get_dir_stats_for_docitem(site_name, dirname=''):
    docid = 0
    result_dict = defaultdict(lambda : {x: {'updated': datetime.datetime.min}
        for x in stat_keys})
    for ftype in stat_keys:
        statslist = _get_dir_ftype_stats(site_name, ftype, dirname)
        for name, mtime in statslist:
            if ftype != 'to_mirror': # for comparability with other backends
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
    filedict = {'/': _get_dir_stats_for_docitem(sitename)}
    for item in list_dirs(sitename, 'src'):
        filedict[item] = _get_dir_stats_for_docitem(sitename, item)
    return filedict
