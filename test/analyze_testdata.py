"""helper program for Rst2HTML tests: interpreting differences
"""
import datetime
from bs4 import BeautifulSoup
from test_dml import list_site_contents, WEBROOT
sitename = 'testsite'


class Comparer:
    """Methods and state for comparing data between subsequent tests
    """
    def __init__(self, backend):
        """
        namelist:   verzameling namen van eerder uitgevoerde tests
                    deze is alleen initieel bij de eerste aanroep van dump_data_and_compare
        hetzelfde geldt voor dbdatalist en htmldatalist
        """
        self.loc = backend
        self.namelist = []
        self.dbdatalist = []
        self.htmldatalist = []


    def dump_data_and_compare(self, name, data):
        """main processing"""
        self.name = name
        print("---- {} ----".format(name))
        # if name.startswith('23b'):  # migdel varianten ,staan nu nog gedeactiveerd
        #     breakpoint()
        fname = '/tmp/{}/{}.html'.format(self.loc, name)
        with open(fname, 'w') as _out:
            _out.write(data)
        htmldata = self.analyze_html_data(fname)

        if self.loc == 'fs' and name.startswith('23'):
            fname = '/tmp/{}/{}_filelist'.format(self.loc, name)
            with open(fname, 'w') as _out:
                print('files in source:', [x for x in (WEBROOT / sitename / '.source').iterdir()],
                        file=_out)
                print('files in target:', [x for x in (WEBROOT / sitename / '.target').iterdir()],
                        file=_out)
                print('files in mirror:', [x for x in (WEBROOT / sitename).iterdir()], file=_out)

        fname = '/tmp/{}/db_{}'.format(self.loc, name)
        db_data = list_site_contents(sitename, fname)

        if self.namelist:
            old, new = self.namelist[-1], name
            # print('in dump_data_and_compare: getting db diff')
            # print('old =', old)
            # print('new =', new)
            # print('db_data old =', self.dbdatalist[-1])
            # print('db_data new =', db_data)
            dbresult = self.get_db_diff(old, new, self.dbdatalist[-1], db_data)
        else:
            dbresult = db_data  # {}
        htmlresult = htmldata  # []
        self.namelist.append(name)
        self.dbdatalist.append(db_data)
        if htmldata:
            self.htmldatalist.append(htmldata)
        return dbresult, htmlresult


    def analyze_db_data(self, name):
        "convert text dump to datastructure"
        # not necessary, the original stuff works as well (or better)


    def get_db_diff(self, old, new, olddata, newdata):
        """compare site data dumps
        """
        result = []
        # because we never remove stuff, we can concentrate on what's new
        oldsite, olddocs = olddata
        newsite, newdocs = newdata
        if newsite == oldsite and not self.name.startswith('20c'):
            result.append('site data has not changed')
            return result
        if newdocs == olddocs:
            result.append('site docs have not changed')
        # with open('/tmp/get_db_diff_print_old_and_new', 'w') as f:
        #     print('--- oldsite: ---\n' + oldsite, file=f)
        #     print('\n\n--- newsite: ---\n' + newsite, file=f)
        ## print(olddocs, newdocs)
        if oldsite == {}:
            result.append('new site has been added')
            return result
        result.extend(self._compare_settings(oldsite, newsite))
        result.extend(self._compare_docstats(oldsite, newsite))
        result.extend(self._compare_docs(olddocs, newdocs))
        return result


    def _compare_settings(self, oldsite, newsite):
        result = []
        for setting in newsite['settings']:
            if setting not in oldsite['settings']:
                result.append('new setting: {} {}'.format(setting, newsite['settings']))
                continue
            if newsite['settings'] != oldsite['settings']:
                result.append('setting {} changed from {} to {}'.format(
                    setting, oldsite['settings'], newsite['settings']))
        return result


    def _compare_docstats(self, oldsite, newsite):
        result = []
        for subdir in list(newsite['docs']):
            if subdir not in oldsite['docs']:
                result.append('new subdir: {}'.format(subdir))
                continue
            olddir = oldsite['docs'][subdir]
            for doc in newsite['docs'][subdir]:
                if doc not in olddir:
                    result.append('new doc in subdir {}: {}'.format(subdir, doc))
                    continue
                olddoc = olddir[doc]
                for doctype in newsite['docs'][subdir][doc]:
                    if doctype not in olddoc:
                        result.append('new doctype for doc {} in {}: {}'.format(
                            doc, subdir, doctype))
                    else:
                        mindate = datetime.datetime.min
                        test = newsite['docs'][subdir][doc][doctype].get('updated', None)
                        test2 = newsite['docs'][subdir][doc][doctype].get('deleted', False)
                        if test and test != olddoc[doctype].get('updated', mindate):
                            if doctype != 'mirror':
                                result.append('{} {} {} was changed'.format( subdir, doc, doctype))
                            else:
                                result.append('{} {} was copied to mirror (again)' ''.format(subdir,
                                                                                             doc))
                        elif test2 != olddoc[doctype].get('deleted', False):
                            if doctype == 'mirror':
                                result.append('{} {} {} was deleted'.format( subdir, doc, doctype))
                            else:
                                result.append('{} {} {} was marked as deleted'.format(subdir, doc,
                                                                                      doctype))
        return result


    def _compare_docs(self, olddocs, newdocs):
        # document ids are sorted, but not necessarily in creation order
        result = []
        oldids = [x['_id'] for x in olddocs]
        newids = [x['_id'] for x in newdocs]
        for _id in set(oldids + newids):
            if _id in oldids and _id not in newids:
                result.append('doc {} is removed'.format(_id))
            elif _id in newids and _id not in oldids:
                result.append('doc {} is new'.format(_id))
            else:
                for doc in olddocs:
                    if doc['_id'] == _id:
                        olddoc = doc
                        break
                for doc in newdocs:
                    if doc['_id'] == _id:
                        newdoc = doc
                        break
                if (newdoc['current'] != olddoc['current'] or
                        newdoc['previous'] != olddoc['previous']):
                    result.append('doc {} is changed'.format(_id))
        return result


    def analyze_html_data(self, name):
        "convert HTML to datastructure"
        result = {}
        with open(name) as _in:
            # try:
            soup = BeautifulSoup(_in, 'lxml')
            # except ???:
            # soup = BeautifulSoup(_in)
        result['title'] = soup.find('title').string
        # ander resultaat als we op een niet-editor pagina zitten
        for btn in soup.find_all('button'):
            test = btn.parent
            if (''.join(x for x in btn.stripped_strings) == 'Back to editor' and
                    test.name == 'a' and
                    'href' in test.attrs and
                    (test['href'].startswith('/loadrst/?rstfile=') or
                     test['href'].startswith('/loadhtml/?htmlfile=') or
                     test['href'].startswith('/loadconf/?settings='))):
                        result['backlink'] = test['href']
                        result['pagetext'] = soup.find('div', 'document').get_text()
                        return result
        # select elementen inspecteren
        for selector in soup.find_all('select'):
            options = []
            selected = ''
            for option in selector.find_all('option'):
                options.append(option.string)
                if 'selected' in option.attrs:
                    selected = option.string
            result[selector["name"]] = {'values': options, 'selected': selected}
        # input elementen inspecteren
        # waarschijnlijk is alleen het naam veld voldoende, de andere inputs zijn meen ik buttons
        for inp in soup.find_all('input'):
            if inp.get("name", '') == 'newfile':
                result["newfile_name"] = inp["value"]
                break
        else:
            result['newfile_name'] = ''
        # melding tekst onthouden
        result["mld_text"] = soup.find('strong').string
        # inhoud textarea onthouden
        result["textdata"] = soup.find('textarea').string or ''
        return result


    # verschillen tussen de htmls zijn eigenlijk niet zo interessant
    # daarom wordt deze ook niet meer gebruikt
    def get_html_diff(self, old, new, olddata, newdata):
        "compare html output"
        diff = []
        ## olddata = analyze_html_data('/tmp/{}.html'.format(old))
        ## newdata = analyze_html_data('/tmp/{}.html'.format(new))
        if 'different_page' in olddata:
            return ['no diff possible: olddata is different_page']
        for key in olddata:
            if olddata[key] != newdata[key]:
                if key.endswith('_list'):
                    for value in olddata[key]:
                        if value not in newdata[key]:
                            diff.append('{}: removed value "{}"'.format(key, value))
                    for value in newdata[key]:
                        if value not in olddata[key]:
                            diff.append('{}: added value "{}"'.format(key, value))
                elif key == 'textdata':
                    if newdata[key]:
                        diff.append('{} changed'.format(key))
                    else:
                        diff.append('{} cleared'.format(key))
                elif key == 'mld_text':
                    diff.append('{} is "{}"'.format(key, newdata[key]))
                else:
                    diff.append('{}: value was "{}", is now "{}"'.format(
                        key, olddata[key], newdata[key]))
        return diff