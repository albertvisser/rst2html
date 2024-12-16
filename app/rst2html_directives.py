"""Rst2HTML: Custom directives
"""
# import pathlib
import datetime
# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive
from app_settings import DFLT, WEBROOT
from app.backend import dml

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
                                        ('section', ".column"), ('div', ".block")),
                       'endsidebar': (('section', "region-sidebar-second"), ('section', "column"),
                                      ('section', "sidebar"), ('div', ".block")),
                       'myfooter': (('div', "#footer"), ('div', ".region"),
                                    ('div', ".region-bottom"), ('div', "#block-block-1"),
                                    ('div', ".block"), ('div', ".block-block"), ('div', ".first"),
                                    ('div', ".last"), ('div', ".odd")),
                       'startcols': (('div', '.container_nn'), ),
                       'firstcol': (('div', '.grid_nn'), ),
                       'nextcol': (('div', '.grid_nn'), ),
                       'clearcol': (('div', ".clear"), ),
                       'spacer': (('div', ".clear"), ('div', "grid_nn"), ('div', "spacer")),
                       'startbody': (('div', '#container'), ('div', '#header')),
                       'navlinks': (('div', '#navigation'), ('li', '.menu')),
                       'textheader': (('div', '#body'),),  # h1.page-title hoeft niet
                       'endmarginless': (('div', '#container'),),
                       'bottomnav': (('div', '#botnav'), ('li', '.menu'))}

# blijkbaar gebruik ik dit niet (meer)
# def align(argument):
#     """Conversion function for the "align" option."""
#     return directives.choice(argument, ('left', 'center', 'right'))


def build_menu(lines, title=''):
    """create menu list from text lines
    """
    if title:
        title = f'<p></p><h2>{title}</h2>'
    text = [title + '<ul class="menu">']
    for line in lines:
        line = line.strip()
        if line.startswith('`') and ' <' in line and line.endswith(">`_"):
            line = line[1:-3]
            linktext, link = line.split(' <', 1)
            line = f'<a class="reference external" href="{link}">{linktext}</a>'
        # else:
        #     line = line
        text.append(f'<li>{line}</li>')
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
            about = '<a class="reference external" href="about.html">terug naar de indexpagina</a> '
        if wid:
            start = '' if wid == '-1' else f'<div class="grid_{wid}">'
            rest = '' if nxt == 'None' else f'<a class="reference external" href="{nxt}">{ltext}</a>'
            start += f'<div style="text-align: center">{about}{rest}'
            end = '' if wid == '-1' else ('</div><div class="clear">&nbsp;</div>'
                                          f'<div class="grid_{wid} spacer">&nbsp;</div>'
                                          '<div class="clear">&nbsp;</div>')
            end = '</div>' + end
        year = datetime.date.today().year
        text_node = nodes.raw('', f'{start}<div class="madeby">content and layout created {year}'
                              ' by Albert Visser <a href="mailto:info@magiokis.nl">'
                              f'contact me</a></div>{end}', format='html')
        return [text_node]


class RefKey(Directive):
    """Trefwoorden voor document met verwijzingen"""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'trefwoord(en)': directives.unchanged}
    has_content = False

    def run(self):
        """dit directive is een placeholder t.b.v. het bouwen van een reference document
        en doet daarom niets"""
        return []


class MyInclude(Directive):
    """pseudo-directive om dit ook voor niet-filesystem sites mogelijk te maken"""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
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
        sitename = self.options.get('site', DFLT)
        try:
            site_settings = dml.read_settings(sitename)
        except FileNotFoundError:
            site_settings = {}
        lines = ['<header id="header" role="banner">']
        href = self.options.get('href', '/')
        lines.append(f'<a href="{href}" id="logo" rel="home" title="Home">')

        src = self.options.get('image', site_settings.get('image', ''))
        if src:
            lines.extend([f'<img alt="Home" src="{src}"/>', '</a>'])

        text = self.options.get('text', site_settings.get('blurb', ''))
        if text:
            lines.extend(['<div id="name-and-slogan">', '<div id="site-slogan">', text, '</div>',
                          '</div>'])
        lines.append('</header>')

        menu = self.options.get('menu', site_settings.get('menu', ''))
        if menu:
            menufile = WEBROOT / sitename / '.source' / menu
            if menufile.exists():
                menutext = [x[2:] for x in menufile.read_text().split('\n') if x.startswith('- ')]
                lines.extend(['<div id="main">', '<div id="navigation">'])
                lines.extend(build_menu(menutext))
                lines.extend(['</div>', '</div>'])
        lines.extend(['<div id="content" class="column">'])

        title = self.options.get('title', '')
        if title:
            lines.append(f'<h1 class="page-title">{title}</h1>')
        text_node = nodes.raw('', ''.join(lines), format='html')
        return [text_node]


