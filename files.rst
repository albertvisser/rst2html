files in this directory
=======================

.gitignore
    git stuff

.hgignore
.hgtags
    mercurial stuff

app_settings_example
    global settings for the application
    you can have variants for each dml type to facilitate testing and running the apps

files.rst
    this file

LICENSE
    legal stuff

mdviewer.py
rstviewer.py
    startup scripts for viewing markup files on the desktop

projdocs.pck/zip + backups (untracked)
    treedocs bestand voor documentatie en development

readme.rst
    information and usage notes

rst2html_*.conf
    cherrypy configuration used by the startup script
    there's a version for each dml variant

run_local.py (untracked)
    module level code extracted from rst2html.py

run_scenariotest
    starter to run the integration tests for all data backends

.rurc
    configuration of unittests (use with `binfab repo.runtests`)

start_rst2html_*.py
    script to start the application with
    because of the way the application is started, a separate version for each data backend is 
    required

use_*
    bash scriptlets to switch out the app_settings between data backends, used by run_scenariotest
    and available for wherever one may seem fit

app/
----
application files directory (package)

custom_directives_template.py
    default source for user-written directives

docs2fs.py
    routines for the file system implementation (data manipulation layer)

docs2mongo.py
    routines for the mongodb implementation (data manipulation layer)

docs2pg.py
    routines for the postgres implementation (data manipulation layer)

dutch.lng
english.lng
    data for homebrew language support

rst2html.html
    the web page (template) in which it all happens

rst2html.py
    the program in which it all happens (presentation layer)

rst2html_directives.py
    all directives used by the application and mentioned in rst2html.html

rst2html_functions.py
    functions and stuff to be used by the webapp (application layer)

search.html
    template for displaying site search results

setup_database.sql
    SQL statements for building the tables for the postgres database

stand.html
    template for displaying the site overview

util/
-----
some helper programs

convert_fs2mongo.py
    used when converting flat files to a mongo database

get_links_for_sitemap (not tracked)
    implementation of ...site search?

r2h_search (untracked)
    another implementation of site search, built as an external program

r2h_util.py
    utility fiunctions for backup restore etc

static/
------
static files for the app to work with; put codemirror javascript library here

960.css
html4css1.css
html4css_960.css
reset.css
    css files to be copied to root of new site
    contain: reset stylesheet, styles for rest conversion, styles for grid_960
    also an all-in one version previously used for rendering in preview mode

htmleditor.js
pyeditor.js
rsteditor.js
yamleditor.js
    syntaxhighlighters for various content in text area

rst2html.ico
    favicon for webapp


tohtml/
-------
stuff used by the markup viewer scripts

htmlfrommd.py
    script to show markdown source in an html window

htmlfromrst.py
    script to show rest source in an html window

makehtml.py
    common code used by these two scripts


unittests/
----------
unittest scripts for the application's core functionality

test_dmlf.py
test_dmlm.py
test_dmlp.py
test_r2h.py
test_rhdir.py
test_rhfn.py

test/
-----
"integration" testscripts

analyze_testdata.py
    functions that help in comparing database and html output, used by test_scenario_1
test_convert_all (untracked)
    uitproberen rhfn.UpdateAll 
test_dml.py
    testscript for the data manipulation layer
test_dml_specific.py
    testscript for non-api functions in the data manipulation layer
test_all_dml.py
    script to run the former for all dml variants, prompts for options 
test_rst2html.py
    testscript for unexposed functions in the presentation layer
test_rst2html_functions.py
    testscript for the application logic layer
test_rhfn_all.py
    script to run the former for all dml variants, takes options from parameters
test_scenario_1.py
    testscript for the web views in the presentation layer
test_all.py
    script to run one or more testscripts with one or all the dml variants
