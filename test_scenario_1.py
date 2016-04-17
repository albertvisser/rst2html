# test scenario 1

import pprint
from bs4 import BeautifulSoup
from rst2html_mongo import Rst2Html
import docs2mongo as dml
from test_mongodml import list_database_contents, clear_database_contents
from test_mongodml import list_site_contents, clear_site_contents

rstdata_1 = """\
test document
=============

This is the first document
"""
rstdata_2 = """\
test document
=============

This is the (slightly changed) first document
"""
rstdata_3 = """\
test document
=============

This is the (slightly changed) first document

It's been changed even more
"""
rstdata_4 = """\
test document
=============

This is the (slightly changed) first document

It's been changed even more
"""
htmldata_1 = """\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="generator" content="Docutils 0.11: http://docutils.sourceforge.net/" />
<title>test document</title>

</head>
<body>
<div class="document" id="test-document">
<h1 class="title">test document</h1>

<p>This is the (slightly changed) first document</p>
<p>It's been changed even more</p>
</div>
</body>
</html>
"""
htmldata_2 = """\
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="generator" content="Docutils 0.11: http://docutils.sourceforge.net/" />
<title>test document</title>

</head>
<body>
<div class="document" id="test-document">
<h1 class="title">test document</h1>

<p>This is the (slightly changed) first document</p>
<p>It's been changed even more</p>
</div>
<p>This footer was created by editing the HTML and should disappear when the document is regenerated</p>
</body>
</html>
"""
namelist = []
dbdatalist = []
htmldatalist = []
sitename = 'testsite'

def analyze_db_data(name):
    "convert text dump to datastructure"
    # let's use the original stuff instead

def get_db_diff(old, new, olddata, newdata):
    """compare site data dumps
    """
    result = []
    # because we never remove stuff, we can concentrate on what's new
    oldsite, olddocs = olddata
    newsite, newdocs = newdata
    if newsite == oldsite:
        result.append('site data has not changed')
        return result
    if newdocs == olddocs:
        result.append('site docs have not changed')
    ## print(newsite, oldsite)
    if oldsite == {}:
        result.append('new site has been added')
        return result
    for setting in newsite['settings']:
        if setting not in oldsite['settings']:
            result.append('new setting: {} {}'.format(setting, newsite['settings']))
            continue
        if newsite['settings'] != oldsite['settings']:
            result.append('setting {} changed from {} to {}'.format(setting,
                oldsite['settings'], newsite['settings']))
    for subdir in list(newsite['docs']):
        if subdir not in oldsite['docs']:
            result.append('new subdir: {}'.format(subdir))
            continue
        olddir = oldsite['docs'][subdir]
        for doc in newsite['docs'][subdir]:
            if doc not in olddir:
                result.append('new doc in subdir {}: {}'.format(subdir, doc))
                continue
            olddoc = olddir[doc]
            for doctype in newsite['docs'][subdir][doc]:
                if doctype not in olddoc:
                    result.append('new doctype for doc {} in {}: {}'.format(doc,
                        subdir, doctype))
                else:
                    if (newsite['docs'][subdir][doc][doctype]['updated'] !=
                            olddoc[doctype]['updated']):
                        if doctype != 'to_mirror':
                            result.append('{} {} {} was changed'.format(subdir,
                                doc, doctype))
                        else:
                            result.append('{} {} was copied to mirror (again)'
                                ''.format(subdir, doc))
    # document ids are sorted, so what's in newdocs should also be in olddocs
    for ix, doc in enumerate(newdocs):
        if ix < len(olddocs):
            if (doc['current'] != olddocs[ix]['current'] or
                    doc['previous'] != olddocs[ix]['previous']):
                result.append('doc {} is changed'.format(doc['_id']))
        else:
            result.append('doc {} is new'.format(doc['_id']))
    return result


