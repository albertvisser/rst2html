"""webapp om teksten in ReST formaat om te zetten naar HTML documenten

presentation layer
"""
# import sys
# import os
import pathlib
import datetime
import cherrypy
## sys.path.append('.')
import rst2html_functions as rhfn
HERE = pathlib.Path(__file__).parent
TEMPLATE = HERE / "rst2html.html"
previewbutton = ('<div style="border: 3px ridge #3a5fcd; border-radius:20px; '
                 'background-color: #C6E2FF; text-align: center; position: fixed">'
                 '<a href={}><button accesskey="b">'
                 '<span style="text-decoration:underline">B</span>ack to editor'
                 '</button></a></div>')
codemirror_stuff = ['<script src="/static/codemirror/lib/codemirror.js"></script>',
                    '<link rel="stylesheet" href="/static/codemirror/lib/codemirror.css"/>']
scriptspec = '<script src="/static/codemirror/mode/{}.js"></script>'
scriptdict = {'yaml': ('yaml/yaml',),
              'html': ('xml/xml', 'javascript/javascript', 'css/css',
                       'htmlmixed/htmlmixed'),
              'py': ('python/python', '../addon/edit/matchbrackets'),
              'rst': ('rst/rst', '../addon/mode/overlay')}
copybuttontext = """\
        <a href="/copysearch"><button accesskey="c">
                <span style="text-decoration:underline">C</span>opy to file</button></a>"""


def load_template(name):
    "load a template file from the base directory"
    template = HERE / name
    output = ''
    with template.open() as _in:
        output = _in.read()
    return output


def apply_lang(lines, state):
    "pas eigengebakken language support toe op tekstregels"
    output = []
    for line in lines:
        while '_(' in line:
            start, rest = line.split('_(', 1)
            keyword, end = rest.split(')', 1)
            line = rhfn.get_text(keyword, state.get_lang()).join((start, end))
        output.append(line)
    return '\n'.join(output)


def format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, state):
    """build page html out of various parameters and a template file
    """
    if state.newfile:
        all_source, all_html = [], []
    else:
        all_source = rhfn.list_files(state.sitename, state.current, rstfile, 'src')
        all_html = rhfn.list_files(state.sitename, state.current, htmlfile, 'dest')
    lines = load_template("rst2html.html").split('\n')
    output = apply_lang(lines, state)
    conflist = rhfn.list_confs(settings)
    format_stuff = ''
    if state.conf.get('highlight', False):
        format_stuff = ''.join(codemirror_stuff)
        if state.loaded:
            format_stuff += ''.join(scriptspec.format(x) for x in scriptdict[state.loaded])
    return output.format(all_source, all_html, newfile, mld, rstdata, state.conf['wid'],
                         state.conf['hig'], conflist, state.loaded, format_stuff)


def format_progress_list(timelist):
    """output the site inventory to html, accentuating the most recently updated
    items

    parts of this logic belong in the template, but since I'm not using a
    template engine I'm implementing it here
    """
    output = load_template('stand.html')
    first_part, rest = output.split('{% if data %}')
    data_part, last_part = rest.split('{% endif %}')
    repeat_part, no_data = data_part.split('{% else %}')
    thead, rest = repeat_part.split('{% for row in data %}')
    repeat_line, tfoot = rest.split('{% endfor %}')
    output = [first_part]
    if timelist:
        output.append(thead)
        for docinfo in timelist:
            line = repeat_line
            items = rhfn.get_progress_line_values(docinfo)
            line = line.replace('{row.0}', items[0])
            for idx, timestring in enumerate(items[1:]):
                timestring = timestring.replace('--> ', '<strong>').replace(' <--', '</strong>')
                line = line.replace('{row.%s}' % str(idx + 1), timestring)
            output.append(line)
        output.append(tfoot)
    else:
        output.append(no_data)
    output.append(last_part)
    return ''.join(output)


def resolve_images(rstdata, url, loc, use_sef=False, fname=''):
    """fix the urls in image links so that preview html points to the right place
    """
    # TODO: dit houdt er nog geen rekening mee dat hrefs die met / beginnen bedoeld zijn om
    # absoluut vanaf de siteroot geladen te worden? dat zit juist in
    data = []
    pos = rstdata.find('<img')
    if pos == -1:
        return rstdata
    while pos >= 0:
        pos2 = rstdata.find('src="', pos) + 5
        if rstdata[pos2:].startswith('http'):
            pos = pos2
        else:
            begin = rstdata[:pos2]
            # if begin.startswith('/'):
            #     begin = begin[1:]
            data.append(begin)
            rstdata = rstdata[pos2:]
            from_root = False
            if rstdata.startswith('/'):
                rstdata = rstdata[1:]
                from_root = True
            pos = 0
        pos = rstdata.find('<img', pos)
    data.append(rstdata)
    if url:
        url = url.rstrip('/') + '/'  # make sure url ends with one and only one /
    if loc:
        url += loc.strip('/') + '/'  # if present add loc with no double //'s
    if use_sef and fname and fname != 'index' and not from_root:
        url += fname + '/'
    return url.join(data)


def format_previewdata(state, previewdata, fname, ftype, settings):
    """
    Insert a "back to source" button into the HTML to show

    arg1 = previewdata: the html to show (text string)
    arg2 = filename parameter for the screen to return to
    arg3 = type of this file: `rst` or `html`
    """
    previewdata = resolve_images(previewdata, state.conf['url'], state.current,
                                 state.conf.get('seflinks', False),
                                 # fname.replace('.rst', '').replace('.html', ''))
                                 fname.replace('.' + ftype, ''))
    try:
        pos = previewdata.index('>', previewdata.index('<body')) + 1
    except ValueError:
        start, end = '', previewdata
    else:
        start, end = previewdata[:pos], previewdata[pos:]
    loadrst = '/load{0}/?{0}file={1}&settings={2}'.format(ftype, fname, settings)
    previewdata = previewbutton.format(loadrst).join((start, end))
    return previewdata


