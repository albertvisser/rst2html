import pytest
import app.rst2html_directives as rhdir
# docutils handelt zelf ontbrekende verplichte argumenten af dus hoeven we hier niet te doen
# with pytest.raises(KeyError):
#     testsubj.run()


def mock_init(*args):
    pass


def test_build_menu():
    assert rhdir.build_menu(['bladibla\n', '` ', '`<>', '<>`_', '`x <y>`_'],
                            'Hallo') == ['<p></p><h2>Hallo</h2><ul class="menu">',
                                         '<li>bladibla</li>', '<li>`</li>', '<li>`<></li>',
                                         '<li><>`_</li>',
                                         '<li><a class="reference external" href="y">x</a></li>',
                                         '</ul>']


def test_bottom(monkeypatch):
    monkeypatch.setattr(rhdir.Bottom, '__init__', mock_init)
    testsubj = rhdir.Bottom()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    year = rhdir.datetime.datetime.today().year
    data = testsubj.run()[0][0]
    assert str(data) == (f'<div class="madeby">content and layout created {year} by Albert Visser '
                         '<a href="mailto:info@magiokis.nl">contact me</a></div>')
    testsubj = rhdir.Bottom()
    testsubj.arguments = ['3', '../nn', 'll']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<div class="grid_3"><div style="text-align: center">'
                         '<a class="reference external" href="../nn">ll</a>'
                         f'<div class="madeby">content and layout created {year} by Albert Visser '
                         '<a href="mailto:info@magiokis.nl">contact me</a></div></div></div>'
                         '<div class="clear">&nbsp;</div><div class="grid_3 spacer">'
                         '&nbsp;</div><div class="clear">&nbsp;</div>')
    testsubj = rhdir.Bottom()
    testsubj.arguments = ['-1', 'None']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<div style="text-align: center"><a class="reference external" '
                         'href="about.html">terug naar de indexpagina</a> '
                         f'<div class="madeby">content and layout created {year} by Albert Visser '
                         '<a href="mailto:info@magiokis.nl">contact me</a></div></div>')


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
    assert testsubj.run() == []


def test_myheader(monkeypatch):
    def mock_build_menu(*args):
        return 'menu_text'
    monkeypatch.setattr(rhdir.MyHeader, '__init__', mock_init)
    monkeypatch.setattr(rhdir, 'build_menu', mock_build_menu)
    testsubj = rhdir.MyHeader()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner"><a href="/" id="logo" rel="home"'
                         ' title="Home"><img alt="Home" src="/zing.gif"/></a>'
                         '<div id="name-and-slogan"><div id="site-slogan">'
                         'Magiokis Productions Proudly Presents!</div></div></header>'
                         '<div id="main"><div id="navigation">menu_text</div></div>'
                         '<div id="content" class="column"><h1 class="page-title"></h1>')

    testsubj.arguments= []
    testsubj.options = {'title': 'Hello World!',
                        'href': 'Go-Home!',
                        'image': 'link-to-image',
                        'text': 'XXXXX',
                        'menu': 'menufile.rst',
                        'site': 'helloworld' }
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner"><a href="Go-Home!" id="logo" '
                         'rel="home" title="Home"><img alt="Home" src="link-to-image"/></a>'
                         '<div id="name-and-slogan"><div id="site-slogan">XXXXX</div>'
                         '</div></header><div id="main"><div id="navigation"></div></div><div'
                         ' id="content" class="column"><h1 class="page-title">Hello World!</h1>')


def test_byline(monkeypatch):
    monkeypatch.setattr(rhdir.ByLine, '__init__', mock_init)
    testsubj = rhdir.ByLine()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>Submitted</span></p></header>')
    testsubj = rhdir.ByLine()
    testsubj.arguments= ['some_text']
    testsubj.options = {'date': 'some_date'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span>'
                         ' on <time>some_date</time></p></header>')
    testsubj.arguments= ['some_text']
    testsubj.options = {'date': 'some_date', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span>'
                         ' op <time>some_date</time></p></header>')
    testsubj.arguments= ['some_text']
    testsubj.options = {'author': 'some_name'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> by '
                         '<span>some_name</span></p></header>')
    testsubj.arguments= ['some_text']
    testsubj.options = {'author': 'some_name', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> door '
                         '<span>some_name</span></p></header>')
    testsubj.arguments= ['some_text']
    testsubj.options = {'date': 'some_date', 'author': 'some_name'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> by <span>some_name</span>'
                         ' on <time>some_date</time></p></header>')
    testsubj.arguments= ['some_text']
    testsubj.options = {'date': 'some_date', 'author': 'some_name', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> door <span>some_name</span>'
                         ' op <time>some_date</time></p></header>')


