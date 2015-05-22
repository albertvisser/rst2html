# -*- coding: utf-8 -*-

import os
import shutil
import pathlib
import importlib
import inspect
import glob
import yaml
import datetime
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
from directives_bitbucket import StartBody, NavLinks, TextHeader, EndBody
standard_directives.update({
    "startbody": StartBody,
    "navlinks": NavLinks,
    "textheader": TextHeader,
    "endbody": EndBody,
    })

HERE = pathlib.Path(__file__).parents[0]
custom_directives = HERE / 'custom_directives.py'
custom_directives_template = HERE / 'custom_directives_template.py'
CSS_LINK = '<link rel="stylesheet" type="text/css" media="all" href="{}" />'
SETT_KEYS = ('root:', 'source:', 'css:', 'mirror:', 'all_css:', 'wid:', 'hig:',
    'starthead:', 'endhead:')

def register_directives():
    for name, func in standard_directives.items():
        rd.directives.register_directive(name, func)
    if custom_directives.exists():
        load_custom_directives()

def striplines(data):
    """list -> string met verwijdering van eventuele line endings"""
    return "".join([line.rstrip() for line in data])

def rst2html(data, css, embed=False):
    """rst naar html omzetten en resultaat teruggeven"""
    overrides = {
        "embed_stylesheet": embed,
        "stylesheet_path": css,
        "report_level": 3,
        }
    return publish_string(source=data,
        destination_path="temp/omgezet.html",
        writer_name='html',
        settings_overrides=overrides,
        )

def save_to(fullname, data):
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

def list_all(inputlist, naam):
    """build list of options from filenames, with naam selected"""
    out = []
    for f in inputlist:
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{1}>{0}</option>".format(f, s))
    return "".join(out)

def list_confs(naam):
    """build list of options containing all settings files in current directory"""
    out = []
    for path in HERE.glob('settings*.yml'):
        f = path.name
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{1}>{0}</option>".format(f, s))
    return "".join(out)

def determine_files(where='', suffix=''):
    def descend(root):
        locals = []
        for name in root.iterdir():
            skip = False
            if name.is_dir() and not name.is_symlink():
                locals.extend(descend(name))
            elif name.is_file() and (suffix == '' or name.suffix == suffix):
                locals.append(name)
        return locals
    if not where:
        where = pathlib.Path('.')
    rstfiles = descend(where)
    return rstfiles

def make_path(root, path):
    if path == 'root':
        path = pathlib.Path(root)
    elif path.startswith('root + '):
        path = path.split(' + ', 1)[1]
        path = pathlib.Path(root) / path
        path = path.resolve()
    else:
        path = pathlib.Path(path)
    return path

def read_conf(naam, debug=False):
    """read a config file; returns //conf//, a dictionary of options"""
    invalid = 'Config: invalid value for {}'
    does_not_exist = invalid + ' {} does not exist'
    test = HERE / naam
    with test.open() as _in:
        conf = yaml.load(_in)
    conf['root'] = pathlib.Path(conf['root'])
    if not conf['root'].exists():
        return does_not_exist.format('"root":', conf['root'])
    conf['source'] = make_path(conf['root'], conf['source'])
    if not conf['source'].exists():
        return does_not_exist.format('"source":', conf['source'])
    conf['css'] = make_path(conf['root'], conf['css'])
    if not conf['css'].exists():
        return does_not_exist.format('"css":', conf['css'])
    conf['mirror'] = make_path(conf['root'], conf['mirror'])
    if not conf['mirror'].exists():
        return invalid.format("mirror")
    csslinks = ''
    try:
        for x in conf['all_css']:
            if csslinks:
                csslinks += '\n'
            csslinks += CSS_LINK.format(x)
    except ValueError:
        return invalid.format("all_css")
    conf['all_css'] = csslinks
    try:
        conf['wid'] = int(conf['wid'])
    except ValueError:
        return invalid.format("wid")
    try:
        conf['hig'] = int(conf['hig'])
    except ValueError:
        return invalid.format("hig")
    return conf

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
        verb = 'opgehaald'
    else:
        fname = custom_directives_template
        verb = 'initieel aangemaakt, nog niet opgeslagen'
    return fname, verb

