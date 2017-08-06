"""Convert text documents to Mongo format
"""
## import os.path
## import sys
## import pprint
import argparse
## import pathlib
import shutil
from app_settings import FS_WEBROOT, DB_WEBROOT
import rst2html_functions_all as rhfn
import docs2fs as fsys
import docs2mongo as mongo


def main(args):
    """do the conversion
    """
    sitename = args.input
    fromloc = FS_WEBROOT / sitename
    tomirror = DB_WEBROOT / sitename
    ## sourceloc = fromloc / 'source'
    ## targetloc = fromloc / 'target'

    # read settings so that we know where everything is
    try:
        print('reading settings for {}'.format(sitename))
        sett = fsys.read_settings(sitename)
    except FileNotFoundError:
        print("settings don't exist")
        return
    if not sett:
        print("settings are empty")
        return

    for item in ('starthead', 'endhead'):
        if item in sett and isinstance(sett[item], str):
            sett[item] = sett[item].split('\n')

    # init site
    newsite = args.newname or sitename
    mongo.clear_site_data(newsite)  # restart
    mongo.create_new_site(newsite)

    # copy site configuration
    conf = rhfn.DFLT_CONF
    for key in rhfn.FULL_CONF:
        if key in sett:
            conf[key] = sett[key]
    ## conf['url'] = "/rst2html-data/{}".format(sitename)
    mongo.update_settings(sitename, conf)

    # transfer docs in source directory
    ## srcpath =  sourceloc
    ## convpath = targetloc
    ## mirrpath = fromloc
    subdirs = fsys.list_dirs(sitename)
    ## newmirrbase = targetloc

    # root files first
    files = fsys.list_docs(sitename, 'src')
    for docname in files:
        mongo.create_new_doc(newsite, docname)
        rstdata = fsys.get_doc_contents(sitename, docname, 'src')
        mongo.update_rst(newsite, docname, rstdata)

        try:
            htmldata = fsys.get_doc_contents(sitename, docname, 'dest')
        except FileNotFoundError:
            continue
        mongo.update_html(newsite, docname, htmldata)

        fname = docname + '.html'
        fromfile = fromloc / fname
        destfile = tomirror / fname
        if fromfile.exists():
            mld, data = fsys.read_data(fromfile)
            mongo.update_mirror(newsite, docname, data)

    for ext in args.extlist:
        spec = "*.{}".format(ext)
        entries = [str(f.relative_to(fromloc)) for f in fromloc.glob(spec)]
        for entry in entries:
            ## shutil.copyfile(str(fromloc / entry), str(destloc / entry))
            shutil.copyfile(str(fromloc / entry), str(tomirror / entry))

    for name in args.dirlist:
        srcdir = fromloc / name
        destdir = tomirror / name
        shutil.copytree(str(srcdir), str(destdir))

    for dirname in subdirs:
        print('new dir:', dirname)
        mongo.create_new_dir(newsite, dirname)
        frompath = fromloc / dirname
        destpath = tomirror / dirname

        files = fsys.list_docs(sitename, 'src', dirname)
        for docname in files:
            print('new doc:', docname)
            mongo.create_new_doc(newsite, docname, dirname)
            rstdata = fsys.get_doc_contents(sitename, docname, 'src', dirname)
            mongo.update_rst(newsite, docname, rstdata, dirname)

            try:
                htmldata = fsys.get_doc_contents(sitename, docname, 'dest', dirname)
            except FileNotFoundError:
                continue
            mongo.update_html(newsite, docname, htmldata, dirname)

            fname = docname + '.html'
            fromfile = frompath / fname
            destfile = destpath / fname
            if fromfile.exists():
                mld, data = fsys.read_data(fromfile)
                mongo.update_mirror(newsite, docname, data, dirname)

        for ext in args.extlist:
            spec = "*.{}".format(ext)
            entries = [str(f.relative_to(frompath)) for f in frompath.glob(spec)]
            for entry in entries:
                mirrfile = frompath / entry
                destfile = destpath / entry
                shutil.copyfile(str(mirrfile), str(destfile))

    print('ready\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert a site from text to mongo format")
    parser.add_argument('-i', '--input', nargs='?', required=True,
                        help="specify name of site to copy")
    parser.add_argument('-n', '--newname', nargs='?',
                        help="enter new name for site")
    parser.add_argument('-d', '--dirlist', nargs='*',
                        help="also copy files within these directories")
    parser.add_argument('-e', '--extlist', nargs='*',
                        help="also copy files with these extensions")
    args = parser.parse_args()
    main(args)
