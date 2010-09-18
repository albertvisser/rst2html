#! /usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import sys
sys.path.append('.')
import os, shutil
from docutils.core import publish_string
from docutils.parsers.rst import directives
from settings import root, source, css, mirror, all_css, wid, hig
from directives import StartCols, EndCols, FirstCol, NextCol, ClearCol, Spacer, Bottom
HERE = os.path.split(__file__)[0]
template = os.path.join(HERE, "rst2html.html") # _met_settings
CSS = os.path.join(root, css)
settpl = "settings.html"
setfn = "settings.py"

def striplines(data):
    """list -> string met verwijdering van eventuele line endings"""
    return "".join([line.rstrip() for line in data])

def rst2html(data, embed=False):
    """rst naar html omzetten en resultaat teruggeven"""
    overrides = {
        "embed_stylesheet": embed,
        "stylesheet_path": CSS,
        "report_level": 3,
        }
    return publish_string(source=data,
        destination_path="temp/omgezet.html",
        writer_name='html',
        settings_overrides=overrides,
        )

def save_to(fullname, data):
    """backup file, then write data to file

    gebruikt copyfile i.v.m. permissies (user = webserver ipv end-user"""
    try:
        if os.path.exists(fullname):
            if os.path.exists(fullname + ".bak"):
                os.remove(fullname + ".bak")
            shutil.copyfile(fullname,fullname + ".bak")
        with open(fullname,"w") as f_out:
            f_out.write(data)
    except Exception as e:
        mld = str(e)
    else:
        mld = ""
    return mld

def list_all(inputlist,naam):
    """build list of options from filenames, with naam selected"""
    out = []
    for f in inputlist:
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{1}>{0}</option>".format(f,s))
    return "".join(out)

