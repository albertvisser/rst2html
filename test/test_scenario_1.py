"""testing a standard set of actions in Rst2HTML web application
deze resultaten worden bewaard op de Comparer klassen om de situatie tussen twee tests te kunnen
vergelijken
omdat het anders dan bij unittests de bedoeling is deze achter elkaar en in een vaste volgorde
uit te voeren
 """
import sys
import os
import shutil
import pytest  # kijken of ik rhfn.check_url kan monkeypatchen
## import pprint
print(sys.path)
import app.rst2html as r2h   # from rst2html import Rst2Html
# import test.analyze_testdata
from test import analyze_testdata
from test.test_dml import DML, clear_site_contents  # , list_site_contents

from test.fixtures import rstdata_1, rstdata_2, rstdata_3, rstdata_4, htmldata_1, htmldata_2
confs_to_restore_after_changing = ['misc/hosts', 'nginx/flatpages']
conf_root = os.path.expanduser('~/nginx-config/')

def test_main(monkeypatch, capsys, tmp_path):
    "call main() using pytest, to make monkeypatching possible"
    destdir = tmp_path /  DML
    for conf in confs_to_restore_after_changing:
        (tmp_path / os.path.dirname(conf)).mkdir()
        shutil.copyfile(os.path.join(conf_root, conf), str(tmp_path / conf))
    # if .exists(destdir):
    #     shutil.rmtree(destdir)
    destdir.mkdir()
    sitename = analyze_testdata.sitename    # start from scratch
    clear_site_contents(sitename)           # clear_database_contents()
    main(monkeypatch, capsys, destdir)      # run the tests
    # niet nodig
    # sitedoc, data = list_site_contents(sitename, filename=os.path.join(destdir,
    #                                                                    'test_scenario_1.out'))
    # clear_site_contents(sitename)           # remove our traces
    for conf in confs_to_restore_after_changing:
        shutil.copyfile(str(tmp_path / conf), os.path.join(conf_root, conf))


