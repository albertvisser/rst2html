"""testing a standard scenario of actions in Rst2HTML web application
"""
import os
import sys
## import pprint
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rst2html import Rst2Html
## from rst2html_all import Rst2Html
from analyze_testdata import sitename, dump_data_and_compare  # , get_db_diff, \
#    analyze_html_data, get_html_diff
from test_dml import list_site_contents, clear_site_contents

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


def sorted_items(input_dict):
    """sort data for easier comparison"""
    return [(x, y) for x, y in sorted(input_dict.items())]


def main():
    """main processing"""
    # simulate starting up the application
    app = Rst2Html()
    dbdata, htmldata = dump_data_and_compare(app.index(), '01_index')
    assert dbdata == ({}, [])  # sitedocs index followed by list of site docs
    # initial html data is not very useful
    ## assert sorted_items(htmldata) == sorted_items({
        ## 'settings_name': '',
        ## 'settings_list': ['-- new --'],
        ## 'rstfile_name': '',
        ## 'rstfile_list': ['-- new --'],
        ## 'htmlfile_name': '',
        ## 'htmlfile_list': ['-- new --'],
        ## 'newfile_name': '',
        ## 'mld_text': ' does not exist',
        ## 'textdata': ''
        ## })

    # simulate loading new conf
    dbdata, htmldata = dump_data_and_compare(
        app.loadconf('-- new --', '', '', '', ''), '02_loadconf_new')
    assert dbdata == ['site data has not changed']
    assert ('mld_text is "New site will be created on save - don\'t forget to '
            'provide a name for it"') in htmldata
    assert 'textdata changed' in htmldata

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
    assert 'new site has been added' in dbdata
    assert 'site docs have not changed' in dbdata
    assert htmldata == ['mld_text is "Settings opgeslagen als testsite; '
                        'note that previews won\'t work with empty url setting"',
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
    assert dbdata == ['new doc in subdir /: testdoc1',
                      "doc ('testdoc1', 'src') is new"]
    assert htmldata == ['mld_text is "Rst source saved as testdoc1.rst"',
                        'rstfile_list: added value "testdoc1.rst"',
                        'rstfile_name: value was "", is now "testdoc1.rst"',
                        'textdata changed']

    # simulate creating a new directory
    dbdata, htmldata = dump_data_and_compare(
        app.saverst(app.state.settings, '-- new --', app.state.htmlfile,
                    'subdir/', rstdata_1),
        '08b_saverst_newdir')
    assert dbdata == ['site docs have not changed', 'new subdir: subdir']
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
        app.loadrst(app.state.settings, '..', app.state.htmlfile, '', rstdata_1),
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
    assert dbdata == ['/ testdoc1 src was changed',
                      "doc ('testdoc1', 'src') is changed"]  # unconditional save
    assert htmldata == [                                # not very useful
        'htmlfile_list: removed value ".."',            # we're not showing
        'mld_text is "switching to parent directory"',  # the interface here
        'rstfile_list: added value "subdir/"',
        'rstfile_list: added value "testdoc1.rst"',
        'rstfile_list: removed value ".."']

    ## return
    # simulate viewing the (slightly changed) document
    dbdata, htmldata = dump_data_and_compare(
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_2),
        '09b_convert_new_changed')
    assert dbdata == ['/ testdoc1 src was changed',
                      "doc ('testdoc1', 'src') is changed"]
    assert htmldata == [                                # not very useful
        'htmlfile_list: removed value ".."',            # we're not showing
        'mld_text is "switching to parent directory"',  # the interface here
        'rstfile_list: added value "subdir/"',
        'rstfile_list: added value "testdoc1.rst"',
        'rstfile_list: removed value ".."']

    # simulate loading an existing source document
    dbdata, htmldata = dump_data_and_compare(
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata),
        '10_loadrst_existing')
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Source file testdoc1.rst loaded"',
                        'rstfile_name: value was "", is now "testdoc1.rst"',
                        'textdata changed']

    # simulate saving an existing document with more changes as html (and rst)
    dbdata, htmldata = dump_data_and_compare(
        app.saveall(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_3),
        '11_saveall_w_changes')
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     'new doctype for doc testdoc1 in /: dest',
                                     "doc ('testdoc1', 'dest') is new",
                                     "doc ('testdoc1', 'src') is changed"])
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
    assert dbdata == ['new doc in subdir /: testdoc1a',
                      "doc ('testdoc1a', 'src') is new"]
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
    # earlier it was not saved, now it is:
    ## assert dbdata == ['site data has not changed']
    assert dbdata == ['/ testdoc1 dest was changed',
                      "doc ('testdoc1', 'dest') is changed"]
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
    assert dbdata == ['/ testdoc1 dest was changed',
                      "doc ('testdoc1', 'dest') is changed"]
    assert htmldata == ['mld_text is "Modified HTML saved as testdoc1.html"']

    # simulate saving an HTML document under a different name - do we allow this?
    dbdata, htmldata = dump_data_and_compare(
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     'testdoc2.html', htmldata_2),
        '15b_savehtml_newname')
    assert dbdata == ['site data has not changed']
    assert htmldata == ['mld_text is "Not executed: can only save HTML '
                        'under the same name"']
    # the system doesn't use the new name (and clears it) - that's how it should be
    # skip this test?

    # simulate promoting a (changed) HTML document to mirror
    dbdata, htmldata = dump_data_and_compare(
        app.copytoroot(app.state.settings, app.state.rstfile, 'testdoc1.html',
                       app.state.newfile, htmldata_2),
        '16_copytoroot')
    # this looks weird, but is correct: mirror data is not included in the docs comparison
    assert dbdata == ['site docs have not changed',
                      'new doctype for doc testdoc1 in /: to_mirror']
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
        '/ testdoc1a src was changed',
        "doc ('testdoc1', 'src') is changed",
        "doc ('testdoc1', 'dest') is changed",
        "doc ('testdoc1a', 'src') is changed"])
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
    assert htmldata == ['htmlfile_name: value was "testdoc1.html", is now ""',              # ok?
                        'mld_text is "Site documents regenerated, messages below"',
                        'rstfile_name: value was "testdoc1.rst", '
                        'is now "testdoc1a.rst"',   # ok?
                        'textdata changed']

    # simulate building a reference document
    dbdata, htmldata = dump_data_and_compare(
        app.makerefdoc(app.state.settings, app.state.rstfile, app.state.htmlfile,
                       app.state.newfile, app.state.rstdata),
        '19_makerefdoc')
    assert sorted(dbdata) == sorted(['new doc in subdir /: reflist',
                                     "doc ('reflist', 'src') is new",
                                     "doc ('reflist', 'dest') is new"])
    # eigenlijk wil je hier ook zeker weten dat de html gegenereerd is en naar mirror gezet
    assert htmldata == ['htmlfile_list: added value "reflist.html"',
                        'mld_text is "Index created as reflist.html"',
                        'rstfile_list: added value "reflist.rst"',
                        'textdata changed']


if __name__ == "__main__":
    # start from scratch
    ## clear_database_contents()
    clear_site_contents('testsite')
    # run the tests
    main()
    # see what we have done
    sitedoc, data = list_site_contents('testsite')
    ## pprint.pprint(sitedoc)
    ## for item in data:
        ## pprint.pprint(item)
    # remove our traces
    ## clear_database_contents()
    clear_site_contents('testsite')
