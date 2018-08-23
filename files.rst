files in this directory
=======================

.hgignore
.hgtags
    mercurial stuff

app_settings_example
    global settings for the application
    there are variants for each dml type to facilitate testing and running the apps

convert_fs2mongo.py

custom_directives_template.py
    default source for user-written directives

directives_bitbucket.py
    directives designed for use on my BitBucket pages

directives_grid.py
    directives designed for applying grid_960 layout

directives_magiokis.py
    directives designed for use on my Magiokis pages

docs2fs.py
    routines for the file system implementation (data manipulation layer)

docs2mongo.py
    routines for the mongodb implementation (data manipulation layer)

docs2pg.py
    routines for the postgres implementation (data manipulation layer)

dutch.lng
english.lng
    data for homebrew language support

fcgi_handler.py
    server program for fastcgi (not used)

files.rst
    this file

LICENSE
    legal stuff

mdviewer.py
rstviewer.py
    startup scripts for viewing markup files on the desktop

readme.rst
    information and usage notes

r2h_util.py
    utility fiunctions for backup restore etc

rst2html.conf
    cherrypy configuration used by the startup script
    there's a version for each dml variant

rst2html.html
    the web page (template) in which it all happens

rst2html.py
    the program in which it all happens (presentation layer)

rst2html_functions.py
    functions and stuff to be used by the webapp (application layer)

setup_database.sql
    SQL statements for building the tables for the postgres database

stand.html
    template for displaying the site overview

start_rst2html.py
    script to start the application with
    there's a version for each dml variant

wsgi_handler.py
    another script to start the app as a wsgi server (not used)


static/
    static files for the app to work with; put codemirror javascript library here

    static/960.css
    static/html4css1.css
    static/html4css_960.css
    static/reset.css
        css files to be copied to root of new site
        contain: reset stylesheet, styles for rest conversion, styles for grid_960
        also an all-in one version previously used for rendering in preview mode
    static/htmleditor.js
    static/pyeditor.js
    static/rsteditor.js
    static/yamleditor.js
        syntaxhighlighters for various content in text area
    static/rst2html.ico
        favicon for webapp


tohtml/
    stuff used by the markup viewer scripts

    htmlfrommd.py
        script to show markdown source in an html window

    htmlfromrst.py
        script to show rest source in an html window

    makehtml.py
        common code used by these two scripts


test/
    directory for tests and testscripts

    analyze_testdata.py
        functions that help in comparing database and html output, used by test_scenario_1
    assert_equals.py (untracked)
        script to change lines of code containing assert statements into lines containing assert_equal function calls
    test_directives.py (untracked)
        script to test directives for bitbucket site    
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