def format_search(results=None):
    "build search screen data"
    output = load_template('search.html')
    first_part, rest = output.split('{% if results %}')
    start, rest = rest.split('{% for row in data %}')
    line, rest = rest.split('{% endfor %}')
    end, last_part = rest.split('{% endif %}')
    output = [first_part]
    if results:
        output.append(start)
        for page, lineno, text in results:
            out = line.replace('{row.0}', page).replace('{row.1}', str(lineno)).replace('{row.2}',
                                                                                        text)
            output.append(out)
        output.append(end)
    output.append(last_part)
    return ''.join(output).replace(' **', '<strong>').replace('** ', '</strong>')


class Rst2Html:
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.state = rhfn.R2hState()

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)
        """
        rstfile, htmlfile, newfile, mld, rstdata, settings = self.state.index()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def loadconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata='', **kwargs):
        """load settings of indicated site
        """
        mld, rstdata, settings, newfile = self.state.loadconf(settings, newfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """(re)save settings for selected site name

        if new name specified, use that"""
        mld, rstdata, settings, newfile = self.state.saveconf(settings, newfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    # @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """load directives file for editing

        if non-existent, create from template
        """
        mld, rstdata = self.state.loadxtra()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    # @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """(re)save directives file
        """
        mld, rstdata = self.state.savextra(rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def loadrst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld, rstdata, htmlfile, newfile = self.state.loadrst(rstfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def saverst(self, settings="", rstfile="", newfile="", rstdata="", action='', **kwargs):
        """(re)save rst file using selected name

        if new name specified, use that (extension must be .rst)
        `action` has a value when rename or delete is checked
        """
        action = rhfn.translate_action(action)
        if action == 'rename':
            mld, rstfile, htmlfile, newfile, rstdata = self.state.rename(rstfile, newfile, rstdata)
        elif action == 'revert':
            mld, rstfile, htmlfile, newfile, rstdata = self.state.revert(rstfile, rstdata)
        elif action == 'delete':
            mld, rstfile, htmlfile, newfile, rstdata = self.state.delete(rstfile, rstdata)
        else:
            mld, rstfile, htmlfile, newfile, rstdata = self.state.saverst(rstfile, newfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile='', newfile="", rstdata="", **kwargs):
        """convert rst to html and show result
        """
        mld, previewdata, fname = self.state.convert(rstfile, newfile, rstdata)
        if mld == '':
            return format_previewdata(self.state, previewdata, fname, 'rst', settings)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def saveall(self, settings="", rstfile="", newfile="", rstdata="", **kwargs):
        """(re)save rst file, (re)convert to html and (re)save html file using selected names
        """
        mld, rstfile, htmlfile, newfile = self.state.saveall(rstfile, newfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """load html file and show code
        """
        mld, rstdata, rstfile, htmlfile = self.state.loadhtml(htmlfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """preview the loaded HTML
        """
        mld, previewdata, fname = self.state.showhtml(rstdata)
        if mld == '':
            return format_previewdata(self.state, previewdata, fname, 'html', settings)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def savehtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """save displayed (edited) html
        """
        mld, rstdata, newfile = self.state.savehtml(htmlfile, newfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """copy html to mirror site
        """
        mld = self.state.copytoroot(htmlfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def status(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        "get status for current document"
        mld = self.state.status(rstfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """build references document
        """
        savestuff = (rstfile, htmlfile, rstdata)
        result = self.state.makerefdoc()
        mld = result[0]
        if len(result) == 1:
            rstfile, htmlfile, rstdata = savestuff
        else:
            rstfile, htmlfile, rstdata = result[1:]
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def convert_all(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """regenerate all html files
        """
        regsubj = kwargs.get('regsubj', '')
        mld, rstdata = self.state.convert_all(option=regsubj)
        outdata = format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)
        selector_text = 'select name="regsubj"'
        begin, end = outdata.split(selector_text)
        option_text = 'value="{}"'.format(regsubj)
        new_end = end.replace(option_text, 'selected="selected" ' + option_text, 1)
        outdata = selector_text.join((begin, new_end))
        return outdata

    @cherrypy.expose
    def find_screen(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """start find/replace action: enter arguments
        """
        return format_search().format(settings, '', '', '', '')

    @cherrypy.expose
    def find_results(self, search="", replace=""):
        """execute find/replace action and show the results
        """
        if search:
            mld, results = self.state.search(search, replace)
            if mld in ('nothing found, no replacements', 'search phrase not found'):
                btntxt = ''
            else:
                btntxt = copybuttontext
                self.search_stuff = search, replace, results
        else:
            mld, results = 'Please tell me what to search for', []
            btntxt = ''
        return format_search(results).format(self.state.settings, btntxt, search, replace, mld)

    @cherrypy.expose
    def copysearch(self):
        """copy the search results to a file
        """
        msg = self.state.copysearch(self.search_stuff)
        btntxt = copybuttontext
        search, replace, results = self.search_stuff
        return format_search(results).format(self.state.settings, btntxt, search, replace, msg)

    @cherrypy.expose
    def check(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """check classes and ids from directives in css
        """
        mld = self.state.check()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, self.state)

    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata="", **kwargs):
        """output the site inventory to html, accentuating the most recently updated items
        """
        self.overviewdata = self.state.overview()
        return format_progress_list(self.overviewdata).format(settings, '')

    @cherrypy.expose
    def copystand(self):
        """copy the overview to a file
        """
        msg = self.state.copystand(self.overviewdata)
        return format_progress_list(self.overviewdata).format(self.state.sitename, msg)
