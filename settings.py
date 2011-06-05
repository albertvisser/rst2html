import os

"""settings for rst2html.py

defines the following items:

HERE     - location of this file
TEMPLATE - full path to the html interface for this app
root     - location of html pages
source   - location of .rst sources
css      - location of css
mirror   - location of (mirror) site on local machine
all_css  - all css in separate files (relative links)
wid, hig - width and height of text area in rst2html.html

"""

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "rst2html.html")
root = "/home/albert/www/magiokis_vv/target"
source = os.path.join(root, "../sources")
css = os.path.join(root, "css/html4css_magiokis_960.css")
mirror = "/home/albert/www/magiokis_vv/"
all_css = """\
<link rel="stylesheet" type="text/css" media="all" href="css/reset.css" />
<link rel="stylesheet" type="text/css" media="all" href="css/960.css" />
<link rel="stylesheet" href="css/magiokis.css" type="text/css" />
<link rel="stylesheet" href="css/html4css1.css" type="text/css" />
"""
wid = 100 # desktop: 72
hig = 32 # desktop: 40
