"""helper functions and processing class for Rst2HTML web app

business logic layer; data storage and retrieval stuff is in the docs2xxx modules
"""
import os
import shutil
import pathlib
import importlib
import inspect
## import glob
import html
import urllib.request
import urllib.error
import datetime
## import gettext
import subprocess
import collections

from app_settings import DFLT, DML, WEBROOT, LOC2EXT, BASIC_CSS, LANG, LOCAL_SERVER_CONFIG
if DML == 'fs':
    import docs2fs as dml
elif DML == 'mongo':
    import docs2mongo as dml
elif DML == 'postgres':
    import docs2pg as dml
from docs2fs import read_data, save_to, load_config_data, ParserError, save_config_data
#
# docutils stuff (including directives
#
from docutils.core import publish_string
import docutils.parsers.rst as rd
import rst2html_directives as rhdir
standard_directives = {"startc": rhdir.StartCols,
                       "endc": rhdir.EndCols,
                       "firstc": rhdir.FirstCol,
                       "nextc": rhdir.NextCol,
                       "clearc": rhdir.ClearCol,
                       "spacer": rhdir.Spacer,
                       "bottom": rhdir.Bottom,
                       'refkey': rhdir.RefKey,
                       'incl': rhdir.MyInclude,
                       'byline': rhdir.ByLine,
                       'audio': rhdir.Audio,
                       'menutext': rhdir.MenuText,
                       # 'mysidebar': rhdir.MySidebar,
                       'transcript': rhdir.Transcript,
                       'myheader': rhdir.MyHeader,
                       'startsidebar': rhdir.StartSideBar,
                       'endsidebar': rhdir.EndSideBar,
                       'myfooter': rhdir.MyFooter,
                       'gedicht': rhdir.Gedicht,
                       'songtekst': rhdir.SongTekst,
                       'startblock': rhdir.StartBlock,
                       'endblock': rhdir.EndBlock,
                       'rollen': rhdir.RoleSpec,
                       'scene': rhdir.Scene,
                       'anno': rhdir.Anno,
                       "startbody": rhdir.StartBody,
                       "navlinks": rhdir.NavLinks,
                       "textheader": rhdir.TextHeader,
                       "startcenter": rhdir.StartMarginless,
                       "endcenter": rhdir.EndMarginless,
                       "bottomnav": rhdir.BottomNav,
                       "endbody": rhdir.EndBody}
#
# internals
#
HERE = pathlib.Path(__file__).parent
custom_directives = HERE / 'custom_directives.py'
custom_directives_template = HERE / 'custom_directives_template.py'
CSS_LINK = '<link rel="stylesheet" type="text/css" media="all" href="{}" />'
# settings stuff
DFLT_CONF = {'wid': 100, 'hig': 32, 'url': '', 'css': []}
FULL_CONF = {'lang': 'en', 'starthead': [], 'endhead': [], 'seflinks': 0, 'highlight': 0}
FULL_CONF.update(DFLT_CONF)
SETT_KEYS = list(sorted(FULL_CONF.keys()))
SRV_CONFIG = pathlib.Path(LOCAL_SERVER_CONFIG)
# constants for loaded data
RST, HTML, CONF, XTRA = 'rst', 'html', 'yaml', 'py'
#
# Language support : eigengebakken spul, tzt te vervangen door gnu_gettext zaken (of niet)
#
# map filenames (minus .lng suffix) to language codes
language_map = (('english', 'en'),
                ('dutch', 'nl'))
# create dictionaries
languages = {}
for _name, _code in language_map:
    _path = HERE / '{}.lng'.format(_name)
    with _path.open(encoding='utf-8') as _in:
        _dict = {}
        for _line in _in:
            _line = _line.strip()
            if _line == "" or _line.startswith('#'):
                continue
            _key, _value = _line.split(' = ', 1)
            _dict[_key] = _value
        languages[_code] = _dict


def get_text(keyword, lang=LANG):
    """look up text in language data"""
    data = languages[lang]
    return data[keyword]
## gettext stuff to use instead
## app_title = 'Rst2HTML'
## locale = HERE / 'locale'
## gettext.install(app_title, str(locale))
## languages = {'nl': gettext.translation(app_title, locale, languages=['nl']),
    ## 'en': gettext.translation(app_title, locale, languages=['en'])}


def translate_action(action):
    "translate action verb from UI to language-independent value"
    for lang in languages:
        for keyword in ('c_rename', 'c_revert', 'c_delete'):
            if action == get_text(keyword, lang):
                action = keyword[2:]
    return action


def format_message(mld, lang, msg_parameter):
    try:
        mld = get_text(mld, lang)
    except KeyError:
        pass
    if '{}' in mld:
        mld = mld.format(msg_parameter)
    return mld


def post_process_title(data):
    """replace generated title with title from document
    """
    try:
        start, rest = data.split('<h1 class="page-title">', 1)
        doit = True
    except ValueError:
        doit = False
    if doit:
        title, end = rest.split('</h1>', 1)
        test = data.index('<head>')
        test2 = data.index('</head>', test)
        test3 = data.index('<title>', test)
        if test3 < test2:
            leng = test3
            start = data[:leng]
            _, end = data[leng:].split('</title>')
            data = ''.join((start, '<title>', title, '</title>', end))
    return data


# -- rst related --
def rst2html(data, css):
    """rst naar html omzetten en resultaat teruggeven
    """
    overrides = {"embed_stylesheet": False,
                 "stylesheet_path": '',
                 "stylesheet": css,
                 "report_level": 3}
    # return publish_string(source=data,
    #                       destination_path="temp/omgezet.html",
    #                       writer_name='html',
    #                       settings_overrides=overrides)
    newdata = str(publish_string(source=data, destination_path="temp/omgezet.html",
                                 writer_name='html', settings_overrides=overrides),
                  encoding='utf-8')
    newdata = post_process_title(newdata)
    return newdata


def register_directives():
    """make directives known to docutils"""
    for name, func in standard_directives.items():
        rd.directives.register_directive(name, func)
    if custom_directives.exists():
        load_custom_directives()


def load_custom_directives():
    """
    importeer de directives uit het genoemde directives file
    dat zijn alle Directive subclasses die daarin gedefinieerd zijn

    voor elk directive moet in de docstring op aparte regels het volgende staan:
        usage: .. directive_name:: <arguments>
        description: directive_name is for doing stuff
    """
    modname = inspect.getmodulename(str(custom_directives))
    data = importlib.import_module(modname)
    for name, value in inspect.getmembers(data, inspect.isclass):
        if rd.Directive in inspect.getmro(value) and value is not rd.Directive:
            directive_name, oms = name, ''
            docs = value.__doc__.split(os.linesep)
            usage = [x for x in docs if 'usage' in x]
            if usage:
                directive_name = usage[0].split('..', 1)[1].split('::', 1)[0].strip()
            desc = [x for x in docs if 'description' in x]
            if desc:
                oms = desc[0].split(':', 1)[1].strip()
            rd.directives.register_directive(directive_name, oms)  # lijkt me beter dan value)


