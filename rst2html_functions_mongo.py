# -*- coding: utf-8 -*-

import os
import shutil
import pathlib
import importlib
import inspect
import glob
import yaml
import datetime
## import gettext
import collections
import docs2mongo as dml
#
# docutils stuff (including directives
#
from docutils.core import publish_string
import docutils.parsers.rst as rd
standard_directives = {}
from directives_grid import StartCols, EndCols, FirstCol, NextCol, ClearCol, Spacer
standard_directives.update({
    "startc": StartCols,
    "endc": EndCols,
    "firstc": FirstCol,
    "nextc": NextCol,
    "clearc": ClearCol,
    "spacer": Spacer,
    })
from directives_magiokis import Bottom, RefKey
standard_directives.update({
    "bottom": Bottom,
    "refkey": RefKey,
    })
from directives_bitbucket import StartBody, NavLinks, TextHeader, EndBody, \
    StartMarginless, EndMarginless
standard_directives.update({
    "startbody": StartBody,
    "navlinks": NavLinks,
    "textheader": TextHeader,
    "startcenter": StartMarginless,
    "endcenter": EndMarginless,
    "endbody": EndBody,
    })

#
# internals
#
HERE = pathlib.Path(__file__).parents[0]
custom_directives = HERE / 'custom_directives.py'
custom_directives_template = HERE / 'custom_directives_template.py'
CSS_LINK = '<link rel="stylesheet" type="text/css" media="all" href="{}" />'
# settings stuff
DFLT_CONF = {'wid': 100, 'hig': 32, 'lang': 'en', 'url': '', 'css': []}
FULL_CONF = {'starthead': [], 'endhead': []}
FULL_CONF.update(DFLT_CONF)
SETT_KEYS = list(sorted(FULL_CONF.keys()))
# constants for loaded data
RST, HTML, CONF, XTRA = 'rst', 'html', 'yaml', 'py'
EXTS, LOCS = ['.rst', '.html'], ['src', 'dest']
EXT2LOC = dict(zip(EXTS, LOCS))
LOC2EXT = dict(zip(LOCS, EXTS))
#
# Language support : eigengebakken spul, tzt te vervangen door gnu_gettext zaken (of niet)
#
# map filenames (minus .lng suffix) to language codes
language_map = (
    ('english', 'en'),
    ('dutch', 'nl')
    )
# create dictionaries
languages = {}
for name, code in language_map:
    path = HERE / '{}.lng'.format(name)
    with path.open(encoding='utf-8') as _in:
        infodict = {}
        for line in _in:
            line = line.strip()
            if line == "" or line.startswith('#'): continue
            key, value = line.split(' = ', 1)
            infodict[key] = value
        languages[code] = infodict

# look up text
def get_text(keyword, lang=DFLT_CONF['lang']):
    data = languages[lang]
    return data[keyword]
## gettext stuff to use instead
## app_title = 'Rst2HTML'
## locale = HERE / 'locale'
## gettext.install(app_title, str(locale))
## languages = {'nl': gettext.translation(app_title, locale, languages=['nl']),
    ## 'en': gettext.translation(app_title, locale, languages=['en'])}
#--- rst related
def rst2html(data, css):
    """rst naar html omzetten en resultaat teruggeven"""
    overrides = {
        "embed_stylesheet": False,
        "stylesheet_path": '',
        "stylesheet": css,
        "report_level": 3,
        }
    return publish_string(source=data,
        destination_path="temp/omgezet.html",
        writer_name='html',
        settings_overrides=overrides,
        )

def register_directives():
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
            rd.directives.register_directive(directive_name, value)

def get_custom_directives_filename():
    if custom_directives.exists():
        fname = custom_directives
        verb = 'loaded'
    else:
        fname = custom_directives_template
        verb = 'init'
    return fname, verb

