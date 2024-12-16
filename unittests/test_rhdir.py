"""unittests for ./app/rst2html_directives.py
"""
import app.rst2html_directives as testee
# docutils handelt zelf ontbrekende verplichte argumenten af dus hoeven we hier niet te doen
# with pytest.raises(KeyError):
#     testsubj.run()


def mock_init(*args):
    """stub to mimic initialisation of the directive classes
    """


def test_build_menu():
    """unittest for rst2html_directives.build_menu
    """
    assert testee.build_menu(['bladibla\n', '` ', '`<>', '<>`_', '`x <y>`_'], 'Hallo') == [
            '<p></p><h2>Hallo</h2><ul class="menu">',
            '<li>bladibla</li>', '<li>`</li>', '<li>`<></li>', '<li><>`_</li>',
            '<li><a class="reference external" href="y">x</a></li>',
            '</ul>']
    assert testee.build_menu(['bladibla\n', '` ', '`<>', '<>`_', '`x <y>`_']) == [
            '<ul class="menu">',
            '<li>bladibla</li>', '<li>`</li>', '<li>`<></li>', '<li><>`_</li>',
            '<li><a class="reference external" href="y">x</a></li>',
            '</ul>']


def test_bottom(monkeypatch):
    """unittest for rst2html_directives.Bottom
    """
    monkeypatch.setattr(testee.Bottom, '__init__', mock_init)
    testsubj = testee.Bottom()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    year = testee.datetime.datetime.today().year
    data = testsubj.run()[0][0]
    assert str(data) == (f'<div class="madeby">content and layout created {year} by Albert Visser '
                         '<a href="mailto:info@magiokis.nl">contact me</a></div>')
    testsubj = testee.Bottom()
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
    testsubj = testee.Bottom()
    testsubj.arguments = ['-1', 'None']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<div style="text-align: center"><a class="reference external" '
                         'href="about.html">terug naar de indexpagina</a> '
                         f'<div class="madeby">content and layout created {year} by Albert Visser '
                         '<a href="mailto:info@magiokis.nl">contact me</a></div></div>')


def test_refkey(monkeypatch):
    """unittest for rst2html_directives.Refkey
    """
    monkeypatch.setattr(testee.RefKey, '__init__', mock_init)
    testsubj = testee.RefKey()
    testsubj.arguments = ['hallo']
    testsubj.options = {}
    testsubj.content = []
    assert testsubj.run() == []


def test_myinclude(monkeypatch):
    """unittest for rst2html_directives.MyInclude
    """
    monkeypatch.setattr(testee.MyInclude, '__init__', mock_init)
    testsubj = testee.MyInclude()
    assert testsubj.run() == []