def get_custom_directives_filename():
    """determine filename to load and action to take"""
    if custom_directives.exists():
        fname = custom_directives
        verb = 'loaded'
    else:
        fname = custom_directives_template
        verb = 'init'
    return fname, verb


def get_directives_used(results):
    """scan search results for directives and return them if any
    """
    result = set()
    for locations in results.values():
        for line_results in locations:
            line, text, locs = line_results
            for loc in locs:
                try:
                    name, rest = text[loc + 2:].split('::', 1)
                except ValueError:
                    pass  # print(line, text, locs)
                else:
                    result.add(name.lstrip())
    return result


def get_idcls(directives_used):
    """collect ids and classes used by custom directives
    """
    result = set()
    for directive in directives_used:
        if directive in rhdir.directive_selectors:  # we don't check the standard docutils ones
            for selector, stuff in rhdir.directive_selectors[directive]:
                result.add(stuff)
    return result


def check_directive_selectors(sitename):
    """check if the used css files contain the ids / classes used in the directives
    """
    # find all directives used by the documents -> directives_used (list)
    results = search_site(sitename, '.. ')
    # return results
    directives_used = get_directives_used(results)
    if not directives_used:
        return ''  # niks te doen
    idcls = get_idcls(directives_used)
    if not idcls:
        return ''  # niks te doen
    css_files = read_conf(sitename)[1]['css']
    tmpfile = '/tmp/r2h_css.css'
    command = ['wget'] + css_files + ['-O', tmpfile]
    subprocess.run(command)
    with open(tmpfile) as infile:
        all_css = infile.read()
    missing = []
    for text in idcls:
        if text not in all_css:
            missing.append(text)
    if missing:
        return missing
    return ''


def preprocess_includes(sitename, current, data):
    "eigengebakken include support (zodat het werkt voor alle backends)"
    keyword = '.. incl::'
    lang = read_conf(sitename)[1].get('lang', '') or LANG
    while keyword in data:
        start, rest = data.split(keyword, 1)
        if '\n' in rest:  # bij laatste regel kan deze ontbreken
            name, end = rest.split('\n', 1)
        else:
            name, end = rest, ''
        if not name:
            name = "it's missing..."
            msg = '.'
        else:
            name = name.strip()
            parts = name.split('/')  # max 2 splits allowed
            msg = ''
        if msg:
            pass
        elif len(parts) == 1:
            include_location = current
        elif len(parts) == 2:
            if parts[0] == '..' and current:
                include_location = ''
            elif parts[0] != '..' and not current:
                include_location = parts[0]
            else:
                msg = '.'
        elif len(parts) == 3:
            if not current or parts[0] == '..' or parts[1] != '..':
                msg = '.'
            else:
                include_location = parts[0]
        else:
            msg = '.'
        if msg:
            msg = 'fname_invalid'  # 'illegal path specified for include'
        else:
            msg, text = read_src_data(sitename, include_location, parts[-1])
        if msg:
            text = '.. error:: {}: {}\n'.format(get_text(msg, lang), name)
        data = text.join((start, end))
    return data


# -- site / conf related --
def default_site():
    """return the first entry in the sites list to provide as default

    check if it exists for this application
    """
    result = DFLT
    all_sites = dml.list_sites()
    if result not in all_sites:
        result = all_sites[0] if all_sites else ''
    return result


def new_conf(sitename, text, lang=LANG):
    """create a new site definition including settings

    returns '' on success, message on failure
    also returns the new site url on success
    """
    newurl = ''
    not_ok, conf = text2conf(text, lang)
    if not_ok:
        return ' '.join((get_text('not_created', lang).format(sitename), not_ok)), newurl
    if not conf['url']:
        newurl = 'http://' + create_server_config(sitename)
    try:
        dml.create_new_site(sitename)
    except FileExistsError as e:
        return str(e), newurl  # is newurl leegmaken hier niet beter ivm vervolg in save_conf ?
    return '', newurl


def create_server_config(sitename):
    """build a url for the mirror site and make it known to the system
    """
    url = '.'.join((sitename, get_tldname()))
    add_to_hostsfile(url)
    location = str(WEBROOT / sitename)
    add_to_server(url, location)
    return url


def get_tldname():
    """look in /etc/hosts or /etc/hostname to determine the top level domain to use
    """
    basename = tldname = ''
    with open('/etc/hosts') as hostsfile:
        for line in hostsfile:
            if not line.strip().startswith('127.0.0.1'):
                continue
            ipaddr, name = line.strip().split(None, 1)
            if '.' in name:
                tldname = name
                break
            if not basename:
                basename = name
    if not tldname:
        if not basename:
            basename = pathlib.Path('/etc/hostname').read_text().strip()
        tldname = basename + '.nl'
    return tldname


def add_to_hostsfile(url):
    """map to localhost and add to /etc/hosts

    update a local version and upload via a script
    """
    with (SRV_CONFIG / 'misc/hosts').open('a') as hostsfile:
        print('127.0.0.1     {}'.format(url), file=hostsfile)


def add_to_server(url, location):
    """map to file system location and add to server configuration

    update a local version and upload / restart server via a script
    """
    logloc = url.rsplit('.', 1)[0]
    with (SRV_CONFIG / 'nginx/flatpages').open('a') as config:
        for line in ('server {',
                     '    server_name {};'.format(url),
                     '    root {};'.format(location),
                     '    error_log /var/log/nginx/{}-error.log error;'.format(logloc),
                     '    access_log /var/log/nginx/{}-access.log ;'.format(logloc),
                     '    }'):
            print(line, file=config)


def init_css(sitename):
    """copy css files to site root and update config
    """
    conf = dml.read_settings(sitename)
    updated = False
    cssdir = WEBROOT / sitename / 'css'
    for cssfile in BASIC_CSS:
        got_css = False
        for entry in conf['css']:
            if entry.endswith(cssfile):
                got_css = True
                break
        if not got_css:
            cssdir.mkdir(exist_ok=True)
            src = str(HERE / 'static' / cssfile)
            dest = str(cssdir / cssfile)
            shutil.copyfile(src, dest)
            conf['css'].append('url + css/' + cssfile)
            updated = True
    if updated:
        dml.update_settings(sitename, conf)


def list_confs(sitename=''):
    """build list of options containing all possible site settings

    if site name provided, show as "selected"""
    out = []
    for name in dml.list_sites():
        s = ' selected="selected"' if name == sitename else ''
        out.append("<option{}>{}</option>".format(s, name))
    return "".join(out)


def read_conf(sitename):
    """read a config file; returns a dictionary of options
    """
    try:
        sett = dml.read_settings(sitename)
    except FileNotFoundError:
        return 'no_such_sett', None
    else:
        return '', sett


