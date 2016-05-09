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
    print('testing _extify...', end=' ')
    path = pathlib.Path(FS_WEBROOT / 'test')
    assert dml._extify(path) == pathlib.Path(FS_WEBROOT / 'test' / 'source')
    assert dml._extify(path, 'src') == pathlib.Path(FS_WEBROOT / 'test' / 'source')
    assert dml._extify(path, 'dest') == pathlib.Path(FS_WEBROOT / 'test' / 'target')
    assert dml._extify(path, 'to_mirror') == pathlib.Path(FS_WEBROOT / 'test')
    ## print('ok')
    # no real unittests, as these items contain execution time specific data
    ## # this  doesn't work anymore since we're deleting the testsite directly after use
    ## subdir = 'guichelheil'
    ## for key in LOCS:
        ## print('testing _get_dir_ftype_stats from root for ftype', key)
        ## pprint.pprint(dml._get_dir_ftype_stats('test', key))
        ## print('testing _get_dir_ftype_stats from subdirectory', subdir,
            ## 'for ftype', key)
        ## pprint.pprint(dml._get_dir_ftype_stats('test', key, subdir))
    ## print('testing _get_dir_stats from root')
    ## pprint.pprint(dml._get_dir_stats('test'))
    ## print('testing _get_dir_stats from subdirectory', subdir)
    ## pprint.pprint(dml._get_dir_stats('test', subdir))
    # _get_dir_stats_for_docitem
    # _get_sitedoc_data
    print('ok')

def test_mongo_extra():
    print('testing extra routines for mongodb dml...', end='')
    import docs2mongo as dml
    # _get_site_id
    # _get_site_doc
    # _update_site_doc
    # _add_doc
    # _update_doc
    # _ get_stats
    # we might test _get_stats here, the rest is merely passing through mongodb query results
    print('ok')

def test_pgsql_extra():
    print('testing extra routines for postgresql dml...', end='')
    import docs2pg as dml
    print('ok')

if __name__ == "__main__":
    test_fs_extra()
