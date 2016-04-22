# import datetime
from collections import namedtuple
import pathlib
HERE = pathlib.Path(__file__).parents[0]
from rst2html_app_settings import WEBROOT
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
    return [x.name for x in HERE.glob('settings*.yml')]
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
    "aanmaken nieuwe directory onder WEBROOT plus subdirectories source en target"
    path = WEBROOT / sitename
    try:
        path.mkdir()
    except FileExistsError:
        raise
    src = path / 'source'
    src.mkdir()
    targ = path / 'target'
    targ.mkdir()
    return ''

def rename_site(sitename, newname): pass
# deze twee worden niet gebruikt door de applicatie, maar wel door de testroutines
def list_site_data(site_name):
    # caveat: we can't 100% derive the settings file name from the site name
    test = 'settings_{}.yml'.format(site_name)
    settings = test if test in list_sites() else 'settings.yml'
    sitedoc = (sitename, read_settings(settings), get_all_doc_stats(site_name))
    # let's not bother with file contents here
    return sitedoc

def clear_site_data(sitename): pass # can remain empty, work is done in caller
def read_settings(filename):
    "lezen settings file"
    test = HERE / filename
    conf = {}
    with test.open(encoding='utf-8') as _in:
        conf = yaml.safe_load(_in) # let's be paranoid
    if conf:
        return conf

def change_setting(sitename, settname, value): pass
def update_settings(path, conf):
    "update (save) settings file"
    if path.exists():
        shutil.copyfile(str(path),
            str(path.with_suffix(path.suffix + '.bak')))
    with path.open('w', encoding='utf-8') as _out:
        yaml.dump(conf, _out, default_flow_style=False)
    return 'ok' # FIXME: remove if result is never used

def clear_settings(sitename): pass
def list_dirs(sitename, ext=''):
    "list subdirs for type"
    test = WEBROOT / sitename
    if not test.exists():
        raise FileNotFoundError('Site bestaat niet')
    path = _extify(test, ext)
    return [str(f.relative_to(path)) + "/" for f in path.iterdir() if f.is_dir()]
    ## return dir_list

def create_new_dir(sitename, dirname):
    "create site subdirectory"
    siteroot = WEBROOT / sitename
    path = siteroot / dirname if dirname else siteroot
    path.mkdir()    # can raise FileExistsError - is caught in caller
    for subdir in ('source', 'target'):
        docroot = siteroot / subdir
        path = docroot / dirname if dirname else docroot
        path.mkdir()

def remove_dir(sitename, directory): pass
def list_docs(sitename, ext, directory=''):
    "list documents in subdir for type"
    path = WEBROOT / sitename
    if not path.exists():
        raise FileNotFoundError('Site bestaat niet')
    path = _extify(path, ext)
    if directory:
        path /= directory
        if not path.exists():
            raise FileNotFoundError('Subdirectory bestaat niet')
    return [str(f.relative_to(path)) for f in path.glob("*.{}".format(ext))]
    ## return doc_list

def create_new_doc(sitename, fname, directory=''):
    "create new document"
    if not doc_name:
        raise AttributeError('No name provided')
    path = _extify(path, 'src')
    path = path / dirname if dirname else path
    if not path.exists():
        raise FileNotFoundError('Subdirectory bestaat niet')
    path = path / fname
    path.touch()        # FileExistsError will be handled in the caller

def get_doc_contents(sitename, docname, doctype='', directory=''):
    """ retrieve a document of a given type in the given directory

    raises AttributeError on missing document name
           FileNotFoundError if document doesn't exist
    """
    if not doc_name:
        raise AttributeError('No name provided')
    path = WEBROOT / sitename / 'source'
    if directory: path /= directory
    mld, doc_data = read_data(path / docname)
    if mld:
        raise FileNotFoundError(mld)
    return doc_data

def update_rst(sitename, doc_name, contents, directory=''):
    "update rst"
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
    "update html"
    if not doc_name:
        raise AttributeError('No name provided')
    if not contents:
        raise AttributeError('No contents provided')
    if doc_name not in list_docs(sitename, 'src', directory):
        raise FileNotFoundError("Document doesn't exist")
    path = WEBROOT / sitename / 'target'
    if directory: path /= directory
    save_to(path / doc_name, contents)

def update_mirror(sitename, doc_name, directory=''):
    "update mirror"
    if not doc_name:
        raise AttributeError('No name provided')
    path = WEBROOT / sitename
    if directory: path /= directory
    # this does nothing more - the rest is done in the caller

def remove_doc(sitename, docname, directory=''): pass
def get_doc_stats(sitename, docname, dirname=''):
    mtimes = [datetime.datetime.min, datetime.datetime.min, datetime.datetime.min]
    for ix, ftype in enumerate(stat_keys):
        path = _extify(WEBROOT / sitename, ftype)
        path = path / dirname if dirname else path
        path /= docname
        if path.exists:
            mtimes[ix] = path.stat().st_mtime
    result = Stats(mtimes)

def _get_dir_ftype_stats(site_name, ftype, dirname=''):
    if ftype in ('', 'src'):
        ext = '.rst'
    elif ftype in ('dest', 'to_mirror'):
        ext = '.html'
    else:
        return
    result = []
    path = _extify(WEBROOT / sitename, ftype)
    path = path / dirname if dirname else path
    for item in path.iterdir():
        if not item.isfile(): continue
        if item.suffix != ext: continue
        result.append(('/'.join((dirname, str(item.relative_to(path)))),
            item.stat().st_mtime))
    return result

def _get_dir_stats(site_name, dirname=''):
    result = collections.defaultdict(lambda x: x, Stats(datetime.datetime.min,
        datetime.datetime.min, datetime.datetime.min))
    for ftype in stat_keys:
        statslist = _get_dir_ftype_stats(site_name, ftype, dirname)
        for name, mtime in statslist:
            result[name][ftype] = mtime
    return sorted((x, y) for x, y in result.items())

def get_all_doc_stats(site_name):
    filelist = [('/', _get_dir_stats(sitename))]
    for item in list_dirs(site_name, 'src'):
        filelist.append((dirname, _get_dir_stats(sitename, dirname)))
    return filelist
    ## return stats_list