def conf2text(conf):
    """convert settings to dict and then to yaml structure"""
    confdict = {}
    for key, value in conf.items():
        if key == 'css':
            items = []
            for item in conf['css']:
                if conf['url'] and item.startswith(conf['url']):
                    item = item.replace(conf['url'] + '/', 'url + ')
                items.append(item)
            confdict[key] = items
        else:
            confdict[key] = value
    return save_config_data(confdict, default_flow_style=False)


def text2conf(text, lang=LANG):
    """convert text (from input area) to settings dict and return it

    also check settings for correctness (valid locations)
    """
    invalid = get_text('sett_invalid', lang)
    # pass data through yaml to parse into a dict
    try:
        conf = load_config_data(text)   # ik wil die parsererror eigenlijk niet hoeven importeren
    except ParserError:                 # maar dan moet ik load_config_html anders definiëren
    # notok, conf = load_config_data(text)
    # if notok:
        return get_text('sett_no_good', lang), {}

    for key in DFLT_CONF:  # check if obligatory keys are present
        if key not in conf:
            return invalid.format(key), {}

    for key in FULL_CONF:  # check value for each key
        if key not in conf:
            continue
        value = conf[key]
        if key in ('wid', 'hig'):  # and isinstance(value, int):
            try:
                int(value)
            except ValueError:
                return invalid.format(key), {}
        elif key == 'lang' and value not in languages:
            return invalid.format('lang'), {}
        elif key == 'url' and value != '':
            if not value.startswith('http'):
                return invalid.format('url'), {}
            else:  # simple check for valid url setting
                if value.endswith('/'):
                    value = value[:-1]
                try:
                    check_url(value)
                except (urllib.error.HTTPError, urllib.error.URLError):
                    return invalid.format('url'), {}
    if isinstance(conf['css'], str):  # als string, dan list van maken met dit als enige element
        conf['css'] = [conf['css']]
    for ix, item in enumerate(conf['css']):
        if item.startswith('url + '):
            if conf['url']:
                conf['css'][ix] = item.replace('url + ', conf['url'] + '/')
        elif not item.startswith('http'):
            conf['css'][ix] = 'https://' + item
    return '', conf


def check_url(value):
    "recursively try to find the url (we could be in a sub-site"
    try:
        urllib.request.urlopen(value)
    except (urllib.error.HTTPError, urllib.error.URLError):
        value = value.rsplit('/', 1)[0]
        if value != 'http:/':
            check_url(value)
        else:
            raise


def save_conf(sitename, text, lang=LANG):
    """save the given settings into the site
    """
    conf = {}
    try:
        dml.read_settings(sitename)
    except FileNotFoundError:
        return get_text('no_such_sett', lang).format(sitename)
    not_ok, conf = text2conf(text, lang)
    if conf:
        dml.update_settings(sitename, conf)
    return not_ok


# -- content related --
def list_subdirs(sitename, ext=''):
    "list all subdirectories that contain the designated type of documents"
    if ext == '':
        ext = 'src'
    elif ext != 'src':
        ext = 'dest'
    try:
        test = dml.list_dirs(sitename, ext)
    except FileNotFoundError:
        return []
    return [x + '/' for x in sorted(test)]


def list_files(sitename, current='', naam='', ext='', deleted=False):  # , lang=LANG
    """build list of options from filenames, with `naam` selected"""
    ext = ext or 'src'  # default
    try:
        items = dml.list_docs(sitename, ext, directory=current, deleted=deleted)
    except FileNotFoundError:
        items = []
        if current == '' and deleted is False:
            return "Site not found"

    if items is None:
        return 'Wrong type: `{}`'.format(ext)
    elif deleted:
        # just return the names of the deleted files
        return items
    else:
        # make sure files have the correct extension
        items = [x + LOC2EXT[ext] for x in items]
    items.sort()
    if current:
        items.insert(0, "..")
    else:
        items = list_subdirs(sitename, ext) + items
    ## items.insert(0, get_text('c_newitem', lang))
    out = []
    if ext == 'src':
        for f in dml.list_templates(sitename):
            out.append("<option>-- {} --</option>".format(f))
    for f in items:
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{}>{}</option>".format(s, f))
    return "".join(out)


def read_src_data(sitename, current, fname):
    """get source data from wherever it's been stored
    """
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.rst'):
        return 'rst_filename_error', ''
    try:
        return '', dml.get_doc_contents(sitename, path.stem, 'src', current)
    except AttributeError:
        return 'src_name_missing', ''
    except FileNotFoundError:
        return 'src_file_missing', ''


def read_html_data(sitename, current, fname):
    """get target data from wherever it's been stored
    """
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.html'):
        return 'html_filename_error', ''
    try:
        return '', dml.get_doc_contents(sitename, path.stem, 'dest', current)
    except AttributeError:
        return 'html_name_missing', ''
    except FileNotFoundError:
        return 'html_file_missing', ''


def read_tpl_data(sitename, fnaam):
    "get template data from wherever it's stored"
    return dml.read_template(sitename, fnaam)


def save_tpl_data(sitename, fnaam, data):
    "store template data"
    return dml.write_template(sitename, fnaam, data)


def check_if_rst(data, loaded, filename=None):
    """simple check if data contains rest
    assuming "loaded" indicates the current type of text

    if filename is filled, also check if it's a correct name
    """
    mld = ""
    if data == "":
        mld = 'supply_text'
    elif loaded != RST:  # data.startswith('<'):
        mld = 'rst_invalid'
    elif filename is None:
        pass
    elif filename.endswith("/") or filename in ("", "-- new --", ".."):
        mld = 'src_name_missing'
    return mld


def check_if_html(data, loaded, filename=None):
    """simple check if rstdata contains html
    assuming "loaded" indicates the current type of text

    if filename is filled, also check if it's a correct name
    """
    mld = ""
    if data == "":
        mld = 'supply_text'
    elif loaded != HTML:  # not data.startswith('<'):
        mld = 'load_html'
    elif filename is None:
        pass
    elif filename.endswith("/") or filename in ("", "-- new --", ".."):
        mld = 'html_name_missing'
    return mld


def make_new_dir(sitename, fname):
    """try to create a new subdirectory on the "site"
    """
    try:
        dml.create_new_dir(sitename, fname)
    except FileExistsError:
        return 'dir_name_taken'
    return ''


def save_src_data(sitename, current, fname, data, new=False):
    "save the source data on the server"
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.rst'):
        return 'rst_filename_error'
    if current and current + '/' not in list_subdirs(sitename):
        try:
            dml.create_new_dir(sitename, current)
        except FileExistsError:
            pass  # already existing is ok
    try:
        if new:
            try:
                dml.create_new_doc(sitename, path.name, directory=current)
            except FileExistsError:
                return 'src_name_taken'
        dml.update_rst(sitename, path.stem, data, directory=current)
        return ''
    except AttributeError as e:
        if 'name' in str(e):
            return 'src_name_missing'
        if 'contents' in str(e):
            return 'supply_text'
        return str(e)
    except FileNotFoundError as e:
        return 'src_file_missing'