def test_audio(monkeypatch):
    monkeypatch.setattr(rhdir.Audio, '__init__', mock_init)
    testsubj = rhdir.Audio()
    testsubj.arguments= ['listen-to-this']
    testsubj.options = {}
    testsubj.content = ['x', 'y']
    data = testsubj.run()[0][0]
    assert str(data) == '<audio controls src="listen-to-this"></audio><p>x<br>\ny</p>'


def test_menutext(monkeypatch):
    def mock_build_menu(*args, **kwargs):
        title = kwargs.get('title', '')
        return '{}<>{}<>'.format(title, ''.join([x for x in args[0]]))
    monkeypatch.setattr(rhdir.MenuText, '__init__', mock_init)
    monkeypatch.setattr(rhdir, 'build_menu', mock_build_menu)
    testsubj = rhdir.MenuText()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<><>'
    testsubj = rhdir.MenuText()
    testsubj.arguments= ['is_navmenu']
    testsubj.options = {}
    testsubj.content = ['line_1']
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation">&nbsp;<>line_1<></div>'
    testsubj = rhdir.MenuText()
    testsubj.arguments= ['menu_title']
    testsubj.options = {}
    testsubj.content = ['line_1']
    data = testsubj.run()[0][0]
    assert str(data) == 'menu_title<>line_1<>'


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
    assert str(data) == (f'{start}<p><em>o</em><br>x<br><em>y: </em>z</p><p><em>a: </em>b<br>'
                         f'<em>a: </em>c<br>d<br><em>a: </em>e</p>{end}')


def test_strofentekst(monkeypatch):
    monkeypatch.setattr(rhdir.StrofenTekst, '__init__', mock_init)
    testsubj = rhdir.StrofenTekst()
    testsubj.arguments= []
    testsubj.options = {'titel': 'een titel', 'tekst': 'een tekst'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="unnamed-container">\n<div class="titel">een titel</div>'
                         '\n<div class="tekst">een tekst</div>\n<div class="couplet">'
                         '\n</div></div>')
    testsubj = rhdir.StrofenTekst()
    testsubj.soortnaam = 'x'
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['een regel', '--', 'nog een regel', '--', ' nog een', '--', '   nog een',
                        '--', 'en nog een']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="x">\n<div class="couplet">'
                         '\n<div class="regel">een regel</div>'
                         '\n</div>\n<div class="couplet">'
                         '\n<div class="regel">nog een regel</div>'
                         '\n</div>\n<div class="refrein">'
                         '\n<div class="regel"> nog een</div>'
                         '\n</div>\n<div class="refrein">'
                         '\n<div class="regel">   nog een</div>'
                         '\n</div>\n<div class="couplet">'
                         '\n<div class="regel">en nog een</div>'
                         '\n</div></div>')


def test_rolespec(monkeypatch):
    monkeypatch.setattr(rhdir.RoleSpec, '__init__', mock_init)
    testsubj = rhdir.RoleSpec()
    testsubj.arguments= []
    testsubj.options = {'titel': 'een titel', 'tekst': 'een tekst'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="rollen">\n<div class="titel">een titel</div>'
                         '\n<div class="tekst">een tekst</div>\n</div>')
    testsubj = rhdir.RoleSpec()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['regel 1', 'regel 2']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="rollen">\n<div class="rol">regel 1</div>'
                         '\n<div class="rol">regel 2</div>\n</div>')


def test_scene(monkeypatch):
    monkeypatch.setattr(rhdir.Scene, '__init__', mock_init)
    testsubj = rhdir.Scene()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '\n<div class="scene">\n</div>'
    testsubj = rhdir.Scene()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['xx yy']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">\n<div class="actie">xx yy</div>\n</div>')
    testsubj = rhdir.Scene()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['::xx']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">\n<div class="actie">xx</div>\n</div>')
    # ik weet niet of dit is wat ik wil, maar zo beginnen is mogelijk ook geen realistische situatie
    # en moet ik misschien afkeuren
    testsubj = rhdir.Scene()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['xx::yy', 'zz::aa']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">'
                         '\n<div class="claus">\n<div class="spreker">xx</div>'
                         '\n<div class="spraak">\n<div class="regel">yy</div>'
                         '\n</div>\n</div>'
                         '\n<div class="claus">\n<div class="spreker">zz</div>'
                         '\n<div class="spraak">\n<div class="regel">aa</div>'
                         '\n</div>\n</div>\n</div>')

    testsubj = rhdir.Scene()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['xx::yy', 'xx yy', '::aa', '::bb']
    data = testsubj.run()[0][0]
    # assert str(data) == ('\n<div class="scene">'
    #                      '\n<div class="claus">\n<div class="spreker">xx</div>'
    #                      '\n<div class="spraak">\n<div class="regel">yy</div>'
    #                      '\n<div class="regel">xx yy</div>'
    #                      '\n<div class="actie">aa</div>'
    #                      '\n</div>\n</div>\n<div class="actie">bb</div>\n</div>')
    # bovenstaand is volgens mij wat ik zou willen dat het deed maar het doet nu:
    assert str(data) == ('\n<div class="scene">'
                         '\n<div class="claus">\n<div class="spreker">xx</div>'
                         '\n<div class="spraak">\n<div class="regel">yy</div>'
                         '\n<div class="regel">xx yy</div>'
                         '\n</div>\n</div>\n<div class="actie">aa</div>'
                         '\n<div class="actie">bb</div>'
                         '\n</div>')


