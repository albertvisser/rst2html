import pytest
import directives_magiokis as dirm


def test_transcript(monkeypatch, capsys):
    def mock_init( *args):
        pass
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
    monkeypatch.setattr(dirm.Transcript, '__init__', mock_init)
    testsubj = dirm.Transcript()
    # testsubj.arguments
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == start + end

    testsubj = dirm.Transcript()
    # testsubj.options = {'title': 'o'}
    testsubj.content = [':title: o', 'x', 'y::z', '::', 'a::b', '::c', 'd', '::e']
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == ''.join((start, '<p><em>o</em><br>', 'x<br>', '<em>y: </em>z</p>',
                                 '<p><em>a: </em>b<br>', '<em>a: </em>c<br>',
                                 'd<br>', '<em>a: </em>e</p>', end))
