"""exceute test_scenario_1 for dml system(s) of choice
"""
import subprocess
import shutil
import os.path
import sys
test = sys.argv[1] if len(sys.argv) == 2 else ''
root = os.path.abspath(os.path.dirname(__file__))
os.chdir(root)
root = os.path.dirname(root)
destfile = os.path.join(root, 'app_settings.py')
for sett in ('fs', 'mongo', 'postgres'):
    if test and sett != test:
        continue
    settfile = os.path.join(root, 'app_settings_{}.py'.format(sett))
    shutil.copyfile(settfile, destfile)
    subprocess.run(['python3', 'test_scenario_1.py'])
    outname = '/tmp/test_scenario_1.out'
    shutil.copyfile(outname, outname.replace('.', '_{}.'.format(sett)))