class Rst2Html(object):

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        self.root = root
        self.source = source
        self.subdirs = sorted([f + "/" for f in os.listdir(source) \
            if os.path.isdir(os.path.join(source,f))])
        self.current = ""
        with open(template) as f_in:
            self.output = f_in.read()
        directives.register_directive("startc", StartCols)
        directives.register_directive("endc", EndCols)
        directives.register_directive("firstc", FirstCol)
        directives.register_directive("nextc", NextCol)
        directives.register_directive("clearc", ClearCol)
        directives.register_directive("spacer", Spacer)
        directives.register_directive("bottom", Bottom)

    def all_source(self, naam):
        """build list of options from rst files"""
        path = os.path.join(source,self.current) if self.current else source
        dirlist = os.listdir(path)
        all_source = [f for f in dirlist if os.path.splitext(f)[1] == ".rst"]
        items = sorted(all_source)
        if self.current:
            items.insert(0,"..")
        else:
            items = self.subdirs + items
        return list_all(items,naam)

    def all_html(self, naam):
        """build list of options from html files"""
        path = os.path.join(root,self.current) if self.current else root
        dirlist = os.listdir(path)
        all_html = [f for f in dirlist if os.path.splitext(f)[1] == ".html"]
        items = sorted(all_html)
        if self.current:
            items.insert(0,"..")
        else:
            items = self.subdirs + items
        return list_all(items,naam)

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        rstfile = htmlfile = newfile = rstdata  = ""
        mld = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def loadrst(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """load indicated .rst file

        pre-builds save-filename by changing extension from rst to html"""
        mld = ""
        if rstfile == "":
            mld = "dit lijkt me onmogelijk"
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
            try:
                where = os.path.join(source,self.current) if self.current else source
                with open(os.path.join(where,rstfile)) as f_in:
                    rstdata = f_in.read()
                htmlfile = os.path.splitext(rstfile)[0] + ".html"
                newfile = ""
            except IOError as e:
                mld = str(e)
            else:
                mld = "Source file {0} opgehaald".format(os.path.join(where,rstfile))
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def saverst(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """(re)save rst file using selected name

        if new  name specified, use that (extension must be .rst)"""
        mld = ""
        if newfile == "":
            newfile = rstfile
            if newfile == "":
                mld = "dit lijkt me onmogelijk"
            elif newfile == "-- new --":
                mld = "Naam invulen of filenaam voor source selecteren s.v.p."
            elif rstfile.endswith("/"):
                self.current = rstfile[:-1]
                mld = " "
            elif rstfile == "..":
                self.current = ""
                mld = " "
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
                nieuw = newfile[:-1]
                os.mkdir(os.path.join(source,nieuw))
                os.mkdir(os.path.join(root,nieuw))
                self.subdirs = sorted([f + "/" for f in os.listdir(source) \
                    if os.path.isdir(os.path.join(source,f))])
                mld = "nieuwe subdirectory {0} aangemaakt in {1} en {2}".format(nieuw,
                    source, root)

            else:
                naam,ext = os.path.splitext(newfile)
                if ext != ".rst":
                    newfile += ".rst"
                where = os.path.join(source,self.current) if self.current else source
                fullname = os.path.join(where,newfile)
                mld = save_to(fullname,rstdata)
                if mld == "":
                    mld = "rst source opgeslagen als " + fullname
                rstfile = newfile
                newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def convert(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """convert rst to html and show result

        needs browser back button to return to application page - not sure if it works in all browsers"""
        mld = ""
        if rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            return rst2html(rstdata,embed=True)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def saveall(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """(re)save rst file, (re)convert to html and (re)save html file using selected names"""
        mld = ""
        if newfile == "":
            if rstfile == "":
                mld = "dit lijkt me onmogelijk"
            elif rstfile == "-- new --":
                mld = "Filenaam voor source opgeven of selecteren s.v.p."
        else:
            naam,ext = os.path.splitext(newfile)
            if ext == ".rst":
                rstfile = newfile
                htmlfile = naam + ".html"
            elif ext == ".html":
                rstfile = naam + ".rst"
                htmlfile = newfile
            else:
                rstfile = newfile + ".rst"
                htmlfile = newfile + ".html"
        if mld == "":
            if htmlfile == "":
                mld = "dit lijkt me onmogelijk"
            elif htmlfile in ("-- new --",".."):
                if rstfile == "-- new --":
                    naam,ext = os.path.splitext(newfile)
                    if ext == ".html":
                        htmlfile = newfile
                    else:
                        htmlfile = newfile + ".html"
                else:
                    naam,ext = os.path.splitext(rstfile)
                    if ext == ".rst":
                        htmlfile = naam + ".html"
                    else:
                        htmlfile = rstfile + ".html"
        if mld == "":
            if rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            elif rstdata[0] == "<":
                mld = "niet uitgevoerd: tekstveld bevat waarschijnlijk HTML (begint met <)"
        if mld == "":
            where = os.path.join(source,self.current) if self.current else source
            rstfile = os.path.join(where,rstfile)
            where = os.path.join(root,self.current) if self.current else root
            htmlfile = os.path.join(where,htmlfile)
            newdata = rst2html(rstdata)
            mld = save_to(rstfile,rstdata)
            if mld == "":
                begin, rest = newdata.split('<link rel="stylesheet"',1)
                rest, end = rest.split(">",1)
                newcss = '<link rel="stylesheet" href="{0}" type="text/css" />'.format(css)
                newdata = newcss.join((begin,end))
                mld = save_to(htmlfile,newdata)
                if mld == "":
                    mld = "rst omgezet naar html en opgeslagen als " + htmlfile
            rstfile = os.path.basename(rstfile)
            htmlfile = os.path.basename(htmlfile)
            if newfile == rstfile or newfile == htmlfile:
                newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def loadhtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
        ## if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        ## elif htmlfile.endswith("/"):
            ## self.current = htmlfile[:-1]
            ## rstdata = ""
            ## mld = " "
        ## elif htmlfile == "..":
            ## self.current = ""
            ## rstdata = ""
            ## mld = " "
        else:
            naam,ext = os.path.splitext(htmlfile)
            rstfile = naam + ".rst"
        if mld == "":
            where = os.path.join(root,self.current) if self.current else root
            htmlfile = os.path.join(where,htmlfile)
            with open(htmlfile) as f_in:
                ## rstdata = striplines(f_in.readlines()).replace("&nbsp","&amp;nbsp")
                rstdata = "".join(f_in.readlines()).replace("&nbsp","&amp;nbsp")
            mld = "target html {0} opgehaald".format(htmlfile)
            htmlfile = os.path.basename(htmlfile)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def showhtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        mld = ""
        ## if htmlfile == "" or htmlfile == "-- new --":
            ## mld = "Filenaam voor html opgeven of selecteren s.v.p."
        ## else:
        data, rstdata = rstdata.split("<link",1)
        niks, rstdata = rstdata.split(">",1)
        if CSS in niks:
            linked_css = CSS
        else:
            niks,linked_css = niks.split('css/',1)
            linked_css,niks = linked_css.split('"',1)
            linked_css = "/css/".join((root,linked_css))
        with open(linked_css) as f_in:
            lines = "".join(f_in.readlines())
        newdata = lines.join(('<style type="text/css">','</style>'))
        newdata = newdata.join((data,rstdata))
        ## for line in data:
            ## newdata.append("X") # line)
        return newdata
        ## return self.output.format(self.all_source(rstfile),
            ## self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def savehtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """save displayed (edited) html"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
        ## if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        ## elif htmlfile.endswith("/"):
            ## self.current = htmlfile[:-1]
            ## mld = " "
        ## elif htmlfile == "..":
            ## self.current = ""
            ## mld = " "
        else:
            if rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            ## else:
                ## rstdata = striplines(rstdata)
        if mld == "":
            ## rstfile = os.path.join(source,rstfile)
            where = os.path.join(root,self.current) if self.current else root
            htmlfile = os.path.join(where,htmlfile)
            newdata = rstdata # striplines(rstdata)
            mld = save_to(htmlfile,newdata)
            rstdata = newdata.replace("&nbsp","&amp;nbsp")
            if mld == "":
                mld = "Gewijzigde html opgeslagen als " + htmlfile
            ## rstfile = os.path.split(rstfile)[1]
            htmlfile = os.path.basename(htmlfile)
            if newfile == rstfile or newfile == htmlfile:
                newfile = ""
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

    @cherrypy.expose
    def copytoroot(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = ""
        if htmlfile.endswith("/") or htmlfile in ("", "-- new --", ".."):
        ## if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            where = os.path.join(mirror,self.current) if self.current else mirror
            target = os.path.join(where,htmlfile)
            where = os.path.join(root,self.current) if self.current else root
            htmlfile = os.path.join(where,htmlfile)
            with open(htmlfile) as f_in:
                htmldata = "".join(f_in.readlines())
            if css in htmldata:
                data, htmldata = htmldata.split("<link",1)
                niks, htmldata = htmldata.split(">",1)
                allcss = all_css
                if self.current:
                    allcss = all_css.replace('href="css','href="../css')
                htmldata = allcss.join((data,htmldata))
            mld = save_to(htmlfile, htmldata)
            mld = save_to(target, htmldata)
            htmlfile = os.path.basename(htmlfile)
            if not mld:
                x = "/" if self.current else ""
                mld = " gekopieerd naar {0}{1}{2}{3}".format(mirror,self.current,x,htmlfile)
        return self.output.format(self.all_source(rstfile),
            self.all_html(htmlfile),newfile,mld,rstdata, wid, hig)

#~ print cherrypy.config
if __name__ == "__main__":
    cherrypy.quickstart(Rst2Html(), config={
    "/": {
        'server.socket_host': 'rst2html.linuxmoby.nl',
        'server.socket_port': 80,
        }})
