# testing non-api functions of dml modules

import os, sys
import pprint
import datetime
import pathlib
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app_settings import FS_WEBROOT, LOCS


def test_fs_extra():
    print('testing extra routines for file system dml...')
    import docs2fs as dml
    print('testing _locify...', end=' ')
    path = pathlib.Path(FS_WEBROOT / 'test')
    assert dml._locify(path) == pathlib.Path(FS_WEBROOT / 'test' / 'source')
    assert dml._locify(path, 'src') == pathlib.Path(FS_WEBROOT / 'test' / 'source')
    assert dml._locify(path, 'dest') == pathlib.Path(FS_WEBROOT / 'test' / 'target')
    assert dml._locify(path, 'to_mirror') == pathlib.Path(FS_WEBROOT / 'test')
    ## print('ok')
    # no real unittests, as these items contain execution time specific data
    ## # this  doesn't work anymore since we're deleting the testsite directly after use
    ## subdir = 'guichelheil'
    # _get_dir_ftype_stats(sitename, ftype, dirname=''):
    ## for key in LOCS:
        ## print('testing _get_dir_ftype_stats from root for ftype', key)
        ## pprint.pprint(dml._get_dir_ftype_stats('test', key))
        ## print('testing _get_dir_ftype_stats from subdirectory', subdir,
            ## 'for ftype', key)
        ## pprint.pprint(dml._get_dir_ftype_stats('test', key, subdir))
    # _get_dir_stats(site_name, dirname=''):
    ## print('testing _get_dir_stats from root')
    ## pprint.pprint(dml._get_dir_stats('test'))
    ## print('testing _get_dir_stats from subdirectory', subdir)
    ## pprint.pprint(dml._get_dir_stats('test', subdir))
    # _get_dir_stats_for_docitem(site_name, dirname='')
    # _get_sitedoc_data(sitename)
    print('ok')

def test_mongo_extra():
    print('testing extra routines for mongodb dml...', end='')
    import docs2mongo as dml
    # _get_site_id(site_name)
    # _get_site_doc(site_name)
    # _add_sitecoll_doc(data) (uitgesterd)
    # _update_site_doc(site_name, site_docs)
    # _add_doc(doc)
    # _update_doc(docid, doc)
    # _ get_stats(docinfo)
    # we might test _get_stats here, the rest is merely passing through mongodb query results
    print('ok')

def test_pgsql_extra():
    print('testing extra routines for postgresql dml...', end='')
    import docs2pg as dml
    # id = _get_site_id(site_name):
    # id = _get_dir_id(site_id, dirname):
    # id_list = _get_all_dir_ids(site_id):
    # name_list = _get_docs_in_dir(dir_id):
    # 3-tuple_= _get_doc_ids(dir_id, docname):
    # 3-tuple = _get_doc_text(doc_id):
    # settings_dict = _get_settings(site_id):
    # _get_site_doc(site_name): - commented out, will probably be discarded
    # new_doc_id =_add_doc()
    # stats_object = _get_stats(docinfo):
    print('ok')

if __name__ == "__main__":
    test_fs_extra()
