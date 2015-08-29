import rst2html_functions as rhfn
import os

def test_import():
    print(rhfn.languages)

def test_get_text():
    with open('languages_read', 'w') as _out:
        for word, phrase in rhfn.languages['en'].items():
            _out.write('{} = {}\n'.format(word, phrase))
    os.system('sort languages.py > languages.sorted')
    os.system('sort languages_read > languages_read.sorted')
    ## os.system('kdiff3 languages.sorted languages_read.sorted')
    os.system('diff languages.sorted languages_read.sorted > languages.diff')
    difflines = []
    origdiff = [
        '< # captions for buttons etc',
        '< # -*- coding: utf-8 -*-',
        '< # onhover descriptions for buttons and fields',
    ]
    with open('languages.diff') as _in:
        for line in _in:
            if line.startswith('<') or line.startswith('>'):
                line = line.strip()
                if len(line) == 1: continue
                difflines.append(line)
    try:
        assert sorted(difflines) == sorted(origdiff)
    except AssertionError as e:
        print(e)
        print(difflines)
    else:
        print('test ok')


if __name__ == "__main__":
    ## test_import()
    test_get_text()
