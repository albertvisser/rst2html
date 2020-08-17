# -*- coding: utf-8 -*-
"""Directives for BitBucket site layout

"""
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive

directive_selectors = {'startbody': (('div', '#container'), ('div', '#header')),
                       'navlinks': (('div', '#navigation'), ('li', '.menu')),
                       'textheader': (('div', '#body'),),  # h1.page-title hoeft niet
                       'endmarginless': (('div', '#container'),),
                       'bottomnav': (('div', '#botnav'), ('li', '.menu'))}


def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))


class StartBody(Directive):
    """genereert de start van de container div en de header div
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'header': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        header_text = self.options.get('header', '')   # "Albert Visser's programmer's blog"
        text = '<div id="container">'
        if header_text:
            text += ' <div id="header">{}</div>'.format(header_text)
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class NavLinks(Directive):
    """Menuutje met links voor navigatie

    Nu op basis van de content, bijvoorbeeld:
    .. navlinks::

       `linktekst <linkadres>`_
       `linktekst <linkadres>`_
       `menutekst`
       . `linktekst <linkadres>`_
       . `linktekst <linkadres>`_
    let op: dit werkt alleen maar in combinatie met de bijbehorende CSS
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):  # nieuwe versie op basis van de directive content
        "genereer de html"
        text = ['<div id="navigation"><ul>']
        in_submenu = False
        for line in self.content:
            if line.startswith('`'):
                if in_submenu:
                    text.append('</ul></li>')
                    in_submenu = False
                line = line.strip()[1:-3]
                if '<' in line:  # menuoptie met tekst en link
                    menu, target = line.split('<')
                    text.append('<li class="menu"><a href="{}">{}</a></li>'.format(target,
                                                                                   menu.strip()))
                else:            # alleen tekst: submenu
                    text.append('<li class="menu">{}<ul>'.format(line))
                    in_submenu = True
            elif line.startswith('. `') and '<' in line:  # submenuoptie met tekst en link
                menu, target = line.strip()[3:-3].split('<')
                text.append('<li><a href="{}">{}</a></li>'.format(target, menu.strip()))
            else:  # error in content
                self.error('Illegal content: {}'.format(line.strip()))
        text.append('</ul></div>')
        text_node = nodes.raw('', ''.join(text), format='html')
        return [text_node]


class TextHeader(Directive):
    """genereert het begin van de echte tekst
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'text': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        text = ['<div id="body">']
        try:
            title_text = self.arguments[0]
        except IndexError:
            title_text = "&nbsp;"
        text.append('<h1 class="page-title">{}</h1>'.format(title_text))
        # datum = datetime.datetime.today().strftime('%A, %B %d, %Y')
        # text.append('<p class="date">last modified on {}</p>'.format(datum))
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


class BottomNav(Directive):
    """Extra menuutje met links voor navigatie onderin
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        "genereer de html"
        text = ['<div><div id="botnav"><ul>']
        for line in self.content:
            line = line.strip()
            if line.startswith('`') and ' <' in line and line.endswith(">`_"):
                line = line[1:-3]
                linktext, link = line.split(' <', 1)
                line = '<a href="{}">{}</a>'.format(link, linktext)
            else:
                line = line
            text.append('<li class="menu">{}</li>'.format(line))
        text.append('</ul></div></div>')
        text_node = nodes.raw('', ''.join(text), format='html')
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
