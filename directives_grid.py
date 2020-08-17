# -*- coding: utf-8 -*-
"""Directives to realize simple grid960 layout
"""
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive

directive_selectors = {'startcols': (('div', '.container_nn'), ),
                       'firstcol': (('div', '.grid_nn'), ),
                       'nextcol': (('div', '.grid_nn'), ),
                       'clearcol': (('div', ".clear"), ),
                       'spacer': (('div', ".clear"), ('div', "grid_nn"), ('div', "spacer"))}


def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))


class StartCols(Directive):
    """Initialisatie van het grid

    required: aantal eenheden (12 0f 16)"""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int}
    has_content = False

    def run(self):
        "genereer de html"
        text = '<div class="container_{}">\n'.format(self.arguments[0])
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class EndCols(Directive):
    "afsluiten van het grid"

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div>\n', format='html')
        return [text_node]


class FirstCol(Directive):
    """definieren van de eerste kolom

    required: aantal eenheden
    optional: class"""

    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int}
    has_content = False

    def run(self):
        "genereer de html"
        width = self.arguments[0]
        try:
            classes = self.arguments[1]
        except IndexError:
            classes = ''
        text = '<div class="grid_{} {}">\n'.format(width, classes)
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class NextCol(Directive):
    """definieren van de volgende kolom

    required: aantal eenheden
    optional: class"""

    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int}
    has_content = False

    def run(self):
        "genereer de html"
        width = self.arguments[0]
        try:
            classes = self.arguments[1]
        except IndexError:
            classes = ''
        text = '</div>\n<div class="grid_{} {}">\n'.format(width, classes)
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class ClearCol(Directive):
    """afsluiten van een rij kolommen"""
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div>\n<div class="clear">&nbsp;</div>\n',
                              format='html')
        return [text_node]


class Spacer(Directive):
    """genereert een lege regel of kolom

    optional: aantal kolomeenheden. Bij niet opgeven hiervan wrdt de spacer genereneerd
    binnen de huidige kolom; anders vergelijkbaar met firstcol/nextcol"""

    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int}
    has_content = False

    def run(self):
        "genereer de html"
        try:
            cls = "grid_{} ".format(self.arguments[0])
            clr = '<div class="clear">&nbsp;</div>\n'
        except IndexError:
            cls = clr = ''
        text = '<div class="{}spacer">&nbsp;</div>\n{}'.format(cls, clr)
        text_node = nodes.raw('', text, format='html')
        return [text_node]
