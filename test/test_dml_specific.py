# testing non-api functions of dml modules

# gather up the single underscore prefixed ones!

import os, sys
import pprint
import datetime
import pathlib
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app_settings import DML, WEBROOT, SETTFILE
if DML == 'fs':
    print('using file system dml')
    import docs2fs as dml
    print('testing _extify...', end=' ')
    path = pathlib.Path(WEBROOT / 'test')
    assert dml._extify(path) == pathlib.Path(WEBROOT / 'test' / 'source')
    assert dml._extify(path, 'src') == pathlib.Path(WEBROOT / 'test' / 'source')
    assert dml._extify(path, 'dest') == pathlib.Path(WEBROOT / 'test' / 'target')
    assert dml._extify(path, 'to_mirror') == pathlib.Path(WEBROOT / 'test')
    print('ok')
    # no real unittests, as these items contain execution time specific data
    subdir = 'guichelheil'
    for key in dml.stat_keys:
        print('testing _get_dir_ftype_stats from root for ftype', key)
        pprint.pprint(dml._get_dir_ftype_stats('test', key))
        print('testing _get_dir_ftype_stats from subdirectory', subdir,
            'for ftype', key)
        pprint.pprint(dml._get_dir_ftype_stats('test', key, subdir))
    print('testing _get_dir_stats from root')
    pprint.pprint(dml._get_dir_stats('test'))
    print('testing _get_dir_stats from subdirectory', subdir)
    pprint.pprint(dml._get_dir_stats('test', subdir))
    # _get_dir_stats_for_docitem
    # _get_sitedoc_data
elif DML == 'mongo':
    print('using mongodb dml')
    import docs2mongo as dml
    # _get_site_id
    # _get_site_doc
    # _update_site_doc
    # _add_doc
    # _update_doc
    # _ get_stats
    # we might test _get_stats here, the rest is merely passing through mongodb query results
elif DML == 'postgres':
    print('using postgresql dml')
    import docs2pg as dml

