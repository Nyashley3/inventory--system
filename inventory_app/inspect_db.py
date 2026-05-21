import os, sqlite3
path = 'inventory.db'
print('DB exists:', os.path.exists(path))
if os.path.exists(path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    print('TABLES:', [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type=\'table\' ORDER BY name")])
    print('USER schema:')
    for row in cur.execute('PRAGMA table_info(user)'):
        print(row)
    con.close()
