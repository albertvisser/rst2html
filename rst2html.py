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

class Rst2Html(object):
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.conffile = 'settings.yml'
        self.conf = rhfn.read_conf(self.conffile)
        self.get_subdirs()
        self.current = ""
        with TEMPLATE.open() as f_in:
            self.output = f_in.read()

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

    def scandocs(self):         # gewijzigd maar nog niet getest (kan via makerefdoc view)
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
            mld = "Trefwoordenlijst aangemaakt"
        return mld

    def lang(self, value):
        scriptspec = '<script src="/static/codemirror/mode/{}.js"></script>'
        scriptdict = {
            'yaml': ('yaml/yaml',),
            'html': ('xml/xml', 'javascript/javascript', 'css/css',
                'htmlmixed/htmlmixed'),
            'python': ('python/python', '../addon/edit/matchbrackets'),
            'rst': ('rst/rst', '../addon/mode/overlay')
                }
        return '\n'.join(scriptspec.format(x) for x in scriptdict[value])

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
        mld = "conffile is " + settings
        rstdata = '\n'.join(['{}: {}'.format(x,y) for x, y in self.conf.items()]) # ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'yml', self.lang('yaml'))

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
            mld = 'settings loaded from ' + settings
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'yml', self.lang('yaml'))

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save settings file using selected name

        if new name specified, use that (extension must be .yml)"""
        mld = ""
        if newfile == "":
            newfile = settings
        if newfile.endswith(os.pathsep):
            mld = "Not a valid filename"
        if mld == "":
            if rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            else:
                sett_ok = False
                for txt in SETT_KEYS:
                    if rstdata.startswith(txt):
                        sett_ok = True
                        break
                if not sett_ok:
                    mld = "Niet uitgevoerd: tekstveld bevat waarschijnlijk geen settings"
        if mld == "":
            newpath = pathlib.Path(newfile)
            if newpath.suffix != ".yml":
                newfile += ".yml"
            data = rhfn.zetom_conf(rstdata)
            fullname = HERE / newfile
            mld = rhfn.save_to(fullname, data)
            if mld == "":
                mld = "settings opgeslagen als " + str(fullname)
            settings = newfile
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'yml', self.lang('yaml'))

    @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load directives file for editing

        if non-existent, create from template
        """
        mld = ''
        fname, verb = rhfn.get_custom_directives_filename()
        try:
            with fname.open() as _in:
                rstdata = _in.read()
        except OSError as e:
            mld = str(e)
        if not mld:
            mld = "Directives file {}".format(verb)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'py', self.lang('python'))

    @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save directives file
        """
        mld = ''
        if rstdata == "":
            mld = "Niet opgeslagen: geen tekst opgegeven"
        if mld == "":
            mld = rhfn.save_to(rhfn.custom_directives, rstdata)
        if mld == "":
            mld = ("Directives file opgeslagen, "
                'herstart de server om wijzigingen te activeren')
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'py', self.lang('python'))

    @cherrypy.expose
    def loadrst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld = ""
        if rstfile == "":
            mld = "dit lijkt me onmogelijk" # stond open bij afsluiten browser
        elif rstfile == "-- new --":
            mld = "Vergeet niet een nieuwe filenaam op te geven om te saven"
            htmlfile = newfile = rstdata = ""
        elif rstfile.endswith("/"):
            self.current = rstfile[:-1]
            rstdata = ""
            mld = " "
        elif rstfile == "..":
            self.current = ""
            rstdata = ""
            mld = " "
        if not mld:
            source = self.currentify(self.conf['source']) / rstfile
            try:
                with source.open() as f_in:
                    rstdata = ''.join(f_in.readlines())
            except IOError as e:
                mld = str(e)
            else:
                htmlfile = str(source.with_suffix(".html").relative_to(
                    self.conf['source']))
                newfile = ""
                mld = "Source file {0} opgehaald".format(str(source))
                ## with open('/tmp/rst2html_source', 'w') as _out:
                    ## _out.write(rstdata)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))

    @cherrypy.expose
    def saverst(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file using selected name

        if new  name specified, use that (extension must be .rst)"""
        mld = ""
        if newfile == "":
            newfile = rstfile
            if newfile == "":
                mld = "dit lijkt me onmogelijk" # browser gesloten met pagina open?
            elif newfile == "-- new --":
                mld = "Naam invullen of filenaam voor source selecteren s.v.p."
            elif rstfile.endswith("/"):
                self.current = rstfile[:-1]
                mld = " "
            elif rstfile == "..":
                self.current = ""
                mld = " "
        elif newfile == "-- new --":
            mld = "Naam invullen of filenaam voor source selecteren s.v.p."
        if mld == "":
            if newfile.endswith("/"):
                if self.current:
                    mld = "nieuwe subdirectory (voorlopig) alleen in root mogelijk"
            elif rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            elif rstdata[0] == "<":
                mld = "niet uitgevoerd: tekstveld bevat waarschijnlijk HTML (begint met <)"
        if mld == "":
            if newfile.endswith("/"):
                source = self.conf['source']
                root = self.conf['root']
                nieuw = newfile[:-1]
                newpath = source / nieuw
                try:
                    newpath.mkdir()
                except OSError as err:
                    mld = str(err)
                if mld == "" and root != source:
                    newpath = root / nieuw
                    try:
                        newpath.mkdir()
                    except OSError as err:
                        mld = str(err)
                if mld == "":
                    self.get_subdirs()
                    mld = "nieuwe subdirectory {} aangemaakt in {}".format(nieuw,
                        source)
                    if root != source:
                        mld += " en {}".format(root)
            else:
                where = self.currentify(self.conf['source'])
                newpath = where / newfile
                if newpath.suffix != ".rst":
                    newfile += ".rst"
                    newpath = where / newfile
                mld = rhfn.save_to(newpath, rstdata)
                if mld == "":
                    mld = "rst source opgeslagen als " + str(newpath.resolve())
                ## rstfile = str(newpath.relative_to(where) # self.conf['source']))
                rstfile = newpath.name
                ## htmlfile = str(newpath.with_suffix(".html").relative_to(where) #  self.conf['source']))
                htmlfile = newpath.with_suffix(".html").name
                newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """convert rst to html and show result

        needs browser back button to return to application page - not sure if it works in all browsers"""
        mld = ""
        if rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            return rhfn.rst2html(rstdata, str(self.conf['css']), embed=True)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))

    @cherrypy.expose
    def saveall(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save rst file, (re)convert to html and (re)save html file using selected names"""
        mld = ""
        if newfile == "":
            if rstfile == "":   # browser afgesloten met pagina open?
                mld = "dit lijkt me onmogelijk"
            elif rstfile == "-- new --":
                mld = "Filenaam voor source opgeven of selecteren s.v.p."
            else:
                rstpath = pathlib.Path(rstfile)
                htmlpath = pathlib.Path(htmlfile)
        elif newfile.startswith("-- new --"):
            mld = "Filenaam voor source opgeven of selecteren s.v.p."
        else:
            newpath = pathlib.Path(newfile)
            ext = newpath.suffix
            if ext == ".rst":
                rstpath = newpath
                htmlpath = newpath.with_suffix('.html')
            elif ext == ".html":
                rstpath = newpath.with_suffix(".rst")
                htmlpath = newpath
            else:
                rstpath = newpath.with_suffix(".rst")
                htmlpath = newpath.with_suffix(".html")
        if mld == "":
            ## if htmlfile == "":
                ## mld = "dit lijkt me onmogelijk"
            if htmlfile in ("-- new --", ".."):
                ## if rstfile == "-- new --":
                    ## newpath = pathlib.Path(newfile)
                    ## ext = newpath.suffix
                    ## if ext == ".html":
                        ## htmlpath = newpath
                    ## else:
                        ## htmlpath = newpath.with_suffix(".html")
                ## else:
                    rstpath = pathlib.Path(rstfile)
                    ext = rstpath.suffix
                    if ext == ".rst":
                        htmlpath = rstpath.with_suffix(".html")
                    else:
                        htmlpath = pathlib.Path(rstfile + ".html")
        if mld == "":
            if rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            elif rstdata[0] == "<":
                mld = "niet uitgevoerd: tekstveld bevat waarschijnlijk HTML (begint met <)"
        if mld == "":
            rstfile = self.currentify(self.conf['source']) / rstpath
            htmlfile = self.currentify(self.conf['root']) / htmlpath
            newdata = rhfn.rst2html(rstdata, str(self.conf['css']))
            mld = rhfn.save_to(rstfile, rstdata)
            if mld == "":
                begin, rest = str(newdata, encoding='utf-8').split(
                    '<link rel="stylesheet"',1)
                rest, end = rest.split(">",1)
                newdata = self.conf['all_css'].join((begin, end))
                mld = rhfn.save_to(htmlfile, newdata)
                if mld == "":
                    mld = "rst omgezet naar html en opgeslagen als " + str(htmlfile)
            rstfile = rstpath.name
            htmlfile = htmlpath.name
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            htmlpath = pathlib.Path(htmlfile)
            rstfile = htmlpath.with_suffix(".rst")
        if mld == "":
            htmlfile = self.currentify(self.conf['root']) / htmlpath
            with htmlfile.open() as f_in:
                ## rstdata = "".join(f_in.readlines()).replace("&nbsp", "&amp;nbsp")
                rstdata = f_in.read().replace("&nbsp", "&amp;nbsp")
            mld = "target html {0} opgehaald".format(htmlfile)
            rstfile = rstfile.name
            htmlfile = htmlfile.name
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, str(rstdata), self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'html', self.lang('html'))

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld = ""
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
        if not mld:
            with self.conf['css'].open() as f_in:
                lines = "".join(f_in.readlines())
            newdata = lines.join(('<style type="text/css">', '</style>'))
            newdata = newdata.join((data, rstdata))
            return newdata
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'html', self.lang('html'))

    @cherrypy.expose
    def savehtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """save displayed (edited) html"""
        mld = ""
        # moet hier niet iets bij als if newfile: htmlfile = newfile ? Of mag "new" niet?
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --",  ".."):
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        elif rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            htmlfile = self.currentify(self.conf['root']) / htmlfile
            newdata = rstdata # striplines(rstdata)
            mld = rhfn.save_to(htmlfile, newdata)
            rstdata = newdata.replace("&nbsp", "&amp;nbsp")
            if mld == "":
                mld = "Gewijzigde html opgeslagen als " + str(htmlfile)
            ## rstfile = os.path.split(rstfile)[1]
            htmlfile = htmlfile.name
            newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'html', self.lang('html'))

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        elif not rstdata.startswith('<'):
            mld = "Please load html first"
        else:
            rstdata = self.complete_header(rstdata)
            target = self.currentify(self.conf['mirror']) / htmlfile
            mld = rhfn.save_to(target, rstdata)
            ## htmlfile = target.name
            if not mld:
                x = "/" if self.current else ""
                mld = " gekopieerd naar {0}/{1}{2}{3}".format(self.conf['mirror'],
                    self.current, x, htmlfile)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'html', self.lang('html'))

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        "build references document"
        mld = self.scandocs()
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))

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
                results.append(str(rstfile) + ' skipped: not in target directory')
                continue
            # lees de rst source en zet ze om
            with rstfile.open() as f_in:
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
                results.append(str(htmlfile) + ' not present at mirror')
                continue
            # nog wat aanpassingen en kopieren naar mirror
            data = self.complete_header(newdata)
            mld = rhfn.save_to(destfile, data)
            if mld:
                results.append(mld)
        rstdata = '\n'.join(results)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile), newfile, mld, rstdata, self.conf['wid'],
            self.conf['hig'], list_confs(settings), 'rst', self.lang('rst'))
    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        rstdata = rhfn.determine_most_recently_updated(settings)
        return rstdata.format(self.conf['mirror'], self.conf['source'],
            self.conf['root'], settings)
        #TODO: add button to return to loadconf page for these settings and send page

#~ print cherrypy.config
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
