# -*- coding: utf-8 -*-
"""
appje om teksten in Markdown formaat om te zetten naar HTML documenten
"""
import os
import sys
import markdown
import PyQt4.QtGui as gui
import PyQt4.QtCore as core
import PyQt4.QtWebKit as webkit
usage = "usage: python3() htmlfrommd.py <filename>"

def zetom(input):
    """md naar html omzetten en resultaat teruggeven"""
    f_in = open(input) if sys.version < '3' else open(input, encoding='utf-8')
    with f_in:
        data = ''.join([x for x in f_in])
    return markdown.markdown(data, extensions=['codehilite'])


class MainFrame(gui.QMainWindow):
    "Main GUI"

    def __init__(self, parent, input):
        self.parent = parent
        gui.QMainWindow.__init__(self) #, parent, _id,
        self.resize(1000,600)
        self.html = webkit.QWebView(self) # , -1,
        self.setCentralWidget(self.html)
        self.setWindowTitle('{} via htmlfrommd.py'.format(input if input else
            "unnamed file"))
        data = str(zetom(input)) # if sys.version < '3' else str(zetom(input),
            ## encoding='utf-8')
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
    frm = MainFrame(None, input)
    frm.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else '')
