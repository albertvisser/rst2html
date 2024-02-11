Rst2HTML
========

This would probably not qualify as a "mini-CMS". It was meant to edit webpage text in ReStructured Text format and have some built in machinery transform it to HTML, making use of the web browser to both do the editing and preview the result.
The idea also was to be able to concentrate on the contents without being too distracted by the layout.

When I found out how to build *directives* I could also apply some simple layout instructions, such as how to embed the text in a grid-960 format. Since it's not WYSIWIG, it's easier to resist the temptation (for me anyway). That's how I used it for the first version of my personal website.

There's a primitive way built in to work with pages in different directories; instead of loading a page you load a directory and then choose the page to load.

To be able to work on different sites at the same time I built a way to change the configuration from one set of source-target-mirror directories to another.

I also wanted to separate out the directives modules according to what they are used for, and make it possible to dedicate a directives module to the site you're working on via the configuration. When you do that it will be possible to load, edit and save the code for the directives from within this webapp (activating them is not yet supported but coming soon I hope - this is also the reason why most directives are in the general collection despite being project-specific).


As a small bonus for myself I built a simple gui app to show the contents of a .rst file, mainly so I could use this from within SciTE. It's a Python script that takes a filename for its argument.
There's also a version that can handle markdown (.md) files.

As another small bonus to myself, I added a javascript library to provide code highlighting in the text area. I thought of it while building the directives stuff, because it makes it slightly easier to edit the Python code.
It also makes editing the rest sources a bit easier because it highlights directives and shows some styles.

Using codemirror has a few drawbacks though: because the original text field is overlayed with a restyled one, the site settings `width` and `height` cease to work, as does the access key for the text field.

The latest addition is the possibility to easily plug in a different data storage mechanisms. In the process I also redesigned the way site settings are stored. It's currently possible to choose between storage on the file system or in a MongoDB or PostgreSQL database.


How to use
----------

1. *setting up a site on your local webserver*

When starting a new site, begin by choosing what kind of implementation to use. For Mongo or Postgres you may have some preparation to do e.g. setting up a database server. With the right configuration and startup script (see below), start up the application and choose "load settings", then enter a nice name and choose "save settings". This will create a destination site in a standard location as well as define locations for keeping the intermediary results. You can then map the location to a url for your local webserver so that you can view the result in all its glory.

When using an existing site, you can use the existing site configuration and map FS_WEBROOT in `app_settings.py` to the physical directory.
For a file system implementation, create a `settings.yml` file and a `source` and `target` directory tree in it and you're good to go.
A MongoDB implementation has all this stuff stored in a database, for this the pertaining database layer takes care of all the setup details. In the same vein there's the possibility to use a Postgres SQL database.
What backend to use is also defined in `app_settings.py` (the DML variable).

Note that when using CodeMirror for syntax highlighting, the size of the editor window becomes fixed and can only be set from within `static/codemirror/lib/codemirror.js` (as far as I've been able to determine). So controlling it from the site settings becomes impossible.

2. *setting up the application*

Use ``cherryd`` or similar to run ``start_rst2html.py`` with the .conf file in this directory.

In this configuration define the output to go to a specific port on localhost.

Configure your local webserver to pick up the output from the port and assign it to a virtual domain (see the examples included) . Have your hosts file translate the virtual domain to localhost.

Of course you can also pick up the output directly in the web browser by specifying localhost:port.

To make the styling of the converted text work you may also need to change the symlink `static/html4css1.css` because it points to the location where docutils is installed.

3. *setting up codemirror*

The below instruction is for codemirror version 5; I recently noticed that for version 6 it's a little more complicated and I haven't tried it out yet:

Extract codemirror.zip nto the "static" directory - this creates a subdirectory codemirror-<version>. You need to remove the version number to make it work.

The actual highlighting is done by a couple of file named `<mode>editor.js`.

Requirements
------------

- Python(3)
- Docutils for the restructured text stuff
- CherryPy for the web application
- yaml for the config parsing stuff
- CodeMirror(5) for the syntax highlighting (you can do without it I think)
- MongoDB/Pymongo if you choose that backend for your data storage
- PostgreSQL/Psycopg2 if you choose that backend for your data storage
- PyQt(5) for the viewer apps