def resolve_images(rstdata, url, loc, use_bytes=False):
    data = []
    to_find = b'<img' if use_bytes else '<img'
    pos = rstdata.find(to_find)
    while pos >= 0:
        test = b'src="' if use_bytes else 'src="'
        pos2 = rstdata.find(test, pos) + 5
        begin = rstdata[:pos2]
        test = b'http' if use_bytes else 'http'
        if begin.startswith(test):
            pos = pos2
        else:
            test = b'/' if use_bytes else '/'
            if begin.startswith(test):
                begin = begin[:-1]
            data.append(begin)
            rstdata = rstdata[pos2:]
            pos = 0
        pos = rstdata.find(to_find, pos)
    data.append(rstdata)
    if not url.endswith('/'):
        url += '/'
    if loc:
        url += loc + '/'
    if use_bytes: url = bytes(url, encoding='utf-8')
    return url.join(data)

#--- site / conf related
def default_site():
    """return the first entry in the sites list to provide as default
    """
    return dml.list_sites()[0]

def new_conf(sitename):
    """create a new site definition including settings

    returns None on success, message on failure
    """
    mld = dml.create_new_site(sitename)
    if mld: return mld
    dml.update_settings(sitename, DFLT_CONF)
    dml.change_setting(sitename, "url", '/rst2html-data/{}'.format(sitename))
    return ''

def list_confs(sitename='', lang=DFLT_CONF['lang']):
    """build list of options containing all possible site settings

    if site name provided, show as "selected"""
    out = []
    for name in [get_text('c_newitem', lang)] + dml.list_sites():
        s = ' selected="selected"' if name == sitename else ''
        out.append("<option{}>{}</option>".format(s, name))
    return "".join(out)

def read_conf(naam):
    """read a config file; returns a dictionary of options
    """
    conf = dml.read_settings(naam)
    return conf

def conf2text(conf):
    return yaml.dump(conf, default_flow_style=False)

def save_conf(sitename, text, lang=DFLT_CONF['lang']):
    """convert text (from input area) to settings dict and return it

    TODO: also check settings for correctness (valid locations)
    """
    invalid = get_text('sett_invalid', lang)
    does_not_exist = invalid + " - " + get_text('no_such_sett', lang)
    # verplichte keys zitten in DFLT_CONF
    # controle: als int(FULL_CONF[x]) dan moet er een string waarde volgen
    #   als FULL_CONF[x] == [] dan moet er een list volgen
    #   anders moet het een enkele string zijn
    data = {}
    conf = {}
    fout = ''
    if dml.read_settings(sitename) is None:
        return get_text('no_such_sett', lang).format(sitename)
    # pass data through yaml to parse into a dict
    conf = yaml.safe_load(text) # let's be paranoid
    for key in DFLT_CONF: # check if obligatory keys are present
        if key not in conf:
            return does_not_exist.format(key, '')
    for key, value in FULL_CONF.items(): # check value for each key
        if key not in conf:
            continue
        if isinstance(value, int):
            try:
                int(conf[key])
            except ValueError:
                return invalid.format(key)
        elif key == 'lang' and conf[key] not in languages:
            return invalid.format(key)
        elif key == 'url' and conf[key] != '/rst2html-data/{}'.format(sitename):
            return get_text('not_the_url', lang)
    dml.update_settings(sitename, conf)
    return ''

#--- content related
def list_subdirs(sitename, ext=''):
    "list all subdirectories that contain the designated type of documents"
    if ext == '':
        ext = 'src'
    elif ext != 'src':
        ext = 'dest'
    test = dml.list_dirs(sitename, ext)
    if test is None: test = [] # 'Wrong type', but we can't return a message
    return [x + '/' for x in test]

