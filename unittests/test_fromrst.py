"""unittests for ./tohtml/fromrst.py
"""
from tohtml import fromrst as testee


def test_main(monkeypatch, capsys):
    """unittest for fromrst.main
    """
    def mock_mainframe(*args):
        print('called MainFrame with args', args)
    monkeypatch.setattr(testee, 'MainFrame', mock_mainframe)
    testee.main('')
    assert capsys.readouterr().out ==("usage: python(3) htmlfromrst.py <filename>\n")
    testee.main('filename')
    assert capsys.readouterr().out ==("called MainFrame with args (None, 'filename', 'rst')\n")
