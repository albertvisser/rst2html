# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive

def align(argument):
    """Conversion function for the "align" option."""
    return directives.choice(argument, ('left', 'center', 'right'))

class StartCols(Directive):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   }
    has_content = False

    def run(self):
        text = '<div class="container_{0}">\n'.format(self.arguments[0])
        text_node = nodes.raw('',text, format='html')
        return [text_node]


class EndCols(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        text_node = nodes.raw('','</div>\n', format='html')
        return [text_node]

class FirstCol(Directive):

    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   }
    has_content = False

    def run(self):
        width = self.arguments[0]
        try:
            classes = self.arguments[1]
        except IndexError:
            classes = ''
        text_node = nodes.raw('',
            '<div class="grid_{0} {1}">\n'.format(width, classes), format='html')
        return [text_node]

class NextCol(Directive):

    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   }
    has_content = False

    def run(self):
        width = self.arguments[0]
        try:
            classes = self.arguments[1]
        except IndexError:
            classes = ''
        text_node = nodes.raw('',
            '</div>\n<div class="grid_{0} {1}">\n'.format(width, classes), format='html')
        return [text_node]

class ClearCol(Directive):

    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        text_node = nodes.raw('',
            '</div>\n<div class="clear">&nbsp;</div>\n', format='html')
        return [text_node]

class Spacer(Directive):

    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   }
    has_content = False

    def run(self):
        try:
            cls = "grid_{0} ".format(self.arguments[0])
            clr = '<div class="clear">&nbsp;</div>\n'
        except IndexError:
            cls = clr = ''
        text_node = nodes.raw('',
            '<div class="{0}spacer">&nbsp;</div>\n{1}'.format(cls,clr), format='html')
        return [text_node]

class Bottom(Directive):

    required_arguments = 0
    optional_arguments = 3
    final_argument_whitespace = True
    option_spec = {'grid': directives.nonnegative_int,
                   'next': directives.unchanged,
                   'ltext': directives.unchanged,
                   }
    has_content = False

    def run(self):
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
            start = '' if wid == '-1' else '<div class="grid_{0}">'.format(wid)
            next = '' if nxt == 'None' else '<a class="reference external" ' \
                'href="{0}">{1}</a>'.format(nxt,ltext)
            start = ''.join((start,
                '<div style="text-align: center">',
                about,
                next,
                ))
            end = '' if wid == '-1' else ''.join(('</div><div class="clear">&nbsp;</div>',
                '<div class="grid_{0} spacer">&nbsp;</div>'.format(wid),
                '<div class="clear">&nbsp;</div>'))
            end = '</div>' + end
        text_node = nodes.raw('',''.join((start,
            '<div class="madeby">content and layout created 2010 by Albert Visser',
            ' <a href="mailto:info@magiokis.nl">contact me</a></div>',
            end)), format='html')
        return [text_node]
