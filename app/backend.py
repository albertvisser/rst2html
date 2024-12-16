"""Rst2HTML: import data backend routines according to app settings
"""
from app_settings import DML
if DML == 'fs':
    import app.docs2fs as dml
elif DML == 'mongo':
    import app.docs2mongo as dml
elif DML == 'postgres':
    import app.docs2pg as dml
else:
    raise ValueError('Invalid data backend specified in app settings')
