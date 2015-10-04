#! /usr/bin/env python3
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
list_confs = rhfn.list_confs        # only because it's in all the views's return statement
HERE = pathlib.Path(__file__).parents[0]
TEMPLATE = HERE / "rst2html.html"
previewbutton = ('<div style="border: 3px ridge #3a5fcd; border-radius:20px; '
    'background-color: #C6E2FF; text-align: center; position: fixed">'
    '<a href={}><button>Back to editor</button></a></div>')
# TODO: a simple "position:fixed" causes this div to shrink and cover the leftmost bit of the
# page - do I mind?

class Rst2Html(object):
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.conffile = 'settings.yml'
        self.conf = rhfn.read_conf(self.conffile)
        self.get_subdirs()
        self.current = ""
        self.oldtext = self.oldhtml = ""
        with TEMPLATE.open() as f_in:
            ## self.output = f_in.read()
            # eigengebakken language support
            output = []
            for line in f_in:
                while '_(' in line:
                    start, rest = line.split('_(', 1)
                    keyword, end = rest.split(')', 1)
                    line = rhfn.get_text(keyword).join((start, end))
                output.append(line)
            self.output = ''.join(output)


    def get_subdirs(self):
        self.subdirs = [str(f.relative_to(self.conf['source'])) + "/"
            for f in self.conf['source'].iterdir() if f.is_dir()]

    def currentify(self, where):
        if self.current:
            where = where / self.current
        return where

    def all_source(self, naam):
        """build list of options from rst files"""
        path = self.currentify(self.conf['source'])
        all_source = [str(f.relative_to(path)) # self.conf['source']))
            for f in path.glob("*.rst")]
        items = sorted(all_source)
        if self.current:
            items.insert(0,"..")
        else:
            items = self.subdirs + items
        return rhfn.list_all(items, naam)

    def all_html(self, naam):
        """build list of options from html files"""
        path = self.currentify(self.conf['root'])
        all_html = [str(f.relative_to(path)) # self.conf['root']))
            for f in path.glob("*.html")]
        items = sorted(all_html)
        if self.current:
            items.insert(0,"..")
        else:
            items = self.subdirs + items
        return rhfn.list_all(items, naam)

    def scandocs(self):
        """scan alle brondocumenten op RefKey directives en bouw hiermee een
        trefwoordenregister op"""
        mld = ""
        rstdata = rhfn.build_trefwoordenlijst(self.conf['source'])
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
            mld = rhfn.get_text('index_built')
        return mld

    def lang(self):
        scriptspec = '<script src="/static/codemirror/mode/{}.js"></script>'
        scriptdict = {
            'yaml': ('yaml/yaml',),
            'html': ('xml/xml', 'javascript/javascript', 'css/css',
                'htmlmixed/htmlmixed'),
            'py': ('python/python', '../addon/edit/matchbrackets'),
            'rst': ('rst/rst', '../addon/mode/overlay')
                }
        return '\n'.join(scriptspec.format(x) for x in scriptdict[self.loaded])

    def complete_header(self, rstdata):
        if self.conf.get('starthead', ''):
            split_on = '<head>' # + os.linesep
            start, end = rstdata.split(split_on, 1)
            middle = os.linesep.join(self.conf['starthead'])
            rstdata = start + split_on + middle + end
        if self.conf.get('endhead', ''):
            split_on = '</head>' # + os.linesep
            start, end = rstdata.split(split_on, 1)
            middle = os.linesep.join(self.conf['endhead'])
            rstdata = start + middle + split_on + end
        return rstdata

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        ## return self.output
        rstfile = htmlfile = newfile = rstdata  = ""
        settings = self.conffile
        mld = rhfn.get_text('conf_init').format(settings)
        rstdata = '\n'.join(['{}: {}'.format(x,y) for x, y in self.conf.items()]) # ""
        self.loaded = rhfn.CONF
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def loadconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .yml file

        changes the locations of source, target and web mirror files"""
        mld = ''
        test = rhfn.read_conf(settings)
        try:
            test['root']
        except TypeError:
            mld = test
        if not mld:
            self.conf = test
            self.get_subdirs()
            self.current = ""
            rstdata = '\n'.join(['{}: {}'.format(x,y) for x, y in self.conf.items()]) # ""
            self.loaded = rhfn.CONF
            mld = rhfn.get_text('conf_loaded').format(settings)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save settings file using selected name

        if new name specified, use that (extension must be .yml)"""
        mld = ""
        if newfile == "":
            newfile = settings
        if newfile.endswith(os.pathsep):
            mld = rhfn.get_text('fname_invalid')
        if mld == "":
            if rstdata == "":
                mld = rhfn.get_text('supply_text')
            elif self.loaded != rhfn.CONF:
                mld = rhfn.get_text('conf_invalid')
        if mld == "":
            newpath = pathlib.Path(newfile)
            if newpath.suffix != ".yml":
                newfile += ".yml"
            test = rhfn.zetom_conf(rstdata)
            try:
                test['root']
            except KeyError:
                mld = test
        if mld == '':
            fullname = HERE / newfile
            rhfn.save_conf(test, fullname)
            settings = newfile
            newfile = ""
            test = rhfn.read_conf(settings)
            try:
                test['root']
            except TypeError:
                mld = test
            else:
                self.conf = test
        if mld == "":
            mld = rhfn.get_text('conf_saved').format(str(fullname))
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load directives file for editing

        if non-existent, create from template
        """
        mld = ''
        fname, verb = rhfn.get_custom_directives_filename()
        mld, data = rhfn.read_data(fname)
        if not mld:
            rstdata = data
            self.loaded = rhfn.XTRA
            mld = rhfn.get_text('dirs_loaded').format(verb, fname)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save directives file
        """
        mld = ''
        if rstdata == "":
            mld = rhfn.get_text('supply_text')
        elif self.loaded != rhfn.XTRA:
            mld = rhfn.get_text('dirs_invalid')
        if mld == "":
            mld = rhfn.save_to(rhfn.custom_directives, rstdata)
        if mld == "":
            mld = rhfn.get_text('dirs_saved')
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def loadrst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld = ""
        if rstfile == "":
            mld = rhfn.get_text('unlikely_1')
        elif rstfile == "-- new --":
            mld = rhfn.get_text('save_reminder')
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
            source = self.currentify(self.conf['source']) / rstfile
            mld, data = rhfn.read_data(source)
        if not mld:
            self.loaded = rhfn.RST
            self.oldtext = rstdata = data
            htmlfile = source.with_suffix(".html").name
            newfile = ""
            mld = rhfn.get_text('src_loaded').format(str(source))
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def saverst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file using selected name

        if new name specified, use that (extension must be .rst)"""
        fname = newfile or rstfile
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld == "":
            where = self.currentify(self.conf['source'])
            newpath = where / fname
            if newpath.suffix != ".rst":
                newfile += ".rst"
                newpath = where / newfile
            mld = rhfn.save_to(newpath, rstdata)
            if mld == "":
                mld = rhfn.get_text('rst_saved').format(str(newpath.resolve()))
            rstfile = newpath.name
            htmlfile = newpath.with_suffix(".html").name
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """convert rst to html and show result
        """
        fname = newfile or rstfile
        if rstdata == self.oldtext:
            mld = rhfn.check_if_rst(rstdata, self.loaded) # alleen inhoud controleren
        else:
            mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld == "":
            if rstdata != self.oldtext:
                mld = rhfn.save_to(
                    self.currentify(self.conf['source']) / pathlib.Path(fname),
                    rstdata)
        if mld == "":
            previewdata = rhfn.rst2html(rstdata, str(self.conf['css']), embed=True)
            ## previewdata = rhfn.resolve_images(previewdata, self.conf['mirror_url'],
                ## self.current)
            pos = previewdata.index(b'>', previewdata.index(b'<body')) + 1
            start, end = previewdata[:pos], previewdata[pos:]
            loadrst = 'loadrst?rstfile={}'.format(fname)
            preview = bytes(previewbutton.format(loadrst), encoding="UTF-8")
            previewdata = preview.join((start, end))
            return previewdata
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def saveall(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file, (re)convert to html and (re)save html file using selected names"""
        fname = newfile or rstfile
        name, test = os.path.splitext(fname)
        if test in ('.html', ''):
            fname = name + '.rst'
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld == "":
            newpath = pathlib.Path(fname)
            rstpath = newpath.with_suffix(".rst")
            htmlpath = newpath.with_suffix(".html")
            rstfile = self.currentify(self.conf['source']) / rstpath
            htmlfile = self.currentify(self.conf['root']) / htmlpath
            newdata = rhfn.rst2html(rstdata, str(self.conf['css']))
            if rstdata != self.oldtext:
                mld = rhfn.save_to(rstfile, rstdata)
            if mld == "":
                begin, rest = str(newdata, encoding='utf-8').split(
                    '<link rel="stylesheet"',1)
                rest, end = rest.split(">",1)
                newdata = self.conf['all_css'].join((begin, end))
                mld = rhfn.save_to(htmlfile, newdata)
                if mld == "":
                    mld = rhfn.get_text('rst_2_html').format(str(htmlfile))
            rstfile = rstpath.name
            htmlfile = htmlpath.name
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = rhfn.get_text('html_name_missing')
        else:
            htmlpath = pathlib.Path(htmlfile)
            rstfile = htmlpath.with_suffix(".rst")
        if mld == "":
            htmlfile = self.currentify(self.conf['root']) / htmlpath
            mld, data = rhfn.read_data(htmlfile)
        if not mld:
            self.oldhtml = rstdata = data.replace("&nbsp", "&amp;nbsp")
            mld = rhfn.get_text('html_loaded').format(htmlfile)
            self.loaded = rhfn.HTML
            rstfile = rstfile.name
            htmlfile = htmlfile.name
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, str(rstdata), self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        ## mld = ""
        mld = rhfn.check_if_html(rstdata, self.loaded)
        if mld:
            pass
        else:
            if 'mirror_url' in self.conf:
                rstdata = rhfn.resolve_images(rstdata, self.conf['mirror_url'],
                    self.current)
            # split html on stylesheets links
            embed = True
            data = ''
            try:
                data, rstdata = rstdata.split("<link", 1)
            except ValueError:
                embed = False
            while embed:
                niks, rstdata = rstdata.split(">", 1)
                try:
                    niks, rstdata = rstdata.split("<link", 1)
                except ValueError:
                    embed = False
            with self.conf['css'].open(encoding='utf-8') as f_in:
                lines = "".join(f_in.readlines())
            newdata = lines.join(('<style type="text/css">', '</style>'))
            newdata = newdata.join((data, rstdata))
            pos = newdata.index('>', newdata.index('<body')) + 1
            start, end = newdata[:pos], newdata[pos:]
            loadhtml = 'loadhtml?htmlfile={}'.format(htmlfile)
            newdata = previewbutton.format(loadhtml).join((start, end))
            return newdata
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def savehtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """save displayed (edited) html"""
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile)
        if mld == "":
            htmlfile = self.currentify(self.conf['root']) / htmlfile
            newdata = rstdata # striplines(rstdata)
            mld = rhfn.save_to(htmlfile, newdata)
            rstdata = newdata.replace("&nbsp", "&amp;nbsp")
            if mld == "":
                mld = rhfn.get_text('html_saved').format(str(htmlfile))
            htmlfile = htmlfile.name
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile)
        if not mld:
            rstdata = self.complete_header(rstdata)
            target = self.currentify(self.conf['mirror']) / htmlfile
            mld = rhfn.save_to(target, rstdata)
            if not mld:
                x = "/" if self.current else ""
                mld = rhfn.get_text('copied_to').format(self.conf['mirror'],
                    self.current, x, htmlfile)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        "build references document"
        mld = self.scandocs()
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

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
                results.append(rhfn.get_text('mirror_missing').format(str(htmlfile)))
                continue
            # nog wat aanpassingen en kopieren naar mirror
            data = self.complete_header(newdata)
            mld = rhfn.save_to(destfile, data)
            if mld:
                results.append(mld)
        rstdata = '\n'.join(results)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), self.loaded, self.lang())

    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        rstdata = rhfn.determine_most_recently_updated(settings)
        return rstdata.format(self.conf['mirror'], self.conf['source'],
            self.conf['root'], settings)
        #TODO: add button to return to loadconf page for these settings and send page

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
