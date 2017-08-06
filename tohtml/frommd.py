"""appje om teksten in Markdown formaat om te zetten naar HTML documenten

startup script
"""
## from .makehtml import zetom_markdown as zetom
from .makehtml import MainFrame


def main(input):
    """start the GUI for markdown"""
    if not input:
        print("usage: python3() htmlfrommd.py <filename>")
    else:
        frm = MainFrame(None, input, 'md')
