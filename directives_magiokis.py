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


# dit kan met een standaard rest directive, enige probleem is dat een absolute filenaam nodig is
# die directive heet header en als argument kun je blijkbaar een include directive opgeven
class HeaderText(Directive):
    """genereert een verwijzing naar de pagina die de tekst voor de heading bevat
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'href': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '<p></p><header id="header">include {}</header>'.format(
                              self.arguments[0]), format='html')
        return [text_node]


class ByLine(Directive):
    """genereert een byline
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'date': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        name = self.arguments[0]
        try:
            date = self.options['date']
        except KeyError:
            text = ''
        else:
            text = " on <time>{}</time>".format(date)
        text_node = nodes.raw('', '<p></p><header><p><span>Submitted by </span><span>{}</span>{}'
                              '</p></header>'.format(name, text), format='html')
        return [text_node]


class Audio(Directive):
    """genereert een audio element
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    # option_spec = {'date': directives.unchanged}
    has_content = True

    def run(self):
        "genereer de html"
        source = self.arguments[0]
        content = '<br>\n'.join(self.content)
        text_node = nodes.raw('', '<audio controls src="{}"></audio><p>{}</p>'.format(source,
                              content), format='html')
        return [text_node]


class MenuText(Directive):
    """genereert een menu met links
    """

    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'title': directives.unchanged}
    has_content = True

    def run(self):
        "genereer de html"
        try:
            title = '<p></p><h2>{}</h2>'.format(self.arguments[0])
        except IndexError:
            title = ''
        text = [title + '<ul>']
        for line in self.content:
            line = line.strip()
            if line.startswith('`') and ' <' in line and line.endswith(">`_"):
                line = line[1:-3]
                linktext, link = line.split(' <', 1)
                line = '<a class="reference external" href="{}">{}</a>'.format(link, linktext)
            else:
                line = line
            text.append('<li class="menu">{}</li>'.format(line))
        text.append('</ul>')
        text_node = nodes.raw('', ''.join(text), format='html')
        return [text_node]


# dit kan met een standaard rest directive, alleen genereert die niet zo'n aside tag
# die directive heet ook sidebar en als argument kun je blijkbaar een include directive opgeven
class MySidebar(Directive):
    """genereert een verwijzing naar de pagina die de tekst voor een sidebar bevat
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'href': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '<p></p><aside><section>include {}</section></aside>'.format(
                              self.arguments[0]), format='html')
        return [text_node]


# dit kan met een standaard rest directive, enige probleem is dat een absolute filenaam nodig is
# die directive heet footer en als argument kun je blijkbaar een include directive opgeven
class FooterText(Directive):
    """genereert een verwijzing naar de pagina die de tekst voor de footer bevat
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'href': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '<p></p><div id="footer">include {}</div>'.format(self.arguments[0]),
                              format='html')
        return [text_node]