def test_myheader(monkeypatch, capsys, tmp_path):
    """unittest for rst2html_directives.MyHeader
    """
    def mock_read(sitename):
        print(f"called dml.read_settings with arg '{sitename}'")
        if sitename == 'magiokis':
            return {'image': '/zing.gif', 'blurb': 'Magiokis Productions Proudly Presents!',
                    'menu': 'hoofdmenu.rst'}
        raise FileNotFoundError

    def mock_build_menu(*args):
        """stub
        """
        print("called build_menu with args", args)
        return 'menu_text'
    monkeypatch.setattr(testee, 'DFLT', 'magiokis')
    monkeypatch.setattr(testee.dml, 'read_settings', mock_read)
    monkeypatch.setattr(testee, 'WEBROOT', tmp_path)
    (tmp_path / 'magiokis' / '.source').mkdir(parents=True)
    (tmp_path / 'magiokis' / '.source' / 'hoofdmenu.rst').write_text('- menu link 1\n'
                                                                     '- menu link 2\n')
    (tmp_path / 'helloworld' / '.source').mkdir(parents=True)
    (tmp_path / 'helloworld' / '.source' / 'menufile.rst').write_text('- menu link X\n'
                                                                      '- menu link Y\n')
    monkeypatch.setattr(testee.MyHeader, '__init__', mock_init)
    monkeypatch.setattr(testee, 'build_menu', mock_build_menu)
    testsubj = testee.MyHeader()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner"><a href="/" id="logo" rel="home"'
                         ' title="Home"><img alt="Home" src="/zing.gif"/></a>'
                         '<div id="name-and-slogan"><div id="site-slogan">'
                         'Magiokis Productions Proudly Presents!</div></div></header>'
                         '<div id="main"><div id="navigation">menu_text</div></div>'
                         '<div id="content" class="column">')
    # loc = testee.WEBROOT / 'magiokis' / '.source' / 'hoofdmenu.rst'
    assert capsys.readouterr().out == (
            "called dml.read_settings with arg 'magiokis'\n"
            "called build_menu with args (['menu link 1', 'menu link 2'],)\n")

    testsubj.options = {'site': 'xxx', 'title': 'Hello World!'}
    testsubj.content = ['will not be used']
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="/" id="logo" rel="home" title="Home"></header>'
                         '<div id="content" class="column"><h1 class="page-title">Hello World!</h1>')
    assert capsys.readouterr().out == "called dml.read_settings with arg 'xxx'\n"

    testsubj.options = {'site': 'xxx', 'href': 'Go-Home!'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="Go-Home!" id="logo" rel="home" title="Home"></header>'
                         '<div id="content" class="column">')
    assert capsys.readouterr().out == "called dml.read_settings with arg 'xxx'\n"

    testsubj.options = {'site': 'xxx', 'image': 'link-to-image'}
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="/" id="logo" rel="home" title="Home">'
                         '<img alt="Home" src="link-to-image"/></a></header>'
                         '<div id="content" class="column">')
    assert capsys.readouterr().out == "called dml.read_settings with arg 'xxx'\n"

    testsubj.options = {'site': 'xxx', 'text': 'XXXXX'}
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="/" id="logo" rel="home" title="Home">'
                         '<div id="name-and-slogan"><div id="site-slogan">XXXXX</div></div>'
                         '</header><div id="content" class="column">')
    assert capsys.readouterr().out == "called dml.read_settings with arg 'xxx'\n"

    testsubj.options = {'site': 'xxx', 'menu': 'menufile.rst'}
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="/" id="logo" rel="home" title="Home"></header>'
                         '<div id="content" class="column">')
    assert capsys.readouterr().out == "called dml.read_settings with arg 'xxx'\n"

    testsubj.options = {'site': 'helloworld', 'menu': 'menufile.rst'}
    data = testsubj.run()[0][0]
    assert str(data) == ('<header id="header" role="banner">'
                         '<a href="/" id="logo" rel="home" title="Home">'
                         '</header><div id="main"><div id="navigation">menu_text</div></div>'
                         '<div id="content" class="column">')
    assert capsys.readouterr().out == (
            "called dml.read_settings with arg 'helloworld'\n"
            "called build_menu with args (['menu link X', 'menu link Y'],)\n")


def test_byline(monkeypatch):
    """unittest for rst2html_directives.ByLine
    """
    monkeypatch.setattr(testee.ByLine, '__init__', mock_init)
    testsubj = testee.ByLine()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>Submitted</span></p></header>')
    testsubj = testee.ByLine()
    testsubj.arguments = ['some_text']
    testsubj.options = {'date': 'some_date'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span>'
                         ' on <time>some_date</time></p></header>')
    testsubj.arguments = ['some_text']
    testsubj.options = {'date': 'some_date', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span>'
                         ' op <time>some_date</time></p></header>')
    testsubj.arguments = ['some_text']
    testsubj.options = {'author': 'some_name'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> by '
                         '<span>some_name</span></p></header>')
    testsubj.arguments = ['some_text']
    testsubj.options = {'author': 'some_name', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> door '
                         '<span>some_name</span></p></header>')
    testsubj.arguments = ['some_text']
    testsubj.options = {'date': 'some_date', 'author': 'some_name'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> by <span>some_name</span>'
                         ' on <time>some_date</time></p></header>')
    testsubj.arguments = ['some_text']
    testsubj.options = {'date': 'some_date', 'author': 'some_name', 'lang': 'nl'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<p></p><header><p><span>some_text</span> door <span>some_name</span>'
                         ' op <time>some_date</time></p></header>')


def test_audio(monkeypatch):
    """unittest for rst2html_directives.Audio
    """
    monkeypatch.setattr(testee.Audio, '__init__', mock_init)
    testsubj = testee.Audio()
    testsubj.arguments = ['listen-to-this']
    testsubj.options = {}
    testsubj.content = ['x', 'y']
    data = testsubj.run()[0][0]
    assert str(data) == '<audio controls src="listen-to-this"></audio><p>x<br>\ny</p>'