def css_link2file(text):
    x, y = CSS_LINK.split('{}')
    text = text.replace(x, '  - ')
    text = text.replace(y, '')
    return text

def zetom_conf(text):
    data = []
    for line in text.split(os.linesep):
        probeer = line.strip().split(': ')
        if len(probeer) > 1:
            sleutel = probeer[0] + ":"
            data.append([SETT_KEYS.index(sleutel), sleutel,
                [css_link2file(probeer[1])]])
        else:
            data[-1][2].append(css_link2file(probeer[0]))
    data.sort()
    for ix, item in enumerate(data):
        seq, key, value = item
        if key == SETT_KEYS[0]:     # root
            ## rootparts = value[0].split('/')
            rootparts = pathlib.Path(value[0]).parts
        elif key in SETT_KEYS[1:4]: # ander path
            ## textparts = value[0].split('/')
            textparts = pathlib.Path(value[0]).parts
            if textparts[:2] != rootparts[:2]: # skip comparison if toplevels differ
                continue
            if len(rootparts) < len(textparts): # get smallest number of subdirs
                max = len(rootparts)
            else:
                max = len(textparts)
            i = 0
            while (i < max and textparts[i] == rootparts[i]):
                i += 1
            textparts = ['..'] * (len(rootparts) - i) + list(textparts[i:])
            value = 'root'
            if textparts:
                value += ' + ' + '/'.join(textparts)
            data[ix] = seq, key, [value]
    lines = []
    for _, key, value in data:
        if key == SETT_KEYS[4]:
            lines.append(key)
            for y in value:
                lines.append(y)
        else:
            lines.append(key + ' ' + value[0])
    return os.linesep.join(lines) + os.linesep

def getrefs(path, source, reflinks):
    "search for keywords in source file and remember their locations"
    if path.is_dir():
        for path in path.iterdir():
            getrefs(path, source, reflinks)
    elif path.suffix == ".rst":
        doc = str(path.relative_to(source).with_suffix('.html'))
        with path.open(encoding='latin-1') as f_in:
            for line in f_in:
                if line.startswith("..") and "refkey::" in line:
                    x, refs = line.split("refkey::",1)
                    for ref in (x.split(":") for x in refs.split(";")):
                        word = ref[0].strip().capitalize()
                        link = doc
                        try:
                            link += "#" + ref[1].strip()
                        except IndexError:
                            pass
                        reflinks.setdefault(word, [])
                        reflinks[word].append(link)

def build_trefwoordenlijst(path):
    reflinks = {}
    for file in path.iterdir():
        getrefs(file, path, reflinks)
    current_letter = ""
    # produceer het begin van de pagina
    data = [
        "Trefwoordenlijst",
        "================",
        "",
            ""
        ]
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
    return "\n".join(data)

def build_file_list(path, ext):
    """returns a list of files with a given extension under a given path
    (1 subdirectory deep)
    """
    items = []
    for p in path.iterdir():
        if p.is_file() and str(p).endswith(ext):
            ptime = p.stat().st_mtime # atime / ctime
            items.append((str(p.relative_to(path)), ptime))
        elif p.is_dir():
            for pp in p.iterdir():
                if pp.is_file() and str(pp).endswith(ext):
                    ptime = pp.stat().st_mtime # atime / ctime
                    items.append((str(pp.relative_to(path)), ptime))
    return items

