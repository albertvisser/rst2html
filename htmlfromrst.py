"""
appje om teksten in ReST formaat om te zetten naar HTML documenten
"""
import os
import sys
from docutils.core import publish_string
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWebKitWidgets as webkit
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

class MainFrame(qtw.QMainWindow):
    "Main GUI"

    def __init__(self, parent, input):
        self.parent = parent
        self.input = input
        super().__init__() #, parent, _id,
        self.resize(1000,600)
        self.html = webkit.QWebView(self) # , -1,
        self.setCentralWidget(self.html)
        self.setWindowTitle('{} via htmlfromrst.py'.format(input if input else
            "unnamed file"))
        self.refresh_display()

    def refresh_display(self):
        self.html.setHtml(str(zetom(self.input), encoding='utf-8'))

    def keyPressEvent(self, e):
        if e.key() == core.Qt.Key_Escape:
            self.close()
        elif e.key() == core.Qt.Key_F5:
            self.refresh_display()
        super().keyPressEvent(e)

def main(input):
    app = qtw.QApplication(sys.argv)
    if not input:
        print(usage)
        return
    app.setOverrideCursor(gui.QCursor(core.Qt.WaitCursor))
    frm = MainFrame(None, input)
    frm.show()
    app.restoreOverrideCursor()
    sys.exit(app.exec_())

