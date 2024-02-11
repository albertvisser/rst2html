"""appje om teksten in ReST of markdown formaat om te zetten naar HTML documenten

PyQt5 versie
"""
import os
import sys
import PyQt6.QtWidgets as qtw
import PyQt6.QtGui as gui
import PyQt6.QtCore as core
import PyQt6.QtWebEngineWidgets as webeng
from docutils.core import publish_string
import markdown
HERE = os.path.dirname(os.path.dirname(__file__))


def zetom_rest(data):
    """rst naar html omzetten en resultaat teruggeven"""
    overrides = {
        "embed_stylesheet": True,
        # "stylesheet_path": '/usr/share/docutils/writers/html4css1/html4css1.css',
        # "stylesheet_path": os.path.join(HERE, 'static', 'html4css1.css'),
        # "stylesheet_path": '',
        # "stylesheet": [os.path.join(HERE, 'static', 'minimal.css'),
        #                os.path.join(HERE, 'static', 'html4css1.css')],
        "report_level": 3}
    return str(publish_string(source=data,
                              destination_path="/tmp/omgezet.html",
                              writer_name='html5',
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
        self.html = webeng.QWebEngineView(self)
        self.setCentralWidget(self.html)
        title = f'{input} via htmlfrom{mode}.py'
        self.setWindowTitle(title)
        failed = self.refresh_display()
        if failed:
            sys.exit()
        self.setup_actions()
        self.show()
        sys.exit(self.app.exec())

    def setup_actions(self):
        """setup action for quitting the app and refreshing the screen"""
        quitaction = gui.QAction('Quit', self)
        quitaction.setShortcuts(['Ctrl+Q', 'Escape'])
        quitaction.triggered.connect(self.close)
        self.addAction(quitaction)
        refresh_action = gui.QAction('Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_display)
        self.addAction(refresh_action)

    def refresh_display(self):
        """(re)show the converted input"""
        failed = False
        if not os.path.exists(self.input):
            failed = True
            qtw.QMessageBox.critical(self, f'{self.mode}view', f'File {self.input} does not exist')
        else:
            self.app.setOverrideCursor(gui.QCursor(core.Qt.CursorShape.WaitCursor))
            try:
                f_in = open(self.input)
            except UnicodeDecodeError:
                f_in = open(self.input, encoding='latin-1')
            with f_in:
                data = ''.join([list(f_in)])
            self.html.setHtml(zetom[self.mode](data))
            self.app.restoreOverrideCursor()
        return failed
