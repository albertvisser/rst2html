# -*- coding: utf-8 -*-

import datetime
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive
"""
wat moet ik maken
- header (zit mogelijk al in standaard functionaliteit)
- container div
- header div: inhoud = variabele tekstregel
- navigation div: inhoud = vaste serie links
- body div
- body start: div class title met inhoud = variabele tekstregel
-             p class date met inhoud = 'written on ...'
"""
header_text = "" # "Albert Visser's programmer's blog"
navlinks = (('/', "Home"),
            ('/about/', 'About me'),
            ('/site/', 'About this site'),
            ('', 'My projects')
            )
projlinks = (("/actiereg/", 'ActieReg'),
            ("/albums/", 'Albums'),
            ("/apropos/", 'A Propos'),
            ("/htmledit/", 'HTML Editor'),
            ("/cssedit/", 'CSS Editor'),
            ("/xmledit/", 'XML Editor'),
            ("/doctree/", 'DocTree'),
            ("/filefindr/", 'FileFindR'),
            ("/hotkeys/", 'Hotkeys'),
            ("/logviewer/", 'LogViewer'),
            ("/myprojects/", 'MyProjects'),
            ("/notetree/", 'NoteTree'),
            ("/probreg/", 'ProbReg'),
            ("/rst2html/", 'Rst2HTML'),
            )

def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))

class StartBody(Directive):
    """genereert de start van de container div en de header div
    """
    required_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text = '<div id="container"> <div id="header">{}</div>'.format(header_text)
        text_node = nodes.raw('', text, format='html')
        return [text_node]

class NavLinks(Directive):
    """Menuutje met links voor navigatie
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text = ['<div id="navigation"><ul>',]
        for link, linktext in navlinks:
            if linktext != 'My projects':
                text.append('<li class="menu"><a href="{}">{}</a></li>'.format(link,
                    linktext))
                continue
            text.append('<li class="menu">{}<ul>'.format(linktext))
            for link, linktext in projlinks:
                text.append('<li><a href="{}">{}</a></li>'.format(link, linktext))
            text.append('</ul></li>')
        text.append('</ul></div>')
        text_node = nodes.raw('', ''.join(text), format='html')
        return [text_node]

class TextHeader(Directive):
    """genereert het begin van de echte tekst
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'text': directives.unchanged,
                   }
    has_content = False

    def run(self):
        "genereer de html"
        text = ['<div id="body">',]
        try:
            title_text =  self.arguments[0]
        except IndexError:
            title_text = "&nbsp;"
        text.append('<h1 class="title">{}</h1>'.format(title_text))
        datum = datetime.datetime.today().strftime('%A, %B %d, %Y')
        text.append('<p class="date">last modified on {}</p>'.format(datum))
        text_node = nodes.raw('', ''.join(text), format='html')
        return [text_node]

class StartMarginless(Directive):
    """opschorten van de marges voor bv. een paginabreed plaatje
    """
    required_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text = '</div></div><div style="margin: auto">'
        text_node = nodes.raw('', text, format='html')
        return [text_node]

class EndMarginless(Directive):
    """marges terugzetten - zou eigenlijk niet moeten werken omdat je een id
    vaker gebruikt
    """
    required_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text = '</div><div id="container"><div id="body">'
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class EndBody(Directive):
    """genereert het eind van de body div en de container div
    """
    required_arguments = 0
    final_argument_whitespace = True
    ## option_spec = {'grid': directives.nonnegative_int,
                   ## 'next': directives.unchanged,
                   ## 'ltext': directives.unchanged,
                   ## }
    has_content = False

    def run(self):
        "genereer de html"
        text = '</div></div>'
        text_node = nodes.raw('', text, format='html')
        return [text_node]
