"""testing a standard set of actions in Rst2HTML web application
deze resultaten worden bewaard op de Comparer klassen om de situatie tussen twee tests te kunnen
vergelijken
omdat het anders dan bij unittests de bedoeling is deze achter elkaar en in een vaste volgorde
uit te voeren
 """
import os
import shutil
## import pprint
import app.rst2html as r2h   # from rst2html import Rst2Html
# import test.analyze_testdata
from test import analyze_testdata
DML = analyze_testdata.DML
dml = analyze_testdata.dml

from test.fixtures import rstdata_1, rstdata_2, rstdata_3, htmldata_2
confs_to_restore_after_changing = ['misc/hosts', 'nginx/flatpages']
conf_root = os.path.expanduser('~/nginx-config/')


def test_main(monkeypatch, capsys, tmp_path):
    "call main() using pytest, to make monkeypatching possible"
    destdir = tmp_path / DML
    for conf in confs_to_restore_after_changing:
        (tmp_path / os.path.dirname(conf)).mkdir()
        shutil.copyfile(os.path.join(conf_root, conf), str(tmp_path / conf))
    # if .exists(destdir):
    #     shutil.rmtree(destdir)
    destdir.mkdir()
    sitename = analyze_testdata.sitename    # start from scratch
    analyze_testdata.clear_site_contents(sitename)           # clear_database_contents()
    main(monkeypatch, capsys, destdir)      # run the tests
    # niet nodig
    # sitedoc, data = list_site_contents(sitename, filename=os.path.join(destdir,
    #                                                                    'test_scenario_1.out'))
    # clear_site_contents(sitename)           # remove our traces
    for conf in confs_to_restore_after_changing:
        shutil.copyfile(str(tmp_path / conf), os.path.join(conf_root, conf))


