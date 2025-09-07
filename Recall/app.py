import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_FILE = "contacts.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        association TEXT,
        phone TEXT,
        social_media TEXT,
        face_id TEXT,
        likes TEXT,
        dislikes TEXT,
        relationship_status TEXT,
        city TEXT,
        birthday TEXT,
        education TEXT,
        close_friend BOOLEAN,
        notes TEXT
    )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, city, phone FROM contacts")
    contacts = cursor.fetchall()
    conn.close()
    return render_template("index.html", contacts=contacts)

@app.route("/add", methods=["GET", "POST"])
def add_contact():
    if request.method == "POST":
        file = request.files.get("face_id")
        filename = None
        if file and file.filename:
            # normalize filename
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # store only the filename in DB
            filename = filename

        data = (
            request.form.get("full_name"),
            request.form.get("association"),
            request.form.get("phone"),
            request.form.get("social_media"),
            filename,  # only filename stored
            request.form.get("likes"),
            request.form.get("dislikes"),
            request.form.get("relationship_status"),
            request.form.get("city"),
            request.form.get("birthday"),
            request.form.get("education"),
            1 if request.form.get("close_friend") else 0,
            request.form.get("notes")
        )

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (
                full_name, association, phone, social_media, face_id, likes, dislikes,
                relationship_status, city, birthday, education, close_friend, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("add_contact.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/search", methods=["GET", "POST"])
def search():
    results = []
    keyword = ""
    if request.method == "POST":
        keyword = request.form["keyword"]
        like_str = f"%{keyword}%"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, full_name, city, phone, social_media, face_id, notes
            FROM contacts
            WHERE full_name LIKE ?
               OR association LIKE ?
               OR phone LIKE ?
               OR social_media LIKE ?
               OR likes LIKE ?
               OR dislikes LIKE ?
               OR relationship_status LIKE ?
               OR city LIKE ?
               OR birthday LIKE ?
               OR education LIKE ?
               OR notes LIKE ?
        """, (like_str,)*11)
        results = cursor.fetchall()
        conn.close()

        # normalize face_id filenames
        results = [
            r[:5] + (r[5].split("\\")[-1] if r[5] else None,) + r[6:]
            for r in results
        ]

    return render_template("search.html", results=results, keyword=keyword)


@app.route("/contact/<int:contact_id>")
def view_contact(contact_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name, association, phone, social_media, face_id, likes, dislikes,
               relationship_status, city, birthday, education, close_friend, notes
        FROM contacts WHERE id = ?
    """, (contact_id,))
    contact = cursor.fetchone()
    conn.close()

    if not contact:
        return "Contact not found", 404

    return render_template("view_contact.html", contact=contact)

@app.route("/delete/<int:contact_id>", methods=["POST"])
def delete_contact(contact_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # optionally, delete the uploaded image from disk
    cursor.execute("SELECT face_id FROM contacts WHERE id=?", (contact_id,))
    face_id = cursor.fetchone()
    if face_id and face_id[0]:
        import os
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], face_id[0]))
        except FileNotFoundError:
            pass

    # delete from DB
    cursor.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)