def list_files(sitename, current='', naam='', ext='', lang=DFLT_CONF['lang']):
    """build list of options from filenames, with `naam` selected"""
    ext = ext or 'src'
    if naam:
        ext = os.path.splitext(naam)[1]
        if ext:
            ext = EXT2LOC[ext]
    if current:
        items = dml.list_docs(sitename, ext, directory=current)
    else:
        items = dml.list_docs(sitename, ext)
    if items is None:
        return 'Wrong type: `{}`'.format(ext)
    else:
        items = [x + LOC2EXT[ext] for x in items]
    items.sort()
    if current:
        items.insert(0,"..")
    else:
        items = list_subdirs(sitename, ext) + items
    items.insert(0, get_text('c_newitem', lang))
    out = []
    for f in items:
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{}>{}</option>".format(s, f))
    return "".join(out)

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

def _get_data(sitename, current, fname, origin):
    """returns the contents or propagates an exception
    """
    try:
        return dml.get_doc_contents(sitename, fname, origin, directory=current)
    except (AttributeError, FileNotFoundError):
        raise

def read_src_data(sitename, current, fname):
    """get source data from wherever it's been stored
    """
    fname, ext = os.path.splitext(fname)
    if ext not in ('', EXTS[0]):
        return 'Not a valid source file name', ''
    try:
        return '', _get_data(sitename, current, fname, 'src')
    except AttributeError:
        return 'src_name_missing', ''
    except FileNotFoundError:
        return 'Source file does not exist', ''

def read_html_data(sitename, current, fname):
    """get target data from wherever it's been stored
    """
    fname, ext = os.path.splitext(fname)
    if ext not in ('', EXTS[1]):
        return 'Not a valid target file name', ''
    try:
        return '', _get_data(sitename, current, fname, 'dest')
    except AttributeError:
        return 'html_name_missing', ''
    except FileNotFoundError:
        return 'Target file does not exist', ''

def check_if_rst(data, loaded, filename=None):
    """simple check if data contains rest
    assuming "loaded" indicates the current type of text

    if filename is filled, also check if it's a correct name
    """
    mld = ""
    if data == "":
        mld = 'supply_text'
    elif loaded != RST: # data.startswith('<'):
        mld = 'rst_invalid'
    elif filename is None:
        pass
    ## this is too much since we also cater for a name without extension in the right location
    ## test = os.path.splitext(filename)
    ## if test[0] == "" or test[1] != '.rst':
        ## mld = get_text('src_name_missing', DFLT_CONF['lang'])
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
    elif loaded != HTML: # not data.startswith('<'):
        mld = 'load_html'
    elif filename is None:
        pass
    ## this is too much since we also cater for a name without extension in the right location
    ## test = os.path.splitext(htmlfile)
    ## if test[0] == "" or test[1] != '.html':
        ## mld = get_text('html_name_missing', lang)
    elif filename.endswith("/") or filename in ("", "-- new --", ".."):
        mld = 'html_name_missing'
    return mld

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

def save_src_data(sitename, current, fname, data, new=False):
    "save the source data on the server"
    fname, ext = os.path.splitext(fname)
    if ext not in ('', EXTS[0]):
        return 'Not a valid source file name'
    if current and current + '/' not in list_subdirs(sitename):
        dml.create_new_dir(sitename, current)
    try:
        if new:
            dml.create_new_doc(sitename, fname, directory=current)
        dml.update_rst(sitename, fname, data, directory=current)
        return ''
    except AttributeError as e:
        if 'name' in str(e):
            return 'src_name_missing'
        if 'contents' in str(e):
            return 'supply_text '
        return str(e)
    except FileNotFoundError:
        return 'Source file does not exist'

def save_html_data(sitename, current, fname, data):
    "save the source data on the server"
    fname, ext = os.path.splitext(fname)
    if ext not in ('', EXTS[1]):
        return 'Not a valid target file name'
    try:
        dml.update_html(sitename, fname, data, directory=current)
        return ''
    except AttributeError as e:
        if 'name' in str(e):
            return 'html_name_missing'
        if 'contents' in str(e):
            return 'supply_text '
        return str(e)

