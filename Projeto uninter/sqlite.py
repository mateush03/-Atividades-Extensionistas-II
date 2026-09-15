import sqlite3
db = sqlite3.connect("relatos.db")
db.row_factory = sqlite3.Row
for r in db.execute("SELECT * FROM relatos"):
    print(dict(r))




db = sqlite3.connect("relatos.db")
db.execute("DELETE FROM relatos")
db.commit()
db.close()   