def main(monkeypatch, capsys, path):
    """main processing"""
    counter = 0
    # simulate starting up the application
    app = r2h.Rst2Html()
    sitename = analyze_testdata.sitename
    comp = analyze_testdata.Comparer(DML, path)
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_index', app.index())
    assert dbdata == ({}, [])  # sitedocs index followed by list of site docs
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'].startswith('Settings file is')
    old_textdata = htmldata['textdata']

    # simulate loading new conf
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadconf_new',
          app.loadconf('-- new --', '', '', '', ''))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    # standard settings
    assert htmldata['textdata'] == "css: []\nhig: 32\nurl: ''\nwid: 100\nwriter: html5\n"
    old_textdata = htmldata['textdata']
    assert htmldata['rstfile']['values'] == ['-- new --']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == (
            "New site will be created on save - don\'t forget to provide a name for it")

    # simulate saving new conf - forgetting to change the name
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveconf_invalid',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    # settings ongewijzigd
    assert htmldata['textdata'] == old_textdata
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Not a valid filename"

    # simulate saving new conf - using a new name
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveconf_new',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     sitename, app.state.rstdata))
    assert dbdata == ['site docs have not changed', 'new site has been added']
    assert 'testsite' in htmldata['settings']['values']
    # assert htmldata['settings']['selected'] == 'testsite'
    assert htmldata['title'] == 'ReStructured Text translator'
    # standaard settings + ingevulde url + ingevulde css
    assert htmldata['textdata'] == (
            "css:\n- url + css/minimal.css\n- url + css/plain.css\n"
            "hig: 32\nurl: http://testsite.lemoncurry.nl\nwid: 100\nwriter: html5\n")
    assert htmldata['mld_text'] == (
            "Settings saved as testsite ; activate the new site using `fabsrv"
            " modconfb -n hosts nginx.modconfb -n flatpages nginx.restart`")

    # simulate saving new conf - using an existing name for a new site
    app.state.newconf = True
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveconf_existing',
        app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     sitename, app.state.rstdata))
    app.state.newconf = False
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['settings']['selected'] == 'testsite'
    assert htmldata['mld_text'] == "site_name_taken"

    # simulate loading a document where none exist yet
    # # special case first: no source name (doesn't normally happen)
    # # ik wil hier eigenlijk laten zien wat er gebeurt als je na restarten van de server
    # # verder gaat op andere pagina dan de index, dit is niet de goede manier
    # dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_notreloaded',
    #     app.loadrst(app.state.settings, '', app.state.htmlfile,
    #                 app.state.newfile, app.state.rstdata))
    # assert dbdata, ['site data has not changed']
    # assert htmldata['title'] == 'ReStructured Text translator'
    # assert htmldata['mld_text'] == "Oops! Page was probably open on closing the browser"

    # om dezelfde reden als hierboven zou onderstaande situatie ook net mogelijk zijn?
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_nonexistant',
        app.loadrst(app.state.settings, 'x', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['values'] == ['-- new --']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    doc = r2h.rhfn.WEBROOT / 'testsite' / '.source' / 'x.rst'
    # de database versies geven een eigengemaakte melding bij een FileNotFoudError
    if DML == 'fs':
        message = f"[Errno 2] No such file or directory: '{doc}'"
    else:  # DML in ('mongo', 'postgres'):
        message = "Document 'x' not found in collection"
    assert htmldata['mld_text'] == message

    # simulate creating a new source document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_new',
        app.loadrst(app.state.settings, '-- new --', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['values'] == ['-- new --']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['mld_text'] == "Don\'t forget to supply a new filename on saving"
    assert htmldata['textdata'] == ''

    # simulate trying to save the new document without providing a name
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_invalid',
        app.saverst(app.state.settings, '-- new --', '', rstdata_1(), ''))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['values'] == ['-- new --']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['mld_text'] == "Source file does not exist"
    assert htmldata['textdata'] == rstdata_1()

    # simulate creating a template
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_template',
        app.saverst(app.state.settings, '-- new --', 'template.tpl', 'xxxx', ''))
    assert dbdata == ['site docs have not changed',
                      'new template template.tpl added']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Template saved as template.tpl"
    assert htmldata['rstfile']['values'] == ['-- new --', '-- template.tpl --']
    assert "-- template.tpl --" in htmldata['rstfile']['values']
    assert htmldata['textdata'] == 'xxxx'
    # simulate loading a template
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_template',
        app.loadrst(app.state.settings, '-- template.tpl --', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Don\'t forget to supply a new filename on saving"
    assert htmldata['rstfile']['values'] == ['-- new --', '-- template.tpl --']
    assert htmldata['rstfile']['selected'] == ''
    assert htmldata['textdata'] == 'xxxx'
    # simulate renaming the template
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_rename_template',
    app.saverst(app.state.settings, 'template.tpl', 'newtpl.tpl', 'xxxx', 'rename'))
    assert dbdata == ['site docs have not changed',
                      'new template newtpl.tpl added', 'template template.tpl removed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "template.tpl renamed to newtpl.tpl"
    assert htmldata['rstfile']['values'] == ['-- new --', '-- newtpl.tpl --']
    assert htmldata['rstfile']['selected'] == ''
    assert "-- newtpl.tpl --" in htmldata['rstfile']['values']
    assert htmldata['textdata'] == 'xxxx'
    # simulate deleting the template
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_delete_template',
        app.saverst(app.state.settings, 'newtpl.tpl', '', 'xxxx', 'delete'))
    assert dbdata == ['site docs have not changed',
                      'template newtpl.tpl removed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "newtpl.tpl deleted"
    assert htmldata['rstfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == ''
    # # create the template again
    # app.saverst(app.state.settings, '-- new --', 'template.tpl', 'xxxx', '')
    # # load the template
    # app.loadrst(app.state.settings, '-- template.tpl --', app.state.htmlfile, app.state.newfile,
    #             app.state.rstdata)

    # simulate saving the new document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_new',
        app.saverst(app.state.settings, '-- new --', 'testdoc1.rst', rstdata_1(), ''))
    assert dbdata == ['new doc in subdir /: testdoc1', "doc ('testdoc1', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc1.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', 'testdoc1.rst']
    assert "testdoc1.rst" in htmldata['rstfile']['values']
    assert htmldata['textdata'] == rstdata_1()

    # simulate creating a new directory
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_newdir',
        app.saverst(app.state.settings, '-- new --', 'sublevel/', rstdata_1(), ''))
    assert dbdata == ['site docs have not changed', 'new subdir: sublevel']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "New subdirectory sublevel created"
    assert htmldata['rstfile']['values'] == ['-- new --', 'sublevel/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'sublevel/'
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == rstdata_1()

    # simulate trying to rename the new directory
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_renamedir_err',
        app.saverst(app.state.settings, 'sublevel/', 'subdir', rstdata_1(), 'rename'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "wrong name for new subdirectory: must end in /"
    assert htmldata['rstfile']['values'] == ['-- new --', 'sublevel/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'sublevel/'
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == rstdata_1()

    # simulate renaming the new directory
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_renamedir',
        app.saverst(app.state.settings, 'sublevel/', 'subdir/', rstdata_1(), 'rename'))
    assert dbdata == ['site docs have not changed',
                      'new subdir: subdir', 'subdir removed: sublevel']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert "sublevel/" not in htmldata['rstfile']['values']
    assert "subdir/" in htmldata['rstfile']['values']
    assert htmldata['mld_text'] == "sublevel/ renamed to subdir/"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'subdir/'
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == rstdata_1()

    # simulate entering the new directory
    # foute naam opgeven kan niet, want je moet hem selecteren
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_dirdown',
        app.loadrst(app.state.settings, 'subdir/', app.state.htmlfile, '', rstdata_1()))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert "subdir/" not in htmldata['rstfile']['values']
    assert ".." in htmldata['rstfile']['values']
    assert htmldata['mld_text'] == "switching to directory subdir"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['htmlfile']['values'] == ['-- new --', '..']
    assert htmldata['textdata'] == ''

    # save a new document in the subdirectory
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_new_in_subdir',
        app.saverst(app.state.settings, '-- new --', 'testdoc1.rst', rstdata_1(), ''))
    assert dbdata == ['new doc in subdir subdir: testdoc1', "doc ('subdir/testdoc1', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc1.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', '..', 'testdoc1.rst']
    assert htmldata['htmlfile']['values'] == ['-- new --', '..']
    assert htmldata['textdata'] == rstdata_1()
    # try to delete the subdirectory - should fail
    # niet mogelijk omdat je binnen en directory de directory zelf niet kunt selecteren

    # simulate going back to the root
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_dirup',
        app.loadrst(app.state.settings, '..', app.state.htmlfile, '', rstdata_1()))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert "testdoc1.rst" in htmldata['rstfile']['values']
    assert "subdir/" in htmldata['rstfile']['values']
    assert htmldata['mld_text'] == "switching to parent directory"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == ''

    # try to delete the subdirectory again - should fail again
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_deletedir',
        app.saverst(app.state.settings, 'subdir/', '', rstdata_1(), 'delete'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "directory subdir/ is niet leeg"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['textdata'] == rstdata_1()

    # simulate viewing the new document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_convert_new',
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_1()))
    assert dbdata == ['/ testdoc1 src was changed', "doc ('testdoc1', 'src') is changed"]
    assert htmldata['title'] == 'test document'
    assert 'rstfile' not in htmldata
    assert 'htmlfile' not in htmldata
    assert htmldata['backlink'] == '/loadrst/?rstfile=testdoc1.rst&settings=testsite'
    assert htmldata['pagetext'] == '\ntest document\nThis is the first document\n'

    # simulate viewing the (slightly changed) document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_convert_changed',
        app.convert(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, rstdata_2()))
    assert dbdata == ['/ testdoc1 src was changed', "doc ('testdoc1', 'src') is changed"]
    assert htmldata['title'] == 'test document'
    assert 'rstfile' not in htmldata
    assert 'htmlfile' not in htmldata
    assert htmldata['backlink'] == '/loadrst/?rstfile=testdoc1.rst&settings=testsite'
    assert htmldata['pagetext'] == '\ntest document\nThis is the (slightly changed) first document\n'

    # simulate loading an existing source document to view changes
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_changes',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata, 'changes'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == 'Recent changes for testdoc1.rst loaded'
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['textdata'] == (
            "--- previous text\n+++ current text\n@@ -1,4 +1,4 @@\n"
            " test document\n =============\n \n-This is the first document\n"
            "+This is the (slightly changed) first document\n")

    # simulate loading an existing source document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_existing',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == 'Source file testdoc1.rst loaded'
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['textdata'] == rstdata_2()

    # simulate saving an existing document with more changes as html (and rst)
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveall_w_error',
        app.saveall(app.state.settings, 'testdoc1.rst', app.state.newfile,
                    rstdata_3() + "\n\n.. error::\n"))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     # 'new doctype for doc testdoc1 in /: dest',
                                     # "doc ('testdoc1', 'dest') is new",
                                     "doc ('testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert 'testdoc1.html' not in htmldata['htmlfile']['values']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['mld_text'] == "Error(s) occurred while generating HTML"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_3() + "\n\n.. error::\n"
    message = capsys.readouterr().err
    assert 'Content block expected for the "error" directive; none found.\n' in message

    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveall_w_changes',
        app.saveall(app.state.settings, 'testdoc1.rst', app.state.newfile, rstdata_3()))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     'new doctype for doc testdoc1 in /: dest',
                                     "doc ('testdoc1', 'dest') is new",
                                     "doc ('testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['mld_text'] == "Rst converted to HTML and saved as testdoc1.html"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an existing document and saving under a different name
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_existing_2',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Source file testdoc1.rst loaded"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['textdata'] == rstdata_3()

    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_existing_othername',
        app.saverst(app.state.settings, app.state.rstfile, 'testdoc1a.rst', app.state.rstdata, ''))
    assert dbdata == ['new doc in subdir /: testdoc1a', "doc ('testdoc1a', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc1a.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an existing document and saving as html under a different name
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadrst_existing',
        app.loadrst(app.state.settings, 'testdoc1.rst', app.state.htmlfile,
                    app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Source file testdoc1.rst loaded"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert htmldata['textdata'] == rstdata_3()

    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saveall_existing_othername',
        app.saveall(app.state.settings, app.state.rstfile, 'testdoc1a.rst', app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Source file already exists"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_3()

    # simulate loading an HTML document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_loadhtml',
        app.loadhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Target HTML testdoc1.html loaded"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>') in htmldata['textdata']
    assert htmldata['textdata'] != rstdata_3()

    counter += 1
    # simulate rendering an unchanged HTML document
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_showhtml',
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadhtml/?htmlfile=testdoc1.html&settings=testsite'
    assert htmldata['pagetext'] == ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    counter += 1
    # simulate rendering a changed HTML document - check if it is saved
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_showhtml_modified',
        app.showhtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, htmldata_2()))
    assert dbdata == ['/ testdoc1 dest was changed', "doc ('testdoc1', 'dest') is changed"]
    assert htmldata['title'] == 'test document'
    assert htmldata['backlink'] == '/loadhtml/?htmlfile=testdoc1.html&settings=testsite'
    assert htmldata['pagetext'] == ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    counter += 1
    # simulate saving a (changed) HTML document
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_savehtml_modified',
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     app.state.newfile, htmldata_2()))
    assert dbdata == ['/ testdoc1 dest was changed', "doc ('testdoc1', 'dest') is changed"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Modified HTML saved as testdoc1.html"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']
    assert htmldata['textdata'] != ('\ntest document\nThis is the (slightly changed) first document\n'
                            "It's been changed even more\n")

    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_savehtml_newname',
        app.savehtml(app.state.settings, app.state.rstfile, 'testdoc1.html',
                     'testdoc2.html', htmldata_2()))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Not executed: can only save HTML under the same name"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']

    # simulate promoting a (changed) HTML document to mirror
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_copytoroot',
        app.copytoroot(app.state.settings, app.state.rstfile, 'testdoc1.html',
                       app.state.newfile, htmldata_2()))
    # this may look weird, but is correct: mirror data is not included in the docs comparison:
    assert dbdata == ['site docs have not changed', 'new doctype for doc testdoc1 in /: mirror']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Generated HTML copied to siteroot/testdoc1.html"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    # zit wel in de HTML, maar BS4 pikt het niet op (HTML binnen HTML)
    # assert ('<div class="document" id="test-document">\n<h1 class="title">test document</h1>\n\n'
    #         "<p>This is the (slightly changed) first document</p>\n<p>It's been changed even"
    #         ' more</p>\n</div>\n<p>This footer was created by editing the HTML and should'
    #         ' disappear when the document is regenerated</p>') in htmldata['textdata']

    # simulate getting the status of a document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_status',
        app.loadrst(app.state.settings, app.state.rstfile, 'testdoc1.html',
                    app.state.newfile, rstdata_2(), 'status'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1.html'
    assert ('/testdoc1.rst: last modified: ' in htmldata['mld_text']
            and ' - last converted: ' in htmldata['mld_text']
            and ' - last migrated: ' in htmldata['mld_text'])
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

    # simulate updating all documents (view mode)
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_convert_all_view',
        app.convert_all(app.state.settings, app.state.rstfile, app.state.htmlfile,
                        app.state.newfile, app.state.rstdata, regsubj='3'))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     '/ testdoc1a src was changed',
                                     "doc ('testdoc1a', 'src') is changed",
                                     "doc ('testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == (
            "Site documents regenerated (in simulation) giving the following messages")
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == (
            "/testdoc1: target and mirror html need to be regenerated\n"
            "/testdoc1a: target and mirror html need to be regenerated\n"
            "subdir/testdoc1: target and mirror html need to be regenerated")

    # simulate updating all documents
    # dat de dbdata meldingen m.b.t de src documenten niet zichtbaar zijn wanneer je dit draait
    # met de preview eerst heeft te maken met de vergelijking t.o.v. de vorige functieaanroep
    # en is dus geen gevolg van dat er wat anders gebeurt tijdens de functieuitvoering
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_convert_all',
        app.convert_all(app.state.settings, app.state.rstfile, app.state.htmlfile,
                        app.state.newfile, app.state.rstdata, regsubj="0"))
    assert sorted(dbdata) == sorted([  # '/ testdoc1 src was changed',
                                     '/ testdoc1 dest was changed',
                                     '/ testdoc1 was copied to mirror (again)',
                                     # '/ testdoc1a src was changed',
                                     'new doctype for doc testdoc1a in /: dest',
                                     'new doctype for doc testdoc1a in /: mirror',
                                     # "doc ('testdoc1a', 'src') is changed",
                                     # "doc ('testdoc1', 'src') is changed",
                                     "doc ('testdoc1a', 'dest') is new",
                                     "doc ('testdoc1', 'dest') is changed",
                                     'new doctype for doc testdoc1 in subdir: dest',
                                     'new doctype for doc testdoc1 in subdir: mirror',
                                     "doc ('subdir/testdoc1', 'dest') is new"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Site documents regenerated  giving the following messages"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.rst', 'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1a.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == 'testdoc1a.html'
    assert htmldata['textdata'] == ('Modified HTML saved as /testdoc1\n'
                                    'Generated HTML copied to /testdoc1\n'
                                    'Modified HTML saved as /testdoc1a\n'
                                    'Generated HTML copied to /testdoc1a\n'
                                    'Modified HTML saved as subdir/testdoc1\n'
                                    'Generated HTML copied to subdir/testdoc1')

    # simulate building a progress list
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_overview',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by date\n\n\nCopy to file\n' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_copy_overview_name',
                                                  app.copystand(order='name'))
    siteroot = r2h.rhfn.WEBROOT / sitename
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by date\n\n\nCopy to file\n' in htmldata['pagetext']
            and 'Overview exported to ' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    file_exists = False
    for item in (siteroot / '.overview').iterdir():
        if not item.suffix:
            item.rename(item.with_suffix('.name'))
            file_exists = True
    assert file_exists
    # nog een keer een overview doen maar nu met andere sortering
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_overview_date',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata, order='date'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by name\n\n\nCopy to file\n' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_copy_overview_date',
                                                  app.copystand(order='date'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by name\n\n\nCopy to file\n' in htmldata['pagetext']
            and 'Overview exported to ' in htmldata['pagetext']
            # and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext']
            )
    file_exists = False
    for item in (siteroot / '.overview').iterdir():
        if not item.suffix:
            item.rename(item.with_suffix('.date'))
            file_exists = True
    assert file_exists

    # simulate building a reference document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_makerefdoc',
        app.makerefdoc(app.state.settings, app.state.rstfile, app.state.htmlfile,
                       app.state.newfile, app.state.rstdata))
    assert sorted(dbdata) == sorted(['new doc in subdir /: reflist',
                                     "doc ('reflist', 'src') is new",
                                     "doc ('reflist', 'dest') is new"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Index created as reflist.html"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == "reflist.rst"
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == "reflist.html"
    assert htmldata['textdata'] == ('.. _top:\n`back to root </>`_\n\n.. textheader:: Index\n'
                                   'R_ \n\nR\n-\n\n+   Ref1 `#`__ \n+   Ref2 `#`__ \n+   top_\n\n'
                                   '..  _R1: /testdoc1.html#here1\n..  _R2: /testdoc1a.html#here2\n'
                                   '\n__ R1_\n__ R2_\n')

    # simulate changing a document and reverting it
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_to_revert',
        app.saverst(app.state.settings, '-- new --', 'testdoc2.rst', rstdata_1()))
    assert dbdata == ['new doc in subdir /: testdoc2', "doc ('testdoc2', 'src') is new"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc2.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst', 'testdoc2.rst']
    assert htmldata['rstfile']['selected'] == "testdoc2.rst"
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_changed',
        app.saverst(app.state.settings, 'testdoc2.rst', '', rstdata_2()))
    assert dbdata == ['/ testdoc2 src was changed', "doc ('testdoc2', 'src') is changed"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "Rst source saved as testdoc2.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst', 'testdoc2.rst']
    assert htmldata['rstfile']['selected'] == "testdoc2.rst"
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_2()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_revert',
        app.saverst(app.state.settings, 'testdoc2.rst', '', rstdata_2(), 'revert'))
    assert dbdata == ['/ testdoc2 src was changed', "doc ('testdoc2', 'src') is changed"]

    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc2.rst reverted to backup"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst', 'testdoc2.rst']
    assert htmldata['rstfile']['selected'] == "testdoc2.rst"
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()

    # simulate renaming a document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_rename',
        app.saverst(app.state.settings, 'testdoc2.rst', 'testdoc3.rst', rstdata_1(), 'rename'))
    assert sorted(dbdata) == sorted(['new doc in subdir /: testdoc3',
                                     '/ testdoc2 src was marked as deleted',
                                     "doc ('testdoc2', 'src') is removed",
                                     "doc ('testdoc3', 'src') is new"])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc2.rst renamed to testdoc3.rst"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst', 'testdoc3.rst']
    assert htmldata['rstfile']['selected'] == "testdoc3.rst"
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()

    # simulate deleting a document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_delete',
        app.saverst(app.state.settings, 'testdoc3.rst', '', rstdata_1(), 'delete'))
    assert sorted(dbdata) == sorted(["doc ('testdoc3', 'src') is removed",
                                     '/ testdoc3 src was marked as deleted'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc3.rst deleted"
    assert htmldata['rstfile']['values'] == ['-- new --', 'subdir/', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', 'subdir/', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert "testdoc3.rst" not in htmldata['rstfile']['values']
    assert htmldata['textdata'] == ''

    # simulate propagating deletions separately (migdel (- all 4 subfunctions)
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_src',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '0'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for target: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_overview_2',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by date\n\n\nCopy to file\n' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_src',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '1'))
    assert sorted(dbdata) == sorted(['site docs have not changed',
                                     'new doctype for doc testdoc2 in /: dest',
                                     'new doctype for doc testdoc3 in /: dest'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from target: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_dest',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '2'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for mirror: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_overview_3',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by date\n\n\nCopy to file\n' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_dest',
        app.migdel(app.state.settings, 'testdoc3.rst', 'testdoc3.html', '', rstdata_1(), '3'))
    assert sorted(dbdata) == sorted(['site docs have not changed',
                                     'doc removed from subdir /: testdoc3',
                                     'doc removed from subdir /: testdoc2'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from mirror: testdoc2, testdoc3"
    assert htmldata['textdata'] == rstdata_1()
    # resultaat laten zien werkt nog niet omdat ik niet naar niet meer bestaande zaken kijk?
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_overview_4',
        app.overview(app.state.settings, app.state.rstfile, app.state.htmlfile,
                     app.state.newfile, app.state.rstdata))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html stand van zaken overzicht'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert ('\n\n\nBack to editor\n\n\nOrder by date\n\n\nCopy to file\n' in htmldata['pagetext']
            and '\n\n\n\npagina\nsource\ntarget\nmirror' in htmldata['pagetext'])

    # start search
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_start_search',
        app.find_screen(app.state.settings, '', '', '', ''))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    # execute search
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_execute_search',
        app.find_results('document', ''))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert ('the following lines / parts were found:'
            '\n\n\n\n\n\n\npagina\nregel\ntekst\n\n\n\n\n') in htmldata['pagetext']
    # execute replace
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_execute_replace',
        app.find_results('document', 'doc-u-mint'))
    assert sorted(dbdata) == sorted(['/ testdoc1 src was changed',
                                     "doc ('testdoc1', 'src') is changed",
                                     '/ testdoc1a src was changed',
                                     "doc ('testdoc1a', 'src') is changed",
                                     'subdir testdoc1 src was changed',
                                     "doc ('subdir/testdoc1', 'src') is changed"])
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert ('the following lines / parts were replaced:'
            '\n\n\n\n\n\n\npagina\nregel\ntekst\n\n\n\n\n') in htmldata['pagetext']
    # repeat search
    app.find_results('doc-u-mint', '')
    # copy results to file
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_copy_results',
        app.copysearch())
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'Rst2Html Search in source documenten'
    assert htmldata['backlink'] == "/loadconf/?settings=testsite"
    assert 'Zoek naar:' in htmldata['pagetext']
    assert 'Vervang door:' in htmldata['pagetext']
    assert 'Search results copied to ' in htmldata['pagetext']
    file_exists = False
    for item in (siteroot / '.search-results').iterdir():
        if item.name.startswith('doc-u-mint'):
            file_exists = True
            break
    assert file_exists

    # go back into the subdirectory, delete the document there and propagate the deletion
    # eerst nog even dit document naar target zetten, dat is een situatie die ik nog niet heb
    app.loadrst(app.state.settings, 'subdir/', app.state.htmlfile, '', rstdata_1())
    # simulate deleting a document
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_delete_2',
        app.saverst(app.state.settings, 'testdoc1.rst', '', rstdata_1(), 'delete'))
    assert sorted(dbdata) == sorted(["doc ('subdir/testdoc1', 'src') is removed",
                                     'subdir testdoc1 src was marked as deleted'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "testdoc1.rst deleted"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', '..', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == "testdoc1.html"
    assert htmldata['textdata'] == ''
    # kijken of er pending deletions zijn en zo ja, deze uitvoeren
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_src_2',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '0'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for target: subdir/testdoc1"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', '..', 'testdoc1.html']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_src_2',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '1'))
    assert sorted(dbdata) == sorted(["doc ('subdir/testdoc1', 'dest') is removed",
                                     'subdir testdoc1 dest was marked as deleted'])
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from target: subdir/testdoc1"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', '..']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_dest_2',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '2'))
    assert dbdata == ['site data has not changed', 'site docs have not changed']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for mirror: subdir/testdoc1"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', '..']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_dest_2',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '3'))
    assert dbdata == ['site docs have not changed', 'doc removed from subdir subdir: testdoc1']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from mirror: subdir/testdoc1"
    assert htmldata['rstfile']['values'] == ['-- new --', '..']
    assert htmldata['rstfile']['selected'] == ""
    assert htmldata['htmlfile']['values'] == ['-- new --', '..']
    assert htmldata['htmlfile']['selected'] == ""
    assert htmldata['textdata'] == rstdata_1()

    app.loadrst(app.state.settings, '..', app.state.htmlfile, '', rstdata_1())
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_saverst_deletedir_2',
        app.saverst(app.state.settings, 'subdir/', '', rstdata_1(), 'delete'))
    assert dbdata == ['site docs have not changed', "subdir 'subdir' is removed in src"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "subdir deleted"
    assert htmldata['rstfile']['values'] == ['-- new --', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == ''
    assert htmldata['htmlfile']['values'] == ['-- new --', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == ''
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_src_3',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '0'))
    assert dbdata == ['site data has not changed', 'site docs have not changed',
                      "subdir 'subdir' is removed in src"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for target: subdir/"
    assert htmldata['rstfile']['values'] == ['-- new --', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_src_3',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '1'))
    assert dbdata == ['site docs have not changed', "subdir 'subdir' is removed in src and dest"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from target: subdir/"
    assert htmldata['rstfile']['values'] == ['-- new --', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_show_dest_3',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '2'))
    assert dbdata == ['site data has not changed', 'site docs have not changed',
                      "subdir 'subdir' is removed in src and dest"]
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "pending deletions for mirror: subdir/"
    assert htmldata['rstfile']['values'] == ['-- new --', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_1()
    counter += 1
    dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_migdel_exec_dest_3',
        app.migdel(app.state.settings, 'testdoc1.rst', '', '', rstdata_1(), '3'))
    assert dbdata == ['site docs have not changed', 'subdir removed: subdir']
    assert htmldata['title'] == 'ReStructured Text translator'
    assert htmldata['mld_text'] == "deleted from mirror: subdir/"
    assert htmldata['rstfile']['values'] == ['-- new --', 'reflist.rst', 'testdoc1.rst',
                                             'testdoc1a.rst']
    assert htmldata['rstfile']['selected'] == 'testdoc1.rst'
    assert htmldata['htmlfile']['values'] == ['-- new --', 'reflist.html', 'testdoc1.html',
                                              'testdoc1a.html']
    assert htmldata['htmlfile']['selected'] == ''
    assert htmldata['textdata'] == rstdata_1()

    # check texts for missing classes in used directives
    # TODO eerst uitzoeken of ik hiervoor iets kan monkeypatchen
    # counter += 1
    # dbdata, htmldata = comp.dump_data_and_compare(f'{counter:02}_check_site_docs',
    #     app.check(app.state.settings, '', '', '', ''))
    # assert dbdata == ['site data has not changed']
    # assert htmldata['title'] == 'Rst2Html Search in source documenten'


# def sorted_items(input_dict):
#     """sort data for easier comparison"""
#     return [list(sorted(input_dict.items()))]