def complete_header(conf, rstdata):
    if conf.get('starthead', ''):
        split_on = '<head>' # + os.linesep
        start, end = rstdata.split(split_on, 1)
        ## middle = os.linesep.join(self.conf['starthead'])
        middle = conf['starthead']
        rstdata = start + split_on + middle + end
    if conf.get('endhead', ''):
        split_on = '</head>' # + os.linesep
        start, end = rstdata.split(split_on, 1)
        ## middle = os.linesep.join(self.conf['endhead'])
        middle = conf['endhead']
        rstdata = start + middle + split_on + end
    return rstdata

def save_to_mirror(sitename, current, fname):
    """store the actual html on the server
    """
    fname, ext = os.path.splitext(fname)
    if ext not in ('', EXTS[1]):
        return 'Not a valid html file name'
    dirname = HERE /'rst2html-data' / sitename
    if current:
        dirname /= current # = dirname / current)
        mld, data = read_html_data(sitename, current, fname)
    else:
        mld, data = read_html_data(sitename, '', fname)
    if mld:
        return mld
    if not dirname.exists():
        dirname.mkdir(parents=True)
    mld = save_to(dirname / fname, data)
    try:
        dml.update_mirror(sitename, fname, directory=current)
        return ''
    except AttributeError as e:
        if 'name' in str(e):
            return 'html_name_missing'
        return str(e)

#-- progress list
def build_progress_list(sitename):
    result = []
    data = dml.get_all_doc_stats(sitename)
    for ix, diritem in enumerate(data):
        if diritem[0] == '/':
            rootitem = data.pop(ix)
            break
    data.sort()
    data.insert(0, rootitem)
    for dirname, docs in data:
        for docname, stats in sorted(docs):
            maxidx = stats.index(max(stats))
            result.append((dirname, docname, maxidx, stats))
    return result

#-- convert all
def update_files_in_dir(sitename, conf, dirname='', missing=False):
    errors = []
    items = dml.list_docs(sitename, 'src', directory=dirname)
    path = HERE /'rst2html-data' / sitename
    if dirname: path /= dirname
    for filename in items:
        msg, rstdata = read_src_data(sitename, dirname, filename)
        if not msg:
            msg, htmldata = read_html_data(sitename, dirname, filename)
            if msg:
                if missing:
                    msg = ''
                else:
                    msg = 'target_missing'
            else:
                htmldata = str(rst2html(rstdata, conf['css']), encoding='utf-8')
        if not msg:
            msg = save_html_data(sitename, dirname, filename, htmldata)
        if not msg:
            # copy to mirror MITS het file daar bestaat
            destfile = path / filename
            if not destfile.exists() and not missing:
                msg = 'mirror_missing'
            else:
                ## newdata = read_html_data(sitename, dirname, filename)
                ## data = complete_header(conf, newdata)
                data = complete_header(conf, htmldata)
                msg = save_to_mirror(sitename, dirname, filename)
        if msg:
            errors.append((filename, msg))
    return errors

def update_all(sitename, conf, missing=False):
    errors = update_files_in_dir(sitename, conf, missing=missing)
    all_dirs = dml.list_dirs(sitename, 'src')
    for dirname in all_dirs:
        errors.extend(update_files_in_dir(sitename, conf, dirname=dirname,
            missing=missing))
    return errors

#--- trefwoordenlijst
def get_reflinks_in_dir(sitename, dirname=''):
    """search for keywords in source file and remember their locations

    NOTE: references are only valid if they're in files that have already been
    converted to html,
    so the html timestamp must be present and greater than the rst timestamp
    """
    reflinks, errors = {}, []
    items = dml.list_docs(sitename, 'src', directory=dirname)
    for filename in items:
        stats = dml.get_doc_stats(sitename, filename, dirname='')
        if stats.src > stats.dest or stats.dest > stats.to_mirror:
            continue
        msg, rstdata = read_src_data(sitename, dirname, filename)
        if msg:
            errors.append((dirname, filename, msg))
            continue
        for line in rstdata.split('\n'):
            if line.startswith("..") and "refkey::" in line:
                x, refs = line.split("refkey::",1)
                for ref in (x.split(":") for x in refs.split(";")):
                    word = ref[0].strip().capitalize()
                    link = filename + '.html'
                    try:
                        link += "#" + ref[1].strip()
                    except IndexError:
                        pass
                    reflinks.setdefault(word, [])
                    reflinks[word].append(link)
    return reflinks, errors

