# -*- coding: utf-8 -*-

"""
webapp om teksten in ReST formaat om te zetten naar HTML documenten
"""
import cherrypy
import sys
sys.path.append('.')
import os
import pathlib
import datetime
import rst2html_functions_mongo as rhfn
HERE = pathlib.Path(__file__).parents[0]
TEMPLATE = HERE / "rst2html.html"
previewbutton = ('<div style="border: 3px ridge #3a5fcd; border-radius:20px; '
    'background-color: #C6E2FF; text-align: center; position: fixed">'
    '<a href={}><button>Back to editor</button></a></div>')
scriptspec = '<script src="/static/codemirror/mode/{}.js"></script>'
scriptdict = {
    'yaml': ('yaml/yaml',),
    'html': ('xml/xml', 'javascript/javascript', 'css/css',
        'htmlmixed/htmlmixed'),
    'py': ('python/python', '../addon/edit/matchbrackets'),
    'rst': ('rst/rst', '../addon/mode/overlay'),
        }

def format_output(rstfile, htmlfile, newfile, mld, rstdata, settings, state):
    """build page html out of various parameters and a template file
    """
    if state.newfile:
        all_source , all_html = [], []
    else:
        all_source = rhfn.list_files(state.sitename, state.current, rstfile, 'src',
            state.conf["lang"])
        all_html = rhfn.list_files(state.sitename, state.current, htmlfile, 'dest',
            state.conf["lang"])
    with TEMPLATE.open() as f_in:
        # eigengebakken language support
        output = []
        for line in f_in:
            while '_(' in line:
                start, rest = line.split('_(', 1)
                keyword, end = rest.split(')', 1)
                line = rhfn.get_text(keyword, state.conf["lang"]).join(
                    (start, end))
            output.append(line)
        output = ''.join(output)
    conflist = rhfn.list_confs(settings)
    if not state.loaded:
        txtlang = ''
    else:
        txtlang = '\n'.join(
            scriptspec.format(x) for x in scriptdict[state.loaded])
    return output.format(all_source, all_html, newfile, mld, rstdata,
        state.conf['wid'], state.conf['hig'], conflist, state.loaded, txtlang)

def format_progress_list(timelist):
    """output the site inventory to html, accentuating the most recently updated
    items

    parts of this logic belong in the template, but since I'm not using a
    template engine I'm implementing it here
    """
    template = HERE / 'stand_dml.html'
    with template.open() as _in:
        output = _in.read()
    first_part, rest = output.split('{% for row in data %}')
    repeat_line, last_part = rest.split('{% endfor %}')
    output = [first_part]
    for docinfo in timelist:
        line = repeat_line
        if docinfo[0] == '/':
            docname = docinfo[1]
        else:
            docname = '/'.join(docinfo[:2])
        maxidx, stats = docinfo[2:]
        line = line.replace('{row.0}', docname)
        for idx, dts in enumerate(stats):
            if dts == datetime.datetime.min:
                timestring = "n/a"
            else:
                timestring = dts.strftime('%d-%m-%Y %H:%M:%S')
            if idx == maxidx:
                timestring = timestring.join(('<strong>', '</strong>'))
            line = line.replace('{row.%s}' % str(idx + 1), timestring)
        output.append(line)
    output.append(last_part)
    return ''.join(output)

def resolve_images(rstdata, url, loc):
    """fix the urls in image links so that preview html points to the right place
    """
    data = []
    pos = rstdata.find('<img')
    while pos >= 0:
        pos2 = rstdata.find('src="', pos) + 5
        if rstdata[pos2:].startswith('http'):
            pos = pos2
        else:
            begin = rstdata[:pos2]
            if begin.startswith('/'):
                begin = begin[1:]
            data.append(begin)
            rstdata = rstdata[pos2:]
            if rstdata.startswith('/'):
                rstdata = rstdata[1:]
            pos = 0
        pos = rstdata.find('<img', pos)
    data.append(rstdata)
    url = url.rstrip('/') + '/' # make sure url ends with one and only one /
    if loc:
        url = url + loc.strip('/') + '/' # if present add loc with no double //'s
    return url.join(data)

def format_previewdata(state, previewdata, fname, ftype):
    """
    Insert a "back to source" button into the HTML to show

    arg1 = previewdata: the html to show (utf-8 string)
    arg2 = filename parameter for the screen to return to
    arg3 = type of this file: `rst` or `html`
    """
    previewdata = resolve_images(previewdata, state.conf['url'], state.current)
    pos = previewdata.index('>', previewdata.index('<body')) + 1
    start, end = previewdata[:pos], previewdata[pos:]
    loadrst = 'load{0}?{0}file={1}'.format(ftype, fname)
    previewdata = previewbutton.format(loadrst).join((start, end))
    return previewdata

class Rst2Html(object):
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.state = rhfn.R2hState()

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        rstfile, htmlfile, newfile, mld, rstdata, settings = self.state.index()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def loadconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load settings of indicated site

        "create new" is deliberatily hidden by not providing a -- new -- option
        """
        mld, rstdata, settings, newfile = self.state.loadconf(settings, newfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save settings for selected site name

        if new name specified, use that"""
        mld, rstdata, settings, newfile = self.state.saveconf(settings, newfile,
            rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

 #   @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load directives file for editing

        if non-existent, create from template
        """
        mld, rstdata = self.state.loadxtra()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

 #   @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save directives file
        """
        mld, rstdata = self.state.savextra(rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def loadrst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld, rstdata, htmlfile, newfile = self.state.loadrst(rstfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def saverst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file using selected name

        if new name specified, use that (extension must be .rst)
        """
        mld, rstfile, htmlfile, newfile = self.state.saverst(rstfile, newfile,
            rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """convert rst to html and show result
        """
        mld, previewdata, fname = self.state.convert(rstfile, newfile, rstdata)
        if mld == '':
            return format_previewdata(self.state, previewdata, fname, 'rst')
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def saveall(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file, (re)convert to html and (re)save html file
        using selected names
        """
        mld, rstfile, htmlfile, newfile = self.state.saveall(rstfile, newfile,
            rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load html file and show code"""
        mld, rstdata, rstfile, htmlfile = self.state.loadhtml(htmlfile)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld, previewdata, fname = self.state.showhtml(rstdata)
        if mld == '':
            return format_previewdata(self.state, previewdata, fname, 'html')
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def savehtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """save displayed (edited) html"""
        mld, rstdata, newfile = self.state.savehtml(htmlfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld, rstdata = self.state.copytoroot(htmlfile, rstdata)
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        "build references document"
        mld, rstdata = self.state.makerefdoc()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def convert_all(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """regenerate all html files
        """
        mld = ""
        rstdata = self.state.convert_all()
        return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            self.state)

    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """output the site inventory to html, accentuating the most recently updated
        items
        """
        data = self.state.overview()
        return format_progress_list(data).format(settings)
        ## if not mld:
            ## return rstdata.format(settings)
        ## return format_output(rstfile, htmlfile, newfile, mld, rstdata, settings,
            ## self.state)

if __name__ == "__main__":
    ## domain = "pythoneer" if len(sys.argv) == 1 else sys.argv[1]
    ## cherrypy.quickstart(Rst2Html())
    cherrypy.quickstart(Rst2Html(), config={
        "global": {
            # 'server.socket_host': 'rst2html.{0}.nl'.format(domain),
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 8099,
            },
        "/": {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
            },
        "/static": {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "./static",
            },
        })
