import sqlite3

conn = sqlite3.connect('papers.db')
cursor = conn.cursor()

cursor.execute(f'''
    DROP TABLE papers;
''')
conn.close()