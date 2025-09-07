import sqlite3, os
conn = sqlite3.connect("contacts.db")
c = conn.cursor()

rows = c.execute("SELECT id, face_id FROM contacts").fetchall()
for r in rows:
    if r[1]:
        filename = os.path.basename(r[1])  # keeps only 'prof1.jpg'
        c.execute("UPDATE contacts SET face_id=? WHERE id=?", (filename, r[0]))

conn.commit()
conn.close()