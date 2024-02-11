"""unittests for ./tohtml/makehtml.py
"""
import pytest
from mockgui import mockqtwidgets as mockqtw
from tohtml import makehtml as testee

def test_zetom_rest(monkeypatch, capsys):
    """unittest for makehtml.zetom_rest
    """
    def mock_publish(**kwargs):
        print('called publish_string with args', kwargs)
        return b'converted to HTML'
    monkeypatch.setattr(testee, 'publish_string', mock_publish)
    assert testee.zetom_rest('restructured text') == "converted to HTML"
    assert capsys.readouterr().out == (
            "called publish_string with args {'source': 'restructured text',"
            " 'destination_path': '/tmp/omgezet.html', 'writer_name': 'html5',"
            " 'settings_overrides': {'embed_stylesheet': True, 'report_level': 3}}\n")


def test_zetom_markdown(monkeypatch, capsys):
    """unittest for makehtml.zetom_markdown
    """
    def mock_markdown(*args, **kwargs):
        print('called markdown.markdown with args', args, kwargs)
        return 'converted to HTML'
    monkeypatch.setattr(testee.markdown, 'markdown', mock_markdown)
    assert testee.zetom_markdown('markdown text') == "converted to HTML"
    assert capsys.readouterr().out == (
            "called markdown.markdown with args ('markdown text',) {'extensions': ['codehilite']}\n")


