"""Backup/restore utility for Rst2Html sites stored in MongoDB format
"""
# backuppen gaat nog wel in tekst, maar voor terugzetten moet deze eerst weer omgezet
# worden naar dicts - waarschijnlijk is het beter om dit met JSON te doen of zo

from clize import Parameter, run
from sigtools.modifiers import annotate, autokwoargs
import docs2mongo as dml

FULLBACKUP_HEADER = '#---------- full backup of rst2html sites ------#\n'

def _backup_site(sitename, stream):
    stream.write('#------------- backup of site {} ------------#\n'.format(sitename))
    sitedoc, data = dml.list_site_data(sitename)
    stream.write(str(sitedoc) + '\n')
    for item in data:
        stream.write(str(item) + '\n')

#@annotate(filename='f')
@autokwoargs
def backup_all(filename):
    """Create a backup of all current Rst2Html sites

    filename: name for the file to backup to
    """
    with open(filename, "w") as _out:
        _out.write(FULLBACKUP_HEADER)
        for sitename in dml.list_sites():
            _backup_site(sitename, _out)

@annotate(sitename=Parameter.REQUIRED)
@autokwoargs
def backup_some(filename, *sitename):
    """Create a backup of one or more Rst2Html sites

    filename: name for the file to backup to
    sitename: list of sites to backup
    """
    with open(filename, "w") as _out:
        for name in sitename:
            _backup_site(name, _out)

# The restore process is not failsafe (yet):
# It's theoretically possible to  restore records of a site that have the same database key
# as existing records of a site that subsequently will be restored.
# In that case clear_site_data() will unfortunately erase those records again.

@annotate(all='A')
@autokwoargs
def restore_all(filename, all=False):
    """restore a previously made backup of one or more Rst2Html sites

    filename: name of the file to restore from
    all: optionally clear out all sites before restoring

    note that the entire contents of the input file (i.e. all of the
    sites included) is restored.
    """
    if all:
        dml.clear_db()
    with open(filename) as _in:
        for line in _in:
            if line == FULLBACKUP_HEADER:
                dml.clear_db()
            elif line.startswith('#'):
                sitename = line[30:].split()[0].strip()
                dml.clear_site_data(sitename)
            else:
                entry = line.rstrip()
                dml.add_sitecoll_doc(entry)

@annotate(sitename=Parameter.REQUIRED)
@autokwoargs
def restore_some(filename, *sitename):
    """restore the named Rst2Html site(s) from a previously made backup

    filename: name of the file to restore from
    sitename: list of sites to backup
    """
    sites_to_restore = sitename
    ok_to_restore = False
    with open(filename) as _in:
        for line in _in:
            if line.startswith('#'):
                site_name = line[30:].split()[0].strip()
                if site_name in sites_to_restore:
                    ok_to_restore = True
                    dml.clear_site_data(sitename)
                else:
                    ok_to_restore = False
            elif ok_to_restore:
                entry = line.rstrip()
                dml.add_sitecoll_doc(entry)

if __name__ == '__main__':
    run(backup_some, backup_all, restore_all, restore_some, description=__doc__)

