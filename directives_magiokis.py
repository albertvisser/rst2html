# -*- coding: utf-8 -*-
"""Directives for Magiokis site
"""
import pathlib
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive


def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))


def build_menu(lines, title=''):
    """create menu list from text lines
    """
    if title:
        title = '<p></p><h2>{}</h2>'.format(title)
    text = [title + '<ul class="menu">']
    for line in lines:
        line = line.strip()
        if line.startswith('`') and ' <' in line and line.endswith(">`_"):
            line = line[1:-3]
            linktext, link = line.split(' <', 1)
            line = '<a class="reference external" href="{}">{}</a>'.format(link, linktext)
        else:
            line = line
        text.append('<li>{}</li>'.format(line))
    text.append('</ul>')
    return text


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
            rest = '' if nxt == 'None' else ''.join(('<a class="reference external" ',
                                                     'href="{0}">{1}</a>')).format(nxt, ltext)
            start = ''.join((start, '<div style="text-align: center">', about, rest))
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
        text = '<p></p><header id="header">include {}</header>'.format(self.arguments[0])
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class MyHeader(Directive):
    """genereert een header die met de css om kan gaan (of andersom)
    """

    required_arguments = 0
    optional_arguments = 5
    final_argument_whitespace = True
    option_spec = {'title': directives.unchanged,
                   'href': directives.unchanged,
                   'image': directives.unchanged,
                   'text': directives.unchanged,
                   'menu': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        lines = ['<header id="header" role="banner">']
        href = self.options['href'] if 'href' in self.options else '/'
        lines.append('<a href="{}" id="logo" rel="home" title="Home">'.format(href))
        src = self.options['image'] if 'image' in self.options else '/zing.gif'  # '/favicon.ico'
        lines.extend(['<img alt="Home" src="{}"/>'.format(src), '</a>'])
        text = 'Magiokis Productions Proudly Presents!'
        text = self.options['text'] if 'text' in self.options else text
        lines.extend(['<div id="name-and-slogan">', '<div id="site-slogan">', text, '</div>',
                      '</div>', '</header>', '<div id="main">', '<div id="navigation">'])
        if 'menu' in self.options:
            menufile = pathlib.Path(self.options['menu'])
        else:
            menufile = pathlib.Path.home() / 'www' / 'magiokis' / 'source' / 'hoofdmenu.rst'
        if menufile.exists():
            text = [x[2:] for x in menufile.read_text().split('\n') if x.startswith('- ')]
            lines.extend(build_menu(text))
        lines.extend(['</div>', '</div>', '<div id="content" class="column">'])
        lines.append('<h1 class="page-title">{}</h1>'.format(self.options['title']))
        text_node = nodes.raw('', ''.join(lines), format='html')
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
        text = '<audio controls src="{}"></audio><p>{}</p>'.format(self.arguments[0],
                                                                   '<br>\n'.join(self.content))
        text_node = nodes.raw('', text, format='html')
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
            text = build_menu(self.content, title=self.arguments[0])
        except IndexError:
            text = build_menu(self.content)
        text_node = nodes.raw('', ''.join(text), format='html')
        return [text_node]


class Transcript(Directive):
    """genereert een transcriptie
    """
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'title': directives.unchanged}
    has_content = True

    def run(self):
        "genereer de html"
        title = self.options['title'] if self.options else ''
        first_line = '<div class="transcript">'
        if title:
            first_line += '<div>{}</div>'.format(title)
        lines = []
        last_line = ''
        for line in self.content:
            try:
                name, text = line.split('::')
            except ValueError:
                if lines:
                    last_line += '<br>'
                name, text = '', line
                if self.content == [line]:
                    name, text = text, name
            else:
                if lines:
                    last_line += '</div><div style="clear: left"></div>'
            lines.append(last_line)
            if name:
                delim = ':' if text else ''
                last_line = ''.join(('<div style="float: left"><em>{}</em>{}&nbsp;</div>',
                                     '<div style="float: left">{}')).format(name, delim, text)
            else:
                last_line = '{}'.format(text)
        last_line += '</div><div style="clear: left"></div>'
        lines.append(last_line)
        lines.insert(0, first_line)
        lines.append('<br></div>')
        text_node = nodes.raw('', ''.join(lines), format='html')
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
        text = '<p></p><aside><section>include {}</section></aside>'.format(self.arguments[0])
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class StrofenTekst(Directive):
    "genereert een gedicht of songtekst "

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'titel': directives.unchanged,
                   'tekst': directives.unchanged}
    has_content = True

    def run(self):
        "genereer de html"
        try:
            lines = ['<div class="{}">'.format(self.soortnaam)]
        except AttributeError:
            lines = ['<div class="unnamed-container">']
        for item in self.option_spec:
            if item in self.options:
                lines.append('<div class="{}">{}</div>'.format(item, self.options[item]))
        lines.append('<div class="couplet">')
        end_couplet = in_refrein = False
        for line in self.content:
            if line == '--':
                if end_couplet:
                    strofe = 'refrein' if in_refrein else 'couplet'
                    lines.append('<div class="{}">'.format(strofe))
                lines.append('</div>')
                end_couplet = True
                continue
            in_refrein = line.startswith(' ')
            if end_couplet:
                strofe = 'refrein' if in_refrein else 'couplet'
                lines.append('<div class="{}">'.format(strofe))
                end_couplet = False
            lines.append('<div class="regel">{}</div>'.format(line))
        lines.append('</div></div>')
        text_node = nodes.raw('', '\n' + '\n'.join(lines), format='html')
        return [text_node]