def main(monkeypatch, capsys, path):
    """main processing"""
    # simulate starting up the application
    app = r2h.Rst2Html()
    sitename = analyze_testdata.sitename
    comp = analyze_testdata.Comparer(DML, path)
    dbdata, htmldata = comp.dump_data_and_compare('01_index', app.index())
    assert dbdata == ({}, [])  # sitedocs index followed by list of site docs
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'].startswith('Settings file is')
    old_textdata = htmldata['textdata']

    # simulate loading new conf
    dbdata, htmldata = comp.dump_data_and_compare('02_loadconf_new',
          app.loadconf('-- new --', '', '', '', ''))
    assert dbdata == ['site data has not changed']
    # standard settings
    assert htmldata['textdata'] == "css: []\nhig: 32\nurl: ''\nwid: 100\nwriter: html5\n"
    old_textdata = htmldata['textdata']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == (
            "New site will be created on save - don\'t forget to provide a name for it")

    # simulate saving new conf - forgetting to change the name
    dbdata, htmldata = comp.dump_data_and_compare('03_saveconf_invalid',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    # settings ongewijzigd
    # assert htmldata['textdata'] == "css: []\nhig: 32\nurl: ''\nwid: 100\nwriter: html5\n"
    assert htmldata['textdata'] == old_textdata
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Not a valid filename"

    # # check_url bij uitzondering patchen anders krijgen we een endless loop
    # monkeypatch.setattr(r2h.rhfn, 'check_url', lambda x: True)

    # simulate saving new conf - using a new name
    dbdata, htmldata = comp.dump_data_and_compare('04_saveconf_new',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     sitename, app.state.rstdata))
    assert dbdata == ['site docs have not changed', 'new site has been added']
    assert 'testsite' in htmldata['settings']['values']
    assert htmldata['settings']['selected'] == 'testsite'
    assert htmldata['title'] == 'ReStructured Text translator'
    # standaard settings + ingevulde url + ingevulde css
    assert htmldata['textdata'] == (
            "css:\n- url + css/minimal.css\n- url + css/plain.css\n"
            "hig: 32\nurl: http://testsite.lemoncurry.nl\nwid: 100\nwriter: html5\n")
    assert htmldata['mld_text'] == ("Settings saved as testsite ; activate the new site using `fabsrv"
                                    " modconfb -n hosts nginx.modconfb -n flatpages nginx.restart`")

    # simulate saving new conf - using an existing name for a new site
    app.state.newconf = True
    dbdata, htmldata = comp.dump_data_and_compare('05_saveconf_existing',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     sitename, app.state.rstdata))
    app.state.newconf = False
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['settings']['selected'] == 'testsite'
    assert htmldata['mld_text'] == "site_name_taken"

    # simulate loading a document where none exist yet
    # special case first: no source name (doesn't normally happen)
    dbdata, htmldata = comp.dump_data_and_compare('06a_loadrst_nonexistant',
        app.loadrst(app.state.settings, '', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata, ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Oops! Page was probably open on closing the browser"

    dbdata, htmldata = comp.dump_data_and_compare('06b_loadrst_nonexistant',
        app.loadrst(app.state.settings, 'x', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Source file does not exist"

    # simulate creating a new source document
    dbdata, htmldata = comp.dump_data_and_compare('07_loadrst_new',
        app.loadrst(app.state.settings, '-- new --', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Don\'t forget to supply a new filename on saving"
    assert htmldata['textdata'] == ''

    # simulate saving the new document
    dbdata, htmldata = comp.dump_data_and_compare('08a_saverst_new',
        app.saverst(app.state.settings, '-- new --', 'testdoc1.rst', rstdata_1(),''))
    assert dbdata == ['new doc in subdir /: testdoc1', "doc ('testdoc1', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc1.rst"
    assert "testdoc1.rst" in htmldata['rstfile']['values']
    assert htmldata['textdata'] == rstdata_1()

    # simulate creating a new directory
    dbdata, htmldata = comp.dump_data_and_compare('08b_saverst_newdir',
        app.saverst(app.state.settings, '-- new --', 'subdir/', rstdata_1(), ''))
    assert dbdata == ['site docs have not changed', 'new subdir: subdir']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "New subdirectory subdir created"
    assert "subdir/" in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == "subdir/"
    assert htmldata['textdata'] == rstdata_1()

    # simulate entering the new directory
    dbdata, htmldata = comp.dump_data_and_compare('08c_loadrst_dirdown',
        app.loadrst(app.state.settings, 'subdir/', app.state.htmlfile, '', rstdata_1()))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert ".." in htmldata['rstfile']['values']
    assert htmldata['mld_text'] == "switching to directory subdir"
    assert htmldata['textdata'] == ''

    # simulate going back to the root
    dbdata, htmldata = comp.dump_data_and_compare('08d_loadrst_dirup',
        app.loadrst(app.state.settings, '..', app.state.htmlfile, '', rstdata_1()))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert "testdoc1.rst" in htmldata['rstfile']['values']
    assert "subdir/" in htmldata['rstfile']['values']
    assert htmldata['mld_text'] == "switching to parent directory"
    assert htmldata['textdata'] == ''

    # simulate viewing the new document
    dbdata, htmldata = comp.dump_data_and_compare('09a_convert_new',
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_1()))
    assert dbdata == ['/ testdoc1 src was changed', "doc ('testdoc1', 'src') is changed"]
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadrst/?rstfile=testdoc1.rst&settings=testsite'
    assert htmldata['pagetext'] == '\ntest document\nThis is the first document\n'


    # simulate viewing the (slightly changed) document
    dbdata, htmldata = comp.dump_data_and_compare('09b_convert_changed',
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_2()))
    assert dbdata == ['/ testdoc1 src was changed', "doc ('testdoc1', 'src') is changed"]
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadrst/?rstfile=testdoc1.rst&settings=testsite'
    assert htmldata['pagetext'] == '\ntest document\nThis is the (slightly changed) first document\n'

    # simulate loading an existing source document to view changes
    dbdata, htmldata = comp.dump_data_and_compare('09c_loadrst_changes',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata, 'changes'))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['mld_text'] == 'Recent changes for testdoc1.rst loaded'
    assert htmldata['textdata'] == (
            "--- current text\n+++ previous text\n@@ -1,4 +1,4 @@\n"
            " test document\n =============\n \n-This is the first document\n"
            "+This is the (slightly changed) first document\n")

    # simulate loading an existing source document
    dbdata, htmldata = comp.dump_data_and_compare('10_loadrst_existing',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['mld_text'] == 'Source file testdoc1.rst loaded'
    assert htmldata['textdata'] == rstdata_2()

    # simulate saving an existing document with more changes as html (and rst)
    dbdata, htmldata = comp.dump_data_and_compare('11_saveall_w_changes',
        app.saveall(app.state.settings, 'testdoc1.rst', app.state.newfile, rstdata_3()))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                         'new doctype for doc testdoc1 in /: dest',
                                         "doc ('testdoc1', 'dest') is new",
                                         "doc ('testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] == "Rst converted to HTML and saved as testdoc1.html"
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an existing document and saving under a different name
    dbdata, htmldata = comp.dump_data_and_compare('12a_loadrst_existing',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] == "Source file testdoc1.rst loaded"
    assert htmldata['textdata'] == rstdata_3()

    dbdata, htmldata = comp.dump_data_and_compare('12a_saverst_existing_othername',
        app.saverst(app.state.settings, app.state.rstfile, 'testdoc1a.rst', app.state.rstdata, ''))
    assert dbdata == ['new doc in subdir /: testdoc1a', "doc ('testdoc1a', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert 'testdoc1.rst' in htmldata['rstfile']['values']
    assert 'testdoc1a.rst' in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['mld_text'] == "Rst source saved as testdoc1a.rst"
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an existing document and saving as html under a different name
    dbdata, htmldata = comp.dump_data_and_compare('12b_loadrst_existing',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert 'testdoc1.rst' in htmldata['rstfile']['values']
    assert 'testdoc1a.rst' in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] == "Source file testdoc1.rst loaded"
    assert htmldata['textdata'] == rstdata_3()

    dbdata, htmldata = comp.dump_data_and_compare('12b_saveall_existing_othername',
        app.saveall(app.state.settings, app.state.rstfile, 'testdoc1a.rst', app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert 'testdoc1.rst' in htmldata['rstfile']['values']
    assert 'testdoc1a.rst' in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['mld_text'] == "Source file already exists"
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an HTML document
    dbdata, htmldata = comp.dump_data_and_compare('13_loadhtml',
        app.loadhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert 'testdoc1.rst' in htmldata['rstfile']['values']
    assert 'testdoc1a.rst' in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert 'testdoc1.html' in htmldata['htmlfile']['values']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] == "Target HTML testdoc1.html loaded"
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>') in htmldata['textdata']
    assert htmldata['textdata'] != rstdata_3()

    # simulate rendering an unchanged HTML document
    dbdata, htmldata = comp.dump_data_and_compare('14a_showhtml',
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadhtml/?htmlfile=testdoc1.html&settings=testsite'
    assert htmldata['pagetext'] == ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    # simulate rendering a changed HTML document - check if it is saved
    dbdata, htmldata = comp.dump_data_and_compare('14b_showhtml_modified',
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, htmldata_2()))
    assert dbdata == ['/ testdoc1 dest was changed', "doc ('testdoc1', 'dest') is changed"]
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadhtml/?htmlfile=testdoc1.html&settings=testsite'
    assert htmldata['pagetext'] == ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    # simulate saving a (changed) HTML document
    dbdata, htmldata = comp.dump_data_and_compare('15a_savehtml_modified',
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, htmldata_2()))
    assert dbdata == ['/ testdoc1 dest was changed', "doc ('testdoc1', 'dest') is changed"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Modified HTML saved as testdoc1.html"
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']
    assert htmldata['textdata'] != ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    dbdata, htmldata = comp.dump_data_and_compare('15b_savehtml_newname',
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     'testdoc2.html', htmldata_2()))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] ==  "Not executed: can only save HTML under the same name"
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']

    # simulate promoting a (changed) HTML document to mirror
    dbdata, htmldata = comp.dump_data_and_compare('16_copytoroot',
        app.copytoroot(app.state.settings, app.state.rstfile, 'testdoc1.html',
                       app.state.newfile, htmldata_2()))
    # this may look weird, but is correct: mirror data is not included in the docs comparison:
    assert dbdata == ['site docs have not changed', 'new doctype for doc testdoc1 in /: mirror']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['mld_text'] == "Generated HTML copied to siteroot/testdoc1.html"
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']

    # simulate getting the status of a document
    dbdata, htmldata = comp.dump_data_and_compare('16a_status',
        app.loadrst(app.state.settings, app.state.rstfile, 'testdoc1.html',
                       app.state.newfile, rstdata_2(), 'status'))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert ('/testdoc1.rst: last modified: ' in htmldata['mld_text'] and
            ' - last converted: ' in htmldata['mld_text'] and
            ' - last migrated: ' in htmldata['mld_text'])
    assert htmldata['textdata'] == rstdata_2()

    # change some documents by adding references
    app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                app.state.newfile, app.state.rstdata)
    app.saverst(app.state.settings, 'testdoc1.rst', app.state.newfile,
            app.state.rstdata + '\n.. refkey:: ref1: here1\n', '')
    app.loadrst(app.state.settings, 'testdoc1a.rst', app.state.htmlfile,
                app.state.newfile, app.state.rstdata)
    app.saverst(app.state.settings, 'testdoc1a.rst', app.state.newfile,
            app.state.rstdata + '\n.. refkey:: ref2: here2\n', '')

    # simulate updating all documents
    dbdata, htmldata = comp.dump_data_and_compare('17_convert_all',
        app.convert_all(app.state.settings, app.state.rstfile, app.state.htmlfile,
                        app.state.newfile, app.state.rstdata))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                         '/ testdoc1 dest was changed',
                                         '/ testdoc1 was copied to mirror (again)',
                                         '/ testdoc1a src was changed',
                                         'new doctype for doc testdoc1a in /: dest',
                                         'new doctype for doc testdoc1a in /: mirror',
                                         "doc ('testdoc1a', 'src') is changed",
                                         "doc ('testdoc1', 'src') is changed",
                                         "doc ('testdoc1a', 'dest') is new",
                                         "doc ('testdoc1', 'dest') is changed"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Site documents regenerated  giving the following messages"
    assert htmldata['textdata'] == ('Modified HTML saved as /testdoc1\n'
                                    'Generated HTML copied to /testdoc1\n'
                                    'Modified HTML saved as /testdoc1a\n'
                                    'Generated HTML copied to /testdoc1a')

    # simulate building a progress list
    dbdata, htmldata = comp.dump_data_and_compare('18_overview',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nCopy to file\n' in htmldata['pagetext'] and
            '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    #18a copy overzicht to file
    dbdata, htmldata = comp.dump_data_and_compare('18a_copy_overview', app.copystand())
    # TODO wel een test op dat dit file aangemaakt wordt in alle versies
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nCopy to file\n' in htmldata['pagetext'] and
            'Overview exported to ' in htmldata['pagetext'] and
            '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])

    # simulate building a reference document
    dbdata, htmldata = comp.dump_data_and_compare('19_makerefdoc',
        app.makerefdoc(app.state.settings, app.state.rstfile, app.state.htmlfile,
                       app.state.newfile, app.state.rstdata))
    print(capsys.readouterr().out)
    assert sorted(dbdata), sorted(['new doc in subdir /: reflist',
                                         "doc ('reflist', 'src') is new",
                                         "doc ('reflist', 'dest') is new"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Index created as reflist.html"
    # de home link </> wordt opgeslokt door BS4 waardoor er > overblijft
    assert htmldata['textdata'] == ('.. _top:\n`back to root >`_\n\n.. textheader:: Index\n'
                                   'R_ \n\nR\n-\n\n+   Ref1 `#`__ \n+   Ref2 `#`__ \n+   top_\n\n'
                                   '..  _R1: /testdoc1.html#here1\n..  _R2: /testdoc1a.html#here2\n'
                                   '\n__ R1_\n__ R2_\n')

    # simulate changing a document and reverting it
    dbdata, htmldata = comp.dump_data_and_compare('20a_saverst_new',
        app.saverst(app.state.settings, '-- new --', 'testdoc2.rst', rstdata_1()))
    dbdata, htmldata = comp.dump_data_and_compare('20b_saverst_changed',
        app.saverst(app.state.settings, 'testdoc2.rst', '', rstdata_2()))
    assert dbdata == ['/ testdoc2 src was changed', "doc ('testdoc2', 'src') is changed"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc2.rst"
    assert "testdoc2.rst" in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == "testdoc2.rst"
    assert htmldata['textdata'] == rstdata_2()
    dbdata, htmldata = comp.dump_data_and_compare('20c_saverst_revert',
        app.saverst(app.state.settings, 'testdoc2.rst', '', rstdata_2(), 'revert'))
    assert "doc ('testdoc2', 'src') is changed" in dbdata
    # fs versie detecteert wijzging niet in de file statistics
    # want de backup krijgt dezelfde datetime als het origineel
    if DML != 'fs':
        assert '/ testdoc2 src was changed' in dbdata
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc2.rst reverted to backup"
    assert "testdoc2.rst" in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == "testdoc2.rst"
    assert htmldata['textdata'] == rstdata_1()

    # simulate renaming a document
    dbdata, htmldata = comp.dump_data_and_compare('21_saverst_rename',
        app.saverst(app.state.settings, 'testdoc2.rst', 'testdoc3.rst', rstdata_1(), 'rename'))
    assert sorted(dbdata) == sorted(['new doc in subdir /: testdoc3',
                                     '/ testdoc2 src was marked as deleted',
                                     "doc ('testdoc2', 'src') is removed",
                                      "doc ('testdoc3', 'src') is new"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc2.rst renamed to testdoc3.rst"
    assert "testdoc2.rst" not in htmldata['rstfile']['values']
    assert "testdoc3.rst" in htmldata['rstfile']['values']
    assert htmldata['rstfile']['selected'] == "testdoc3.rst"
    assert htmldata['textdata'] == rstdata_1()

    # simulate deleting a document
    dbdata, htmldata = comp.dump_data_and_compare('22_saverst_delete',
        app.saverst(app.state.settings, 'testdoc3.rst', '', rstdata_1(), 'delete'))
    assert sorted(dbdata) == sorted([ "doc ('testdoc3', 'src') is removed",
                                     '/ testdoc3 src was marked as deleted'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc3.rst deleted"
    assert "testdoc3.rst" not in htmldata['rstfile']['values']
    assert htmldata['textdata'] == ''

    # simulate propagating deletions separately (migdel (- all 4 subfunctions)
    # FIXME dml.list_site_contents voorziet nog niet in deletion marks
    dbdata, htmldata = comp.dump_data_and_compare('23a_migdel_show_src',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '0'))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for target: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    dbdata, htmldata = comp.dump_data_and_compare('23a_overview',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nCopy to file\n' in htmldata['pagetext'] and
            '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    dbdata, htmldata = comp.dump_data_and_compare('23b_migdel_exec_src',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '1'))
    assert sorted(dbdata) == sorted(['site docs have not changed',
                                     'new doctype for doc testdoc2 in /: dest',
                                     'new doctype for doc testdoc3 in /: dest'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from target: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    dbdata, htmldata = comp.dump_data_and_compare('23c_migdel_show_dest',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '2'))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for mirror: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    dbdata, htmldata = comp.dump_data_and_compare('23c_overview',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nCopy to file\n' in htmldata['pagetext'] and
            '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    dbdata, htmldata = comp.dump_data_and_compare('23d_migdel_exec_dest',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '3'))
    assert dbdata == ['site docs have not changed']  # hier ontbreekt wat
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from mirror: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()

    # start search
    dbdata, htmldata = comp.dump_data_and_compare('24a_start_search',
        app.find_screen(app.state.settings, '', '', '', ''))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    # execute search
    dbdata, htmldata = comp.dump_data_and_compare('24b_execute_search',
        app.find_results('document', ''))
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert ('the following lines / parts were found:'
            '\n\n\n\n\n\n\npagina\nregel\ntekst\n\n\n\n\n') in htmldata['pagetext']
    # execute replace
    dbdata, htmldata = comp.dump_data_and_compare('24c_execute_replace',
        app.find_results('document', 'doc-u-mint'))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     '/ testdoc1a src was changed',
                                     "doc ('testdoc1a', 'src') is changed",
                                     "doc ('testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert ('the following lines / parts were replaced:'
            '\n\n\n\n\n\n\npagina\nregel\ntekst\n\n\n\n\n') in htmldata['pagetext']
    # repeat search
    app.find_results('doc-u-mint', '')
    # copy results to file
    dbdata, htmldata = comp.dump_data_and_compare('24d_copy_results',
        app.copysearch())
    # TODO wel een test op dat dit file aangemaakt wordt in alle versies
    assert dbdata == ['site data has not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert 'Search results copied to ' in htmldata['pagetext']

    # check texts for missing classes in used directives
    # TODO eerst uitzoeken of ik hiervoor iets kan monkeypatchen
    # dbdata, htmldata = comp.dump_data_and_compare('25_check_site_docs',
    #     app.check(app.state.settings, '', '', '', ''))
    # assert dbdata == ['site data has not changed']
    # assert htmldata['title'] == 'Rst2Html Search in source documenten'


def sorted_items(input_dict):
    """sort data for easier comparison"""
    return [(x, y) for x, y in sorted(input_dict.items())]