class ByLine(Directive):
    """genereert een byline
    Als er een argument wordt opgegeven kan dat gebruikt worden als alternatieve tekst
    Optionele argumenten: `author`, `date` en `lang`
    De voorzetsels gebruikt bij auteur en datum zijn standaard in het Engels
    Daarvan kan worden afgeweken door het voor `lang` een taalcode meet te geven
    Momenteel is alleen nl voor Nederlands geïmplementeerd
    """

    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'author': directives.unchanged,
                   'date': directives.unchanged,
                   'lang': directives.unchanged}
    has_content = False

    def run(self):
        "genereer de html"
        text = self.arguments[0] if self.arguments else 'Submitted'
        author = self.options.get('author', '')
        date = self.options.get('date', '')
        lang = self.options.get('lang', 'en')
        if lang == 'nl':
            by, on = 'door', 'op'
        else:   # add additional language variants above this line
            by, on = 'by', 'on'
        authortext = f' {by} <span>{author}</span>' if author else ''
        datetext = f' {on} <time>{date}</time>' if date else ''
        text_node = nodes.raw('', (f'<p></p><header><p><span>{text}</span>{authortext}{datetext}'
                                   '</p></header>'), format='html')
        return [text_node]


class Audio(Directive):
    """genereert een audio element
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        "genereer de html"
        src, content = self.arguments[0], '<br>\n'.join(self.content)
        text = f'<audio controls src="{src}"></audio><p>{content}</p>'

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
        text = build_menu(self.content, title=title) if title else build_menu(self.content)
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
                 "     else {\n       e.style.height = '1px';\n",
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
                    lines.append(f'<em>{line[7:].strip()}</em>')
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
            lines.append(f'<em>{name}: </em>{text}')
        if paragraph_started:
            lines.append('</p>')
        lines.append('</div></div> </div> </div> <script type=' "'text/javascript'" '>'
                     "document.getElementById('transcript-content').style.visibility = 'hidden';"
                     "document.getElementById('transcript-content').style.height = '1px';"
                     '</script>')
        text_node = nodes.raw('', ''.join(lines), format='html')
        return [text_node]


# dit kan met een standaard rest directive, alleen genereert die niet zo'n aside tag
# die directive heet ook sidebar en als argument kun je blijkbaar een include directive opgeven
# echter die include moet in deze eigen implementatie van te voren omgezet zijn want je wilt de
# de inhoud van het aangegeven file tussenvoegen, niet de verwijzing ernaar
# class MySidebar(Directive):
#     """genereert een verwijzing naar de pagina die de tekst voor een sidebar bevat
#     """
#
#     required_arguments = 1
#     optional_arguments = 0
#     final_argument_whitespace = True
#     option_spec = {'href': directives.unchanged}
#     has_content = False
#
#     def run(self):
#         "genereer de html"
#         text = f'<p></p><aside><section>include {self.arguments[0]}</section></aside>'
#         text_node = nodes.raw('', text, format='html')
#         return [text_node]


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
            lines = [f'<div class="{self.soortnaam}">']
        except AttributeError:
            lines = ['<div class="unnamed-container">']
        for item in self.option_spec:
            if item in self.options:
                lines.append(f'<div class="{item}">{self.options[item]}</div>')
        lines.append('<div class="couplet">')
        end_couplet = in_refrein = False
        for line in self.content:
            if line == '--':
                # if end_couplet:
                #     strofe = 'refrein' if in_refrein else 'couplet'
                #     lines.append(f'<div class="{strofe}">')
                lines.append('</div>')
                end_couplet = True
                continue
            in_refrein = line.startswith(' ')
            if end_couplet:
                strofe = 'refrein' if in_refrein else 'couplet'
                lines.append(f'<div class="{strofe}">')
                end_couplet = False
            lines.append(f'<div class="regel">{line}</div>')
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
                lines.append(f'<div class="{item}">{self.options[item]}</div>')
        for line in self.content:
            lines.append(f'<div class="rol">{line}</div>')
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
        open_claus = found_who = False
        for line in self.content:
            try:
                who, what = line.split('::', 1)
                found_who = True
            except ValueError:
                if found_who:
                    lines.append(f'<div class="regel">{line}</div>')
                else:
                    lines.append(f'<div class="actie">{line}</div>')
                continue
            if open_claus:
                lines.append('</div></div>')
                open_claus = False
            if who:
                lines.append('<div class="claus">')
                lines.append(f'<div class="spreker">{who}</div>')
                lines.append('<div class="spraak">')
                lines.append(f'<div class="regel">{what}</div>')
                open_claus = True
            else:
                lines.append(f'<div class="actie">{what}</div>')
        if open_claus:
            lines.append('</div></div>')
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
            lines.append(f'<p>{line}</p>')
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
        lines = [f'<div class="{self.arguments[0]}">']
        if 'text' in self.options:
            divclass = 'title'
            lines.append(f'<div class="{divclass}">{self.options["text"]}</div>')
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
        divname = self.arguments[0]
        text_node = nodes.raw('', f'</div> <!-- end {divname} -->\n', format='html')
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
                              '<div class="block">', format='html')
        return [text_node]