def test_anno(monkeypatch):
    monkeypatch.setattr(rhdir.Anno, '__init__', mock_init)
    testsubj = rhdir.Anno()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['een regel', 'nog een regel']
    data = testsubj.run()[0][0]
    assert str(data) == '\n<div class="anno">\n<p>een regel</p>\n<p>nog een regel</p>\n</div>'


def test_gedicht(monkeypatch, capsys):
    def mock_init(self, *args):
        print('initializing class with soortnaam', self.soortnaam)
    monkeypatch.setattr(rhdir.StrofenTekst, '__init__', mock_init)
    rhdir.Gedicht()
    assert capsys.readouterr().out == 'initializing class with soortnaam gedicht\n'


def test_songtekst(monkeypatch, capsys):
    def mock_init(self, *args):
        print('initializing class with soortnaam', self.soortnaam)
    monkeypatch.setattr(rhdir.StrofenTekst, '__init__', mock_init)
    rhdir.SongTekst()
    assert capsys.readouterr().out == 'initializing class with soortnaam songtekst\n'


def test_startblock(monkeypatch):
    monkeypatch.setattr(rhdir.StartBlock, '__init__', mock_init)
    testsubj = rhdir.StartBlock()
    testsubj.arguments= ['block']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="block">'
    testsubj = rhdir.StartBlock()
    testsubj.arguments= ['block']
    testsubj.options = {'text': 'this is a block'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="block">\n<div class="title">this is a block</div>'


def test_endblock(monkeypatch):
    monkeypatch.setattr(rhdir.EndBlock, '__init__', mock_init)
    testsubj = rhdir.EndBlock()
    testsubj.arguments= ['block']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div> <!-- end block -->\n'


def test_startsidebar(monkeypatch):
    monkeypatch.setattr(rhdir.StartSideBar, '__init__', mock_init)
    testsubj = rhdir.StartSideBar()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div><aside><section class="region-sidebar-first column">'
                         '<div class="block">')


def test_sidebarkop(monkeypatch):
    monkeypatch.setattr(rhdir.SideBarKop, '__init__', mock_init)
    testsubj = rhdir.SideBarKop()
    testsubj.arguments= ['Tekst']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<h1>Tekst</h1>')


def test_endsidebar(monkeypatch):
    monkeypatch.setattr(rhdir.EndSideBar, '__init__', mock_init)
    testsubj = rhdir.EndSideBar()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></section><section class="region-sidebar-second column">'
                         '<div class="block"><p>&nbsp;</p></div></section></aside>')


def test_myfooter(monkeypatch):
    monkeypatch.setattr(rhdir.MyFooter, '__init__', mock_init)
    testsubj = rhdir.MyFooter()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></div>\n<div id="footer" class="region region-bottom">\n'
                         '<div id="block-block-1" class="block block-block first last odd">\n'
                         "<footer>\n<p>Please don't copy without source attribution. contact me:"
                         ' <a href="mailto:info@magiokis.nl">info@magiokis.nl</a></p></footer>')
    testsubj = rhdir.MyFooter()
    testsubj.arguments= []
    testsubj.options = {'text': 'some text', 'mailto': 'message-me'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></div>\n<div id="footer" class="region region-bottom">\n'
                         '<div id="block-block-1" class="block block-block first last odd">\n'
                         '<footer>\n<p>some text: <a href="mailto:message-me">message-me'
                         '</a></p></footer>')


def test_startcols(monkeypatch):
    monkeypatch.setattr(rhdir.StartCols, '__init__', mock_init)
    testsubj = rhdir.StartCols()
    testsubj.arguments= ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="container_x">\n'


def test_endcols(monkeypatch):
    monkeypatch.setattr(rhdir.EndCols, '__init__', mock_init)
    testsubj = rhdir.EndCols()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n'


def test_firstcol(monkeypatch):
    monkeypatch.setattr(rhdir.FirstCol, '__init__', mock_init)
    testsubj = rhdir.FirstCol()
    testsubj.arguments= ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="grid_x ">\n'
    testsubj = rhdir.FirstCol()
    testsubj.arguments= ['x', 'y']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="grid_x y">\n'


