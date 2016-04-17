"""Convert text documents to Mongo format
"""
import os.path
import sys
import pprint
import argparse
import pathlib
import shutil
import rst2html_functions as rhfn
import rst2html_functions_mongo as rhfnm
import docs2mongo as dml

def main(args):

    settings = 'settings.yml'
    if args.input:
        settings = args.input if args.input.endswith('.yml') else args.input + '.yml'

    # read settings so that we know where everything is
    mld, sett = rhfn.read_conf(settings)
    for item in ('starthead', 'endhead'):
        if item in sett and isinstance(sett[item], str):
            sett[item] = sett[item].split('\n')

    # init site
    sitename = sett['mirror_url'][7:].split('.')[0]
    if args.newname:
        sitename = args.newname
    dml.clear_site_data(sitename) # restart
    dml.create_new_site(sitename)

    # copy site configuration
    conf = rhfnm.DFLT_CONF
    for key in rhfnm.FULL_CONF:
        if key in sett:
            conf[key] = sett[key]
    conf['url'] = "/rst2html-data/{}".format(sitename)
    dml.update_settings(sitename, conf)

    # transfer docs in source directory
    srcpath = sett["source"]
    convpath = sett["root"]
    mirrpath = sett["mirror"]
    subdirs = [str(f.relative_to(srcpath)) for f in srcpath.iterdir() if f.is_dir()]
    newmirrbase = pathlib.Path(__file__).parent / 'rst2html-data' / sitename

    # root files first
    newmirrpath = newmirrbase
    files = [str(f.relative_to(srcpath)) for f in srcpath.glob("*.rst")]
    for item in files:
        file_to_read = srcpath / item
        docname = file_to_read.stem
        dml.create_new_doc(sitename, docname)
        with file_to_read.open() as _in:
            data = _in.read()
        dml.update_rst(sitename, docname, data)
        convfile = convpath / item.replace('.rst', '.html')
        if convfile.exists():
            with convfile.open() as _in:
                data = _in.read()
            dml.update_html(sitename, docname, data)
        mirrfile = mirrpath / item.replace('.rst', '.html')
        newmirrfile = newmirrpath / item.replace('.rst', '.html')
        if mirrfile.exists():
            with mirrfile.open() as _in:
                data = _in.read()
            dml.update_mirror(sitename, docname)
            if not newmirrpath.exists():
                newmirrpath.mkdir(parents=True)
            rhfn.save_to(newmirrfile, data)

    for ext in args.extlist:
        spec = "*.{}".format(ext)
        entries = [str(f.relative_to(mirrpath)) for f in mirrpath.glob(spec)]
        for entry in entries:
            mirrfile = mirrpath / entry
            destfile = newmirrpath / entry
            shutil.copyfile(str(mirrfile), str(destfile))

    for name in args.dirlist:
        srcdir = mirrpath / name
        destdir = newmirrpath / name
        shutil.copytree(str(srcdir), str(destdir))

    for dirname in subdirs:
        dml.create_new_dir(sitename, dirname)
        dirpath = srcpath / dirname
        wrkpath = mirrpath / dirname
        newmirrpath = newmirrbase / dirname
        files = [str(f.relative_to(dirpath)) for f in dirpath.glob("*.rst")]
        for item in files:
            file_to_read = dirpath / item
            docname = file_to_read.stem
            dml.create_new_doc(sitename, docname, dirname)
            with file_to_read.open() as _in:
                data = _in.read()
            dml.update_rst(sitename, docname, data, dirname)
            convfile = convpath / dirname / item.replace('.rst', '.html')
            if convfile.exists():
                with convfile.open() as _in:
                    data = _in.read()
                dml.update_html(sitename, docname, data, dirname)
            mirrfile = wrkpath / item.replace('.rst', '.html')
            if mirrfile.exists():
                with mirrfile.open() as _in:
                    data = _in.read()
                dml.update_mirror(sitename, docname, dirname)
                newmirrfile = newmirrpath / item.replace('.rst', '.html')
                if not newmirrpath.exists():
                    newmirrpath.mkdir(parents=True)
                rhfn.save_to(newmirrfile, data)

        for ext in args.extlist:
            spec = "*.{}".format(ext)
            entries = [str(f.relative_to(wrkpath)) for f in wrkpath.glob(spec)]
            for entry in entries:
                mirrfile = wrkpath / entry
                destfile = newmirrpath / entry
                shutil.copyfile(str(mirrfile), str(destfile))
    print('ready\n')

    ## # check results so far
    ## index, docs = dml.list_site_data(sitename)
    ## pprint.pprint(index)
    ## for doc in docs:
        ## pprint.pprint(doc)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Convert a site from text to mongo format")
    parser.add_argument('-i', '--input', nargs='?',
        help="specify settings file for site to copy")
    parser.add_argument('-n', '--newname', nargs='?',
        help="enter new name for site")
    parser.add_argument('-d', '--dirlist', nargs='*',
        help="also copy files within these directories")
    parser.add_argument('-e', '--extlist', nargs='*',
        help="also copy files with these extensions")
    args = parser.parse_args()
    main(args)
