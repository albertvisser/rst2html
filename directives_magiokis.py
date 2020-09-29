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
from app_settings import FS_WEBROOT

directive_selectors = {'bottom': (('div', ".clear"), ('div', "grid_nn"), ('div', "spacer")),
                       'myheader': (('a', "#logo"), ('div', "#name-and-slogan"), ('div',
                                    "#site-slogan"), ('div', "#main"), ('div', "#navigation"),
                                    ('div', "#content"), ('div', ".column"), ),
                       'menutext': (('div', "#navigation"), ),
                       'transcript': (('div', ".transcript"), ),
                       'gedicht': (('div', ".gedicht"), ('div', ".couplet"), ('div', ".refrein"),
                                   ('div', ".regel")),
                       'songtekst': (('div', ".songtekst"), ('div', ".couplet"),
                                     ('div', ".refrein"), ('div', ".regel")),
                       'rolespec': (('div', ".rollen"), ('div', '.titel'), ('div', '.tekst'),
                                    ('div', '.rol')),
                       'scene': (('div', ".scene"), ('div', ".regel"), ('div', ".actie"),
                                 ('div', ".claus"), ('div', ".spreker"), ('div', ".spraak"),
                                 ('div', ".regel")),
                       'anno': (('div', ".anno"), ),
                       'startsidebar': (('section', ".region-sidebar-first"),
                                        ('section', ".column"), ('div', "#block")),
                       'endsidebar': (('section', "region-sidebar-second"), ('section', "column"),
                                      ('section', "sidebar"), ('div', "#block")),
                       'myfooter': (('div', "#footer"), ('div', ".region"),
                                    ('div', ".region-bottom"), ('div', "#block-block-1"),
                                    ('div', ".block"), ('div', ".block-block"), ('div', ".first"),
                                    ('div', ".last"), ('div', ".odd"))}


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
               target voor link naar volgende document of None om ...
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
                   'menu': directives.unchanged,
                   'site': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        lines = ['<header id="header" role="banner">']
        href = self.options.get('href', '/')
        lines.append('<a href="{}" id="logo" rel="home" title="Home">'.format(href))
        src = self.options.get('image', '/zing.gif')  # '/favicon.ico'
        lines.extend(['<img alt="Home" src="{}"/>'.format(src), '</a>'])
        text = self.options.get('text', 'Magiokis Productions Proudly Presents!')
        lines.extend(['<div id="name-and-slogan">', '<div id="site-slogan">', text, '</div>',
                      '</div>', '</header>', '<div id="main">', '<div id="navigation">'])
        menu = self.options.get('menu', '')
        if menu:
            menufile = pathlib.Path(menu)
        else:
            sitename = self.options.get('site', 'magiokis')
            menufile = FS_WEBROOT / sitename / '.source' / 'hoofdmenu.rst'
        if menufile.exists():
            text = [x[2:] for x in menufile.read_text().split('\n') if x.startswith('- ')]
            lines.extend(build_menu(text))
        lines.extend(['</div>', '</div>', '<div id="content" class="column">'])
        lines.append('<h1 class="page-title">{}</h1>'.format(self.options.get('title', '')))
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
        lines = []
        try:
            title = self.arguments[0]
        except IndexError:
            title = ''
        navmenu = title == 'is_navmenu'
        if navmenu:
            lines.append('<div id="navigation">')
            title = '&nbsp;'
        if title:
            text = build_menu(self.content, title=title)
        else:
            text = build_menu(self.content)
        lines.extend(text)
        if navmenu:
            lines.append('</div>')
        text_node = nodes.raw('', ''.join(lines), format='html')
        return [text_node]


class Transcript(Directive):
    "genereert het begin van een blok met transcripts"

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        "genereer de html"
        lines = [" <script type='text/javascript'>\n   function toggle_expander(id) {\n",
                 "     var e = document.getElementById(id);\n",
                 "     if (e.style.visibility == 'hidden') {\n",
                 "       e.style.height = 'auto';\n",
                 "       e.style.visibility = 'visible'; }\n",
                 "     else {\n       e.style.height = '1px';\n"
                 "       e.style.visibility = 'hidden'; }\n   }</script>\n",
                 '<div class="transcript-border" style="border: solid"> <div id="transcript">',
                 '<a href="javascript:toggle_expander(' "'transcript-content'" ');" ',
                 'class="transcript-title">&darr; Transcript</a><div id="transcript-content">',
                 '<div class="transcript">']
        name = old_name = ''
        paragraph_started = False
        for line in self.content:
            line = line.strip()
            if line == '::':
                if paragraph_started:
                    lines.append('</p>')
                    paragraph_started = False
                lines.append('<p>')
                continue
            if '::' not in line:
                if paragraph_started:
                    lines.append('<br>')
                else:
                    lines.append('<p>')
                    paragraph_started = True
                if line.startswith(':title:'):
                    lines.append('<em>{}</em>'.format(line[7:].strip()))
                else:
                    lines.append(line)
                continue
            name, text = line.split('::')
            if not name:
                name = old_name
            else:
                old_name = name
            if paragraph_started:
                lines.append('<br>')
            else:
                paragraph_started = True
            lines.append('<em>{}: </em>{}'.format(name, text))
        if paragraph_started:
            lines.append('</p>')
        lines.append(('</div></div> </div> </div> <script type=' "'text/javascript'" '>'
                      "document.getElementById('transcript-content').style.visibility = 'hidden';"
                      "document.getElementById('transcript-content').style.height = '1px';"
                      '</script>'))
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
        # TODO dit werkt zo niet: je moet de inhoud van het aangegeven file tussenvoegen, niet
        # de verwijzing ernaar
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
        text_node = nodes.raw('', '</div> <!-- end {} -->\n'.format(self.arguments[0]),
                              format='html')
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
    """genereert tag-eindes zodat een sidebar met een include directive kan worden opgenomen

    voegt een dummy sidebar toe bij wijze van rechtermarge
    """
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        text_node = nodes.raw('', '</div></section>'
                              '<section class="region-sidebar-second column sidebar">'
                              '<div id="block"><p>&nbsp;</p></div></section>'
                              '</aside>', format='html')
        return [text_node]


class MyFooter(Directive):
    """genereert een footer die met de css om kan gaan (of andersom)
    """

    required_arguments = 0
    optional_arguments = 0  # was 2 maar dat slaat op het aantal options
    final_argument_whitespace = True
    option_spec = {'text': directives.unchanged,
                   'mailto': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        # helaas, letterlijk overnemen van de footer code helpt ook niet om dit onderaan
        # te krijgen
        text = self.options.get('text', "Please don't copy without source attribution. contact me")
        mailto = self.options.get('mailto', 'info@magiokis.nl')
        lines = ('</div></div>',
                 '<div id="footer" class="region region-bottom">',
                 '<div id="block-block-1" class="block block-block first last odd">',
                 '<footer>',
                 '<p>{0}: <a href="mailto:{1}">{1}</a></p></footer>'.format(text, mailto))
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]
        # lines = ['<p></p><div id="footer">']
        lines = ['</div></div><div class="region-bottom"><div class="block">']
        # lines.append('</div>')
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]
