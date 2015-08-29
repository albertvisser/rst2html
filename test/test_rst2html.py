from rst2html import Rst2Html
import pickle as pck

def test_init():
    test = Rst2Html()
    ## # establish baseline
    ## with open('rst2html_baseline', 'wb') as _out:
        ## pck.dump(test, _out)
    ## return
    # compare output with baseline
    with open('rst2html_baseline', 'rb') as _in:
        baseline = pck.load(_in)
    print('conffile...', end='')
    try:
        assert test.conffile == baseline.conffile
    except AssertionError as e:
        print(e)
    else:
        print('ok')
    print('current...', end='')
    try:
        assert test.current == baseline.current
    except AssertionError as e:
        print(e)
    else:
        print('ok')
    print('conf...', end='')
    try:
        assert test.conf == baseline.conf
    except AssertionError as e:
        print(e)
        print(test.conf)
        print(baseline.conf)
    else:
        print('ok')
    print('subdirs...', end='')
    try:
        assert test.subdirs == baseline.subdirs
    except AssertionError as e:
        print(e)
        print(test.subdirs)
        print(baseline.subdirs)
    else:
        print('ok')
    print('output...', end='')
    try:
        assert test.output == baseline.output
    except AssertionError as e:
        print(e)
        print("compare html")
        with open('rst2html_output_fout.html', "w") as _out:
            _out.write(baseline.output)
    else:
        print('ok')

if __name__ == "__main__":
    test_init()