def test_menutext(monkeypatch):
    """unittest for rst2html_directives.MenuText
    """
    def mock_build_menu(*args, **kwargs):
        """stub
        """
        title = kwargs.get('title', '')
        return f"{title}<>{''.join(list(args[0]))}<>"
    monkeypatch.setattr(testee.MenuText, '__init__', mock_init)
    monkeypatch.setattr(testee, 'build_menu', mock_build_menu)
    testsubj = testee.MenuText()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<><>'
    testsubj = testee.MenuText()
    testsubj.arguments = ['is_navmenu']
    testsubj.options = {}
    testsubj.content = ['line_1']
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation">&nbsp;<>line_1<></div>'
    testsubj = testee.MenuText()
    testsubj.arguments = ['menu_title']
    testsubj.options = {}
    testsubj.content = ['line_1']
    data = testsubj.run()[0][0]
    assert str(data) == 'menu_title<>line_1<>'


def test_transcript(monkeypatch):
    """unittest for rst2html_directives.Transcript
    """
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
    monkeypatch.setattr(testee.Transcript, '__init__', mock_init)
    testsubj = testee.Transcript()
    # testsubj.arguments
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == start + end

    testsubj = testee.Transcript()
    # testsubj.options = {'title': 'o'}
    testsubj.content = [':title: o', 'x', 'y::z', '::', 'a::b', '::c', 'd', '::e']
    data = testsubj.run()[0][0]  # .children[0]
    assert str(data) == (f'{start}<p><em>o</em><br>x<br><em>y: </em>z</p><p><em>a: </em>b<br>'
                         f'<em>a: </em>c<br>d<br><em>a: </em>e</p>{end}')
    # for full branch coverage
    testsubj.content = ['::']
    data = testsubj.run()[0][0]
    assert str(data) == f'{start}<p>{end}'


def test_strofentekst(monkeypatch):
    """unittest for rst2html_directives.StrofenTekst
    """
    monkeypatch.setattr(testee.StrofenTekst, '__init__', mock_init)
    testsubj = testee.StrofenTekst()
    testsubj.arguments = []
    testsubj.options = {'titel': 'een titel', 'tekst': 'een tekst'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="unnamed-container">\n<div class="titel">een titel</div>'
                         '\n<div class="tekst">een tekst</div>\n<div class="couplet">'
                         '\n</div></div>')
    testsubj = testee.StrofenTekst()
    testsubj.soortnaam = 'x'
    testsubj.arguments = []
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
    """unittest for rst2html_directives.RoleSpec
    """
    monkeypatch.setattr(testee.RoleSpec, '__init__', mock_init)
    testsubj = testee.RoleSpec()
    testsubj.arguments = []
    testsubj.options = {'titel': 'een titel', 'tekst': 'een tekst'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="rollen">\n<div class="titel">een titel</div>'
                         '\n<div class="tekst">een tekst</div>\n</div>')
    testsubj = testee.RoleSpec()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['regel 1', 'regel 2']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="rollen">\n<div class="rol">regel 1</div>'
                         '\n<div class="rol">regel 2</div>\n</div>')


def test_scene(monkeypatch):
    """unittest for rst2html_directives.Scene
    """
    monkeypatch.setattr(testee.Scene, '__init__', mock_init)
    testsubj = testee.Scene()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '\n<div class="scene">\n</div>'
    testsubj = testee.Scene()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['xx yy']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">\n<div class="actie">xx yy</div>\n</div>')
    testsubj = testee.Scene()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['::xx']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">\n<div class="actie">xx</div>\n</div>')
    # ik weet niet of dit is wat ik wil, maar zo beginnen is mogelijk ook geen realistische situatie
    # en moet ik misschien afkeuren
    testsubj = testee.Scene()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['xx::yy', 'zz::aa']
    data = testsubj.run()[0][0]
    assert str(data) == ('\n<div class="scene">'
                         '\n<div class="claus">\n<div class="spreker">xx</div>'
                         '\n<div class="spraak">\n<div class="regel">yy</div>'
                         '\n</div></div>'
                         '\n<div class="claus">\n<div class="spreker">zz</div>'
                         '\n<div class="spraak">\n<div class="regel">aa</div>'
                         '\n</div></div>\n</div>')

    testsubj = testee.Scene()
    testsubj.arguments = []
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
                         '\n</div></div>\n<div class="actie">aa</div>'
                         '\n<div class="actie">bb</div>'
                         '\n</div>')


def test_anno(monkeypatch):
    """unittest for rst2html_directives.Anno
    """
    monkeypatch.setattr(testee.Anno, '__init__', mock_init)
    testsubj = testee.Anno()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['een regel', 'nog een regel']
    data = testsubj.run()[0][0]
    assert str(data) == '\n<div class="anno">\n<p>een regel</p>\n<p>nog een regel</p>\n</div>'


