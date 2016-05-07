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
    dml routines for the file system implementation

docs2mongo.py
    dml routines for the mongodb implementation

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
    functions and stuff to be used bu the webapp (application layer)

sample_settings.yml
    configuration example

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
    directory for tests and testscripts - to be filled with proper testing stuff
    e.g. (these files currently reside in the top level directory)
    analyze_testdata.py
    test_dml.py
    test_rst2html.py
    test_rst2html_functions.py
    test_scenario_1.py
    test_dml_specific.py