def revert_src(sitename, current, fname):
    "restore the source to the previous version"
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.rst'):
        return 'rst_filename_error'
    try:
        dml.revert_rst(sitename, path.stem, current)
        return ''
    except AttributeError as e:
        return 'src_name_missing'
    except FileNotFoundError as e:
        if 'backup' in str(e):
            return 'backup_missing'
        return 'src_file_missing'


def mark_deleted(sitename, current, fname):
    """te verwijderen tekst als zodanig kenmerken
    """
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.rst'):
        return 'rst_filename_error'
    try:
        dml.mark_src_deleted(sitename, path.stem, directory=current)
        return ''
    except AttributeError:
        return 'src_name_missing'
    except FileNotFoundError:
        return 'src_file_missing'


def save_html_data(sitename, current, fname, data, dry_run=False):
    "save the converted data on the server"
    dml.apply_deletions_target(sitename, current)  # always do pending deletions
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.html'):
        return 'html_filename_error'
    try:
        dml.update_html(sitename, path.stem, data, directory=current, dry_run=dry_run)
        return ''
    except (AttributeError, FileNotFoundError) as e:
        if 'name' in str(e):
            return 'html_name_missing'
        if 'contents' in str(e):
            return 'supply_text'
        return str(e)


def complete_header(conf, rstdata):
    """add data from the settings into the html header
    """
    if conf.get('starthead', ''):
        if '<head>' in rstdata:
            split_on = '<head>'  # + os.linesep
            start, end = rstdata.split(split_on, 1)
        else:
            split_on, start, end = '', '', rstdata
        if isinstance(conf['starthead'], str):
            middle = conf['starthead']
        else:
            middle = ''.join(conf['starthead'])
        rstdata = start + split_on + middle + end
    if conf.get('endhead', ''):
        if '</head>' in rstdata:
            split_on = '</head>'  # + os.linesep
            start, end = rstdata.split(split_on, 1)
        else:
            split_on, start, end = '', '', rstdata
        if isinstance(conf['endhead'], str):
            middle = conf['endhead']
        else:
            middle = ''.join(conf['endhead'])
        rstdata = start + middle + split_on + end
    # replace references to local domain
    if conf['url']:
        rstdata = rstdata.replace(conf['url'] + '/', '/')
        rstdata = rstdata.replace(conf['url'], '/')
    return rstdata


def save_to_mirror(sitename, current, fname, conf, dry_run=False):
    """store the actual html on the server
    """
    dml.apply_deletions_mirror(sitename, current)  # always do pending deletions
    path = pathlib.Path(fname)
    if path.suffix not in ('', '.html'):
        return 'Not a valid html file name'  # TODO: language string van maken
    if current:
        mld, data = read_html_data(sitename, current, path.stem)
    else:
        mld, data = read_html_data(sitename, '', path.stem)
    if mld:
        return mld
    data = complete_header(conf, data)
    sitename = conf.get("mirror", sitename)
    try:
        dml.update_mirror(sitename, path.stem, data, directory=current, dry_run=dry_run)
        return ''
    except AttributeError as e:
        if 'name' in str(e):
            return 'html_name_missing'
        return str(e)


# -- progress list --
def build_progress_list(sitename):
    """build a list of the conversion state of all site documents
    """
    result = []
    rootitem = None
    data = dml.get_all_doc_stats(sitename)
    for ix, diritem in enumerate(data):
        if diritem[0] == '/':
            rootitem = data.pop(ix)
            break
    data.sort()
    if rootitem:
        data.insert(0, rootitem)
    for dirname, docs in data:
        for docname, stats in sorted(docs):
            maxval = max(stats)
            for idx, val in enumerate(stats):
                if maxval == val:
                    maxidx = idx
            result.append((dirname, docname, maxidx, stats))
    return result


def get_copystand_filepath(sitename):
    "determine filename to use for saving the progress overview data"
    dts = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
    return  WEBROOT / sitename / 'voortgangsoverzicht-{}'.format(dts)


def get_progress_line_values(docinfo):
    "convert a progress_list entry into a sequence of text items"
    if docinfo[0] == '/':
        docname = docinfo[1]
    else:
        docname = '/'.join(docinfo[:2])
    result = [docname]
    maxidx, stats = docinfo[2:]
    for idx, dts in enumerate(stats):
        if dts == datetime.datetime.min:
            timestring = "n/a"
        else:
            timestring = dts.strftime('%d-%m-%Y %H:%M:%S')
        if idx == maxidx:
            timestring = timestring.join(('--> ', ' <--'))
        result.append(timestring)
    return result


# -- convert all --
class UpdateAll:
    """Regenerate documents om a site according to parameters
    """

    def __init__(self, sitename, conf, missing_only=False, needed_only=False, show_only=False):
        """process all documents on the site
        """
        self.sitename = sitename
        self.conf = conf
        self.include_timestamps = {}
        self.missing_only = missing_only
        self.needed_only = needed_only
        self.show_only = show_only

    def go(self):
        "main line"
        messages = []
        result = build_progress_list(self.sitename)

        files_to_skip = self.conf.get('do-not-generate', [])
        for dirname, filename, phase, stats in result:
            self.path = WEBROOT / self.sitename
            if dirname == '/':
                self.fname = dirname + filename
            else:
                self.fname = '/'.join((dirname, filename))
                self.path /= dirname
            if self.fname in files_to_skip:
                continue

            msg, self.rstdata = read_src_data(self.sitename, dirname, filename)
            if msg:
                messages.append((self.fname, msg))
                continue

            target_needed = mirror_needed = True
            if self.needed_only:
                if stats.dest >= stats.src:
                    target_needed = False
                    if stats.mirror >= stats.dest:
                        mirror_needed = False
                    saved = mirror_needed
                    target_needed, mirror_needed = self.check_for_updated_includes(stats)
                    if not mirror_needed and saved:
                        mirror_needed = True
            elif self.missing_only:
                if stats.dest != datetime.datetime.min:  # bestaat, dus overslaan
                    target_needed = mirror_needed = False
            if target_needed:
                msg = self.rebuild_html(dirname, filename)
                if msg:
                    messages.append((self.fname, msg))
                    continue
                msg = 'html_saved'
                messages.append((self.fname, msg))
            if mirror_needed:
                msg = self.rebuild_mirror(dirname, filename)
                if not msg:
                    msg = 'copied_to'
                messages.append((self.fname, msg))
        return messages

    def check_for_updated_includes(self, doc_timestamp):
        "find out which documents are not updated since included files were:"
        contained_includes = check_for_includes(self.sitename, self.rstdata)
        target_needed = mirror_needed = False
        for item in contained_includes:
            inc_timestamp = self.include_timestamps.get(item, '')
            if not inc_timestamp:
                inc_timestamp = dml.get_doc_stats(self.sitename, item)
                self.include_timestamps[item] = inc_timestamp
            if doc_timestamp.dest < inc_timestamp.src:
                target_needed = mirror_needed = True
            elif doc_timestamp.mirror < inc_timestamp.src:
                mirror_needed = True
        return target_needed, mirror_needed

    def rebuild_html(self, dirname, filename):
        "regenerate target html if needed / possible"
        htmldata = rst2html(preprocess_includes(self.sitename, dirname, self.rstdata),
                            self.conf['css'])
        if self.show_only:
            # msg = save_html_data(self.sitename, dirname, filename, htmldata, dry_run=True)
            msg = 'regen_target_msg'
        else:
            msg = save_html_data(self.sitename, dirname, filename, htmldata)
        return msg

    def rebuild_mirror(self, dirname, filename):
        "regenerate mirror file if needed / possible"
        if self.show_only:
            # msg = save_to_mirror(self.sitename, dirname, filename, self.conf, dry_run=True)
            msg = 'regen_mirror_msg'
        else:
            msg = save_to_mirror(self.sitename, dirname, filename, self.conf)
        return msg


