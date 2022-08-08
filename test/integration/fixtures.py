def rstdata_1():
    return 'test document\n=============\n\nThis is the first document'

def rstdata_2():
    return 'test document\n=============\n\nThis is the (slightly changed) first document'

def rstdata_3():
    return ('test document\n=============\n\nThis is the (slightly changed) first document\n\n'
            "It's been changed even more")

def rstdata_4():
    return ('test document\n=============\n\nThis is the (slightly changed) first document\n\n'
            "It's been changed even more")

def htmldata_1():
    return ('<?xml version="1.0" encoding="utf-8" ?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
            ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n'
            '<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
            '<meta name="generator" content="Docutils 0.14: http://docutils.sourceforge.net/" />\n'
            '<title>test document</title>\n\n</head>\n'
            '<body>\n<div class="document" id="test-document">\n'
            '<h1 class="title">test document</h1>\n\n'
            '<p>This is the (slightly changed) first document</p>\n'
            "<p>It's been changed even more</p>\n</div>\n</body>\n</html>")

def htmldata_2():
    return ('<?xml version="1.0" encoding="utf-8" ?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"'
            ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n'
            '<head>\n<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />\n'
            '<meta name="generator" content="Docutils 0.14: http://docutils.sourceforge.net/" />\n'
            '<title>test document</title>\n\n</head>\n'
            '<body>\n<div class="document" id="test-document">\n'
            '<h1 class="title">test document</h1>\n\n'
            '<p>This is the (slightly changed) first document</p>\n'
            "<p>It's been changed even more</p>\n</div>\n"
            '<p>This footer was created by editing the HTML and should disappear'
            ' when the document is regenerated</p>i\n'
            "</body>\n</html>")