def test_gedicht(monkeypatch, capsys):
    """unittest for rst2html_directives.Gedicht
    """
    def mock_init(self, *args):
        """stub
        """
        print('initializing class with soortnaam', self.soortnaam)
    monkeypatch.setattr(testee.StrofenTekst, '__init__', mock_init)
    testee.Gedicht()
    assert capsys.readouterr().out == 'initializing class with soortnaam gedicht\n'


def test_songtekst(monkeypatch, capsys):
    """unittest for rst2html_directives.SongTekst
    """
    def mock_init(self, *args):
        """stub
        """
        print('initializing class with soortnaam', self.soortnaam)
    monkeypatch.setattr(testee.StrofenTekst, '__init__', mock_init)
    testee.SongTekst()
    assert capsys.readouterr().out == 'initializing class with soortnaam songtekst\n'


def test_startblock(monkeypatch):
    """unittest for rst2html_directives.StartBlock
    """
    monkeypatch.setattr(testee.StartBlock, '__init__', mock_init)
    testsubj = testee.StartBlock()
    testsubj.arguments = ['block']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="block">'
    testsubj = testee.StartBlock()
    testsubj.arguments = ['block']
    testsubj.options = {'text': 'this is a block'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="block">\n<div class="title">this is a block</div>'


def test_endblock(monkeypatch):
    """unittest for rst2html_directives.EndBlock
    """
    monkeypatch.setattr(testee.EndBlock, '__init__', mock_init)
    testsubj = testee.EndBlock()
    testsubj.arguments = ['block']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div> <!-- end block -->\n'


def test_startsidebar(monkeypatch):
    """unittest for rst2html_directives.StartSideBar
    """
    monkeypatch.setattr(testee.StartSideBar, '__init__', mock_init)
    testsubj = testee.StartSideBar()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div><aside><section class="region-sidebar-first column">'
                         '<div class="block">')


def test_sidebarkop(monkeypatch):
    """unittest for rst2html_directives.SideBarKop
    """
    monkeypatch.setattr(testee.SideBarKop, '__init__', mock_init)
    testsubj = testee.SideBarKop()
    testsubj.arguments = ['Tekst']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<h1>Tekst</h1>')


def test_endsidebar(monkeypatch):
    """unittest for rst2html_directives.EndSideBar
    """
    monkeypatch.setattr(testee.EndSideBar, '__init__', mock_init)
    testsubj = testee.EndSideBar()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></section><section class="region-sidebar-second column">'
                         '<div class="block"><p>&nbsp;</p></div></section></aside>')