def check_for_includes(sitename, rstdata):
    "gebruikte includes afleiden uit source"
    includenames = []
    includes = [x.lstrip().split(None, 1)[0] for x in rstdata.split('.. include::')[1:]]
    # standard include (only file besed)
    for item in includes:
        path = pathlib.Path(item)
        if path.parent == WEBROOT / sitename / '.source':
            includenames.append(path.stem)
    # custom include using relative names and working for all backends
    includes = [x.lstrip().split(None, 1)[0] for x in rstdata.split('.. incl::')[1:]]
    for item in includes:
        path = pathlib.Path(item)
        includenames.append(path.stem)
    return includenames


# -- trefwoordenlijst --
def get_reflinks_in_dir(sitename, dirname='', sef=False):
    """search for keywords in source file and remember their locations

    NOTE: references are only valid if they're in files that have already been
    converted to html,
    so the html timestamp must be present and greater than the rst timestamp

    Klopt deze redenatie wel? Als je een document met reflinks aanpast nadat het omgezet is
    wil je de nieuwste versie met eventueel aangepaste referenties toch verwerken ook al
    zijn de documenten waarnaar gerefereerd wordt nog niet opnieuw gegenereerd?
    Uiteraard verdwijnt het probleem als je de index pas maakt nadat alle bestanden t/m mirror
    bijgewerkt zijn
    """
    reflinks, errors = {}, []
    items = dml.list_docs(sitename, 'src', directory=dirname)
    for filename in items:
        stats = dml.get_doc_stats(sitename, filename, dirname)
        if stats.src > stats.dest or stats.dest > stats.mirror:
            continue
        msg, rstdata = read_src_data(sitename, dirname, filename)
        if msg:
            errors.append((dirname, filename, msg))
            continue
        for line in rstdata.split('\n'):
            if line.startswith("..") and "refkey::" in line:
                refs = line.split("refkey::", 1)[1]
                for ref in (x.split(":") for x in refs.split(";")):
                    word = ref[0].strip().capitalize()
                    prefix = '/{}/'.format(dirname).replace('//', '/')
                    suffix = '/' if sef else '.html'
                    link = prefix + filename + suffix
                    if len(ref) > 1:
                        link += "#" + ref[1].strip()
                    reflinks.setdefault(word, [])
                    reflinks[word].append(link)
    return reflinks, errors


class TrefwoordenLijst:
    """create a document from predefined reference links
    """
    def __init__(self, sitename, lang=LANG, sef=False):
        self.sitename = sitename
        self.lang = lang
        self.sef = sef
        self.current_letter = ""
        self.clear_containers()

    def build(self):
        "scan for references and build the result page"
        has_errors = False
        reflinks, errors = self.get_reflinks()
        if not reflinks and not errors:
            return '', 'No index created: no reflinks found'  # TODO: make translation
        to_top = self.start_page()
        for key in sorted(reflinks.keys()):
            if key[0] != self.current_letter:
                if self.titel:
                    self.finish_letter(to_top)
                    to_top = "+   top_"
                    self.clear_containers()
                self.current_letter = key[0]
                self.start_new_letter()
            self.start_new_keyword(reflinks, key)
        if self.teksten:
            self.finish_letter(to_top)
        if errors:
            has_errors = True
            self.data.append('while creating this page, the following messages were generated:')
            self.data.append('----------------------------------------------------------------')
            for err in errors:
                self.data.append('. ' + err)
        return "\n".join(self.data), has_errors

    def clear_containers(self):
        """reset container attributes
        """
        self.titel, self.teksten, self.links, self.anchors = [], [], [], []

    def get_reflinks(self):
        """find the references in the sources
        """
        reflinks, errors = get_reflinks_in_dir(self.sitename, sef=self.sef)
        all_dirs = dml.list_dirs(self.sitename, 'src')
        for dirname in all_dirs:
            refs, errs = get_reflinks_in_dir(self.sitename, dirname, self.sef)
            reflinks.update(refs)
            errors.extend(errs)
        return reflinks, errors

    def start_page(self):
        """produceer het begin van de pagina"""
        hdr = get_text('index_header', self.lang)
        if self.sitename == 'magiokis':
            self.data = [hdr, "=" * len(hdr), "", ""]
            to_top = "+   `top <#header>`_"
        else:
            self.data = ['.. _top:', '`back to root </>`_', '', '.. textheader:: Index', '']
            to_top = "+   top_"
        return to_top

    def start_new_letter(self):
        """produceer het begin voor een letter"""
        loc = 3 if self.sitename == 'magiokis' else 6
        self.data[loc] += "{}_ ".format(self.current_letter)
        self.data.append("")
        if self.sitename == 'magiokis':
            self.titel = [".. _{0}:\n\n**{0}**".format(self.current_letter), ""]
        else:
            self.titel = ["{}".format(self.current_letter), "-"]
        self.linkno = 0

    def start_new_keyword(self, reflinks, key):
        """produceer het begin en de links voor een nieuw trefwoord"""
        current_trefw = "+   {}".format(key)
        for link in reflinks[key]:
            current_trefw += " `#`__ "
            self.linkno += 1
            linknm = self.current_letter + str(self.linkno)
            self.links.append("..  _{}: {}".format(linknm, link))
            self.anchors.append("__ {}_".format(linknm))
        self.teksten.append(current_trefw)

    def finish_letter(self, to_top):
        "produceer het eind voor een letter"
        self.data.extend(self.titel)
        self.data.append("")
        self.data.extend(self.teksten)
        self.data.append(to_top)
        self.data.append("")
        self.data.extend(self.links)
        self.data.append("")
        self.data.extend(self.anchors)
        self.data.append("")


# -- global search --
def search_site(sitename, find, replace=None):
    """return the results from the root and its subdirectories

    walk the root to get results from it
    then walk the subdirectories to add the results from there
    """
    results = read_dir(sitename, find, replace)
    for dirname in dml.list_dirs(sitename, 'src'):
        results.update(read_dir(sitename, find, replace, dirname))
    return results


def read_dir(sitename, search, replace, dirname=''):
    """return the results by walking a directory and getting results from the files in it

    results in this case being search results (and replacements) in each document
    """
    results = collections.defaultdict(list)
    for filename in dml.list_docs(sitename, 'src', directory=dirname):
        results[(dirname, filename)] = process_file(sitename, dirname, filename, search, replace)
    return results


