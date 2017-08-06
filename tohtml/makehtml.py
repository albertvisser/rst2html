"""appje om teksten in ReST of markdown formaat om te zetten naar HTML documenten

PyQt5 versie
"""
import sys
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as gui
import PyQt5.QtCore as core
import PyQt5.QtWebKitWidgets as webkit
from docutils.core import publish_string
import markdown


def zetom_rest(input):
    """rst naar html omzetten en resultaat teruggeven"""
    f_in = open(input) if sys.version < '3' else open(input, encoding='utf-8')
    with f_in:
        data = ''.join([x for x in f_in])
    overrides = {
        "embed_stylesheet": True,
        "stylesheet_path": '/usr/share/docutils/writers/html4css1/html4css1.css',
        "report_level": 3}
    return str(publish_string(source=data,
                              destination_path="/tmp/omgezet.html",
                              writer_name='html',
                              settings_overrides=overrides), encoding='utf-8')


def zetom_markdown(input):
    """md naar html omzetten en resultaat teruggeven"""
    f_in = open(input) if sys.version < '3' else open(input, encoding='utf-8')
    with f_in:
        data = ''.join([x for x in f_in])
    return markdown.markdown(data, extensions=['codehilite'])


zetom = {'rst': zetom_rest, 'md': zetom_markdown}


class MainFrame(qtw.QMainWindow):
    "Main GUI"
    def __init__(self, parent, input, mode):
        if mode not in zetom:
            raise ValueError('Unknown mode')
        self.app = qtw.QApplication(sys.argv)
        self.parent = parent
        self.input = input
        self.mode = mode
        super().__init__()
        self.resize(1000, 600)
        self.html = webkit.QWebView(self)
        self.setCentralWidget(self.html)
        title = '{} via htmlfrom{}.py'.format(input, mode)
        self.setWindowTitle(title)
        self.refresh_display()
        self.show()
        sys.exit(self.app.exec_())

    def refresh_display(self):
        """(re)show the converted input"""
        self.app.setOverrideCursor(gui.QCursor(core.Qt.WaitCursor))
        self.html.setHtml(zetom[self.mode](self.input))
        self.app.restoreOverrideCursor()

    def keyPressEvent(self, event):
        """reimplementation of event handler"""
        if event.key() == core.Qt.Key_Escape:
            self.close()
        elif event.key() == core.Qt.Key_F5:
            self.refresh_display()
        super().keyPressEvent(event)
