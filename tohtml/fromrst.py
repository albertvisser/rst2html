"""
appje om teksten in ReST formaat om te zetten naar HTML documenten
"""
import os
import sys
## from .makehtml import zetom_rest as zetom
from .makehtml import MainFrame


def main(input):
    if not input:
        print("usage: python(3) htmlfromrst.py <filename>")
    else:
        frm = MainFrame(None, input, 'rst')