def build_trefwoordenlijst(sitename, lang=DFLT_CONF['lang']):
    reflinks, errors = get_reflinks_in_dir(sitename)
    all_dirs = dml.list_dirs(sitename, 'src')
    for dirname in all_dirs:
        refs, errs = get_reflinks_in_dir(sitename)
        reflinks.update(refs)
        errors.extend(errs)
    current_letter = ""
    # produceer het begin van de pagina
    hdr = get_text('index_header', lang)
    data = [hdr, "=" * len(hdr), "", ""]
    titel, teksten, links, anchors = [], [], [], []
    for key in sorted(reflinks.keys()):
        if key[0] != current_letter:
            if titel:
                data.extend(titel)
                data.append("")
                data.extend(teksten)
                data.append("")
                data.extend(links)
                data.append("")
                data.extend(anchors)
                data.append("")
                titel, teksten, links, anchors = [], [], [], []
            # produceer het begin voor een letter
            current_letter = key[0]
            data[3] += "`{0}`_ ".format(current_letter)
            data.append("")
            titel = ["{0}".format(current_letter), "-"]
            linkno = 0
        # produceer het begin voor een nieuw trefwoord
        current_trefw = "+   {0}".format(key)
        for link in reflinks[key]:
            # produceer de tekst voor een link
            current_trefw += " `#`__ "
            linkno += 1
            linknm = current_letter + str(linkno)
            links.append("..  _{0}: {1}".format(linknm, link))
            anchors.append("__ {0}_".format(linknm))
        teksten.append(current_trefw)
    # produceer het eind van de pagina
    if teksten:
        data.extend(titel)
        data.append("")
        data.extend(teksten)
        data.append(" ")
        data.extend(links)
        data.append(" ")
        data.extend(anchors)
        data.append(" ")
    if errors:
        data.append('while creating this page, the following messages were generated:')
        data.append('----------------------------------------------------------------')
        for err in errors:
            data.append('. ' + err)
    return "\n".join(data)

