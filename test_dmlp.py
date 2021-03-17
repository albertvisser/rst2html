import docs2pg as dmlp

# class DbWrapper
# r. 25:      def __init__(self, f):
#                 pass
# r. 28:      def __call__(self, *args, **kwargs):
#                 pass
# module level code
# r. 36:  def wrapit(f):
#             pass
# function wrapit
# r. 39:      def wrapping(*args, **kwargs):
#                 pass

def _is_equal(x, y):
    pass

def _get_site_id(site_name):
    pass

def _get_dir_id(site_id, dirname):
    pass

def _get_all_dir_ids(site_id):
    pass

def _get_docs_in_dir(dir_id):
    pass

def _get_doc_ids(dir_id, docname):
    pass

def _get_doc_text(doc_id):
    pass

def _get_settings(site_id):
    pass

def _add_doc():
    pass

def _get_stats(docinfo):
    pass

def clear_db():
    pass

def read_db():
    pass

def list_sites():
    pass

def create_new_site(site_name):
    pass

def rename_site(site_name, newname):
    pass

def read_settings(site_name):
    pass

def update_settings(site_name, settings_dict):
    pass

def clear_settings(site_name):  # untested - do I need/want this?
    pass
    pass


def list_dirs(site_name, doctype=''):
    pass

def create_new_dir(site_name, directory):
    pass

def remove_dir(site_name, directory):  # untested - do I need/want this?
    pass

def list_docs(site_name, doctype='', directory='', deleted=False):
    pass

def list_templates(site_name):
    pass

def read_template(site_name, doc_name):
    pass

def write_template(site_name, doc_name, data):
    pass

def create_new_doc(site_name, doc_name, directory=''):
    pass

def get_doc_contents(site_name, doc_name, doctype='', directory=''):
    pass

def update_rst(site_name, doc_name, contents, directory=''):
    pass

def mark_src_deleted(site_name, doc_name, directory=''):
    pass

def update_html(site_name, doc_name, contents, directory='', dry_run=True):
    pass

def apply_deletions_target(site_name, directory=''):
    pass

def update_mirror(site_name, doc_name, data, directory='', dry_run=True):
    pass

def apply_deletions_mirror(site_name, directory=''):
    pass

def get_doc_stats(site_name, docname, dirname=''):
    pass

def get_all_doc_stats(site_name):
    pass

def list_site_data(site_name):
    pass

def clear_site_data(site_name):
    pass