def process_file(sitename, dirname, filename, search, replace):
    """do the finds and if needed the replacements
    """
    results = []
    contents = dml.get_doc_contents(sitename, filename, 'src', dirname)
    for number, line in enumerate(contents.split('\n')):
        if search in line:
            pos_list = []
            pos = line.find(search)
            while pos > -1:
                pos_list.append(pos)
                pos = line.find(search, pos + 1)
            # results.append((number + 1, line.strip(), [x + 1 for x in pos_list]))
            results.append((number + 1, line, [x + 1 for x in pos_list]))
    if replace is not None:
        new_contents = contents.replace(search, replace)
        dml.update_rst(sitename, filename, new_contents, dirname)
    return results


def searchdict2list(inputdict, search):
    """transfrom the search output to a list displayable on the site
    """
    outputlist = []
    for filespec, lines in sorted([x for x in inputdict.items()]):
        if not lines:
            continue
        dirname, filename = filespec
        if dirname:
            filespec = '/'.join((dirname, filename))
        else:
            filespec = '/' + filename
        for lineno, linetext, locs in lines:
            maxlen = 80
            if len(linetext) <= maxlen:
                text = linetext.replace(search, search.join((' **', '** ')))
                outputlist.append((filespec, lineno, text))
                continue
            for pos in locs:
                start = pos - 20 if pos > 20 else 0
                text = linetext[start:start + maxlen]
                text = text.replace(search, search.join((' **', '** ')), 1)
                if start > 0:
                    text = '...' + text
                if start + maxlen < len(linetext):
                    text += '...'
                outputlist.append((filespec, lineno, text))
    return outputlist


