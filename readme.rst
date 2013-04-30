Rst2HTML
========

This would probably not qualify as a "mini-CMS". It was meant to edit webpage text in ReStructured Text format and have some built in machinery transform it to HTML, making use of the web browser to both do the editing and preview the result.
The idea also was to be able to concentrate on the contents without being too distracted by the layout.

When I found out how to build *directives* I could also apply some simple layout instructions, such as how to embed the text in a grid-960 format. Since it's not WYSIWIG, it's easier to resist the temptation (for me anyway). That's how I used it for the first version of my personal website.

There's a primitive way built in to work with pages in different directories; instead of loading a page you load a directory and then choose the page to load.

To be able to work on different sites at the same time I built a way to change the configuration from one set of source-target directories to another.

I also separated out the directives modules according to what they are used for.

Requirements
------------

- Python
- Docutils for the restsructured text stuff
- CherryPy
- yaml for the config parsing stuff
