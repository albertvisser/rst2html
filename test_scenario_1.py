# test scenario 1

from rst2html_mongo import Rst2Html
from docs2mongo import clear_db as init_db
from test_mongodml import list_database_contents

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

def main():

    # start from scratch
    init_db()

    # simulate starting up the application
    app = Rst2Html()
    data = app.index()
    with open('/tmp/01_index.html', 'w') as _out:
        _out.write(data)

    # simulate loading new conf
    data = app.loadconf('-- new --', '', '', '', '')
    with open('/tmp/02_loadconf_new.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - forgetting to change the name
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    with open('/tmp/03_saveconf_invalid.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - using a new name
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testsite', app.state.rstdata)
    with open('/tmp/04_saveconf_new.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - using an existing name for a new site
    app.state.newconf = True
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testsite', app.state.rstdata)
    with open('/tmp/05_saveconf_existing.html', 'w') as _out:
        _out.write(data)
    app.state.newconf = False

    # simulate loading a document where none exist yet
    data = app.loadrst(app.state.settings, '', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    # gives "Oops!" message because rstfile is empty
    with open('/tmp/06a_loadrst_nonexistant.html', 'w') as _out:
        _out.write(data)
    data = app.loadrst(app.state.settings, 'x', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    # gives "file not found" message
    with open('/tmp/06b_loadrst_nonexistant.html', 'w') as _out:
        _out.write(data)

    # simulate creating a new source document
    data = app.loadrst(app.state.settings, '-- new --', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    with open('/tmp/07_loadrst_new.html', 'w') as _out:
        _out.write(data)

    # simulate saving the new document
    data = app.saverst(app.state.settings, '-- new --', app.state.htmlfile,
        'testdoc1.rst', rstdata_1)
    with open('/tmp/08_saverst_new.html', 'w') as _out:
        _out.write(data)

    # simulate viewing the new document
    data = app.convert(app.state.settings, app.state.rstfile, app.state.htmlfile,
        app.state.newfile, rstdata_1)
    with open('/tmp/09a_convert_new.html', 'w') as _out:
        _out.write(data)

    # simulate viewing the (slightly changed) document
    data = app.convert(app.state.settings, app.state.rstfile, app.state.htmlfile,
        app.state.newfile, rstdata_2)
    with open('/tmp/09b_convert_new_changed.html', 'w') as _out:
        _out.write(data)

    # simulate loading an existing source document
    data = app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    with open('/tmp/10_loadrst_existing.html', 'w') as _out:
        _out.write(data)

    # simulate saving an existing document with more changes as html (and rst)
    data = app.saveall(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, rstdata_3)
    with open('/tmp/11_saveall_w_changes.html', 'w') as _out:
        _out.write(data)

    # simulate loading an existing document and saving under a different name
    data = app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    data = app.saverst(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testdoc1a.rst', app.state.rstdata)
    with open('/tmp/12a_saverst_existing_othername.html', 'w') as _out:
        _out.write(data)

    # simulate loading an existing document and saving as html under a different name
    data = app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    data = app.saveall(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testdoc1a.rst', app.state.rstdata)
    with open('/tmp/12b_saveall_existing_othername.html', 'w') as _out:
        _out.write(data)

    # simulate loading an HTML document
    data = app.loadhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
        app.state.newfile, app.state.rstdata)
    with open('/tmp/13_loadhtml.html', 'w') as _out:
        _out.write(data)

    # simulate rendering an unchanged HTML document
    data = app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
        app.state.newfile, app.state.rstdata)
    with open('/tmp/14a_showhtml.html', 'w') as _out:
        _out.write(data)

    # simulate rendering a changed HTML document - check if it is saved
    data = app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
        app.state.newfile, htmldata_2)
    with open('/tmp/14b_showhtml_modified.html', 'w') as _out:
        _out.write(data)
    # nope, it's not saved - that means it could be gone when we go back to the editor
    # maybe try out in "real life" first before I change this?

    # simulate saving a (changed) HTML document
    data = app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
        app.state.newfile, htmldata_2)
    with open('/tmp/15a_savehtml_modified.html', 'w') as _out:
        _out.write(data)

    # simulate saving an HTML document under a different name - do we allow this?
    data = app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
        'testdoc2.html', htmldata_2)
    with open('/tmp/15b_savehtml_newname.html', 'w') as _out:
        _out.write(data)
    # the system doesn't use the new name (and clears it) - that's how it should be
    # skip this test?

    # simulate promoting a (changed) HTML document to mirror
    data = app.copytoroot(app.state.settings, app.state.rstfile, 'testdoc1.html',
        app.state.newfile, htmldata_2)
    with open('/tmp/16_copytoroot.html', 'w') as _out:
        _out.write(data)

    # simulate building a reference document

    # simulate building a progress list

    # simulate updating all documents




if __name__ == "__main__":
    main()
    list_database_contents()
