import cherrypy
import sys
sys.path.append('.')
import os,shutil
from docutils.core import publish_string
from settings import root, source, css
template = "rst2html.html"
settpl = "settings.html"
setfn = "settings.py"

def striplines(data):
    data_n = ""
    for line in data:
        line = line[:-1] if line[-1] == "\n" else line
        data_n += line
    return data_n

def rst2html(data, embed=False):
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
    out = []
    for f in inputlist:
        s = ' selected="selected"' if naam == f else ''
        out.append("<option{1}>{0}</option>".format(f,s))
    return "".join(out)

def all_source(naam):
    all_source = [f for f in os.listdir(source) if os.path.splitext(f)[1] == ".rst"]
    return list_all(sorted(all_source),naam)

def all_html(naam):
    all_html = [f for f in os.listdir(root) if os.path.splitext(f)[1] == ".html"]
    return list_all(sorted(all_html),naam)

class Rst2Html(object):

    def __init__(self):
        self.root = root
        self.source = source
        with open(template) as f_in:
            self.output = f_in.read()

    @cherrypy.expose
    def index(self):
        rstfile = ""
        htmlfile = ""
        newfile = ""
        rstdata  = ""
        mld = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def load(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        mld = ""
        if rstfile == "":
            mld = "dit lijkt me onmogelijk"
        elif rstfile == "-- new --":
            mld = "Filenaam voor source selecteren s.v.p."
        if not mld:
            try:
                with open(os.path.join(source,rstfile)) as f_in:
                    rstdata = f_in.read()
            except IOError as e:
                mld = str(e)
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def save(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        mld = ""
        rstdata = striplines(rstdata)
        if newfile == "":
            newfile = rstfile
            if newfile == "":
                mld = "dit lijkt me onmogelijk"
            elif newfile == "-- new --":
                mld = "Filenaam voor source selecteren s.v.p."
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
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def convert(self,rstfile="",htmlfile="",newfile="",rstdata=""):
        mld = ""
        if rstdata == "":
            mld = "Tekstveld invullen s.v.p."
        if mld == "":
            return rst2html(rstdata,embed=True)
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

    @cherrypy.expose
    def store(self,rstfile="",htmlfile="",newfile="",rstdata=""):
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
            else:
                rstdata = striplines(rstdata)
        if mld == "":
            rstfile = os.path.join(source,rstfile)
            htmlfile = os.path.join(root,htmlfile)
            newdata = rst2html(rstdata)
            mld = save_to(rstfile,rstdata)
            if mld == "":
                mld = save_to(htmlfile,newdata)
                if mld == "":
                    mld = "rst omgezet naar html en opgeslagen als " + htmlfile
            rstfile = os.path.split(rstfile)[1]
            htmlfile = os.path.split(htmlfile)[1]
            if newfile == rstfile or newfile == htmlfile:
                newfile = ""
        return self.output.format(all_source(rstfile),all_html(htmlfile),newfile,mld,rstdata)

#~ print cherrypy.config
cherrypy.quickstart(Rst2Html())