def analyze_html_data(name):
    result = {}
    with open(name) as _in:
        soup = BeautifulSoup(_in)
    test = soup.select('body > form > input')
    if test and test[0]["value"] == 'Back to editor':
        return
    for btn in soup.find_all('button'):
        test = btn.parent
        if (btn.string == 'Back to editor' and
                test.name == 'a' and
                'href' in test.attrs and
                (test['href'].startswith('loadrst?rstfile=') or
                 test['href'].startswith('loadhtml?htmlfile='))):
            return
    for selector in soup.find_all('select'):
        options = []
        selected = ''
        for option in selector.find_all('option'):
            options.append(option.string)
            if 'selected' in option.attrs:
                selected = option.string
        result[selector["name"] + '_list'] = options
        result[selector["name"] + '_name'] = selected
    for inp in soup.find_all('input'):
        if inp.get("name", '') == 'newfile':
            result["newfile_name"] = inp["value"]
            break
    else:
        newfile_name = ''
    result["mld_text"] = soup.find('strong').string
    result["textdata"] = soup.find('textarea').string or ''
    return result

def get_html_diff(old, new, olddata, newdata):
    "compare html output"
    diff = []
    ## olddata = analyze_html_data('/tmp/{}.html'.format(old))
    ## newdata = analyze_html_data('/tmp/{}.html'.format(new))
    for key in olddata:
        if olddata[key] != newdata[key]:
            if key.endswith('_list'):
                for value in olddata[key]:
                    if value not in newdata[key]:
                        diff.append('{}: removed value "{}"'.format(key, value))
                for value in newdata[key]:
                    if value not in olddata[key]:
                        diff.append('{}: added value "{}"'.format(key, value))
            elif key == 'textdata':
                if newdata[key]:
                    diff.append('{} changed'.format(key))
                else:
                    diff.append('{} cleared'.format(key))
            elif key == 'mld_text':
                diff.append('{} is "{}"'.format(key, newdata[key]))
            else:
                diff.append('{}: value was "{}", is now "{}"'.format(key,
                    olddata[key], newdata[key]))
    return diff

def dump_data_and_compare(data, name):
    global namelist, dbdatalist, htmldatalist

    print("---- {} ----".format(name))
    fname = '/tmp/{}.html'.format(name)
    with open(fname, 'w') as _out:
        _out.write(data)
    htmldata = analyze_html_data(fname)

    fname = '/tmp/db_{}'.format(name)
    db_data = list_site_contents(sitename, fname)

    if namelist:
        old, new = namelist[-1], name

        dbresult = get_db_diff(old, new, dbdatalist[-1], db_data)

        if htmldata:
            cmpold, cmpnew = htmldatalist[-1], htmldata
        else:
            cmpold, cmpnew = htmldatalist[-2:]
        htmlresult = sorted(get_html_diff(old, new, cmpold, cmpnew))
        ## htmlresult = []
        ## for hname, olddata, newdata in get_html_diff(old, new, cmpold, cmpnew):
            ## print('difference in {}'.format(hname), end='')
            ## if hname == 'textdata':
                ## print()
            ## else:
                ## print(':')
                ## print('  {}: {}'.format(old, olddata))
                ## print('  {}: {}'.format(new, newdata))
            ## htmlresult.append((hname, old, olddata, new, newdata))
    else:
        dbresult = db_data # []
        htmlresult = htmldata # []
    namelist.append(name)
    dbdatalist.append(db_data)
    if htmldata:
        htmldatalist.append(htmldata)
    return dbresult, htmlresult


def sorted_items(input_dict):
    return [(x, y) for x, y in sorted(input_dict.items())]