class Compare:
    """Compare three lists of files with their last changetimes
    """

    def __init__(self, list1, list2, list3):
        self.list = [None, sorted(list1), sorted(list2), sorted(list3)]
        self.idx = [None, -1, -1, -1]
        self.item = [None, None, None, None]
        self.sentinel = 'ZZZZZZZZZZ'
        for ix in range(1,4):
            self.item[ix] = self.get_next_item_from_list(ix)
        # strictly speaking, this is not the highest possible value, but close enough

    def get_next_item_from_list(self, num):
        """return filename without extension with index in list
        """
        seq = self.idx[num]
        seq += 1
        if seq >= len(self.list[num]):
            name = self.sentinel
        else:
            name = self.list[num][seq][0].split('.', 1)[0]
            self.idx[num] = seq
        return name, seq

    def get_next_smallest_items(self):
        """returns a list and gets the names for the next comparison"""
        result = []
        if self.item[1][0] < self.item[2][0]:
            if self.item[1][0] < self.item[3][0]:
                result = [(1, self.item[1])]
                self.item[1] = self.get_next_item_from_list(1)
            elif self.item[1][0] == self.item[3][0]:
                result = [(1, self.item[1]), (3, self.item[3])]
                self.item[1] = self.get_next_item_from_list(1)
                self.item[3] = self.get_next_item_from_list(3)
            elif self.item[1][0] > self.item[3][0]:
                result = [(3, self.item[3])]
                self.item[3] = self.get_next_item_from_list(3)
        elif self.item[1][0] == self.item[2][0]:
            if self.item[1][0] < self.item[3][0]:
                result = [(1, self.item[1]), (2, self.item[2])]
                self.item[1] = self.get_next_item_from_list(1)
                self.item[2] = self.get_next_item_from_list(2)
            elif self.item[1][0] == self.item[3][0]:
                result = [(1, self.item[1]), (2, self.item[2]), (3, self.item[3])]
                self.item[1] = self.get_next_item_from_list(1)
                self.item[2] = self.get_next_item_from_list(2)
                self.item[3] = self.get_next_item_from_list(3)
            elif self.item[1][0] > self.item[3][0]:
                result = [(3, self.item[3])]
                self.item[3] = self.get_next_item_from_list(3)
        elif self.item[1][0] > self.item[2][0]:
            if self.item[2][0] < self.item[3][0]:
                result = [(2, self.item[2])]
                self.item[2] = self.get_next_item_from_list(2)
            elif self.item[2][0] == self.item[3][0]:
                result = [(2, self.item[2]), (3, self.item[3])]
                self.item[2] = self.get_next_item_from_list(2)
                self.item[3] = self.get_next_item_from_list(3)
            elif self.item[2][0] > self.item[3][0]:
                result = [(3, self.item[3])]
                self.item[3] = self.get_next_item_from_list(3)
        return result

# vergelijk de lijsten (datum/tijd)
def compare_lists(list1, list2, list3):
    """Compare three lists of files with datetimes into one ordered list
    of filenames with dates and a number indicating the most recent date
    """
    workitem = Compare(list1, list2, list3)
    lists = (sorted(list1), sorted(list2), sorted(list3))
    timeslist = []
    while True:
        test = workitem.get_next_smallest_items()
        if all([x[1][0] == workitem.sentinel for x in test]):
            break
        times = ['', '', '']
        name = test[0][1][0]
        maxtime = 0
        for listno, item in test:
            _, indx = item
            mtime = lists[listno - 1][indx][1]
            if int(mtime) >= maxtime:
                maxtime = int(mtime)
                maxindex = listno
            times[listno - 1] = datetime.datetime.fromtimestamp(mtime).strftime(
                '%d-%m-%Y %H:%M:%S')
        line = [name]
        for mtime in times:
            line.append(mtime or 'n/a')
        line.append(maxindex)
        timeslist.append(line)
    return timeslist

def determine_most_recently_updated(settingsfile):
    """output the site inventory to html, accentuating the most recently updated
    items
    parts of this logic belong in the template, but since I'm not using a template
    engine I'm implementing it here"""
    opts = read_conf(settingsfile)
    source = build_file_list(opts['source'], '.rst')
    target = build_file_list(opts['root'], '.html')
    mirror = build_file_list(opts['mirror'], '.html')
    timelist = compare_lists(source, target, mirror)
    template = HERE / 'stand.html'
    with template.open() as _in:
        output = _in.read()
    first_part, rest = output.split('{% for row in data %}')
    repeat_line, last_part = rest.split('{% endfor %}')
    output = [first_part]
    for row in timelist:
        line = repeat_line
        for idx, word in enumerate(row[:-1]):
            if idx == row[-1]:
                word = word.join(('<strong>', '</strong>'))
            line = line.replace('{row.%s}' % idx, word)
        output.append(line)
    output.append(last_part)
    return ''.join(output)