def test_nextcol(monkeypatch):
    monkeypatch.setattr(rhdir.NextCol, '__init__', mock_init)
    testsubj = rhdir.NextCol()
    testsubj.arguments= ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="grid_x ">\n'
    testsubj = rhdir.NextCol()
    testsubj.arguments= ['x', 'y']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="grid_x y">\n'


def test_clearcol(monkeypatch):
    monkeypatch.setattr(rhdir.ClearCol, '__init__', mock_init)
    testsubj = rhdir.ClearCol()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="clear">&nbsp;</div>\n'


def test_spacer(monkeypatch):
    monkeypatch.setattr(rhdir.Spacer, '__init__', mock_init)
    testsubj = rhdir.Spacer()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="spacer">&nbsp;</div>\n'
    testsubj = rhdir.Spacer()
    testsubj.arguments= ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<div class="grid_x spacer">&nbsp;</div>\n'
                         '<div class="clear">&nbsp;</div>\n')


def test_startbody(monkeypatch):
    monkeypatch.setattr(rhdir.StartBody, '__init__', mock_init)
    testsubj = rhdir.StartBody()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="container">'
    testsubj = rhdir.StartBody()
    testsubj.arguments= []
    testsubj.options = {'header': 'some text'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="container"> <div id="header">some text</div>'


def test_navlinks(monkeypatch, capsys):
    def mock_error(self, *args):
        print(args[0])
    monkeypatch.setattr(rhdir.NavLinks, '__init__', mock_init)
    testsubj = rhdir.NavLinks()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation"><ul></ul></div>'
    testsubj = rhdir.NavLinks()
    monkeypatch.setattr(rhdir.NavLinks, 'error', mock_error)
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['menu tekst?']
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation"><ul></ul></div>'
    assert capsys.readouterr().out == 'Illegal content: `menu tekst?`\n'
    testsubj = rhdir.NavLinks()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['. `menu <jansen']
    data = testsubj.run()[0][0]
    assert str(data) == ('<div id="navigation"><ul></ul></div>')
    assert capsys.readouterr().out == 'Submenu entry before main menu: `. `menu <jansen`\n'
    testsubj = rhdir.NavLinks()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['`linktekst <linkadres>`_', '`menutekst`', '. `linktekst <linkadres>`_',
                        '. `linktekst <linkadres>`_', '`linktekst <linkadres>`_']
    data = testsubj.run()[0][0]
    assert str(data) == ('<div id="navigation"><ul>'
                         '<li class="menu"><a href="linkadres">linktekst</a></li>'
                         '<li class="menu">menutekst<ul>'
                         '<li><a href="linkadres">linktekst</a></li>'
                         '<li><a href="linkadres">linktekst</a></li></ul></li>'
                         '<li class="menu"><a href="linkadres">linktekst</a></li>'
                         '</ul></div>')


def test_textheader(monkeypatch):
    monkeypatch.setattr(rhdir.TextHeader, '__init__', mock_init)
    testsubj = rhdir.TextHeader()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="body"><h1 class="page-title">&nbsp;</h1>'
    testsubj = rhdir.TextHeader()
    testsubj.arguments= ['some text']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="body"><h1 class="page-title">some text</h1>'


def test_startmarginless(monkeypatch):
    monkeypatch.setattr(rhdir.StartMarginless, '__init__', mock_init)
    testsubj = rhdir.StartMarginless()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div></div><div style="margin: auto">'


def test_endmarginless(monkeypatch):
    monkeypatch.setattr(rhdir.EndMarginless, '__init__', mock_init)
    testsubj = rhdir.EndMarginless()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div><div id="container"><div id="body">'


def test_bottomnav(monkeypatch):
    monkeypatch.setattr(rhdir.BottomNav, '__init__', mock_init)
    testsubj = rhdir.BottomNav()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div><div id="botnav"><ul></ul></div></div>'
    testsubj = rhdir.BottomNav()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = ['', 'plain text', '` only', '` < only', '` <>`_', '`x <y>`_']
    data = testsubj.run()[0][0]
    assert str(data) == ('<div><div id="botnav"><ul><li class="menu"></li>'
                         '<li class="menu">plain text</li><li class="menu">` only</li>'
                         '<li class="menu">` < only</li><li class="menu"><a href=""></a></li>'
                         '<li class="menu"><a href="y">x</a></li></ul></div></div>')


def test_endbody(monkeypatch):
    monkeypatch.setattr(rhdir.EndBody, '__init__', mock_init)
    testsubj = rhdir.EndBody()
    testsubj.arguments= []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div></div>'