def main():

    # simulate starting up the application
    app = Rst2Html()
    dbdata, htmldata = dump_data_and_compare(app.index(), '01_index')
    assert dbdata == ({}, []) # sitedocs index followed by list of site docs
    assert sorted_items(htmldata) == sorted_items({
        'settings_name': '',
        'settings_list': ['-- new --'],
        'rstfile_name': '',
        'rstfile_list': ['-- new --'],
        'htmlfile_name': '',
        'htmlfile_list': ['-- new --'],
        'newfile_name': '',
        'mld_text': ' does not exist',
        'textdata': ''
        })

    # simulate loading new conf
    dbdata, htmldata = dump_data_and_compare(
        app.loadconf('-- new --', '', '', '', ''), '02_loadconf_new')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'mld_text is "New site will be created on save"',
        'textdata changed']

    # simulate saving new conf - forgetting to change the name
    dbdata, htmldata = dump_data_and_compare(
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '03_saveconf_invalid')
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Not a valid filename"']

    # simulate saving new conf - using a new name
    dbdata, htmldata = dump_data_and_compare(
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
            sitename, app.state.rstdata),
        '04_saveconf_new')
    assert dbdata == ['new site has been added']
    assert htmldata == [
        'mld_text is "Settings opgeslagen als testsite"',
        'settings_list: added value "testsite"',
        'settings_name: value was "", is now "testsite"',
        'textdata changed']

    # simulate saving new conf - using an existing name for a new site
    app.state.newconf = True
    dbdata, htmldata = dump_data_and_compare(
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
            sitename, app.state.rstdata),
        '05_saveconf_existing')
    app.state.newconf = False
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Site already exists"']

    # simulate loading a document where none exist yet
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, '', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '06a_loadrst_nonexistant')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'mld_text is "Oops! Page was probably open on closing the browser"']
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'x', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '06b_loadrst_nonexistant')
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Source file does not exist"']

    # simulate creating a new source document
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, '-- new --', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '07_loadrst_new')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'mld_text is "Don\'t forget to supply a new filename on saving"',
        'textdata cleared']

    # simulate saving the new document
    dbdata, htmldata = dump_data_and_compare(
        app.saverst(app.state.settings, '-- new --', app.state.htmlfile,
            'testdoc1.rst', rstdata_1),
        '08a_saverst_new')
    assert dbdata == ['new doc in subdir /: testdoc1']
    assert htmldata == [
        'mld_text is "Rst source saved as testdoc1.rst"',
        'rstfile_list: added value "testdoc1.rst"',
        'rstfile_name: value was "", is now "testdoc1.rst"',
        'textdata changed']

    # simulate creating a new directory
    dbdata, htmldata = dump_data_and_compare(
        app.saverst(app.state.settings, '-- new --', app.state.htmlfile,
            'subdir/', rstdata_1),
        '08b_saverst_newdir')
    assert dbdata == ['new subdir: subdir']
    assert htmldata == [
        'mld_text is "New subdirectory subdir created"',
        'rstfile_list: added value "subdir/"',
        'rstfile_name: value was "testdoc1.rst", is now "subdir/"']

    # simulate entering the new directory
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'subdir/', app.state.htmlfile,
            '', rstdata_1),
        '08c_loadrst_dirdown')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_list: added value ".."',
        'mld_text is "switching to directory subdir"',
        'rstfile_list: added value ".."',
        'rstfile_list: removed value "subdir/"',
        'rstfile_list: removed value "testdoc1.rst"',
        'rstfile_name: value was "subdir/", is now ""',
        'textdata cleared']

    # simulate going back to the root
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, '..', app.state.htmlfile,
            '', rstdata_1),
        '08d_loadrst_dirup')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_list: removed value ".."',
        'mld_text is "switching to parent directory"',
        'rstfile_list: added value "subdir/"',
        'rstfile_list: added value "testdoc1.rst"',
        'rstfile_list: removed value ".."']

    # simulate viewing the new document
    ## app.state.rstdata = rstdata_1
    dbdata, htmldata = dump_data_and_compare(
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
            app.state.newfile, rstdata_1),
        '09a_convert_new')
    assert dbdata == ['/ testdoc1 src was changed']     # is this ok?
    assert htmldata == [                                # not very useful
        'htmlfile_list: removed value ".."',            # we're not showing
        'mld_text is "switching to parent directory"',  # the interface here
        'rstfile_list: added value "subdir/"',
        'rstfile_list: added value "testdoc1.rst"',
        'rstfile_list: removed value ".."']

    ## return
    # simulate viewing the (slightly changed) document
    dbdata, htmldata = dump_data_and_compare(
        app.convert(app.state.settings, app.state.rstfile, app.state.htmlfile,
            app.state.newfile, rstdata_2),
        '09b_convert_new_changed')
    assert dbdata == ['site data has not changed']      # is this ok? (and the rest)
    assert htmldata == [
        'mld_text is "Please enter or select a source (.rst) file name"',
        'textdata changed']

    # simulate loading an existing source document
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '10_loadrst_existing')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'mld_text is "Source file testdoc1.rst loaded"',
        'rstfile_name: value was "", is now "testdoc1.rst"',
        'textdata changed']

    # simulate saving an existing document with more changes as html (and rst)
    dbdata, htmldata = dump_data_and_compare(
        app.saveall(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
            app.state.newfile, rstdata_3),
        '11_saveall_w_changes')
    assert sorted(dbdata) == sorted([
        '/ testdoc1 src was changed',
        'new doctype for doc testdoc1 in /: dest'])
    assert htmldata == [
        'htmlfile_list: added value "testdoc1.html"',
        'htmlfile_name: value was "", is now "testdoc1.html"',
        'mld_text is "Rst converted to html and saved as testdoc1.html"',
        'textdata changed']

    # simulate loading an existing document and saving under a different name
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '12a_loadrst_existing')
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Source file testdoc1.rst loaded"']

    dbdata, htmldata = dump_data_and_compare(
        app.saverst(app.state.settings, app.state.rstfile, app.state.htmlfile,
            'testdoc1a.rst', app.state.rstdata),
        '12a_saverst_existing_othername')
    assert dbdata == ['new doc in subdir /: testdoc1a']
    assert htmldata == [
        'htmlfile_name: value was "testdoc1.html", is now ""',
        'mld_text is "Rst source saved as testdoc1a.rst"',
        'rstfile_list: added value "testdoc1a.rst"',
        'rstfile_name: value was "testdoc1.rst", is now "testdoc1a.rst"']

    # simulate loading an existing document and saving as html under a different name
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '12b_loadrst_existing')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_name: value was "", is now "testdoc1.html"',
        'mld_text is "Source file testdoc1.rst loaded"',
        'rstfile_name: value was "testdoc1a.rst", is now "testdoc1.rst"']

    dbdata, htmldata = dump_data_and_compare(
        app.saveall(app.state.settings, app.state.rstfile, app.state.htmlfile,
            'testdoc1a.rst', app.state.rstdata),
        '12b_saveall_existing_othername')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_name: value was "testdoc1.html", is now ""',
        'mld_text is "Source file already exists"',
        'rstfile_name: value was "testdoc1.rst", is now "testdoc1a.rst"']

    # simulate loading an HTML document
    dbdata, htmldata = dump_data_and_compare(
        app.loadhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
            app.state.newfile, app.state.rstdata),
        '13_loadhtml')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_name: value was "", is now "testdoc1.html"',
        'mld_text is "Target html testdoc1.html loaded"',
        'rstfile_name: value was "testdoc1a.rst", is now "testdoc1.rst"',
        'textdata cleared']

    # simulate rendering an unchanged HTML document
    dbdata, htmldata = dump_data_and_compare(
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
            app.state.newfile, app.state.rstdata),
        '14a_showhtml')
    assert dbdata == ['site data has not changed']
    assert htmldata == [                                        # not very useful
        'htmlfile_name: value was "", is now "testdoc1.html"',  # we're not showing
        'mld_text is "Target html testdoc1.html loaded"',       # the interface here
        'rstfile_name: value was "testdoc1a.rst", is now "testdoc1.rst"',
        'textdata cleared']

    # simulate rendering a changed HTML document - check if it is saved
    dbdata, htmldata = dump_data_and_compare(
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
            app.state.newfile, htmldata_2),
        '14b_showhtml_modified')
    assert dbdata == ['site data has not changed']
    assert htmldata == [                                        # see previous
        'htmlfile_name: value was "", is now "testdoc1.html"',
        'mld_text is "Target html testdoc1.html loaded"',
        'rstfile_name: value was "testdoc1a.rst", is now "testdoc1.rst"',
        'textdata cleared']

    # simulate saving a (changed) HTML document
    dbdata, htmldata = dump_data_and_compare(
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
            app.state.newfile, htmldata_2),
        '15a_savehtml_modified')
    assert dbdata == ['/ testdoc1 dest was changed']
    assert htmldata == ['mld_text is "Modified HTML saved as testdoc1.html"']

    # simulate saving an HTML document under a different name - do we allow this?
    dbdata, htmldata = dump_data_and_compare(
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
            'testdoc2.html', htmldata_2),
        '15b_savehtml_newname')
    assert dbdata == ['/ testdoc1 dest was changed']
    assert htmldata == []   # is this ok?
    # the system doesn't use the new name (and clears it) - that's how it should be
    # skip this test?

    # simulate promoting a (changed) HTML document to mirror
    dbdata, htmldata = dump_data_and_compare(
        app.copytoroot(app.state.settings, app.state.rstfile, 'testdoc1.html',
            app.state.newfile, htmldata_2),
        '16_copytoroot')
    assert dbdata == ['new doctype for doc testdoc1 in /: to_mirror']
    assert htmldata == ['mld_text is "Copied to siteroot/testdoc1.html"']

    # change some documents by adding references
    app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    app.saverst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata + '.. refkey:: ref1: here1\n')
    app.loadrst(app.state.settings, 'testdoc1a.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    app.saverst(app.state.settings, 'testdoc1a.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata + '.. refkey:: ref2: here2\n')

    # simulate updating all documents
    dbdata, htmldata = dump_data_and_compare(
        app.convert_all(app.state.settings, app.state.rstfile, app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '17_convert_all')
    assert sorted(dbdata) == sorted([
        '/ testdoc1 dest was changed',
        '/ testdoc1 was copied to mirror (again)',
        '/ testdoc1 src was changed',
        '/ testdoc1a src was changed'])
    assert htmldata == [
        'htmlfile_name: value was "testdoc1.html", is now ""',              # ok?
        'mld_text is "Site documents regenerated, messages below"',
        'rstfile_name: value was "testdoc1.rst", is now "testdoc1a.rst"',   # ok?
        'textdata changed']

    # simulate building a progress list
    dbdata, htmldata = dump_data_and_compare(
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '18_overview')
    assert dbdata == ['site data has not changed']
    assert htmldata == [
        'htmlfile_name: value was "testdoc1.html", is now ""',              # ok?
        'mld_text is "Site documents regenerated, messages below"',
        'rstfile_name: value was "testdoc1.rst", is now "testdoc1a.rst"',   #ok?
        'textdata changed']

    # simulate building a reference document
    dbdata, htmldata = dump_data_and_compare(
        app.makerefdoc(app.state.settings, app.state.rstfile, app.state.htmlfile,
            app.state.newfile, app.state.rstdata),
        '19_makerefdoc')
    assert dbdata == ['new doc in subdir /: reflist']
    # eigenlijk wil je hier ook zeker weten dat de html gegenereerd is en naar mirror gezet
    assert htmldata == [
        'htmlfile_list: added value "reflist.html"',
        'mld_text is "Index created as reflist.html"',
        'rstfile_list: added value "reflist.rst"',
        'textdata changed']


if __name__ == "__main__":
    # start from scratch
    clear_database_contents()
    ## clear_site_contents('testsite')
    # run the tests
    main()
    # see what we have done
    sitedoc, data = list_site_contents('testsite')
    pprint.pprint(sitedoc)
    for item in data:
        pprint.pprint(item)
    # remove our traces
    ## clear_database_contents()
    ## clear_site_contents('testsite')

