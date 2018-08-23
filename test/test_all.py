"""Rst2HTML tests: choose testscript to run and dml variants to run with
"""
import argparse
import subprocess
import shutil
import os.path
root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
os.chdir(root)
root = os.path.dirname(root)
dmloms = ['file system', 'mongodb', 'postgresql']
scripts = {'dml': ['test_dml.py', 'test_all_dml.py'],
           'functions': ['test_rst2html_functions', 'test_rhfn_all.py'],
           'scenario': ['test_scenario1.py', ''],
           'app': ['test_rst2html.py', '']}

def main(args):
    """call the test program for a specific type of dml
    """
    if args.dml == 'all':
        for name in args.scripts:
            if scripts[name][1]:
                subprocess.run(['python3', scripts[name][1])
        return
    destfile = os.path.join(root, 'app_settings.py')
    settfile = os.path.join(root, 'app_settings_{}.py'.format(args.dml))
    shutil.copyfile(settfile, destfile)
    for name in args.scripts:
        subprocess.run(['python3', scripts[name][0])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rst2HTML testscript runner")
    parser.add_argument('dml', choices=['fs', 'mongo', 'postgres', 'all'],
                        help="data manipulation type to use")
    parser.add_argument('scripts', nargs='+', choices=scripts.keys(),
                        help="script(s) to execute")
    args = parser.parse_args()
    main(args)
