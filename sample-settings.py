# rename this file to settings.py to make it work
import os

"""settings for rst2html.py

defines the following items:

HERE     - location of this file
TEMPLATE - full path to the html interface for this app
root     - location of html pages
source   - location of .rst sources
css      - location of css (needs to be in one file, apparently)
mirror   - location of (mirror) site on local machine
all_css  - all css in separate files (relative links)
wid, hig - width and height of text area in rst2html.html

"""

HERE = os.path.dirname(__file__)
TEMPLATE = os.path.join(HERE, "rst2html.html")
root = os.path.join(HERE, "target")
source = os.path.join(root, "../source")
css = os.path.join(root, "style/html4css1_960.css")
mirror = os.path.dirname(root) # os.path.join(root, "../")
all_css = """\
<link rel="stylesheet" type="text/css" media="all" href="css/reset.css" />
<link rel="stylesheet" type="text/css" media="all" href="css/960.css" />
<link rel="stylesheet" href="css/html4css1.css" type="text/css" />
"""
wid = 100 # desktop: 72
hig = 32 # desktop: 40
