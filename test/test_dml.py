"""Rst2HTML unit tests for dml modules: same tests apply for all variants

can be configured which module to use via app_settings
"""
import sys
import os
import pprint
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_settings import DML, WEBROOT
if DML == 'fs':
    print('using file system dml')
    import docs2fs as dml
elif DML == 'mongo':
    print('using mongodb dml')
    import docs2mongo as dml
elif DML == 'postgres':
    print('using postgresql dml')
    import docs2pg as dml


def list_site_contents(sitename, filename=''):
    """show site contents in a standard structure, independent of the data backend
    """
    errs = ''
    try:
        sitedoc, docdata = dml.list_site_data(sitename)
    except FileNotFoundError as e:
        errs = str(e)
        sitedoc, docdata = {}, []
    if not filename:
        print('\n--------- Listing contents of site {} ----------'.format(sitename))
        if errs:
            print(errs)
        else:
            pprint.pprint(sitedoc)
            print("----")
            for doc in docdata:
                pprint.pprint(doc)
            print("----")
    else:
        with open(filename, 'w') as _out:
            if errs:
                print(errs, file=_out)
            else:
                pprint.pprint(sitedoc, stream=_out)
                for doc in docdata:
                    pprint.pprint(doc, stream=_out)
    return sitedoc, docdata


def list_site_and_docs(sitename, filename):
    """show site contents and also all types of directory listings
    """
    list_site_contents(sitename, filename)
    with open(filename, 'a') as _out:
        for ftype in ('src', 'dest', 'mirror'):
            data = dml.list_docs(sitename, ftype)
            print('list files for', ftype, ':', data, file=_out)
            data = dml.list_docs(sitename, ftype, deleted=True)
            print('list deleted for', ftype, ':', data, file=_out)


def clear_site_contents(sitename):
    "remove site"
    dml.clear_site_data(sitename)
