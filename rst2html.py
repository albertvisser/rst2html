#! /usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy
import sys
sys.path.append('.')
import os,shutil
from docutils.core import publish_string
from docutils.parsers.rst import directives
from settings import root, source, css, mirror, all_css
from directives import StartCols, EndCols, FirstCol, NextCol, ClearCol, Spacer, Bottom
HERE = os.path.split(__file__)[0]
template = os.path.join(HERE, "rst2html.html") # _met_settings
css = os.path.join(HERE, css)
settpl = "settings.html"
setfn = "settings.py"

def striplines(data):
    """list -> string met verwijdering van eventuele line endings"""
    return "".join([line.rstrip() for line in data])

def rst2html(data, embed=False):
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

def all_source(naam):
    """build list of options from rst files"""
    all_source = [f for f in os.listdir(source) if os.path.splitext(f)[1] == ".rst"]
    return list_all(sorted(all_source),naam)

def all_html(naam):
    """build list of options from html files"""
    all_html = [f for f in os.listdir(root) if os.path.splitext(f)[1] == ".html"]
    return list_all(sorted(all_html),naam)

class Rst2Html(object):

    def __init__(self):
        """initialize using imported settings; read template; register directives"""
        self.root = root
        self.source = source
        with open(template) as f_in:
            self.output = f_in.read()
        directives.register_directive("startc", StartCols)
        directives.register_directive("endc", EndCols)
        directives.register_directive("firstc", FirstCol)
        directives.register_directive("nextc", NextCol)
        directives.register_directive("clearc", ClearCol)
        directives.register_directive("spacer", Spacer)
        directives.register_directive("bottom", Bottom)

    @cherrypy.expose
    def index(self):
        """show page with empty fields (and selectable filenames)"""
        rstfile = ""
        htmlfile = ""
        newfile = ""
        rstdata  = ""
        mld = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

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
        if not mld:
            try:
                with open(os.path.join(source,rstfile)) as f_in:
                    rstdata = f_in.read()
                htmlfile = os.path.splitext(rstfile)[0] + ".html"
                newfile = ""
            except IOError as e:
                mld = str(e)
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

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
        if mld == "" and rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            naam,ext = os.path.splitext(newfile)
            if ext != ".rst":
                newfile += ".rst"
            fullname = os.path.join(source,newfile)
            mld = save_to(fullname,rstdata)
            if mld == "":
                mld = "rst source opgeslagen als " + fullname
            rstfile = newfile
            newfile = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def convert(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """convert rst to html and show result

        needs browser back button to return to application page - not sure if it works in all browsers"""
        mld = ""
        if rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            return rst2html(rstdata,embed=True)
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

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
            elif htmlfile == "-- new --":
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
        if mld == "":
            rstfile = os.path.join(source,rstfile)
            htmlfile = os.path.join(root,htmlfile)
            newdata = rst2html(rstdata)
            mld = save_to(rstfile,rstdata)
            if mld == "":
                mld = save_to(htmlfile,newdata)
                if mld == "":
                    mld = "rst omgezet naar html en opgeslagen als " + htmlfile
            rstfile = os.path.basename(rstfile)
            htmlfile = os.path.basename(htmlfile)
            if newfile == rstfile or newfile == htmlfile:
                newfile = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def loadhtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """load html file and show code"""
        mld = ""
        if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            naam,ext = os.path.splitext(htmlfile)
        if mld == "":
            htmlfile = os.path.join(root,htmlfile)
            with open(htmlfile) as f_in:
                ## rstdata = striplines(f_in.readlines()).replace("&nbsp","&amp;nbsp")
                rstdata = "".join(f_in.readlines()).replace("&nbsp","&amp;nbsp")
            htmlfile = os.path.basename(htmlfile)
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def showhtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        mld = ""
        if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            data, rstdata = rstdata.split("<link",1)
            niks, rstdata = rstdata.split(">",1)
            with open(css) as f_in:
                lines = "".join(f_in.readlines())
            newdata = lines.join(('<style type="text/css">','</style>'))
            newdata = newdata.join((data,rstdata))
            ## for line in data:
                ## newdata.append("X") # line)
            return newdata
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def savehtml(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """save displayed (edited) html"""
        mld = ""
        if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            if rstdata == "":
                mld = "Tekstveld invullen s.v.p."
            ## else:
                ## rstdata = striplines(rstdata)
        if mld == "":
            ## rstfile = os.path.join(source,rstfile)
            htmlfile = os.path.join(root,htmlfile)
            newdata = rstdata # striplines(rstdata)
            mld = save_to(htmlfile,newdata)
            rstdata = newdata.replace("&nbsp","&amp;nbsp")
            if mld == "":
                mld = "Gewijzigde html opgeslagen als " + htmlfile
            ## rstfile = os.path.split(rstfile)[1]
            htmlfile = os.path.basename(htmlfile)
            if newfile == rstfile or newfile == htmlfile:
                newfile = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def copytoroot(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        """copy html to mirror site

        along the way the right stylesheets are added"""
        mld = ""
        if htmlfile == "" or htmlfile == "-- new --":
            mld = "Filenaam voor html opgeven of selecteren s.v.p."
        else:
            target = os.path.join(mirror,htmlfile)
            htmlfile = os.path.join(root,htmlfile)
            with open(htmlfile) as f_in:
                htmldata = "".join(f_in.readlines())
            if css in htmldata:
                data, htmldata = htmldata.split("<link",1)
                niks, htmldata = htmldata.split(">",1)
                htmldata = all_css.join((data,htmldata))
            mld = save_to(htmlfile, htmldata)
            mld = save_to(target, htmldata)
            htmlfile = os.path.basename(htmlfile)
            if not mld:
                mld = " gekopieerd naar ".join((htmlfile,mirror))
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

#~ print cherrypy.config
if __name__ == "__main__":
    cherrypy.quickstart(Rst2Html(), config={
    "/": {
        'server.socket_host': 'rst2html.linuxmoby.nl',
        'server.socket_port': 80,
        }})
