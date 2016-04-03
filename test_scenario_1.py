# test scenario 1

from rst2html_mongo import Rst2Html
from docs2mongo import clear_db as init_db
from test_mongodml import list_database_contents

def main():

    init_db()
    # simulate starting up the application
    app = Rst2Html()
    data = app.index()
    with open('/tmp/01_index.html', 'w') as _out:
        _out.write(data)

    # simulate loading new conf
    data = app.loadconf('-- new --', '', '', '', '')
    with open('/tmp/02_loadconf_new.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - forgetting to change the name
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        app.state.newfile, app.state.rstdata)
    with open('/tmp/03_saveconf_invalid.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - using a new name
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testsite', app.state.rstdata)
    with open('/tmp/04_saveconf_new.html', 'w') as _out:
        _out.write(data)

    # simulate saving new conf - using an existing name for a new site
    app.state.newconf = True
    data = app.saveconf(app.state.settings, app.state.rstfile, app.state.htmlfile,
        'testsite', app.state.rstdata)
    with open('/tmp/05_saveconf_existing.html', 'w') as _out:
        _out.write(data)
    app.state.newconf = False

    # simulate creating a new source document

    # simulate saving the new document

    # simulate viewing the (slightly changed) document - check if it's being saved

    # simulate loading an existing source document

    # simulate saving the converted document

if __name__ == "__main__":
    main()
    list_database_contents()