class R2hState:

    def __init__(self):
        self.sitename = default_site()
        self.current = ""
        self.oldtext = self.oldlang = self.oldhtml = ""

    def currentify(self, fname):
        if self.current:
            fname = '/'.join((self.current, fname))
        return fname

    def read_conf(self, settings):
        # settings is hier de site naam
        conf = read_conf(settings)
        if conf is not None:
            mld = ''
            self.conf = conf
            self.subdirs = list_subdirs(settings, 'src')
            self.current = ""
            self.loaded = CONF
        else:
            mld = get_text('no_such_sett', self.conf["lang"]).format(settings)
        return mld

    def index(self):
        # config defaults so we can always show the first page
        self.conf = DFLT_CONF
        rstfile = htmlfile = newfile = rstdata = ""
        mld = self.read_conf(self.sitename)
        if mld == '':
            rstdata = conf2text(self.conf)
            mld = get_text('conf_init', self.conf["lang"]).format(self.sitename)
        return rstfile, htmlfile, newfile, mld, rstdata, self.sitename

    def loadconf(self, settings, newfile, rstdata):
        mld = ""
        rstdata = rstdata # create local version
        if newfile and newfile != settings:
            settings, newfile = newfile, ''
            ## mld = new_conf(settings) -- niks geen stilzwijgend nieuw aanmaken
        if mld == "":
            mld = self.read_conf(settings)
        if mld == '':
            rstdata = conf2text(self.conf)
            mld = get_text('conf_loaded', self.conf["lang"]).format(settings)
            self.sitename = settings
        return mld, rstdata, settings, newfile

    def saveconf(self, settings, newfile, rstdata):
        mld = ""
        newsett = settings
        if rstdata == "":
            mld = get_text('supply_text', self.conf["lang"])
        elif self.loaded != CONF:
            mld = get_text('conf_invalid', self.conf["lang"])
        if mld == '':
            if newfile:
                newsett, newfile = newfile, ""
                mld = new_conf(newsett)
            else:
                mld = save_conf(newsett, rstdata, self.conf["lang"])
        if mld == "":
            settings = newsett # only change this when successful
            mld = read_conf(settings)
            if self.oldlang != self.conf["lang"]:
                self.oldlang = self.conf["lang"]
        if mld == '':
            mld = get_text('conf_saved', self.conf["lang"]).format(settings)
        return mld, settings, newfile

    def loadxtra(self):
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
        mld = ''
        fname, verb = get_custom_directives_filename()
        verb = get_text(verb, self.conf['lang'])
        mld, data = read_data(fname)
        if not mld:
            rstdata = data
            self.loaded = XTRA
            mld = get_text('dirs_loaded', self.conf["lang"]).format(verb, fname)
        return mld, rstdata

    def savextra(self, rstdata):
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
        mld = ''
        if rstdata == "":
            mld = get_text('supply_text', self.conf["lang"])
        elif self.loaded != XTRA:
            mld = get_text('dirs_invalid', self.conf["lang"])
        if mld == "":
            mld = save_to(custom_directives, rstdata) # standard file name
        if mld == "":
            mld = get_text('dirs_saved', self.conf["lang"])
        return mld, rstdata

    def loadrst(self, rstfile):
        mld = ""
        if rstfile == "":
            mld = get_text('unlikely_1', self.conf["lang"])
        elif rstfile == "-- new --":
            mld = get_text('save_reminder', self.conf["lang"])
            htmlfile = newfile = rstdata = ""
        elif rstfile.endswith("/"):
            self.current = rstfile[:-1]
            rstdata = ""
            mld = " "
            htmlfile = rstfile
        elif rstfile == "..":
            self.current = ""
            rstdata = ""
            mld = " "
            htmlfile = rstfile
        if not mld:
            mld, data = read_src_data(self.sitename, self.current, rstfile)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            self.loaded = RST
            self.oldtext = rstdata = data
            htmlfile = os.path.splitext(rstfile)[0] + ".html"
            newfile = ""
            mld = get_text('src_loaded', self.conf["lang"]).format(rstfile)
        return mld, rstdata, htmlfile, newfile

    def saverst(self, rstfile, newfile, rstdata):
        fname = newfile or rstfile
        is_new_file = (newfile == "")
        mld = check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            if fname.suffix != ".rst":
                fname += ".rst"
            mld = save_src_data(self.sitename, self.current, fname, rstdata,
                is_new_file)
            if mld == "":
                mld = get_text('rst_saved', self.conf["lang"]).format(
                    self.currentify(fname))
            rstfile = fname
            htmlfile = os.path.basename(rstfile) + ".html"
            newfile = ""
        return mld, rstfile, htmlfile, newfile

    def convert(self, rstfile, newfile, rstdata):
        fname = newfile or rstfile
        if rstdata == self.oldtext:
            mld = rhfn.check_if_rst(rstdata, self.loaded) # alleen inhoud controleren
        else:
            mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            if rstdata != self.oldtext:
                mld = rhfn.save_src_data(self.sitename, self.current, fname,
                    rstdata, self.conf["lang"])
        if mld == "":
            previewdata = rhfn.rst2html(rstdata, self.conf['css'])
            previewdata = rhfn.resolve_images(previewdata, self.conf['url'],
                self.current, use_bytes=True)
            pos = previewdata.index(b'>', previewdata.index(b'<body')) + 1
            start, end = previewdata[:pos], previewdata[pos:]
            loadrst = 'loadrst?rstfile={}'.format(fname)
            preview = bytes(previewbutton.format(loadrst), encoding="UTF-8")
            previewdata = preview.join((start, end))
            return mld, previewdata
        else:
            return mld, (rstfile, newfile)

    def saveall(self, rstfile, newfile, rstdata):
        fname = newfile or rstfile
        name, test = os.path.splitext(fname)
        if test in ('.html', ''):
            fname = name + '.rst'
        mld = check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            rstfile = fname
            htmlfile = name + ".html"
            newdata = str(rst2html(rstdata, self.conf['css']), encoding='utf-8')
            if rstdata != self.oldtext:
                mld = save_src_data(self.sitename, self.current, rstfile, rstdata)
            if mld == "":
                mld = save_html_data(self.sitename, self.current, htmlfile, newdata)
                if mld == "":
                    mld = get_text('rst_2_html', self.conf["lang"]).format(
                        self.currentify(htmlfile))
            newfile = ""
        return mld, rstfile, htmlfile, newfile

    def loadhtml(self, htmlfile):
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = get_text('html_name_missing', self.conf["lang"])
        else:
            rstfile = os.path.basename(htmlfile) + ".rst"
        if mld == "":
            mld, data = read_html_data(self.sitename, self.current, htmlfile)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            self.oldhtml = rstdata = data.replace("&nbsp", "&amp;nbsp")
            mld = get_text('html_loaded', self.conf["lang"]).format(htmlfile)
            self.loaded = rhfn.HTML
        return mld, rstdata, rstfile

    def showhtml(self, rstdata):
        mld = rhfn.check_if_html(rstdata, self.loaded)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
            newdata = ''
        else:
            newdata = rhfn.resolve_images(rstdata, self.conf['url'], self.current)
            pos = newdata.index('>', newdata.index('<body')) + 1
            start, end = newdata[:pos], newdata[pos:]
            loadhtml = 'loadhtml?htmlfile={}'.format(htmlfile)
            newdata = previewbutton.format(loadhtml).join((start, end))
        return mld, newdata

    def savehtml(self, htmlfile, rstdata):
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            newdata = rstdata # striplines(rstdata)
            mld = save_html_data(self.sitename, self.current, htmlfile, newdata)
            rstdata = newdata.replace("&nbsp", "&amp;nbsp")
            if mld:
                mld = get_text(mld, self.conf["lang"])
            else:
                mld = get_text('html_saved', self.conf["lang"]).format(
                    self.currentify(htmlfile))
            newfile = ""
        return mld, rstdata, newfile

    def copytoroot(self, htmlfile, rstdata):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = get_text(mld, self.conf["lang"])
        else:
            rstdata = complete_header(self.conf, rstdata)
            mld = save_to_mirror(self.sitename, self.current, htmlfile, rstdata)
            if not mld:
                x = "/" if self.current else ""
                mld = rhfn.get_text('copied_to', self.conf["lang"]).format(
                    'siteroot/' + self.currentify(htmlfile))
        return mld, rstdata

    def makerefdoc(self):
        rstdata = build_trefwoordenlijst(sitename, self.conf["lang"])
        dirname, docname = '', 'reflist'
        mld = save_src_data(self.sitename, dirname, docname + 'rst', rstdata,
            new=True)
        if mld: # might not be present yet, so try again
            mld = save_src_data(self.sitename, dirname, docname + '.rst', rstdata)
        if mld == "":
            newdata = str(rst2html(rstdata, self.conf['css']), encoding='utf-8')
            mld = save_html_data(self.sitename, dirname, docname + '.html', newdata)
            if mld == "":
                mld = save_to_mirror(self.sitename, dirname, docname + '.html')
        if not mld:
            mld = get_text('index_built', self.conf["lang"])
        return mld, rstdata

    def convert_all(self):
        results = rhfn.update_all(self.sitename, self.conf["css"])
        return '\n'.join(results)

    def overview(self):
        return rhfn.build_progress_list(self.sitename)

#--- eof