class RoleSpec(Directive):
    "genereert rolverdeling"
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'titel': directives.unchanged,
                   'tekst': directives.unchanged}
    has_content = True

    def run(self):
        "genereer de html"
        lines = ['<div class="rollen">']
        for item in self.option_spec:
            if item in self.options:
                lines.append('<div class="{}">{}</div>'.format(item, self.options[item]))
        for line in self.content:
            lines.append('<div class="rol">{}</div>'.format(line))
        lines.append('</div>')
        text_node = nodes.raw('', '\n' + '\n'.join(lines), format='html')
        return [text_node]


class Scene(Directive):
    "genereert scene tekst"
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = True

    def run(self):
        "genereer de html"
        lines = ['<div class="scene">']
        open_claus = open_spraak = found_who = False
        for line in self.content:
            try:
                who, what = line.split('::', 1)
                found_who = True
            except ValueError:
                if found_who:
                    lines.append('<div class="regel">{}</div>'.format(line))
                else:
                    lines.append('<div class="actie">{}</div>'.format(line))
                continue
            if open_claus:
                if open_spraak:
                    lines.append('</div>')
                    open_spraak = False
                lines.append('</div>')
                open_claus = False
            if who:
                lines.append('<div class="claus">')
                lines.append('<div class="spreker">{}</div>'.format(who))
                lines.append('<div class="spraak">')
                lines.append('<div class="regel">{}</div>'.format(what))
                open_claus = open_spraak = True
            else:
                if open_spraak:
                    lines.append('</div>')
                    open_spraak = False
                lines.append('<div class="actie">{}</div>'.format(what))
        if open_claus:
            if open_spraak:
                lines.append('</div>')
                open_spraak = False
            lines.append('</div>')
            open_claus = False
        lines.append('</div>')
        text_node = nodes.raw('', '\n' + '\n'.join(lines), format='html')
        return [text_node]


class Anno(Directive):
    "genereert annotatietekst"
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = True

    def run(self):
        "genereer de html"
        lines = ['<div class="anno">']
        for line in self.content:
            lines.append('<p>{}</p>'.format(line))
        lines.append('</div>')
        text_node = nodes.raw('', '\n' + '\n'.join(lines), format='html')
        return [text_node]


class Gedicht(StrofenTekst):
    "specifieke subclass"
    def __init__(self, *args, **kwargs):
        self.soortnaam = 'gedicht'
        super().__init__(*args, **kwargs)


class SongTekst(StrofenTekst):
    "specifieke subclass"
    def __init__(self, *args, **kwargs):
        self.soortnaam = 'songtekst'
        super().__init__(*args, **kwargs)


class StartBlock(Directive):
    "genereert divstart met class "

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'text': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        lines = ['<div class="{}">'.format(self.arguments[0])]
        if 'text' in self.options:
            divclass = 'title'
            lines.append('<div class="{}">{}</div>'.format(divclass, self.options['text']))
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]


class EndBlock(Directive):
    """genereert divend corresponderend met StartBlock

    het argument wordt vooralsnog niet gebruikt maar is alleen ter verduidelijking
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div> <!-- end {} -->\n'.format(self.arguments[0]), format='html')
        return [text_node]


class StartSideBar(Directive):
    "genereert tagstarts zodat een sidebar met een include directive kan worden opgenomen"

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div><aside><section class="region-sidebar-first column">'
                              '<div id="block">', format='html')
        return [text_node]


class EndSideBar(Directive):
    "genereert tageindes zodat een sidebar met een include directive kan worden opgenomen"

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div></section></aside>', format='html')
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


class MyFooter(Directive):
    """genereert een header die met de css om kan gaan (of andersom)
    """

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        # helaas, letterlijk overnemen van de footer code helpt ook niet om dit onderaan
        # te krijgen
        lines = ('</div></div>',
                 '<div id="footer" class="region region-bottom">',
                 '<div id="block-block-1" class="block block-block first last odd">',
                 '<footer>',
                 "<p>Please don't copy without source attribution. contact me: "
                 '<a href="mailto:info@magiokis.nl">info@magiokis.nl</a></p></footer>')
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]
        # lines = ['<p></p><div id="footer">']
        lines = ['</div></div><div class="region-bottom"><div class="block">']
        # lines.extend(self.content)
        for line in self.content:
            try:
                first, last = line.split('mailto:', 1)
            except ValueError:
                pass
            else:
                # first = linie[0]
                last = last.split(None, 1)
                mailto = last[0]
                last = last[1] if len(last) > 1 else ''
                line = ''.join((first, 'mailto', mailto, last))
            lines.append('<p>{}</p>'.format(line))
        # lines.append('</div>')
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]
