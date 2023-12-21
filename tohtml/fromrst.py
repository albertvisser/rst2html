"""appje om teksten in ReST formaat om te zetten naar HTML documenten

startup script
"""
## from .makehtml import zetom_rest as zetom
from .makehtml import MainFrame


def main(input):
    """start the GUI for ReST"""
    if not input:
        print("usage: python(3) htmlfromrst.py <filename>")
    else:
        MainFrame(None, input, 'rst')