class R2hState:
    """state class containing the functions called up from the web app
    """
    def __init__(self):
        self.sitename = default_site()
        self.rstfile = self.htmlfile = self.newfile = self.rstdata = ""
        self.current = self.oldtext = self.oldhtml = ""
        self.conf = DFLT_CONF
        self.newconf = False
        self.loaded = 'initial'

    def currentify(self, fname):
        """add site directory to document name
        """
        if self.current:
            fname = '/'.join((self.current, fname))
        if self.conf.get('seflinks', False):
            fname = '/index'.join(os.path.splitext(fname))
        return fname

    def get_lang(self):
        "return language setting or a default if not set"
        if 'lang' not in self.conf:
            return LANG
        return self.conf["lang"]

    def get_conf(self, settings):
        """retrieve site config and set some variables
        """
        # settings is hier de site naam
        mld = ''
        if self.newconf:
            self.conf = DFLT_CONF
            self.current = ""
            self.subdirs = []
            self.loaded = CONF
        else:
            mld, conf = read_conf(settings)
            if mld == '':
                self.conf = conf
                self.current = ""
                self.subdirs = list_subdirs(settings, 'src')
                self.loaded = CONF
            else:
                mld = get_text(mld, self.get_lang()).format(settings)
        return mld

    def index(self):
        """create landing page
        """
        mld = get_text('no_confs', self.get_lang())
        if self.sitename:
            mld = self.get_conf(self.sitename)
        if mld == '':
            self.settings = self.sitename
            self.rstdata = conf2text(self.conf)
            mld = get_text('conf_init', self.get_lang()).format(self.sitename)
        return (self.rstfile, self.htmlfile, self.newfile, mld, self.rstdata,
                self.sitename)

    def loadconf(self, settings, newfile):
        """load settings for indicated site name

        if "-- new --" specified, create new settings from default (but don't save)
        """
        ## rstdata = self.rstdata
        if newfile and newfile != settings:
            settings = newfile
        if settings == get_text('c_newitem', self.get_lang()):
            self.newconf = True
            okmeld = 'new_conf_made'
        else:
            self.newconf = False
            okmeld = 'conf_loaded'
        mld = self.get_conf(settings)
        if mld == '':
            if newfile:
                self.newfile = ''
            self.settings = self.sitename = settings
            self.rstdata = conf2text(self.conf)
            mld = get_text(okmeld, self.get_lang()).format(self.settings)
            self.sitename = self.settings
        return mld, self.rstdata, self.settings, self.newfile

    def saveconf(self, settings, newfile, rstdata):
        """(re)save settings file using selected name

        if new name specified, use that
        """
        command = mld = ""
        newsett = settings
        if rstdata == "":
            mld = get_text('supply_text', self.get_lang())
        elif self.loaded != CONF:
            mld = get_text('conf_invalid', self.get_lang())
        if mld == '':
            if newfile and newfile != newsett:
                newsett = newfile
            if newsett == get_text('c_newitem', self.get_lang()):
                mld = get_text('fname_invalid', self.get_lang())
            elif self.newconf:
                mld, newurl = new_conf(newsett, rstdata, self.get_lang())
                if newurl:
                    rstdata = rstdata.replace("url: ''", "url: {}".format(newurl))
                    command = 'fabsrv modconfb -n hosts nginx.modconfb -n flatpages nginx.restart'
        if mld == "":
            mld = save_conf(newsett, rstdata, self.get_lang())
            if mld == '' and self.newconf:
                init_css(newsett)
        if mld == "":
            self.newfile = ''
            self.newconf = False
            self.settings = self.sitename = newsett
            mld = self.get_conf(self.settings)
            self.rstdata = rstdata = conf2text(self.conf)
        if mld == '':
            mld = get_text('conf_saved', self.get_lang()).format(self.settings)
            if command:
                mld += ' ' + get_text('activate_url', self.get_lang()).format(command)
            elif self.conf['url'] == '':
                mld += ' ' + get_text('note_no_url', self.get_lang())
        return mld, rstdata, self.settings, self.newfile

    def loadxtra(self):
        """load site directives file and show on page
        """
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
        mld = ''
        fname, verb = get_custom_directives_filename()
        verb = get_text(verb, self.get_lang())
        mld, data = read_data(fname)
        if not mld:
            self.rstdata = data
            self.loaded = XTRA
            mld = get_text('dirs_loaded', self.get_lang()).format(verb, fname)
        return mld, self.rstdata

    def savextra(self, rstdata):
        """(re)save site directives file
        """
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
        mld = ''
        if rstdata == "":
            mld = get_text('supply_text', self.get_lang())
        elif self.loaded != XTRA:
            mld = get_text('dirs_invalid', self.get_lang())
        if mld == "":
            mld = save_to(custom_directives, rstdata)  # standard file name
        if mld == "":
            mld = get_text('dirs_saved', self.get_lang())
        return mld

    def loadrst(self, rstfile):
        """load rest source into page
        """
        mld = ""
        if rstfile == "":
            mld = 'unlikely_1'
        elif rstfile.startswith('--'):
            if rstfile == get_text('c_newitem', self.get_lang()):
                self.rstdata = ''
            else:
                self.rstdata = read_tpl_data(self.sitename, rstfile.split()[1])
            mld = 'save_reminder'
            self.loaded = RST
            self.htmlfile = self.newfile = ""
        elif rstfile.endswith("/"):
            self.current = rstfile[:-1]
            self.rstdata = ""
            mld, fmtdata = 'chdir_down', self.current
            self.htmlfile = self.rstfile = ''
        elif rstfile == "..":
            self.current = ""
            self.rstdata = ""
            mld = 'chdir_up'
            self.htmlfile = self.rstfile = ''
        if not mld:
            mld, data = read_src_data(self.sitename, self.current, rstfile)
        if mld:
            self.oldtext = self.rstdata
            mld = get_text(mld, self.get_lang())
            if '{}' in mld:
                mld = mld.format(fmtdata)
        else:
            self.loaded = RST
            self.oldtext = self.rstdata = data
            self.rstfile = rstfile
            self.htmlfile = pathlib.Path(rstfile).stem + ".html"
            self.newfile = ""
            mld = get_text('src_loaded', self.get_lang()).format(rstfile)
        return mld, self.rstdata, self.htmlfile, self.newfile

    def rename(self, rstfile, newfile, rstdata):
        """rename `rstfile` to `newfile` by saving `rstdata` under a new name and deleting `rstfile`
        """
        # import pdb; pdb.set_trace()
        if newfile:
            if newfile.endswith('/') or newfile.endswith('.tpl'):
                mld = 'incorrect_name'
            else:
                mld = read_src_data(self.sitename, self.current, newfile)[0]
                mld = "new_name_taken" if not mld else ''
        else:
            mld = "new_name_missing"
        if mld == '':
            oldpath = pathlib.Path(rstfile)
            path = pathlib.Path(newfile)
            if path.suffix != ".rst":
                newfile = newfile + ".rst"
            mld = save_src_data(self.sitename, self.current, newfile, rstdata, True)
            mld = mld.replace('src_', 'new_')
        if mld == '':
            mld = mark_deleted(self.sitename, self.current, rstfile)
        if mld == '':
            mld = '{} renamed to {}'.format(str(oldpath), str(path))
            self.oldtext = self.rstdata = rstdata
            self.rstfile = newfile
            self.htmlfile = path.stem + ".html"
            self.newfile = ""
        mld = format_message(mld, self.get_lang(), newfile)
        return mld, self.rstfile, self.htmlfile, self.newfile, rstdata

    def revert(self, rstfile, rstdata):
        """revert `rstfile` to  backed up contents
        """
        if rstfile.endswith('/') or rstfile.endswith('.tpl'):
            mld = 'incorrect_name'
        else:
            mld = revert_src(self.sitename, self.current, rstfile)
            mld, rstdata = read_src_data(self.sitename, self.current, rstfile)
        if mld == "":
            path = pathlib.Path(rstfile)
            mld = '{} reverted to backup'.format(str(path))
            self.oldtext = self.rstdata = rstdata
            self.rstfile = rstfile
            self.htmlfile = path.stem + ".html"
            self.newfile = ""
        mld = format_message(mld, self.get_lang(), rstfile)
        return mld, self.rstfile, self.htmlfile, self.newfile, rstdata

    def delete(self, rstfile, rstdata):
        """(re)save rest source
        """
        if rstfile.endswith('/') or rstfile.endswith('.tpl'):
            mld = 'incorrect_name'
        else:
            fname = rstfile
            mld = read_src_data(self.sitename, self.current, rstfile)[0]
        if mld == '':
            mld = mark_deleted(self.sitename, self.current, rstfile)
        if mld == "":
            path = pathlib.Path(rstfile)
            rstdata = ''
            mld = '{} deleted'.format(str(path))
            self.oldtext = self.rstdata = rstdata
            self.rstfile = rstfile
            self.htmlfile = path.stem + ".html"
            self.newfile = ""
        mld = format_message(mld, self.get_lang(), rstfile)
        return mld, self.rstfile, self.htmlfile, self.newfile, rstdata

    def saverst(self, rstfile, newfile, rstdata):
        """(re)save rest source
        """
        if rstfile.startswith('-- ') and rstfile.endswith(' --'):
            rstfile = rstfile[3:-3]
        fname = newfile or rstfile
        if fname.endswith('/'):
            mld = make_new_dir(self.sitename, fname[:-1])
            msg_parameter = fname[:-1]
            if mld == "":
                self.oldtext = self.rstdata = rstdata
                mld = 'new_subdir'
                self.rstfile = fname
                self.newfile = ""

        elif fname.endswith('.tpl'):
            # NOTE: geen controle op `bestaat al`, bestaande data wordt zonder meer overschreven
            mld = save_tpl_data(self.sitename, fname, rstdata)
            msg_parameter = fname
            if mld == "":
                self.oldtext = self.rstdata = rstdata
                mld = 'tpl_saved'
                self.rstfile = self.htmlfile = ''
                self.newfile = ""

        else:
            path = pathlib.Path(rstfile)
            mld = check_if_rst(rstdata, self.loaded, fname)
            msg_parameter = fname
            if mld == '':
                oldpath = path
                path = pathlib.Path(fname)
                if path.suffix != ".rst":
                    fname = fname + ".rst"
                mld = save_src_data(self.sitename, self.current, fname, rstdata, bool(newfile))
            if mld == "":
                self.oldtext = self.rstdata = rstdata
                mld = 'rst_saved'
                self.rstfile = fname
                self.htmlfile = path.stem + ".html"
                self.newfile = ""

        mld = format_message(mld, self.get_lang(), msg_parameter)
        return mld, self.rstfile, self.htmlfile, self.newfile, rstdata

    def convert(self, rstfile, newfile, rstdata):
        """convert rest source to html and show on page
        """
        fname = newfile or rstfile
        rstdata = rstdata.replace('\r\n', '\n')
        if rstdata == self.oldtext:
            mld = check_if_rst(rstdata, self.loaded)  # alleen inhoud controleren
        else:
            mld = check_if_rst(rstdata, self.loaded, fname)
            if mld == '':
                # only if current text type == previous text type?
                mld = save_src_data(self.sitename, self.current, fname, rstdata)
        if mld == "":
            rstdata = preprocess_includes(self.sitename, self.current, rstdata)
            previewdata = rst2html(rstdata, self.conf['css'])
        else:
            mld = get_text(mld, self.get_lang())
            previewdata = fname = ''
        return mld, previewdata, fname

    def saveall(self, rstfile, newfile, rstdata):
        """convert rest source to html and save
        """
        fname = newfile or rstfile
        is_new_file = newfile != ""
        path = pathlib.Path(fname)
        if path.suffix in ('.html', ''):
            fname = path.stem + '.rst'
        mld = check_if_rst(rstdata, self.loaded, fname)
        if mld == '':
            self.rstfile = fname
            self.htmlfile = path.stem + ".html"
            if rstdata != self.oldtext or is_new_file:
                mld = save_src_data(self.sitename, self.current, self.rstfile,
                                    rstdata, is_new_file)
                if mld == "":
                    self.oldtext = self.rstdata = rstdata
            if mld == "":
                rstdata = preprocess_includes(self.sitename, self.current, rstdata)
                newdata = rst2html(rstdata, self.conf['css'])
                mld = save_html_data(self.sitename, self.current, self.htmlfile,
                                     newdata)
                if mld == "":
                    mld = 'rst_2_html'
                self.newfile = ""
        if mld:
            mld = get_text(mld, self.get_lang())
            if '{}' in mld:
                mld = mld.format(self.currentify(self.htmlfile))
        return mld, self.rstfile, self.htmlfile, self.newfile

    def loadhtml(self, htmlfile):
        """load the created html and show on page
        """
        mld = ""
        # perhaps we want the same changing directory behaviour as in loadrst?
        if htmlfile.endswith("/") or htmlfile in (
                "", "..", get_text('c_newitem', self.get_lang())):
            mld = 'html_name_missing'
        if mld == "":
            mld, data = read_html_data(self.sitename, self.current, htmlfile)
        if mld:
            mld = get_text(mld, self.get_lang())
        else:
            path = pathlib.Path(htmlfile)
            self.htmlfile = path.stem + '.html'
            self.rstfile = path.stem + ".rst"
            self.oldhtml = data.replace("&nbsp", "&amp;nbsp")
            self.rstdata = self.oldhtml
            mld = get_text('html_loaded', self.get_lang()).format(
                self.currentify(self.htmlfile))
            self.loaded = HTML
        return mld, self.rstdata, self.rstfile, self.htmlfile

    def showhtml(self, rstdata):
        """render the loaded html
        """
        fname = self.htmlfile
        ## if rstdata.replace('\r\n', '\n') == html.unescape(self.oldhtml):
        if html.escape(rstdata.replace('\r\n', '\n')) == html.escape(
                self.oldhtml).replace('&amp;', '&'):
            mld = check_if_html(rstdata, self.loaded)
        else:
            mld = check_if_html(rstdata, self.loaded, fname)
            if mld == '':
                mld = save_html_data(self.sitename, self.current, fname, rstdata)
        if mld:
            mld = get_text(mld, self.get_lang())
            newdata = fname = ''
        else:
            newdata = rstdata
        return mld, newdata, fname

    def savehtml(self, htmlfile, newfile, rstdata):
        """(re)save the html
        """
        if newfile:
            mld = 'html_name_wrong'
        else:
            mld = check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = get_text(mld, self.get_lang())
        else:
            newdata = rstdata  # striplines(rstdata)
            mld = save_html_data(self.sitename, self.current, htmlfile, newdata)
            if mld:
                mld = get_text(mld, self.get_lang())
            else:
                self.rstdata = newdata.replace("&nbsp", "&amp;nbsp")
                self.htmlfile = htmlfile
                mld = get_text('html_saved', self.get_lang()).format(
                    self.currentify(self.htmlfile))
            self.newfile = ""
        return mld, self.rstdata, self.newfile

    def copytoroot(self, htmlfile, rstdata):
        """copy html to mirror site

        along the way the right stylesheets are added
        """
        mld = check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = get_text(mld, self.get_lang())
        else:
            mld = save_to_mirror(self.sitename, self.current, htmlfile, self.conf)
            if not mld:
                self.htmlfile = htmlfile
                mld = get_text('copied_to', self.get_lang()).format(
                    'siteroot/' + self.currentify(self.htmlfile))
        return mld

    def makerefdoc(self):
        """create a document with reference links

        (this would be the actual index of the site but hey, HTML conventions)
        """
        use_sef = self.conf.get('seflinks', False)
        rstdata, has_err = TrefwoordenLijst(self.sitename, self.get_lang(), use_sef).build()
        if not rstdata:
            return (has_err, )
        dirname, docname = '', 'reflist'
        rstfile = docname + '.rst'
        htmlfile = docname + '.html'
        # assume it is new
        mld = save_src_data(self.sitename, dirname, rstfile, rstdata, new=True)
        if mld:  # if this goes wrong, simply try again assuming it is not new
            mld = save_src_data(self.sitename, dirname, rstfile, rstdata)
        if mld == "":
            newdata = rst2html(rstdata, self.conf['css'])
            mld = save_html_data(self.sitename, dirname, htmlfile, newdata)
            if mld == "":
                mld = save_to_mirror(self.sitename, dirname, htmlfile, self.conf)
        if not mld:
            mld = get_text('index_built', self.get_lang())
            if has_err:
                mld += ' ' + get_text('with_err', self.get_lang())
        self.loaded = RST
        return mld, rstfile, htmlfile, rstdata

    def convert_all(self, option='3'):
        """(re)generate all html documents and copy to mirror"""
        # optdict = {'0': 'all', '1': 'needed', '2': 'missing',
        #            '3': 'all (show)', '4': 'needed (show)', '5': 'missing (show)'}
        needed_only = option in ('1', '4')
        missing_only = option in ('2', '5')
        show_only = option in ('3', '4', '5')
        results = UpdateAll(self.sitename, self.conf, needed_only=needed_only,
                            missing_only=missing_only, show_only=show_only).go()
        data = []
        with open('/tmp/rhfn_convert_all', 'w') as f:
            for item in results:
                print(item, file=f)
        for fname, msgtype in results:
            msg = get_text(msgtype, self.get_lang())
            if '{}' in msg:
                data.append(msg.format(fname))
            else:
                data.append(fname + ': ' + msg)
        txt = get_text('in_sim', self.get_lang()) if show_only else ''
        mld = get_text('docs_converted', self.get_lang()).format(txt)
        return mld, '\n'.join(data)

    def search(self, search, replace):
        "do a search and optionally replace action for all documents on the site"
        # TODO: wat te doen bij een achterlijk groot aantal zoekresultaten (bv. bij zoeken op "de")?
        if replace:
            items_found = search_site(self.sitename, search, replace)
        else:
            items_found = search_site(self.sitename, search)
        results = searchdict2list(items_found, search)
        if results:
            mld = 'de onderstaande regels/regeldelen zijn {}:'
            hlp = 'vervangen' if replace else 'gevonden'
            mld = mld.format(hlp)
        else:
            mld = 'nothing found, no replacements' if replace else 'search phrase not found'
        return mld, results

    def check(self):
        """check css for classes / ids used by directives"""
        missing = check_directive_selectors(self.sitename)
        if missing:
            return get_text('clsid_missing', self.get_lang()).format(', '.join(missing))
        return get_text('clsid_ok', self.get_lang())

    def overview(self):
        """show the state of all site documents"""
        return build_progress_list(self.sitename)

    def copystand(self, data):
        """copy the overview to a file"""
        outfile = get_copystand_filepath(self.sitename)
        with outfile.open('w') as out:
            for docinfo in data:
                docinfo = get_progress_line_values(docinfo)
                print(';'.join(docinfo), file=out)
        return 'Overzicht geëxporteerd naar {}'.format(outfile)

# -- eof
