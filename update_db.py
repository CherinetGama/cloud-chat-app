import sqlite3

def update_database():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        # file_url የሚባል አዲስ ኮለምን መጨመር
        cursor.execute('ALTER TABLE messages ADD COLUMN file_url TEXT')
        conn.commit()
        print("Database updated successfully!")
    except sqlite3.OperationalError:
        print("Column already exists or database error.")
    conn.close()

if __name__ == '__main__':
    update_database()
