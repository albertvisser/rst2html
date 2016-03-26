# -*- coding: utf-8 -*-

"""
webapp om teksten in ReST formaat om te zetten naar HTML documenten
"""
import cherrypy
import sys
sys.path.append('.')
import os
import pathlib
import rst2html_functions as rhfn
HERE = pathlib.Path(__file__).parents[0]
TEMPLATE = HERE / "rst2html.html"
previewbutton = ('<div style="border: 3px ridge #3a5fcd; border-radius:20px; '
    'background-color: #C6E2FF; text-align: center; position: fixed">'
    '<a href={}><button>Back to editor</button></a></div>')

class Rst2Html(object):
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.conffile = 'settings.yml'
        self.current = ""
        self.oldtext = self.oldlang = self.oldhtml = ""

    def currentify(self, where):
        is_not_root = False
        if self.current:
            is_not_root = True
            where = where / self.current
        return where, is_not_root

    def all_source(self, naam):
        """build list of options from rst files"""
        path, not_root = self.currentify(self.conf['source'])
        ext = 'rst'
        return rhfn.list_files(path, not_root, naam, ext)

    def all_html(self, naam):
        """build list of options from html files"""
        path, not_root = self.currentify(self.conf['root'])
        ext = 'html'
        return rhfn.list_files(path, not_root, naam, ext)

    def scandocs(self):
        """scan alle brondocumenten op RefKey directives en bouw hiermee een
        trefwoordenregister op"""
        mld = ""
        rstdata = rhfn.build_trefwoordenlijst(self.conf['source'], self.conf["lang"])
        mld = rhfn.save_to(self.conf['source'] / 'trefwoorden.rst', rstdata)
        if mld == "":
            cssfile = str(self.conf['css'])
            newdata = rhfn.rst2html(rstdata, cssfile)
            begin, rest = str(newdata, encoding='utf-8').split(
                '<link rel="stylesheet"', 1)
            rest, end = rest.split(">", 1)
            newcss = '<link rel="stylesheet" href="{0}" type="text/css" />'.format(
                cssfile)
            newdata = newcss.join((begin, end))
            mld = rhfn.save_to(self.conf['root'] / "trefwoorden.html", newdata)
            if mld == "":
                mld = rhfn.save_to(self.conf['mirror'] / "trefwoorden.html",
                    cssfile.join((begin, end)))
        if not mld:
            mld = rhfn.get_text('index_built', self.conf["lang"])
        return mld

    def format_output(self, rstfile, htmlfile, newfile, mld, rstdata, settings):
        if self.oldlang != self.conf["lang"]:
            self.oldlang = self.conf["lang"]
        with TEMPLATE.open() as f_in:
            # eigengebakken language support
            output = []
            for line in f_in:
                while '_(' in line:
                    start, rest = line.split('_(', 1)
                    keyword, end = rest.split(')', 1)
                    line = rhfn.get_text(keyword, self.oldlang).join((start, end))
                output.append(line)
            self.output = ''.join(output)
        ## def lang(self):
        scriptspec = '<script src="/static/codemirror/mode/{}.js"></script>'
        scriptdict = {
            'yaml': ('yaml/yaml',),
            'html': ('xml/xml', 'javascript/javascript', 'css/css',
                'htmlmixed/htmlmixed'),
            'py': ('python/python', '../addon/edit/matchbrackets'),
            'rst': ('rst/rst', '../addon/mode/overlay'),
                }
        if not self.loaded:
            txtlang = ''
        else:
            txtlang = '\n'.join(scriptspec.format(x) for x in scriptdict[self.loaded])
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], rhfn.list_confs(settings), self.loaded, txtlang)

    def complete_header(self, rstdata):
        if self.conf.get('starthead', ''):
            split_on = '<head>' # + os.linesep
            start, end = rstdata.split(split_on, 1)
            ## middle = os.linesep.join(self.conf['starthead'])
            middle = self.conf['starthead']
            rstdata = start + split_on + middle + end
        if self.conf.get('endhead', ''):
            split_on = '</head>' # + os.linesep
            start, end = rstdata.split(split_on, 1)
            ## middle = os.linesep.join(self.conf['endhead'])
            middle = self.conf['endhead']
            rstdata = start + middle + split_on + end
        return rstdata

    def read_conf(self, settings):
        mld, conf = rhfn.read_conf(settings, self.conf["lang"])
        if mld == '':
            self.conf = conf
            self.subdirs = rhfn.list_subdirs(self.conf["source"])
            self.current = ""
        self.loaded = rhfn.CONF
        return mld

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        # config defaults so we can always show the first page
        self.conf = rhfn.DFLT_CONF
        rstfile = htmlfile = newfile = rstdata  = ""
        settings = self.conffile
        fullname = HERE / settings
        mld, rstdata = rhfn.read_data(fullname)
        if mld == '':
            mld = self.read_conf(settings)
            if mld == '':
                mld = rhfn.get_text('conf_init', self.conf["lang"]).format(fullname)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def loadconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .yml file

        changes the locations of source, target and web mirror files"""
        if newfile and newfile != settings:
            settings = newfile
        fullname = HERE / settings
        mld, rstdata = rhfn.read_data(fullname)
        if mld == '':
            mld = self.read_conf(settings)
            if mld == '':
                mld = rhfn.get_text('conf_loaded', self.conf["lang"]).format(
                    fullname)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save settings file using selected name

        if new name specified, use that (extension must be .yml)"""
        mld = ""
        if newfile:
            if newfile.endswith(os.pathsep):
                mld = rhfn.get_text('fname_invalid', self.conf["lang"])
            else:
                settings = newfile
                newfile = ""
        if mld == "":
            if rstdata == "":
                mld = rhfn.get_text('supply_text', self.conf["lang"])
            elif self.loaded != rhfn.CONF:
                mld = rhfn.get_text('conf_invalid', self.conf["lang"])
        if mld == "":
            fullname = HERE / settings
            test = ".yml"
            if fullname.suffix != test:
                fullname = fullname.with_suffix(test)
                settings += test
            rhfn.save_to(fullname, rstdata)
            settings = newfile
            newfile = ""
            mld = self.read_conf(fullname)
            if mld != '':
                rhfn.restore_file(fullname)
            else:
                mld = rhfn.get_text('conf_saved', self.conf["lang"]).format(
                    str(fullname))
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load directives file for editing

        if non-existent, create from template
        """
        mld = ''
        fname, verb = rhfn.get_custom_directives_filename(self.conf['lang'])
        mld, data = rhfn.read_data(fname)
        if not mld:
            rstdata = data
            self.loaded = rhfn.XTRA
            mld = rhfn.get_text('dirs_loaded', self.conf["lang"]).format(verb, fname)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save directives file
        """
        mld = ''
        if rstdata == "":
            mld = rhfn.get_text('supply_text', self.conf["lang"])
        elif self.loaded != rhfn.XTRA:
            mld = rhfn.get_text('dirs_invalid', self.conf["lang"])
        if mld == "":
            mld = rhfn.save_to(rhfn.custom_directives, rstdata)
        if mld == "":
            mld = rhfn.get_text('dirs_saved', self.conf["lang"])
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def loadrst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld = ""
        if rstfile == "":
            mld = rhfn.get_text('unlikely_1', self.conf["lang"])
        elif rstfile == "-- new --":
            mld = rhfn.get_text('save_reminder', self.conf["lang"])
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
            source = self.currentify(self.conf['source'])[0] / rstfile
            mld, data = rhfn.read_data(source)
        if not mld:
            self.loaded = rhfn.RST
            self.oldtext = rstdata = data
            htmlfile = source.with_suffix(".html").name
            newfile = ""
            mld = rhfn.get_text('src_loaded', self.conf["lang"]).format(str(source))
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def saverst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file using selected name

        if new name specified, use that (extension must be .rst)
        """
        fname = newfile or rstfile
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname, self.conf["lang"])
        if mld == "":
            where = self.currentify(self.conf['source'])[0]
            newpath = where / fname
            if newpath.suffix != ".rst":
                newfile += ".rst"
                newpath = where / newfile
            mld = rhfn.save_to(newpath, rstdata)
            if mld == "":
                mld = rhfn.get_text('rst_saved', self.conf["lang"]).format(
                    str(newpath.resolve()))
            rstfile = newpath.name
            htmlfile = newpath.with_suffix(".html").name
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """convert rst to html and show result
        """
        fname = newfile or rstfile
        if rstdata == self.oldtext:
            mld = rhfn.check_if_rst(rstdata, self.loaded, lang=self.conf["lang"]) # alleen inhoud controleren
        else:
            mld = rhfn.check_if_rst(rstdata, self.loaded, fname, self.conf["lang"])
        if mld == "":
            if rstdata != self.oldtext:
                mld = rhfn.save_to(
                    self.currentify(self.conf['source'])[0] / pathlib.Path(fname),
                    rstdata)
        if mld == "":
            previewdata = rhfn.rst2html(rstdata, self.conf['css'])
            previewdata = rhfn.resolve_images(previewdata, self.conf['mirror_url'],
                self.current, use_bytes=True)
            pos = previewdata.index(b'>', previewdata.index(b'<body')) + 1
            start, end = previewdata[:pos], previewdata[pos:]
            loadrst = 'loadrst?rstfile={}'.format(fname)
            preview = bytes(previewbutton.format(loadrst), encoding="UTF-8")
            previewdata = preview.join((start, end))
            return previewdata
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def saveall(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file, (re)convert to html and (re)save html file
        using selected names
        """
        fname = newfile or rstfile
        name, test = os.path.splitext(fname)
        if test in ('.html', ''):
            fname = name + '.rst'
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname, self.conf["lang"])
        if mld == "":
            newpath = pathlib.Path(fname)
            rstpath = newpath.with_suffix(".rst")
            htmlpath = newpath.with_suffix(".html")
            rstfile = self.currentify(self.conf['source'])[0] / rstpath
            htmlfile = self.currentify(self.conf['root'])[0] / htmlpath
            newdata = rhfn.rst2html(rstdata, self.conf['css'])
            if rstdata != self.oldtext:
                mld = rhfn.save_to(rstfile, rstdata)
            if mld == "":
                mld = rhfn.save_to(htmlfile, str(newdata, encoding='utf-8'))
                if mld == "":
                    mld = rhfn.get_text('rst_2_html', self.conf["lang"]).format(
                        str(htmlfile))
            rstfile = rstpath.name
            htmlfile = htmlpath.name
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = rhfn.get_text('html_name_missing', self.conf["lang"])
        else:
            htmlpath = pathlib.Path(htmlfile)
            rstfile = htmlpath.with_suffix(".rst")
        if mld == "":
            htmlfile = self.currentify(self.conf['root'])[0] / htmlpath
            mld, data = rhfn.read_data(htmlfile)
        if not mld:
            self.oldhtml = rstdata = data.replace("&nbsp", "&amp;nbsp")
            mld = rhfn.get_text('html_loaded', self.conf["lang"]).format(htmlfile)
            self.loaded = rhfn.HTML
            rstfile = rstfile.name
            htmlfile = htmlfile.name
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld = rhfn.check_if_html(rstdata, self.loaded, lang=self.conf["lang"])
        if mld:
            pass
        else:
            if 'mirror_url' in self.conf:
                newdata = rhfn.resolve_images(rstdata, self.conf['mirror_url'],
                    self.current)
            pos = newdata.index('>', newdata.index('<body')) + 1
            start, end = newdata[:pos], newdata[pos:]
            loadhtml = 'loadhtml?htmlfile={}'.format(htmlfile)
            newdata = previewbutton.format(loadhtml).join((start, end))
            return newdata
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def savehtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """save displayed (edited) html"""
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile, self.conf["lang"])
        if mld == "":
            htmlfile = self.currentify(self.conf['root'])[0] / htmlfile
            newdata = rstdata # striplines(rstdata)
            mld = rhfn.save_to(htmlfile, newdata)
            rstdata = newdata.replace("&nbsp", "&amp;nbsp")
            if mld == "":
                mld = rhfn.get_text('html_saved', self.conf["lang"]).format(
                    str(htmlfile))
            htmlfile = htmlfile.name
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile, self.conf["lang"])
        if not mld:
            rstdata = self.complete_header(rstdata)
            target = self.currentify(self.conf['mirror'])[0] / htmlfile
            mld = rhfn.save_to(target, rstdata)
            if not mld:
                x = "/" if self.current else ""
                mld = rhfn.get_text('copied_to', self.conf["lang"]).format(target)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        "build references document"
        mld = self.scandocs()
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def convert_all(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """regenerate all html files
        """
        # step 1: read source tree to determine files to be converted
        results = []
        pathlist = rhfn.determine_files(self.conf['source'], suffix='.rst')
        mld = ''
        for rstfile in pathlist:
            # bepaal de juiste pad namen
            htmlfile = rstfile.relative_to(self.conf['source']).with_suffix('.html')
            destfile = self.conf['mirror'] / htmlfile
            htmlfile = self.conf['root'] / htmlfile
            if not destfile.exists(): #only process files with target counterpart
                results.append(rhfn.get_text('target_missing').format(str(rstfile)))
                continue
            # lees de rst source en zet ze om
            with rstfile.open(encoding='utf-8') as f_in:
                rstdata = ''.join(f_in.readlines())
            newdata = rhfn.rst2html(rstdata, str(self.conf['css']))
            # nog wat aanpassingen en dan opslaan in target
            begin, rest = str(newdata, encoding='utf-8').split(
                '<link rel="stylesheet"', 1)
            rest, end = rest.split(">",1)
            newdata = self.conf['all_css'].join((begin, end))
            mld = rhfn.save_to(htmlfile, newdata)
            if mld:
                results.append(mld)
                continue
            if not destfile.exists(): #do not process files not on mirror site
                results.append(rhfn.get_text('mirror_missing',
                    self.conf["lang"]).format(str(htmlfile)))
                continue
            # nog wat aanpassingen en kopieren naar mirror
            data = self.complete_header(newdata)
            mld = rhfn.save_to(destfile, data)
            if mld:
                results.append(mld)
        rstdata = '\n'.join(results)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld, rstdata = rhfn.determine_most_recently_updated(settings,
            self.conf['lang'])
        if not mld:
            return rstdata.format(self.conf['mirror'], self.conf['source'],
                self.conf['root'], settings)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

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
