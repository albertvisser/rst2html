import argparse
import collections
import docs2fs as dmlf
import docs2mongo as dmlm
import docs2pg as dmlp


def main(args):
    """return the results from the root and its subdirectories

    walk the root to get results from it
    then walk the subdirectories to add the results from there
    """
    sitename = args.input
    find = args.search
    replace = args.replace
    report = [f'search in site "{sitename}" documents for "{find}"']
    if replace is not None:
        report[0] += f' and replace with "{replace}"'
    # determine dml to use
    if sitename in dmlf.list_sites():
        dml = dmlf
    elif sitename in dmlm.list_sites():
        dml = dmlm
    elif sitename in dmlp.list_sites():
        dml = dmlp
    else:
        return [f'sitename `{sitename}` not found in known configurations']
    report.append('')
    results = read_dir(dml, sitename, find, replace)
    for dirname in dml.list_dirs(sitename, 'src'):
        results.update(read_dir(dml, sitename, find, replace, dirname))
    for key, value in sorted(results.items()):
        starter_line = 'found in document {}'.format('/'.join(key))
        # is het wel interessant om te melden waar het niet gevonden is?
        # if value:
        #     lines = ['  at line {} index {}: {}'.format(x, z, y) for (x, y, z) in value]
        #     if len(lines) == 1:
        #         starter_line += lines[0]
        #         lines = []
        # else:
        #     starter_line = 'not ' + starter_line
        #     lines = []
        if not value:
            continue
        lines = [f'  at line {x} index {y}: {z}' for (x, y, z) in value]
        if len(lines) == 1:
            starter_line += lines[0]
            lines = []
        report.extend([starter_line] + lines)
    if len(report) == len(['header', 'lines']):
        report.append('  nothing found')
    return report


def read_dir(dml, sitename, search, replace, dirname=''):
    """return the results by walking a directory and getting results from the files in it

    results in this case being search results (and replacements) in each document
    """
    results = collections.defaultdict(list)
    for filename in dml.list_docs(sitename, 'src', directory=dirname):
        results[(dirname, filename)] = process_file(dml, sitename, dirname, filename,
                                                    search, replace)
    return results


def process_file(dml, sitename, dirname, filename, search, replace):
    """do the finds and if needed the replacements
    """
    results = []
    contents = dml.get_doc_contents(sitename, filename, 'src', dirname)
    for number, line in enumerate(contents.split('\n')):
        if search in line:
            pos_list = []
            pos = line.find(search)
            while pos > -1:
                pos_list.append(pos)
                pos = line.find(search, pos + 1)
            results.append((number + 1, line.strip(), [x + 1 for x in pos_list]))
        if replace is not None:
            new_contents = contents.replace(search, replace)
            dml.update_rst(sitename, filename, new_contents, dirname)
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='simple search_all functionality')
    parser.add_argument('-i', '--input', nargs='?', required=True, help='name of site to search')
    parser.add_argument('-s', '--search', nargs='?', required=True, help='string to search for')
    parser.add_argument('-r', '--replace', nargs='?', required=False, help='string to replace with')
    args = parser.parse_args()
    for line in main(args):
        print(line)
