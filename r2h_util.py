"""Backup/restore utility for Rst2Html sites stored in MongoDB format
"""
# backuppen gaat nog wel in tekst, maar voor terugzetten moet deze eerst weer omgezet
# worden naar dicts - waarschijnlijk is het beter om dit met JSON te doen of zo

import datetime
import json
import bson
## import pprint
from sigtools.modifiers import annotate, autokwoargs
from clize import Parameter, run

import docs2mongo as dml

FULLBACKUP_HEADER = '#---------- full backup of rst2html sites ------#'
siteheader = '#------------- backup of site {} ------------#'


class CustomJSONEncoder(json.JSONEncoder):
    """Processing class for doing the backup
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        else:
            return super().default(obj)


def custom_decoder(obj):
    """read the backup data file
    """
    if isinstance(obj, dict):
        if 'docid' in obj:
            obj['docid'] = bson.objectid.ObjectId(obj['docid'])
        if 'updated' in obj:
            obj['updated'] = datetime.datetime.strptime(
                obj['updated'], "%Y-%m-%dT%H:%M:%S.%f")
        if '_id' in obj:
            obj['_id'] = bson.objectid.ObjectId(obj['_id'])
    return obj

## def _backup_site(sitename):
    ## stream.write(.format(sitename))
    ## sitedoc, data = dml.list_site_data(sitename)
    ## stream.write(str(sitedoc) + '\n')
    ## for item in data:
        ## stream.write(str(item) + '\n')


def _get_site_data(sitename):
    sitedoc, data = dml.list_site_data(sitename)
    return siteheader.format(sitename), sitedoc, [x for x in data]


def _do_backup(outlist, siteslist, filename):
    for sitename in siteslist:
        outlist.append(_get_site_data(sitename))
    filename = filename.replace('%d', datetime.datetime.today().strftime("%Y%m%d_%H%M%S"))
    print('writing backup to {}'.format(filename))
    with open(filename, "w") as _out:
        json.dump(outlist, _out, cls=CustomJSONEncoder)


@autokwoargs    # @annotate(filename='f')
def backup_all(filename):
    """Create a backup of all current Rst2Html sites

    filename: name for the file to backup to (use %d to include a date-time stamp)
    """
    _do_backup([FULLBACKUP_HEADER], dml.list_sites(), filename)


@annotate(sitename=Parameter.REQUIRED)
@autokwoargs
def backup_some(filename, *sitename):
    """Create a backup of one or more Rst2Html sites

    filename: name for the file to backup to (use %d to include a date-time stamp)
    sitename: list of sites to backup
    """
    _do_backup([], sitename, filename)

# The restore process is not failsafe (yet):
# scenarios:
# - restore to an exising site - refuse unless a -f option is provided or answered by prompt
# - site to restore contains existing keys - need to make sure which existing key belongs to
#  which site so we know if it's a site we can overwrite


def _get_backup_data(filename):
    with open(filename) as _in:
        inlist = json.load(_in, object_hook=custom_decoder)
    return inlist


def _restore_site(sitename, sitedoc, data):
    dml.clear_site_data(sitename)
    dml.add_sitecoll_doc(sitedoc)
    for doc in data:
        dml.add_sitecoll_doc(doc)


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
    inlist = _get_backup_data(filename)
    start = 0
    if inlist[0] == FULLBACKUP_HEADER:
        dml.clear_db()
        start += 1
    for line in inlist[start:]:
        header, sitedoc, data = line
        sitename = line[30:].split()[0].strip()
        _restore_site(sitename, sitedoc, data)


@annotate(sitename=Parameter.REQUIRED)
@autokwoargs
def restore_some(filename, *sitename):
    """restore the named Rst2Html site(s) from a previously made backup

    filename: name of the file to restore from
    sitename: list of sites to backup
    """
    sites_to_restore = sitename
    inlist = _get_backup_data(filename)
    for line in inlist:
        header, sitedoc, data = line
        sitename = line[30:].split()[0].strip()
        if sitename in sites_to_restore:
            _restore_site(sitename, sitedoc, data)

if __name__ == '__main__':
    run(backup_some, backup_all, restore_all, restore_some, description=__doc__)
