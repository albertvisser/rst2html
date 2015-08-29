# -*- coding: utf-8 -*-
"""
appje om teksten in ReST formaat om te zetten naar HTML documenten
"""
import os
import sys
from docutils.core import publish_string
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import PyQt4.QtWebKit as webkit
usage = "usage: python(3) htmlfromrst.py <filename>"

def zetom(input):
    """rst naar html omzetten en resultaat teruggeven"""
    f_in = open(input) if sys.version < '3' else open(input, encoding='utf-8')
    with f_in:
        data = ''.join([x for x in f_in])
    overrides = {
        "embed_stylesheet": True,
        "stylesheet_path": '/usr/share/docutils/writers/html4css1/html4css1.css',
        "report_level": 3,
        }
    return publish_string(source=data,
        destination_path="/tmp/omgezet.html",
        writer_name='html',
        settings_overrides=overrides,
        )

class MainFrame(gui.QMainWindow):
    "Main GUI"

    def __init__(self, parent, input):
        self.parent = parent
        gui.QMainWindow.__init__(self) #, parent, _id,
        self.resize(1000,600)
        self.html = webkit.QWebView(self) # , -1,
        self.setCentralWidget(self.html)
        self.setWindowTitle('{} via htmlfromrst.py'.format(input if input else
            "unnamed file"))
        data = str(zetom(input)) if sys.version < '3' else str(zetom(input),
            encoding='utf-8')
        self.html.setHtml(data)
        ## action = gui.QAction('close', self)
        ## action.setShortcut(core.Qt.Key_Escape)
        ## action.triggered.connect(self.close)

    def keyPressEvent(self, e):
        if e.key() == core.Qt.Key_Escape:
            self.close()
        gui.QMainWindow.keyPressEvent(self, e)

def main(input):
    app = gui.QApplication(sys.argv)
    if not input:
        print(usage)
        return
    app.setOverrideCursor(gui.QCursor(core.Qt.WaitCursor))
    frm = MainFrame(None, input)
    frm.show()
    app.restoreOverrideCursor()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else '')
