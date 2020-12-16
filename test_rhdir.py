import pytest
import rst2html_directives as rhdir


def mock_init(*args):
    pass


def test_refkey(monkeypatch):
    monkeypatch.setattr(rhdir.RefKey, '__init__', mock_init)
    testsubj = rhdir.RefKey()
    testsubj.arguments= ['hallo']
    testsubj.options = {}
    testsubj.content = []
    assert testsubj.run() == []


def test_myinclude(monkeypatch):
    monkeypatch.setattr(rhdir.MyInclude, '__init__', mock_init)
    testsubj = rhdir.MyInclude()
    testsubj.arguments = ['hallo']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == 'hallo'


def test_transcript(monkeypatch, capsys):
    start = (" <script type='text/javascript'>\n   function toggle_expander(id) {\n"
             "     var e = document.getElementById(id);\n"
             "     if (e.style.visibility == 'hidden') {\n"
             "       e.style.height = 'auto';\n       e.style.visibility = 'visible'; }\n"
             "     else {\n       e.style.height = '1px';\n       e.style.visibility = 'hidden'; }"
             '\n   }</script>\n<div class="transcript-border" style="border: solid"> '
             '<div id="transcript">'
             '<a href="javascript:toggle_expander(' "'transcript-content'" ');" '
             'class="transcript-title">&darr; Transcript</a><div id="transcript-content">'
             '<div class="transcript">')
    end = ("</div></div> </div> </div> <script type='text/javascript'>"
           "document.getElementById('transcript-content').style.visibility = 'hidden';"
           "document.getElementById('transcript-content').style.height = '1px';</script>")
    monkeypatch.setattr(rhdir.Transcript, '__init__', mock_init)
    testsubj = rhdir.Transcript()
    # testsubj.arguments
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == start + end

    testsubj = rhdir.Transcript()
    # testsubj.options = {'title': 'o'}
    testsubj.content = [':title: o', 'x', 'y::z', '::', 'a::b', '::c', 'd', '::e']
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == ''.join((start, '<p><em>o</em><br>', 'x<br>', '<em>y: </em>z</p>',
                                 '<p><em>a: </em>b<br>', '<em>a: </em>c<br>',
                                 'd<br>', '<em>a: </em>e</p>', end))
