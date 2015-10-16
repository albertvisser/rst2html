Rst2HTML
========

This would probably not qualify as a "mini-CMS". It was meant to edit webpage text in ReStructured Text format and have some built in machinery transform it to HTML, making use of the web browser to both do the editing and preview the result.
The idea also was to be able to concentrate on the contents without being too distracted by the layout.

When I found out how to build *directives* I could also apply some simple layout instructions, such as how to embed the text in a grid-960 format. Since it's not WYSIWIG, it's easier to resist the temptation (for me anyway). That's how I used it for the first version of my personal website.

There's a primitive way built in to work with pages in different directories; instead of loading a page you load a directory and then choose the page to load.

To be able to work on different sites at the same time I built a way to change the configuration from one set of source-target directories to another.

I also separated out the directives modules according to what they are used for, and made it possible to dedicate a directives module to the site you're working on via the configuration. When you do that it will be possible to load, edit and save the code for the directives from within this webapp (activating them is not yet supported but coming soon I hope).


As a small bonus for myself I built a simple gui app to show the contents of a .rst file, mainly so I could use this from within SciTE. It's a Python script that takes a filename for its argument.
There's also a version that can handle markdown (.md files).

As another small bonus to myself, I added a javascript library to provide code highlighting in the text area. I thought of it while building the directives stuff, because it makes it slightly easier to edit the Python code.
It also makes editing the rest sources a bit easier because it highlights directives and shows some styles.

How to use
----------

Use ``cherryd`` or similar (these days I use ``gunicorn``) to run ``start_rst2html.py`` with the .conf file in this directory.
In this configuration define the output to go to a specific port on localhost.
Configure your local webserver to pick up the output from the port and assign it to a virtual domain. Have your hosts file translate the virtual domain to localhost.
Of course you can also pick up the output directly in the web browser by specifying localhost:port.


Requirements
------------

- Python
- Docutils for the restsructured text stuff
- CherryPy for the web application
- yaml for the config parsing stuff
- PyQt for the gui version
- CodeMirror for the syntax highlighting (you can do without it I think)