def test_myfooter(monkeypatch):
    """unittest for rst2html_directives.MyFooter
    """
    monkeypatch.setattr(testee.MyFooter, '__init__', mock_init)
    testsubj = testee.MyFooter()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></div>\n<div id="footer" class="region region-bottom">\n'
                         '<div id="block-block-1" class="block block-block first last odd">\n'
                         "<footer>\n<p>Please don't copy without source attribution. contact me:"
                         ' <a href="mailto:info@magiokis.nl">info@magiokis.nl</a></p></footer>')
    testsubj = testee.MyFooter()
    testsubj.arguments = []
    testsubj.options = {'text': 'some text', 'mailto': 'message-me'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('</div></div>\n<div id="footer" class="region region-bottom">\n'
                         '<div id="block-block-1" class="block block-block first last odd">\n'
                         '<footer>\n<p>some text: <a href="mailto:message-me">message-me'
                         '</a></p></footer>')


def test_startcols(monkeypatch):
    """unittest for rst2html_directives.StartCols
    """
    monkeypatch.setattr(testee.StartCols, '__init__', mock_init)
    testsubj = testee.StartCols()
    testsubj.arguments = ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="container_x">\n'


def test_endcols(monkeypatch):
    """unittest for rst2html_directives.EndCols
    """
    monkeypatch.setattr(testee.EndCols, '__init__', mock_init)
    testsubj = testee.EndCols()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n'


def test_firstcol(monkeypatch):
    """unittest for rst2html_directives.FirstCol
    """
    monkeypatch.setattr(testee.FirstCol, '__init__', mock_init)
    testsubj = testee.FirstCol()
    testsubj.arguments = ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="grid_x ">\n'
    testsubj = testee.FirstCol()
    testsubj.arguments = ['x', 'y']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="grid_x y">\n'


def test_nextcol(monkeypatch):
    """unittest for rst2html_directives.NextCol
    """
    monkeypatch.setattr(testee.NextCol, '__init__', mock_init)
    testsubj = testee.NextCol()
    testsubj.arguments = ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="grid_x ">\n'
    testsubj = testee.NextCol()
    testsubj.arguments = ['x', 'y']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="grid_x y">\n'


def test_clearcol(monkeypatch):
    """unittest for rst2html_directives.ClearCol
    """
    monkeypatch.setattr(testee.ClearCol, '__init__', mock_init)
    testsubj = testee.ClearCol()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div>\n<div class="clear">&nbsp;</div>\n'


def test_spacer(monkeypatch):
    """unittest for rst2html_directives.Spacer
    """
    monkeypatch.setattr(testee.Spacer, '__init__', mock_init)
    testsubj = testee.Spacer()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div class="spacer">&nbsp;</div>\n'
    testsubj = testee.Spacer()
    testsubj.arguments = ['x']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == ('<div class="grid_x spacer">&nbsp;</div>\n'
                         '<div class="clear">&nbsp;</div>\n')


def test_startbody(monkeypatch):
    """unittest for rst2html_directives.StartBody
    """
    monkeypatch.setattr(testee.StartBody, '__init__', mock_init)
    testsubj = testee.StartBody()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="container">'
    testsubj = testee.StartBody()
    testsubj.arguments = []
    testsubj.options = {'header': 'some text'}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="container"> <div id="header">some text</div>'


def test_navlinks(monkeypatch, capsys):
    """unittest for rst2html_directives.NavLinks
    """
    def mock_error(self, *args):
        """stub
        """
        print(args[0])
    monkeypatch.setattr(testee.NavLinks, '__init__', mock_init)
    testsubj = testee.NavLinks()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation"><ul></ul></div>'
    testsubj = testee.NavLinks()
    monkeypatch.setattr(testee.NavLinks, 'error', mock_error)
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['menu tekst?']
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="navigation"><ul></ul></div>'
    assert capsys.readouterr().out == 'Illegal content: `menu tekst?`\n'
    testsubj = testee.NavLinks()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['. `menu <jansen']
    data = testsubj.run()[0][0]
    assert str(data) == ('<div id="navigation"><ul></ul></div>')
    assert capsys.readouterr().out == 'Submenu entry before main menu: `. `menu <jansen`\n'
    testsubj = testee.NavLinks()
    testsubj.arguments = []
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
    """unittest for rst2html_directives.TextHeader
    """
    monkeypatch.setattr(testee.TextHeader, '__init__', mock_init)
    testsubj = testee.TextHeader()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="body"><h1 class="page-title">&nbsp;</h1>'
    testsubj = testee.TextHeader()
    testsubj.arguments = ['some text']
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div id="body"><h1 class="page-title">some text</h1>'


def test_startmarginless(monkeypatch):
    """unittest for rst2html_directives.StartMarginless
    """
    monkeypatch.setattr(testee.StartMarginless, '__init__', mock_init)
    testsubj = testee.StartMarginless()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div></div><div style="margin: auto">'


def test_endmarginless(monkeypatch):
    """unittest for rst2html_directives.EndMarginless
    """
    monkeypatch.setattr(testee.EndMarginless, '__init__', mock_init)
    testsubj = testee.EndMarginless()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div><div id="container"><div id="body">'


def test_bottomnav(monkeypatch):
    """unittest for rst2html_directives.BottomNav
    """
    monkeypatch.setattr(testee.BottomNav, '__init__', mock_init)
    testsubj = testee.BottomNav()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '<div><div id="botnav"><ul></ul></div></div>'
    testsubj = testee.BottomNav()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = ['', 'plain text', '` only', '` < only', '` <>`_', '`x <y>`_']
    data = testsubj.run()[0][0]
    assert str(data) == ('<div><div id="botnav"><ul><li class="menu"></li>'
                         '<li class="menu">plain text</li><li class="menu">` only</li>'
                         '<li class="menu">` < only</li><li class="menu"><a href=""></a></li>'
                         '<li class="menu"><a href="y">x</a></li></ul></div></div>')


def test_endbody(monkeypatch):
    """unittest for rst2html_directives.EndBody
    """
    monkeypatch.setattr(testee.EndBody, '__init__', mock_init)
    testsubj = testee.EndBody()
    testsubj.arguments = []
    testsubj.options = {}
    testsubj.content = []
    data = testsubj.run()[0][0]
    assert str(data) == '</div></div>'
