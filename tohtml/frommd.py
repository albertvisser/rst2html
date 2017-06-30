"""
appje om teksten in Markdown formaat om te zetten naar HTML documenten
"""
import os
import sys
## from .makehtml import zetom_markdown as zetom
from .makehtml import MainFrame


def main(input):
    if not input:
        print("usage: python3() htmlfrommd.py <filename>")
    else:
        frm = MainFrame(None, input, 'md')

