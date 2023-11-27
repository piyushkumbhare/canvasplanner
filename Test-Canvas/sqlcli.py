import sqlite3

con = sqlite3.connect("users.db")
cursor = con.cursor()
cursor.row_factory = sqlite3.Row