# -*- coding: utf-8 -*-

# Import Docutils document tree nodes module.
from docutils import nodes
# Import ``directives`` module (contains conversion functions).
from docutils.parsers.rst import directives
# Import Directive base class.
from docutils.parsers.rst import Directive

class ExampleDirective(Directive):
    """usage: .. directive_example:: <arguments>
    description: example of how to write/use a directive

    follow the above specs with an explanation of the arguments and whatever else
    you think is necessary
    """

    required_arguments = 1 # enter a number
    optional_arguments = 0 # enter a number
    option_spec = {} # dictionary of argument names mapped to specifications
                     # e.g. `dir.nonnegative_int` to define the type
                     #    or `dir.unchanged` to take the entered text as-is
    final_argument_whitespace = True # can be True or False
    has_content = False              # this one also

    def run(self):
        """body of the directive

        evaluate the arguments with `self.arguments[index]`
        to generate HTML, define a string and turn it into a "text node"
        return this in a list as shown below
        there are other possibilities, this is probably the simplest one
        """
        return [nodes.raw('', 'some_text', format='html')]


