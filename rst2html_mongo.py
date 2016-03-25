# -*- coding: utf-8 -*-

"""
webapp om teksten in ReST formaat om te zetten naar HTML documenten
"""
import cherrypy
import sys
sys.path.append('.')
import os
import pathlib
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

class Rst2Html(object):
    "the actual webapp"

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        rhfn.register_directives()
        self.conffile = rhfn.default_site()
        self.current = ""
        self.oldtext = self.oldlang = self.oldhtml = ""

    def read_conf(self, settings):
        # settings is hier de site naam
        mld, conf = rhfn.read_conf(settings)
        if mld == '':
            self.conf = conf
            self.subdirs = rhfn.list_subdirs(settings, 'src')
            self.current = ""
        self.loaded = rhfn.CONF
        return mld

    def format_output(self, rstfile, htmlfile, newfile, mld, rstdata, settings):
        if self.oldlang != self.conf["lang"]:
            self.oldlang = self.conf["lang"]
        all_source = rhfn.list_files(self.conffile, self.current, rstfile, 'src',
            self.conf["lang"])
        all_html = rhfn.list_files(self.conffile, self.current, htmlfile, 'dest',
            self.conf["lang"])
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
        conflist = rhfn.list_confs(settings)
        if not self.loaded:
            txtlang = ''
        else:
            txtlang = '\n'.join(scriptspec.format(x) for x in scriptdict[self.loaded])
        return self.output.format(all_source, all_html, newfile, mld, rstdata,
            self.conf['wid'], self.conf['hig'], conflist, self.loaded, txtlang)

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        # config defaults so we can always show the first page
        self.conf = rhfn.DFLT_CONF
        rstfile = htmlfile = newfile = rstdata  = ""
        settings = self.conffile
        mld = self.read_conf(settings)
        if mld == '':
            rstdata = rhfn.conf2text(self.conf)
            mld = rhfn.get_text('conf_init', self.conf["lang"]).format(settings)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def loadconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load settings of indicated site

        "create new" is deliberatily hidden by not providing a -- new -- option
        """
        if newfile and newfile != settings:
            settings = newfile
            mld = rhfn.new_conf(settings)
        if mld == "":
            newfile = ''
            mld = self.read_conf(settings)
        if mld == '':
            rstdata = rhfn.conf2text(self.conf)
            mld = rhfn.get_text('conf_loaded', self.conf["lang"]).format(settings)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def saveconf(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save settings for selected site name

        if new name specified, use that"""
        mld = ""
        if newfile:
            settings = newfile
            newfile = ""
        if rstdata == "":
            mld = rhfn.get_text('supply_text', self.conf["lang"])
        elif self.loaded != rhfn.CONF:
            mld = rhfn.get_text('conf_invalid', self.conf["lang"])
        if mld == "":
            mld = rhfn.save_conf(settings, rstdata, self.conf["lang"])
        if mld == "":
            mld = self.read_conf(settings)
        if mld == '':
            mld = rhfn.get_text('conf_saved', self.conf["lang"]).format(settings)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

 #   @cherrypy.expose    # nog testen
    def loadxtra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load directives file for editing

        if non-existent, create from template
        """
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
        mld = ''
        fname, verb = rhfn.get_custom_directives_filename()
        verb = rhfn.get_text(verb, self.conf['lang'])
        mld, data = rhfn.read_data(fname)
        if not mld:
            rstdata = data
            self.loaded = rhfn.XTRA
            mld = rhfn.get_text('dirs_loaded', self.conf["lang"]).format(verb, fname)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

 #   @cherrypy.expose    # nog testen
    def savextra(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """(re)save directives file
        """
        # this data actually *does* come from the file system as itś code stored on the server
        # but itś effectively deactivated for now
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
            mld, data = rhfn.read_src_data(settings, current, rstfile)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
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
        is_new_file = (newfile != "")
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            if fname.suffix != ".rst":
                fname += ".rst"
            if newfile == '':
                mld = rhfn.save_src_data(settings, current, fname, rstdata)
            else:
                mld = rhfn.save_src_data(settings, current, fname, rstdata, True)
            if mld == "":
                mld = rhfn.get_text('rst_saved', self.conf["lang"]).format(fname)
            rstfile = fname
            htmlfile = fname.replace(".rst", ".html")
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def convert(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """convert rst to html and show result
        """
        fname = newfile or rstfile
        if rstdata == self.oldtext:
            mld = rhfn.check_if_rst(rstdata, self.loaded) # alleen inhoud controleren
        else:
            mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            if rstdata != self.oldtext:
                mld = rhfn.save_src_data(settings, current, fname, rstdata,
                    self.conf["lang"])
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
        mld = rhfn.check_if_rst(rstdata, self.loaded, fname)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            rstfile = fname
            htmlfile = name + ".html"
            newdata = str(rhfn.rst2html(rstdata, self.conf['css']), encoding='utf-8')
            if rstdata != self.oldtext:
                mld = rhfn.save_src_data(settings, current, rstfile, rstdata)
            if mld == "":
                mld = rhfn.save_html_data(settings, current, htmlfile, newdata)
                if mld == "":
                    mld = rhfn.get_text('rst_2_html', self.conf["lang"]).format(
                        str(htmlfile))
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def loadhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
            mld = rhfn.get_text('html_name_missing', self.conf["lang"])
        else:
            rstfile = os.path.split(htmlfile)[0] + ".rst"
        if mld == "":
            mld, data = rhfn.read__html_data(settings, current, htmlfile)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            self.oldhtml = rstdata = data.replace("&nbsp", "&amp;nbsp")
            mld = rhfn.get_text('html_loaded', self.conf["lang"]).format(htmlfile)
            self.loaded = rhfn.HTML
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def showhtml(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld = rhfn.check_if_html(rstdata, self.loaded)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
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
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            newdata = rstdata # striplines(rstdata)
            mld = rhfn.save_html_data(settings, current, htmlfile, newdata)
            rstdata = newdata.replace("&nbsp", "&amp;nbsp")
            if mld:
                mld = rhfn.get_text(mld, self.conf["lang"])
            else:
                mld = rhfn.get_text('html_saved', self.conf["lang"]).format(
                    str(htmlfile))
            newfile = ""
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def copytoroot(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = rhfn.check_if_html(rstdata, self.loaded, htmlfile)
        if mld:
            mld = rhfn.get_text(mld, self.conf["lang"])
        else:
            rstdata = rhfn.complete_header(self.conf, rstdata)
            mld = rhfn.save_to_mirror(settings, self.current, htmlfile, rstdata)
            if not mld:
                x = "/" if self.current else ""
                mld = rhfn.get_text('copied_to', self.conf["lang"]).format(
                    self.conf['mirror'], self.current, x, htmlfile)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def makerefdoc(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        "build references document"
        rstdata = rhfn.build_trefwoordenlijst(sitename, self.conf["lang"])
        dirname, docname = '', 'reflist'
        mld = rhfn.save_src_data(sitename, dirname, docname + 'rst', rstdata,
            new=True)
        if mld: # might not be present yet, so try again
            mld = rhfn.save_src_data(sitename, dirname, docname + '.rst', rstdata)
        if mld == "":
            newdata = str(rhfn.rst2html(rstdata, self.conf['css']), encoding='utf-8')
            mld = rhfn.save_html_data(sitename, dirname, docname + '.html', newdata)
            if mld == "":
                mld = rhfn.save_to_mirror(sitename, dirname, docname + '.html')
        if not mld:
            mld = rhfn.get_text('index_built', self.conf["lang"])
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def convert_all(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        """regenerate all html files
        """
        results = rhfn.update_all(settings, self.conf["css"])
        rstdata = '\n'.join(results)
        return self.format_output(rstfile, htmlfile, newfile, mld, rstdata, settings)

    @cherrypy.expose
    def overview(self, settings="", rstfile="", htmlfile="", newfile="", rstdata=""):
        mld, rstdata = rhfn.determine_most_recently_updated(settings,
            self.conf['lang'])
        if not mld:
            return rstdata.format(settings)
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