class SideBarKop(Directive):
    """vervanging voor een standaard gestylede titel omdat deze in een sidebar de html verpest

    Er wordt namelijk een div omheen gegenereerd die de erop volgende inhoud ook omvat. De logica
    hiervoor houdt geenrekening met de <aside> waardoor deze er ook in terecht komt
    Ik weet niet of die div interessant is want die is bedoeld als navigatie-target
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        "genereer de html"
        title = self.arguments[0]
        text_node = nodes.raw('', f'<h1>{title}</h1>', format='html')
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
                              '<section class="region-sidebar-second column">'
                              '<div class="block"><p>&nbsp;</p></div></section>'
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
                 f'<p>{text}: <a href="mailto:{mailto}">{mailto}</a></p></footer>')
        text_node = nodes.raw('', '\n'.join(lines), format='html')
        return [text_node]
        # # lines = ['<p></p><div id="footer">']
        # lines = ['</div></div><div class="region-bottom"><div class="block">']
        # # lines.append('</div>')
        # text_node = nodes.raw('', '\n'.join(lines), format='html')
        # return [text_node]


# ---------------- Directives to realize simple grid960 layout ----------------------
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
        colcount = self.arguments[0]
        text = f'<div class="container_{colcount}">\n'
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
        text = f'<div class="grid_{width} {classes}">\n'
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
        text = f'</div>\n<div class="grid_{width} {classes}">\n'
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
            colcount = self.arguments[0]
            cls = f"grid_{colcount} "
            clr = '<div class="clear">&nbsp;</div>\n'
        except IndexError:
            cls = clr = ''
        text = f'<div class="{cls}spacer">&nbsp;</div>\n{clr}'
        text_node = nodes.raw('', text, format='html')
        return [text_node]


# ---------------- Directives for Magiokis-docs site layout ------------------------
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
            text += f' <div id="header">{header_text}</div>'
        text_node = nodes.raw('', text, format='html')
        return [text_node]


class NavLinks(Directive):
    """Menuutje met links voor navigatie

    Op basis van de content, bijvoorbeeld:
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

    def run(self):
        "genereer de html"
        text = ['<div id="navigation"><ul>']
        in_submenu = False
        for line in self.content:
            if line.startswith('`'):
                if in_submenu:
                    text.append('</ul></li>')
                    in_submenu = False
                line = line.strip()[1:-1]
                if '<' in line:  # menuoptie met tekst en link
                    menu, target = line.split('<')
                    text.append(f'<li class="menu"><a href="{target[:-2]}">{menu.strip()}</a></li>')
                else:            # alleen tekst: submenu
                    text.append(f'<li class="menu">{line}<ul>')
                    in_submenu = True
            elif line.startswith('. `') and '<' in line:  # submenuoptie met tekst en link
                if in_submenu:
                    menu, target = line.strip()[3:-3].split('<')
                    text.append(f'<li><a href="{target}">{menu.strip()}</a></li>')
                else:
                    self.error(f'Submenu entry before main menu: `{line.strip()}`')
            else:  # error in content
                self.error(f'Illegal content: `{line.strip()}`')
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
        text.append(f'<h1 class="page-title">{title_text}</h1>')
        # datum = datetime.datetime.today().strftime('%A, %B %d, %Y')
        # text.append(f'<p class="date">last modified on {datum}</p>')
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
                line = f'<a href="{link}">{linktext}</a>'
            # else:
            #     line = line
            text.append(f'<li class="menu">{line}</li>')
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
