files in this directory
=======================

.hgignore
    hg ignore file

app_settings
    global settings for the application

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
    server program for fastcgi

files.rst
    this file

htmlfrommd.py
    script to show markdown source in an html window

htmlfrommd.py
    script to show rest source in an html window

readme.rst
    information and usage notes

rst2html.conf
    cherrypy configuration used by the startup script

rst2html.html
    the web page (template) in which it all happens

rst2html.py
    the program in which it all happens (presentation layer)

rst2html_functions.py
    functions and stuff to be used by the webapp (application layer)

sample_settings.yml         - to be removed
    configuration example

setup_database.sql
    SQL satatements for building the database tables

stand.html
    template for displaying the site overview

start_rst2html.py
    script to start the application with

wsgi_handler.py
    another script to start the app as a wsgi server


static/
    static files for the app to work with; put codemirror javascript library here

    static/htmleditor.js
    static/pyeditor.js
    static/rsteditor.js
    static/yamleditor.js
        syntaxhighlighters for various content in text area
    static/rst2html.ico
        favicon for webapp
    static/960.css
    static/html4css1.css
    static/html4css_960.css
    static/reset.css
        css files to be copied to root of new site
        contain: reset stylesheet, styles for rest conversion, styles for grid_960
        also an all-in one version previously used for rendering in preview mode

test/
    directory for tests and testscripts

    analyze_testdata.py
        functions that help in comparing database and html output, used by test_scenario_1
    test_dml.py
        testscript for the data manipulation layer
    test_rst2html.py
        testscript for unexposed functions in the presentation layer
    test_rst2html_functions.py
        testscript for the application logic layer
    test_scenario_1.py
        testscript for the web views in the presentation layer
    test_dml_specific.py
        testscript for non-api functions in the data manipulation layer

