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


def zetom_rest(data):
    """rst naar html omzetten en resultaat teruggeven"""
    overrides = {
        "embed_stylesheet": True,
        "stylesheet_path": '/usr/share/docutils/writers/html4css1/html4css1.css',
        "report_level": 3}
    return str(publish_string(source=data,
                              destination_path="/tmp/omgezet.html",
                              writer_name='html',
                              settings_overrides=overrides), encoding='utf-8')


def zetom_markdown(data):
    """md naar html omzetten en resultaat teruggeven"""
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
        failed = self.refresh_display(input, mode)
        if failed:
            sys.exit()
        self.show()
        sys.exit(self.app.exec_())

    def refresh_display(self, input, mode):
        """(re)show the converted input"""
        failed = False
        self.app.setOverrideCursor(gui.QCursor(core.Qt.WaitCursor))
        try:
            f_in = open(input)
        except FileNotFoundError:
            failed = True
            self.app.restoreOverrideCursor()
            qtw.QMessageBox.critical(self, '{}view'.format(mode),
                                     'File {} does not exist'.format(input))
            return failed
        except UnicodeDecodingError:
            f_in = open(input, encoding='latin-1')
        with f_in:
            data = ''.join([x for x in f_in])
        self.html.setHtml(zetom[self.mode](data))
        self.app.restoreOverrideCursor()
        return failed

    def keyPressEvent(self, event):
        """reimplementation of event handler"""
        if event.key() == core.Qt.Key_Escape:
            self.close()
        elif event.key() == core.Qt.Key_F5:
            self.refresh_display()
        super().keyPressEvent(event)
