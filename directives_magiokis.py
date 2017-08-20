# -*- coding: utf-8 -*-
"""Directives for Magiokis site
"""
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive


def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))


class Bottom(Directive):
    """genereert de page footer eventueel inclusief gridlayout

    optioneel: aantal eenheden (gridlayout) of -1 (geen gridlayout, wel volgende argumenten)
               target voor lnk naar volgende document of None om ...
               tekst voor link naar volgende document"""

    required_arguments = 0
    optional_arguments = 3
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   'next': directives.unchanged,
                   'ltext': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        try:
            wid = self.arguments[0]
        except IndexError:
            start = end = wid = ''
        try:
            nxt = self.arguments[1]
        except IndexError:
            nxt = ''
        try:
            ltext = self.arguments[2]
        except IndexError:
            ltext = 'volgende episode'
        if nxt.startswith("../"):
            about = ""
        else:
            about = ''.join(('<a class="reference external" href="about.html">',
                             'terug naar de indexpagina</a> '))
        if wid:
            start = '' if wid == '-1' else '<div class="grid_{}">'.format(wid)
            next = '' if nxt == 'None' else ''.join(
                '<a class="reference external" ',
                'href="{0}">{1}</a>').format(nxt, ltext)
            start = ''.join((start, '<div style="text-align: center">', about, next))
            end = '' if wid == '-1' else ''.join(
                '</div><div class="clear">&nbsp;</div><div class="grid_{} spacer">'
                '&nbsp;</div><div class="clear">&nbsp;</div>').format(wid)
            end = '</div>' + end
        text_node = nodes.raw('', '<div class="madeby">content and layout created 2010 '
                              'by Albert Visser <a href="mailto:info@magiokis.nl">'
                              'contact me</a></div>'.join((start, end)), format='html')
        return [text_node]


class RefKey(Directive):
    """Trefwoorden voor document met verwijzingen"""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'trefwoord(en)': directives.unchanged}
    has_content = False

    def run(self):
        """dit directive is bedoeld om door een apart proces gebruikt te worden
        en doet daarom niets"""
        return []