class TestMainFrame:
    """unittest for makehtml.MainFrame
    """
    def setup_testobj(self, monkeypatch, capsys):
        """stub for makehtml.MainFrame object

        create the object skipping the normal initialization
        intercept messages during creation
        return the object so that other methods can be monkeypatched in the caller
        """
        def mock_init(self, *args):
            """stub
            """
            print('called MainFrame.__init__ with args', args)
        monkeypatch.setattr(testee.MainFrame, '__init__', mock_init)
        testobj = testee.MainFrame()
        assert capsys.readouterr().out == 'called MainFrame.__init__ with args ()\n'
        return testobj

    def test_init(self, monkeypatch, capsys):
        """unittest for MainFrame.__init__
        """
        def mock_display(self):
            print('called MainFrame.refresh_display')
        def mock_display_failed(self):
            print('called MainFrame.refresh_display')
            return True
        def mock_setup(self):
            print('called MainFrame.setup_actions')
        monkeypatch.setattr(testee.qtw.QApplication, 'exec', mockqtw.MockApplication.exec)
        monkeypatch.setattr(testee.qtw.QMainWindow, '__init__', mockqtw.MockMainWindow.__init__)
        monkeypatch.setattr(testee.qtw.QMainWindow, 'resize', mockqtw.MockMainWindow.resize)
        monkeypatch.setattr(testee.qtw.QMainWindow, 'setCentralWidget',
                            mockqtw.MockMainWindow.setCentralWidget)
        monkeypatch.setattr(testee.qtw.QMainWindow, 'setWindowTitle',
                            mockqtw.MockMainWindow.setWindowTitle)
        monkeypatch.setattr(testee.qtw.QMainWindow, 'show', mockqtw.MockMainWindow.show)
        monkeypatch.setattr(testee.webeng.QWebEngineView, '__init__',
                            mockqtw.MockWebEngineView.__init__)
        monkeypatch.setattr(testee.MainFrame, 'refresh_display', mock_display)
        monkeypatch.setattr(testee.MainFrame, 'setup_actions', mock_setup)
        with pytest.raises(ValueError) as exc:
            testobj = testee.MainFrame('parent', 'input', 'mode')
        assert str(exc.value) == 'Unknown mode'
        monkeypatch.setattr(testee, 'zetom', {'mode': 'any'})
        with pytest.raises(SystemExit):
            testobj = testee.MainFrame('parent', 'input', 'mode')
            assert isinstance(testobj.app, testee.qtw.QApplication)
            assert testobj.parent == 'parent'
            assert testobj.input == 'input'
            assert testobj.mode == 'mode'
            assert isinstance(testobj.html, testee.qtw.QWebEngineView)
        assert capsys.readouterr().out == (
                "called MainWindow.__init__\n"
                "called Application.__init__\n"
                "called MainWindow.resize with args (1000, 600)\n"
                "called WebEngineView.__init__()\n"
                "called MainWidget.setCentralWindow with arg of type"
                " `<class 'PyQt6.QtWebEngineWidgets.QWebEngineView'>`\n"
                "called MainWindow.setWindowTitle to `input via htmlfrommode.py`\n"
                "called MainFrame.refresh_display\n"
                "called MainFrame.setup_actions\n"
                "called MainWindow.show\n"
                "called Application.exec\n")
        monkeypatch.setattr(testee.MainFrame, 'refresh_display', mock_display_failed)
        with pytest.raises(SystemExit):
            testobj = testee.MainFrame('parent', 'input', 'mode')
        assert capsys.readouterr().out == (
                "called MainWindow.__init__\n"
                "called Application.__init__\n"
                "called MainWindow.resize with args (1000, 600)\n"
                "called WebEngineView.__init__()\n"
                "called MainWidget.setCentralWindow with arg of type"
                " `<class 'PyQt6.QtWebEngineWidgets.QWebEngineView'>`\n"
                "called MainWindow.setWindowTitle to `input via htmlfrommode.py`\n"
                "called MainFrame.refresh_display\n")

    def test_setup_actions(self, monkeypatch, capsys):
        """unittest for MainFrame.setup_actions
        """
        def mock_add(arg):
            print(f'called MainFrame.addaction')
        monkeypatch.setattr(testee.gui, 'QAction', mockqtw.MockAction)
        testobj = self.setup_testobj(monkeypatch, capsys)
        testobj.addAction = mock_add
        testobj.setup_actions()
        assert capsys.readouterr().out == (
                f"called Action.__init__ with args ('Quit', {testobj})\n"
                "called Action.setShortcuts with arg `['Ctrl+Q', 'Escape']`\n"
                f"called Signal.connect with args ({testobj.close},)\n"
                "called MainFrame.addaction\n"
                f"called Action.__init__ with args ('Refresh', {testobj})\n"
                "called Action.setShortcut with arg `F5`\n"
                f"called Signal.connect with args ({testobj.refresh_display},)\n"
                "called MainFrame.addaction\n")

    def test_refresh_display(self, monkeypatch, capsys, tmp_path):
        """unittest for MainFrame.refresh_display
        """
        # def mock_setcursor(self, arg):
        #     print(f'called Application.setOverrideCursor with arg of type {type(arg)}')
        # def mock_restorecursor(self):
        #     print('called Application.restoreOverrideCursor')
        def mock_zetom(arg):
            print(f'called zetom_function with arg {arg}')
            return 'omgezet'
        inputpath = tmp_path / 'makehtml' / 'filename'
        monkeypatch.setattr(testee, 'zetom', {'mode': mock_zetom})
        monkeypatch.setattr(testee.qtw, 'QMessageBox', mockqtw.MockMessageBox)
        testobj = self.setup_testobj(monkeypatch, capsys)
        testobj.input = str(inputpath)
        testobj.mode = 'mode'
        testobj.app = mockqtw.MockApplication()
        testobj.html = mockqtw.MockWebEngineView()
        assert capsys.readouterr().out == ("called Application.__init__\n"
                                           "called WebEngineView.__init__()\n")
        monkeypatch.setattr(testee.gui, 'QCursor', mockqtw.MockCursor)
        # # testobj.app.setOverrideCursor = mockqtw.MockApplication.setOverrideCursor
        # testobj.app.setOverrideCursor = mock_setcursor
        # # testobj.app.restoreOverrideCursor = mockqtw.MockApplication.restoreOverrideCursor
        # testobj.app.restoreOverrideCursor = mock_restorecursor
        failed = testobj.refresh_display()
        assert failed
        assert capsys.readouterr().out == (f"called MessageBox.critical with args `{testobj}`"
                                           f" `modeview` `File {inputpath} does not exist`\n")
        inputpath.parent.mkdir()
        inputpath.write_text('something')
        failed = testobj.refresh_display()
        assert not failed
        assert capsys.readouterr().out == (
                "called Cursor with arg CursorShape.WaitCursor\n"
                "called Application.setOverrideCursor with arg of type"
                " <class 'mockgui.mockqtwidgets.MockCursor'>\n"
                "called zetom_function with arg something\n"
                "called WebEngineView.setHtml() with args ('omgezet',)\n"
                "called Application.restoreOverrideCursor\n")
